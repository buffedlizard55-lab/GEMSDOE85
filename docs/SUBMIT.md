# SUBMIT — v2, 2026-10-23 (supersedes the earlier STOP note)

The earlier v2 preflight session (commit `a6004d6`) had no candidate and said STOP. This session
built three gated candidates; the STOP applies only to files **not** listed below. Upload one file
per slot from the human's registered account. Nothing here logs in, scrapes or submits.

The human submits from their own registered account. Nothing in this repository logs in, scrapes or
submits. Upload **one file per slot**. `TOP_PUBLIC` and the remaining slot count are read by the
human off the leaderboard/account page and written into `README.md` (CURRENT STATE block).

## Slot 1 (highest expected value)

- **File:** `releases/h33-2-b2-prune3-20261023-fb308615.tif` (NaN outside the footprint, per the brief
  and the sample submission encoding). Fallback if the portal rejects NaN outside: the identical-pixel
  twin `releases/h33-2-b2-prune3-20261023-fb308615-zeros.tif`.
- **sha256:** `fb308615161ad8f62b063d90972a4c36e7c66e7c58beb3316c81497cfe65261e` (346,839 B, 35,483 dots)
- **Name / note (115 / 140 chars):**
  `R0 h33-2-b2 PRUNE rung3: drop 2<d_cat<=3px flank dots, 37654->35483 (5.77%), no refill; pred +0.007 MODEL; UNSCORED`
- **Format receipt** (`evidence/session_prune_receipt.json → variants["h33-2-b2-prune3"]`):
  EPSG:32611 · 3730×3292 · 1 band · float32 · transform `100,0,243350,0,-100,4508550` ·
  `nodata=nan` · values ⊆ {0,1} inside footprint · 0 NaN/Inf inside footprint · NaN everywhere outside ·
  0 positive px on the catalogue · min distance to catalogue = 3.16 px · re-read from disk after writing ·
  **14/14 checks PASS** (zeros twin: 15/15).
- **After scoring:** paste the score and date into `ledger/submissions.csv` (`receipt_score`,
  `receipt_date`) and mark it RECEIPT in `README.md`.

## Slot 2

- **File:** `releases/h33-2-b2-prune4-20261023-2880b0e9.tif` (fallback `…-zeros.tif`)
- **sha256:** `2880b0e90582d4cfe03165c41201c107071d3a1a88a5717351a6943f29365e7a` (340,096 B, 33,829 dots)
- **Note (116 / 140):**
  `R0 h33-2-b2 PRUNE rung4: drop 2<d_cat<=4px flank dots, 37654->33829 (10.16%), no refill; pred +0.003 MODEL; UNSCORED`
- **Format receipt:** identical grid/crs/dtype/band/encoding checks; min distance to catalogue = 4.12 px;
  **14/14 checks PASS** (zeros twin: 15/15).

## Slot 3 (spend only if slots 1 and 2 both scored ≥ 0.2778)

- **File:** `releases/h33-2-b2-prune5-20261023-7ebfc408.tif` (fallback `…-zeros.tif`)
- **sha256:** `7ebfc4086506e574ec9481de08f5efd0a4b4f3180081957d09e4692f14dde6e7` (332,443 B, 32,017 dots)
- **Note (116 / 140):**
  `R0 h33-2-b2 PRUNE rung5: drop 2<d_cat<=5px flank dots, 37654->32017 (14.97%), no refill; pred -0.003 MODEL; UNSCORED`
- **Format receipt:** identical checks; min distance to catalogue = 5.10 px; **14/14 checks PASS** (zeros twin: 15/15).

## Gates actually enforced by the build script (`scripts/gemsdoe85_prune_session.py`)

Parent pins verified (7 SHA-256) → R0 rebuilt from the pinned H19-5 skeleton and proven pixel-identical
to the pinned parent rasters → each variant proven a subset of the parent's dot set → 1–50 % change rule
→ zero mass on the catalogue, ≥ 3 px from it → written → **re-read from disk** → 14 format checks (NaN encoding; 15 for zeros) →
sha256 not already in the ledger or in any pin. `ALL GATES PASS` is printed only if every variant passes
both encodings.

## Report-only, never gates

- **Catalogue hide-and-recover PROXY** (60,988 withheld positives): R0 = 0.00671, every variant = 0.0.
  Degenerate by construction (all mass is > 3 px from the catalogue), reported only so nobody mistakes
  it for evidence.
- **SGMC control PROXY:** R0 = 0.08938 (all SGMC faults) / 0.09539 (SGMC minus a 3 px catalogue collar);
  rungs 3/4/5 = 0.09369 / 0.08989 / 0.08461 on the collar-free truth. The two known live rungs calibrate
  the proxy's bias at **+0.0083 ± 0.0014** (both signs reproduced); that calibration, not the raw proxy,
  is what produces the MODEL projections in `SLOT_PLAN.md`.
- **Leakage canary:** best single-feature AUC on the catalogue = **0.5687** (`geod_2ndinv`) over 19
  features, 60,988 positives vs 200,000 background — **CLEAN** (< 0.90). The PRUNE axis uses no
  geophysical feature at all; the canary is reported for the record.

## Do not

Do not upload a file whose sha256 differs from the row in `ledger/submissions.csv`, do not upload two
files in one slot, do not re-upload an encoding twin expecting a different score (the ledger's repeats
scored identically), and do not read the leaderboard with anything but a human browser.

## Still missing from the human (blocks slot 2 and the final choice)

- A submission-page **receipt** (score + date) for each upload, pasted into `ledger/submissions.csv`
  (`receipt_score`, `date`; set `receipt` to `Y`). Until then 0.2778 stays CLAIM.
- `TOP_PUBLIC` with the date observed, and the remaining rolling-week quota from the account page.
- A human-confirmed deadline/timezone: the brief's 2026-12-03 is provisional
  (https://www.drivendata.org/competitions/306/competition-doe-gems/ — human browser only).
- Confirmation that the pinned competition rasters may be redistributed (IR-V2-10).

---

## Backup only — SNAP arms (built 2026-10-23, gated, predicted ≈ 0.000)

These three are **not** slots 1–3. They exist to close the question "are R0's dot positions 1–2 px
off?" (mechanism cards in `evidence/session_snap_receipt.json → mechanism_cards`). Upload one only if
a rolling-week slot would otherwise expire unused.

| arm | file (fallback: `-zeros` twin) | sha256 (nan) | dots / moved | note (≤ 140 chars) | gates |
|---|---|---|---|---|---|
| gravity edge | `releases/h33-2-b2-snapgrav2-20261023-1b033f40.tif` | `1b033f4005e2a996206ce8694ebefbefa6d2822bbb317fb4ae3fef7ecddab6aa` | 37,654 / 2,603 (6.9 %) | `R0 SNAP 2603 dots (6.9%) <=2px onto gravity-hg edge, count fixed; pred -0.000 MODEL; UNSCORED` | 15/15 + 15/15 PASS |
| magnetic edge | `releases/h33-2-b2-snapmag2-20261023-a2fa8b95.tif` | `a2fa8b95aff406d7ea623d2e46ffd17840e75c4789b1788b4d11e4785347eeed` | 37,654 / 9,213 (24.5 %) | `R0 SNAP 9213 dots (24.5%) <=2px onto magnetic-hg edge, count fixed; pred -0.000 MODEL; UNSCORED` | 15/15 + 15/15 PASS |
| scarp edge | `releases/h33-2-b2-snaptop2-20261023-7be865f5.tif` | `7be865f5c3da2f26c755afbbe79720007cc01844943410617801ebe4cecb9bbd` | 37,654 / 19,768 (52.5 %) | `R0 SNAP 19768 dots (52.5%) <=2px onto det-elev scarp edge, count fixed; pred +0.000 MODEL; UNSCORED` | 15/15 + 15/15 PASS |

Format (all three, re-read from disk after writing): `EPSG:32611` · 3730×3292 · 1 band · `float32` ·
transform `100,0,243350,0,-100,4508550` · values ⊆ {0,1} inside the footprint · no NaN/Inf inside ·
NaN everywhere outside (primary) or `nodata=None` all-finite (twin) · **0 dots on the catalogue** ·
no dot moved closer to the catalogue than it started · dot count equal to the parent.

**One disclosed exception:** SNAP keeps the parent's `> 2 px` catalogue exclusion, so 2,171 inherited
flank dots sit at 2–3 px (min 2.236 px). Re-pruning them is PRUNE rung 3 — a second axis — so it is
not done here. Only the PRUNE files satisfy the `>= 3 px` rule numerically.

After scoring: paste the score and date into `ledger/submissions.csv` (`receipt_score`, `date`) and
mark it RECEIPT in `README.md`.
