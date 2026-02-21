#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREBUILD = ROOT / "prebuild" / "src" / "main" / "resources" / "assets"

PNG_FILES = ["i", "j", "k", "l", "n", "q", "t", "u", "w", "z"]
DAT_FILES = ["m", "o", "p", "r", "s", "v"]
LANG_FILES = {
    "0": "en.txt",
    "1": "fr.txt",
    "2": "de.txt",
    "3": "es.txt",
    "4": "it.txt",
    "5": "pt.txt",
}
TEXT_FILES = {
    "x": "credits.txt",
    "y": "licenses.txt",
}


def _clean_null_separated(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace").replace("\x00", "\n")
    lines = []
    for ln in text.splitlines():
        ln = ln.lstrip("\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f").strip()
        if ln:
            lines.append(ln)
    return "\n".join(lines) + "\n"


def main() -> None:
    (PREBUILD / "images").mkdir(parents=True, exist_ok=True)
    (PREBUILD / "lang").mkdir(parents=True, exist_ok=True)
    (PREBUILD / "data").mkdir(parents=True, exist_ok=True)

    for name in PNG_FILES:
        src = ROOT / name
        dst = PREBUILD / "images" / f"{name}.png"
        data = src.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"{src} is not a PNG payload")
        dst.write_bytes(data)

    for name in DAT_FILES:
        src = ROOT / name
        dst = PREBUILD / "data" / f"{name}.dat"
        dst.write_bytes(src.read_bytes())

    for src_name, out_name in LANG_FILES.items():
        (PREBUILD / "lang" / out_name).write_text(
            _clean_null_separated((ROOT / src_name).read_bytes()), encoding="utf-8"
        )

    for src_name, out_name in TEXT_FILES.items():
        (PREBUILD / "data" / out_name).write_text(
            _clean_null_separated((ROOT / src_name).read_bytes()), encoding="utf-8"
        )

    ini_src = ROOT / "supplied by D@nilYcH.ini"
    (PREBUILD / "data" / "supplied_by_D@nilYcH.ini").write_bytes(ini_src.read_bytes())

    print("Generated prebuild assets successfully.")


if __name__ == "__main__":
    main()
