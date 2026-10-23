# Pre-Registered Untried Geological Hypotheses & Single-Lane Experimental Protocol (`GEMSDOE85`)

**Branch:** `arena/348a7290-gemsdoe85` · **Locked Date:** `2026-10-22` (locked **before** opening `existing_faults.tif` / `labels.tif` pixels)  
**Shared Evaluator Pin:** `vendor/gems57/evaluate_holdout.py` (`VERSION = "gems57-pooled-hide-v2"`, `buffered_component_draw` with whole 8-connected components, `DOMAIN_ERODE = 12 px = 1.2 km`, `buffer_px = 3`, pixel-exact `masked_known`, pooled `DTI` with `alpha = 0.2`, `beta = 0.8`, `R = 300 m`)  
**Shared Writer & Uniqueness Pin:** `vendor/gems57/submission_writer.py` & `vendor/gems57/uniqueness.py` (unmodified)  
**Experiment Cap:** Strictly **`<= 3` experiments** (`E1`, `E2`, `E3`) within a **single coherent method lane**

---

## 1. Declared Single Method Lane (`Lane H85-Conduit`)

**Method Lane:** *Fold-safe out-of-fold multi-physics hidden geothermal fault-conduit probability & proximity estimation (`1 px` crest targets against stratified near-flank + basin negatives), coupled with Bayes prior-shift calibration and exact submodular 29-offset Dinkelbach fractional `DTI` dot selection.*

Every experiment in this session (`E1 -> E2 -> E3`) stays strictly inside this single lane and shares the identical unmodified evaluator (`gems57-pooled-hide-v2`), identical `buffered_component_draw` folds, identical `B = 2 px` (`<= 200 m`) fold-visible halo rule, and per-feature single-channel leakage canary (`AUC <= 0.90`).

---

## 2. Five Pre-Registered Untried Geological Hypotheses Ranked by Expected `DTI` Gain vs Cost

### Rank 1 — `H1`: Sub-Kilometer Brittle-Conduit Seismicity (`1900–2026` USGS ComCat) + Shallow `2 m` Conductive Thermal Plume (`F2mDAB`) & Siliceous Paleo-Vent Alignment (**NEW EXTERNAL DATA ON DISK — NEVER TRIED IN ANY PRIOR REPO**)

- **Specific Layers Used:**
  1. `data/external/usgs_comcat_geodawn.csv` (`3,977` deduplicated USGS ComCat events `1900–2026-10-20`, `100.000000%` valid GeoDAWN pixel coverage; `541` post-2021 events absent from GDR 1391);
  2. `data/external/.../2m_temperature_probe_n83geo.dbf` (`2,782` inside-footprint GBCGE shallow probes with seasonal/elevation-corrected `F2mDAB` up to `+54.7 °C` and `T2m`);
  3. `data/external/paleo_geothermal_regional/Paleo_geothermal_final.csv` (`281` inside-footprint deposits separated into `195` high-enthalpy siliceous sinter / silica-cemented sand / explosion crater / alteration conduits vs `86` pluvial tufa mounds);
  4. `data/external/gdr_wellspring_in_footprint.csv` (`temp_c`, quartz/chalcedony/Na-K-Ca cation geothermometers — strictly excluding `dist_known_fault_px`) + `cond_surf` (Band 17) + `geod_shearrate`/`geod_dilaterate` (Bands 7–8).
- **Physical Signature & Mathematical Transform:**
  - Multi-scale radial & moment-weighted kernel densities (`sigma = 300 m, 1.0 km, 3.0 km, 8.0 km`) of shallow brittle hypocenters (`depth_km <= 12 km`), post-2021 unmapped swarm density (`year >= 2022`), local swarm clustering count within `2.5 km`, IDW/Gaussian-interpolated `2 m` conductive anomaly `F2mDAB_pos = max(0, F2mDAB)` + survey-density confidence weight, high-enthalpy siliceous paleo-vent kernel density (`sinter + silica-cemented sand + explosion craters + silicified breccia + acid-sulfate`), and thermal-conductivity upflow coupling (`F2mDAB_pos * cond_surf`).
- **Why It Catches Hidden Faults Missing from USGS/INGENIOUS:**
  - Over 75% of Great Basin geothermal systems occur on concealed faults beneath Holocene playa clays and young alluvial fans where surface scarps were erased or never breached the surface. GDR 1391 blurred pre-2022 seismicity across `100 km` (`deq_n100a15`, `ieq_n100a15`), destroying sub-kilometer fault localization and missing all `2022–2026` blind ruptures (`2024` Gillis Range, `2024` Parker Butte `Mwr 5.71`, `2025–2026` Hot Creek, `2025–2026` Smoke Creek, `2026` SE Silver Springs `Mwr 5.68`). Meanwhile, GBCGE's `2 m` temperature probes and paleo-sinter mapping explicitly targeted concealed geothermal upflow zones in Gabbs Valley, Hawthorne, Astor Pass, Desert Queen, Desert Peak, Dixie/Fairview, Granite Springs Valley, Fallon, Columbus Marsh, Silver Peak, Blue Wing, and Rhodes Marsh where newly mapped INGENIOUS blind faults reside.
- **Named Non-Fault Mimic Processes & Anti-Mimic Suppression:**
  1. *Pleistocene Lake Lahontan wave-agitated shoreline tufa mounds (`Tufa`, ~1,330 m elevation)* that precipitate along pluvial strandlines without fault conduits $\to$ separated explicitly from siliceous/explosion paleo-vents into an independent channel coupled with `det_elev` / shoreline elevation bands;
  2. *Lateral outflow thermal plumes in shallow alluvial aquifers* where hot water migrates down-gradient away from the range-front fault $\to$ disambiguated by requiring coincidence with basement/magnetic step gradients or shallow microseismicity rather than unconditioned thermal halos;
  3. *Quarry blasts / geothermal injection microseismicity* $\to$ depth-stratified (`depth <= 3 km` vs `3–12 km` brittle seismogenic zone) and moment-weighted.
- **Difference from All Prior Fleet Implementations (`GEMSDOE1`–`GEMSDOE88`):**
  - Zero prior repositories in the entire fleet parsed `usgs_comcat_geodawn.csv`, `2m_temperature_probe_n83geo.dbf`, or `Paleo_geothermal_final.csv`.
- **Expected `DTI` Gain vs Compute Cost:** **Highest (`Rank 1`)** — `~4 s` CPU rasterization cost on 2 vCPU; directly illuminates basin-interior blind fault segments where scarp detectors score near zero.

---

### Rank 2 — `H2`: Sharp `1 px` Trace Crest Learning + Flight-Line-Notched (`090°` De-Aliased) Multi-Scale Structural & Geomorphometric Feature Stack

- **Specific Layers Used:**
  - `data/training_features.tif` (all 19 geophysical bands), `data/external/lidar_scarp_features_u8.tif` (12 bands including 1 m LiDAR `ex_max`, `step_max`, `downface_max`, `upface_max`, `coh100`, `strike`), `data/external/topo_10m_derived_100m_u8.tif` (9 bands from 10 m 3DEP DEM covering 100% of non-LiDAR areas), `data/external/dem10_chi_100m_u8.tif` (`chan_n`, `knick_n`, `raised_n`), and `data/external/derived_sgmc_faults_100m_u8.tif` (pre-Quaternary bedrock faults).
- **Physical Signature & Mathematical Transform:**
  1. **1-Pixel Crest vs Near-Flank Contrast Training:** Train out-of-fold gradient boosters strictly on **exact `1 px` fault centerline positives (`y = 1`)** against **explicit near-flank negatives (`2 <= d <= 8 px`, `y = 0`) + basin negatives (`d > 8 px`, `y = 0`)**, eliminating the `3x3` positive dilation + `10 px` blind-zone defect of `scripts/run_supervised.py`.
  2. **GeoDAWN `090°` Flight-Line De-Aliasing:** Compute directional North–South vs East–West gradient anisotropy ratios (`|d/dx| - |d/dy|` across `rtp`, `tmi`, `rad_K`, `rad_TC`) and tectonic strike favorability (`sin(strike)` weighting NNW–NNE Great Basin extension fabric vs `090°` E–W survey line azimuth).
  3. **10 m 3DEP Drainage Knickpoint ($\chi$) & Bedrock Fault Continuity:** Cross-correlate `dem10_chi` `knick_n` / `raised_n` river profile steps and `topo_10m` `curv_prof_absmax` / `aspect_coherence` with `SGMC` bedrock fault distance so reactivated range-front/intrabasin bedrock faults without 1 m LiDAR coverage are sharply localized.
- **Why It Catches Hidden Faults Missing from USGS/INGENIOUS:**
  - Legacy USGS Qfaults miss low-throw piedmont scarps outside 1 m LiDAR polygons, mislocate range-front traces by `100–400 m` (Hermant et al., 2025), and omit pre-Quaternary `SGMC` bedrock faults whose subtle Holocene reactivation is expressed only as aligned `10 m` stream knickpoints (`knick_n`) and `topo_10m` profile curvature breaks.
- **Named Non-Fault Mimic Processes & Anti-Mimic Suppression:**
  1. *GeoDAWN `090°` airborne traverse micro-leveling seams (`200–400 m` spacing)* $\to$ suppressed explicitly by `E-W` directional gradient ratio channels so trees penalize single-domain `090°` magnetic/radiometric stripes;
  2. *Incised dendritic fan channels (`chan_n` high without `raised_n` block uplift or magnetic/gravity step)* $\to$ separated cleanly using simultaneous `chan_n` vs `raised_n` + `iso_grav_anom_hg`.
- **Difference from Prior Implementations:** Fixes `run_supervised.py`'s `3x3` positive dilation, adds `10 m` 3DEP + $\chi$ knickpoints + `SGMC` bedrock faults + explicit `090°` flight-line de-aliasing features.
- **Expected `DTI` Gain vs Compute Cost:** **Very High (`Rank 2`)** — `~25 s` feature build + `~35 s` 4-fold OOF training.

---

### Rank 3 — `H3`: Exact Dual-Expectation `(p_hat, q_hat)` Bayes-Calibrated Submodular Dinkelbach `300 m` Dot Selection

- **Specific Layers / Inputs Used:** Out-of-fold calibrated trace crest probability $\hat{p}(x) = \mathbb{P}(x \in G \mid \mathcal{F})$ mapped via exact Bayes prior shift to unseen target density $\pi_{\text{target}}$, paired with OOF-calibrated 300 m max-kernel proximity $\hat{q}(x) = \mathbb{E}[\max_{v \in G} K(x, v) \mid \mathcal{F}] \in [0, 1]$ and `B = 2 px` (`<= 200 m`) fold-visible halo pruning.
- **Physical / Mathematical Signature:**
  - Maximizes the exact global fractional `DTI` expectation $\widehat{\mathrm{DTI}}(S) = \widehat{T}(S) / (0.8\,P_{\text{tot}} + 0.2\,\widehat{T}(S) + 0.2\,\widehat{F}(S))$ via Minoux lazy-greedy submodular updates over all 29 kernel offsets $K(\delta) > 0$, halting automatically at the exact unimodal Dinkelbach optimum $t^\star = \arg\max_t \widehat{\mathrm{DTI}}(S_t)$ where $\Delta\widehat{T}(u \mid S) = \frac{0.2\,\tau\,(1 - \hat{q}(u))}{1 - 0.2\,\tau}$.
- **Why It Improves Hidden-Fault Recovery Under `DTI`:**
  - Automatically places dots every `~3.0 px` (`300 m`) along linear fault crests, tightens spacing to `2.0 px` on high-certainty fault junctions/stepovers, widens spacing to `3.5–4.0 px` on lower-probability tips, suppresses isolated `1 px` speckle blobs whose `29-cell` integral $\Delta\widehat{T}$ is small even if peak $\hat{p}$ is moderate, and chooses total dot budget without arbitrary magic constants.
- **Named Mimic / Failure Mode & Mitigation:** Over-confident uncalibrated tree probabilities inflating $\widehat{q}(u)$ $\to$ mitigated via out-of-fold isotonic calibration against held-out fold segments before Bayes prior scaling.
- **Difference from Prior Implementations:** Fixes `src/gems85/emitter.py`'s `sum_delta p * k > 1` bug (`3x` over-estimation of `q_hat` on 1 px lines) and replaces isotropic `d = 2.8` Poisson thinning.
- **Expected `DTI` Gain vs Compute Cost:** **High (`Rank 3`)** — `~2.5 s` per full-footprint emission pass.

---

### Rank 4 — `H4`: Fold-Safe Structural Tip Propagation, En-Echelon Stepover & Relay-Ramp Continuation Field

- **Specific Layers Used:** Fold-visible fault mask `visible_faults` (`fold['visible']` on holdout; `grid.catalogue` on full inference) combined with local strike vectors, `iso_grav_anom_hg`, `rtp`, and `topo_10m`.
- **Physical Signature & Mathematical Transform:**
  - Extract skeleton endpoints (tips) and local tangent unit vectors $(t_y, t_x)$ strictly from `visible_faults` (never seeing withheld components or the `3 px` buffer!). Propagate an anisotropic forward-cone tip field along $(t_y, t_x)$ over `0.4–5.0 km` plus multi-scale fault-corridor density (`sigma = 8, 20, 45 px`) capturing `0.5–4.5 km` synthetic/antithetic en-echelon relay ramps and horsetail splays (Faulds & Hinz, 2015), while hard-masking `d <= 2 px` around `visible_faults`.
- **Why It Catches Hidden Faults Missing from USGS/INGENIOUS:**
  - Normal faults grow by segment linkage across `0.5–4 km` relay ramps and horse-tail tip splays whose displacement tapers below field-mapping thresholds (Hermant et al., 2025).
- **Named Non-Fault Mimic Process:** Artificial truncation of mapped traces at quadrangle boundaries or playa edges where the fault actually steps across an aseismic sediment-filled graben $\to$ gated by requiring multi-physics geophysical/thermal corroboration rather than blind straight-line extrapolation.
- **Difference from Prior Implementations:** Strictly fold-safe inside `gems57-pooled-hide-v2` (recomputed independently for each fold's `visible` mask, verified by per-feature leakage canary `AUC <= 0.90`).
- **Expected `DTI` Gain vs Compute Cost:** **Moderate-High (`Rank 4`)** — `~2 s` per unique visible mask.

---

### Rank 5 — `H5`: Hydrothermal Magnetite-Destruction + Potassic Alteration Coupled Juxtaposition (`GEO-Pb` + `K/Th` vs `TMI` Trough)

- **Specific Layers Used:** `GEO-Pb` across-strike covariance-whitened 10-band step crests (`src/gems85/geopb.py` `geopb_r3_L15`, `geopb_r6_L25`, `geopb_crest`) fused with hydrothermal magnetite-destruction / adularia-sericite alteration contrast (`rad_K / Th` high (`ext_ThK` inverted / `rad_K - rad_Th`) coincident with local high-pass `rtp` trough + high MT `cond_surf`).
- **Why It Catches Hidden Faults Missing from USGS/INGENIOUS:** Upwelling boiling fluids oxidize titanomagnetite to non-magnetic pyrite/hematite (`rtp` trough along the fault damage zone!) while precipitating potassium feldspar / illite (`K` enrichment relative to immobile `Th`) and smectite clay caps (`cond_surf` high) across concealed basement steps (`GEO-Pb`).
- **Named Non-Fault Mimic Process:** Potassium-rich rhyolite ash-flow tuff contacts and evaporitic potash playas (`rad_K` high across broad closed basins) $\to$ suppressed by across-strike `1.5–2.5 km` linear persistence and multi-model diversity (`LightGBM` + `HistGradientBoosting`).
- **Expected `DTI` Gain vs Compute Cost:** **Moderate (`Rank 5`)** — leverages fast cached `GEO-Pb` step crests + `~15 s` diverse GBDT ensemble.

---

## 3. Pre-Registered 3-Experiment Ladder (`<= 3` Experiments Total)

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

# Session `arena/41c29ae2-gemsdoe85` — Five Pre-Implementation Hypotheses (`H85-HJCD`)

**Preregistered BEFORE any model code modification or holdout execution (2026-10-22 UTC).**

Why prior `GEMSDOE85` lanes stalled at `0.09838` (`GEO-Pb`, 90k dots; `0.07475` @ 37,654) and
`0.09837` (`E1_supervised_hgb` on `gems85-pooled-hide-v1`, losing to `CTRL_d28 = 0.102305`):
1. **Metric-target mismatch (`pixel binary` vs `300 m triangular kernel`):** Prior supervised learners trained on 1-pixel binary rasterized traces (`y(x) in {0,1}`, positive rate `1.18%`), mislabeling ~85% of the true `300 m` scoring halo (`k(100 m) = 0.667`, `k(141 m) = 0.529`) as negative class `0` right where dipping (~60 deg) normal-fault gravity/magnetic/MT offsets peak down-dip in the hanging wall.
2. **Unused geothermal-vent & shallow-probe discovery datasets:** `GEO-Pb` had `AUC = 0.5034` (`p = 0.213`, statistically indistinguishable from coin flip) at geothermal vents because hydrothermal smectite/illite argillic alteration and magnetite destruction erase crisp fresh-rock magnetic steps while creating **direct fluid-conduit anomalies** in temperature, silica/cation geothermometry, 2-m shallow temperature probes, and siliceous sinter / tufa mounds.
3. **Coarse strike quantization (`8` strikes = `22.5 deg`) & discarded active-tectonic bands:** `GEO-Pb` discarded `training_features.tif` seismicity (`deq_n100a15`, `ieq_n100a15`) and GPS strain (`geod_2ndinv`, `geod_shearrate`, `geod_dilaterate`) and coarsely quantized Basin & Range (`N15-30E`) and Walker Lane (`N35-50W`) fault strikes into `22.5 deg` steps.

### Five Candidate Hypotheses Ranked by Expected DTI Gain vs Implementation Cost

| Rank | ID | Exact Free Official Data Layers Used | Targeted Physical / Geothermal Signature & Transform | Why It Captures Unmapped Hidden Faults Specifically | Difference From ALL Existing Repo & Fleet Methods | Non-Fault Mimic Process | Expected Gain / Cost | Status |
|---:|---|---|---|---|---|---|---|---|
| **1** | **`H85-HJCD-1`** | `training_features.tif` (all 19 official bands incl. unlocked geodetic strain `[4,7,8]` & seismicity `[10,16]`), `lidar_scarp_features_u8.tif` (12 bands, USGS 3DEP 1 m), `geodawn_rad_u8.tif` (4 bands, DOI `10.5066/P93LGLVQ`), `geodawn_extensions_u8.tif` (`ThK`, `UK`, `UTh`, `TMI_up150`) | **16-Azimuth Covariance-Whitened Hotelling Step Juxtaposition (`GEO-Pb-16`, `r=300 m` & `r=600 m`) + Exact `300 m` Kernel-Expectation Regression** (`K_G(x) = max_{g in G}(1 - d(x,g)/300 m)_+`) + shallow magnetic residual (`TMI - TMI_up150`) + transtensional dilatation-shear invariant | Concealed intrabasin/pediment faults offset basement density, cover thickness, and shallow volcanic sheets 100–300 m into the hanging wall without surface scarps; regressing onto `K_G(x)` matches the exact `300 m` Tversky credit surface instead of penalizing off-trace down-dip offset | Upgrades `GEMSDOE85`'s unique `GEO-Pb` Hotelling step operator to `16` orientations (`11.25 deg`), unlocks the 5 discarded active-tectonic bands, and replaces pixel classification with `300 m` kernel-target regression | Unfaulted depositional contacts (pinch-outs, pluton margins) and 400 m E–W GeoDAWN flight-line leveling corrugations | **High gain / Low-Medium cost (~2 min CPU)** — **TESTED IN `EXP-1`, `EXP-2`, `EXP-3`** | **Implemented** |
| **2** | **`H85-HJCD-2`** | **Official DOE GDR 1391 (`https://gdr.openei.org/submissions/1391`, CC BY 4.0):** (a) `paleo_geothermal_regional.zip` (`281` in-footprint sinters, silicified fault sands/breccias, tufas, explosion craters — **measured `2.73x` fault lift within `300 m`**), (b) `2m_temperature_probe_INGENIOUS_regional_data.zip` (`2,782` in-footprint UNR/GBCGE shallow 2-m probes with background-subtracted `F2mDAB`), (c) `gdr_wellspring_in_footprint.csv` (`temp_c`, quartz/chalcedony/Na-K-Ca geothermometers); plus **USGS 3DEP 10 m** `dem10_chi_100m_i16.tif` (`step_max`, `ksn_max`) & `topo_10m_derived_100m_u8.tif` (`curv_prof_absmax`, `aspect_coherence`, `dem_mean`) | **Multi-Observable Blind Hydrothermal Conduit & Fluvial Disequilibrium Coupling:** multi-scale kernel plumes of boiling silica sinter (`>175 C`), shallow 2-m `F2mDAB` thermal anomalies, geothermometry excess, conductive clay-cap (`cond_surf`), and 10 m cross-divide `Delta chi` / Lahontan bench (`~1,335 m`) coupled multiplicatively with oriented `GEO-Pb-16` / scarp structure | Across the Great Basin (`619` hot/warm sites `>3 km` from any mapped fault; `456` hot 2-m probes at median `2.6 km`), fluids cannot cross `10^-17 m^2` basin clay without a permeable (`10^-13 to 10^-11 m^2`) fault-valve conduit — directly pinpointing unmapped blind faults beneath dry playas and fans | **First model in GEMSDOE85 or sibling fleet** to combine UNR/GBCGE 2-m temperature probe surveys + paleo-sinter/tufa fault deposits + cross-divide `Delta chi` + `GEO-Pb-16` juxtaposition | Lateral shallow aquifer outflow plumes (`1–3 km` down hydraulic gradient from upflow fault) & Lake Lahontan wave-cut tufa benches | **High gain / Low cost (~30 s CPU, verified in-sandbox via `60GEMSDOE` mirror of GDR 1391)** — **TESTED IN `EXP-1`, `EXP-2`, `EXP-3`** | **Implemented** |
| **3** | **`H85-HJCD-3`** | Strictly per-fold **`fold.visible` fault mask ONLY** (withheld segments + `300 m` buffer stripped BEFORE any computation; zero full-catalogue leakage) + coupled `H85-HJCD-1/2` hydrothermal & geophysical channels | **Fold-Proper Crack-Tip Stress Projection, En-Echelon Relay Bridges & Submodular `300 m` Dinkelbach Tversky Point-Process Emission** (`Delta TP_300m - lambda_FP * Delta FP_300m` with live coverage map `C_S` and explicit fleet-overlap constraint `<= 0.65 < 0.70`) | `>75%` of Great Basin geothermal systems sit in unmapped fault step-overs, horse splays, and alluvial tip continuations (Faulds & Hinz 2015), where photogeologic traces artificially terminate at bedrock-alluvium contacts; submodular `300 m` coverage eliminates redundant dot overlap | Combines fold-clean fracture-tip/relay fields with `GEO-Pb-16` + 2-m thermal probe / sinter conduits AND explicitly enforces `< 0.70` overlap across all `227` non-saturating fleet rasters | Erosional range-front sinuosity or unfaulted pediment embayments between independent fault segments | **Very High gain / Medium cost (~4 min CPU)** — **TESTED IN `EXP-2` (NMS ablation) & `EXP-3` (Submodular Dinkelbach)** | **Implemented** |
| **4** | **`H85-HJCD-4`** | `training_features.tif` (`tmi`, `tmi_vg`, `mag_anom`), `geodawn_extensions_u8.tif` (`TMI_up150`), `gdr_volcanic_vents_in_footprint.csv` | **GeoDAWN `400 m` Flight-Line Corrugation & Volcanic Flow-Margin Mimic Decoupling:** separate shallow residual (`TMI - TMI_up150`) from deep `TMI_up150` and volcanic-vent proximity so single-sensor magnetic spikes along `400 m` E–W flight lines or basalt flow margins are downweighted unless corroborated by gravity/topographic/thermal structure | Prevents false positives over unfaulted Tertiary lava mesas and `400 m` survey leveling artifacts, preserving mass budget for true concealed faults | Explicitly addresses the verified GeoDAWN Area 2 `400 m` E–W line-spacing artifact (`DOI: 10.5066/P93LGLVQ`) | Dike-fed fault-controlled basalt fissures (rare true positive coincidence where a fault also erupted basalt) | **Moderate gain / Low cost** — shallow residual & volcanic confounder channels folded into `EXP-1..3`; raw flight-line microleveling deferred (raw XYZ blocked) | **Partially folded into `EXP-1..3`** |
| **5** | **`H85-HJCD-5`** | Copernicus Sentinel-1 InSAR time-series (`https://dataspace.copernicus.eu/`) + USGS ANSS / NSL waveform-relocated hypocenters (`https://earthquake.usgs.gov/fdsnws/event/1/query`) | **Sub-km InSAR Phase-Gradient Creep & Relocated Microseismic Fault-Plane Tomography** | Directly images aseismic slip/poroelastic geothermal deformation and blind seismogenic planes (e.g. Monte Cristo Range sequence) beneath featureless playas | Independent dynamic crust measurements at `<100 m` scale | Pumping-induced agricultural/mining subsidence bowls around playa wells | **High potential gain / Blocked in sandbox** (verified egress allowlist permits `github.com`, `pypi.org`, `npmjs.org` only) | **Documented next step (`[BLOCKED]` in sandbox)** |

