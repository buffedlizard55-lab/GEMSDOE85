# Repository review and decision — 2026-10-23

## Executive decision

**BLOCKED — DO NOT DOWNLOAD OR SUBMIT ANY HISTORICAL TIFF.** This checkout has no new competition candidate cleared for download or submission. The generated site must state that plainly. A file's passing format checks in a previous session does not establish that it is unique, scientifically supported, authorized by the method lane, or approved for a weekly slot.

This is a **negative preflight**, not a geological negative and not a candidate holdout result. No new geological experiment, leakage canary, holdout evaluation, surface/final-dot registry comparison, GeoTIFF validation, weekly selector action, or submission was performed in this review. The machine record is [`evidence/run_card.json`](../evidence/run_card.json); the blocked submission registry is [`registry/submission.json`](../registry/submission.json).

The demand for a unique TIFF conflicts with three prerequisites: the method lane is unassigned, the transformed cache is unavailable, and a binding literal saturation certificate records a universal overlap blocker under the required support definition. Creating a placeholder, copying a prior, moving predictions into mapped faults, changing masks, or relaxing the 70%/3-pixel rule would not resolve those prerequisites scientifically. Therefore this review creates **no TIFF** and does not choose or submit to a weekly slot.

## H33: score report, evidence, and plausible mechanism

The value **0.2778** is retained as **OWNER-REPORTED / NOT RECEIPT-VERIFIED**. A historical owner page says no organizer score existed for its artifacts, and there is no authenticated submission-page receipt plus file-hash crosswalk in this checkout. Repetition in a README or sibling site does not upgrade that value to `ORGANIZER-CONFIRMED`. The task prompt also contains two different leaderboard snapshots, 0.3195 and 0.4413; neither was freshly retrieved for this review, and neither is used as a score or current leaderboard claim here.

A prior session recorded an `ARTIFACT-MEASUREMENT` for an educational H33 raster: SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, 37,654 positive pixels, binary values, and zero mapped/near-catalogue support according to the archived audit. That raster is not present in this checkout and was not re-read during the current preflight. See [`evidence/h33_learning_audit.json`](../evidence/h33_learning_audit.json) and [`evidence/archive/input_audit-previous-session.json`](../evidence/archive/input_audit-previous-session.json) for the provenance limits. Those artifact statistics are not a score or causal explanation.

The proposed metric-level mechanism is plausible but conditional: under a maximum-coverage distance-weighted Tversky metric, thinning redundant nearby predictions can reduce false-positive mass while preserving the maximum credit to a truth pixel. That could improve the ratio. It does not establish that H33's reported value is valid, that thinning caused a particular increment, that catalogue-adjacent structure is false, or that a similar method will find hidden faults. Hidden labels, an authenticated receipt, and a matched ablation would be needed to answer those questions. See [`docs/why-h33.html`](../docs/why-h33.html).

## Decisive gates and current evidence

### Lane and inputs

- [`registry/lane.json`](../registry/lane.json) is `unassigned`; the brief's referenced method paragraph is absent. No prior method or research shortlist is permission to choose a lane.
- [`registry/data_manifest.json`](../registry/data_manifest.json) pins owner-supplied GitHub mirrors, not organizer-authenticated downloads.
- The current local presence/hash check is [`evidence/data_restore.json`](../evidence/data_restore.json): `labels.tif`, `existing_faults.tif`, and `sample_submission.tif` are present and match their manifest sizes/hashes; `training_features.tif` is absent. The sample is only a grid reference.
- [`registry/cache_manifest.json`](../registry/cache_manifest.json) is `unavailable` with no cache files. The requested transformed feature stack must not be privately rebuilt or replaced by raw features under the current instructions.

### Literal uniqueness blocker

[`evidence/saturation_certificate.json`](../evidence/saturation_certificate.json) is labeled **REGISTRY-MEASUREMENT, not DTI**. It records 5,106,385 allowed pixels, zero uncovered, covered fraction 1.0, and `universal_overlap_blocker: true` under the literal support definition `finite prediction > 0`. Its implication is that every nonempty candidate on that allowed domain would have forward overlap 1.0 with the recorded prior and exceed the 0.70 stop threshold.

The witness raster named by the certificate is not present locally, and its recorded path (`data/raw/learning/registry-saturation-witness.tif`) differs from the learning-manifest restore destination (`data/learning/registry-saturation-witness.tif`). The current preflight records this provenance mismatch and leaves the binding certificate **not locally revalidated** and unchanged. Missing witness bytes or a path mismatch do not erase the certificate or create uniqueness clearance. No new candidate surface existed for a pre-placement rank-correlation test, and no emitted dots existed for the final overlap test. The thresholds remain the user's literal thresholds: stop if absolute rank correlation exceeds 0.90 or if more than 70% of candidate dots are within 3 pixels of any registry raster. No chance correction, dense-prior exemption, or alternate mask is authorized.

### Holdout, format, and slot

- Current candidate `HOLDOUT-DTI`: **NOT RUN**. The recorded template evaluator identity is `gems57-pooled-hide-v2`; current candidate value, withheld-positive count, and conditional 95% CI are all null because there is no evaluated candidate. This is not a zero score.
- No feature-only leakage canary was run. A future feature with AUC >0.90 against withheld labels is a leakage stop pending explanation, not a result to tune around.
- No candidate raster exists to validate, hash, name, or package. `raster_sha256`, current submission name, and format receipt are null. Format validity alone would not establish uniqueness or skill.
- Zero experiments and zero competition slots were used by this preflight. The separate selector must check the actual authenticated account cap after a candidate clears the research gates; this work does not select a slot.

## Ranked geological hypotheses — proposals, not results

These four hypotheses are distinct, falsifiable research proposals based on feature-band descriptions recorded in the prior raster audit. They use only the competition-supplied feature stack for an initial test; **no new external dataset is required** to form or initially test them. The raw raster and exact transformed cache needed to execute that test are unavailable locally. Expected benefit and cost below are qualitative judgments, not numerical DTI forecasts. Cross-repository novelty is unverified.

| Rank | Hypothesis and layers | Physical signature / missing-catalogue rationale | Difference from methods described in this repository | Named non-fault mimic | Relative cost and expected benefit |
|---|---|---|---|---|---|
| 1 | **Paired basin-interface flexure** — depth-to-base proxy (band 15), surface conductance (17), isostatic gravity anomaly (13); elevation/slope (12, 19) as nuisance controls. | Directional, detrended profiles requiring an ordered signed depth/curvature pair with a consistent gravity response across a basin interface. A basement step beneath fill could persist where no continuous surface scarp is exposed; catalogue absence alone does not prove concealment. | Tests signed two-flank geometry and relative displacement rather than covariance-whitened boundary strength, ridge/gradient selection, or post-placement catalogue-collar thinning. | Lateral sedimentary facies change or erosional basement relief. | **Medium cost; highest conditional research priority.** No measured gain or DTI projection. |
| 2 | **Gravity-curvature polarity reversal** — isostatic gravity anomaly (13), vertical/horizontal gravity gradients (11, 18), gravity slope (5), depth-to-base proxy (15). | At multiple physical scales, require an inflection bracketed by opposite signed curvature lobes and stable profile order. A covered basement offset could retain a density contrast without a scarp. | Tests signed polarity/order rather than scalar gradient magnitude, gravity-worm strength, or orientation consensus. Derived gravity bands are one source family, not independent evidence. | Unfaulted lithologic density contact, regional detrending error, or inversion edge artifact. | **Medium cost; moderate conditional benefit.** Not scored. |
| 3 | **Depth-conditioned displaced magnetic edge** — reduced-to-pole field (2), total magnetic intensity (14), magnetic gradients (9, 3), depth-to-base proxy (15), terrain slope (19). | Measure lateral displacement between magnetic edge responses across smoothing scales, conditioned on the depth proxy and subdued relief, with orientation/uncertainty checks. A buried continuation could shift the deeper boundary from the surviving lineament. | Measures scale-dependent edge displacement rather than a scalar Euler-depth estimate or line-orientation vote. | Intrusive contact, remanent magnetization, interpolation seam, or variable survey flight height. | **Medium-high cost; moderate-to-low conditional benefit.** Not scored. |
| 4 | **Cross-drainage residual facet discontinuity** — detrended elevation and slope (12, 19); gravity (13) only as a separate corroboration arm. | Test repeatability of signed terrain-height/slope breaks across separate drainage profiles after matching elevation, aspect, and relief. A degraded fault could retain repeated facet offsets after a continuous scarp is lost. | Profile-to-profile residual consistency rather than scarp-ridge thinning, straight-valley occupancy, or a local slope peak. | Lacustrine terrace, resistant bedding, or fluvial incision. | **High cost; lower conditional benefit and greater novelty risk.** Not scored. |

The leading proposal is **not** an assigned method lane. It was not implemented or evaluated. If a future authorized run is possible, each feature must first be tested alone as a leakage canary, then use whole-component buffered holdout splits; all catalogue-derived features must use fold-visible faults only; visible faults must be masked pixel-exactly; pooled DTI must use α=0.2, β=0.8, and a 300 m triangular kernel; and uncertainty must be paired over spatial clusters. Only after those steps could a top candidate be considered for a separate selector.

The four initial tests do not depend on a newly fetched external data source. Official references retained for manual review include the [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [official competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [DOI](https://doi.org/10.5066/P93LGLVQ), and the [DOE GDR/INGENIOUS listing](https://gdr.openei.org/submissions/1391). These external pages were not freshly fetched in this review; links and prior source-register notes do not prove current availability or terms.

## Public artifact quarantine

Before this reconciliation, `docs/downloads/` contained 25 TIFF/ZIP artifacts plus supporting receipts and reports; several pages offered them as current downloads. Sixteen GEO-Pb/H85 TIFF/ZIP artifacts were byte-identical to files already in `submissions/quarantine/`; nine CTXFUS TIFF/ZIP artifacts had no matching quarantine copy. Six GEO-Pb check receipts matched quarantine; six CTXFUS receipts did not. The reconciliation preserves existing identical copies, moves previously unquarantined material and associated sidecars into quarantine, and records file hashes in a quarantine manifest. No historical artifact is cleared for submission.

The old `docs/downloads/run_card.json`, prior audit/preview files, old site text, and prior session results are historical. They are not the current run card or a release approval. The new public site must contain no TIFF/ZIP file, no link to one, and no positive “ready to submit” banner while no current candidate exists.

## External evidence and access limits

No external web page was fetched in this review. Official-source links remain available for manual inspection, and earlier `registry/sources.json` entries are prior-session retrieval notes—not fresh verification. The DrivenData data/submission pages are account-gated in the existing source record; no authenticated account session, current eligibility check, remaining weekly quota, or submission receipt is available here. Public owner mirrors can be hash-checked but cannot prove organizer provenance.

Fault prediction is not direct vent, heat, permeability, fluid-flow, reservoir, or economic-resource discovery. A fault hypothesis alone cannot establish geothermal productivity. Use any successful fault prediction only as one piece of evidence, not as a geothermal-resource claim.

## Reproducibility and remaining work

1. Obtain an explicit single-method lane paragraph; do not infer it from prior work.
2. Obtain the exact transformed feature cache and verify its hashes, band semantics, and fold dependencies; do not rebuild it privately.
3. Obtain policy-owner resolution of the binding literal saturation blocker without changing the specified 0.90 rank-correlation or 70% within-3-pixel thresholds. Preserve the current recorded certificate until then.
4. Only after gates 1–3, run the preregistered feature-only leakage canaries and the specified whole-segment buffered holdout. Keep the experiment budget to three runs or two hours, whichever occurs first.
5. Compare pre-placement surfaces and final dots against the registry. Stop and log a duplicate at either literal threshold.
6. If all research gates clear, use the pinned shared evaluator and writer; verify the written single-band float32 GeoTIFF against the exact grid, range [0,1], footprint and no-NaN rule, compute SHA-256, and produce the machine-readable run card. The note must remain ≤140 characters.
7. Publish a download link only when the current candidate has passed every required gate. The separate selector—not this research task—checks the displayed weekly cap and decides whether to use a slot. `ORGANIZER-CONFIRMED` requires an authenticated submission-page receipt.

The three code/review passes, their actual checks, and any remaining failures are recorded in [`evidence/review_passes.json`](../evidence/review_passes.json). A negative preflight and a blocked site are the correct result until those dependencies are resolved.
