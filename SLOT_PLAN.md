# SLOT PLAN — GEMSDOE85, axis CONCENTRATION (parent R0 = `h33-h33-2-b2`, 0.2778 CLAIM)

**Slots left this week: UNKNOWN (human to confirm; 3 scored submissions per rolling week for
one entity).** **TOP_PUBLIC: UNKNOWN (human to fill; the 2026-10-22 brief quotes 0.3195 as
the leader on a 2026-10-03 snapshot and 0.4413 as a later number — neither is a target
until the human pastes a dated read).** Deadline 2026-12-03 (to be confirmed on the
competition page; not fetched here — DrivenData ToS ban automated access).

## The next three slots, in order

| # | file to upload | what it tests | what the result changes |
|---|---|---|---|
| 1 | `releases/gems85-h33-h33-2-b2-conc10-20261023-f89e4659-zeros.tif` | 10 % of R0's dots moved from the lowest-prior 0.8 km blocks into the highest-prior ones (CV 0.551 → 0.767) | If live ≥ **0.2778 + 0.01**, the block prior is a *positive* predictor of hidden new-fault truth: promote `conc15`, build a 30 % arm, and make concentration the headline axis. If live is within ±0.01, the dose is too small to read and the axis is uninformative. If live ≤ **0.2778 − 0.02**, the "clustering costs score" reading is confirmed and the family stops paying slots for distribution edits. |
| 2 | `releases/gems85-h33-h33-2-b2-conc15-20261023-45bfb93b-zeros.tif` | same axis, 15 % dose (CV → 0.786) | Together with slot 1 this gives the *slope* of live score against dose. A monotone decline confirms the dose–response reading; a rise at 15 % after a fall at 10 % says the effect is non-monotone and the 10 % arm was noise. |
| 3 | `releases/gems85-h33-h33-2-b2-conc20-20261023-a93e0b41-zeros.tif` | same axis, 20 % dose (CV → 0.782) | Confirms or breaks the monotone reading at the brief's upper dose. This is also the archive-quality arm: it is the variant whose spatial signature most resembles the H19-5 field (CV 0.787, 0.1922 CLAIM), so a large loss here is the cleanest possible refutation of "concentrate the mass". |

**Blind choice.** The three files are a dose series of one axis, deliberately: the slope is
the measurement. If only one slot survives, submit **conc10** — it is the smallest
departure from the incumbent, so the downside is bounded and the information per unit of
risk is highest.

**Not submitted, and why.** The three NaN-outside twins (`.tif` without `-zeros`) are the
spec-literal encodings (published spec: null outside the footprint) but the repo's shared
validator rejects NaN pixels and the *incumbent itself* is a zeros-outside file, so the
zeros twins are the proven-submittable encoding. See `docs/SUBMIT.md`.

## Weeks to the deadline (2026-12-03)

* **wk 1 (this week) — submit the three CONCENTRATION arms** above, one per slot, and
  paste the three receipts into `ledger/submissions.csv` (`receipt_score`, `receipt_date`).
* **wk 2 — the pivot.** Whatever the slope says, wk 2 moves to the term that the metric
  algebra says is worth ~+0.048 DTI per 1,000 units of truth credit `T`: **SNAP**
  (move each dot ≤ 2 px onto the strongest TMI / gravity-gradient / scarp response in its
  window, same count, same exclusions). The 57-channel stack and the shared edge channels
  already exist in this repo (`src/gems85/features.py`: `tmi_edge`, `rtp_edge`, `grav_edge`,
  `tophat2`, `ridge_s1..s3`); it needs the 419 MB competition feature stack restored
  (`scripts/restore_data.py --groups core`, 5 pinned parts).
* **wk 3 — PRUNE arms, if and only if SNAP is not yet read.** Exclusion radius 3 px
  (the metric's own 300 m kernel radius) with the count held at 37,654; the family record
  says the 2 px prune was worth +0.0070 live, and R0 still carries 2,171 dots in the
  2–3 px flank annulus. The refill pool is thin (74 legal cells at ≥ 3 px), so a PRUNE=3
  arm must refill from the 1–2 px shell and the arm is a *net* edit, not a pure delete.
* **wk 4 — combine the two axes that actually moved the score**, re-validate both files'
  format, and pick the final candidate plus a fallback.
* **wk 5 — re-validate** the chosen file and the fallback from disk (format gate, zero
  catalogue mass, sha256 not already in the ledger), write the final note, and stop.
* **wk 6 (to 2026-12-03) — buffer** for the Phase 2 brief (rules require reproducible code,
  one final file, and generative-AI disclosure) and for the `TRACKB` deliverable
  (strike-consistent traces ≥ 1 km as GeoJSON + raster, one evidence paragraph per trace)
  if the human opens it. TRACKB is *not* a weekly-slot candidate until the human says so.

## Axes proposed for later sessions (not built this session)

1. **SNAP** — hypothesis: the parent's dot positions inherit the ~300 m positional
   uncertainty of 400 m-spaced GeoDAWN lineaments, so a ≤ 2 px nudge to the strongest
   local edge/scarp response raises per-dot truth credit. Confounder: the strongest edge
   may be a lithologic contact or a dike, not a fault. Falsifier: live change within
   ±0.01 at matched count ⇒ the parent's positions were already at the local optimum.
2. **PRUNE=3** — hypothesis: the 300 m kernel radius means dots at 2–3 px from a mapped
   fault pay the full α=0.2 false-positive tax while capturing no new-fault credit.
   Confounder: new-fault truth *can* lie within 300 m of known traces (organiser forum
   11536), so the annulus is not provably empty. Falsifier: live score rises after
   pruning ⇒ the annulus carries real credit and the 2 px prune was over-fitted.
3. **T-RETRACE** (new, proposed here) — hypothesis: R0's 37,654 dots are a maximal 300 m
   cover of a 121,131-cell field, so the field's *unreached* cells are the cheapest
   unexplored truth; emit the ~74 legal ≥ 3 px cells as a small add-on and see whether
   marginal credit beats the 0.059 bar. Confounder: only 74 cells exist, so the arm has
   almost no statistical power; its value is as a bound on the "coverage is exhausted"
   claim. Falsifier: live change within ±0.01 ⇒ coverage is saturated and any future gain
   must come from a *better detector*, not from a different thinning of this field.
