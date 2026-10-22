# GEMSDOE85 — automated release audit

## Executive summary: **DO NOT SUBMIT**

**No new unique, submission-cleared TIFF was generated this session.** The literal duplicate-stop rule prevents one: a pinned prior raster's three-pixel halo covers every allowed cell. Renaming an old TIFF, adding noise, or exempting dense priors would not satisfy the request.

- **Website:** [status](docs/index.html) · [submission instructions](docs/executive-summary.html)
- **Automated decision:** [JSON run card](evidence/run_card.json)
- **Historical TIFFs:** `submissions/quarantine/` and `submissions/`; retained for reproducibility, **not approved for a slot**. Quarantine is a publication policy, not access control: repository files remain publicly accessible.
- **No new HOLDOUT-DTI:** no geological experiment ran; no new raster exists. This is a negative **protocol preflight**, not a falsified geological hypothesis.
- **No ORGANIZER-CONFIRMED score:** no authenticated submission-page receipt was available. Scores in the user brief remain owner reports. Current leaderboard position and account quota were not checked.

The prior README's “OK to download and submit” banner was incorrect under the unchanged protocol. Format checks alone cannot establish scientific skill or uniqueness. Historical claims and calculations are preserved, explicitly superseded, in [the pre-review README](research/archive/README-before-release-audit.md). In particular, its chance-corrected overlap exemption, hidden-label back-solve, leaderboard projections, and proposed live-slot experiments are **not current authorization or verified conclusions**.

## Start here every session — standing operator brief

Read this README, `AGENTS.md`, [the retained standing brief and supplied links](research/archive/README-before-release-audit.md#the-standing-brief), `research/review.md`, `research/release-review-2026-10-22.md`, `registry/lane.json`, `registry/template_pin.json`, and `evidence/run_card.json` before making changes. The archived brief is an inherited thematic transcription, **not a verbatim copy of the full chat prompt**; repeated instructions and exact prose were not all preserved by earlier sessions. Do not claim otherwise.

The operative requirements from the current request are:

1. Generate a **unique** single-band GeoTIFF, never copy a previous submission except for education. Make download and submit eligibility obvious at the beginning of the site and executive summary. Validate within the project, without a human inspector. A file must match reference CRS, shape and affine transform, have predictions in `[0,1]`, and no NaN inside the footprint. Provide a unique name and a short note at most 140 characters. Do not equate a format PASS with a release PASS.
2. Follow the **parallel-run protocol**: stay in the explicitly assigned single method lane. Stop as duplicate if rank correlation exceeds `0.90` or more than `70%` of candidate dots are within `3 px` of any registry raster's dots. Check the surface before placement and final dots. No unauthorized dense-prior or chance-correction exemptions.
3. **Reuse, don't rebuild:** use the template's cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Fix shared defects once upstream, never in a private fork. Whole fault segments must be withheld with a buffer; derive all catalogue features only from visible faults, mask visible faults pixel-exactly, and score pooled DTI with alpha `0.2`, beta `0.8`, and the `300 m` triangular kernel.
4. Run each feature alone as a leakage canary; AUC above `0.90` is leakage until proven otherwise. Label performance as **HOLDOUT-DTI**, with evaluator version, withheld positives and a conditional 95% CI, or **ORGANIZER-CONFIRMED** only with a submission-page receipt. A projection is never a score. Geometry, thresholds, hashes and inventory counts are diagnostics, not performance scores.
5. End with one JSON run card naming hypothesis, mechanism, named non-fault mimic, holdout and CI, registry comparison, raster hash, validator result, name and short note, and verdict `promote` or `negative`. Null fields must explicitly mean not run, not fabricated results.
6. Stop at **three experiments or two hours**, whichever comes first. Promotion to a real slot is a separate selector step; do not spend a weekly slot without beating the current comparable holdout best. Negative results are deliverables.
7. Before implementing a geological model, propose and rank three to five geological hypotheses with layers, physical signature, missing-fault rationale, differences from implemented methods, confounders, expected improvement and cost. External data must be free and official, and obtainability checked before calling it viable. [The retained shortlist](research/hypotheses.md) needs reassessment against the merged repo; it is not an assigned lane or a fresh novelty claim.
8. Research the highest reported H33 submission and the competition reference solution; explain plausible mechanisms without claiming hidden truth or unverified receipts. Fault prediction is a geothermal exploration proxy, not direct vent or reservoir discovery. Store research and source limitations for reuse.
9. Build a clear GitHub Pages status and executive-summary site. Official source links must be auditable; inaccessible sources must be labeled, not called freshly verified. The project should automate checks and maintain a current feed without making unauthorized submissions.
10. Work autonomously, resume prior blockers first, state access limits, review in **three passes**, fix defects, open and merge a PR, and report remaining work. Preserve **Maximize P(Win)** and **Own the Outcome** through scientifically honest, end-to-end decisions—not by weakening gates to publish a file.

## What was actually verified this session

The immutable [registry witness](https://github.com/buffedlizard55-lab/17GEMSDOE/blob/6fc71d19d49dca4960d5434bd81b6dd06fcc030a/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif) was downloaded through the GitHub API and its hash matched `registry/learning_manifest.json`. The unmodified shared `saturation_certificate` was executed with reference grid, footprint and catalogue. Its measured halo covers all allowed cells. This is a **REGISTRY-MEASUREMENT**, not DTI or a score projection.

`release_audit.py` verifies shared-code pins and reference hashes, remeasures that obstruction, and independently opens historical TIFFs to check ranges, footprint finiteness, band/type, CRS, shape and transform. It writes no raster. Historical all-finite exports can pass conservative format checks while remaining ineligible. NaN-outside variants are not called conservative-format compliant; this does not prove organizer rejection.

The lane registry is still `unassigned`; the transformed cache manifest has no cache bytes. Different inherited holdout instruments are not comparable. The historical GEO-Pb card also reports raw overlap above the stop limit and an experiment-budget overrun; these cannot be excused as merely a refinement or chance effect.

## Why H33 may have worked — and can we beat it?

Sparse off-catalogue predictions can reduce redundant prediction mass under a distance-weighted maximum-cover objective. That is a plausible explanation for H33's efficiency. It does not prove why its **owner-reported** result occurred. Scores and dot counts do not uniquely identify hidden true-positive credit, false-positive mass or undiscovered fault length. Matched ablations and organizer receipts are required for stronger claims. No candidate in this session demonstrated a higher score or a same-instrument holdout improvement. See [H33 analysis](docs/why-h33.html).

## Reproduce the release checks

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
# Fetch educational priors privately; hash-pinned, not organizer-authenticated.
.venv/bin/python scripts/restore_learning.py
.venv/bin/python scripts/release_audit.py  # expected exit 2: BLOCKED, not success
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/check_site.py
.venv/bin/python -m pytest -q
```

The small reference TIFFs currently tracked in `data/` are needed for the historical-format audit. Larger raw data and cache files remain ignored. Retired generation/export entrypoints exit blocked and cannot republish a legacy candidate. No template bytes were modified. CI runs offline contracts and checks reproducible site generation; it cannot refresh an authenticated organizer feed.

## Official sources and access boundaries

- [Organizer task and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official reference code](https://github.com/drivendataorg/gems-prize-reference-solution) — repository availability verified through GitHub API this session.
- [Rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS GDR](https://gdr.openei.org/submissions/1391)

Only the GitHub source was freshly accessible here. DrivenData, USGS, GDR, the PDF host and Dropbox are outside the sandbox's allowed network hosts. Inherited source notes are not fresh verification. No DrivenData session, eligibility confirmation, organizer receipts or remaining quota was available. GitHub credentials are handled by the configured CLI, never requested in chat.

## Next session — dependency order

1. Obtain an explicit method-lane assignment and an authorized resolution of the saturated-registry policy conflict. Until then, do not generate another TIFF.
2. Supply the exact pinned transformed feature stack and verify provenance; raw features are not a substitute.
3. Establish a current incumbent under the same shared whole-component buffered splits, pooled metric and paired spatial uncertainty. Audit inherited private evaluators before reusing any numbers.
4. Reassess the four retained research hypotheses against all merged implementations; run feature canaries before selecting an experiment. No data-dependent method is declared viable until bytes and provenance are checked.
5. Only after scientific, uniqueness and format gates pass should the separate selector consult authenticated quota and enable a one-click TIFF download. Preserve the organizer receipt and comply with disclosure/competition rules.
