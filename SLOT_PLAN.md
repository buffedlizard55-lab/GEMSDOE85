# SLOT_PLAN — 3 scored submissions per rolling week, ONE entity, deadline 2026-12-03 (provisional)

Parent for every candidate: **R0 = `h33-h33-2-b2`** (GEMSDOE32 `e5eb6e7e`, 37,654 dots, live **0.2778
CLAIM** — owner-reported, no receipt in this repository). `TOP_PUBLIC` is **unfilled**: the human must
read it off the leaderboard with a date; no other target number is valid. Remaining slots this rolling
week: **unknown**.

## The decision this session produces

SNAP's predicted effect is **inside the ±0.01 no-evidence band** (cards: +0.001 / 0.000 / −0.004).
A SNAP receipt therefore cannot, by construction, teach us anything unless it moves by ≥0.01. It is
a **bound on position sensitivity**, not a bet on a gain — so it is ranked **below** the PRUNE ladder,
which is the only axis in this lineage with two live/CLAIMed positive steps (+0.0108, +0.0070).

Rule of thumb this implies: **spend a slot on SNAP only if the PRUNE ladder is closed or the slot
would otherwise go unused.** Do not spend two SNAP slots in one week.

## Next 3 slots, in order

| # | upload this file (fallback: the `-zeros` twin) | change vs R0 | what the result would change | prediction (MODEL) |
|---|---|---|---|---|
| 1 | `releases/h33-2-b2-prune3-20261023-fb308615.tif` | drop 2,171 dots at 2 < d_cat ≤ 3 px → 35,483 (−5.77 %) | Δ ≥ +0.005 ⇒ the catalogue-shadow mechanism is alive and rungs 4/5 become the plan; Δ ≤ 0 ⇒ ladder exhausted at 2 px, week 2 switches axis | **+0.007** (+0.001…+0.012) |
| 2 | `releases/h33-2-b2-prune4-20261023-2880b0e9.tif` | drop 3,825 dots at 2 < d_cat ≤ 4 px → 33,829 (−10.16 %) | brackets the optimum: if prune4 ≥ prune3 the shadow is ≥ 400 m and rung 5 is worth the slot; if prune4 < prune3 but > R0 the optimum is bracketed in (3,4) px | **+0.003** (−0.004…+0.010) |
| 3 | `releases/h33-2-b2-prune5-20261023-7ebfc408.tif` | drop 5,637 dots at 2 < d_cat ≤ 5 px → 32,017 (−14.97 %) | spend only if 1 and 2 both scored ≥ 0.2778. A gain means the shadow exceeds the documented 100–400 m offset class and the next session sweeps rungs 5–8 | **−0.003** (−0.012…+0.006) |

### If a slot is free and the ladder is closed — SNAP, in this order

| order | file | what it buys |
|---|---|---|
| 1 | `releases/snap-free-lidar2-20261023-ac3fc128.tif` (57 % moved, coverage −18.9 %) | the **largest** SNAP effect: if position within ±200 m mattered at all, this is where it shows. ≥ +0.01 ⇒ the ridge is misplaced relative to the scarp; ≤ −0.01 ⇒ leaving the ridge is harmful, next spend the on-ridge file |
| 2 | `releases/snap-ridge-lidar2-20261023-6913d029.tif` (22 % moved, coverage −1.4 %) | the *conservative* version of the same idea: along-trace refinement only. Only informative after #1 shows an off-ridge cost |
| 3 | `releases/snap-ridge-tmi2-20261023-de094d8e.tif` (30 % moved, coverage −2.3 %) | the only variant that tests the 400 m *aeromagnetic* positional story directly; a loss demotes all magnetic-gradient axes |

Live changes under 0.01 are **no evidence** (public chunks only; the private chunks plus the Phase-2
expert-expanded labels may differ). Every live result needs a submission-page RECEIPT. Catalogue and
SGMC results are PROXY and never a promotion gate. Never schedule an exact repeat for another score.

## Calendar (deadline provisional, human must confirm)

- **wk 1 (Oct 23–29):** slots 1–3 above, rolling week permitting. Keep one slot in reserve if the
  account shows fewer than three left.
- **wk 2 (Oct 30–Nov 5):** if PRUNE is alive, combine the winning rung with one non-PRUNE axis at a
  time (predicted Δ ≥ +0.005, else do not spend a slot). If PRUNE is flat, spend one slot on
  `snap-free-lidar2` as the position bound and keep two in reserve.
- **wk 3 (Nov 6–12):** the best combination, one change at a time; re-validate both encodings of the
  incumbent file.
- **wk 4–5 (Nov 13–26):** confirm the winner on fresh proxies, choose the final file and one fallback,
  re-validate both formats with `scripts/gemsdoe85_snap_session.py` / `..._prune_session.py`.
- **wk 6 (to Dec 3):** freeze. One blind final submission; no geometry changes after the last receipt.
- **41 calendar days** remain from Oct 23 to Dec 3; the deadline and timezone are not independently
  confirmed — the human checks https://www.drivendata.org/competitions/306/competition-doe-gems/ .

## Better axes for later sessions — proposed, NOT built, NOT assigned

1. **MASS-UP on scarp response, off-catalogue.** This session measured, without labels, that the lidar
   scarp field is *higher* near the known catalogue than the parent's own dots are (the catalogue
   hide-and-recover proxy rises from 0.0048 for R0 to 0.0135 for `snap-free-lidar2` purely from dots
   moving toward mapped faults). That is evidence the field is a fault-likelihood surface; the
   unspent question is whether *adding* dots at its maxima where `d_cat > 5 px` pays the 0.2 FP charge
   back. Confounder: additions have failed live before (T-v2, 1,259 dots, −0.0028) and the earlier
   failures were also off-ridge. Falsifier: matched-count random additions must lose by ≥ 0.01.
2. **PRUNE-EXCHANGE** (carried over from the previous session): same count as R0, but the dots removed
   from the catalogue shadow are moved along strike into `d_cat > 5 px` segments, at fixed mass.
   Falsifier: a matched-count random-relocation control must score worse by ≥ 0.01.
3. **RELIEF terciles.** Shift 10–15 % of mass between basin / piedmont / range-front terciles
   (`det_elev`), count fixed. Confounder: range-front concentration can be a survey-coverage artefact.
   Falsifier: sign flips inside the lidar-covered subset.
4. **CONCENTRATION at 1 km blocks — direction unresolved.** R0's occupied-block density CV is **0.619**
   (10-px blocks, median 2, p95 5 dots/block), *above* the 0.51–0.59 band the brief attributes to the
   best files. The brief's CONCENTRATION moves mass toward high-prior blocks, which would raise CV
   further; the observation suggests de-concentration instead. Do not build until the direction is
   settled, and note the band is confounded with file naming (mass is confounded with field).
5. **SPACING at matched count** on the pruned geometry: the parent's mean nearest-neighbour distance is
   **2.828 px**; SNAP incidentally raised it to 3.51–3.61 px at identical count, which is a free
   spacing experiment already in the ledger's files if a receipt ever contrasts them.

## What this session did *not* do, on purpose

No submission of any kind, no leaderboard access, no new heavy data beyond the pinned inputs, no
combination of two axes in one file, no MASS/CONCENTRATION/RELIEF build (each needs either its own
direction decision or the 419 MB stack's detrended elevation), and no site redesign.
