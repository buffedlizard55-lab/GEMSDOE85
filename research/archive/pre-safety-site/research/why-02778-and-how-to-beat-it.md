# Why h33-h33-2-b2 scored 0.2778 (ORGANIZER-CONFIRMED) — and what beating it requires

Artifact: `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`
(GEMSDOE32 site; sha256 `c55bafc470054e82…` per that site; full hash in its audit JSON).
Score 0.2778: **[ORGANIZER-CONFIRMED]** as listed in this project's brief.
Current brief-reported leaderboard high: 0.4413 **[ORGANIZER-CONFIRMED per brief]**,
with no file/hash crosswalk available (IR-85-04) — so 0.4413 is a target number,
not an analysable artifact.

## The metric is a budget (official)

DrivenData problem page (official): distance-weighted Tversky index, triangular
kernel `k(d)=max(1−d/R,0)`, R = 300 m, α = 0.2 (FP penalty), β = 0.8 (FN penalty):
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

With T = weighted TP mass, F = weighted FP mass, G = truth pixels:

    DTI = T / (0.2·(T + F) + 0.8·G)

Adding one unit dot whose realised kernel credit is k raises T by k and F by
(1−k); the denominator rises by exactly 0.2 regardless of placement. Hence:

    a dot improves DTI  ⟺  k > 0.2 · DTI        (credit bar)

At DTI = 0.2778 the bar is 0.0556; at 0.4413 it is 0.0883. Verified numerically
against a brute-force transcription of the published equations in
`tests/test_metric_bruteforce.py` (template suite, re-run here).

## Why that file won (mechanism, each step measured in the fleet)

1. **Strong parent field.** Its dots are a thinned subset of the H19-5
   multi-physics ridge field (LiDAR scarp + topography + geophysics corroboration),
   the same family that scored 0.1922 continuous → 0.2477 (d1.5) → 0.2600 (d2.8)
   **[ORGANIZER-CONFIRMED, brief list]**. Field ranking quality, not emission
   cleverness, sets the ceiling.
2. **Binary amplitude.** For fixed support, DTI is strictly increasing in a
   constant amplitude p ∈ (0,1], so {0,1} emission dominates soft probabilities
   emitted as values. (Algebra from the formula above.)
3. **Poisson thinning at d ≈ 2.8 px.** Under the 300 m kernel, adjacent dots on a
   1-px ridge duplicate coverage: the second dot pays ~full FP mass (0.2) for
   ~zero marginal TP. Spacing dots ~2.8 px apart multiplies credit per dot.
   d2.8 (44,090 dots) → r1-solo (40,199) → 0.2708 shows the sweep optimum is real.
4. **Catalogue-halo prune (B2).** Deleting dots within 2 px of the catalogue
   (44,090 → 37,654) removes dots whose 300 m disks mostly overlap faults the
   organizer masks out of scoring — dead FP mass. 0.2708 → 0.2778 followed.
5. **All-finite zeros encoding.** No NaN, no nodata sentinel, every value in
   [0,1] — immune to the `"Predicted values must be in range [0, 1]"` rejection
   that the −3.4e38 feature nodata (or a NaN nodata tag) can trigger.

## Can we beat 0.2778? What it would take

At fixed budget, beating it means raising mean realised credit per dot above
the winner's — i.e. a **surface whose top ~38k pixels are more often within
300 m of a hidden fault**. Three honest routes exist: (a) a better detector
(Lane H85-A, tested here on the protocol holdout against the winner raster
itself as control); (b) better emission on the *same* field — but that drifts
into the winner's lane (dots would land within 3 px of its dots; protocol §1
forbids >70% overlap); (c) genuinely new data (sub-km seismicity — named,
sandbox-blocked). This repo tests (a) and lets the holdout decide; it does not
promise a score. Any number not labelled ORGANIZER-CONFIRMED is a HOLDOUT-DTI
screen on catalogue truth, which structurally cannot reward a fault no expert
has mapped yet.
