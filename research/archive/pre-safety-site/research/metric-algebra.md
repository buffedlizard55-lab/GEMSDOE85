# The metric, reduced — and what it says about every design choice in this repo

All formulas are transcribed from the official problem description and verified in
`tests/test_metric.py` (11 tests, including an O(N²) brute-force transcription at 1e-9 and the
organisers' own worked example).

**Source:** <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>

---

## 1. The published definitions

```
k(d) = (1 - d/R)_+ ,  R = 300 m  (= 3 pixels at the competition's 100 m resolution)

TP_w = sum_{g in G}        max_{x : d(x,g) <= R}  p(x) k(d(x,g))
FP_w = sum_{x : p(x) > 0}  p(x) [ 1 - max_{g in G} k(d(x,g)) ]
FN_w = sum_{g in G}      [ 1 - max_{x : d(x,g) <= R} p(x) k(d(x,g)) ]

DTI  = TP_w / (TP_w + alpha*FP_w + beta*FN_w + eps) ,   alpha = 0.2, beta = 0.8
```

Organisers' worked example: `TP_w = 3.00, FP_w = 1.89, FN_w = 2.00` →
`3.00 / (3.00 + 0.2·1.89 + 0.8·2.00) = 0.6027` → published as **0.60**.
`tests/test_metric.py::test_published_worked_example_combination` ✔

**Implementation note.** Both maxima are grey-scale morphological dilations with the same
non-flat structuring element — the 29-pixel disc of radius 3 weighted by `k`. So the metric is
computed *exactly*, in O(29·N), with no approximation. `kernel_offsets()` returns exactly 29
offsets and `k(0)=1`, `k(3)=0`; both asserted in the tests.

---

## 2. Two exact identities

Writing `T = TP_w`, `F = FP_w`, `K = |G|`, `S = Σ_x p(x)`, `M = Σ_x p(x)·max_g k(d(x,g))`:

| identity | why | test |
|---|---|---|
| `FN_w = K − T` | each FN term is `1 −` the same max that TP sums | `test_fn_identity_equals_K_minus_TP` |
| `FP_w = S − M` | regroup the FP sum by prediction pixel | `test_fp_identity_equals_S_minus_M` |

Substituting the first gives the **design equation**:

```
            T                                       1           alpha·F     beta·K
DTI = -------------------------            <=>   ------- = alpha + ------- + -------
      alpha·(T + F) + beta·K                       DTI              T           T
```

`K` is common to every submission in a round, so **ranking on the leaderboard is ranking by
`T / (alpha·F + beta·K)` and by nothing else** — not by pixel count, not by visual plausibility.

---

## 3. Binary predictions are optimal (why this repo ships dots, not a heat map)

Hold every pixel but `x` fixed. `T` is affine in `p(x)` on each linear piece of the `max`, and
`F` is exactly affine in `p(x)`. A ratio of two affine functions is monotone on an interval, so
its maximum over `p(x) ∈ [0,1]` is at an endpoint: **0 or 1**. Graded confidence is therefore
weakly dominated, pixel by pixel.

*Also verified empirically:* `test_scaling_monotonicity` shows `DTI(λp)` is strictly increasing
in `λ`, so there is never a reason to scale a prediction down.

---

## 4. The marginal rule (the only emission rule used here)

Adding mass at `x` which captures `t` of new truth-weight and wastes `f = 1 − k(x,G)`:

```
new DTI > old DTI   <=>   t > [ alpha·DTI / (1 − alpha·DTI) ] · f
```

| DTI level | bar on `t` per unit wasted mass |
|---:|---:|
| 0.08 (this repo's holdout scale) | 0.0163 |
| 0.26 | 0.0549 |
| 0.2778 | 0.0588 |
| 0.4413 (current leader) | 0.0969 |

**Consequence that matters.** The bar rises with the score you already have, so **the optimal
emitted mass is a function of the achieved DTI, and a budget tuned on a low-scoring proxy does
not transfer to a high-scoring live board.** This repo measures budget behaviour on the holdout
but never imports the holdout's optimum directly — see `docs/research/budget.md`.

---

## 5. What the group's own live data says about the hidden truth set

The one *controlled* two-point experiment on the live scorer in the whole family record
[OWNER-REPORT]: the same raster, with the 2,545 dots lying within 200 m of the mapped catalogue
deleted.

| | dots | live DW-Tversky |
|---|---:|---:|
| `h27-4-solo-d28` | 40,199 | 0.2708 |
| `h33-2-b2` (same file, catalogue-proximal dots deleted) | 37,654 | **0.2778** |

Deleted dots sat on mapped faults, so they can have carried no credit for *new* faults: `T` is
unchanged and only `S` moves. Then `D₁ − D₂ = alpha·2545 = 509` and `D_i = T/DTI_i`, giving

```
T = 509 / (1/0.2708 − 1/0.2778) = 5,470
D₂ = 5,470 / 0.2778 = 19,690
K  = (D₂ − 0.2·(T + S − M)) / 0.8   ≈ 14,400      (M ≈ T/2.5 for thin dots on line truth)
F  = S − M ≈ 35,400
```

So the best artifact in the family's history **captures 5,470 of ≈14,400 units of hidden truth
weight (38 %) and wastes 94 % of its dots**, and the denominator is 8,187 FP-tax against 11,520
`beta·K`. Reproduced by `scripts/solve_truth_scale.py`.

Two readings follow, and they set this session's whole agenda:

1. **Catalogue-proximal mass is measurably negative live.** That single deletion was worth
   +0.0070. Every emission in this repo therefore hard-excludes a 2-pixel halo around the
   catalogue, and the submission validator *checks* it.
2. **The emission lever is spent.** Fitting the family's own thinning cascade
   (121,131 → 0.1922; 60,069 → 0.2477; 44,090 → 0.2600) to `T(n) = c·n^γ` gives γ = 0.229 and an
   optimum near 20,000 px worth **DTI ≈ 0.280** — three thousandths above what the family already
   has. Only a field with higher credit *per emitted pixel* can move this project, which is why
   the lane chosen this session changes the detector statistic rather than the emission rule.
