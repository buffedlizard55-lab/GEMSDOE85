"""Control surfaces the candidate must beat on the same holdout, at matched emitted mass.

All three are rebuilt per fold exactly like the candidate, so the comparison is like-for-like.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import grid


def sato_ridge(band: str = "det_elev", sigmas=(1.0, 2.0, 4.0), footprint=None) -> np.ndarray:
    """Multi-scale Hessian (Sato/Frangi-style) line response -- the archetype of every
    derivative-based detector in the sibling repositories.  Used as the primary control."""
    fp = grid.footprint() if footprint is None else footprint
    a = grid.read_feature(band)
    med = float(np.nanmedian(a[fp]))
    a = np.nan_to_num(a, nan=med).astype(np.float32)
    best = np.zeros(a.shape, np.float32)
    for s in sigmas:
        g = ndi.gaussian_filter(a, s, mode="nearest")
        gyy = ndi.gaussian_filter(g, 0, order=(2, 0), mode="nearest")
        gxx = ndi.gaussian_filter(g, 0, order=(0, 2), mode="nearest")
        gxy = ndi.gaussian_filter(g, 0, order=(1, 1), mode="nearest")
        tmp = np.sqrt((gyy - gxx) ** 2 + 4 * gxy ** 2)
        l1 = 0.5 * (gyy + gxx + tmp)      # larger |eigenvalue|
        r = (s ** 2) * np.abs(l1)         # gamma-normalised ridge strength, both polarities
        np.maximum(best, r.astype(np.float32), out=best)
    best[~fp] = 0.0
    return best


def gradient_magnitude(band: str = "rtp", sigma: float = 2.0, footprint=None) -> np.ndarray:
    """Single-field horizontal-gradient edge strength -- the classic potential-field control."""
    fp = grid.footprint() if footprint is None else footprint
    a = grid.read_feature(band)
    med = float(np.nanmedian(a[fp]))
    a = np.nan_to_num(a, nan=med).astype(np.float32)
    gy = ndi.gaussian_filter(a, sigma, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(a, sigma, order=(0, 1), mode="nearest")
    out = np.hypot(gy, gx).astype(np.float32)
    out[~fp] = 0.0
    return out


def uniform_random(footprint: np.ndarray, seed: int = 0) -> np.ndarray:
    """Pure chance -- the floor any claimed skill must clear."""
    rng = np.random.default_rng(seed)
    out = rng.random(footprint.shape).astype(np.float32)
    out[~footprint] = 0.0
    return out
