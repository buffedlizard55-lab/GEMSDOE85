# H33: what the bytes and metric establish—and what they do not

## Evidence boundary

The brief associates H33-2-B2 with **0.2778 (OWNER-REPORTED, not submission-receipt verified)**. That is not a new measurement and is **not labeled ORGANIZER-CONFIRMED** here. The [source page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) describes the file as unscored; a later owner report could be real, but the authenticated receipt is absent. No projection is a score, and no previous model-derived “live mirror” statistic is substituted for the strict HOLDOUT-DTI requested in this run.

## Artifact forensics

The primary was downloaded privately for education, hash checked, reopened with Rasterio and tested against the restored reference. See [`evidence/h33_learning_audit.json`](../evidence/h33_learning_audit.json) and [`registry/learning_manifest.json`](../registry/learning_manifest.json) for measured data and immutable artifact provenance.

**ARTIFACT-MEASUREMENT, not model performance:**

- SHA-256: `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`.
- The single float32 band matches the mirror grid: EPSG:32611, shape (height, width) = (3730, 3292), affine (100, 0, 243350, 0, -100, 4508550).
- Positive support: 37,654 pixels; zero positives on mapped catalogue pixels; zero at Euclidean distance at most two pixels from the catalogue.
- The local format validator reports finite values in [0,1], zero positive mass outside the footprint, and no nodata tag. This is not organizer upload acceptance.

The [GEMSDOE32 builder](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/scripts/run_h33_validation.py) explicitly constructs H33-2-B2 as a flank-deletion sweep of an existing sparse base. Its source describes deleting dots within the catalogue-distance collar; that is **not** the same thing as a new geothermal detector, a PINN, or the separately named H33 multiphysics hypothesis union. Reusing this file with a new filename would violate this run's uniqueness requirement.

## Metric explanation

From the [organizer formula](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric), let:

- `T` be the sum, over ground-truth pixels, of the **maximum** predicted-confidence × triangular-distance weight;
- `F` be weighted false-positive prediction mass;
- `N` be the number of truth pixels, so weighted false-negative mass is `N − T`.

The metric constants are alpha = 0.2, beta = 0.8 and a 300 m support radius. Then, ignoring only the tiny stabilizing epsilon in the displayed algebra,

`DTI = T / [0.2 T + 0.2 F + 0.8 N]`.

For a proposed change `(ΔT, ΔF)`, cross-multiplication gives the exact improvement condition (with positive denominators):

`ΔT × (D − 0.2 T) > 0.2 T × ΔF`, where `D` is the old denominator (including epsilon if used).

Thus:

- Removing redundant predictions that do not change any truth pixel's maximum coverage leaves `T` unchanged and can reduce `F`; that improves DTI whenever `T > 0` and weighted false-positive mass actually falls.
- A sparse set spaced on the scale of the scoring kernel can avoid paying for many redundant pixels. This explains a plausible benefit of thinning a broad detector field.
- Deleting near-catalogue dots might remove redundant or already-mapped-looking structure. But an unknown fault can join a mapped fault, form a secondary strand, or fall inside that collar. Therefore a collar deletion can also reduce `T` and worsen DTI. Distance from a known fault is **not** proof of a false positive.
- A lower dot count alone is not evidence of improvement. Equal-size candidate comparisons must hold the physical domain, hidden segments and masks fixed; compare the pooled ratio, not an average of ratios.

The organizer also says to submit predictions for **all faults** and describes rescoring on expanded labels in the final round. Zeroing the mapped catalogue or widening a collar is a modeling/round-objective choice, not an official file-format requirement. A rule useful against new-fault truth could lose recall under expanded truth. The local holdout mask is prescribed by this prompt; its implementation is not proof of undisclosed live-scorer behavior.

This arithmetic explains a *mechanism by which* H33's design could help. It cannot establish exactly why its owner-reported result occurred, how much of the reported gain came from thinning versus location choice, whether the reported artifact matches an uploaded file, or what the private/final result would be. Those require hidden truth or a matched organizer ablation and receipts. Any categorical geological explanation of the reported increment without that evidence would overclaim.

## Can a unique candidate exceed it?

There is no mathematical ceiling at the owner's reported value. Better incremental truth coverage per unit false-positive mass could improve DTI. The public leaderboard supports that stronger performance is possible for some models, not that our untested model will achieve it. No numerical forecast is made.

The most defensible path is a distinct, physically motivated detector for concealed faults, calibrated on a leakage-screened, whole-component spatial holdout, then a separately checked emission rule. The [research shortlist](hypotheses.md) defines falsifiable candidates and non-fault mimics. We cannot implement the top candidate yet: no lane assignment/cache was supplied and the literal overlap rule is saturated by an existing dense prior. The correct result today is **negative preflight**, not an artificially “unique” TIFF or an unsupported higher-score promise.

## Portal range error

The organizer requires in-footprint confidence values in [0,1]. Passing through feature nodata sentinels, infinities, NaNs inside the footprint, or unnormalized logits violates a valid export policy. The shared writer rejects these values **before** serializing; it does not silently clip or fill them. It reopens the written TIFF, compares grid metadata and validates a one-TIFF ZIP.

The organizer's public format description permits null/NaN outside bounds. The observed error text does **not** prove NaN or a particular nodata tag caused the user's failure. The template's all-finite, no-nodata, zero-outside export is a conservative local policy, not an assertion of organizer acceptance or a reinterpretation of the rules. Local tests alone never earn a competition score.
