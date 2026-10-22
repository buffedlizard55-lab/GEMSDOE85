# Repository review and decision record — 2026-10-22

## Executive decision

**No new submission TIFF is ready, downloadable, unique-cleared, or approved for a weekly slot.** This is a negative **preflight** result, not a negative geological experiment. No geological experiment was run. A previous submission was downloaded privately for education only and is not offered as a deliverable.

The seed commit `1c38781cb20dbab2e1a193f65badba2f5246ea92` contains only `README.md` (11 bytes). The inherited claims about a ready train→inference pipeline, previous-session next steps, GPU-only training, and data being the single remaining blocker do **not** describe this checkout. There was no model, template, cache, evaluator, data, website, registry, or test suite to resume.

## Decisive protocol conflict: uniqueness saturation

The shared `gems57.uniqueness.saturation_certificate` was run on the pinned `17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif` witness. See [`evidence/saturation_certificate.json`](../evidence/saturation_certificate.json), [`registry/learning_manifest.json`](../registry/learning_manifest.json), and its [immutable source](https://github.com/buffedlizard55-lab/17GEMSDOE/blob/6fc71d19d49dca4960d5434bd81b6dd06fcc030a/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif).

**REGISTRY-MEASUREMENT (not a DTI score):** it has positive finite support on all 5,167,373 footprint cells. Every one of the 5,106,385 cells outside the mapped catalogue is within the 3-pixel halo. Consequently, every nonempty candidate supported there has forward overlap 1.0 with this prior, exceeding the prompt's 0.70 gate. This is a set-theoretic obstruction, not an empirical guess about a particular candidate. It does not establish a rank correlation for an ungenerated candidate.

An empty raster avoids this overlap but cannot be a useful fault-discovery solution, has undefined rank correlation, and would be a fabricated response to the request for a high-performing unique candidate. We did not produce one. Changing the filename, adding noise, moving dots to dodge a gate, or changing the support definition is not a scientifically justified solution.

Some sibling code offers alternative dense-surface classifications. **Those exemptions are not used here.** The literal shared comparison remains binding. The protocol/policy owner must specify whether the registry's continuous surfaces have a different authorized representation before an admissible nonempty candidate is possible. This cannot be repaired by a human visually inspecting a TIFF.

## Other blockers

- **Missing lane:** the prompt references a “single method paragraph below” but supplies no explicit method assignment. Candidate research is not permission to select a lane in a parallel run.
- **Missing transformed cache:** raw features were restored, but the requested template's cached feature-stack bytes were not supplied. Public cache receipts are not the bytes. No private substitute was built. The public metadata inventory records candidate `.npy`/`.npz` files without asserting they match the requested stack.
- **No comparable current holdout incumbent:** existing sibling receipts use different instruments. No candidate/current-best pair with the same hidden whole segments, masks, pooled terms, and uncertainty was available in this checkout. We did not declare an improvement against a heterogeneous historical metric.
- **Incomplete uniqueness clearance:** public Git-tree metadata for 88 repository names was inventoried at immutable commits, with 2,060 possible-prior TIFF paths at retrieval. Counts include archival copies and quarantined files; they are not distinct submissions. These are **inventory counts**, not scores. Full raster bytes, open PRs, private artifacts and every live page were not all compared. There is no global novelty certificate.
- **No DrivenData account session:** the data page redirected to login. Public owner mirrors can supply bytes but not eligibility, rule acceptance, live remaining weekly quota, or authenticated submission receipts. No credentials were requested and no submission was made.

## What was actually recovered and checked

[`registry/data_manifest.json`](../registry/data_manifest.json) pins owner mirrors at immutable Git commits. `python scripts/restore_data.py` successfully restored `training_features.tif`, `labels.tif`, `existing_faults.tif`, and `sample_submission.tif`. They are ignored local data, not committed bulk artifacts. Hash consistency is **not organizer authentication**.

[`evidence/input_audit.json`](../evidence/input_audit.json) records measured CRS, shape, affine transform, band descriptions, footprint, missing-feature counts, and byte identity of `labels.tif` and `existing_faults.tif`. The sample's values are never used as a predicted surface; only its finite footprint/grid is used. Missing feature values inside the footprint must not be passed through into any future prediction. The restored band 15 description says “depth to basement surface,” while the official summary mentions a conductive base; do not silently equate these interpretations or infer conductivity units.

The shared evaluator, whole-component holdout helper, metric, literal uniqueness gate and fail-closed writer are vendored **unmodified** from `buffedlizard55-lab/60GEMSDOE@b99591eede63c6d45c8a896255b8cd34824fa00b`. Per-file SHA-256 pins are in [`registry/template_pin.json`](../registry/template_pin.json). Only required modules are included. Their original package docstring names the template's lane, **not this run's assignment**. No shared defect was fixed privately. Synthetic contract tests exercise the metric and interfaces, but they do not validate a geological candidate.

## What is official, and what is not

- The [organizer problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) specifies **fault prediction**, not direct vent or productive-reservoir discovery. Fault evidence alone does not demonstrate heat, permeability, usable flow or a geothermal resource.
- The same page gives a 300 m triangular distance-weighted Tversky index with alpha 0.2, beta 0.8; these are **metric constants**, not measured scores. It requests a single float32 layer in the reference CRS, bounds and resolution with predictions in [0,1].
- The [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), §3.2, states a weekly cap of three submissions, subject to competition-site limits. Remaining account quota is **unknown**. No slot is selected here. The rules also require disclosure of generative-AI assistance in the narrative; this repository was developed with an AI coding agent.
- The public leaderboard retrieved on 2026-10-22 displays a leading value of **0.4413**. This is a **PUBLIC-LEADERBOARD-OBSERVATION**, not this team's submission-page receipt. The prompt's “0.3195 is highest right now” is inconsistent with that retrieved page. We do not label either the owner's historical reports or the public observation `ORGANIZER-CONFIRMED` because the requested evidence standard specifically requires a submission-page receipt.
- The requested **0.2778** for H33 is **OWNER-REPORTED / NOT RECEIPT-VERIFIED**. Its own source page says no organizer score exists, whereas a sibling write-up labels it organizer-confirmed without supplying a submission-page receipt. Repetition is not verification. We do not import that label.
- The user's historical score list is retained as quoted context in the README, not treated as organizer-confirmed measurements. New measured performance must be labeled **HOLDOUT-DTI** with evaluator version, withheld positives and conditional 95% CI; no such candidate measurement exists here. Projections will never be called scores.

## Why H33 plausibly worked; why its reported score cannot be explained exactly

See [H33 analysis](why-h33.md). Byte inspection establishes a sparse binary dot raster, off-catalogue and pruned near catalogue traces. The official maximum-cover metric explains why reducing redundant mass can improve DTI. Without hidden labels, a receipt, and a matched ablation, it cannot prove that a particular deletion caused the reported increase or forecast a higher public/private score. Treating every pixel adjacent to a known fault as a false positive would be an unjustified geological and statistical assumption.

## Automation boundary

The project performs data integrity, saturation preflight, shared-code integrity, and format diagnostics without a human inspector. It publishes a negative run card and a blocked website. **A geological model/feature engine, full two-stage uniqueness audit, feature canary runner, paired candidate-versus-incumbent holdout experiment, selector, and organizer upload are not implemented.** This is not a finished train→submit system.

The static Pages site is a truthful status/research portal, not an in-browser model generator. A future model must feed the shared `submission_writer.py` only after passing the independent gates, and publish only the validated bytes. Local format PASS is neither geological validation nor organizer acceptance. The public spec permits null/NaN outside bounds; the template's all-finite/zero-outside policy is a conservative export policy, not proof that DrivenData rejects NaN. The historic portal message alone does not identify its cause.

## Parallel-session reconciliation

While this branch was under review, a parallel session merged README-only research in PRs #1 and #2. The resulting README conflict was resolved by preserving that entire prior text in `research/previous-review-2026-10-22.md`, headed as a superseded historical snapshot. Its untested MT/thermal/geochemical shortlist is retained, not represented as our executed work or as an explicit lane assignment. The current status reflects the mirror restoration and saturation measurement from this session.

## Next session, in dependency order

1. Obtain an explicit parallel-run method assignment and an authorized resolution of the saturated-prior overlap policy. Preserve the current literal result until then.
2. Restore the exact transformed cache with channel semantics, per-file hashes and fold dependency metadata. Catalogue-derived features must be rebuilt **from each fold's visible faults**, never reused from a full-catalogue geometry cache.
3. Pin one incumbent and a whole-component spatial split. Use the shared `buffered_component_draw` (not legacy short chunks), recompute catalogue features inside fold boundaries, mask all non-withheld mapped pixels exactly, and compare identical pooled physical blocks. The per-fold evaluation region must be label-blind.
4. Run every proposed feature alone as a holdout leakage canary. AUC above the protocol's threshold is a stop pending a documented investigation; a low AUC is not proof of no leakage. Explicitly handle absent classes, NaN/missing channels and feature-support masks.
5. Within the experiment/time budget, evaluate the authorized hypothesis and incumbent with shared pooled DTI and paired spatial-cluster confidence intervals. Show withheld **pixels and whole-component counts**. Unknown catalogue-zero cells remain unlabeled, not verified absence.
6. Inventory and hash-verify all accessible priors; compare rank correlation before placement, then literal overlap/correlation on final dots. Stop/log duplicates immediately. Preserve the exact registry snapshot used.
7. Package only an evidence-backed, distinct candidate through the unmodified shared writer; reopen the TIFF, verify the ZIP contains that exact one TIFF, and record SHA-256. Give it a content-derived name and note of at most 140 characters. Publish a clear candidate-download status separate from `promote-to-selector` and `approved-for-slot`.
8. The separate selector must check the authenticated submission page's remaining quota. Only a returned organizer submission receipt can establish acceptance and `ORGANIZER-CONFIRMED` performance. Do not spend slots just to test formatting.

## Core values applied

**Maximize P(Win):** avoid wasting scarce submission slots on a misleading metric or trivial duplicate. **Own the Outcome:** publish the obstruction, exact evidence and next dependencies instead of inventing a “ready” TIFF. There is no guarantee of winning or of exceeding any reported leaderboard value.
