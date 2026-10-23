# Geothermal Vent & Blind-Fault Conduit Discovery in the Great Basin — Reusable Scientific Knowledge Base

**Scope.** What is physically established about hidden geothermal upflow and unmapped fault permeability in the northwestern Great Basin (DOE GEMS study area, EPSG:32611, `3730 × 3292` at `100 m`), what is **directly measured in this repository**, and how those physical signatures translate into positive holdout DTI gains under the competition's `300 m` (`3 px`) triangular Tversky kernel (`alpha = 0.2`, `beta = 0.8`).

**Source discipline.** Every statement carries an explicit provenance tag:
- `[MEASURED-HERE]` — computed directly from SHA-256-pinned data on disk in `/home/user/GEMSDOE85` with pure stdlib + `numpy`/`scipy`/`rasterio` (zero external `pandas` dependency).
- `[VERIFIED-OFFICIAL]` — verified directly line-by-line during this session from official agency pages/documents (`drivendata.org`, `docs.nlr.gov/docs/fy26osti/96647.pdf`, `gdr.openei.org/submissions/1391`, `usgs.gov` GeoDAWN).
- `[PUBLISHED]` — peer-reviewed structural geology / Great Basin geothermal literature (Faulds & Hinz 2015; Sibson 1990; Whipple et al. 2017; Willett et al. 2014).

---

## 1. Why Geothermal Upflow Targets Unmapped Fault Conduits Rather Than Mapped Main Scarps

Great Basin hydrothermal systems rarely possess shallow magmatic chambers (`only 21 Quaternary volcanic vents` lie inside the entire `51,674 km²` survey footprint `[MEASURED-HERE]`). Instead, meteoric fluids circulate to `3–6 km` depth within high-heat-flow crust and ascend narrowly where **fault-valve permeability** (`Sibson 1990`) stays propped open against active WNW–ESE Basin-and-Range extension (`Faulds & Hinz 2015`) `[PUBLISHED]`:

| Structural setting | Why permeability stays open (`[PUBLISHED]`) | Why standard USGS QFFD / INGENIOUS maps miss it (`[PUBLISHED] + [MEASURED-HERE]`) |
|---|---|---|
| **Dilational relay ramps / en-échelon step-overs** | Displacement transfers across `1–8 km` step-overs via dense secondary normal faults & tensile vein networks instead of a single tall master scarp | Individual relay splays have `< 0.5–1.5 m` throw across unconsolidated fan gravel or playa silt, falling below 1:24,000 aerial-photo scarp mapping thresholds |
| **Horsetail fault tips & terminations** | Crack-tip tensile stress quadrants (`sigma_xx` dilatation) maintain open vertical fracture pipes | Throw decays continuously to zero toward fault terminations, burying the outer `1–4 km` tip damage zone beneath Holocene alluvium |
| **Silica-sealed fossil fault-valve conduits** | Episodic co-seismic boiling precipitates opal-A -> chalcedony sinters & silicified fault breccias at the surface outlet, shifting active upflow into adjacent splays | Once sealed, surface scarp relief erodes while indurated siliceous sinter/tufa mounds persist for `10^4–10^5 yr` directly over the buried conduit |
| **Blind basin-floor outflows (`2-m` temperature probes)** | Upwelling thermal water rises along buried intrabasin faults to the water table, generating shallow conductive anomalies (`F2mDAB >= +2 °C`) | Zero surface topographic break across active playa / alluvial-flat evaporites |

---

## 2. Empirical Measurements Across All Four Public Geothermal & 3DEP Layers in `GEMSDOE85` `[MEASURED-HERE]`

### 2.1 Exact Public Catalogue Inventory (`existing_faults.tif` vs `labels.tif`)
Direct full-array comparison (`src/gems85/hjcd.py`, resolving `IR-85-010`):
- Grid shape: **`3730 × 3292`** (`12,279,160` total cells; **`5,167,373`** finite in-footprint cells = `51,673.73 km²`).
- `existing_faults.tif == 1`: **`60,988` pixels** (`1.1803%` of footprint).
- `labels.tif == 1`: **`60,988` pixels** — **pixel-for-pixel identical** (`np.array_equal(existing_faults == 1, labels == 1) == True`). Every withheld segment in Phase 1 test and Phase 2 expert update is scored strictly outside `existing_faults.tif == 1`.

### 2.2 Finding A — Paleo-Geothermal Sinter & Tufa Deposits (`paleo_geothermal_regional.zip`, DOE GDR 1391, CC-BY 4.0)
Parsed pure-stdlib from `data/external/paleo_geothermal_regional.zip` (`src/gems85/hydrothermal.py`):
- **Regional records:** `709` deposits; **in-footprint records:** **`281` deposits** (`86` tufa, `73` silica-cemented sand, `50` siliceous sinter, `36` travertine, `13` hydrothermal alteration, `10` phreatic explosion craters, `5` native sulfur, `2` silicified fault breccia, `6` undifferentiated).
- **Direct 300 m scoring-kernel enrichment:** **`8.90%`** of paleo-vents fall within the exact **`300 m` (`3 px`)** competition scoring kernel of an already-mapped fault versus **`3.26%`** for uniform random in-footprint cells — a **`2.73×` empirical lift right at the scoring radius**, rising to **`24.56%`** within `1 km` (`~2.0×` lift).
- **Crucial unmapped discovery target:** **`256 of 281` (`91.1%`)** sit **outside `300 m`** of any mapped fault in `existing_faults.tif`. Because siliceous sinter (`SiO2` precipitation requiring reservoir temperatures `> 175 °C`) cannot form without a deep bedrock fault conduit reaching the surface, non-Lahontan sinter/breccia mounds outside mapped scarps directly pinpoint unmapped hydrothermal fault outlets.
- **Physical non-fault mimic controlled in features:** Pleistocene **Lake Lahontan (`~1,335 m` highstand)** shoreline wave-cut tufa benches (`lahontan_1335m_prox = exp(-((elev - 1335)/32)^2)` explicitly included so gradient-boosted trees down-weight shoreline tufas relative to high-elevation siliceous sinters!).

### 2.3 Finding B — UNR / GBCGE Shallow 2-Metre Temperature Probe Surveys (`2m_temperature_probe_INGENIOUS_regional_data.zip`, DOE GDR 1391, CC-BY 4.0)
- **Regional stations:** `3,800` probes across hidden-system prospect grids; **in-footprint stations:** **`2,782` stations**, of which **`456` stations** record background-detrended shallow temperature anomalies **`F2mDAB >= +2.0 °C`** (`max > +25 °C`).
- Crucially, `probe2m_survey_dens_s10` is paired alongside `probe2m_dab_s5` and `probe2m_dab_s15` so the learner distinguishes **true positive thermal anomalies within a survey grid** from **survey selection bias** (cold background stations inside the exact same survey grid yield explicit negative contrast).

### 2.4 Finding C — Thermal Well/Spring Geothermometry (`gdr_wellspring_in_footprint.csv`, `dist_known_fault_px` Banned)
- **Records parsed:** `27,092` fluid analyses (`2,060` unique hot/warm cells inside footprint; `619` hot/warm sites sit `> 3 km` from any mapped fault, up to `296.5 °C` cation geothermometer temperature).
- **Leakage prevention (`BANNED_COLUMNS`):** Both `gdr_wellspring_in_footprint.csv` and `gdr_volcanic_vents_in_footprint.csv` carry a pre-joined `dist_known_fault_px` column in their upstream CSV schema. `src/gems85/hydrothermal.py` hard-bans `BANNED_COLUMNS = {"dist_known_fault_px"}` in code and enforces this with automated unit tests (`tests/test_hjcd.py`) plus single-feature holdout AUC canaries (`max AUC = 0.75985 <= 0.90` across all `112` features).
- **Orthogonality to 8-strike `GEO-Pb`:** Pure `GEO-Pb-8` achieves Mann–Whitney `AUC = 0.5034` (`p = 0.213`) on hot/warm spring locations — statistically orthogonal to hydrothermal fluid flow — confirming that geothermal upflow brings genuinely independent fault information unseen by potential-field step filters alone.

### 2.5 Finding D — 12/16-Strike `GEO-Pb-16` + USGS 3DEP `10 m` Cross-Divide $\chi$ & Asymmetric Piedmont Hinges
- On an integer lattice, radius `r = 3 px` realizes only `8` distinct step orientations (`22.5°` strike gaps), aliasing NNE/NNW Walker Lane vs Humboldt structural trends. Adding exact lattice rings `NORMALS_R4_12` (`12` unique orientations at `r = 4`) and `NORMALS_R6_16` (`16` unique orientations at `r = 6`) raises blind topographic step `AUC` on withheld faults from `~0.562` to **`0.60067`**, and asymmetric piedmont hinge inflection reaches **`0.61936`** without touching a single fault pixel.
- **Measured blind holdout breakthrough:** Even with **zero fault catalogue input at test time**, `EXP1_hjcd_blind_phys_nms` beats both `CTRL_d28` and fold-proper `H33-2-B2` (`0.2778` live winner rule):
  - `gems57-pooled-hide-v2` (`11,321` withheld positives): **`HOLDOUT-DTI = 0.104076`** vs `CTRL_h33_2_b2_foldproper = 0.094613` and `CTRL_d28 = 0.091888`.
  - `gems85-holdout-v1.0.0` (`60,988` positives across 4 spatial folds): **`HOLDOUT-DTI = 0.131399`** vs `CTRL_d28 = 0.111529` (`+17.8%`) and `CTRL_geopb8_90k = 0.094943` (`+38.4%`).
- When coupled with strictly fold-visible fracture continuation and opposing half-beam geometric-mean relay bridges (`sqrt(B^+ * B^-)`), `EXP3_hjcd_submod_dinkelbach` reaches **`HOLDOUT-DTI = 0.196461`** (`95% CI [0.176165, 0.216681]`), **more than doubling `H33-2-B2` (`+0.101848`, `+107.6%`)** at virtually identical dot budget (`37,288` vs `35,212` / `37,656` dots).

---

## 3. Verified Official Data & Competition Sources `[VERIFIED-OFFICIAL]`

| Official source | Verified URL / DOI | License / Competition Status |
|---|---|---|
| DrivenData Competition #306 — DOE GEMS | <https://www.drivendata.org/competitions/306/competition-doe-gems/> | Active (`#1 xiaofanhu 0.4413`, `#2 cfld__ 0.3904`, `#3 Batik Shirt Brothers 0.3904`, `#4 BrandenKMurray 0.3713`, `#5 No Fault of Our Own 0.3539`, verified `2026-10-22`) |
| DrivenData #306 Problem Description & Exact DTI Formula | <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> | `EPSG:32611`, `100 m`, `float32 in [0, 1]`, `alpha=0.2, beta=0.8, R=300 m` |
| Official DOE / NLR Complete Prize Rules (OSTI #96647) | <https://docs.nlr.gov/docs/fy26osti/96647.pdf> | `$50K` Phase 1 + `$250K` Phase 2; `3` subs/week; external public data & generative AI allowed with disclosure |
| DOE GDR Submission 1391 — INGENIOUS Great Basin Regional Compilation | <https://gdr.openei.org/submissions/1391> (`DOI: 10.15121/1881483`) | **CC BY 4.0** (free open public license; attribution included) |
| USGS GeoDAWN Airborne Magnetic & Radiometric Survey (Glen & Earney 2024) | <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> (`DOI: 10.5066/P93LGLVQ`) | **CC0 1.0 Public Domain** (`200 m` E–W lines Area 1; `400 m` E–W lines Area 2) |
| USGS 3D Elevation Program (3DEP) `1/3` arc-second (`~10 m`) DEM | <https://www.usgs.gov/3d-elevation-program> | **U.S. Public Domain** |

---

## 4. Pure-Stdlib + NumPy/SciPy Reproducibility Snippet (Zero `pandas` Dependency — Fixes `IR-85-014`)

```python
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, "src")
from gems85 import grid, hydrothermal

fp, cat = grid.footprint(), grid.catalogue()
assert int(cat.sum()) == 60_988  # exact mapped fault count in both labels.tif & existing_faults.tif

paleo_f, paleo_stats = hydrothermal.load_paleo_geothermal_fields(Path("data/external"), fp)
probe_f, probe_stats = hydrothermal.load_2m_probe_fields(Path("data/external"), fp)
spring_f, spring_stats = hydrothermal.load_wellspring_and_volcanic_fields(Path("data/external"), fp)

print("Paleo-vents in footprint:", paleo_stats)     # 281 sites (86 tufa, 50 sinter, ...)
print("2-m probes in footprint :", probe_stats)     # 2,782 probes, 456 >= +2.0 C
print("Hot/warm spring cells   :", spring_stats)    # 2,060 hot/warm cells, dist_known_fault_px banned
```
