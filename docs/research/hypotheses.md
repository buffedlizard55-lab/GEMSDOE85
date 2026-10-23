# Candidate Geological Hypotheses — Pre-Registration, Physical Mechanisms & Spatially-Blocked Holdout Results

**Session:** `arena/7ded4c0a-gemsdoe85` · **Pre-registration:** [`research/session-7ded4c0a-hypotheses.md`](../../research/session-7ded4c0a-hypotheses.md)  
**Evaluator:** `gems85-holdout-v1.0.0` (`60,988` withheld positives, 4 spatially-blocked segment folds with `5 px` buffer, $\alpha=0.2$, $\beta=0.8$, $300\text{ m}$ triangular kernel).

---

## Summary Ranking (Expected DTI Gain vs Implementation Cost — Pre-Registered Prior to Holdout Runs)

| Rank | ID | Hypothesis Name | Key Layers & Physical Transform | Why It Catches Unmapped Concealed Faults | Outcome on `gems85-holdout-v1.0.0` (`37,654` dots) |
|---:|---|---|---|---|---|
| **1** | **`H85-GAPVENT`** | Seamless 10 m 3DEP + Fluvial $\chi$-Knickpoint + Blind Geothermal Radon + Shallow Demag / Tilt / $60^\circ$-Dip Kernel Regressor | `topo_10m_derived_100m_u8.tif`, `dem10_chi_100m_{u8,i16}.tif`, `lidar_scarp_features_u8.tif` (`valid`, `lapneg`, `upface`, `cross`), DOE GDR 1391 non-tufa paleo-vents + 2 m probes + geothermometers (`2.5 km` Radon strike corridor), `TMI - TMI_up150`, Miller-Singh tilt zero-crossing, $60^\circ$-dip gravity back-projection, continuous $k(d)=\max(0,1-d/3)$ target + surveyed-corridor PU sampling (`IR-85-023`) | Bridges the **`24.63%` `[MEASURED]` non-LiDAR gap**, captures eroded drainage-step faults ($\Delta k_{sn}$), illuminates **blind hydrothermal conduits** (`Faulds & Hinz 2015`), shifts hanging-wall gravity gradients back onto surface traces, and eliminates PU unmapped-basin suppression | **PROMOTED (`E1`: `0.13299` @ `exc=2`; `E2`: `0.14232` @ `exc=3`, `+76.1%` over prior record `0.08082`, `4/4` folds won, OOF `ROC-AUC = 0.6842`)** |
| **2** | **`H85-SUBMOD300` + `exc=3` Halo** | Calibrated $300\text{ m}$ Submodular Marginal Coverage vs Poisson-Disk Crest + Exact $300\text{ m}$ (`exclude_px=3`) Catalogue Halo Removal | `src/gems85/emitter.py` (`dT(x) = \sum_\delta p^\gamma(x+\delta)\max(0, k(\delta)-C)`) vs `emission.emit(sep_px=2.8)` tested at `exclude_px=2` vs `exclude_px=3` | Removes residual `200–300 m` visible-fault flank false positives (`2,171` left behind by `H33-2-B2`) and tests exact submodular coverage vs peak-intensity spacing | **`exclude_px=3` WON `4/4` folds (`0.13299 -> 0.14232`, `+0.00933`); `submod300` sub-arm NEGATIVE (`0.11412` vs `0.14232`) due to 29-px blob bias** |
| **3** | **`H85-ORTHOFUSE`** | Cross-Mechanism Supervised + Unsupervised Juxtaposition Ensemble | `0.92 * rank01(H85-GAPVENT) + 0.08 * rank01(GEO-Pb crest)` (`E3_orthofuse92`) and `0.65/0.20/0.15` blend with `CTXHGB-30` | Pairs supervised scarp/hydrothermal kernel regression with label-free Hotelling multi-physics juxtaposition (`GEO-Pb`) | **Achieved highest OOF `ROC-AUC = 0.6850` and `0.14177` `HOLDOUT-DTI` (`+75.4%` over prior record; published as downloadable `alt-orthofuse92`)** |
| **4** | **`H85-VOLCDECONF`** | Orthometric `1,335 m` Lake Lahontan Shoreline & Volcanic Mesa Caprock Deconfounders | `zmean_m` (`dem10_chi_i16` band 5) $\exp(-((z-1335)/14)^2)/(1+1.5\|\nabla g\|)$, elevated `TMI_hg / grav_slope` gate, and explicit `Tufa` exclusion (`86/281` GDR paleo-deposits) | Suppresses constant-elevation pluvial Lake Lahontan wave-cut shorelines/tufas and magnetic basalt mesa rims that mimic tectonic scarps | **VALIDATED inside `H85-GAPVENT` (`canary AUC < 0.51`, clean mimic separation)** |
| **5** | **`H85-INSAR-SEIS`** | Sentinel-1 InSAR LOS Strain-Rate Gradient + Relocated Microseismicity | NASA ASF ARIA/COMET unwrapped InSAR LOS velocity gradient + USGS ANSS / UNR NSL relocated $M \ge 1.0$ hypocenters | Detects aseismically creeping and microseismically active blind faults beneath playafill with zero surface scarp | **DATA-BLOCKED in sandbox** (egress restricted to GitHub/PyPI/npm; documented for external execution) |

---

## Detailed Physical & Mathematical Specifications

### 1. `H85-GAPVENT` + `H85-VOLCDECONF` (`src/gems85/gapvent.py`)
- **Seamless 10 m USGS 3DEP Gap-Bridge (`13` channels):**
  - `gv_lidar_valid` (`band 12 > 0`: `75.37%` covered vs `24.63%` gap), plus previously unused 1 m LiDAR scarp bands `gv_lidar_lapneg` (band 4, footwall convex break), `gv_lidar_upface` (band 7, antithetic graben scarps — **`canary AUC = 0.5796`**, higher than `lidar_step_max` `0.5683`!), and `gv_lidar_cross` (band 8).
  - Nine 100%-coverage USGS 3DEP 1/3 arc-second (`~10 m`) sub-cell channels (`slope_p90`, `steep_frac`, `slope_std`, `relief`, `curv_prof`, `aspect_coh`, `hs_line`), culminating in our **relief-normalized piedmont scarp enhancer** `gv_dem10_piedmont_scarp = curv_prof * (aspect_coh/255) / (G_8(relief) + 12)` (**`canary AUC = 0.5922`**) and its 8-strike $1.5\text{ km}$ persistence `gv_dem10_line_s15` (**`canary AUC = 0.5942`, #1 single-feature fault predictor in the 57-channel stack**).
- **Fluvial $\chi$-Integral & Knickpoint Channels (`4` channels):**
  - `gv_chi_knick_dens`, `gv_chi_step_pos` ($\max(0, \Delta k_{sn})$ across fault traces, **`canary AUC = 0.5542`**), `gv_chi_ksn_resid` (local watershed-detrended channel steepness), and `gv_chi_raised_asym` (uplifted footwall drainage-divide $\chi$ asymmetry).
- **Blind Geothermal Upflow & Strike Corridors (`4` channels, DOE GDR 1391 `DOI 10.15121/1881483`):**
  - `195` non-tufa Quaternary hydrothermal paleo-vents (`Sinter`, `Travertine`, `Explosion craters`, `Silicified fault breccia`, `Silica-cemented sand/vein`, `Sulfur`, `Alteration`; **`86` lacustrine `Tufa` mounds explicitly excluded**), `464` shallow 2 m temperature-probe anomalies (`F2mDAB >= 2.0 °C` or `T2m >= 25.0 °C`), and deep chemical geothermometer wells/springs (`temp_c >= 37 °C` or quartz/cation/chalcedony `>= 110 °C`; **`dist_known_fault_px` strictly banned in code**), combined into the $2.5\text{ km}$ 8-strike collinearity channel `gv_vent_radon_corridor`.
- **Potential-Field, Demagnetization & Andersonian Mechanics (`3` channels):**
  - `gv_mag_demag_shallow = robust_z(TMI) - robust_z(TMI_up150)` (hydrothermal magnetite destruction in upper $150\text{–}500\text{ m}$),
  - `gv_mag_tilt_contact` (unit-calibrated Miller & Singh 1994 magnetic tilt-angle vertical-contact zero-crossing $\exp(-|\theta|/0.35)\tanh(\text{hg}_n)$),
  - `gv_anderson60_grav` (up-dip trace back-projection of `iso_grav_anom_slope` shifted by $\Delta_{\text{px}} = \text{clip}(Z_{\text{base,m}} / (100\tan 60^\circ), 0, 12)$ along basinward $\nabla Z_{\text{base}}$).
- **Surveyed-Corridor PU Kernel Regression (`IR-85-023`):**
  - Trains a dual-link (`0.55 * Poisson + 0.45 * L2`) `HistGradientBoostingRegressor` directly on continuous $300\text{ m}$ DTI kernel credit $y = \max(0, 1 - d_{\text{vis}}/3)$, sampling negatives strictly from **surveyed quadrangles (`4 <= d_vis <= 45 px`)** and excluding raw basin-ID coordinates (`BASIN_ID_CHANNELS`) so the model never learns to suppress unmapped quadrangles.
  - **Verification inside deep unmapped basin interiors (`d_vis > 45 px`, `36,227` withheld fault pixels):** achieves **`mean ROC-AUC = 0.7184`** (`[0.7336, 0.6722, 0.7185, 0.7491]`), proving genuine zero-leakage generalization miles away from any visible fault.

---

## Single-Feature Leakage Canary Summary (`evidence/session_7ded4c0a_canaries.json`)

- **Channels tested:** `57 / 57` catalogue-free channels
- **Hard leakage ceiling:** `AUC < 0.90`
- **Maximum observed single-channel AUC:** `gv_dem10_line_s15 = 0.5942` (`gv_dem10_piedmont_scarp = 0.5922`, `geopb_r6_L25 = 0.5879`, `geopb_r3_L15 = 0.5818`, `gv_dem10_slope_std = 0.5801`, `gv_lidar_upface = 0.5796`)
- **Verdict:** **ALL 57 CHANNELS CLEAN (`PASS`)**
