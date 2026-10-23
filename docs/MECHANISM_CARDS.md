# Mechanism cards — AXIS = CONCENTRATION (parent R0 = `h33-h33-2-b2`, 37,654 dots, 0.2778 CLAIM)

Written for a structural geologist. One card per built variant. Every number here is
[MEASURED] on SHA-256-pinned bytes unless labelled otherwise.

## 0. What the parent is, and what "the prior" is

* **Parent R0** = `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`
  (sha256 `c55bafc4…`, 37,654 unit-mass 1-px dots, min dot-to-catalogue distance 2.236 px).
  Its recipe was **rebuilt and confirmed pixel-exact** this session:
  *R0 = `h27-4-solo-d28` (40,199 dots) minus every dot whose Euclidean distance to the
  public catalogue is ≤ 2 px* (2,545 dots removed). The rebuilt raster has identical pixels
  to the pinned file (its sha256 differs only because the pinned file was written with a
  different GeoTIFF byte layout).
* **The prior** = the archived **H19-5 field support** (121,131 cells), i.e. the parent's own
  geophysical/structural field, aggregated to **0.8 km × 0.8 km blocks** (8 × 8 px at 100 m).
  `prior(block) = H19-5 support cells in block / footprint cells in block`.
  The archive stores H19-5 binarised, so the continuous field value is **not** recoverable;
  the ranking used here is the lineage's own nested-set membership plus local support
  density as a monotone proxy → evidence class **MODEL**.
* **Block size and CV definition.** CV = coefficient of variation of dot counts over
  *occupied* blocks. This definition was calibrated against the family's own record: it puts
  the three best files (d2.8 0.2600, h27-4 0.2708, h33-2-b2 0.2778) at **0.541 / 0.547 /
  0.551**, i.e. inside the 0.51–0.59 band quoted in the brief, while the 121,131-cell
  H19-5 field sits at 0.787 (0.1922 CLAIM) and the 206,895-dot lattice at 0.446 (0.0904 CLAIM).
  R0 sits at **0.551 (0.8 km)** / 0.619 (1.0 km).
* **Geometry that constrains everything (measured, decisive):** R0 is a **maximal 300 m
  cover of its own field**. Of the 121,131 H19-5 support cells, only **74** are ≥ 3 px from
  every R0 dot and > 3 px from the catalogue. A concentration that adds *new* 300 m coverage
  inside the strongest structures is therefore **geometrically impossible**; concentration
  can only be bought by doubling up at ≥ 1 px (100 m) offset, which can only sharpen the
  credit kernel, never widen it.

## 1. Variant `conc10` — move 10 % of the dots (3,765) into the highest-prior blocks

* **Hypothesis.** New-fault truth in the hidden label set is not uniformly distributed over
  the parent's field: it is relatively concentrated in the blocks where the H19-5 field is
  dense (i.e. where the multi-physics evidence agrees: aligned gravity/magnetic gradients
  and topographic scarps along the same lineament). If that is true, mass spent on the
  *tips* of weak lineaments is wasted and should be moved into the strongest blocks.
* **Mechanism.** R0's dot density already tracks the field, but its 19,659 occupied 0.8 km
  blocks still include thousands of near-isolated "tip" cells (block prior ≤ 0.016). The
  edit deletes 3,765 such dots (source blocks: prior mean 0.017) and re-places them on
  free cells of the highest-prior blocks (target blocks: prior mean **0.260**, ~2.3× the
  parent-wide dot-weighted prior of 0.115). The share of dots sitting in the top-decile
  prior blocks rises **10.6 % → 20.6 %**; block-density CV rises **0.551 → 0.767**.
  Mean displacement 152 km (median 148 km, p95 295 km).
* **The non-fault process that could mimic it.** The H19-5 field is a *consensus* of
  independent geophysical indicators; a dense block may simply be a place where a
  **lithologic contact or a dike swarm** produces a strong, sharp, multi-indicator
  response without a Quaternary fault at all. Doubling up on such a line converts one
  FP-taxed dot into two, i.e. it doubles the penalty with no new credit.
* **Predicted live change.** **−0.010 to −0.030** against R0's 0.2778 (CLAIM), i.e. a
  *loss*, and the reason is arithmetic, not pessimism: the family's own record pairs
  clustered patterns with low scores (H19-5 field: CV 0.787 → 0.1922 CLAIM) and the least
  clustered dot files with the best scores (CV 0.541–0.551 → 0.2600–0.2778 CLAIM). This
  variant moves the file *towards* the clustered signature that has always scored worst.
  A second, opposite effect could offset it: a doubled dot 1–2 px from a retained dot
  sharpens the triangular kernel on truth that is offset from the parent's lineament
  (GeoDAWN positions are uncertain by ~300 m), and the marginal bar is only
  0.2·DTI/(1−0.2·DTI) ≈ 0.059 of credit per wasted unit.
* **Falsifier.** If the live score of `conc10` is **≥ R0 + 0.01**, then (i) the block-scale
  prior is a *positive* predictor of hidden new-fault truth, and (ii) the CV band quoted in
  the brief is not the causal variable. In that case the 15 % and 20 % arms are promoted
  and the concentration axis becomes the session's headline axis. If the live change is
  within ±0.01, the axis is uninformative at this dose and the family record stands.

## 2. Variant `conc15` — move 15 % of the dots (5,648)

* **Hypothesis / mechanism.** As `conc10`, one step further: 5,648 tips removed
  (source prior mean 0.022), mass re-placed in 1,367 high-prior blocks (target prior mean
  0.243). Top-decile share 10.6 % → 22.1 %; CV **0.551 → 0.786**; mean displacement 143 km.
* **Non-fault mimic.** As `conc10`; at this dose the doubled mass is now the dominant
  pattern in the strongest blocks (≈ 4 extra dots per touched block), so the "consensus
  lineament" is sampled repeatedly and a single systematic mis-mapping (e.g. a magnetic
  contact) is paid several times over.
* **Predicted live change.** **−0.015 to −0.040**. The report-only holdout proxy agrees in
  sign and in ordering: HOLDOUT-DTI falls 0.00401 (R0) → 0.00366, and truth credit
  TPw 129.3 → 117.9. (PROXY, n = 22,663 withheld positives; this instrument is known to
  correlate −0.87…+0.54 with live scores and is never a gate.)
* **Falsifier.** Live ≥ R0 + 0.01 ⇒ same reading as above, with a larger dose. Live ≤
  R0 − 0.02 ⇒ the "clustering costs score" reading is confirmed and the family should stop
  paying slots for concentration-style edits.

## 3. Variant `conc20` — move 20 % of the dots (7,531)

* **Hypothesis / mechanism.** As above, at the brief's upper dose: 7,531 tips removed
  (source prior mean 0.026) and re-placed in 1,940 high-prior blocks (target prior mean
  0.229). Top-decile share 10.6 % → 22.2 %; CV **0.551 → 0.782**; mean displacement 152 km.
* **Non-fault mimic.** As above. At 20 % the variant is, in spatial terms, a partial
  return to the *field* pattern (H19-5 CV 0.787) that scored 0.1922 CLAIM — this is the
  clearest way to state the risk.
* **Predicted live change.** **−0.020 to −0.050**. Report-only proxy: HOLDOUT-DTI 0.00350
  (TPw 112.9), again monotone with dose.
* **Falsifier.** Live ≥ R0 + 0.01 ⇒ the prior is a *positive* predictor and concentration
  should be pushed further (a 30 % arm, then a 40 % arm, are the next pairs to build).
  Live ≤ R0 − 0.02 ⇒ the axis is closed for this parent; the next axis should attack the
  *truth-capture* term T (SNAP / a new detector), not the spatial distribution.

## 4. Why all three arms are predicted to *lose* (the uncomfortable part)

The metric is `DTI = T / (0.2(T+F) + 0.8K)` with `F = S − M` (mass not within 300 m of
truth) and `K` = number of truth pixels. The parent's own arithmetic (from the family's
back-solve) is `T ≈ 5,470`, `K ≈ 14,400`, `F ≈ 35,400`, i.e. **94 % of the parent's mass
is wasted**. Concentrating mass does not change `S`; it changes only *where* the same mass
sits. In the strongest blocks the parent has *already* placed its dots at 300 m spacing, so
the new mass can only be a near-duplicate. A near-duplicate adds `ΔT ≥ 0` (the truth-pixel
maximum can only go up) and `ΔF = 1 − k`, so it is profitable **only** if the doubled
position happens to sit within ≈ 280 m of a truth pixel. In blocks where the parent already
covers the structure, that probability is low; in the weak blocks we just emptied, the
removed dots were the *least* likely to be on truth, so their removal returns little.
The two effects are both small and both unfavourable, which is why the prediction is a
small loss rather than a large one — and why the arms are built as a *dose–response
series*: the slope of live score against dose is the real measurement, not any single point.

## 5. What would make this axis worth more (for the next session)

The three arms test the *distribution* of the parent's mass. They cannot test the
*detector*. The binding constraint is `T` (38 % of hidden truth captured). A variant that
keeps the spatial distribution and improves `T` (e.g. SNAP: move each dot ≤ 2 px onto the
strongest TMI/gravity-gradient/scarp response in its window) attacks the term that the
metric algebra says is worth ≈ +0.048 DTI per 1,000 units of T, while every mass-axis
edit is worth < 0.01.
