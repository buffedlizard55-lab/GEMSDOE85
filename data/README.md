# Data placement

The three small files in `data/raw/` are the grid/catalogue mirrors used for the
reproducible receipts:

| File | SHA-256 | Role |
|---|---|---|
| `sample_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | grid, CRS, transform, and finite scoring footprint |
| `labels.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | catalogue labels used for local hide-and-recover evaluation |
| `existing_faults.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | byte-identical catalogue alias |

**Provenance limitation:** these bytes are owner-supplied mirrors of the
competition files. The SHA-256 values prove byte stability after placement;
they do not authenticate the organizer or the private evaluation labels.
The official data-tab URL is in `registry/sources.json` and requires a
DrivenData account/enrollment in the current environment.

The 19-band `training_features.tif` is approximately 419 MB and is deliberately
not committed. Run:

```bash
bash scripts/restore_feature_stack.sh
python scripts/prepare_data.py
```

The restore script fetches the public GitHub bridge, checks all five part hashes
and the concatenated SHA-256, and writes the ignored local file. It never uses
credentials. A full organizer download can instead be placed at
`data/training_features.tif` and must pass the same geometry checks.
