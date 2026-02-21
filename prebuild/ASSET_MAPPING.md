# Asset mapping and inferred extensions

This pre-build layout is reconstructed from extracted artifacts in repository root.

## Generated locally

Binary-incompatible artifacts are **not versioned** inside `prebuild/src/main/resources/assets`.
Generate them locally with:

```bash
python scripts/generate_prebuild_assets.py
```

## Mapping rules

- PNG detected by signature: `89 50 4E 47` -> `assets/images/*.png`
- Null-separated localization blobs (`0`..`5`) -> `assets/lang/*.txt`
- Null-separated text blobs (`x`, `y`) -> `assets/data/{credits,licenses}.txt`
- Opaque binary payloads (`m`, `o`, `p`, `r`, `s`, `v`) -> `assets/data/*.dat`
- INI blob (`supplied by D@nilYcH.ini`) -> `assets/data/supplied_by_D@nilYcH.ini`
