# SUBMIT — exact text for each slot (PRUNE, 2026-10-23)

One file per slot. Upload the **`-zeros.tif`** (all-finite) file; the NaN-outside twin exists only as
a fallback if the portal rejects an all-finite file (the ledger records that twins score identically).
All paths are relative to the repo root. SHA-256 is of the uploaded bytes — check it after download.

| slot | file | sha256 | bytes | n dots |
|---|---|---|---:|---:|
| 1 | `releases/h33-b2-prune-x3-nofill-20261023-89498c48-zeros.tif` | `89498c488cb1cf5be5fb71c31b2b873b107f8905bbc82a84760969fbbee5297b` | 144,469 | 35,483 |
| 2 | `releases/h33-b2-prune-x3-pushout-20261023-ab917ea0-zeros.tif` | `ab917ea041a2b7e875df22e1eb2f5b85b42ea09403152091c856d6d44478f6fa` | 149,080 | 37,645 |
| 3 | `releases/h33-b2-prune-x2-readd-20261023-dfe20999-zeros.tif` | `dfe20999bf549c138c856354584f0434426e69d569403d2fed6e691b7d4cdaca` | 154,720 | 40,199 |

Fallback twins (NaN outside the footprint, identical dots):
`…-x3-nofill-20261023-2776477c.tif` (188,983 B), `…-x3-pushout-20261023-cdcc6c30.tif` (193,698 B),
`…-x2-readd-20261023-5b6ca72b.tif` (199,378 B).

## Submission name / note (≤140 chars, paste as-is)

**Slot 1** — name: `h33-b2 prune x3 nofill 35483`
note (97 chars):
```
h33-b2 parent; delete 2171 dots at 2<d_cat<=3px (cat-flank mass); pred +0.0062 to 0.2840
```

**Slot 2** — name: `h33-b2 prune x3 pushout 37645`
note (110 chars):
```
h33-b2 parent; ring re-placed outside 3px (count held); tests sign vs mass; pred ~0.2778
```

**Slot 3** — name: `h33-b2 prune x2 readd 40199`
note (96 chars):
```
CONTROL: re-add 2545 dots at 1<d_cat<=2px (scored 0.2708 before); pred 0.2708, not a candidate
```

## Format receipt (re-read from disk after writing, 2026-10-23)

Every file passes, from the bytes on disk: 1 band · `float32` · `3730 × 3292` · `EPSG:32611` ·
transform `(100, 0, 243350, 0, -100, 4508550)` · bounds `(243350, 4135550) – (572550, 4508550)` ·
values in `[0, 1]` · no NaN inside the footprint · the primary file is all-finite (zeros outside) and
the twin is NaN outside · zero positive pixels on the catalogue (`existing_faults.tif`, 60,988 px) ·
positive count matches the dot support exactly · `vendor/gems57/gates.format_report` PASS with
`sample_submission.tif` as the reference. Full machine record: `evidence/prune_variants.json`.

**Before uploading:** confirm the file's sha256 matches the row above, and record the submission-page
receipt (`receipt_score`, `receipt_date`) in `ledger/submissions.csv` — a score without a receipt is
`CLAIM`, not a receipt.
