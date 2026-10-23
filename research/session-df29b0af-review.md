# Review — 2026-10-23, arena/df29b0af-gemsdoe85

## Decision first

**BLOCKED — DO NOT SUBMIT.** No new raster was generated, no geological experiment was run, and no weekly slot was selected or used. This is a negative protocol preflight, **not evidence against a geological hypothesis**. The user's requested unique submission remains unmet; inventing a file, using a prior, changing thresholds, or picking a lane would not meet it.

This review implements the first dependency in prior safety reviews: reconcile merged promotion claims with the standing literal protocol. `AGENTS.md`, `registry/lane.json` and `registry/cache_manifest.json` remain binding. They record no assigned method paragraph and no pinned transformed cache. The prompt again supplies no explicit single-method assignment. A paragraph self-declared in `geopb.py` is not an assignment by the protocol owner.

## Verified locally, versus historical claims

- `scripts/restore_learning.py` fetched the educational H33 TIFF and the dense prior through GitHub at their manifest-pinned commits. Their bytes match SHA-256 pins; this is owner-mirror consistency, not organizer authentication.
- The unchanged shared `gems57.uniqueness.saturation_certificate` was executed after verifying **all** shared-file hashes and reference input hashes. The fresh result is embedded in `evidence/run_card.json`.
- **REGISTRY-MEASUREMENT, not a DTI score:** the witness has positive support across all footprint cells, and its three-pixel halo covers every allowed off-catalogue pixel. Every nonempty allowed prediction has forward overlap 1.0, exceeding the literal 0.70 gate. This proves the overlap obstruction without manufacturing a candidate. A rank correlation for a nonexistent candidate is undefined and is left null. There is no claim that the full registry has been compared.
- Historical TIFFs in both `docs/downloads/` and `submissions/` are reopened and checked against the sample using the pinned shared validator. Exact affine transform, CRS, shape, band count, dtype, footprint, finite values and [0,1] range are checked. Failed NaN-exterior variants remain historical artifacts, not recommended uploads. Every historical row has `safe_to_submit: false` even if its format passes.
- The required transformed cache and raw `training_features.tif` are absent in this checkout. Raw data is not the transformed cache. Restoring hundreds of MB of unused inputs cannot remove the missing assignment or proven overlap obstruction, so no feature cache was rebuilt.
- `registry/submission.json` still points to the old GEO-Pb TIFF, while README/root HTML promoted CTXFUS. Previous tests asserted promotion rather than checking prerequisites. The new canonical decision is `evidence/run_card.json`; all prior scientific cards remain historical. No historical DTI is relabeled as a result from this run.
- A successful CI/site check means the **blocked status is correct**, not that an upload is authorized. The audit CLI deliberately exits 2 for blocked; tests/site validation use the structured report.

## Official verification and source boundary

This session retrieved the organizer's [README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md) and [notebook](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb) at immutable commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b` through GitHub's API. The README supports CPU-only use; the blanket statement that a GPU is required is wrong. Notebook cell 0 describes fault detection with a U-Net ensemble, and cell 16 uses Tversky training loss with alpha 0.2 and beta 0.8. **These are training constants, not measured HOLDOUT-DTI.** The reference notebook's random patch splits are not a substitute for the prompt's stricter spatial hide-and-recover protocol.

Current network access is limited to GitHub and package registries. The [competition format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [USGS GeoDAWN DOI](https://doi.org/10.5066/P93LGLVQ), [GDR 1391](https://gdr.openei.org/submissions/1391) and [SGMC](https://mrdata.usgs.gov/geology/state/) are official review links, **not freshly verified downloads this session**. Their earlier retrieval descriptions are historical, not proof of current availability. No current rules interpretation, remaining weekly quota, live leaderboard value or organizer score receipt is asserted.

The historical metadata inventory covers the owner's listed public repositories, but does not establish global novelty. Fetching every website's repeated unreceipted score would not resolve the overlap obstruction, and could not produce a verified receipt. The two leaderboard targets supplied in the prompt conflict; both remain unverified owner context.

## H33: a defensible answer, not a private-label reconstruction

The educational H33 file is hash-pinned (`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`). Historical byte measurements record sparse binary off-catalogue support. The reported 0.2778 is **OWNER-REPORTED / NOT RECEIPT-VERIFIED**; it cannot satisfy the requested ORGANIZER-CONFIRMED label.

In the supplied metric implementation, let T be recovered truth credit, S prediction mass, M credited prediction mass and K truth mass. With alpha + beta = 1, DTI = T / [alpha(T + S - M) + beta K]. Thus reducing **uncredited** mass while holding T and M fixed raises the ratio. Sparse placement can avoid redundant prediction mass. This is a conditional mathematical explanation of why sparse pruning might help, not proof that any particular deletion caused the reported score.

A difference between two scores does **not** identify K, T or M without additional justified invariance assumptions and hidden labels. The inherited numerical back-solve and live projections are not observations and must not be used to pick a slot. A blanket binary-optimality assertion also does not follow from an objective that contains changing max-cover assignments. There is no defensible numerical promise of exceeding the owner's reported result.

The useful next scientific objective is improved off-catalogue credit at fixed mass, tested against a fold-rebuilt incumbent. Static historical rasters pruned against the full catalogue are invalid holdout promotion bars: the hidden catalogue traces have already influenced their support. Different evaluators/splits/positive counts cannot be compared by their headline DTI.

## Ranked research candidates — no implementation or assignment

Priorities are **qualitative expected research value**, not predicted DTI. Costs are engineering judgments, not measured runtimes. The first three refine previously proposed but unexecuted profile ideas; the fourth is a new explicit negative-control formulation. None is claimed globally novel or viable for release while the preflight fails. No proposal assumes unverified new external data is obtainable.

| Rank / cost | Specific layers and physical transform | Why an absent fault might be detected | Difference from inspected implementation | Named non-fault mimic / falsification |
|---|---|---|---|---|
| First / medium | `depth_to_base_surf` (15), `iso_grav_anom` (13), `det_elev` (12), `det_elev_slope` (19): signed, ordered opposing-flank depth offsets with gravity curvature support after terrain-stratified detrending | A buried basement step could survive sediment cover without a visible scarp | GEO-Pb computes whitened unsigned domain changes; this would test flank order and asymmetric profile fit against a symmetric valley null | Lateral sedimentary facies or erosional basement relief. Reject if matched unfaulted basin-edge profiles perform equally well |
| Second / medium–high | `rtp` (2), `tmi` (14), `tmi_vg` (9), `depth_to_base_surf` (15), relief: track signed lateral edge displacement across smoothing scales | A deeper contact could continue beneath cover with its magnetic edge displaced from a surface expression | Not scalar Euler depth, gradient magnitude or a worm; estimates cross-scale edge displacement with uncertainty | Intrusive contacts, remanence or flight geometry. Reject if acquisition-aligned controls reproduce the signature |
| Third / high | `det_elev` (12), slope (19), optional independent gravity arm: repeated residual facet offsets across separate drainages matched for relief and aspect | Degraded fault scarps may leave repeated offsets rather than a continuous ridge | Not LiDAR/scarp top-K or crest thinning; tests signed cross-drainage replication | Lake Lahontan terraces, resistant bedding, incision. Reject if constant-elevation contours explain detections better |
| Fourth / medium | Detrended terrain plus supplied radiometric/magnetic fields: fit radial fan drainage and test discordant throughgoing boundaries after subtracting a fan-front null | Could reject alluvial-fan contacts that consume prediction mass while retaining buried cross-fan structural boundaries | GEO-Pb names fans as mimics but does not fit and subtract a radial fan-front negative control; CTXFUS has generic context, not this explicit null | True fan-front faults can be falsely removed. Require paired precision gain at matched mass and report sensitivity loss |

Band numbering is inherited metadata from `evidence/input_audit.json`, not remeasured from an absent core feature raster. The depth/basement-versus-conductive-base interpretation remains unresolved: do not infer thickness or units from the name. The signed/profile controls are not present in inspected `geopb.py`, `relay.py`, `fields.py`, `features.py` or `featurestack.py`; related generic transforms are present, so a registry comparison is still mandatory.

**Top-candidate preregistered test once prerequisites are legitimately supplied:** one fixed detector versus the fold-rebuilt incumbent, matched emission budget, identical whole-segment buffered splits. Test every primitive feature alone; AUC above 0.90 is a leakage alarm until resolved. Fit all catalogue-derived features from fold-visible faults only and mask visible faults pixel-exactly. Use the pinned shared evaluator's pooled terms and paired spatial-cluster CI; publish evaluator hash/version, withheld-positive count, conditional 95% CI, confounder controls and the full registry surface/final-dot measurements. At most three experiments or two hours. No slot unless the candidate beats the current same-instrument incumbent and all gates clear. There is currently no valid numerical result to report.

## Reusable geothermal knowledge corrections

The old `knowledge/geothermal-vent-discovery.md` is a historical exploratory note, not an official literature review. In particular:

- An insignificant hot-spring AUC does not establish independence or statistical orthogonality of two features.
- Re-ranking at fixed mass can change false-positive credit; a fixed number of dots does not guarantee that uncredited mass cannot increase.
- A sparse vent catalogue may still supply useful covariates; its size alone cannot prove it is unusable.
- InSAR or seismicity is not a guaranteed fault detector or a guaranteed competition gain; motion and earthquakes have non-geothermal and non-tectonic confounders.
- Thermal association does not prove a permeable, hot reservoir. The competition target is a fault raster, not direct vent productivity.
- No broad statement that all US-government-hosted external data are automatically eligible is justified without the actual license and challenge-rule review.

Free official external sources worth a future availability check are [USGS ComCat](https://earthquake.usgs.gov/fdsnws/event/1/) for seismicity and [ASF DAAC](https://asf.alaska.edu/) for Sentinel-1. They are outside this session's network allowlist; availability/coverage/access requirements are **not checked**, so they are not proposed as currently viable experiments.

## Next session, in dependency order

1. Obtain a versioned protocol decision for dense priors and an explicit single-method lane. This is an authorization dependency, not a request for visual inspection. No private reinterpretation.
2. Obtain the pinned transformed cache and a current incumbent recipe; use the same shared evaluator for both. Raw-data placement alone is not the only blocker.
3. Test the first authorized hypothesis above, with per-feature canaries and paired conditional uncertainty. Stop on duplicate or budget exhaustion.
4. Only after the gates clear, write a genuinely new TIFF through the shared writer, publish its name/hash/note/download and let the separate selector decide any weekly slot.

The agent can implement and verify code autonomously; it cannot invent permission, create authenticated organizer receipts, reach blocked official hosts, or guarantee private-label performance. That is the remaining boundary to completing the original submission request.
