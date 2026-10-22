# GEMSDOE85 — DOE GEMS Prize (DrivenData #306): Lane H85

**Read this first, every session.** This repository exists to generate ONE unique,
validated, easy-to-download GeoTIFF submission for the DOE GEMS competition, and to
make it *obvious* whether that file is OK to download and submit — with the inspection
done by code, not by a human.

## ⬇ Submission status

See the live banner in [`docs/index.html`](docs/index.html) (GitHub Pages) — it is
generated from the machine validator receipt. The executive summary is
[`docs/executive-summary.html`](docs/executive-summary.html). The submission file,
its `.zip`, and its audit JSON live in `docs/downloads/`.

**Portal error fixed by construction:** the user previously received
`"Predicted values must be in range [0, 1]"`. Every primary download here is
single-band float32, EPSG:32611, 3730×3292, **all-finite (nodata=None, no NaN,
no −3.4e38 sentinel), every value in [0, 1]**, re-validated from the written bytes
by `scripts/validate_submission.py` before the site may say "OK TO SUBMIT".

---

## The brief (standing prompt for this project — read every session)

> **PARALLEL-RUN PROTOCOL**
> 1. **LANE.** Stay inside the single method lane. If the raster's rank-correlation
>    with any registry raster exceeds **0.90**, or more than **70%** of dots fall
>    within 3 px of one registry raster's dots, log it as a duplicate and stop.
>    Check on the surface before placement AND on the final dots.
> 2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack,
>    `evaluate_holdout.py` and `submission_writer.py`. Holdout = hide-and-recover:
>    withhold whole fault segments with a buffer, derive every catalogue-based
>    feature only from visible faults, mask visible faults pixel-exactly, score
>    pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool
>    is wrong, fix it once in the template and report it; never keep a private fork.
> 3. **LABEL EVERY NUMBER** as HOLDOUT-DTI (evaluator version, number of withheld
>    positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page
>    receipt). A projection is never written as a score.
> 4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any
>    result. AUC above 0.90 means leakage until proven otherwise.
> 5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; the named
>    non-fault process that could mimic it; holdout DTI + CI; correlation/overlap
>    vs registry; raster sha256; validator output (no NaN inside the footprint,
>    values in [0,1], CRS/shape/transform match); submission name + note of at
>    most 140 characters; verdict promote / negative. Negative results are deliverables.
> 6. **BUDGET.** Stop after 3 experiments or 2 hours. Promotion to a real slot is a
>    separate selector step, within the weekly cap.
>
> Generate 3–5 candidate geological hypotheses not yet tried, each naming: the
> specific layer(s), the physical signature targeted, why it should catch a fault
> missing from the USGS/INGENIOUS catalogue rather than one already in it, and how
> it differs from anything already implemented. Rank by expected DTI improvement
> and implementation cost. Validate the top candidate on the spatially-blocked
> holdout before touching a weekly submission slot. If a candidate can't be
> validated without new external data, name the specific free official source and
> check obtainability first. No hallucinations; verify line by line from official
> sources; flag irregularities.
>
> **Core Values.** *Maximize P(Win)* — every decision weighs tradeoffs and risk to
> maximize the probability of winning. *Own the Outcome* — own results end to end;
> when problems arise and we have the means to act, act without waiting.

### Lane declaration (see IR-85-01)

No single method paragraph was supplied with this session's prompt (flagged as
**IR-85-01** in `registry/irregularities.json`). The lane adopted, declared before
any results were seen, is:

> **Lane H85:** a *fold-proper supervised detector* (HistGradientBoosting on the
> template 35-channel stack + 20 external channels; **no catalogue-derived
> feature**) whose probability surface is emitted by the template's metric-exact
> lazy-greedy max-coverage emitter, confined to the footprint and to pixels
> >2 px from the catalogue, at the 37,654-dot operating point. Two label-free
> surfaces (orientation consensus; strain-gated lineament) are run as the other
> two permitted experiments. The dotted-ridge registry family (H19-5 → d1.5 →
> d2.8 → h33-2-b2) is used **only as holdout controls**, never as a candidate.

## Why the best registry file scored 0.2778 (ORGANIZER-CONFIRMED) — and the path past it

Full analysis: [`docs/research/why-02778-and-how-to-beat-it.md`](docs/research/why-02778-and-how-to-beat-it.md).
Summary: the metric `DTI = TP_w / (0.2·(TP_w+FP_w) + 0.8·|G|)` (α=0.2, β=0.8,
300 m triangular kernel) makes every emitted pixel cost 0.2 of denominator mass;
a dot improves the score iff its expected kernel credit exceeds `0.2·DTI`
(= 0.0556 at 0.2778). The winning file is a *binary, Poisson-thinned (d≈2.8 px),
catalogue-halo-pruned (≤2 px)* subset of a strong multi-physics ridge field —
thinning removes dots whose coverage is already supplied by a neighbour (they
would pay FP mass for ~zero marginal TP). Beating it requires a **better-ranked
surface** at the same emission discipline, not more dots: that is exactly what
Lane H85 tests, and the holdout — not hope — decides.

Current competition leaderboard high reported in the brief: **0.4413**
(ORGANIZER-CONFIRMED per brief; no file/hash crosswalk is available, IR-85-04).

## Hypotheses

Five candidates, ranked, with layers/signatures/mimics/data-dependency:
[`docs/research/hypotheses.md`](docs/research/hypotheses.md). Three were run
(budget = 3 experiments): H85-A (supervised, top candidate), H85-B (orientation
consensus), H85-C (strain-gated). H85-D/E are documented, ranked, and not run.

## Results (this session — verdict: NEGATIVE, honestly)

All in `evidence/`; HOLDOUT-DTI = `gems85-pooled-hide-v1`, n = 24,440 withheld
positives, 8 cells (4 quadrants × 2 draws), cluster-bootstrap 95% CI:

| candidate / control | HOLDOUT-DTI | 95% CI |
|---|---:|---:|
| E1 H85-A fold-proper HGB @37,654 (best budget of 20k/25k/37,654/44,090/55k sweep) | 0.0984 | [0.079, 0.118] |
| E2 H85-B orientation consensus | 0.0366 | [0.029, 0.044] |
| E3 H85-C strain-gated lineament | 0.0317 | [0.022, 0.040] |
| CTRL d2.8 raster (ORGANIZER-CONFIRMED 0.2600) — **valid promotion bar** | **0.1023** | [0.085, 0.122] |
| CTRL h33-2-b2 raster (ORGANIZER-CONFIRMED 0.2778) — invalid bar, IR-85-08 | 0.0046 | [0.004, 0.005] |

Leakage canary: no feature alone AUC > 0.90 (max single channel 0.600; E1 field
0.673). Uniqueness: max |Spearman| vs registry 0.224 (≤ 0.90 ✓); dot overlap vs
comparable dotted submissions 0.397–0.497 (≤ 0.70 ✓) but > 0.70 vs three
saturated registry rasters under the strict reading (IR-85-07 — logged, promotion
stopped). The generated artifact (37,654 dots, sha256 in the run card) is
validator-clean but is **NOT promoted: 🔴 DO NOT SUBMIT**. Next levers, in order:
H85-D spring-chain (data in hand), sub-km USGS FDSN seismicity (official/free,
sandbox-blocked), better base detector — each needs its own 3-experiment budget.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group all        # sha256-pinned mirrors (no DrivenData auth)
.venv/bin/python scripts/run_experiments.py data /tmp/gems85_cache   # 3 experiments + controls + canary
.venv/bin/python scripts/build_submission.py data /tmp/gems85_cache <WINNING_METHOD> [budget]
.venv/bin/python scripts/check_uniqueness.py data /tmp/gems85_cache docs/downloads/<file>.tif <registry dirs>
.venv/bin/python scripts/validate_submission.py data docs/downloads/<file>.tif
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest tests -q
```

Data placement: competition rasters are login-walled at DrivenData; this repo
restores them from the fleet's sha256-pinned GitHub mirrors
(`registry/data_manifest.json`, provenance: owner-supplied mirror, NOT
organizer-authenticated — IR-85-03). `data/` is gitignored.

## Limitations / what is still needed

- No DrivenData credentials in this sandbox: the submission cannot be uploaded
  from here; the user downloads the validated `.tif` from the site and submits it.
- Holdout truth is the visible catalogue; it cannot reward a genuinely new fault
  (fleet-known limitation IR-32-PROXY-01, inherited). Holdout is a screen, and
  every live number remains ORGANIZER-CONFIRMED only via a submission receipt.
- 3 GB RAM sandbox: full-grid work is chunked/memmap-backed; training is CPU HGB.

## Official sources (verify line by line)

- Competition + metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Rules (NLR PDF): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- INGENIOUS: https://gbcge.org/current-projects/ingenious/
- EPSG:32611: https://epsg.io/32611
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- GDR submission 1391 (wellsprings): https://gdr.openei.org/submissions/1391
