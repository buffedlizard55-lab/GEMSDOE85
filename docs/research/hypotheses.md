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

1. **`E1` (`H2 + H3 + H4`: Structural-Geophysical + Fold-Safe Network Continuation + Dual-Expectation Submodular Dinkelbach Selector):**
   - Evaluates sharp `1 px` OOF `LightGBM` probability/proximity models on core + 1 m LiDAR + 10 m 3DEP + $\chi$ knickpoints + flight-line-notched GeoDAWN + SGMC + fold-safe visible-fault network features, emitted via exact submodular Dinkelbach selection on `gems57-pooled-hide-v2`.
2. **`E2` (`+ H1`: Adding Newly Assembled Blind Hydrothermal & `1900–2026` Sub-km Seismotectonic Conduit Stack):**
   - Identical learner hyperparameters, identical folds, and identical Dinkelbach selector, adding `usgs_comcat_geodawn.csv` (`3,977` events), `2m_temperature_probe` (`2,782` probes `F2mDAB`), `Paleo_geothermal` (`195` siliceous vents vs `86` tufa), and `gdr_wellspring` geothermometry — isolating the exact causal `HOLDOUT-DTI` delta of blind hydrothermal-seismic conduit physics.
3. **`E3` (`+ H5`: Full Multi-Physics Stack + `GEO-Pb` Juxtaposition Crests + Hydrothermal Alteration Coupling + Diverse OOF `LightGBM + HistGradientBoosting` Ensemble & Anisotropic Along-Strike Kernel Refinement):**
   - Full `H1..H5` feature set trained with diverse out-of-fold learners (`LightGBM` + `HistGradientBoosting`) and along-strike ridge continuity weighting inside the submodular Dinkelbach selector. Best holdout arm on `gems57-pooled-hide-v2` (provided it beats every valid control and clears leakage + uniqueness gates) generates the final unique submission `.tif` + `.zip` via unmodified `vendor/gems57/submission_writer.py`.
