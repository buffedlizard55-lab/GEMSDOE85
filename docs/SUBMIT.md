# SUBMIT — v2, 2026-10-23 (supersedes the earlier STOP note; SNAP contingency added)

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

## Contingency uploads — SNAP (only if a slot is free and the PRUNE ladder is closed)

Axis SNAP keeps the parent's **count and mass** (37,654 dots, each 1.0) and moves a subset of dots
≤ 2 px onto a pre-declared response field. All three were built by `scripts/gemsdoe85_snap_session.py`;
mechanism, confounders and falsifiers are in `docs/mechanism_cards_snap.md`. Spend them in the order
below — the first is the largest effect and the only one that can show an off-ridge cost.

### SNAP-1 (spend first among SNAP)

- **File:** `releases/snap-free-lidar2-20261023-ac3fc128.tif` (fallback `…-ac3fc128-zeros.tif`)
- **sha256:** `ac3fc128de9f9c9e320b20b6be04ba2d81b62727d3875d08dd60e5974d020519` (332,727 B, 37,654 dots)
- **Name / note (126 / 140):**
  `R0 h33-2-b2 SNAP control: 57% dots move <=2px to lidar-scarp peak anywhere in window; count fixed; pred -0.004 MODEL; UNSCORED`
- **Change:** 21,441 dots (56.94 %) moved, mean 1.493 px; support coverage 0.63341 → 0.51368 (−18.9 %).
- **Format receipt** (`evidence/session_snap_receipt.json → variants["snap-free-lidar2"]`):
  EPSG:32611 · 3730×3292 · 1 band · float32 · transform `100,0,243350,0,-100,4508550` · `nodata=nan` ·
  values ⊆ {0,1} · 0 NaN/Inf inside footprint · NaN everywhere outside · **0 px on the catalogue** ·
  min distance to catalogue 2.24 px (identical to the parent, never reduced) · re-read from disk ·
  **14/14 checks PASS** (zeros twin: 15/15).

### SNAP-2

- **File:** `releases/snap-ridge-lidar2-20261023-6913d029.tif` (fallback `…-6913d029-zeros.tif`)
- **sha256:** `6913d029a6941e0519bedc08d9d839f75afd1fc508dd5406b357fdd8408c1230` (332,766 B, 37,654 dots)
- **Note (126 / 140):**
  `R0 h33-2-b2 SNAP: 22% dots slide <=2px along ridge to peak lidar-scarp response; count/mass fixed; pred +0.001 MODEL; UNSCORED`
- **Change:** 8,384 dots (22.27 %) moved, mean 1.209 px; support coverage −1.4 %. **14/14 PASS** (zeros 15/15).

### SNAP-3

- **File:** `releases/snap-ridge-tmi2-20261023-de094d8e.tif` (fallback `…-de094d8e-zeros.tif`)
- **sha256:** `de094d8e89834cfc571a9d409248a1aa0363e4d0cbd6ea470e44ed07bfedec43` (332,816 B, 37,654 dots)
- **Note (122 / 140):**
  `R0 h33-2-b2 SNAP: 30% dots slide <=2px along ridge to peak TMI-edge response; count/mass fixed; pred 0.000 MODEL; UNSCORED`
- **Change:** 11,412 dots (30.31 %) moved, mean 1.245 px; support coverage −2.3 %. **14/14 PASS** (zeros 15/15).

**Do not spend two SNAP slots in one week.** A SNAP change under ±0.01 is no evidence; the axis is a
bound on position sensitivity, ranked below the PRUNE ladder in `SLOT_PLAN.md`.

## Gates actually enforced by the build scripts

`scripts/gemsdoe85_prune_session.py` (PRUNE): parent pins verified (7 SHA-256) → R0 rebuilt from the
pinned H19-5 skeleton and proven pixel-identical to the pinned parent rasters → each variant proven a
subset of the parent's dot set → 1–50 % change rule → zero mass on the catalogue, ≥ 3 px from it →
written → **re-read from disk** → 14 format checks (NaN encoding; 15 for zeros) → sha256 not already in
the ledger or in any pin. `ALL GATES PASS` is printed only if every variant passes both encodings.

`scripts/gemsdoe85_snap_session.py` (SNAP): the same pins (7) **plus 4 external pins** (lidar scarp,
GeoDAWN extensions, SGMC control, 419 MB feature stack — all SHA-256 verified) → R0 rebuilt and
pixel-identical → for every variant: count and mass unchanged (37,654), displacement ≤ 2 px, no dot
inside 2 px of the catalogue, no dot moved *closer* to it than it already was, minimum separation
≥ 2.0 px, all dots inside the footprint → written → **re-read from disk** → the same 14/15 checks →
sha256 not already in the ledger. The script is **byte-idempotent**: re-running it reproduces the same
`sha8` filenames and refuses to add duplicate ledger rows.

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
- **SNAP (2026-10-23 session):** best single feature **0.5696** (`geod_2ndinv`, 19 bands + the two
  response fields) — **CLEAN**. SGMC off-catalogue control: R0 0.09539, SNAP 0.09396 / 0.09338 /
  0.09591 — **all within ±0.002 of the parent, i.e. no signal**. Label-free *support coverage*
  C(H19-5 skeleton): parent 0.63341, SNAP 0.62456 / 0.61891 / 0.51368 (−1.4 % / −2.3 % / −18.9 %);
  this is the diagnostic the predicted signs come from. **Catalogue hide-and-recover PROXY** is
  reported but is structurally biased for these files (R0 0.00479 → 0.01350): every dot is free to
  move back toward *withheld* catalogue pixels, which the live scorer masks. It is therefore not used
  as evidence for SNAP — see IR-V2-15.

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
