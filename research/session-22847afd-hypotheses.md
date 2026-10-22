# Session `arena/22847afd-gemsdoe85` — pre-registered hypotheses (written before any experiment)

Date: 2026-10-22. Lane problem IR-85-01 remains open: the prompt references a single
method paragraph but supplies none. Following the precedent of the two merged lanes in
this repository (H85-1 GEO-Pb, H85-A), this session **declares its lane here, before
measuring anything**, and flags the declaration for review. Declared lane:

> **RELAY — fault-network completion gated by multi-physics line evidence.** Hidden
> faults are concentrated where the mapped network is geometrically incomplete —
> beyond segment tips, across en-échelon relay gaps, and along collinear segment
> trains — *provided* independent geophysics shows a line there. Local per-pixel
> detectors (every previous lane in this repo) cannot express "incomplete network";
> a tip/relay geometry field built from fold-visible catalogue only, multiplied into
> a catalogue-free multi-physics field, can.

## Why `h33-h33-2-b2` (0.2778, OWNER-REPORT) won — session answer, verified from bytes

Measured this session from the sha256-pinned raster (`c55bafc4…`, restored and hash-verified):

1. It is a **nested thinning of one field**: `h33 (37,654) ⊂ h27-4 (40,199) ⊂ d2.8
   (44,090) ⊂ h19-5 solid support (121,131 px)`. 100.0 % of h33 dots lie exactly on
   h19-5 support pixels. The score cascade 0.1922 → 0.2477 → 0.2600 → 0.2708 → 0.2778
   is one geological field at five emission budgets — not five ideas.
2. The metric (official: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>)
   pays `T/(0.2(T+F)+0.8K)`. Thinning removes dots whose 300 m kernel credit is already
   claimed by a neighbour; each removed redundant dot cuts the denominator by ≈0.2 while
   cutting `T` by ≈0. Credit/bar algebra: a dot helps iff realised credit `> 0.2·DTI/(1−0.2·DTI)`
   ≈ 0.0588 at DTI 0.2778.
3. The **B2 catalogue-halo prune** (delete dots ≤2 px from the catalogue, 40,199→37,654)
   removed pure false-positive mass: the live truth is *new* faults, so mass on/near mapped
   faults cannot earn credit.
4. **All-finite zeros encoding** avoids the `[0,1]` upload rejection.

Can it be beaten? Only by a field whose **top ~38 k pixels earn more credit per dot**
(>0.145/dot implied). Emission tuning of the same field is exhausted (fleet cascade is
flattening: 44 k→37.6 k bought +0.007). The two live-proven independent signals in the
fleet record that are *not* h19-5 thinnings are tip/stepover geometry (0.2632,
GEMSDOE33, OWNER-REPORT) and an orthogonal-gated field (0.2376 at 40 k, GEMSDOE49;
measured this session: only 42 % of h33 dots lie within 3 px of its dots, so it is a
substantially independent dot set). Independence + live strength is exactly what a
fusion needs. **No local instrument can prove a live beat** — the catalogue holdout is
a screen (IR-85-001/08); this session therefore (a) requires the new *rule* to beat the
repo's holdout best at matched budget, and (b) emits at the **live** operating point
(~38 k, sep ≈2.8–3 px, 2 px halo), not the holdout optimum (90 k) that the previous
primary used — that mismatch is logged as a new irregularity.

## Five candidate hypotheses not previously implemented in this repo

| rank | id | layers | physical signature / transform | why it catches catalogue-missing faults | differs from repo code | named mimic | cost | data needed |
|---:|---|---|---|---|---|---|---|---|
| 1 | **H-RELAY** network completion | fold-visible `labels.tif` geometry + GEO-Pb crest + LiDAR scarp (`lidar_scarp_features_u8` b1/3/6/10) + `rtp/tmi_hg/iso_grav` gradients + radiometrics | Segment-tip extraction (endpoints of thinned segments), tip strike from PCA of terminal 15 px, decaying along-strike **extension rays** (≤60 px), **relay bridges** between facing tip pairs (≤80 px, strike misfit <20°), collinear-train density; geometry field gates the multi-physics field | USGS/INGENIOUS mapping stops where surface expression dies under alluvium; the fault continues. Expert hidden faults were traced with GeoDAWN magnetics through cover — i.e. continuations and gap-links of the visible network | No code in this repo uses segment topology at all; GEO-Pb/HGB are per-pixel | True displacement-death tips (extension overshoots into intact rock); chance-collinear fan/shoreline edges | ~10 min CPU | none (in-repo pins) |
| 2 | **H-CTXHGB** contextual PU supervised v2 | 24-ch stack (`featurestack`) + oriented line-integral context (along-strike means at 8 orientations × 1.5 km of crest/line fields), corroboration count, σ∈{3,9} context means, + RELAY channel (fold-visible) | HistGradientBoosting, PU-style (positives = visible ±1 px, negatives ≥10 px away), trained per fold | A fault is a *line*, not a pixel: per-pixel HGB (AUC 0.57 here) throws away the context an expert uses | Previous HGB arms used per-pixel channels only; no line context, no geometry channel | Cultural lineaments (roads/canals) with line context | ~20 min CPU | none |
| 3 | **H-DEEPSTEP** large-aperture basement step | `rtp` + `TMI_up150` (extensions b4), `iso_grav_anom`, `depth_to_base_surf` | GEO-Pb-style whitened two-sample step at radius 12 px on potential fields only, crest-thinned, gated by shallow ridge ≤3 px | Deep basement faults under thick basin fill have broad, low-amplitude potential-field steps invisible at 300 m aperture | GEO-Pb radii were 3/6 px and mixed shallow bands; fleet pure basement-step scored 0.0009 live, so standalone expectation is low — gate use only | Basin-margin depositional edges (no fault) | ~5 min | none |
| 4 | **H-SPRING** collinear thermal chains | GDR-1391 wellspring points in footprint (`external/gdr_wellspring_in_footprint.csv`; 27,092 rows, ~2 k Hot; **its `dist_known_fault_px` column is label-derived and must not be used**) | Directional line support: max over 16 strikes of thermally-weighted point density along a 2 km line; requires ≥3 collinear Warm/Hot points; used as booster on main field | Geothermal upflow needs permeable fault conduits; aligned hot springs can mark a blind fault with zero scarp/magnetic contrast | Never run in this repo (listed as H85-D, budget-blocked) | Valley-floor / playa-margin spring lines; irrigation wells along roads | ~10 min | present, hash-pinned |
| 5 | **H-CONSENSUS** scored-registry stacking | 17 registry rasters + OWNER-REPORT scores | Live-score-weighted vote field | Would exploit live feedback directly | **Rejected as a submission field**: dots are near-duplicates of registry lanes by construction (protocol §1), it is leaderboard fitting not geology, and the Final Prize Round rescues *discoveries*, not echoes. Retained only as a diagnostic upper-bound reference, never emitted | — | low | present |

Ranking rationale: H-RELAY has the only *independent live evidence* (fleet tip/stepover
0.2632) plus a clean holdout test; H-CTXHGB has the highest holdout ceiling; H-DEEPSTEP
and H-SPRING are cheap gates/boosters, not standalone fields at 38 k dots; H-CONSENSUS
is protocol-rejected.

## Experiments (budget: 3, per protocol §6)

- **E1 — RELAY alone + RELAY-gated GEO-Pb crest.** Canary AUC per new feature first.
- **E2 — CTXHGB** (24 ch + context + RELAY channel), with built-in ablation vs the
  previous 24-ch arm's published numbers on the same evaluator.
- **E3 — Fusion** (rank-average of E2 field, GEO-Pb crest, RELAY-gated crest; weights
  fixed here: 0.5 / 0.25 / 0.25) × emission comparison (Poisson-thin vs greedy
  max-coverage on the kernel-blurred field).

Evaluator for all: `gems85-holdout-v1.0.0` (`src/gems85/holdout.py::score_folds`,
4 spatially-blocked folds, block 200 px, buffer 5 px, 60,988 withheld positives,
pooled DTI α=0.2 β=0.8, 300 m triangular kernel). Every catalogue-derived quantity is
rebuilt per fold from `fold.visible` only; visible faults masked pixel-exactly.

**Reference to beat (same evaluator, matched budget):** GEO-Pb crest sep 4 px —
HOLDOUT-DTI **0.07475 @ 37,654** and **0.09838 @ 90,000** (README §3 table;
`evidence/budget_sweep.json`, `evidence/exp_crest.json`).

## Pre-registered promotion gate (all must hold to publish a NEW primary)

1. Beats 0.07475 @ 37,654 on pooled HOLDOUT-DTI, ≥3/4 folds above the crest reference's
   per-fold values at that budget where available, CI reported.
2. Every new feature's single-feature canary AUC < 0.90 (protocol §4).
3. Not a duplicate: |Spearman| ≤ 0.90 vs every registry surface **and** dot-overlap
   ≤70 % within 3 px vs every *comparable dotted* registry raster, with the
   chance-corrected lift also reported (IR-85-002); raw overlap numbers published, no hiding.
4. Validator: all 17 checks PASS on the re-read written bytes (zeros encoding).
5. Emission at the live operating point (≤44,090 dots primary), 0 dots ≤2 px from catalogue.

Failure of 1–3 ⇒ the file may still be written for inspection but the site banner must
say **DO NOT SUBMIT — did not beat holdout best**, and the session verdict is negative.
No slot is spent by this session in any case (no DrivenData auth in sandbox; selection
is the separate selector step, protocol §6).

## External data check

No new external data is required for ranks 1–4: all layers are already hash-pinned in
`registry/data_manifest.json` (competition mirror + USGS GeoDAWN-derived externals +
GDR-1391 CSV). Official sources: problem/metric/format
<https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> ·
GeoDAWN <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> ·
INGENIOUS <https://gbcge.org/current-projects/ingenious/> · EPSG:32611
<https://epsg.io/32611> · GDR 1391 <https://gdr.openei.org/submissions/1391>.
