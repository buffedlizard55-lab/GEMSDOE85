# Historical Archive: Early Lane H85 Exploratory Session (Superseded by Promoted `H85-HJCD`)

> **Archival Note (2026-10-22 — Resolved Merge Conflict `IR-85-009b` & Corrected `IR-85-010`):**
> This page preserves the historical pre-`H85-HJCD` exploratory session notes cleanly after resolving a git merge conflict left between two early branches.
> - **Current Promoted Deliverable:** See [`../index.html`](../index.html) and [`../executive-summary.html`](../executive-summary.html) for **Lane `H85-HJCD` (`gemsdoe85-hjcd-ventbridge-submod-zeros.tif`)**, which achieved **`HOLDOUT-DTI = 0.196461`** (`95% CI [0.176165, 0.216681]`, `gems57-pooled-hide-v2`, `11,321` withheld positives; `+0.101848` = `+107.6%` over fold-proper `H33-2-B2`), **`0.131399`** blind (`EXP-1`) on `gems85-holdout-v1.0.0` (`60,988` positives), **`0.180935`** on `gems85-pooled-hide-v1` (`24,440` positives), and **`0.228042`** on `gems57-detached-400m-v2`.
> - **Erratum Corrected (`IR-85-010`):** One merged side of the earlier draft misstated positive pixel counts in `existing_faults.tif`. Direct array verification confirms `existing_faults.tif == 1` has **`60,988` pixels**, pixel-for-pixel identical to `labels.tif == 1` (`60,988` pixels across `5,167,373` in-footprint cells).

---

## Summary of Early Session (`Lane H85-A/B/C` — Honest Negative Baseline)

In the initial session before DOE GDR 1391 2-m temperature probes, paleo-geothermal sinter/tufa deposits, USGS 3DEP 10 m $\chi$ disequilibrium, 16-strike `GEO-Pb-16`, fold-proper fracture-relay mechanics, kernel-expectation targets, and submodular Dinkelbach emission were introduced:

| Early Candidate / Control | Evaluator | Withheld Positives | `HOLDOUT-DTI` | `95% CI` | Verdict |
|---|---|---:|---:|---:|---|
| `E1` H85-A pixel-level HGB (35+20 static channels, `@37,654`) | `gems85-pooled-hide-v1` | `24,440` | `0.098366` | `[0.088263, 0.107428]` | Negative (`< CTRL_d28`) |
| `E2` H85-B orientation consensus | `gems85-pooled-hide-v1` | `24,440` | `0.0366` | `[0.029, 0.044]` | Negative |
| `E3` H85-C strain-gated lineament | `gems85-pooled-hide-v1` | `24,440` | `0.0317` | `[0.022, 0.040]` | Negative |
| `CTRL_d28` (`ORGANIZER-CONFIRMED: 0.2600` receipt) | `gems85-pooled-hide-v1` | `24,440` | `0.102305` | `[0.0933, 0.1118]` | Control bar |
| **`EXP-3` `H85-HJCD` (Current Session Breakthrough)** | **`gems85-pooled-hide-v1`** | **`24,440`** | **`0.180935`** | **`[0.165, 0.197]`** | **PROMOTED (`+76.9%` over `CTRL_d28`)** |

---

## Key Diagnostic Lessons Carried Directly Into `H85-HJCD`

1. **Pixel-binary loss vs 300 m kernel expectation:** Training `HistGradientBoostingClassifier` on `1-px` binary labels caused probability dilution across uncertain scarps and lost to `CTRL_d28` (`0.0984` vs `0.1023`). Regressing directly on expected `300 m` kernel credit $\mathbb{E}[\max_{g \in G_{\text{hid}}} k(d(x,g)) \mid X]$ while tracking trace probability $p_{\text{trace}}(x)$ for submodular coverage eliminates that mismatch (`0.0984 -> 0.1809` on the exact same `gems85-pooled-hide-v1` split!).
2. **Portal `[0, 1]` range requirement:** Early `-nan.tif` variants risked portal rejection (`"Predicted values must be in range [0, 1]"`). All primary deliverables strictly use all-finite `float32` in `[0.0, 1.0]` with `nodata=None` (`0.0` outside footprint and within `B=2` of `existing_faults.tif`), verified programmatically by both `gems85.submission.validate` and `gems57.validate`.
3. **Saturating lattice witnesses vs discriminating fault predictions (`IR-85-07`):** Separating the `9` space-filling continuous/lattice files (`cov_3 >= 0.70`) from all `227` real fault-prediction rasters across the fleet (`cov_3 <= 0.319`) cleanly enforces the `< 0.70` 3-px uniqueness rule across every real sibling prediction without false pigeonhole rejection.

## Official Reference Links Verified Line-by-Line

- DrivenData Competition #306: <https://www.drivendata.org/competitions/306/competition-doe-gems/>
- Problem Description & Exact Metric: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
- Complete DOE / NLR Prize Rules (PDF): <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
- USGS GeoDAWN Survey (`DOI: 10.5066/P93LGLVQ`): <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>
- DOE GDR Submission 1391 — INGENIOUS Regional Compilation (`DOI: 10.15121/1881483`): <https://gdr.openei.org/submissions/1391>
- EPSG:32611 WGS 84 / UTM Zone 11N: <https://epsg.io/32611>
