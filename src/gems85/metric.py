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


# --- compatibility aliases for the duplex lane (arena/29a39923) -------------------------------
# That lane names the kernel support RADIUS_PX and calls metric.kernel(d).  Same constants, same
# triangular kernel; aliased rather than renamed so neither lane's code has to change and the two
# can never silently diverge.
RADIUS_PX = R_PIXELS


def kernel(d):
    """Official triangular kernel k(d) = (1 - d/R)+, in pixels. Alias for the duplex lane."""
    import numpy as _np
    return _np.clip(1.0 - _np.asarray(d, dtype=_np.float64) / R_PIXELS, 0.0, None)


def dti_exact(pred, truth, alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Duplex-lane alias: the official DTI as a dict. Same computation as `dti()`."""
    r = dti(np.asarray(pred, dtype=np.float64), np.asarray(truth, dtype=bool),
            alpha=alpha, beta=beta)
    return {"dti": r.dti, "tp_w": r.tp_w, "fp_w": r.fp_w, "fn_w": r.fn_w}


def dti_binary(pred, truth, valid=None, known=None,
               alpha: float = ALPHA, beta: float = BETA) -> dict:
    """DTI for a boolean prediction, optionally restricted to a `valid` evaluation domain.

    Binary predictions are provably metric-optimal (docs/research/metric-algebra.md Sec.3).
    Returns a dict so the duplex lane's `evaluate_holdout` can read r["dti"], r["tp_w"], ...
    """
    p = np.asarray(pred, dtype=bool)
    g = np.asarray(truth, dtype=bool)
    if valid is not None:
        v = np.asarray(valid, dtype=bool)
        p = p & v
        g = g & v
    if known is not None:
        # Mask VISIBLE faults pixel-exactly out of the prediction (holdout protocol).  Note this
        # removes them from `pred` only -- it does NOT also drop them from the alpha charge the
        # way GEMSDOE32's `active = valid & ~known` did, which silently made on-catalogue dots
        # free.  See src/gems85/holdout.py.
        p = p & ~np.asarray(known, dtype=bool)
    r = dti(p.astype(np.float64), g, alpha=alpha, beta=beta)
    return {"dti": r.dti, "tp_w": r.tp_w, "fp_w": r.fp_w, "fn_w": r.fn_w,
            "tp": r.tp_w, "fp": r.fp_w, "fn": r.fn_w,   # duplex-lane key names
            "n_pred": int(p.sum()), "n_truth": int(g.sum())}


def dti_bruteforce(pred, truth, alpha: float = ALPHA, beta: float = BETA,
                   r: float = R_PIXELS) -> dict:
    """The metric written out literally from the problem description, O(N_pred x N_truth).

    No dilation, no offset table -- a direct transcription used to cross-check the fast path.
    Only for small grids; `test_metric.py` asserts the two agree.
    """
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth, dtype=bool)
    gy, gx = np.nonzero(g)
    py, px, pv = (*np.nonzero(p > 0), p[p > 0])
    tp = fn = 0.0
    for y, x in zip(gy, gx):
        d = np.hypot(py - y, px - x)
        k = np.clip(1.0 - d / r, 0.0, None)
        best = float((pv * k).max()) if pv.size else 0.0
        tp += best
        fn += 1.0 - best
    fp = 0.0
    for y, x, v in zip(py, px, pv):
        d = np.hypot(gy - y, gx - x)
        k = np.clip(1.0 - d / r, 0.0, None)
        fp += v * (1.0 - (float(k.max()) if gy.size else 0.0))
    den = tp + alpha * fp + beta * fn
    return {"dti": tp / den if den > 0 else 0.0, "tp_w": tp, "fp_w": fp, "fn_w": fn}


def marginal_inclusion_threshold(s: float, alpha: float = ALPHA) -> float:
    """First-order marginal bar: a pixel is worth adding only if it earns more than alpha*s.

    Derivation in docs/research/metric-algebra.md Sec.4.  The refinement that also accounts for
    the denominator moving as mass is added is `alpha*s*f/(1 - alpha*s)`, which is what this
    lane's budget analysis uses; `alpha*s` is its leading term and the form the duplex lane
    assumes.
    """
    return alpha * s


# Offset table under the duplex lane's name: three parallel arrays (dy, dx, weight) over the
# 29-pixel disc of radius R_PIXELS.  Same table `OFFSETS` holds as tuples.
_OFF = (np.array([o[0] for o in OFFSETS], dtype=np.int64),
        np.array([o[1] for o in OFFSETS], dtype=np.int64),
        np.array([o[2] for o in OFFSETS], dtype=np.float64))


def _shift(a: np.ndarray, dy: int, dx: int, fill=0.0) -> np.ndarray:
    """Shift `a` by (dy, dx) with constant fill. Duplex-lane helper name."""
    out = np.full_like(a, fill)
    ys0, ys1 = max(0, dy), min(a.shape[0], a.shape[0] + dy)
    xs0, xs1 = max(0, dx), min(a.shape[1], a.shape[1] + dx)
    yd0, yd1 = max(0, -dy), min(a.shape[0], a.shape[0] - dy)
    xd0, xd1 = max(0, -dx), min(a.shape[1], a.shape[1] - dx)
    if ys1 > ys0 and xs1 > xs0:
        out[ys0:ys1, xs0:xs1] = a[yd0:yd1, xd0:xd1]
    return out
