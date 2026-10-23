# SUBMIT — GEMSDOE85, axis CONCENTRATION (parent R0 = `h33-h33-2-b2`, 0.2778 CLAIM)

The human submits from their own registered DrivenData account. Nothing in this repository
logs in, scrapes the leaderboard or submits. **Upload exactly one file per slot: the
zeros-outside twin** (see IRREGULARITIES.md IR-85-A5 — the incumbent `h33-2-b2` is itself a
zeros-outside file, and the shared validator accepts only that encoding).

## The three candidate slots (blind order: submit the smallest dose first)

| slot | file to upload | sha256 | bytes | dots | note (≤ 140 chars) |
|---|---|---|---|---|---|
| 1 | `releases/gems85-h33-h33-2-b2-conc10-20261023-f89e4659-zeros.tif` | `8b406ca6d73af59d757fe26686c8b9035488cfc9f05217222f19b7a7cc5a9fef` | 145,105 | 37,654 | `parent h33-2-b2 0.2778 CLAIM; 10% of dots moved from lowest- to highest-prior 0.8km blocks; pred live -0.01 to -0.03` |
| 2 | `releases/gems85-h33-h33-2-b2-conc15-20261023-45bfb93b-zeros.tif` | `a52fba562d4dbc57e5741a04bd19f4a644d68deffaeec1d134c3fa93261fd2cd` | 144,107 | 37,654 | `parent h33-2-b2 0.2778 CLAIM; 15% of dots moved from lowest- to highest-prior 0.8km blocks; pred live -0.01 to -0.03` |
| 3 | `releases/gems85-h33-h33-2-b2-conc20-20261023-a93e0b41-zeros.tif` | `67b6680f0ec18e72b8266a1f0f6126dc937803cecf92472cdb702b3fe7f96337` | 143,050 | 37,654 | `parent h33-2-b2 0.2778 CLAIM; 20% of dots moved from lowest- to highest-prior 0.8km blocks; pred live -0.01 to -0.03` |

The three notes are also in `ledger/submissions.csv` (`form_note`); the exact strings there
are the ones to paste into the portal.

## Format receipt (re-read from disk after writing; `evidence/axis_concentration_build.json`)

| check | conc10 | conc15 | conc20 |
|---|---|---|---|
| single band, float32, 3730×3292, EPSG:32611, transform = `sample_submission.tif` | PASS | PASS | PASS |
| values in [0, 1] inside the footprint | PASS | PASS | PASS |
| no NaN inside the footprint; NaN outside (NaN twin) | PASS | PASS | PASS |
| all finite, zeros outside (zeros twin) | PASS | PASS | PASS |
| no Inf anywhere | PASS | PASS | PASS |
| **zero mass on catalogue pixels** (60,988 known-fault pixels) | PASS | PASS | PASS |
| dot count held exactly at 37,654 | PASS | PASS | PASS |
| every newly placed dot > 3 px from the catalogue | PASS | PASS | PASS |
| every newly placed dot ≥ 1 px from every retained dot | PASS | PASS | PASS |
| sha256 not already present in the ledger | PASS | PASS | PASS |
| file re-read from disk after writing | PASS | PASS | PASS |
| shared validator `vendor/gems57.gates.format_report` (zeros twin) | `ok = true` | `ok = true` | `ok = true` |
| shared validator `vendor/gems57.validate.validate` (zeros twin, footprint + catalogue) | all checks passed | all checks passed | all checks passed |
| shared validator on the NaN twin | `ok = false` (rejects NaN pixels) | same | same |

**Parent rebuild (the "never approximate the parent" check).** R0 was rebuilt from its
recipe — `h27-4-solo-d28` minus every dot with Euclidean catalogue distance ≤ 2 px — and
the rebuild is **pixel-exact** against the pinned parent
(`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`); the rebuilt file's
own sha256 differs only because the pinned parent was written with a different GeoTIFF byte
layout. The recipe, both hashes and the verdict are in
`evidence/axis_concentration_build.json → parent_rebuild`.

**Parent diff (what changed, per file).** Dot count is unchanged; the edit is a relocation.

| | conc10 | conc15 | conc20 |
|---|---|---|---|
| dots moved | 3,765 (10.00 %) | 5,648 (15.00 %) | 7,531 (20.00 %) |
| source blocks (lowest prior) | 3,713 | 5,299 | 6,740 |
| target blocks (highest prior) | 838 | 1,367 | 1,940 |
| mean block prior: source → target | 0.017 → 0.260 | 0.022 → 0.243 | 0.026 → 0.229 |
| share of dots in top-decile prior blocks | 10.6 % → 20.6 % | 10.6 % → 22.1 % | 10.6 % → 22.2 % |
| block-density CV, 0.8 km occupied blocks (R0 = 0.551) | 0.767 | 0.786 | 0.782 |
| block-density CV, 1.0 km occupied blocks (R0 = 0.619) | 0.774 | 0.806 | 0.820 |
| mean displacement | 151.8 km | 142.7 km | 151.5 km |

**Report only (never gates).** Catalogue hide-and-recover PROXY, evaluator
`gems57-pooled-hide-v2`, 22,663 withheld positives, 95 % CI from the paired physical
spatial-cluster bootstrap (157 clusters, 1,000 draws, seed 520810): R0 `0.00401`
[0.00342, 0.00469] → conc10 `0.00378` [0.00322, 0.00444] → conc15 `0.00366`
[0.00311, 0.00431] → conc20 `0.00350` [0.00297, 0.00414]. This instrument correlates
−0.87…+0.54 with live scores in the family record and is **never** called a score.

## After the human submits

1. Copy the receipt score and the date into `ledger/submissions.csv`
   (`receipt_score`, `receipt_date`) and add the row to `ledger/history.csv` with
   `receipt = Y` and evidence class `RECEIPT`.
2. Update the CURRENT STATE block in `README.md` (best receipt, slots left).
3. Re-plan against `SLOT_PLAN.md`: a live change under 0.01 is "no evidence" (public chunks
   only; the private score may differ).
