# GEMSDOE85 — Parity-Resolved Piedmont-Concordant (PRPC) Concealed Fault Synthesis (`Lane H85-P1`)

**DOE GEMS Prize Challenge · DrivenData Competition #306 · Active Lane `H85-P1 (PRPC-Submod)`**

> **SUBMISSION READINESS STATUS (`zero-human automated gate`):** **OK TO DOWNLOAD & FORMAT-VALIDATED FOR UPLOAD — PROMOTED TO WEEKLY SELECTOR (`verdict: promote`, `0` weekly DrivenData slots spent in sandbox)**
>
> - **Primary Competition GeoTIFF:** [`docs/downloads/gems85-h85p1-prpc-knight38k-20261022-b37c8b3c-zeros.tif`](docs/downloads/gems85-h85p1-prpc-knight38k-20261022-b37c8b3c-zeros.tif) (`134,927 B`, `SHA-256: 53055d498c5daf2371962e35508bce049e4491e894f1491bad020f8789ecab53`)
> - **Single-TIFF ZIP Twin:** [`docs/downloads/gems85-h85p1-prpc-knight38k-20261022-b37c8b3c-zeros.zip`](docs/downloads/gems85-h85p1-prpc-knight38k-20261022-b37c8b3c-zeros.zip) (`SHA-256: 1ab48078...`) · **Alternate `NaN`-Outside Twin:** [`docs/downloads/gems85-h85p1-prpc-knight38k-20261022-b37c8b3c-nan.tif`](docs/downloads/gems85-h85p1-prpc-knight38k-20261022-b37c8b3c-nan.tif)
> - **Unique Submission Name:** `gems85-h85p1-prpc-knight38k-20261022-b37c8b3c-zeros.tif`
> - **Submission Note (`122 / 140` chars):** `H85-P1 PRPC: 16-strike odd/even multi-physics + seam-free 1m LiDAR + piedmont/TMI depth + relay OOF HGB + knight r>2.2 38k`
> - **Automated Format & Range Validation:** **`17 / 17` PASS** (`src/gems85/submission.py`) + **`PASS`** (`vendor/gems57/submission_writer.py` & `gates.py`): single-band `float32`, `EPSG:32611`, `3730 × 3292` @ `100 m`, `0` NaN, `0` Inf, all `12,279,160` cells finite in `[0.0, 1.0]`, `37,654` binary `{0, 1}` dots, `0` outside footprint, `0` within `300 m` (`B = 2` Chebyshev) of mapped catalogue.
> - **Leakage Canary (`64` individual features):** **`64 / 64` PASS** (`max symmetric AUC = 0.7724 ≤ 0.90` on `net_dist2_clip`; [`evidence/prpc_leakage_canary.json`](evidence/prpc_leakage_canary.json)).
> - **Spatially-Blocked Holdout (`[HOLDOUT-DTI, evaluator=gems57-pooled-hide-v2, seed=20, buffer_px=3, n_withheld=11,321]`):** **`0.14229`** (`95%` spatial-cluster CI **`[0.12541, 0.15815]`**, `ROC AUC = 0.7748`) — **`+163.3%` (`2.63×`)** over prior `GEMSDOE85` `PR #6 GEO-Pb` (`0.05405` at matched `37,654` dots; `0.07282` at `90,000` dots) and **`+27.8%`** over `GEMSDOE70` `P8-OOF38k` (`0.1113`, live `0.2478` `[OWNER-REPORT]`).
> - **Two-Phase Uniqueness Gate (`73` SHA-256 rasters across `GEMSDOE`–`GEMSDOE88`):** **`PASS`** across all **`71 / 71`** discriminating fault-prediction rasters (`surface max |ρ| = 0.4869 ≤ 0.90`, `dots max |ρ| = 0.0667 ≤ 0.90`, `dots max 3-px forward overlap = 0.5985 ≤ 0.70`, `max Jaccard = 0.0301`; `2` space-covering calibration witnesses separately certified via `vendor/gems57/uniqueness.py::saturation_certificate`).
> - **GitHub Pages Site & Upload Guide:** [`docs/index.html`](docs/index.html) · [`docs/executive-summary.html`](docs/executive-summary.html)

---

## Standing Full User Prompt (Read First at the Start of Every Session)

> **Instruction:** Read this full prompt first at the start of every session before doing anything else.

```text
Please review your current repo for the project. Remember to work on next steps from previous sessions first.

Work on this competition https://www.drivendata.org/competitions/306/competition-doe-gems/ and use the current empty repo GEMSDOE85 to create a complete, verified project for this competition. Also please study and explain why the submission h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros in repo GEMSDOE32 got the high score of 0.2778 and see if you can improve and beat that score, the highest score right now is 0.3195! Make sure you study and understand everything thoroughly at a PhD level. Please also review all the results and findings from the previous experiments in the user's repos GEMSDOE–GEMSDOE88. Please do deep original research on this topic on the scientific discovery of geothermal vents and store your findings as knowledge for this project from official verified sources. Please create a clean and simple GitHub Pages site for this project with all the information and official source links. Finish the whole task and all next steps, then create a pull request and merge to main, and then suggest upgrades and improvements and remaining work and limitations. Work line by line and verify from official verified trusted sources and provide links for manual review, flag irregularities, no hallucinations. No manual input from the user, you must do all work autonomously. State your limitations and what access is needed. Make sure you use free publicly available data if external data is used from official verified sources. Also keep the Core Values of Arena AI "Maximize P(Win)" and "Own the Outcome" as a focal point in building, developing, researching, suggesting upgrades, and implementing this project. Be contrarian and look for data and ideas that other competitors may overlook, while remaining scientifically grounded — the heart of this project is the scientific discovery of geothermal vents.

Crucial requirement: Must generate a UNIQUE tif submission, unlike any of the previous submissions on the GEMSDOE sites, and must be able to download your generated unique submission on the site in the executive summary right at the top. Make sure you do NOT copy any previous submissions, except for learning and education. Also make sure it is obvious at the start of the site/executive summary whether it is ok to download and submit your submission, validated automatically with no human intervention needed. Many previous submissions/sites say "inspection only" or "human inspector", which is NOT acceptable — validation must be automated in the project without human intervention. Remember one previous submission gave an error on the submission form "Predicted values must be in range [0, 1]", so make sure predicted values are in [0, 1], no NaN inside the footprint, and matching the submission format CRS, shape, and geotransform. Also include a unique submission name and <=140-character note string for the submission form to tell submissions apart. Also create an executive summary subpage explaining how to submit in detail. Put the full prompt in the repo README, as the starting point. Read this first at the start of every session before doing anything else.

Before implementing anything, generate 3–5 genuinely new candidate geological hypotheses (not tweaks to existing thresholds). For each, state: the specific layer(s) used, the physical signature or transform you're targeting, why it should catch a fault that's MISSING from the USGS/INGENIOUS catalog rather than one already in it, and how it differs from what's already in the repo. Rank them by expected DTI gain vs. implementation cost, and validate the top candidate against our spatially-blocked holdout before spending a weekly submission slot. If a candidate needs new external data, name the specific free official source and confirm we can actually pull it first. Do not spend a weekly submission slot on an idea that has not beaten our current spatially-blocked holdout best, and try to beat the GEMSDOE leaderboard high of 0.4413!

PARALLEL-RUN PROTOCOL (this session is one of several running at once):
1. LANE: Stay inside the assigned single method paragraph. If your surface's or final dots' Spearman rank-correlation with any registry raster exceeds 0.90, OR >70% of your dots fall within 3 px of any single registry raster's dots, log as duplicate and stop — do not ship it. Check the surface before placement and the final dots after.
2. REUSE, DON'T REBUILD: Reuse the template's cached feature stack, evaluate_holdout.py, and submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive all catalog-based features from visible faults only, mask visible faults pixel-exactly, and score pooled DTI (alpha=0.2, beta=0.8, 300 m triangular kernel). Fix shared-tool bugs once in the template and report them; no private forks.
3. LABEL EVERY NUMBER: Every score must say HOLDOUT-DTI (with evaluator version, withheld positives count, and 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). Never write a projection as a score.
4. LEAKAGE CANARY: Test each feature alone on holdout first; AUC > 0.90 means leakage until proven otherwise.
5. RUN CARD: End with one JSON card: hypothesis, mechanism, named non-fault process that could mimic it, holdout DTI + CI, correlation/overlap vs. registry, raster sha256, validator output, submission name + <=140-char note, and verdict: promote or negative. Negative results are valid deliverables.
6. BUDGET: Stop after 3 experiments or 2 hours. Do not pick real submission slots here — a separate selector step chooses across all parallel runs within the weekly cap.

Use 3 passes: Pass 1 implement and verify; Pass 2 review your work for bugs, missing requirements, unverified assumptions, and edge cases, then fix everything you find; Pass 3 re-check against the original request and polish. Do not stop after Pass 1.
```

---

## 1. Quick Reproduction & Automated Verification Commands

```bash
# 1. Restore SHA-256 verified competition, USGS 3DEP/GeoDAWN external, and scored fleet rasters
.venv/bin/python scripts/restore_data.py --groups core external scored

# 2. Run all 81 unit, shared-contract (vendor/gems57), metric, emission, and PRPC tests
.venv/bin/python -m pytest -q

# 3. Reproduce leakage canary (64 channels) + 3-experiment ablations on both holdout evaluators
.venv/bin/python -u scripts/run_prpc_experiments.py --stage all

# 4. Build full-catalogue LOQO candidate GeoTIFF + ZIP + 73-raster uniqueness audit
.venv/bin/python -u scripts/build_prpc_submission.py

# 5. Sync manifests, deterministically generate GitHub Pages site, and run offline site gate
.venv/bin/python scripts/sync_prpc_manifests.py
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/check_site.py
```

---

## 2. Summary of Deliverables & Research Architecture

| Deliverable | File Path | Key Verified Result |
|---|---|---|
| **PhD Dissection of `0.2778` & Fleet Review (`GEMSDOE`–`GEMSDOE88`)** | [`research/why_02778_and_fleet_review.md`](research/why_02778_and_fleet_review.md) | Proves `Theorems 1–4` (binary `{0,1}` optimality, Dinkelbach marginal bar `0.0588`/dot at `0.2778` & `Spearman = -0.926` dot-count law, static `B=2` holdout censoring `IR-85-008`, and `223.6 m` knight's-move Basin-and-Range strike geometry `IR-85-011`); audits live leaderboard (`#1 xiaofanhu 0.4413`, `#5 0.3539` `[ORGANIZER-LEADERBOARD]`). |
| **Concealed Geothermal Vent Scientific Knowledge Base** | [`knowledge/geothermal-vent-discovery.md`](knowledge/geothermal-vent-discovery.md) | Synthesizes USGS GeoDAWN (`DOI:10.5066/P93LGLVQ`), INGENIOUS GDR #1391 (`DOI:10.15121/1881483`), USGS MT (`P9TWT2LU`), USGS 3DEP 1 m LiDAR, NLR Official Rules (`FY26OSTI-96647`), Sibson fault-valve alteration, and Curewitz/Karson relay-ramp mechanics. |
| **5 Candidate Geological Hypotheses & Controlled Ablation** | [`research/candidate_hypotheses_prpc.md`](research/candidate_hypotheses_prpc.md) | Ranks `H85-P1`..`H85-P5`, verifies free official sources, passes `64/64` single-feature canaries (`max AUC = 0.7724`), and lifts `gems57-pooled-hide-v2` `HOLDOUT-DTI` monotonically: `ctrl_uniform = 0.04383` → `ctrl_pr6_geopb = 0.05405` → `E1 = 0.05511` → `E2 = 0.06412` → **`E3 = 0.14229` (`CI95 [0.12541, 0.15815]`)**. |
| **PRPC Multi-Physics & Fold-Proper Relay Engine** | [`src/gems85/prpc.py`](src/gems85/prpc.py) · [`tests/test_prpc.py`](tests/test_prpc.py) | 16-strike parity-locked odd/even operators, 400 m cosine LiDAR seam feathering, `TMI_up150/TMI` basement depth persistence, piedmont vs volcanic-mesa decontamination, fold-proper wash-gap/relay features, component-OOF monotonic `HGB`, and `min_sep_px=2.20` knight allocator. |
| **Validated Unique Competition GeoTIFF + Audit** | [`docs/downloads/gems85-h85p1-prpc-knight38k-20261022-b37c8b3c-zeros.tif`](docs/downloads/gems85-h85p1-prpc-knight38k-20261022-b37c8b3c-zeros.tif) · [`evidence/prpc_submission_audit.json`](evidence/prpc_submission_audit.json) | `37,654` binary `{0,1}` dots, `17/17` format checks PASS, `0/71` discriminating uniqueness firings (`max 3-px overlap = 0.5985 ≤ 0.70`, `surface max |ρ| = 0.4869 ≤ 0.90`). |
| **GitHub Pages Site & Executive Summary Upload Guide** | [`docs/index.html`](docs/index.html) · [`docs/executive-summary.html`](docs/executive-summary.html) | Top-of-page readiness banner, one-click downloads, exact 6-step DrivenData upload guide, interactive evidence tables, and offline `scripts/check_site.py` verification. |
| **Protocol JSON Run Card & Irregularities Registry** | [`evidence/run_card.json`](evidence/run_card.json) · [`registry/irregularities.json`](registry/irregularities.json) | Machine-verified protocol run card + 12 documented irregularities (`IR-85-001`..`IR-85-012`). |

---

## 3. Limitations, Access Needed & Next-Tier Upgrades Toward `0.4413`

### Honest Statement of Limitations & Access Needed
1. **Zero Live Organizer Receipts Inside This Sandbox:** No submission has been uploaded to DrivenData from this environment (`0` weekly slots spent). All `H85-P1` scores are `[HOLDOUT-DTI]`; historical fleet scores (`0.2778`, `0.2478`, etc.) are `[OWNER-REPORT]`; live leaderboard standings (`0.4413`, `0.3539`) are `[ORGANIZER-LEADERBOARD]` fetched `2026-10-22`.
2. **Catalogue-Transfer vs Concealed-Truth Epistemic Gap:** Any local hide-and-recover holdout withholds segments of the public USGS/INGENIOUS catalogue, whereas DrivenData's hidden test set (Initial Round) and expert-updated map (Final Round, NLR Rules §3.5) evaluate unmapped concealed faults. Our `0.15 * P_blind` multi-physics floor and `E2_PRPC_Blind_OOF` (`AUC = 0.6245` on 20 km square-hole blind blocks) explicitly hedge against pure catalogue-tip overfitting.
3. **Sandbox Shell Network Allowlist:** Outbound shell access is restricted to `github.com`, `api.github.com`, and `pypi.org`. Direct ingestion of NASA ASF DAAC OPERA Sentinel-1 InSAR velocity tiles (`H85-P4`, <https://search.asf.alaska.edu/>) and USGS ANSS ComCat relocated microseismic hypocenters (`H85-P5`, <https://earthquake.usgs.gov/fdsnws/event/1/>) requires external network access.
4. **CPU-Only Compute Envelope (`2 vCPU`, `3.6 GB RAM`):** Prevented training multi-scale 2D Swin-UNet / ConvNeXt architectures directly on a differentiable 300 m Tversky loss over all `12.28M` pixels. Access to `1× GPU (24–32 GB VRAM)` + `32 GB RAM` is the single highest-leverage compute upgrade.
5. **Uniqueness Scope:** Verified against all `73` locally cached SHA-256 rasters spanning `GEMSDOE`–`GEMSDOE88`; unpushed private files outside those repositories cannot be scanned locally.

### Recommended High-ROI Next Steps (For Future Lanes & Weekly Selector)
1. **Cross-Lane Ensembling in the External Weekly Selector:** Fuse `GEMSDOE85` `H85-P1` (`0.14229` `seed=20`, parity-resolved 16-strike + seam-free LiDAR + knight spacing, `max overlap 0.5985`) with `GEMSDOE86` `H86-FVMB` (`0.14576`, iSPI basement pullback + `±22°` wing-crack SAR-PU) via rank-calibrated probability averaging before a single joint knight-spaced (`min_sep_px = 2.20`) 38k allocation.
2. **End-to-End Differentiable 300 m Tversky U-Net on GPU:** Feed our cached 48-channel parity-resolved multi-physics tensor (`prpc_X_fp_v1.npy`) + 15 fold-proper continuation channels into a multi-scale Dilated ResUNet trained directly on the exact 29-pixel max-pooled DTI loss under 4-quadrant component-withheld cross-validation.
3. **Ingest NASA OPERA `DISP-S1` InSAR & Relocated ComCat Microseismicity (`H85-P4`, `H85-P5`):** Add persistent-scatterer groundwater-barrier phase gradients across flat agricultural/playa basins (Fallon, Dixie Valley, Humboldt Sink) where both LiDAR and radiometrics are attenuated by Holocene muds.

---

## 4. Preserved Historical Lanes in `GEMSDOE85`

All prior merged work on `main` remains intact and auditable:
- **PR #1 (Preflight Contract & Shared `vendor/gems57` Pin):** `vendor/gems57/` remains byte-for-byte unmodified (`33/33` contract tests in `tests/test_shared_contracts.py` passing).
- **PR #3 (Transtensional Pull-Apart + Gravity Worm Duplex Lane):** Preserved under `docs/duplex-lane/`, `src/gems85/*_duplex.py`, and `evidence/run_card_duplex.json`.
- **PR #4 (`H85-A` Fold-Proper HGB Lane):** Preserved under `docs/lane-h85.html` and `submissions/gems85-h85a-*`.
- **PR #6 (`H85-1` `GEO-Pb` 8-Strike Juxtaposition Lane):** Preserved in `src/gems85/geopb.py` and benchmarked directly as `ctrl_pr6_geopb_38k` (`0.05405`) and `ctrl_pr6_geopb_90k` (`0.07282`) inside `evidence/prpc_experiments.json`.
