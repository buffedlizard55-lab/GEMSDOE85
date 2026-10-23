# SUBMIT — how the human uploads one of these files

DrivenData is never contacted by this repository. Everything below is done from the human's
own registered account, by hand.

## Pick a slot

See `SLOT_PLAN.md`. Per file:

| slot | file (upload this one) | name field | note (≤140 chars) | format receipt |
|---|---|---|---|---|
| 1 | `releases/h33-2-b2-mass-m20-20261023-a6075d2f-zeros.tif` | `h33-2-b2-mass-m20` | `R0 h33-2-b2 minus 20% lowest field-credit dots (30124); MODEL bracket [-0.081,+0.007]` | `evidence/mass_axis.json` → `variants.mass-m20.checks` (17/17), sha256 `a6075d2f…4fc4cb` |
| 2 | `releases/h33-2-b2-mass-p10-20261023-82aa483f-zeros.tif` | `h33-2-b2-mass-p10` | `R0 plus 10% next-ranked dots at d1.5 (41415); MODEL bracket [-0.004,+0.020]` | `evidence/mass_axis.json` → `variants.mass-p10.checks`, sha256 `82aa483f…f9261` |
| 3 | `releases/h33-2-b2-mass-m10-20261023-a296bbd1-zeros.tif` | `h33-2-b2-mass-m10` | `R0 minus 10% lowest field-credit dots (33887); MODEL bracket [-0.040,+0.004]` | `evidence/mass_axis.json` → `variants.mass-m10.checks`, sha256 `a296bbd1…10e8a` |

Upload **one file per slot**. Each has a `-nan` twin (NaN outside the footprint) with identical
content; if the upload form rejects the `-zeros` form, use the twin and say so in the receipt.

## After the upload

1. Copy the score and the date from the submission page receipt into
   `ledger/submissions.csv` → `receipt_score`, `receipt_date` for that row, and change
   `status` from `BUILT …` to `RECEIPT <score>`.
2. If the score differs from the bracket in the ledger by more than 0.01, say so — it falsifies
   or confirms the mechanism card, and that is the actual product of the slot.
3. Do not re-upload a file whose sha256 is already in the ledger; at least eight fleet slots
   were spent on exact repeats.

## Format facts a reviewer can re-check locally

`python scripts/build_mass_axis.py --check-parent` reproduces the parent pixel-exactly.
`python scripts/write_mass_ledger.py` re-verifies every hash it writes.
`python -m pytest -q` re-checks release integrity and the mechanism arithmetic.

Every file in `releases/` passed, on disk and after re-read: single band, float32, 3730×3292,
EPSG:32611, template transform, values in [0, 1], no NaN/Inf inside the footprint, zeros (or
NaN, for the twin) outside it, no nodata tag, zero mass on catalogue pixels, minimum Euclidean
distance to the catalogue > 2.0 px. **Not** satisfied: the repo's Chebyshev-2 buffer check
(IR-85-MASS-02) and the brief's ≥3 px rule — both are inherited from R0 itself.
