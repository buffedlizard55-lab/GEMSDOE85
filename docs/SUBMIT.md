# SUBMIT — file, name, note, format receipt

One entity, three scored submissions per rolling week plus one final. **The human submits from their
own account; nothing here logs in, scrapes or submits.**

Slots: **3 of 3 left this week, 0 used** (human, 2026-10-23). Parent `h33-h33-2-b2`, live 0.2778
= **CLAIM** (no receipt in this repo). TOP_PUBLIC **not supplied** — do not fill it from the README's
cited 0.4413.

Upload the `-zeros` twin. Every file below is 37,654 unit dots unless stated, float32, EPSG:32611,
3730 × 3292, values in [0, 1] inside the footprint, zero outside, zero mass on the catalogue, and
re-read from disk after writing.

## Slot 1 — `releases/h33-2-b2-prune3-20261023-fb308615.tif`
* sha256 in `ledger/submissions.csv` (row `h33-2-b2-prune3-20261023-fb308615`) · **35,483 dots** (the
  only file here that changes the count: it *deletes* the 2 < d_cat ≤ 3 px ring)
* name: `GEMSDOE85 PRUNE3 | drop 2171 dots at 2<d_cat<=3px, 35483 dots`
* note: `parent h33-h33-2-b2 (0.2778 CLAIM); PRUNE collar 2<d_cat<=3px removed, no refill; predicts +0.007 (MODEL)`

## Slot 2 — `releases/gems85-h33-h33-2-b2-conc10-20261023-f89e4659-zeros.tif`
* 37,654 dots, 10 % moved between 0.8 km blocks by prior
* name: `GEMSDOE85 CONC10 | 3765 dots moved low-prior->high-prior 0.8km blocks`
* note: `parent h33-h33-2-b2; 10% of dots re-blocked by prior, count fixed; predicts +0.000..+0.010 (MODEL)`

## Slot 3 — conditional (see `SLOT_PLAN.md`)
`reliefp2r10-…-669f0637` if slot 2 is flat · `conc15-…-45bfb93b` if slot 2 is positive ·
`h33-h33-2-b2-space10-20261023-b4a3bd25-zeros.tif` only if the collar proves free.

## This session's SPACING files (capacity probe, not slot candidates unless both above are flat)
| file | change | sha256 (zeros) |
|---|---|---|
| `h33-h33-2-b2-space10-20261023-b4a3bd25-zeros.tif` | 3,765 lowest-unique-credit dots removed, refilled at the cells adding most new credit; 10.00 % of dots differ, Jaccard 0.818 | `b4a3bd259829987c…` |
| `h33-h33-2-b2-space20-20261023-48eea7b7-zeros.tif` | 7,531 removed/refilled, 20.00 %, Jaccard 0.667 | `48eea7b7475cbb59…` |
| `h33-h33-2-b2-space10s-20261023-55abf636-zeros.tif` | as space10 but refills only inside continuous traces (≥ 4 skeleton px in 5 × 5) | `55abf6368ab79167…` |

## Format receipt (all files re-read from disk)

`python scripts/validate_submission.py releases/<file>-zeros.tif` → `format_ok: true` for every
`-zeros` twin in `releases/`; `vendor/gems57/gates.format_report` and `gems57.validate.validate`
report no problems, 0 catalogue pixels, 37,654 (or 35,483) positive pixels, min 0.0, max 1.0.

The `-nan` twins match the competition spec (NaN outside, `nodata=nan`) and pass every substantive
check but fail this repo's stricter all-finite export policy on the outside-footprint cells — that is
why they are published, but not uploaded.

**A PASS here is not geological skill, not uniqueness clearance, not slot approval, and not
organizer acceptance. A live change under 0.01 is no evidence.**
