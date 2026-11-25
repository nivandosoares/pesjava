"""Command line interface for inspecting and patching the supported PES 6 build."""
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
import struct
import subprocess
from tempfile import TemporaryDirectory
from urllib.request import urlopen
import zlib

from PIL import Image

from .aplicar import clubs, patch_cv, rewrite_xex, we_image
from .elencos import read_database, read_team_names
from .inspecionar import Archive, compare, describe, parts, unwrap

ORIGINAL_XEX = "b76db0fc2f86794f4e99bb4d93dd8148d31a00b518cb1e5c822ef0bc75ac1087"
CREST_BANKS = (2710, 2711)


def inventory(args):
    archives = sorted(args.game.glob("*.img"))
    if not archives:
        raise ValueError("No IMG archives found in the game directory")
    return [Archive(path).inventory(args.deep) for path in archives]


def inspect_entry(args):
    return describe(Archive(args.archive), args.index)[0]


def club_rows(_args):
    return [{"team_row": row, "crest_slot": slot, "original": old, "club": new,
             "abbr": abbr, "logo_id": logo}
            for row, slot, old, new, abbr, logo in clubs()]


def fetch_logos(args):
    args.directory.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for _, _, _, _, _, logo in clubs():
        path = args.directory / f"{logo}.png"
        if not path.exists():
            url = f"https://a.espncdn.com/i/teamlogos/soccer/500/{logo}.png"
            with urlopen(url, timeout=15) as response:
                data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise ValueError(f"Image too large for crest {logo}")
            with Image.open(BytesIO(data)) as image:
                if image.format != "PNG":
                    raise ValueError(f"Expected PNG for crest {logo}")
                image.verify()
            with path.open("xb") as output:
                output.write(data)
            downloaded.append(logo)
        else:
            with Image.open(path) as image:
                if image.format != "PNG":
                    raise ValueError(f"Expected PNG for crest {logo}")
                image.verify()
    return {"directory": str(args.directory), "downloaded": downloaded}


def extract_pe(xex, out, tool):
    subprocess.run([tool, "basefile", str(xex), "-o", str(out)],
                   check=True, capture_output=True, text=True)


def roster(args):
    if args.pe and args.base != 6668:
        raise ValueError("Team labels are only mapped to the 6668 roster variant")
    players, teams, shirts, _ = read_database(Archive(args.game / "cv.img"), args.base)
    i = args.team
    if not 0 <= i < len(teams):
        raise ValueError("Team row out of range")
    result = {"archive_index": args.base, "team_row": i}
    if args.pe:
        result["team_label"] = read_team_names(args.pe)[i]["nome"]
    result["players"] = [
        {"slot": slot, "shirt_number": None if number == 255 else number, **players[player]}
        for slot, (player, number) in enumerate(zip(teams[i], shirts[i * 32:(i + 1) * 32]))
        if player
    ]
    return result


def named_crests(archive, handle, index):
    raw = unwrap(archive.read(handle, archive.entries[index]))
    entries = []
    for entry in parts(raw):
        start, size = entry["offset"], entry["bytes"]
        pos = int(entry["aux"], 16)
        entries.append((raw[pos:raw.index(b"\0", pos)], raw[start:start+size]))
    if len(entries) != 207:
        raise ValueError(f"Unexpected number of crest entries in AFS {index}")
    return entries


def verify_build(original, modified, new_pe):
    mapping = list(clubs())
    labels = read_team_names(new_pe)
    for row, slot, _, name, short, _ in mapping:
        label = labels[row]
        if (label["nome"], label["sigla"], label["campo_id_b"]) != (name, short, slot):
            raise ValueError(f"Name, abbreviation or crest link does not match team row {row}")
    a, b = Archive(original / "cv.img"), Archive(modified / "cv.img")
    if compare(a, b) != list(CREST_BANKS):
        raise ValueError("Expected exactly two changed AFS entries")
    changed_slots = {row[1] for row in mapping}
    checked = 0
    with a.path.open("rb") as first, b.path.open("rb") as second:
        for index in CREST_BANKS:
            old = named_crests(a, first, index)
            new = named_crests(b, second, index)
            for i, ((old_name, old_data), (new_name, new_data)) in enumerate(zip(old, new)):
                if old_name != new_name or not old_name.startswith((b"flag_", b"emblem_")):
                    raise ValueError(f"Invalid internal name in AFS {index}, slot {i}")
                if (old_data != new_data) != (i in changed_slots):
                    raise ValueError(f"Unexpected crest change in AFS {index}, slot {i}")
                if i in changed_slots:
                    before = we_image(unwrap(old_data))
                    after = we_image(unwrap(new_data))
                    if before.size != after.size or not after.getbbox() or before.tobytes() == after.tobytes():
                        raise ValueError(f"Invalid decoded crest in AFS {index}, slot {i}")
                checked += 1
    return {"clubs": len(mapping), "changed_crests": len(mapping) * 2,
            "verified_internal_names": checked, "changed_afs_entries": list(CREST_BANKS)}


def apply(args):
    source, destination = args.game.resolve(), args.output.resolve()
    if destination.exists() or destination.is_relative_to(source):
        raise ValueError("Choose a new output directory outside the source game")
    xex = source / "default.xex"
    if sha256(xex.read_bytes()).hexdigest() != ORIGINAL_XEX:
        raise ValueError("Source XEX is not the verified build for Media ID 617138EB")
    mapping = list(clubs())
    for _, _, _, _, _, logo in mapping:
        if not (args.logos / f"{logo}.png").is_file():
            raise ValueError(f"Missing crest {logo}.png")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as tmp:
        scratch = Path(tmp)
        stage = scratch / "game"
        stage.mkdir()
        pe, output_pe = scratch / "original.pe", scratch / "modified.pe"
        extract_pe(xex, pe, args.xex2ool)
        rewrite_xex(xex, pe, stage / "default.xex", mapping)
        patch_cv(source / "cv.img", stage / "cv.img", mapping, args.logos)
        extract_pe(stage / "default.xex", output_pe, args.xex2ool)
        result = verify_build(source, stage, output_pe)
        for filename in source.iterdir():
            if filename.is_file() and filename.name not in {"default.xex", "cv.img"}:
                shutil.copy2(filename, stage / filename.name)
        stage.rename(destination)
    return {"output": str(destination), **result}


def verify(args):
    with TemporaryDirectory() as tmp:
        pe = Path(tmp) / "patched.pe"
        extract_pe(args.modified / "default.xex", pe, args.xex2ool)
        return verify_build(args.original, args.modified, pe)


def option_info(args):
    content = args.file.read_bytes()
    magic = content[:4]
    container = {
        b"CON ": "Xbox 360 CON (STFS)", b"LIVE": "Xbox 360 LIVE (STFS)",
        b"PIRS": "Xbox 360 PIRS (STFS)",
    }.get(magic, "Unidentified payload")
    return {"filename": args.file.name, "bytes": len(content),
            "sha256": sha256(content).hexdigest(), "container_hint": container,
            "save_write_support": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(required=True)
    scan = sub.add_parser("inventory", help="List AFS entries and detected formats")
    scan.add_argument("game", type=Path)
    scan.add_argument("--deep", action="store_true")
    scan.set_defaults(run=inventory)
    entry = sub.add_parser("entry", help="Inspect an AFS entry")
    entry.add_argument("archive", type=Path)
    entry.add_argument("index", type=int)
    entry.set_defaults(run=inspect_entry)
    sub.add_parser("clubs", help="List the 27 club mappings").set_defaults(run=club_rows)
    logos = sub.add_parser("fetch-logos", help="Download crest PNGs to a local directory")
    logos.add_argument("directory", type=Path)
    logos.set_defaults(run=fetch_logos)
    team = sub.add_parser("roster", help="Read a team roster and shirt numbers")
    team.add_argument("game", type=Path)
    team.add_argument("--team", type=int, required=True)
    team.add_argument("--base", type=int, choices=(6667,6668), default=6668)
    team.add_argument("--pe", type=Path)
    team.set_defaults(run=roster)
    patch = sub.add_parser("apply", help="Build a new local game copy with corrected names and crests")
    patch.add_argument("game", type=Path)
    patch.add_argument("output", type=Path)
    patch.add_argument("--logos", type=Path, required=True)
    patch.add_argument("--xex2ool", default="xex2ool")
    patch.set_defaults(run=apply)
    check = sub.add_parser("verify", help="Compare an original and a modified game folder")
    check.add_argument("original", type=Path)
    check.add_argument("modified", type=Path)
    check.add_argument("--xex2ool", default="xex2ool")
    check.set_defaults(run=verify)
    save = sub.add_parser("option-info", help="Fingerprint a save without modifying it")
    save.add_argument("file", type=Path)
    save.set_defaults(run=option_info)
    args = parser.parse_args()
    try:
        print(json.dumps(args.run(args), ensure_ascii=False, indent=2))
    except subprocess.CalledProcessError as error:
        parser.exit(1, f"xex2ool failed: {(error.stderr or error.stdout or '').strip()}\n")
    except (OSError, ValueError, IndexError, KeyError, struct.error, zlib.error) as error:
        parser.exit(1, f"{error}\n")
