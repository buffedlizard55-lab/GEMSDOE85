> **2026-10-22 safety review:** this shortlist predates merged GEO-Pb, duplex and supervised implementations. Statements below about an empty seed are historical. Method-level novelty must be re-audited; no current lane is assigned and no new experiment is authorized. See [current review](safety-review-2026-10-22.md).

# Research shortlist — proposed, not assigned or tested

Prepared before any geological implementation. **No hypothesis has a HOLDOUT-DTI result.** These are falsifiable proposals, not discovered faults or claimed new global methods. The seed repo implements none; metadata-only review of sibling repos cannot prove that another lane has never tried them. Their cross-lane novelty is **unverified**. Implementation is blocked by the missing lane/cache and the literal uniqueness-saturation certificate, so this is not an invitation to start another lane.

Expected improvement is ranked **qualitatively**; no numerical DTI forecast is justified. Cost means relative CPU/memory engineering cost, not a measured runtime. All proposals use only layers present in the restored core raster; none is made “viable” by assuming an unavailable new external dataset.

## Ranked shortlist

| Priority | Hypothesis | Expected benefit conditional on validation | Implementation cost | Primary non-fault mimic |
|---|---|---|---|---|
| First | Paired basin-interface flexure | Highest research priority: tests buried displacement rather than another surface scarp | Medium: directional profiles and scale selection | Lateral sedimentary facies / erosional basement relief |
| Second | Gravity curvature polarity reversal across a basin shoulder | Moderate: possible independent evidence for a concealed structural step | Medium: multiscale signed profiles and detrending | Unfaulted lithologic density contact |
| Third | Magnetic depth/edge displacement, conditioned on subdued relief | Moderate-to-low: could detect covered continuation not expressed topographically | Medium-to-high: uncertainty and coherent displacement estimation | Intrusive contact / remanent magnetization |
| Fourth | Cross-drainage residual facet discontinuity | Lower: stronger surface evidence but more likely to reproduce known-scarp lanes | High: terrain matching and channel controls | Lake terrace / resistant bedding / fluvial incision |

These priority words are research judgments, not scores or a selected submission. The top candidate must beat a **same-split current incumbent** in shared pooled HOLDOUT-DTI, with paired CI reported, before consideration by a separate selector. At present neither top candidate nor comparable incumbent has been evaluated here.

## First — paired basin-interface flexure

**Specific supplied layers:** `depth_to_base_surf` (band 15), `cond_surf` (17), `iso_grav_anom` (13), with `det_elev` (12) and `det_elev_slope` (19) as nuisance controls. Band identities come from the restored raster audit, not inferred units. The band-15 metadata says basement depth; the official summary describes a conductive base. Resolve this provenance ambiguity before interpreting a fitted scale as a geological thickness.

**Physical signature to test:** for each candidate direction, detrend a depth profile across an edge; seek a persistent signed offset/curvature pair whose gravity profile changes consistently across the same interface. Surface conductivity contrast is supporting evidence, not proof of fault-zone conductivity. Match comparison profiles within elevation/relief strata. Unlike a simple product of edge magnitudes, this hypothesis asks for an **ordered pair of flanks with consistent sign and relative displacement**, allowing the detector to reject a symmetric valley-shaped anomaly.

**Why a missing fault might be recovered:** a structural step under basin fill can affect subsurface proxy fields while lacking an exposed scarp. That makes off-catalogue discovery plausible, not guaranteed; catalogue absence does not itself prove concealment. Predictive features must not use distance to the withheld trace to define profile orientation, scale, or evaluation geometry.

**Difference from inspected work:** the seed repo had no implementation. GEMSDOE32's H33 description includes multiphysics line/orientation consensus; the proposed object is signed paired-flank geometry, not line-strength consensus or H33's post-placement near-catalogue deletion. H32 clay-cap/dip-projection ideas are related, so **cross-repo novelty remains unresolved** and requires the registry surface check. It must not be advertised as new merely because its code is new.

**Falsification/control:** if matched sedimentary basin edges without independent structural evidence produce the same signature, the model is detecting stratigraphy/erosion rather than fault displacement. Compare to a depth-only arm, a gravity-only arm and the fixed incumbent; assess each feature alone for leakage before trusting a combined result. Small missing-value regions or interpolation boundaries can create artificial paired edges.

## Second — gravity curvature polarity reversal

**Layers:** `iso_grav_anom` (13), `iso_grav_anom_vg` (11), `iso_grav_anom_hg` (18), `iso_grav_anom_slope` (5), and detrended terrain (12/19) as controls.

**Signature:** signed second derivatives and directional cross-edge profiles at several physical scales; require an inflection bracketed by opposite curvature lobes, persistent under smoothing, rather than simply selecting the largest gradient. Fit profile scales on training regions only. Treat the derived gravity layers as **one source family**, not independent confirmation.

**Missing-fault rationale:** an intrabasin basement offset may retain a density step even where young sediment removes scarp expression. A density contact can also be wholly unfaulted, so this inference needs heldout evidence.

**Difference:** not a global upward-continuation worm or maximum-gradient ridge; it tests profile polarity/order and uses non-edge controls. No such implementation exists in this seed repo. Broad sibling worm/curvature work makes uniqueness unproven.

**Mimic/falsification:** unfaulted density boundaries, inversion artifacts or regional detrending. Reject if performance is explained by a single raw gradient or survey-edge mask, or disappears when basin/relief strata are held out.

## Third — depth-conditioned displaced magnetic edge

**Layers:** `rtp` (2), `tmi` (14), `tmi_vg` (9), `tmi_hg` (3), `depth_to_base_surf` (15), `det_elev_slope` (19). Do not assume any of these is an independently measured fault probability.

**Signature:** estimate consistent lateral displacement between magnetic edge responses at different smoothing scales, conditioned on the supplied depth proxy and low terrain relief. Require coherent orientation over a track, but do not equate grid-scale changes with a physically inverted dip without an uncertainty model. RTP and TMI are not independent experiments.

**Missing-fault rationale:** a covered continuation could produce a deeper magnetic boundary offset from the surviving surface lineament. This targets evidence that visible-scarp cataloguing could miss, but remanence/source geometry can move magnetic edges without faulting.

**Difference:** proposed measured **edge displacement under scale change**, not another scalar Euler-depth or orientation-consensus rank. Existing sibling Euler/depth lanes are closely related; clearance is not assumed.

**Mimic/falsification:** intrusive contacts, remanent magnetization, interpolation and survey flight-height variation. USGS explicitly warns that variable terrain clearance should be considered when modeling GeoDAWN. If a flight-direction/height proxy predicts detections as well as the geological variables, downgrade the candidate.

## Fourth — cross-drainage residual facet discontinuity

**Layers:** `det_elev` (12), `det_elev_slope` (19), optionally gravity (13) as a separate corroboration arm. No 1 m DEM is assumed available or required for this proposal's first coarse-scale test.

**Signature:** seek a signed terrain-height/slope change that repeats across separate drainage profiles after matching local elevation, aspect and relief. Test discontinuity of aligned residual facets across drainages, not simple straight-valley occupancy or local slope peaks. At the supplied coarse resolution some scarps will be unresolved; that is a limitation, not evidence of absence.

**Missing-fault rationale:** a degraded fault may preserve repeated facet offsets despite losing a continuous scarp. Catalogue completeness/selection bias may instead favor exactly these visible features.

**Difference:** profile-to-profile residual consistency, not H33 valley collinearity or simple LiDAR-scarp thinning. The seed repo implements neither. The many existing scarp/drainage lanes make this the least attractive novelty risk.

**Mimic/falsification:** lacustrine terraces, dipping resistant strata and channel incision. Use matched nonaligned profiles and basin-floor/terrace controls. If the signature follows a constant elevation more closely than a structural trajectory, reject it as a likely shoreline mimic.

## Data viability and sources

- **Available locally, integrity-verified owner mirror:** all named core layers, documented in [`evidence/input_audit.json`](../evidence/input_audit.json). Authentication to original organizer bytes is not established.
- **Official definitions and task:** [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), retrieved 2026-10-22. Supports the feature families and fault-prediction objective, not the success of these hypotheses.
- **Official physics/acquisition caveats:** [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOI](https://doi.org/10.5066/P93LGLVQ), retrieved 2026-10-22. Describes magnetic/radiometric products, processing, varying terrain clearance and flight-path products; marks the work CC0. These details motivate artifact controls, not fault labels.
- **Official baseline:** [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b) uses a U-Net with Monte Carlo patch splits; this is not an endorsement of random-patch validation for this research. The protocol's whole-segment blocked hide-and-recover instrument remains binding.

## Proposed validation design — not executed

Use the template's cached non-catalogue features and shared whole-component splits. Any catalogue-dependent transform gets **only visible faults** for its fold, including profile orientation priors; no saved full-catalogue distances, tip positions or densities are admissible. Never derive the allowed placement region from hidden-fault geometry. Mask non-withheld known pixels exactly, pool additive metric components rather than averaging quadrant ratios, and bootstrap aligned physical spatial clusters with the same truth counts in candidate/control arms. Keep scale tuning and threshold tuning out of outer held regions. Report conditional CI scope and selection bias.

Feature-only AUC canaries are diagnostic stop gates, not the optimization target. Missing features, nodata fill, spatial coverage and source-edge masks must be tested as features too. Final output format checks run only after scientific evidence and uniqueness gates; they cannot make a low-skill model a high-scoring model. No weekly slot is consumed by this shortlist.
