# Mechanism cards — AXIS = SNAP on parent R0 (`h33-h33-2-b2`)

Written for a structural geologist. Every number here is reproducible from
`scripts/gemsdoe85_snap_session.py` (receipt: `evidence/session_snap_receipt.json`) on the pinned
inputs in `registry/data_manifest.json`. Live scores are CLAIMs; proxies are PROXYs; predictions are
MODELs. Nothing here is an organizer score.

## The rule the three variants share

Each of the parent's 37,654 unit-mass dots is an independent decision. In a window of radius ≤ 2 px
(≤ 200 m) around its parent position, the dot looks for the **strictly higher** value of a
*pre-declared* response field and takes the best admissible destination. Admissibility is checked
before the response is compared:

1. the destination is inside the scored footprint;
2. `d_cat(destination) ≥ max(3 px, d_cat(parent position))` — a dot may never move closer to the
   known-fault catalogue, so the brief's zero-mass-on-catalogue and 3-px rules can only improve;
3. no other dot ends up strictly within 2.0 px of it (separation floor; parent packing is 2.8 px).

Count and mass are unchanged: 37,654 dots before and after, each 1.0. Dots with no strictly better
admissible destination stay where they are. The assignment is deterministic (gain-descending,
raster-index tie-break, no RNG), and re-running the script reproduces byte-identical GeoTIFFs.

**Response fields** (fixed before any score existed; no tuning to the catalogue):

* **Lidar scarp** — mean of `step_max`, `lapneg_max`, `downface_max` from
  `data/external/lidar_scarp_features_u8.tif` (owner-derived from USGS 3DEP 1 m DEM; uint8), masked
  by the file's `valid` band. Coverage: 75.4 % of the footprint, 76.4 % of the parent's dots.
* **TMI edge** — |∇ TMI_up150| after σ = 1.5 px Gaussian smoothing, scaled by its 99th percentile,
  from `data/external/geodawn_extensions_u8.tif` (USGS GeoDAWN, DOI 10.5066/P93LGLVQ). Coverage:
  99.9 % of the footprint.

**Instrument used to set the predicted sign** (label-free, no truth, no score): *support coverage*
`C(skeleton) = mean over the parent's own 121,131-px H19-5 skeleton of max_j k(x − d_j)`. That is
literally the kernel term the metric reads at a truth pixel, evaluated on the parent's own support
estimate. Parent = **0.63341**.

---

## Card 1 — `snap-ridge-lidar2` (on-ridge, ≤ 2 px, lidar scarp)

* **File** `releases/snap-ridge-lidar2-20261023-6913d029.tif` (sha256 `6913d029…`, 37,654 dots,
  **22.27 %** of dots moved, mean displacement of movers **1.209 px**, 3,350 candidate moves refused
  by the separation floor).
* **Hypothesis.** The H19-5 ridge is the right structure at 100 m scale, but the *sample points* along
  it are arbitrary: the parent's own priority ordering is a raster sweep, not a geological ranking.
  Where the scarp is best expressed the dot should sit, because DTI pays a dot's full unit mass only
  when it is within ~1 px of truth and decays linearly to zero at 3 px.
* **Mechanism.** A scarp is a step + convex-up break + down-slope-facing escarpment. Fresh, well
  preserved fault segments show all three; degraded or buried segments show none. Sliding 1–2 px
  *along* the mapped trace changes the dot's position on the same structure (so coverage of the
  parent support falls only 1.4 %), while the chance that a truth pixel lies within 1 px rather than
  2–3 px rises. Mass, and therefore the 0.2-weighted false-positive charge, is unchanged.
* **Non-fault process that could mimic it.** Anthropogenic linear features (roads, fence lines,
  canals, stock tanks) in the 1 m DEM; lava-flow margins; shoreline terraces around the pluvial lakes;
  and DEM tile seams. In basin fill the step/convexity response is dominated by channel banks, so the
  basin-floor dots are the ones most likely to be pulled onto a non-fault edge.
* **Predicted live change (MODEL).** **+0.001** (band −0.006 … +0.008). Prior is near zero because the
  move is small (22 % of dots, 1.2 px) and the parent support is only 1.4 % less well covered.
* **Falsifier.** A receipt loss of ≥ 0.005 kills along-trace refinement; a gain ≥ +0.01 would show
  that sub-kernel *position*, not mass or coverage, is the lever, and would justify re-running the
  whole lineage with the response field as the dot placer.

## Card 2 — `snap-ridge-tmi2` (on-ridge, ≤ 2 px, TMI edge)

* **File** `releases/snap-ridge-tmi2-20261023-de094d8e.tif` (sha256 `de094d8e…`, 37,654 dots,
  **30.31 %** moved, mean displacement of movers **1.245 px**, 4,533 refusals by the separation floor).
* **Hypothesis.** If the ridge's along-strike position is uncertain *because* it was built from
  400 m-spaced aeromagnetic/radiometric lineaments (GeoDAWN Area 2), then the independent physics —
  the upward-continued magnetic edge — should re-centre the dot where the magnetic contrast is
  sharpest. This is the variant that directly tests the brief's stated positional-uncertainty
  mechanism, since the 400 m line spacing is a property of the *aeromagnetic* survey, not of the
  lidar DEM.
* **Mechanism.** Same as card 1 but the pull is toward a magnetic gradient maximum. If a fault is a
  magnetite-destroying or magnetite-introducing structure, the gradient peak sits on the structure.
* **Non-fault process that could mimic it.** The dominant TMI gradients in the Basin & Range are
  *lithological contacts* — basin fill against volcanic or Precambrian rock — not faults. A contact is
  not a fault trace; a dot snapped onto a contact can end up 1–2 px off the structure with no
  compensating credit. This is the most likely failure mode and the reason the prediction is not
  positive.
* **Predicted live change (MODEL).** **0.000** (band −0.008 … +0.008). Support coverage 0.61891
  (−2.3 % vs parent).
* **Falsifier.** |Δ| ≥ 0.01. A *loss* would identify the magnetic edge as a contact proxy for this
  grid — a result worth keeping, because it also demotes any future magnetic-gradient axis. A gain
  would mean the ridge is systematically offset from the magnetic edge and should be rebuilt on it.

## Card 3 — `snap-free-lidar2` (free window, ≤ 2 px, lidar scarp) — the brief-literal control

* **File** `releases/snap-free-lidar2-20261023-ac3fc128.tif` (sha256 `ac3fc128…`, 37,654 dots,
  **56.94 %** moved, mean displacement of movers **1.493 px**).
* **Hypothesis.** The strongest form: the scarp response locates the fault better than the ridge does,
  so a dot should be allowed to leave the mapped trace entirely within the 2-px window.
* **Mechanism.** Identical pull to card 1 with the confinement removed. It is the *control*: same
  field, same cap, only the confinement differs, so the pair (free − on-ridge) isolates the cost of
  leaving the parent support.
* **Non-fault process that could mimic it.** As card 1, plus the liberty to jump onto any nearby
  strong edge (roads, lake terraces, canyon rims). Support coverage falls **18.9 %** (0.63341 →
  0.51368); 56.9 % of the dots move (never more than 2 px, by construction) and the result is no
  longer a subset of the ridge, so this is the variant that can measurably *lose*.
* **Predicted live change (MODEL).** **−0.004** (band −0.012 … +0.004).
* **Falsifier.** ≥ +0.005 would be a strong result: it would mean the H19-5 skeleton is
  *systematically* offset from the scarp response, i.e. the whole lineage has been drawing the trace
  in the wrong place — a bigger finding than any mass edit. ≤ −0.01 closes the "scarp beats ridge"
  branch and retires the free-window form of SNAP.

---

## What the three cards jointly decide

| receipt pattern | reading | next build |
|---|---|---|
| all three within ±0.01 | position within ±200 m of the ridge is not a lever; the lineage's remaining headroom is mass/coverage, not geometry | do not build SNAP again; spend on PRUNE rungs and PRUNE-EXCHANGE |
| free < on-ridge by ≥ 0.01 | leaving the ridge is harmful; confinement matters | keep SNAP-on-ridge as a refinement of the final file, combine with the winning PRUNE rung |
| free ≥ on-ridge ≥ +0.01 | the ridge is misplaced relative to the scarp | rebuild the skeleton on the scarp response (Phase-2 TRACKB style), not a dot edit |
| TMI ≥ lidar + 0.01 | the magnetic edge, not the DEM scarp, is the better locator | propose a magnetic-gradient axis (new session, human-assigned) |

**Evidence status.** All three are predictions with no receipt. The live-change floor is 0.01 (public
chunks only); a receipt inside ±0.01 is *no evidence* about the private chunks or the Phase-2
expert-expanded labels, and must be recorded as such.
