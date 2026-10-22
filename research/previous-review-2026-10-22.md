# Historical parallel review — superseded status snapshot

Preserved from `main@4ca1333` during reconciliation of PR #3 on 2026-10-22. This is another session's README-only review, not this session's executed research and not an explicit lane assignment. Its statements that only a README exists and no mirror bytes/shared tools are present are **historical**, superseded by the current [review](review.md) and [run card](../evidence/run_card.json). Its external-data shortlist remains **untested**. The old run card below is archival, not the current run card. No claims were silently promoted or discarded.

---

# GEMSDOE85 — GEMS Prize research and submission gate

> **Read this file at the start of every project session.** It is the persistent mission brief, operating protocol, source register, and current blocker log. Do not treat an unscored model projection, a sibling repository's claim, or a local holdout result as an organizer-confirmed competition score.

## Executive status — 2026-10-22

**No submission is ready or available to download from this repository.** The checkout contains only this README: no competition rasters, cached feature stack, labels, evaluator, writer, generated predictions, or test suite. Therefore this session cannot run the required spatial holdout, compare a surface/final raster against registry rasters, validate a GeoTIFF, or honestly claim an improved score. No synthetic or placeholder TIF is being supplied: a fabricated file would not be a valid, scientific competition submission.

The competition's official data page redirects to login when accessed without an authenticated DrivenData session. The reference-solution README also says to download the data from the challenge and place it in `data/`. The existing prompt says a local download/prepare workflow exists, but its scripts are **not present in this checkout**. This is a verified mismatch, not a task completed here. Do not attempt to train or run a submission until the official inputs and shared template are available.

### Decision on the reported H33 score

The question identifies `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` and supplies a score for it. That claimed value is **prompt-reported and unverified**: I could not associate it with an organizer submission receipt. The linked GEMSDOE32 page describes H33-2-B2 as an off-catalogue, dot-pruned candidate, reports a **model projection** (not a score), and explicitly says that no organizer score exists for that artifact. Those statements do not establish that this exact file received the prompt-reported result.

Accordingly, there is no defensible causal explanation for a verified result. **Conditional hypothesis only:** if a comparable score was in fact earned by the described method, the page's account suggests that thinning a broad, catalogue-derived surface into a smaller set of spatially distributed dots could improve the distance-weighted precision/recall tradeoff by removing redundant predictions while retaining coverage. This is not a confirmed explanation, and the holdout described there uses catalogue faults as proxy truth; it cannot prove discovery of hidden faults.

The official leaderboard page fetched on 2026-10-22 showed a different first-place entry from the older figures in the prompt. Treat leaderboard entries as dated snapshots, not measurements from this repository, and do not treat them as **ORGANIZER-CONFIRMED** under this project's receipt requirement. No local submission has been scored or promoted here.

## Mission and values

Build an auditable, useful system for finding **faults not present in the current public fault catalogue** in the GeoDAWN region, with the aim of improving the probability of success in the GEMS Prize. Scientific discovery and prediction of hidden faults—not fitting the known catalogue for its own sake—is the objective. The final-round expert review and expanded labels make defensible, interpretable candidates valuable as well as leaderboard performance.

- **Maximize P(Win):** make decisions against the best available evidence, conserve the weekly submission cap, use preregistered comparisons, and never promote an untested hunch.
- **Own the Outcome:** verify end-to-end, publish negative findings, fix shared tools centrally rather than forking them, and state limitations plainly.
- **No hallucinations:** source every factual claim; distinguish official facts, local measurements, owner-reported claims, hypotheses, projections, and organizer receipts.

### Submission must be unmistakable

When a candidate eventually passes the gates below, make the submission GeoTIFF and its download link the most prominent item in the site's executive summary. Show the exact unique submission name, a note of at most 140 characters, the file hash, and a validated receipt. Never label a candidate **OK TO DOWNLOAD AND SUBMIT** unless its on-disk bytes have passed all required format checks and its preregistered holdout gate. Never claim that a local holdout score guarantees a competition score.

The official submission requirements are: one-band float32 GeoTIFF, EPSG:32611, 100 m resolution, the same bounds/shape/geotransform as the competition target, and predictions in [0, 1]; pixels outside the target bounds are null/NaN. Validate both range and nodata handling by reopening the written file. A previous user-reported portal error (“Predicted values must be in range [0, 1]”) makes explicit finite/range checks mandatory; do not assume a nodata sentinel is accepted as a prediction.

## Required experiment protocol (do not relax)

1. **Lane control.** Develop one preregistered method at a time. Before placement and on final emitted dots, compare against each registry raster: calculate raster rank-correlation and nearest-dot overlap within 3 px. If any rank-correlation exceeds **0.90**, or over **70%** of candidate dots fall within 3 px of one registry raster's dots, record a duplicate and stop. Save the exact masks, thresholds, sample counts, comparison code/version, and results. Do not claim this check was performed without input rasters.
2. **Reuse the shared template.** Use its cached feature stack plus shared `evaluate_holdout.py` and `submission_writer.py`. Holdout is hide-and-recover: withhold whole fault segments plus buffer; derive every catalogue-based feature from visible faults only; mask visible faults pixel-exactly; score pooled DTI with alpha 0.2, beta 0.8, and the 300 m triangular distance kernel. If a shared tool is wrong, fix it once in the template and report it—never carry a private fork here. At present the named scripts/template are absent from this checkout.
3. **Leakage canary.** Score every feature alone on the spatial holdout before trusting a model or ensemble. Any AUC above **0.90** is leakage until investigated and explained. Record folds, held-out segment IDs, buffer, positive count, evaluator version, AUC, and confidence intervals.
4. **Evidence labels.** Every reported score must be labelled either **HOLDOUT-DTI** (with evaluator version, number of withheld positives, and 95% CI) or **ORGANIZER-CONFIRMED** (copied from a submission-page receipt). A projection is never a score. Leaderboard readings must include URL and retrieval date/time.
5. **Promotion gate.** A candidate must beat the current best spatially blocked holdout candidate under a preregistered paired comparison, pass leakage and duplicate checks, and pass byte-level format validation before it can be considered for a weekly slot. A holdout proxy is not organizer truth; failure or inconclusive evidence means no slot. The selector—not this research step—chooses a real weekly submission slot, within the current submission-page cap.
6. **Budget.** Stop at 3 experiments or 2 hours, whichever comes first. Keep negative results. No unvalidated candidate is an invitation to spend a competition submission slot.
7. **Unique artifact.** Use an original method and a unique name. Do not copy a prior raster. Compare candidate values and dots with accessible registry/prior rasters before placement and after emission. Store the final raster SHA-256 and an independently re-read validation receipt. No artifact exists yet in this checkout.

## Candidate hypotheses — shortlist, not results

These are **research hypotheses**, not demonstrated improvements and not claims of novelty across all GEMSDOE sibling repositories. This checkout has no implementation to compare against. Before testing, search the shared template and available prior experiment manifests; reject a candidate if the actual transform overlaps an existing method or fails the lane check. Rank is qualitative because no local holdout results exist; numeric DTI gains would be fabricated.

| Rank | Candidate, inputs, target signature | Why it might reveal an unmapped fault; known difference / risk | Expected DTI potential / cost | Official source and obtainability |
|---|---|---|---|---|
| 1 | **Depth-persistent MT conductance breaks:** USGS Great Basin electrical-conductance GeoTIFFs at 2–12, 12–20, 20–50, 50–90, and 90–200 km; calculate scale-normalized lateral gradients and test whether aligned breaks persist across depth intervals. | Fault-controlled fluid/alteration corridors may produce spatially coherent conductivity contrasts not represented by surface traces. This targets vertical persistence across the conductance stack, not just a single surface raster. **Mimics:** lithologic boundaries, basin fill, and inversion smoothing. Deep conductance is regional and may be too coarse to localize surface faults. | **Medium / medium.** Must show held-out benefit after all fault-derived features are rebuilt using visible faults only. | Public USGS ScienceBase record [P9TWT2LU](https://doi.org/10.5066/P9TWT2LU) lists all five downloadable TIFFs and their depth intervals. Landing page and attachments were confirmed in this session; the rasters have **not** been downloaded, clipped, aligned, or tested here. This source is publicly listed as obtainable, but local download remains unverified under the sandbox's host restrictions. |
| 2 | **Shallow-temperature anomaly gradients:** INGENIOUS 2-m temperature-probe observations; after accounting for sampling support and available elevation/context, test local residual-temperature gradients and elongated anomaly alignments rather than raw hot-point density. | Shallow heat anomalies can mark active fluid pathways associated with unmapped structures. **Mimics:** season, soil moisture, solar exposure, topography, land use, and sparse sampling; point locations may be biased toward accessible or already-known thermal sites. | **Low–medium / medium.** Sparse coverage may limit map-wide lift. | GDR INGENIOUS [dataset 1391](https://gdr.openei.org/submissions/1391) lists “2m Temperature Probes.zip” (1.03 MB) as publicly accessible. The record is reachable; archive content and coverage are not verified in this checkout. |
| 3 | **Geodetic strain-orientation discontinuity:** competition-provided dilatation, shear strain rate, and second strain invariant; derive local orientation/coherence breaks and test fault-like linear discontinuities without using withheld fault geometry. | Brittle structures can localize strain and create permeability pathways even where the mapped catalogue is incomplete. Transforming the continuous tensor field into orientation discontinuities is distinct from using a raw strain layer, but may overlap prior experiments and needs a sibling-repository audit. **Mimics:** broad block-boundary deformation, interpolation artefacts, and non-fault geodetic gradients. | **Low–medium / low.** Inputs should be part of official competition features; the feature stack is missing here. | Feature families are enumerated in the official [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). No feature file is present locally to confirm exact band names or availability. |
| 4 | **Geochemical discharge anomaly corridors:** INGENIOUS well/spring temperature and aqueous chemistry compilation; test spatially coherent anomalies in measured temperature/chemistry around candidate linear structures, with strict spatial blocking and no catalogue-derived labels in the feature construction. | Hydrothermal discharge can be focused along faults not yet mapped. **Mimics:** lithology, mixing, water-rock reaction, sampling bias, and springs unrelated to geothermal faults; observations are sparse and point-based. | **Low / high.** Data harmonization, sampling-bias control, and spatial support are substantial. | GDR INGENIOUS [dataset 1391](https://gdr.openei.org/submissions/1391) lists a public “Well and Spring Temperature and Chemistry.zip” (19.85 MB). Record reachable; archive has not been inspected locally. |

**Top candidate selection:** Rank 1 is the best next *research test*, not a viable submission yet. Its USGS source is officially listed with five downloadable rasters, but local alignment/coverage and access to the shared feature stack are not established. The next experiment is blocked until the competition data and shared evaluator/writer are restored and these rasters can be aligned to the exact competition grid. Run the leakage canary per layer and then the prescribed hide-and-recover evaluation; do not emit or submit a candidate first.

## Evidence and source register

| Claim / dataset | Evidence and status | Link |
|---|---|---|
| Competition objective and hidden-fault setup | Official description says to identify faults, notes the public fault set is incomplete/potentially inaccurate, and says expert-identified faults comprise the initial prize test set. Verified from page content in this session. | [Problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| Metric and submission format | Official description specifies distance-weighted Tversky, alpha 0.2, beta 0.8, triangular kernel support 300 m, and a single-band float32 GeoTIFF with EPSG:32611, 100 m resolution, matching extent, and probabilities in [0,1]. | [Metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| Public leaderboard | Official page fetched 2026-10-22; its first-place entry differs from older figures in the prompt. Snapshot only; leaderboard changes. This was not an **ORGANIZER-CONFIRMED** receipt for a local submission. | [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) |
| Competition data | Data page redirects to DrivenData login in this session. No files were retrieved. | [Data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) |
| Reference solution | Official GitHub repository states the challenge data must be downloaded and placed in `data/`; it includes a notebook and environment definitions. This checkout does not include it. | [Reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) |
| GeoDAWN surveys | USGS describes magnetic and radiometric acquisition; airborne lidar collection was coordinated over a similar extent. | [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) |
| INGENIOUS compilation | GDR describes a public regional compilation with faults, probes, geophysics, geochemistry, wells/springs and other data; dataset listing is not proof that a particular layer has suitable coverage for this task. | [GDR dataset 1391](https://gdr.openei.org/submissions/1391) |
| MT conductance maps | USGS ScienceBase gives five depth ranges and downloadable TIFF attachments; coverage and grid compatibility still need empirical verification. | [USGS ScienceBase P9TWT2LU](https://doi.org/10.5066/P9TWT2LU) |
| Reported H33 artifact and claimed score | The prompt gives a value, but the GEMSDOE32 page characterizes H33 as a candidate, gives a model projection (not a score), and says no organizer score exists for the artifact. Treat the prompt's value as unverified, not **ORGANIZER-CONFIRMED**. | [GEMSDOE32 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) |
| Official project/problem PDF | User supplied NLR PDF link; not fetched or independently checked in this session. | [GEMS rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) |
| CRS reference | EPSG page linked by the official competition problem description. | [EPSG:32611](https://epsg.io/32611) |

## Next actions, in order

1. Restore the intended **shared template** to this branch (or ensure this repository is cloned from the correct template) with its cached feature stack, `evaluate_holdout.py`, `submission_writer.py`, and tests. Do not create a private replacement.
2. Obtain the competition's licensed data through an authorized DrivenData session and put it in the agreed `data/` location. Verify checksums, band descriptions, CRS, affine transform, dimensions, nodata, labels, and masking. Current blocker: this session has no DrivenData authentication, and the data page redirects to login.
3. Run the repository's official download/prepare commands only after confirming the scripts exist. The prompt-mentioned `scripts/download_competition_data.sh` and `scripts/prepare_data.py` are **not present** in this checkout; the claim that they are ready cannot be substantiated here.
4. Retrieve and align the public USGS conductance layers; record source URL, retrieval date, file hashes, resampling method, and grid coverage. Confirm license/competition use terms before using external data.
5. Pre-register the Rank 1 single-feature and combined tests, spatial folds, whole-segment buffers, leakage canary and duplicate tests. Keep within the 3-experiment / 2-hour budget. Report negative findings.
6. Only after the top candidate beats the current holdout best, passes all gates, and produces a byte-validated raster, create the unique name/comment and make the file prominently downloadable. The contest slot selector is a separate step.
7. Review the latest official leaderboard and submission rules just before any future slot decision; never hard-code an old score as “current.”

## Limitations and irregularities to keep visible

- This repository is not currently an application/site or training pipeline; only a README exists. No GitHub Pages configuration or user interface is present.
- No feature rasters or label data are present, and competition data access requires login. We cannot calculate holdout DTI, confidence intervals, leakage, rank-correlation, overlap, or a valid final GeoTIFF.
- The user's supplied score statements conflict across dates. The official page retrieval in this session showed a different leader from the older figures in the prompt; historical leaderboard snapshots may differ. None of these figures is a local **HOLDOUT-DTI** or an **ORGANIZER-CONFIRMED** score copied from a submission receipt.
- GEMSDOE32's owner-maintained page is useful evidence about the author's described method, but it is not an official score receipt. Its own text calls the H33 result unscored/projected. No causal claim about the prompt-reported score is established.
- The user-provided sibling site score list is not independently audited here; names, values, and alleged validation results are treated as leads, not verified measurements. A full deduplication requires access to their actual rasters/code/manifests, not names alone.
- “Publicly listed” and “downloadable” do not establish spatial coverage, license compatibility, alignment, scientific utility, or holdout improvement.
- No competition slot has been used or selected. No submission TIF is being represented as generated or submission-ready.

## Current run card

```json
{
  "hypothesis": "H1: depth-persistent lateral conductance breaks from the five official USGS Great Basin MT conductance rasters may identify fluid/alteration corridors associated with unmapped faults; untested.",
  "mechanism": "Test normalized conductance-edge persistence across 2–12, 12–20, 20–50, 50–90, and 90–200 km layers; no model or raster has been run.",
  "named_non_fault_mimic": "Lithologic boundaries and basin fill, with additional broadening from inversion smoothing.",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "evaluator_version": null,
    "withheld_positives": null,
    "value": null,
    "ci95": null,
    "status": "not computed: evaluator, labels, and feature stack are absent"
  },
  "correlation_overlap_vs_registry": {
    "rank_correlation": null,
    "fraction_within_3px": null,
    "status": "not computed: candidate and registry rasters are absent"
  },
  "raster_sha256": null,
  "validator_output": {
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "status": "not run: no candidate raster exists"
  },
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```
