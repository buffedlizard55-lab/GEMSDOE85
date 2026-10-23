> **ARCHIVAL SNAPSHOT — NOT CURRENT RELEASE AUTHORITY.** Historical candidate, score, lane, test, and download assertions below are preserved for traceability only. They are superseded by the current root `README.md`, `research/review.md`, and `evidence/run_card.json`; no TIFF in these snapshots is cleared for download or submission.

---

# GEMSDOE85 — GEO-Pb: a juxtaposition detector for concealed faults

**DOE GEMS Prize · DrivenData competition #306 · lane H85-1**

A self-driving, fully auditable pipeline that restores the competition data, builds a novel
fault-discovery surface, scores it on a spatially-blocked hide-and-recover holdout, converts it
to a dot field, validates the written GeoTIFF against 17 format checks **with no human in the
loop**, and publishes it on a GitHub Pages site with a one-click download at the very top.

| | |
|---|---|
| **Site** | `docs/index.html` (GitHub Pages: Settings → Pages → `main` / `/docs`) |
| **Submission** | `docs/downloads/gems85-geopb-crest-90000dots-sep4-*-zeros.tif` |
| **Status** | all 17 format checks **PASS** → OK to download and submit |
| **Holdout DTI** | **0.09838**, 95 % CI [0.09022, 0.10654], 4 spatially-blocked folds, 60,988 withheld positives |
| **vs uniform random** | **+0.0298** at matched emitted mass (3.3× the CI half-width) |
| **Duplicate check** | max \|Spearman ρ\| vs 17 registry rasters = **0.012**; chance-corrected dot-overlap lift = 1.00 → distinct |
| **Verdict** | `promote-as-candidate` — cleared the pre-registered gate. **No organizer score exists.** |

```bash
python -m venv .venv && .venv/bin/pip install numpy scipy rasterio pandas scikit-learn pytest
.venv/bin/python scripts/restore_data.py --groups core external scored   # 23 files, SHA-256 verified
.venv/bin/python -m pytest                                               # 25 passed
.venv/bin/python scripts/build_submission.py                             # validate + publish
.venv/bin/python scripts/build_site.py                                   # regenerate docs/
```

---

## The standing brief

> **Transcription note.** The operator's brief arrived as a chat message, not a file. What follows
> is a faithful, complete transcription of its requirements, grouped by topic; wording is the
> operator's where it was preserved verbatim. It is the standing starting point — **re-read this
> section at the start of every session before doing anything else.** Nothing below has been
> softened or dropped. Where a requirement was met, the link says where; where it was not, the
> *Limitations* section says so.

### Objective

Work on the **DOE GEMS Prize Challenge**, DrivenData competition #306
(<https://www.drivendata.org/competitions/306/competition-doe-gems/>). Build, in the empty repo
`GEMSDOE85`, a complete, auditable, self-driving system that produces a **unique,
downloadable, submission-ready single-band GeoTIFF**.

Answer with PhD-level rigor: **why** did the artifact
`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` score **0.2778**, and can we beat it? The target
is to beat the stated leaderboard high (the brief gives 0.3195, and separately 0.4413 as the
GEMSDOE leaderboard high).

### Hard requirements

1. **Generate a UNIQUE TIF submission.** It must not duplicate any artifact on the prior
   GEMSDOE sites. Prior submissions may be studied **for learning/education only**.
2. **It must be obvious on the site whether the generated TIF is OK to download and submit.**
   The one-click download goes in the **executive summary at the very top** of the site.
3. **Validation must be automated in-project — no human inspector** — and must **gate**
   submission. Many prior sites said "inspection only / human inspector"; that is not acceptable.
4. **Fix the prior failure.** A previous submission form upload was rejected with
   **"Predicted values must be in range [0, 1]"**. Values must be in [0, 1], no NaN inside the
   footprint, CRS / shape / geotransform matching the submission format.
5. Provide a **unique submission name** and a **≤ 140-character note** string, so submissions can
   be told apart.
6. Create an **executive-summary subpage** explaining **exactly how to submit**.
7. **Put the full prompt into the repo README** as the standing starting point.
8. **Before implementing**, generate **3–5 new geological hypotheses**. Each must name the
   specific layers, the physical signature/transform, **why it catches a fault _missing_ from the
   USGS/INGENIOUS catalogue** rather than one already in it, and how it differs from what is in
   the repo. Rank by expected DTI gain vs implementation cost. **Validate the top candidate on
   the spatially-blocked holdout before spending a weekly submission slot.**
9. Do **deep original research on geothermal-vent discovery**, stored as reusable knowledge from
   **official verified sources**.
10. Build a **clean, simple GitHub Pages site** with all information and official source links.
11. Run a **three-pass workflow**: implement + verify → review and fix bugs and edge cases →
    re-check against the original request. Do not stop after the first pass.
12. **Finish by creating a pull request and merging it to main**, then list remaining work,
    suggestions and limitations.
13. **State my limitations and what access is needed.**

### How the work must be done

- Work **line by line, verifying from official verified trusted sources**; provide links for
  manual review. **Flag irregularities. No hallucinations.**
- **No manual input from the user** — work autonomously, end to end.
- Use only **free, publicly available, official/verified** external data. If a candidate needs new
  external data, **name the specific free official source and confirm obtainability first.**
- Keep **Arena's Core Values — "Maximize P(Win)" and "Own the Outcome"** — central to building,
  developing, researching, suggesting upgrades and implementing.
- Be **contrarian but scientifically grounded**; find data others overlook. The heart of the
  project is the **scientific discovery of geothermal vents**.
- **Work on next steps from previous sessions first.**
- **Do not spend a weekly submission slot on an idea that has not beaten the current holdout
  best.**

### Parallel-run protocol (this session is one lane of several)

- **Stay in one method lane.** If rank-correlation with any registry raster > 0.90, or > 70 % of
  dots fall within 3 px of one registry raster's dots, **log as duplicate and stop.** Check on the
  surface before placement **and** on the final dots.
- **Reuse the template's cached feature stack, `evaluate_holdout.py`, `submission_writer.py`.
  Fix shared tools in the template, never fork privately.**
- **Holdout = hide-and-recover**: withhold whole fault segments with a buffer; derive
  catalogue-based features **only from visible faults**; mask visible faults **pixel-exactly**;
  score pooled DTI (α 0.2, β 0.8, 300 m triangular kernel).
- **Label every number** as `HOLDOUT-DTI` (evaluator version, number of withheld positives, 95 %
  CI) or `ORGANIZER-CONFIRMED`. **A projection is never written as a score.**
- **Leakage canary**: test each feature alone on the holdout; **AUC > 0.90 means leakage** until
  proven otherwise.
- End with **one JSON run card**: hypothesis; mechanism; named non-fault mimic process; holdout
  DTI + CI; correlation/overlap vs registry; raster sha256; validator output; submission name +
  ≤ 140-char note; verdict promote/negative. **Negative results are deliverables.**
- **Budget: stop after 3 experiments or 2 hours.** Do not pick submissions — promotion to a real
  slot is a separate selector step.

---

## 1. Why `h33-2-b2` scored 0.2778 — the answer

The metric is a distance-weighted Tversky index
([official problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)):
with a triangular kernel `k(d) = (1 − d/R)₊`, `R = 300 m = 3 px`, `α = 0.2`, `β = 0.8`,

```
TPw = Σ_{g∈G} max_{x: d(x,g)≤R} p(x)·k(d(x,g))
FPw = Σ_{x: p(x)>0} p(x)·[1 − max_{g∈G} k(d(x,g))]
FNw = Σ_{g∈G} [1 − max_{x: d(x,g)≤R} p(x)·k(d(x,g))]
DTI = TPw / (TPw + α·FPw + β·FNw + ε)
```

Two exact identities collapse this (derivation in
[`docs/research/metric-algebra.md`](docs/research/metric-algebra.md)):
`FNw = K − TPw` and `FPw = S − M`, where `K = |G|`, `S = Σp` is the emitted mass and
`M = Σ_x p(x)·max_g k` is the mass that sits within 300 m of truth. So

```
DTI = T / ( α·(T + F) + β·K )          with F = S − M
```

Both maxima are grey dilations over the same 29-pixel disc, so the whole metric is exact in
O(29N) — no distance transform, no approximation. A corollary falls straight out: because the
objective is linear in each `p(x)` at fixed support, **binary `p ∈ {0,1}` is provably optimal**;
soft confidence ramps strictly lose. Every artifact in this repo is therefore binary.

**Back-solving the incumbent.** `h33-2-b2` is `h27-4` (40,199 dots, 0.2708) minus the 2,545 dots
within 2 px of the mapped catalogue → 37,654 dots, 0.2778. Solving the reduced form for that pair:

| quantity | value | meaning |
|---|---:|---|
| `T` (captured credit) | **5,470** | ~ 5.5 k pixel-equivalents of new fault recovered |
| `K` (hidden truth mass) | **≈ 14,400 px** | **≈ 144 km of unmapped trace** in the private set |
| `F` (uncredited mass) | **≈ 35,466** | 94 % of the dots earn nothing |
| `A = T/n` (credit per dot) | **0.1453** | ~ 5× a uniform-random dot |
| denominator split | 8,187 α + 11,520 β | **the false-positive tax is 42 %** of the denominator |

So the incumbent is not a good *map*; it is a well-priced *bet*. It wins because 0.1453 credit per
dot at a 42 % tax beats every alternative that was tried, not because it localises faults well.

**Can it be beaten, and how?** The marginal rule — add mass only while the credit it earns exceeds
`t > α·DTI·f/(1 − α·DTI)` — gives a bar of **0.0588 per dot at DTI 0.2778** and **0.0969 at
0.4413**. Fitting the family's own decay `T = 468.4·n^0.2292` gives a marginal of 0.032/dot over
44 k→60 k and 0.0148 over 60 k→121 k. **Both are under the bar: emission tuning on that field is
exhausted.** A blanket background is fatal (a uniform ε floor scores 0.0137). The leader's 0.4413
is reachable either by sustaining the incumbent's credit-per-dot out to ~100 k dots, or by raising
credit-per-dot 1.64× at the same 37,654. **Both require a better field, not better packing** —
which is why this lane spent its budget on a new detector rather than on emission.

Ceilings for calibration: a perfect raster scores 1.0; 3-px-spaced dots along perfect truth score
0.814; an oracle allowed only `K/10` dots scores 0.349.

## 2. The hypothesis — GEO-Pb

Every fault detector across the 60 sibling repositories is a **derivative** operator (Sato/Frangi
ridges, tilt angle, horizontal gradient, Euler deconvolution, worms, coherence). A derivative asks
*"is this field changing fast here?"* But a fault is a **juxtaposition**: it puts two different
geological domains side by side. The right question is the two-sample one — *"do the rocks on the
two sides of this line have different **joint** geophysical signatures?"*

**GEO-Pb** (geophysical probability-of-boundary, after the half-disc `Pb` operator in computer
vision) answers it directly. At each pixel and each of 8 candidate strikes it forms the
**offset difference of a covariance-whitened 10-band stack** across the candidate line — a
windowed Hotelling-style step statistic — then takes the **median of three independent physics
domains** (potential-field/subsurface, airborne radiometric, topographic) so at least **two of
three must agree**, multiplies by an **along-strike persistence** term over 1.5 km, maximises over
orientation, and finally **crest-thins** by non-maximum suppression across its own normal.

*Why it should find faults the catalogue lacks:* the labels are USGS Quaternary faults plus
INGENIOUS — structures mapped from **surface** evidence. A fault concealed under Holocene alluvium
has no scarp, but it still juxtaposes different basement susceptibility, different cover thickness
and different surface geochemistry. **Each band changes a little; the joint 10-vector changes a
lot.** That is precisely the class a scarp-first catalogue under-samples and a derivative detector
under-weights.

*Declared mimics (named before measuring):* distal alluvial-fan margins and Lake Lahontan
shorelines (lobate — killed by the straightness term); aeromagnetic/radiometric acquisition seams
(single-domain — killed by the two-of-three vote; azimuth audit shows max single-orientation share
0.254 < 0.35); **erosional volcanic mesa and lava-flow margins — straight, multi-domain, and
declared irreducible.**

Full ranked hypothesis set (5 candidates, with layers, transforms and cost):
[`docs/research/hypotheses.md`](docs/research/hypotheses.md).

## 3. Results

All numbers are **HOLDOUT-DTI** (evaluator `gems85-holdout-1`, 60,988 withheld positives,
4 spatially-blocked folds, block 200 px, buffer 5 px). **None is a competition score.**

| surface | AUC | n = 37,654 | n = 60,000 | n = 90–100 k |
|---|---:|---:|---:|---:|
| **geopb_crest · sep 4 px** | 0.5036 | **0.07475** | **0.08971** | **0.09838** |
| geopb_crest · sep 2.8 px | 0.5036 | 0.06953 | 0.08513 | 0.09494 |
| geopb_fused (no NMS) | 0.5884 | 0.06877 | 0.08231 | — |
| supervised GBM, 24 ch **with** GEO-Pb | 0.5728 | 0.06230 | 0.07759 | 0.09437 |
| supervised GBM, 21 ch **without** GEO-Pb | 0.5685 | 0.05713 | 0.07411 | 0.09200 |
| `ctrl_random` (uniform) | 0.5000 | 0.05374 | 0.06854 | — |
| `ctrl_grad_rtp` (derivative) | 0.5329 | 0.04983 | 0.06096 | — |
| `ctrl_sato_elev` (derivative) | 0.4742 | 0.01013 | 0.01763 | — |

Four findings worth keeping:

1. **GEO-Pb adds real, independent signal.** Pre-registered ablation inside a 24-channel gradient
   boosting model: adding the 3 GEO-Pb channels moves holdout DTI **+0.00517 at 37,654 (4/4 folds
   positive)**, +0.00348 at 60 k (3/4), +0.00236 at 100 k (3/4); mean withheld AUC +0.0042.
2. **The persistence term is a null result.** L = 1, 15 and 25 px are statistically
   indistinguishable (0.0683 / 0.0666 / 0.0679). The straightness story is *not* supported —
   published as a negative, not quietly dropped.
3. **Supervised learning lost to the hand-built field** (0.0623 vs 0.0695 at the same budget),
   reversing the GEMSDOE32 §13.2 precedent where a supervised field beat a hand-crafted one by
   15 %. Published as a negative.
4. **Topographic ridge crests are *anti*-correlated with faults.** `ctrl_sato_elev` scores
   **5× worse than uniform random** (AUC 0.474). Several sibling lanes are built on exactly this
   operator.

### Instrument calibration — and the defect it exposed

Before trusting the holdout, it was calibrated against the 17 registry rasters whose live scores
the operator's ledger records (`evidence/instrument_calibration.json`):

- ρ(static holdout score, live score) = **−0.2222, p = 0.391** — *no* relationship.
- ρ(number of emitting pixels, live score) = **−0.9257, p < 1e-4** — the live board was, over this
  sample, almost perfectly explained by how few dots you emitted.

**IR-85-001.** A catalogue-truth holdout **cannot** fairly score a *static* raster that already
hard-excluded the catalogue: `T = 0` by construction. (Re-reading the shipped file through the
official metric confirms it: self-DTI vs the catalogue is exactly **0.0**.) The fix, implemented
in `src/gems85/holdout.py`, is that `score_folds` takes a **callable** and **rebuilds the rule per
fold from the visible faults only**. Every number in the table above uses that path.
`score_static` is retained for duplicate checks only and is labelled as biased.

**IR-85-002** (found and fixed in this lane's duplicate checker): the protocol's raw "70 % of dots
within 3 px" rule is **unconditionally true against any space-filling registry raster** — the
`r13-lattice` artifact dilates to cover the whole footprint, so *every* candidate, including
uniform random, "overlaps" it at 99 %. A chance correction (`overlap / coverage`, duplicate only
when lift > 1.5) was added. **Both irregularities are logged, not worked around.**

### Honest verdict on shipping

GEO-Pb's lift over uniform random on the holdout is **1.3–1.4×**. The incumbent's credit-per-dot
on the **live** board is **≈ 5×** random's. Those are different truth sets, so they are not
directly comparable — but transferring the measured ratio with the one scale factor the record
supports projects this file to roughly **0.17–0.23 live [MODEL, not a score]**, i.e. **probably
below the 0.2778 incumbent.** That projection is stated on the site, in the run card, and here.
This lane therefore publishes a **validated candidate**, not a recommendation to spend a weekly
slot — exactly the separation the protocol asks for.

## 4. Repository map

```
src/gems85/      grid.py metric.py holdout.py geopb.py emission.py
                 baselines.py submission.py featurestack.py
scripts/         restore_data.py build_registry.py calibrate_instrument.py
                 run_experiments.py run_supervised.py run_budget_sweep.py
                 build_submission.py build_site.py
evidence/        instrument_calibration.json experiments.json exp_crest.json
                 supervised_ablation.json budget_sweep.json duplicate_check.json
                 run_card.json
registry/        data_manifest.json scored_artifacts.json submission.json
docs/            index.html executive-summary.html method.html data.html
                 downloads/*.tif  research/{hypotheses,metric-algebra}.md
knowledge/       geothermal-vent-discovery.md
tests/           test_metric.py test_emission.py        (25 passing)
```

## 5. Limitations, access needed, and what is still open

**Limitations of this agent and environment**

- **No organizer score can be produced here.** Nothing in this repository has been scored by
  DrivenData. Every number is a local holdout measurement; the words `HOLDOUT-DTI`, `[MODEL]` and
  `OWNER-REPORT` mark which is which.
- **Network is allowlisted** to `github.com`, `api.github.com`, `codeload.github.com`, `pypi.org`,
  `files.pythonhosted.org`, `registry.npmjs.org`. `drivendata.org`, `usgs.gov`,
  `gdr.openei.org` and `*.github.io` are **unreachable from the sandbox shell**. The competition
  data is therefore restored from operator-supplied GitHub mirrors, **integrity-pinned by SHA-256
  but not organizer-authenticated**. The rules PDF, the GeoDAWN DOI landing page, the INGENIOUS
  submission page and the community thread on fault masking are **cited but unverified here**.
- **The live-score ledger is OWNER-REPORT.** The 17 live scores used for calibration were copied
  from the operator's records, not from DrivenData receipts. If any is wrong, the calibration and
  the 0.2778 back-solve move with it.
- **2 CPU cores, 3 GB RAM, no GPU.** This capped the supervised arm at a 24-channel gradient
  boosting model on sub-sampled pixels; a CNN on the full stack was not affordable.
- **The holdout's truth is the known catalogue; the competition's truth is a private set of faults
  deliberately absent from it.** This is the central epistemic gap and it cannot be closed from
  inside the repository.

**Access that would change the outcome**

1. A **DrivenData session** (or any organizer-authenticated fetch) to verify the data hashes, read
   the rules PDF, and confirm the 17 live scores.
2. **Two to three real submission slots** to measure this field's live credit-per-dot at 37,654 and
   90,000 dots — that single experiment resolves the budget question the holdout cannot.
3. **GPU + 32 GB RAM** for a U-Net on the full 24-channel stack with the official Tversky loss.
4. **InSAR (Sentinel-1 / ESA)** and **ANSS/NSHM seismicity**, neither reachable here, to test
   hypotheses H85-3 and H85-4.

**Remaining work, in priority order**

1. **Resolve the budget question empirically.** The holdout says 90 k dots; the live record says
   37–60 k. The two disagree because the marginal bar scales with the score already achieved
   (0.024/dot at holdout 0.08 vs 0.059/dot at live 0.278). The 60 k and 37,654 alternates are
   published for exactly this test.
2. **Retire the persistence term** (null result) and spend the parameters on orientation
   resolution — 8 strikes is coarse; 16 is affordable.
3. **Fuse GEO-Pb with the h19-5 lineage field.** The ablation shows GEO-Pb's contribution is
   *additive* to a 21-channel derivative stack; the incumbent's field is not in that stack. A
   union-of-ranks hedge is the most likely route past 0.2778 and was not affordable here.
4. **Cross-lane de-duplication at the dot level** before any slot is spent, using the
   chance-corrected rule from IR-85-002.
5. **Re-derive the mesa/flow-margin confounder** with a geological-map mask (USGS SGMC volcanic
   units) — the one declared-irreducible mimic, and the clearest route to higher credit-per-dot.

## 6. Official sources

| what | link | state |
|---|---|---|
| Competition home | <https://www.drivendata.org/competitions/306/competition-doe-gems/> | fetched |
| Problem description (metric, format, structure) | <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> | **fetched — authoritative** |
| Leaderboard | <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/> | fetched 2026-10-22 — high **0.4413** (xiaofanhu) |
| Organizer reference solution | <https://github.com/drivendataorg/gems-prize-reference-solution> | cloned — U-Net + Tversky, confirms α/β |
| USGS GeoDAWN data release | DOI <https://doi.org/10.5066/P93LGLVQ> | cited, not fetchable here |
| USGS SGMC | <https://mrdata.usgs.gov/geology/state/> | cited, not fetchable here |
| INGENIOUS fault database | <https://gdr.openei.org/submissions/1391> | cited, not fetchable here |
| Challenge rules (PDF) | <https://docs.nrel.gov/docs/fy26osti/96647.pdf> | cited, not fetchable here |

Everything used is US-government public domain (USGS GeoDAWN, USGS 3DEP, USGS SGMC) or supplied
by the competition.

## 7. The other lane in this repository

GEMSDOE85 was worked by **two independent lanes in parallel**. This README documents the
**GEO-Pb juxtaposition** lane (H85-1). The **transtensional pull-apart + gravity worm duplex**
lane (`arena/29a39923`) reached `main` first; its code, evidence and three submissions are
preserved here untouched:

| duplex-lane artifact | where it now lives |
|---|---|
| site | `docs/duplex-lane/index.html`, `docs/duplex-lane/executive-summary.html` |
| submissions | `docs/downloads/gems85-h85-{duplex-pullapart-worm,ti-pure,worm-pure}-*` |
| run card | `evidence/run_card_duplex.json` |
| scripts | `scripts/duplex_lane/` |
| modules | `src/gems85/{emission,submission}_duplex.py`, re-exported from the canonical modules |
| hypotheses | appended to `docs/research/hypotheses.md` |

**The two lanes' holdout numbers are not comparable.** Different evaluators, different fold
geometry, different withheld-positive counts. The duplex lane reports 0.1542; this lane reports
0.09838. Ranking them against each other would be precisely the apples-to-oranges error that
IR-85-001 and the instrument calibration exist to prevent. Both sets of artifacts are published;
**neither has an organizer score.**

What the merge *did* establish, which is worth more than a ranking:

- **One metric implementation now serves both lanes.** `src/gems85/metric.py` gained
  `dti_exact`, `dti_binary`, `dti_bruteforce`, `marginal_inclusion_threshold`, `kernel`,
  `RADIUS_PX`, `_OFF` and `_shift` as a compatibility layer, so the duplex lane's `emitter.py`
  and `evaluate_holdout.py` run against the same ruler this lane used.
- **`tests/test_metric.py` now asserts the fast O(29N) dilation path equals a literal
  brute-force transcription** of the published definition, on both binary and soft predictions.
- **The duplex lane's independent validator passes all five of this lane's GeoTIFFs**
  (`All downloads PASS`) — a cross-lane confirmation of format correctness from code this lane
  did not write.

### Defects found during the merge (all pre-existing on `main`, all logged not silenced)

| id | defect | resolution |
|---|---|---|
| **IR-85-003** | `tests/test_shared_contracts.py` imports a package `gems57` that does not exist in this repo — a template copied without renaming. It failed at **collection**, taking the whole suite down. | `pytest.importorskip` with a stated reason |
| **IR-85-004** | `tests/test_project.py` asserts `safe_to_submit is False`, `raster_sha256 is None` and that `docs/` contains **no** `.tif` — the exact inverse of this project's requirement. It also imports a `build` entry point that never existed. | quarantined with a written reason, not deleted |
| **IR-85-005** | `tests/test_gems85.py::test_writer_validator_roundtrip` placed its test mask at `[100:200, 100:200]`, which is **entirely outside the survey footprint** (0 of 10,000 cells valid). The writer correctly zeroed it; the test then asserted `0 == 1156`. **The writer was right and the test was wrong.** | mask moved to an interior block and intersected with the footprint |
| **IR-85-002** | the parallel-run protocol's raw "70 % of dots within 3 px" duplicate rule is unconditionally true against a space-filling registry raster | chance-corrected lift added |

`main`'s `src/gems85/metric.py` was an **empty file**, so every duplex-lane test that imported
from it could never have passed. After the merge the full suite is **75 passed, 1 skipped**.
