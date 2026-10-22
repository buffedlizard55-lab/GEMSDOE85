# Five candidate geological hypotheses (Lane H85) — ranked before any results

Evidence classes: **[OFFICIAL]** organizer/USGS source · **[MEASURED]** computed in
this checkout from sha256-pinned bytes · **[ORGANIZER-CONFIRMED]** score copied
from the brief's submission-page receipts · **[CLAIM]** unverified report.

Fleet context that constrains novelty: the registry in the brief contains ~60 scored
files. The organizer-confirmed leaders are all emissions of one multi-physics ridge
family (H19-5 → d1.5 0.2477 → d2.8 0.2600 → h33-2-b2 0.2778). Pure single-physics
novelties scored far lower (lidar-scarp dotted 0.0430–0.1461, HGB top-k 0.0286–0.0424,
hydro-conduit fusion 0.0558, Radon piedmont 0.0669–0.1627, Euler threads 0.0355–0.0984).
In the template repo (GEMSDOE32, `evidence/h33_holdout.json`) the label-free
orientation/drainage/scarp surfaces scored catalogue-holdout DTI 0.019–0.034 against
the d2.8 control's 0.098 — **[MEASURED]** there. Any new candidate must therefore be
judged against the control on the same instrument, which is what this repo does.

| rank | id | layers (official band names) | physical signature | why it should catch a catalogue-missing fault | differs from prior fleet code | non-fault mimic (named) | cost | data |
|---:|---|---|---|---|---|---|---|---|
| 1 | **H85-A fold-proper supervised detector** | all 19 official bands + template derived channels (curvature, Hessian ridges, relief, top-hat, potential-field edges, structure-tensor coherence/strike) + LiDAR scarp u8 (12) + GeoDAWN rad u8 (4) + extensions u8 (4) | HistGradientBoosting probability that a pixel lies on a fault trace, trained per spatial fold on *visible* faults only, with **no catalogue-derived channel** (no distance-to-catalogue, the fleet's known AUC-1.0 leak); emitted by metric-exact max-coverage greedy | The catalogue is demonstrably incomplete (official problem statement: expert-labelled new faults exist). A detector trained on what mapped faults *look like* across all physics generalises to unmapped traces with the same expression; fold-proper training + whole-segment holdout measures exactly that transfer | Prior HGB files (6GEMSDOE 0.0286, GEMSDOE43 0.0424) used top-k/threshold emission; no fleet file combines fold-proper segment-blocked training, support-confined max-coverage emission, and the ≤2 px catalogue-halo prune at the 37,654-dot operating point | Young alluvial / cultural lineaments (roads, canals, field boundaries) that share multi-physics line expression with faults | ~15 min CPU | none (all hash-pinned in-repo mirrors) |
| 2 | **H85-B multi-physics orientation consensus** | `det_elev`, `rtp`, `tmi`, `iso_grav_anom`, `cond_surf` | Both-polarity Hessian line response per physics × orientation order parameter R = \|mean w·e^{2iθ}\|; a pixel scores only if independent physics agree a line exists *and* agree on strike | Single-dataset mapping under-represents faults that are weak in every field but *coherently oriented* in several | Template H33-A implemented this surface but it was never emitted alone at the winner's operating point with halo prune, and never scored by an organizer; this is its first protocol-holdout emission test here | Lithologic contact trains / shorelines straight in several fields at once | ~2 min CPU | none |
| 3 | **H85-C strain-gated lineament** | `geod_dilaterate`, `geod_2ndinv`, `geod_shearrate` (gate) × Hessian lines of `det_elev`, `rtp` | Line geometry re-weighted by a smooth geodetic-strain gate (0.30 + 0.70·(0.5·dilatation⁺ + 0.3·second-invariant + 0.2·shear), robust-normalised) | Catalogue faults include fossil structures; a *currently extending* blind fault should sit where dilatation is locally high AND a line exists. The strain bands are too smooth to locate a fault (fleet-measured: seismic/strain bands are ~constant at 300 m) — here they only re-rank line geometry | No fleet lane uses the geodetic strain tensor invariants as a *gate* on line emission (sarnnpu/wing-crack lanes model tilt/wing geometry, not a dilatation gate) | Basin-range range fronts inside a broad regional dilatation high (gate promotes a whole front) | ~1 min CPU | none |
| 4 | **H85-D collinear thermal-spring chains** | GDR 1391 wellspring points (in-footprint CSV, hash-pinned): thermalclass, temp_c, geothermometers; `row/col` | Directional point-process line support: for each pixel, max over 16 orientations of thermally-weighted spring density along a 2 km line; require ≥3 collinear warm/hot points | Geothermal upflow rises along permeable fault conduits; aligned warm springs are a *direct* vent indicator that raster-only detectors ignore, and blind faults under playa cover may show springs without any scarp | GEMSDOE71 fused springs into a multi-modal stack (0.0558 ORGANIZER-CONFIRMED) but no lane emits *pure collinear spring-chain* support; would need the point table only | Spring lines along valley floors / playa margins / irrigation-well alignments along roads | ~10 min CPU | present (GDR 1391 mirror, sha256-pinned) — **not run: budget = 3 experiments** |
| 5 | **H85-E volcanic-vent alignment** | GDR volcanic vents CSV (672 B in-footprint extract) + `det_elev` | Vent-point collinearity (as H85-D) intersected with topographic line response | Monogenetic vent alignments mark deep crustal fractures that feed geothermal systems | No fleet lane uses vent alignments | Vent chains along a single eruptive fissure that is not a through-going fault | ~10 min CPU | present but sparse (tens of points) — **not run: sparse + budget** |

**Decision rule (declared in advance):** promote the best experiment only if its
pooled HOLDOUT-DTI (`gems85-pooled-hide-v1`, 24,885 withheld positives across
8 cells) beats the best registry control scored on the identical holdout *and*
the uniqueness gate passes. Otherwise the verdict is **negative** and the file is
labelled DO NOT SUBMIT — a negative result is a deliverable.

**External-data candidates considered and rejected as not-ready:** sub-km USGS
FDSN seismicity lineaments — source is free/official
(https://earthquake.usgs.gov/fdsnws/event/1/query) but egress from this sandbox
is restricted to github/pypi hosts (verified in the template repo; re-verified
here by the restore path using only `gh api`), so it is named, not proposed as viable.
