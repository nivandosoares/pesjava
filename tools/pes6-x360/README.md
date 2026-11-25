# pes6-x360

A Python command-line application for the studied Xbox 360 build of Pro Evolution Soccer 6. It inspects the game's AFS archives and creates a new local game directory with real names, abbreviations and crests for 27 clubs.

Supported input is the analyzed TriploPlayBR build, Title ID `4B4E07DA`, Media ID `617138EB`. The `apply` command also checks the original XEX hash. The output targets Xenia Canary. Xbox 360 hardware compatibility remains unverified.

## Install

From the root of the `pesjava` repository:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install ./tools/pes6-x360
pes6-x360 --help
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`. Use Python 3.10 or newer. The `apply` and `verify` commands need [xex2ool](https://github.com/landaire/acceleration/releases) on your PATH or specified with `--xex2ool`.

## Commands

| Command | Result |
|---|---|
| `inventory GAME [--deep]` | List AFS archive sizes, entry counts and detected formats. |
| `entry ARCHIVE INDEX` | Inspect an entry by zero-based index, including its sizes and inner table. |
| `clubs` | List the 27 club mappings with team rows, crest slots and source IDs. |
| `fetch-logos DIRECTORY` | Download the crest PNGs used by the mapping. Existing PNGs are reused. |
| `roster GAME --team INDEX [--base 6668] [--pe FILE]` | Read a team's player references and shirt numbers. The optional PE adds the inferred team label for base 6668. |
| `apply GAME OUTPUT --logos DIRECTORY [--xex2ool PATH]` | Build and validate a patched game in a new directory outside the source. |
| `verify GAME OUTPUT [--xex2ool PATH]` | Check the club names, crest images, internal names and changed AFS entries. |
| `option-info FILE` | Report a save's size, SHA-256 and possible STFS container signature. Read-only. |

```sh
pes6-x360 fetch-logos ./logos
pes6-x360 apply "/path/to/PES 6" "./PES 6 - Real Clubs" --logos ./logos
pes6-x360 verify "/path/to/PES 6" "./PES 6 - Real Clubs"
```

You can supply your own PNGs instead of downloading them. Use the IDs listed by `pes6-x360 clubs` as filenames, for example `364.png` for Liverpool. The default download retrieves the versions available from the CDN at the time of the request. Crests can differ from their 2006 designs.

The patch edits the local game data in `default.xex` and `cv.img`. The Option File command reports metadata only. You bring your own game dump, XEX tool and save. [Illustrated guide](../../docs/pes-6-xbox-360/option-file.md)
