# Geothermal vent & blind-system discovery in the Great Basin — reusable knowledge

**Scope.** What is actually known about how hidden geothermal upflow is found in the Basin and
Range, which of it is usable as a *fault-prediction* prior for DrivenData #306, and — the part
that matters most — **measurements made in this repository rather than recited.**

**Source discipline.** Every claim is tagged:
`[MEASURED-HERE]` reproducible from this repo · `[PUBLISHED]` established literature/agency
result, source linked, **not re-fetchable from this sandbox** (network allowlist — see README §5)
· `[INFERENCE]` reasoning by the author of this file. Nothing here is organizer-authenticated.

---

## 1. Why geothermal evidence is a fault prior at all

A Basin-and-Range geothermal system has, with very few exceptions, **no magmatic heat source.**
Heat comes from deep circulation of meteoric water down a permeable structure and back up
another. The permeability *is* the fault. `[PUBLISHED]` — this is the central finding of the
USGS/Nevada "blind geothermal systems" programme and the DOE **INGENIOUS** project, the same
project that contributed part of this competition's fault catalogue
(<https://gdr.openei.org/submissions/1391>).

The structural settings repeatedly identified as hosting upflow `[PUBLISHED]`:

| setting | why it leaks | map signature |
|---|---|---|
| **Fault step-overs / relay ramps** | dilational jog keeps fracture apertures open | two sub-parallel traces with an en-échelon gap |
| **Fault tips & terminations** | horsetail splays, high fracture density | a trace that simply stops |
| **Fault intersections** | sub-vertical pipe of intersecting fracture sets | X or Y junctions |
| **Accommodation zones** | transfer of extension between opposing dip domains | change in fault polarity along strike |
| **Displacement minima on long faults** | a fault "waist" tends to be where segments linked | along-strike low in throw |

**The operational consequence for this competition.** Those settings are all *geometric relations
between faults*, not pixel textures. They predict **where an unmapped fault should connect two
mapped ones** — which is exactly the `h27`/`h34` "corridor/gap-closure" family already tried in
the sibling repositories (live 0.2708 for `h27-4`; the H34 corridor variant scored 0.0778 on
holdout). `[INFERENCE]` The lesson is that the *idea* is right and already harvested; the
remaining value is in the **thermal evidence that sits where no fault is mapped at all.**

## 2. What the repository's own thermal data says `[MEASURED-HERE]`

Source: `data/external/gdr_wellspring_in_footprint.csv` — 27,092 rows / **12,570 unique sites**
inside the survey footprint, derived from the DOE **Geothermal Data Repository** spring- and
well-chemistry compilations (`spring_chemistry_20220808` and siblings). Reproduce with the script
block in §6.

**1,839 unique sites are classed `Hot` or `Warm`.**

| statistic | hot/warm sites | uniform random in footprint | lift |
|---|---:|---:|---:|
| median distance to nearest mapped fault | **16.5 px (1.65 km)** | 23.4 px (2.34 km) | — |
| within 1 km of a mapped fault | **37.4 %** | 24.9 % | **1.50×** |
| within 3 km | 66.3 % | 59.3 % | 1.12× |
| within 5 km | 82.9 % | 78.8 % | 1.05× |

**Finding 1 — thermal features really are fault-associated, but the association is short-range
and weak.** A 1.50× enrichment at 1 km decaying to 1.05× at 5 km. That is a *real* signal and it
is *far too diffuse to localise a 300 m-kernel prediction on its own*. Any method that paints a
3–5 km halo around hot springs is emitting ~99 % uncredited mass.

**Finding 2 — the discovery target, quantified. 619 of the 1,839 hot/warm sites (33.7 %) are more
than 3 km from *any* mapped fault.** One of them carries a cation-geothermometer reservoir
estimate of **296.5 °C**. These are places with direct physical evidence of deep circulation and
**no mapped structure to explain it**. That set — not the catalogue — is the population the
competition's private labels are drawn from in spirit.

**Finding 3 (a clean negative) — GEO-Pb does not see them.** The lane's own detector, evaluated
at those hot/warm sites against matched random pixels:

| field | AUC at hot/warm sites | p (Mann–Whitney, one-sided) |
|---|---:|---:|
| `geopb_crest` | 0.5034 | 0.213 |
| `geopb_r3_L15` (pre-NMS) | 0.5023 | 0.371 |

**Indistinguishable from random.** `[INFERENCE]` This is the most useful result in this file,
and it cuts two ways. It falsifies any claim that GEO-Pb is "finding geothermal structure"; it is
finding *lithological juxtaposition*, which is a different thing. But it also means a thermal
channel is **statistically orthogonal** to GEO-Pb — it is a genuine fusion partner rather than a
redundant one, which is rarer and more valuable than a correlated confirmation would have been.

**Finding 4 — the volcanic-vent layer is too sparse to use.** `gdr_volcanic_vents_in_footprint.csv`
contains **21 vents** (mostly basalt, ages largely null). Twenty-one points cannot support a
feature on a 12.3-million-pixel grid. Recorded so no future session re-opens it.

## 3. The remote-sensing toolkit, and why most of it fails *this* metric

`[PUBLISHED]` The standard blind-system detection stack, with this lane's assessment:

| technique | what it detects | usable here? |
|---|---|---|
| **ASTER/TIR night-time thermal** | surface temperature anomaly over upflow | **No.** 90 m TIR; anomalies are 1–5 K over 10²–10³ m blobs. Wrong shape for a 300 m kernel on a *line*. |
| **Hydrothermal mineral mapping** (ASTER SWIR: opal, chalcedony, alunite, kaolinite) | fossil & active sinter/alteration | **Partially.** Sinter aprons are 10–100 m — *smaller* than a pixel. Would need the 30 m product, not reachable here. |
| **Self-potential / audio-MT** | fluid flow, conductive clay cap | **No.** Ground surveys; no regional coverage. |
| **InSAR subsidence/uplift** | production- or circulation-driven ground motion | **High value, unreachable.** Sentinel-1 is free (ESA/Copernicus, ASF DAAC) and Basin-and-Range extension is detectable. Blocked by the network allowlist. |
| **Seismicity (ANSS / NSHM)** | active fault planes, including buried ones | **High value, unreachable.** The single best independent evidence that a *blind* structure is active. |
| **Soil-gas CO₂ / Hg** | deep gas leakage along faults | **No.** Point surveys only. |
| **Airborne radiometric K/Th/U** | hydrothermal K-metasomatism; U/Th mobility | **Yes — already in the stack.** GEO-Pb's radiometric domain uses exactly this (GeoDAWN K/Th/U/TC). |
| **Aeromagnetics (RTP, tilt, Euler)** | magnetite destruction in upflow zones; basement offset | **Yes — already in the stack, and saturated.** Every sibling lane uses it. |

`[INFERENCE]` **The honest conclusion: the geothermal literature's best discovery tools are
either the wrong spatial scale for a 300 m line-kernel metric, or unreachable from this sandbox.**
The two that would genuinely move the needle — InSAR and seismicity — are both free and both
blocked. That is stated as a blocker in the README, not papered over.

## 4. The one geothermal idea that *is* metric-shaped

`[INFERENCE]` Derived from Findings 1–3 above, not from the literature:

> **Thermal sites are a weak, isotropic, short-range prior; GEO-Pb is a strong, oriented,
> zero-thermal-information prior. The metric rewards lines, not blobs. Therefore use the thermal
> layer as a *multiplier on an oriented field*, never as a field of its own.**

Concretely: `score(x) = geopb_crest(x) · (1 + λ·exp(−d_thermal(x)/τ))` with τ ≈ 10 px (1 km, the
scale at which the measured lift is 1.50×) and λ tuned on the holdout. This re-ranks GEO-Pb's own
crests toward thermal evidence without emitting a single pixel that GEO-Pb did not already
propose — so it cannot increase uncredited mass, only redistribute the fixed budget. It is a pure
**re-ranking under a mass constraint**, which is the only kind of change the marginal-bar algebra
(`docs/research/metric-algebra.md` §4) says is free.

**Status: specified, not implemented.** It did not fit in this session's budget. It is item 3 in
the README's remaining-work list and is the highest-value cheap experiment left in this lane.

## 5. Official sources

| source | link | state |
|---|---|---|
| DOE Geothermal Data Repository (host of the spring/well chemistry + INGENIOUS) | <https://gdr.openei.org/> | data present in-repo; site not fetchable from sandbox |
| INGENIOUS fault & favourability compilation | <https://gdr.openei.org/submissions/1391> | cited, unverified here |
| USGS GeoDAWN airborne geophysics (mag + radiometric), Nevada | DOI <https://doi.org/10.5066/P93LGLVQ> | data present in-repo; DOI not fetchable from sandbox |
| USGS Quaternary Fault and Fold Database | <https://www.usgs.gov/programs/earthquake-hazards/faults> | cited, unverified here |
| USGS State Geologic Map Compilation (SGMC) | <https://mrdata.usgs.gov/geology/state/> | derived raster present in-repo |
| USGS 3DEP 1 m lidar | <https://www.usgs.gov/3d-elevation-program> | derived raster present in-repo |
| Copernicus Sentinel-1 (InSAR), free | <https://dataspace.copernicus.eu/> | **blocked by allowlist** |
| USGS ANSS Comprehensive Catalog (seismicity), free | <https://earthquake.usgs.gov/earthquakes/search/> | **blocked by allowlist** |

## 6. Reproducing §2

```python
import sys; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from scipy import ndimage as ndi, stats as st
from gems85 import grid

fp, cat = grid.footprint(), grid.catalogue()
ws = pd.read_csv("data/external/gdr_wellspring_in_footprint.csv")
sites = ws.drop_duplicates(subset=["row", "col"])
hot = sites[sites.thermalclass.astype(str).str.contains("Hot|Warm", case=False, na=False)]

d = ndi.distance_transform_edt(~cat)                      # px to nearest mapped fault
rng = np.random.default_rng(7); ys, xs = np.nonzero(fp)
k = rng.choice(ys.size, 20_000, replace=False)
hot_d, rand_d = d[hot.row.values, hot.col.values], d[ys[k], xs[k]]
for r in (10, 30, 50):
    print(r, (hot_d <= r).mean() / (rand_d <= r).mean())  # 1.50x, 1.12x, 1.05x

f = np.load("data/cache/ch_geopb_crest.npy")
u = st.mannwhitneyu(f[hot.row.values, hot.col.values], f[ys[k], xs[k]], alternative="greater")
print(u.statistic / (len(hot) * 20_000), u.pvalue)        # AUC 0.5034, p 0.213
```

---

## 6. Session `arena/7ded4c0a-gemsdoe85` Empirical Expansion — Seamless 10 m 3DEP, Fluvial $\chi$-Knickpoints, Non-Tufa Paleo-Vents & 2 m Thermal Probes

All datasets below were restored via `scripts/restore_data.py` and SHA-256-verified against `registry/data_manifest.json` (`28/28` verified):

### 6.1 Audited Public Datasets & Measured Footprint Coverage (`5,167,373` pixels)

| Dataset ID (`registry/data_manifest.json`) | Official Public Source & License | Measured Coverage / Count in Footprint | Key Physical Signal & Mimic Control |
|---|---|---|---|
| `ext_lidar_scarp` (`lidar_scarp_features_u8.tif`) | USGS 3DEP 1 m LiDAR (`1m_DEM_links.csv`), public domain | **`75.37%` valid** (`3,894,768` px; **`24.63%` gap** = `1,272,605` px) | Explicit `gv_lidar_valid` (band 12) + unused scarp bands `lapneg` (b4), `upface` (b7, `AUC=0.5796`), `cross` (b8) (`IR-85-018`). |
| `ext_topo_10m_derived_u8` (`topo_10m_derived_100m_u8.tif`) | USGS 3DEP 1/3 arc-sec (`~10 m`) seamless DEM (`usgs.gov/3d-elevation-program`), public domain | **`100.00%` valid** (`5,167,373` px) | Relief-normalized piedmont scarp `curv_prof * aspect_coh / (G_8(relief)+12)` (`AUC=0.5922`) + 1.5 km strike persistence `gv_dem10_line_s15` (`AUC=0.5942`). |
| `ext_dem10_chi_u8` & `ext_dem10_chi_i16` (`dem10_chi_100m_{u8,i16}.tif`) | USGS 3DEP 10 m tiles (`n38w117..n41w121`), $\theta=0.45$, $A_c=0.2\text{ km}^2$ (`Perron & Royden 2013`) | **`99.90%` valid** (`21.77%` active channel cells) | Across-fault steepness step $\Delta k_{sn} > 0$ (`gv_chi_step_pos`, `AUC=0.5542`), uplifted footwall $\chi$ asymmetry, and orthometric elevation `zmean_m` (m ASL). |
| `ext_gdr_paleo_geothermal` (`paleo_geothermal_regional.zip`) | DOE GDR 1391 INGENIOUS (`DOI 10.15121/1881483`, CC BY 4.0) | `281 / 709` in footprint: **`195` hydrothermal vents** vs **`86` lacustrine `Tufa`** | `Sinter` (50), `Travertine` (36), `Explosion craters` (10), `Silica-cemented sand` (73), `Alteration/Sulfur/Breccia` (26); **`Tufa` explicitly excluded** to avoid Lake Lahontan shoreline mimicry. |
| `ext_gdr_2m_probes` (`2m_temperature_probe_INGENIOUS_regional_data.zip`) | DOE GDR 1391 INGENIOUS (`Coolbaugh/Sladek` UNR/GBCGE, CC BY 4.0) | `2,782 / 3,800` stations in footprint; **`464` anomalies** (`F2mDAB >= 2 °C` or `T2m >= 25 °C`) | Spans 12 blind Great Basin geothermal systems (`Gabbs Valley`, `Astor Pass`, `Desert Queen`, `Dead Horse Wells`, `Desert Peak`, `Salt Wells`, `Hawthorne`, etc.); encoded via 2.5 km 8-strike Radon collinearity (`gv_vent_radon_corridor`) rather than radial halos (`GEMSDOE36` lesson). |
| `ext_geodawn_ext` (`geodawn_extensions_u8.tif`) + `training_features.tif` | USGS GeoDAWN (`DOI 10.5066/P93LGLVQ`, CC0) + INGENIOUS regional compilations | **`99.98%`–`100%` valid** | Shallow hydrothermal magnetite destruction `robust_z(TMI) - robust_z(TMI_up150)`, unit-calibrated Miller & Singh (1994) magnetic tilt zero-crossing, Andersonian $60^\circ$-dip gravity back-projection, and `1,335 m` Lake Lahontan shoreline deconfounder. |

### 6.2 Key Methodological Discovery (`IR-85-023`): Positive-Unlabeled Basin-Void Debiasing
When training supervised fault detectors on an incomplete geological map (`existing_faults`), sampling background negatives uniformly across `d_vis > 12 px` while supplying long-wavelength basin-identifying coordinates (`zmean_m`, `depth_to_base`, `cond_surf`, `rad_K/Th/TC`, radial site proximity) teaches tree ensembles to predict zero inside **unsurveyed quadrangles and blind basins** — the exact regions where concealed faults reside. Restricting PU negative sampling to **surveyed corridors (`4 <= d_vis <= 45 px`, strictly from `fold.visible`)** and restricting tree splits to **48 translation-invariant local physical channels** raised 4-fold spatially-blocked `OOF ROC-AUC` from `0.5844 -> 0.6842` (`0.6801` inside the `24.63%` non-LiDAR gap and **`0.7184` inside deep unmapped basin interiors `d_vis > 45 px`**) and raised `HOLDOUT-DTI` at `37,654` dots from **`0.08082` to `0.14232` (`+76.1%`)**.

