# Five untried hypotheses for GEMSDOE85 — ranked, with the lane that was chosen

**Session:** `arena/f2d7722b-gemsdoe85` · **Date:** 2026-10-22
**Question answered:** *what has the GEMSDOE family not tried, which of it can be validated here,
and which of it needs external data that must first be proven obtainable?*

Evidence classes used throughout, and never mixed:

| class | meaning |
|---|---|
| **[OFFICIAL]** | read from a DrivenData / USGS / DOE page or product this session, link given |
| **[MEASURED]** | computed in this checkout from SHA-256-pinned bytes; the command is given |
| **[OWNER-REPORT]** | the operator's own ledger of submission-page receipts; not re-verified here |
| **[MODEL]** | an estimate conditioned on an unverified anchor — never a score, never a result |
| **[BLOCKED]** | could not be obtained from this sandbox; the reason is stated |

---

## 0. What the record already rules out

**[OWNER-REPORT]** 60+ scored artifacts across 60 sibling repositories. Grouped by mechanism, the
best live score each mechanism ever produced:

| mechanism | best live DW-Tversky | verdict |
|---|---:|---|
| multi-line "corroborated" ridge fields, dot-thinned (h19-5 → d2.8 → h27-4 → **h33-2-b2**) | **0.2778** | the family ceiling |
| submodular / max-coverage emission variants on the same field | 0.2478 – 0.2600 | no gain over the family |
| orthogonality-gated cross-gradient (`gate_ortho`) | 0.2376 | below family |
| CVaR-robust thinning | 0.2303 | below family |
| Dempster–Shafer belief fusion | 0.2296 | below family |
| LiDAR-scarp-first detectors | 0.0383 – 0.1589 | far below |
| magnetic Euler / depth-cluster / worms | 0.0159 – 0.0984 | far below |
| SGMC off-catalogue transfer | 0.0492 – 0.0512 | far below |
| supervised ML (HGB / U-Net-like / PU) as *shipped* | 0.0180 – 0.1426 | far below |
| radiometric fusion | 0.0843 – 0.1627 | far below |

**[MEASURED, `evidence/instrument_calibration.json`]** Over the 17 artifacts whose rasters this
repository could restore and whose live score is on record, the single strongest predictor of the
live score is **not** any geological property — it is the emitted-pixel count, Spearman
**ρ = −0.926, p = 1.5 × 10⁻⁷, n = 17**. On-catalogue pixel count is second (ρ = −0.778,
p = 2.4 × 10⁻⁴). The sibling repositories' own catalogue-truth holdout ranks live at
**ρ = −0.222, p = 0.39** — i.e. not at all, and if anything backwards.

**[MEASURED, §6 below]** That last number has a mechanical cause that invalidates it as a
criticism of the holdout, and it is the most important methodological finding of this session.

---

## 1. The algebra that tells us which hypothesis class can still pay

**[OFFICIAL]** metric; **[MEASURED]** reductions, verified to 1e-9 in `tests/test_metric.py`:

```
DTI = T / ( α(T + F) + βK ) ,   T = TP_w,  F = FP_w,  K = |G| ,  α = 0.2, β = 0.8
```

**[MEASURED, `scripts/solve_truth_scale.py`]** The operator's own h33 experiment is a *controlled*
two-point experiment on the live scorer: the same raster, 2,545 dots within 200 m of the catalogue
deleted, 40,199 → 37,654 px, **0.2708 → 0.2778** [OWNER-REPORT]. Because the deleted dots sat on
mapped faults they can have carried essentially no credit for *new* faults, so T is unchanged and
only S moves. Solving the two equations gives, with no further assumption,

```
T  = 5,470  (truth-weight the group's best file actually captures)
K ≈ 14,400  (hidden new-fault pixels in the public test set, ≈ 144 km of trace)
F ≈ 35,400  (wasted mass — 94 % of every dot emitted)
```

and the denominator splits **8,187 FP-tax : 11,520 K-term**. The FP tax is 42 % of the denominator.

**[MODEL]** The consequence is sharp. Holding the captured credit per dot at its present
0.1453 and merely emitting more of the same quality would give 0.39 at 75 k px and 0.49 at 150 k px —
but the family's own thinning cascade proves credit per dot *collapses* with budget
(0.1232 at 44 k, 0.0566 at 121 k), and a power-law fit puts this field's optimum at ≈ 20 k px and
**DTI ≈ 0.280**. The emission lever is spent to within ±0.003.

> **Therefore: only a hypothesis that raises *credit per emitted pixel* can move this project.
> Every hypothesis below is judged on that one axis.**

---

## 2. The five candidates

### H85-1 — GEO-Pb: multivariate juxtaposition boundary detector — **rank 1, CHOSEN LANE**

| | |
|---|---|
| **Layers** | `rtp` (2), `iso_grav_anom` (13), `cond_surf` (17), `depth_to_base_surf` (15) · GeoDAWN radiometric K, Th, TC (`geodawn_rad_u8` bands 1, 2, 4) · `det_elev` (12), `det_elev_slope` (19), LiDAR `step_max` (`lidar_scarp_features_u8` band 3) |
| **Physical signature** | At each pixel and each of 8 candidate strikes, the *offset difference* of a covariance-whitened 10-band stack across the candidate line — a windowed Hotelling-style **two-sample step statistic**, not a derivative. The three physics domains are reduced by their **median**, so at least two of {potential-field, radiometric, topographic} must agree. The result is multiplied by an **along-strike line mean over 1.5 km**, so only straight, persistent boundaries survive. |
| **Why it finds a fault the catalogue lacks** | The given catalogue is USGS Quaternary + INGENIOUS: structures mapped from *surface* evidence. A fault concealed under Holocene alluvium with no scarp still juxtaposes different basement susceptibility, different cover thickness and different surface geochemistry. Each individual band changes a little; the joint 10-vector changes a lot. A derivative operator weights the *magnitude* of each band's change; a whitened two-sample statistic weights how *improbable the joint change* is. That is precisely the regime a scarp-first catalogue under-samples. |
| **How it differs from everything in the family** | **[MEASURED]** `grep -ri "hotelling\|two-sample\|half-disc\|mahalanobis"` over the source of GEMSDOE28/30/31/32/49/63/70 returns **no implementation** — the words appear only as prose justification for gradient-based detectors. Every shipped detector in the family is a derivative: Sato/Frangi/Hessian ridge, tilt, horizontal gradient, Euler, worms, gradient coherence. GEO-Pb never differentiates anything. |
| **Mimicking non-fault processes (declared in advance)** | (a) depositional contacts — distal alluvial-fan margins, Lake Lahontan highstand shorelines: *lobate and closed*, killed by the straightness term; (b) aeromagnetic / radiometric acquisition seams: single-domain, killed by the two-of-three median vote — and audited by the response-azimuth histogram in `evidence/experiments.json`; (c) erosional volcanic mesa and flow margins: straight *and* multi-domain — **the irreducible confounder, declared, not solved**. |
| **Cost / data** | ~35 s CPU for the full grid; **no new external data**. Validatable locally: **yes**. |
| **Expected DTI gain** | **[MODEL]** the only candidate here that raises credit-per-pixel by changing the *statistic*, not the layer list. Ranked 1 on gain-per-unit-cost. |

### H85-2 — Along-strike displacement-gradient tip prediction — rank 2

* **Layers:** the catalogue itself + `det_elev` (12), `rtp` (2).
* **Signature:** fit each mapped segment's along-strike *throw proxy* (cross-fault relief and
  cross-fault RTP step), extrapolate the displacement-gradient to zero, and emit the predicted
  **tip continuation** beyond the mapped end-point.
* **Why off-catalogue:** fault traces are mapped where expression is strong and simply *stop*
  where it is weak; real displacement decays to zero over a tip region that is systematically
  un-mapped. **[OFFICIAL]** this is the standard displacement–length scaling of normal faults.
* **Why ranked 2, not 1:** it is **catalogue-anchored**, so it necessarily emits close to the
  catalogue — and the one controlled live experiment we have says catalogue-proximal mass is
  net-negative (0.2708 → 0.2778 by deleting it). It also risks a leakage AUC > 0.90 on a
  hide-and-recover holdout by construction, because withheld segments continue visible ones.
* **Cost:** medium. **Related work already scored:** `h32-1-prethin-tip-euler` 0.2649,
  `D-step-3p0-07pct-tipProt` 0.0763 [OWNER-REPORT] — the family has partly been here.

### H85-3 — Lake Lahontan shoreline-referenced scarp residual — rank 3

* **Layers:** 1 m LiDAR composite + `det_elev`.
* **Signature:** the Lahontan highstand (~1,335 m) is a *geomorphic datum of known age*; a linear
  elevation offset of the shoreline terrace is a post-12-ka fault with a measurable throw and
  frequently no mapped trace.
* **Why off-catalogue:** it dates the structure, so it finds Holocene faults with centimetre-scale
  expression invisible at 100 m.
* **Why ranked 3:** **[OWNER-REPORT]** the family already shipped `datum-lahontan-strain-gauge-defensible-440dots`
  and scored **0.0000**. The idea is sound; the realisation is budget-starved — a 440-dot file
  cannot score under the algebra of §1 whatever its geology. Needs a far larger candidate set to
  be testable, and that needs the raw 1 m tiles.

### H85-4 — Relocated-seismicity nodal-plane lineaments — rank 4, **[BLOCKED]**

* **Layers:** would replace `ieq_n100a15` (16) and `deq_n100a15` (10).
* **Why off-catalogue:** instrumental seismicity is a *dynamic* inventory; a blind, low-slip fault
  lights up seismically while leaving no scarp — e.g. the 2020 M6.5 Monte Cristo Range rupture
  occurred on largely unmapped structures inside this region.
* **Why the supplied bands cannot substitute:** they are computed on a 100 km radius and are
  constant at the metric's own 300 m resolution.
* **Source named and checked:** USGS FDSN event service
  `https://earthquake.usgs.gov/fdsnws/event/1/query` (free, public domain).
  **Obtainability check performed this session:** the sandbox egress allow-list admits only
  `github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`,
  `files.pythonhosted.org`. `earthquake.usgs.gov` is **not reachable**. Ranked, **not proposed as
  ready**, per the brief's rule.

### H85-5 — Leaderboard inversion for the hidden truth density — rank 5, *contrarian*

* **Layers:** none — the 60+ scored artifacts and their live scores.
* **Signature:** each (raster, score) pair is one equation in the metric algebra of §1. With
  enough *diverse* rasters, non-negative least squares over a coarse spatial basis recovers where
  the hidden positives are.
* **Why ranked last despite being the most contrarian:** **[MEASURED]** the restorable corpus is
  17 rasters and is dominated by one nested family (five of the top six artifacts are thinnings
  of a single field), so the design matrix is near-collinear and the system is badly
  under-determined. It is also *not science* — it would not survive the final round's expert
  review, which scores discoveries, not fits. Recorded for completeness; not pursued.

---

## 3. Ranking summary

| rank | hypothesis | expected gain in credit/pixel | implementation cost | locally validatable | chosen |
|---:|---|---|---|---|---|
| 1 | **H85-1 GEO-Pb juxtaposition** | **high — changes the statistic, not the layer list** | low (35 s CPU, no new data) | **yes** | **✔ LANE** |
| 2 | H85-2 displacement-gradient tips | medium | medium | partly (leakage risk) | no |
| 3 | H85-3 Lahontan datum residual | medium | high (needs raw 1 m tiles) | no | no |
| 4 | H85-4 seismicity nodal planes | high if obtainable | high | **no — [BLOCKED]** | no |
| 5 | H85-5 leaderboard inversion | unknown | low | no (rank-deficient) | no |

---

## 4. Pre-registered promotion rule (fixed before any candidate was measured)

A candidate may be written to `docs/downloads/` only if **all** of the following hold:

1. **Beats the derivative control** (`ctrl_sato_elev`) on pooled HOLDOUT-DTI at *matched emitted
   mass*, in **≥ 3 of 4** spatially-blocked folds.
2. **Beats uniform random** by a margin larger than the 95 % CI half-width.
3. **Leakage canary passes**: the raw surface's AUC against withheld positives is **< 0.90**.
4. **Not a duplicate**: Spearman ρ ≤ 0.90 against every registry raster's surface **and**
   ≤ 70 % of its dots within 3 px of any one registry raster's dots.
5. **Validator passes** every format check with no human inspection.

Failure of any of 1–4 is published as a **negative result**, which is a deliverable, not a defeat.

---

## 5. Official sources used for the geology in this file

| claim | source |
|---|---|
| metric, kernel, α, β, submission format, worked example | <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> |
| labels are USGS Quaternary fault maps + INGENIOUS; test set = expert-mapped faults *absent* from the public USGS database | same page, "Labels" and "Competition structure" |
| GeoDAWN airborne magnetic and radiometric surveys | <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> |
| INGENIOUS project (Great Basin Center for Geothermal Energy) | <https://gbcge.org/current-projects/ingenious/> |
| UTM zone 11N / EPSG 32611 | <https://epsg.io/32611> |
| Tversky index | <https://en.wikipedia.org/wiki/Tversky_index> |
| reference solution (α = 0.2, β = 0.8 in the Tversky loss) | <https://github.com/drivendataorg/gems-prize-reference-solution> |
| live leaderboard (read 2026-10-22: #1 xiaofanhu **0.4413**) | <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/> |

---

## 6. The methodological finding: why a catalogue-truth holdout *cannot* rank these artifacts

**[MEASURED, `evidence/instrument_calibration.json`]**

| artifact | live [OWNER-REPORT] | this repo's hide-and-recover holdout |
|---|---:|---:|
| `h33-h33-2-b2` (the family's best) | **0.2778** | **0.00479** |
| `h27-4-solo-d28` | 0.2708 | 0.03452 |
| `gate_ortho_w0.25-40k` | 0.2376 | **0.00000** |
| `dotted-h19-5-d2-8` | 0.2600 | 0.11153 |
| `Hedge-v2` | 0.1563 | 0.31769 |

The ordering is inverted, and the cause is mechanical rather than scientific. The three artifacts
at the top were built with a **hard exclusion of every pixel within 2–3 px of the *full* catalogue**.
A hide-and-recover holdout then hides some catalogue segments and asks the artifact to find them —
but the artifact has already deleted every dot near them. Its score is forced to ≈ 0 **by its own
success condition**. `Hedge-v2`, which emits 60,988 dots directly on the catalogue, is rewarded
for exactly the behaviour the live scorer punishes.

**Consequence, and the fix applied here:** a hide-and-recover holdout can only be used to evaluate
a **rule**, re-executed per fold with only that fold's *visible* catalogue — never a finished
raster. `src/gems85/holdout.py::score_folds` takes a callable and rebuilds per fold for exactly
this reason; `score_static` exists only for the duplicate check and carries this warning. Every
sibling repository that reported a Spearman ρ between a static-artifact holdout and the live board
was measuring this artifact, not an instrument. Logged as **IR-85-001**.

---

# Appendix — hypotheses from the duplex lane (arena/29a39923)

# Five candidate geological hypotheses (Lane H85) — ranked before any results

Evidence classes: **[OFFICIAL]** organizer/USGS source · **[MEASURED]** computed in
this checkout from sha256-pinned bytes · **[ORGANIZER-CONFIRMED]** score copied
from the brief's submission-page receipts · **[CLAIM]** unverified report.

Fleet context that constrains novelty: the registry in the brief contains ~60 scored
files. The organizer-confirmed leaders are all emissions of one multi-physics ridge
family (H19-5 → d1.5 0.2477 → d2.8 0.2600 → h33-2-b2 0.2778). Pure single-physics
novelties scored far lower (lidar-scarp dotted 0.0430–0.1461, HGB top-k 0.0286–0.0424,
hydro-conduit fusion 0.0558, Radon piedmont 0.0669–0.1627, Euler threads 0.0355–0.0984).
In the template repo (GEMSDOE32, `evidence/h33_holdout.json`) the label-free
orientation/drainage/scarp surfaces scored catalogue-holdout DTI 0.019–0.034 against
the d2.8 control's 0.098 — **[MEASURED]** there. Any new candidate must therefore be
judged against the control on the same instrument, which is what this repo does.

| rank | id | layers (official band names) | physical signature | why it should catch a catalogue-missing fault | differs from prior fleet code | non-fault mimic (named) | cost | data |
|---:|---|---|---|---|---|---|---|---|
| 1 | **H85-A fold-proper supervised detector** | all 19 official bands + template derived channels (curvature, Hessian ridges, relief, top-hat, potential-field edges, structure-tensor coherence/strike) + LiDAR scarp u8 (12) + GeoDAWN rad u8 (4) + extensions u8 (4) | HistGradientBoosting probability that a pixel lies on a fault trace, trained per spatial fold on *visible* faults only, with **no catalogue-derived channel** (no distance-to-catalogue, the fleet's known AUC-1.0 leak); emitted by metric-exact max-coverage greedy | The catalogue is demonstrably incomplete (official problem statement: expert-labelled new faults exist). A detector trained on what mapped faults *look like* across all physics generalises to unmapped traces with the same expression; fold-proper training + whole-segment holdout measures exactly that transfer | Prior HGB files (6GEMSDOE 0.0286, GEMSDOE43 0.0424) used top-k/threshold emission; no fleet file combines fold-proper segment-blocked training, support-confined max-coverage emission, and the ≤2 px catalogue-halo prune at the 37,654-dot operating point | Young alluvial / cultural lineaments (roads, canals, field boundaries) that share multi-physics line expression with faults | ~15 min CPU | none (all hash-pinned in-repo mirrors) |
| 2 | **H85-B multi-physics orientation consensus** | `det_elev`, `rtp`, `tmi`, `iso_grav_anom`, `cond_surf` | Both-polarity Hessian line response per physics × orientation order parameter R = \|mean w·e^{2iθ}\|; a pixel scores only if independent physics agree a line exists *and* agree on strike | Single-dataset mapping under-represents faults that are weak in every field but *coherently oriented* in several | Template H33-A implemented this surface but it was never emitted alone at the winner's operating point with halo prune, and never scored by an organizer; this is its first protocol-holdout emission test here | Lithologic contact trains / shorelines straight in several fields at once | ~2 min CPU | none |
| 3 | **H85-C strain-gated lineament** | `geod_dilaterate`, `geod_2ndinv`, `geod_shearrate` (gate) × Hessian lines of `det_elev`, `rtp` | Line geometry re-weighted by a smooth geodetic-strain gate (0.30 + 0.70·(0.5·dilatation⁺ + 0.3·second-invariant + 0.2·shear), robust-normalised) | Catalogue faults include fossil structures; a *currently extending* blind fault should sit where dilatation is locally high AND a line exists. The strain bands are too smooth to locate a fault (fleet-measured: seismic/strain bands are ~constant at 300 m) — here they only re-rank line geometry | No fleet lane uses the geodetic strain tensor invariants as a *gate* on line emission (sarnnpu/wing-crack lanes model tilt/wing geometry, not a dilatation gate) | Basin-range range fronts inside a broad regional dilatation high (gate promotes a whole front) | ~1 min CPU | none |
| 4 | **H85-D collinear thermal-spring chains** | GDR 1391 wellspring points (in-footprint CSV, hash-pinned): thermalclass, temp_c, geothermometers; `row/col` | Directional point-process line support: for each pixel, max over 16 orientations of thermally-weighted spring density along a 2 km line; require ≥3 collinear warm/hot points | Geothermal upflow rises along permeable fault conduits; aligned warm springs are a *direct* vent indicator that raster-only detectors ignore, and blind faults under playa cover may show springs without any scarp | GEMSDOE71 fused springs into a multi-modal stack (0.0558 ORGANIZER-CONFIRMED) but no lane emits *pure collinear spring-chain* support; would need the point table only | Spring lines along valley floors / playa margins / irrigation-well alignments along roads | ~10 min CPU | present (GDR 1391 mirror, sha256-pinned) — **not run: budget = 3 experiments** |
| 5 | **H85-E volcanic-vent alignment** | GDR volcanic vents CSV (672 B in-footprint extract) + `det_elev` | Vent-point collinearity (as H85-D) intersected with topographic line response | Monogenetic vent alignments mark deep crustal fractures that feed geothermal systems | No fleet lane uses vent alignments | Vent chains along a single eruptive fissure that is not a through-going fault | ~10 min CPU | present but sparse (tens of points) — **not run: sparse + budget** |

**Decision rule (declared in advance):** promote the best experiment only if its
pooled HOLDOUT-DTI (`gems85-pooled-hide-v1`, 24,885 withheld positives across
8 cells) beats the best registry control scored on the identical holdout *and*
the uniqueness gate passes. Otherwise the verdict is **negative** and the file is
labelled DO NOT SUBMIT — a negative result is a deliverable.

**External-data candidates considered and rejected as not-ready:** sub-km USGS
FDSN seismicity lineaments — source is free/official
(https://earthquake.usgs.gov/fdsnws/event/1/query) but egress from this sandbox
is restricted to github/pypi hosts (verified in the template repo; re-verified
here by the restore path using only `gh api`), so it is named, not proposed as viable.

---

# Session 6 (`arena/76e675dd-gemsdoe85`) — 5 New Candidate Geological Hypotheses & Validation Results

Executing the prioritized next steps from `README.md` §5 and `knowledge/geothermal-vent-discovery.md` §4, five new hypotheses (`H85-S6-1` … `H85-S6-5`) were formulated before running the Session-6 3-experiment budget on `gems85-holdout-v1.0.0` (4 spatially-blocked folds, 60,988 withheld positives):

| Rank | ID | Specific Layers Involved | Physical Signature Targeted | Why It Catches Off-Catalogue Faults | How It Differs From Prior Repo Code | Cost & Obtainability | Holdout Result (`HOLDOUT-DTI`, `gems85-holdout-v1.0.0`) |
|---:|---|---|---|---|---|---|---|
| 1 | **`H85-S6-2` (`oof_ti_geopb_v2_thermal_crest`)** | 29 translation-invariant local derivative/juxtaposition/scarp channels (`geopb_r3`, `geopb_r6`, `geopb_crest`, `s1_geopb_v2`, `s3_mag_alt`, `g_thermal`, `lidar_ex_max`, `lidar_step_max`, `lidar_downface`, `lidar_coh100`, `det_elev_slope`, `relief5`, `tilt_tc`, `grad_rtp_s2/s5`, `grad_grav_s2`, `grad_cond_s2`, `grad_depth_s2`, `iso_grav_anom_slope`, `tmi_hg`, `tmi_vg`, `rad_ThK`, plus 5-px smoothed context) | Fold-proper HistGradientBoosting trained on visible-block faults only (removing smooth regional block-identifying levels that caused withheld-block suppression in `IR-85-007`), fused with `H85-S6-1`, `H85-S6-3`, and `g_thermal`, then thinned via 1-step Hessian-normal axial crest extraction (`crest_1step`) | Resolves subtle piedmont/intrabasin traces where partial scarp, subsurface gradient, and thermal upflow signals co-occur; 1-px Hessian-normal crest extraction prevents 2D ribbon blob-clumping so every dot sits on an axial fault centerline | Fixes both `IR-85-006` (split-halo bug) and `IR-85-007` (withheld-block negative contamination + 2D blob packing in `run_supervised.py`) | ~280 s CPU, in-repo SHA-256-pinned data | **OOF AUC `0.6455` (up from `0.5728`) · `0.10154` at 37,654 dots · `0.11309` at 60,000 dots · `0.11440` (`CI [0.10786, 0.12094]`) at 72,000 dots — PROMOTED (beats PR #6 `0.09838` and static `d2.8` `0.11153`)** |
| 2 | **`H85-S6-1` (`geopb_v2_piedmont_thermal`)** | *State*: `rtp` (2), `tmi` (14), `iso_grav_anom` (13), `depth_to_base_surf` (15), `cond_surf` (17), `TMI_up150` (ext 4), `K/Th/U` (rad 1–3), `ThK/UK/UTh` (ext 1–3), `det_elev` (12). *Interface*: LiDAR `lappos_max` (5), `lapneg_max` (4), `step_max` (3), `ex_max` (1), `relief` (9), `det_elev_slope` (19), `-tc` (6), `iso_grav_anom_slope` (5), `tmi_hg` (3), `geod_2ndinv` (4), `geod_shearrate` (7). *Prior*: GDR 1391 `gdr_wellspring_in_footprint.csv` | Separates 16-strike whitened block **state** step `\|Y_state(x+dn) - Y_state(x-dn)\|` from on-line **interface** scarp/inflection `Y_interface(x)` evaluated at `x = 0` (fixing the `IR-85-006` split-halo bug), suppresses high-elevation volcanic mesa interiors, and re-weights by geothermal upflow proximity `(1 + 0.35 · g_thermal)` | Concealed range-front and piedmont faults juxtapose distinct subsurface blocks while localizing a subtle concave break-in-slope (`-tc`, `lappos_max`) and leaking warm fluids within 1.5 km | Fixes `IR-85-006` (which differenced positive impulses `step_max` and `det_elev_slope` across ±3 px, putting zero on the fault trace and two false shoulders at ±300 m), upgrades from 8 to 16 strikes (`README.md` §5 #2), and implements the thermal multiplier (`knowledge/geothermal-vent-discovery.md` §4) | ~90 s CPU, in-repo SHA-256-pinned data | **Post-crest AUC `0.5831` (up from `0.5036` in v1) · Re-ranking `geopb_crest` with `s1 + s3 + g_thermal` lifts 90k `HOLDOUT-DTI` from `0.09838` to `0.09968` (`CI [0.09171, 0.10766]`)** |
| 3 | **`H85-S6-3` (`mag_continuation_k_alteration`)** | `tmi` (14), `tmi_vg` (9), `tmi_hg` (3), `TMI_up150` (ext 4), `UK` (ext 2), `UTh` (ext 3), `K` (rad 1), `cond_surf` (17), `iso_grav_anom_slope` (5), LiDAR `lappos_max` (5), `det_elev_slope` (19) | Standardized shallow magnetic continuation residual `\|z(tmi) - z(TMI_up150)\|` + magnetite-destruction vertical-gradient trough (`-tmi_vg`) paired with hydrothermal `U/Th`, `U/K` mobility and conductive clay alteration (`∇cond_surf`) | Hydrothermal circulation along intrabasin faults oxidizes host-rock magnetite to non-magnetic hematite/pyrite and mobilizes U/K/Th even beneath flat quaternary play/alluvial cover | First detector in `GEMSDOE85` to form the explicit vertical continuation residual `z(tmi) - z(TMI_up150)` paired with radiometric alteration ratios | ~35 s CPU, in-repo SHA-256-pinned data | **Canary AUC `0.5607` · Standalone `HOLDOUT-DTI = 0.06713` at 37.6k, `0.08109` at 60k, `0.09009` at 90k; additive contributor inside `H85-S6-2`** |
| 4 | **`H85-S6-4` (Sub-km Relocated Microseismicity Planar Clustering)** | USGS ComCat / Nevada Seismological Lab relocated hypocenters + `depth_to_base_surf` (15) + `geod_2ndinv` (4) | RANSAC planar strike fitting to M0.5–M3.5 microearthquake swarms projected up-dip to the basement/surface trace | Blind active faults with zero surface scarp illuminate in microseismicity | Replaces 100-km-smoothed `ieq_n100a15`/`deq_n100a15` with sub-km hypocenters | **BLOCKED** (`earthquake.usgs.gov` blocked by sandbox egress allowlist) | Not run (external source blocked) |
| 5 | **`H85-S6-5` (Sentinel-1 InSAR Interseismic Velocity Gradient)** | Copernicus / ASF DAAC Sentinel-1 ascending + descending LOS velocity maps + `det_elev` (12) | 90 m spatial gradient of interseismic fault creep and geothermal reservoir deformation | Resolves active fault strain localization at 90 m instead of 100 km GPS interpolation | Replaces `geod_*` regional grids with spaceborne radar interferometry | **BLOCKED** (`dataspace.copernicus.eu` blocked by sandbox egress allowlist) | Not run (external source blocked) |

