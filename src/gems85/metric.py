"""Exact transcription of the official distance-weighted Tversky index (DTI).

Source (read 2026-10-22, quoted verbatim in docs/research/metric-transcription.md):
  https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

    k(d) = (1 - d/R)_+ ,  R = 300 m  (3 pixels at 100 m)

    TP_w = sum_{g in G}        max_{x : d(x,g) <= R}  p(x) k(d(x,g))
    FP_w = sum_{x : p(x) > 0}  p(x) [ 1 - max_{g in G} k(d(x,g)) ]
    FN_w = sum_{g in G}      [ 1 - max_{x : d(x,g) <= R} p(x) k(d(x,g)) ]

    DTI(alpha, beta) = TP_w / (TP_w + alpha*FP_w + beta*FN_w + eps)
    alpha = 0.2 (false positives), beta = 0.8 (false negatives)

Both maxima are *grey-scale morphological dilations* with the same non-flat structuring
element (the triangular kernel over the 29-pixel disc of radius 3), so the metric is exact
and O(29 N) -- no approximation anywhere in this file.

Verified in tests/test_metric.py against
  (a) the organisers' own published worked example  (TP_w 3.00, FP_w 1.89, FN_w 2.00 -> 0.60), and
  (b) a literal O(N^2) brute-force transcription of the three sums on random rasters.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

ALPHA = 0.2
BETA = 0.8
R_PIXELS = 3.0
EPS = 0.0  # organisers' eps is a zero-division guard; it is 0 for every non-degenerate raster


def kernel_offsets(r: float = R_PIXELS) -> list[tuple[int, int, float]]:
    """All integer offsets within Euclidean distance r, with their triangular kernel weight."""
    ri = int(np.floor(r))
    out = []
    for dy in range(-ri, ri + 1):
        for dx in range(-ri, ri + 1):
            d = float(np.hypot(dy, dx))
            if d <= r:
                out.append((dy, dx, max(0.0, 1.0 - d / r)))
    return out


OFFSETS = kernel_offsets()


def kernel_dilate(a: np.ndarray, offsets=OFFSETS) -> np.ndarray:
    """max_{offset} a(x + offset) * k(|offset|)  -- exact, boundary-safe (outside = 0)."""
    a = np.asarray(a, dtype=np.float64)
    h, w = a.shape
    out = np.zeros_like(a)
    for dy, dx, k in offsets:
        if k == 0.0:
            continue
        ys_src = slice(max(0, -dy), h - max(0, dy))
        ys_dst = slice(max(0, dy), h - max(0, -dy))
        xs_src = slice(max(0, -dx), w - max(0, dx))
        xs_dst = slice(max(0, dx), w - max(0, -dx))
        np.maximum(out[ys_dst, xs_dst], a[ys_src, xs_src] * k, out=out[ys_dst, xs_dst])
    return out


@dataclass(frozen=True)
class DTIResult:
    dti: float
    tp_w: float
    fp_w: float
    fn_w: float
    n_truth: int
    pred_mass: float
    pred_pixels: int

    def as_dict(self) -> dict:
        return asdict(self)


def dti(
    pred: np.ndarray,
    truth: np.ndarray,
    *,
    domain: np.ndarray | None = None,
    alpha: float = ALPHA,
    beta: float = BETA,
) -> DTIResult:
    """Official DTI.

    pred   : float array in [0,1] (NaN treated as 0 -- NaN carries no prediction mass)
    truth  : boolean / 0-1 array of ground-truth fault pixels G
    domain : optional boolean mask restricting *both* sums (used by the holdout evaluator to
             score one spatial block; the live scorer's domain is the whole raster).
    """
    p = np.nan_to_num(np.asarray(pred, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
    g = np.asarray(truth).astype(bool)
    if domain is not None:
        dom = np.asarray(domain).astype(bool)
        p = np.where(dom, p, 0.0)
        g = g & dom
    if p.shape != g.shape:
        raise ValueError(f"shape mismatch {p.shape} vs {g.shape}")

    # TP_w: for every truth pixel, the best kernel-weighted prediction within R.
    best_pred_at_truth = kernel_dilate(p)
    tp_w = float(best_pred_at_truth[g].sum())

    # FP_w: for every predicting pixel, its mass times (1 - closeness to the nearest truth).
    kernel_truth = kernel_dilate(g.astype(np.float64))
    pos = p > 0
    fp_w = float((p[pos] * (1.0 - kernel_truth[pos])).sum())

    n_truth = int(g.sum())
    fn_w = float(n_truth - tp_w)  # identity: each term is 1 - (that same max)

    denom = tp_w + alpha * fp_w + beta * fn_w + EPS
    value = float(tp_w / denom) if denom > 0 else 0.0
    return DTIResult(value, tp_w, fp_w, fn_w, n_truth, float(p.sum()), int(pos.sum()))


def dti_value(pred, truth, **kw) -> float:
    return dti(pred, truth, **kw).dti
