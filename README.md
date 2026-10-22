# GEMSDOE85 — an auditable, unique GEMS submission lane

> **Start here.** The formal H85 run is **negative and blocked** by the registry-overlap gate.
> The GeoTIFFs in [`docs/downloads/`](docs/downloads/) are retained as format-valid evidence,
> but neither the formal candidate nor the selector control is submission-ready. **Do not
> upload either file or associate it with an organizer score.** The landing page is
> [`docs/index.html`](docs/index.html); this checkout does not submit, spend a weekly slot, or
> claim an organizer score.

## Executive answer — why the reported h33 `0.2778` happened

The number in the request is not independently authenticated here. The inspected
GEMSDOE32 artifact ledger says the h33-2-b2 file was **UNSCORED** and describes `0.2747` as a
projection; the user brief separately reports `0.2778`. The discrepancy is registered as
[`IR-85-01`](registry/irregularities.json). It would be unsafe to call `0.2778`
`ORGANIZER-CONFIRMED` without a submission-page receipt.

The mechanism nevertheless has a sound metric-level explanation. The prior file was a sparse
binary dot emission derived from the earlier dotted field, with catalogue-near dots removed.
The distance-weighted Tversky metric has a false-positive weight of `0.2` and a false-negative
weight of `0.8`; low-credit dots outside the `300 m` triangular kernel can lower the ratio more
than they help. Removing dots adjacent to known catalogue faults therefore can improve the
reported ordering if those dots earn little hidden-test credit. This is an explanation of the
observed artifact design, not a claim that the portal awarded `0.2778`.

A sparse emission alone cannot guarantee a better live score. The only defensible way to test a
new idea before a slot is a preregistered, buffered hide-and-recover evaluation. H85 therefore
uses the cached 19-band feature stack, withholds whole catalogue segments, masks visible segments
pixel-exactly, runs three fixed arms, checks a per-feature leakage canary, and refuses promotion
if any gate fails. The detailed slate is [`docs/hypotheses.md`](docs/hypotheses.md).

## What this checkout ships

* **Unique method lane:** `H85-scale-space-detrended-slope-persistence`. It takes only official
  feature band 19, `det_elev_slope`, computes Gaussian gradient magnitude at four fixed scales,
  takes the scale-persistence maximum, then emits separated local peaks off the catalogue. It is
  not a copy of h33, a copied raster, a catalogue-tip graph, a multi-band Radon field, or a
  prior submodular submission.
* **Three experiments, no more:** single scale; two-scale envelope; four-scale envelope. The
  four-scale arm is eligible only because it beats the single-scale control on the same holdout.
* **Safe writer:** the retained evidence artifacts are one single-band `float32` GeoTIFF,
  exact sample CRS/shape/transform, all pixels finite, all values in `[0,1]`, zeros outside
  the finite footprint, and zero known catalogue pixels. This directly addresses the portal
  error “Predicted values must be in range [0, 1]”; format validity does **not** override the
  failed uniqueness gate.
* **Independent receipts:** [`evidence/run_card.json`](evidence/run_card.json), validator,
  leakage canary, experiment table, and registry uniqueness audit. Every evaluation score is
  labelled `HOLDOUT-DTI`; a live number is `ORGANIZER-CONFIRMED` only after a portal receipt.
* **Static GitHub Pages site:** [`docs/index.html`](docs/index.html) is the user-facing status
  page; the executive review guide is [`docs/executive-summary.html`](docs/executive-summary.html).

## Review-only artifact workflow

1. Open the site and read the red **DO NOT SUBMIT** status before opening any download.
2. Use the `-zeros.tif` and one-TIFF `.zip` files only to reproduce or inspect the validator
   receipt. They are not a promoted competition candidate.
3. The formal candidate's unique name and short note are recorded for provenance, but the
   overlap gate blocks both upload and slot selection. The separate selector control is also
   blocked: its 0.40 internal cap did not make the final dots unique.
4. Review the competition rules and any generative-AI disclosure required by the organizer.
   No portal action is taken by this repository and no credentials are requested or stored.

## Reproduce the local pipeline

The small grid/catalogue mirrors are committed in `data/raw/`; the roughly 419 MB feature stack
is intentionally not committed. Restore it from the hash-pinned public GitHub bridge, then run
the pipeline:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
bash scripts/restore_feature_stack.sh
.venv/bin/python scripts/prepare_data.py --features data/training_features.tif
.venv/bin/python scripts/run_experiments.py \
  --features data/training_features.tif \
  --registry-root /path/to/local/registry/repositories
.venv/bin/pytest
```

The final command writes a format-valid candidate under `docs/downloads/` and receipts under
`evidence/`; it may and in this checkout does end with a `negative` verdict when uniqueness
fails. The restore path is a mirror, not a bypass of DrivenData authentication. On an
unrestricted machine the official data-tab download can be used instead; see
[`scripts/download_competition_data.sh`](scripts/download_competition_data.sh).

## Session brief captured from the request

This section is the standing project prompt and must be read before each future run:

> Generate a **unique TIF submission** for the GEMS competition. Never copy a previous submission
> except for learning/education. Make the file obviously safe to download and submit. Review the
> complete prompt and validate the inspection through the project without human intervention.
>
> Follow the parallel-run protocol: stay in one method lane; compare the surface before placement
> and final dots against the registry; stop if rank correlation exceeds `0.90` or more than `70%`
> of dots fall within `3 px` of a registry raster. Reuse the template's cached feature stack,
> `evaluate_holdout.py`, and `submission_writer.py`. Withhold whole fault segments with a buffer,
> derive catalogue features only from visible faults, mask visible faults pixel-exactly, score
> pooled DTI with `alpha=0.2`, `beta=0.8`, and a `300 m` triangular kernel, and report a `95%`
> CI. Test every feature alone for leakage; effective AUC above `0.90` is a leakage canary.
> Run no more than `3` experiments and do not spend a weekly submission slot in the experiment.
>
> Before implementation, write `3–5` geological hypotheses. Each must name the layer(s), physical
> signature, reason it could find a fault missing from the USGS/INGENIOUS catalogue, difference
> from existing work, rank by expected DTI improvement and cost, and name/check a free official
> source if new data are necessary. Keep official links and irregularities auditable. Explain
> the reported h33 result and the gap to the reported leaderboard values without hallucinating a
> score. Generate a unique, validated, easy-to-download GeoTIFF and an executive submission guide.
>
> Build a clean GitHub Pages site. Include the competition overview, official/manual-review
> sources, limitations, current data placement status, the range-error fix, a unique name and a
> note of at most `140` characters. Preserve the Core Values **Maximize P(Win)** and **Own the
> Outcome** while reporting negative results honestly. Run three passes: implement and verify;
> review bugs/edge cases; re-check the entire request and improve it. Open a pull request from
> the fixed Arena branch; do not switch branches. Merging is allowed only after all checks and
> review receipts pass.

The original link set is preserved in [`registry/sources.json`](registry/sources.json), and the
long-form research record is [`research/geothermal-knowledge.md`](research/geothermal-knowledge.md).

## Limitations and what is needed next

* The agent cannot authenticate to DrivenData, see private labels, or receive a portal score.
  A real score must be copied from a submission-page receipt and labelled `ORGANIZER-CONFIRMED`.
* The feature stack and core files are hash-pinned owner mirrors. The hashes prove local byte
  stability, not organizer authenticity. Replace them with an official account download when
  available and retain the receipt.
* The catalogue holdout is a useful engineering gate but its truth is the known catalogue; it
  cannot prove discovery of private new faults. The structural H85 surface can also be fooled by
  shorelines, terraces, roads, mines, lithologic contacts, and processing seams.
* NASA ASF/OPERA deformation, USGS ComCat, USGS 3DEP, GeoDAWN radiometry, heat flow, and GDR
  chemistry are promising future inputs. The current outbound policy did not permit fetching
  their non-GitHub hosts, so they are documented but deliberately not used in this lane.
* The separate selector control was run only as a diagnostic after the H85 stop. It emitted
  25,111 dots, still had a maximum final overlap of `0.9557564414`, and is explicitly
  `DO-NOT-SUBMIT`; it is not a repair, experiment, or slot recommendation. A future selector
  must compare any new artifact with current registry receipts, enforce the weekly cap, review
  the official leaderboard, and only then decide whether to spend a slot. This repository never
  auto-submits.

## Core values

**Maximize P(Win.** Choose changes by measured evidence, not optimism: first improve the internal
holdout and format gates, then preserve uniqueness and provenance.
**Own the Outcome.** A failed hypothesis, an unavailable source, a portal error, and a missing
receipt are all deliverables to surface and fix—not reasons to invent a result.

## Repository map

| Path | Purpose |
|---|---|
| `scripts/run_experiments.py` | fixed three-arm run and unique artifact build |
| `scripts/evaluate_holdout.py` | buffered hide-and-recover CLI |
| `scripts/submission_writer.py` | finite `[0,1]` zeros-outside writer |
| `scripts/validate_submission.py` | independent re-read validator |
| `scripts/uniqueness_audit.py` | rank/overlap lane gate |
| `docs/` | GitHub Pages site and executive guide |
| `evidence/` | machine receipts and final JSON card |
| `registry/` | sources, preregistration, irregularities |
| `research/` | geothermal knowledge and limitations |
