"""Turning a belief field into the pixel set that the metric actually pays for.

The design rule is the metric's own first-order condition, derived in docs/research/
metric-algebra.md and verified in tests/test_emission.py:

    DTI = T / ( alpha*(T + F) + beta*K )        T = TP_w, F = FP_w, K = |G|

    adding mass at x improves DTI  <=>  t  >  alpha*DTI/(1 - alpha*DTI) * f
                                        with t = truth-weight newly captured,
                                             f = 1 - k(x, G)  (<= 1)

Two consequences used here:

 * **p is binary.** DTI is a ratio of two functions each affine in p(x), so for every pixel the
   optimum of p(x) on [0,1] is an endpoint.  Graded confidences are strictly dominated.
   (`tests/test_emission.py::test_binary_is_optimal`)
 * **Dots, not lines.** Mass whose captured truth-weight is already claimed by a neighbour adds
   nothing to T (which is a max over predictions) but a full alpha to the denominator, so a
   minimum separation is applied: it is redundancy removal, not aesthetics.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .metric import ALPHA


def marginal_bar(dti: float, alpha: float = ALPHA) -> float:
    """Truth-weight a new unit of mass must capture, per unit of wasted mass, to pay for itself."""
    return alpha * dti / (1.0 - alpha * dti)


def _disc_offsets(radius: float) -> np.ndarray:
    r = int(np.ceil(radius))
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    keep = (dy * dy + dx * dx) <= radius * radius
    return np.stack([dy[keep], dx[keep]], axis=1).astype(np.int32)


def poisson_thin(
    field: np.ndarray,
    *,
    n: int,
    sep_px: float,
    allowed: np.ndarray,
    topk_pool: int = 4_000_000,
) -> np.ndarray:
    """Greedy highest-value-first dot placement with a hard minimum separation.

    Deterministic: ties are broken by raster order.  Returns a boolean array with <= n True.
    """
    h, w = field.shape
    cand = allowed & np.isfinite(field) & (field > 0)
    idx = np.flatnonzero(cand)
    if idx.size == 0:
        return np.zeros((h, w), bool)
    vals = field.ravel()[idx]
    if idx.size > topk_pool:
        part = np.argpartition(-vals, topk_pool)[:topk_pool]
        idx, vals = idx[part], vals[part]
    order = np.argsort(-vals, kind="stable")
    idx = idx[order]
    ys, xs = np.divmod(idx, w)

    blocked = np.zeros((h, w), dtype=bool)
    out = np.zeros((h, w), dtype=bool)
    offs = _disc_offsets(sep_px)
    oy, ox = offs[:, 0], offs[:, 1]
    taken = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        if blocked[y, x]:
            continue
        out[y, x] = True
        taken += 1
        yy = y + oy; xx = x + ox
        ok = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
        blocked[yy[ok], xx[ok]] = True
        if taken >= n:
            break
    return out


def exclusion_mask(catalogue: np.ndarray, *, buffer_px: int) -> np.ndarray:
    """Pixels that may NOT be emitted on: within `buffer_px` of a known-catalogue fault.

    Justification is measured, not aesthetic: the operator's own ledger reports that deleting
    the 2,545 dots within 200 m of the catalogue from a 40,199-dot artifact moved the live score
    0.2708 -> 0.2778 (OWNER-REPORT).  Mass on a mapped fault cannot be a *new* fault, so it
    earns no TP and pays a full alpha.
    """
    if buffer_px <= 0:
        return ~catalogue.astype(bool)
    halo = ndi.binary_dilation(catalogue.astype(bool), np.ones((3, 3), bool), iterations=buffer_px)
    return ~halo


def emit(
    field: np.ndarray,
    *,
    footprint: np.ndarray,
    visible_catalogue: np.ndarray,
    n: int,
    sep_px: float = 2.8,
    exclude_px: int = 2,
) -> np.ndarray:
    """Full emission rule -> float32 raster of 0.0/1.0."""
    allowed = footprint & exclusion_mask(visible_catalogue, buffer_px=exclude_px)
    dots = poisson_thin(field, n=n, sep_px=sep_px, allowed=allowed)
    return dots.astype(np.float32)
