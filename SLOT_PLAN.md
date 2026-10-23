# SLOT_PLAN — 3 scored submissions per rolling week, ONE entity · deadline 2026-12-03 (provisional)

**State (2026-10-23).** Parent R0 = `h33-h33-2-b2` (GEMSDOE32 `e5eb6e7e`, 37,654 dots, rebuilt
pixel-identical to its pins). `0.2778` is a **CLAIM**, not a receipt. `TOP_PUBLIC` (with date), the
incumbent receipt, the rolling-week slot count and a confirmed deadline/timezone are **all still
missing** — the human reads them off the leaderboard/account page. The brief leaves AXIS to the human;
no answer has been received (the question was asked and skipped, IR-V2-14). Two build sessions therefore
exist — three PRUNE rungs and three SNAP variants — and **none of them is authorized or scored**. Every
file below is `BUILT`, `receipt = N`.

**The one rule that outranks the ordering below:** a live change under **0.01** is no evidence (public
chunks only; the private chunks and the Phase-2 expert-expanded labels may differ). Do not spend a slot
on an experiment whose predicted effect is inside that band unless it is the only way to close a branch.

## Next 3 slots — only if the human confirms AXIS = PRUNE and the quota permits

| # | upload (fallback: the `-zeros` twin) | change vs R0 | prediction (MODEL) | what the result changes |
|---|---|---|---|---|
| 1 | `releases/h33-2-b2-prune3-20261023-fb308615.tif` | drop 2,171 dots at 2 < d_cat ≤ 3 px → 35,483 (−5.77 %) | **+0.007** (+0.001…+0.012) | Δ ≥ +0.01 ⇒ the catalogue-shadow mechanism is alive and rungs 4/5 become the plan; Δ ≤ 0 ⇒ the ladder is exhausted at 2 px and the axis budget moves on |
| 2 | `releases/h33-2-b2-prune4-20261023-2880b0e9.tif` | drop 3,825 dots at 2 < d_cat ≤ 4 px → 33,829 (−10.16 %) | **+0.003** (−0.004…+0.010) | brackets the shadow width: if prune4 ≥ prune3 the shadow is ≥ 400 m and rung 5 is worth a slot; if prune4 < prune3 but > R0 the optimum sits in (3,4) px |
| 3 | `releases/h33-2-b2-prune5-20261023-7ebfc408.tif` | drop 5,637 dots at 2 < d_cat ≤ 5 px → 32,017 (−14.97 %) | **−0.003** (−0.012…+0.006) | spend only if 1 and 2 both scored ≥ 0.2778; a gain means the shadow exceeds the documented 100–400 m class and the next session sweeps rungs 5–8 |

Each has a `-zeros.tif` encoding twin; upload **one** encoding per slot. No exact-hash or
`(parent, axis, value)` repeat — the ledger already contains at least eight wasted exact repeats from
earlier sessions. PRUNE's requested count-preserving refill was measured **infeasible** on the parent's
residual ridge at the same 2.8 px rung (611/577/469 candidate pixels vs 2,171/3,825/5,637 dots removed;
`evidence/session_prune_receipt.json → refill_capacity`, IR-V2-09): the candidates are removal-only and
that limitation must be accepted before choosing PRUNE.

## If a slot is free and the PRUNE ladder is closed — SNAP, in this order

SNAP's predicted effect is **inside the ±0.01 no-evidence band** (+0.001 / 0.000 / −0.004). It is a
**bound on position sensitivity**, not a bet on a gain, so it ranks below PRUNE. Spend **at most one**
SNAP slot in a week.

| order | file | what it buys |
|---|---|---|
| 1 | `releases/snap-free-lidar2-20261023-ac3fc128.tif` (56.9 % of dots moved ≤2 px, support coverage −18.9 %) | the **largest** SNAP effect: if position within ±200 m mattered at all, it shows here. ≥ +0.01 ⇒ the ridge is misplaced relative to the scarp; ≤ −0.01 ⇒ leaving the ridge is harmful, and the on-ridge file becomes the refined test |
| 2 | `releases/snap-ridge-lidar2-20261023-6913d029.tif` (22.3 % moved, coverage −1.4 %) | along-trace refinement only; informative mainly after #1 shows an off-ridge cost |
| 3 | `releases/snap-ridge-tmi2-20261023-de094d8e.tif` (30.3 % moved, coverage −2.3 %) | the only variant that tests the 400 m *aeromagnetic* positional story directly; a loss demotes every magnetic-gradient axis |

Catalogue and SGMC results are PROXY and never promotion gates. The catalogue hide-and-recover PROXY is
**biased** for these files and is not evidence (IR-V2-15). Never schedule an exact repeat for another
score.

## Calendar (deadline provisional, human must confirm)

- **wk 1 (Oct 23–29):** only the first candidate, after the human confirms axis, `TOP_PUBLIC`, quota and
  the incumbent receipt. Keep one slot in reserve if the account shows fewer than three left.
- **wk 2 (Oct 30–Nov 5):** if PRUNE is alive, combine the winning rung with one non-PRUNE axis at a time
  (predicted Δ ≥ +0.005, else do not spend). If PRUNE is flat, spend one slot on `snap-free-lidar2` as
  the position bound and keep two in reserve.
- **wk 3 (Nov 6–12):** the best combination, one change at a time; re-validate both encodings.
- **wk 4–5 (Nov 13–26):** confirm the winner on fresh proxies, choose the final file **and** one fallback,
  re-validate both formats (`scripts/gemsdoe85_prune_session.py`, `scripts/gemsdoe85_snap_session.py`).
- **wk 6 (to Dec 3):** freeze. One blind final submission; no geometry changes after the last receipt.
- **41 calendar days** remain from Oct 23 to Dec 3, not six full weeks. Deadline and timezone are not
  independently confirmed; the human checks
  https://www.drivendata.org/competitions/306/competition-doe-gems/ . Quota per
  https://docs.nlr.gov/docs/fy26osti/96647.pdf (not fetched by this session).

## Better axes — proposed, NOT built, NOT assigned

1. **MASS-UP on scarp response, off-catalogue.** Measured without labels this session: the lidar scarp
   field scores *higher* near the known catalogue than the parent's own dots do (the catalogue
   hide-and-recover proxy rises 0.0048 → 0.0135 for `snap-free-lidar2` purely from dots moving toward
   mapped faults), i.e. the field is a fault-likelihood surface. The unspent question is whether adding
   dots at its maxima where `d_cat > 5 px` pays back the 0.2 FP charge. Confounder: additions have
   failed live before (T-v2, 1,259 dots, −0.0028). Falsifier: matched-count random additions must lose
   by ≥ 0.01.
2. **PRUNE-EXCHANGE.** Same count as R0, but the dots removed from the catalogue shadow are moved along
   strike on the parent's own ridge into `d_cat > 5 px` segments at fixed mass. Mechanism: exchange
   isolates position from mass. Confounder: it re-seeds the packing. Falsifier: a matched-count
   random-relocation control must score worse by ≥ 0.01.
3. **RELIEF terciles.** Shift 10–15 % of mass between basin / piedmont / range-front terciles
   (`det_elev`), count fixed. Confounder: range-front concentration can be a survey-coverage artefact
   (lidar footprint edge). Falsifier: the sign flips inside the lidar-covered subset.
4. **CONCENTRATION at 1 km blocks — direction unresolved.** R0's occupied-block density CV is **0.619**
   (10-px blocks, median 2, p95 5 dots/block), *above* the 0.51–0.59 band the brief attributes to the
   best files; the brief's direction (toward high-prior blocks) would raise CV further. Do not build
   until settled; then run it two-sided at matched CV distance (IR-V2-17).
5. **Cross-physics strike agreement**, matched count/ranking strata: independent magnetic/gravity
   boundary alignment may separate faults from lithologic contacts. Falsifier: ≥ 0.01 receipt loss
   despite increased agreement; smaller changes are inconclusive.
6. **Persistence versus closed edges**, matched count/relief: favour kilometre-scale open,
   strike-consistent boundaries over closed rims. Confounder: shorelines and lava margins persist too.
   Falsifier: no ≥ 0.01 receipt gain and no improved blind geological evidence on reviewed traces.
7. **SPACING at matched count** on the pruned geometry: the parent's mean nearest-neighbour distance is
   **2.828 px**, and SNAP incidentally raised it to 3.51–3.61 px at identical count — a free spacing
   contrast already sitting in the ledger if those receipts ever exist. Lowest priority; partly
   duplicates the PRUNE dose ladder.

## What these sessions did *not* do, on purpose

No submission of any kind; no leaderboard or competition-page access; no credentials; no combination of
two axes in one file; no MASS/CONCENTRATION/RELIEF build; no site redesign. Builds are unspent until the
human confirms the axis and the quota.
