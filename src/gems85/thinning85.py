"""Deterministic geodesic Poisson-disk dot thinning (re-implemented, order-recording).

Why this file exists
--------------------
Parent R0 (`h33-h33-2-b2`, owner-reported live DTI 0.2778) is not a model output that can be
re-fitted: it is a *deterministic function* of two pinned rasters.  The chain, as recorded in the
GEMSDOE24/25/28 lineage, is

    H19-5 1-px ridge skeleton (121,131 px, `e27054cf`)
        -> priority-ordered Poisson-disk thinning at min_dist = 2.8 px   -> 44,090 dots (`e56ea318`)
        -> drop dots with d(catalogue) <= 1.0 px (H27-4 flank prune)     -> 40,199 dots (`8acb75e1`)
        -> drop dots with d(catalogue) <= 2.0 px (H33-2-B2 = R0)         -> 37,654 dots (`e5eb6e7e`)

This module re-implements the thinning so the whole chain can be rebuilt in this repository and
**verified by SHA-256**, and so that the ordering the packing algorithm used (its "priority") can
be recovered as an explicit per-dot rank instead of being an implicit side effect of raster order.

Determinism contract (identical to the sibling implementation this was checked against):
  * seeds are the lowest raster index of each 8-connected component;
  * traversal inside a component is FIFO breadth-first over the 8-neighbourhood;
  * a candidate pixel is kept iff no already-kept pixel lies strictly inside radius `min_dist`;
  * output is always a subset of the input and reads no labels, scores or features.

`dot_thin(order=True)` additionally returns the acceptance rank of every kept pixel
(0 = kept first).  That rank is the parent's *recorded* priority order and is reported as a
diagnostic; the MASS experiment uses the metric-geometry ranking in `r0_lineage.py` instead,
because raster-order acceptance is spatially biased (see the mechanism card).
"""

from __future__ import annotations

from collections import deque

import numpy as np
from scipy.ndimage import label

__all__ = ["dot_thin", "disc_offsets"]


def disc_offsets(min_dist: float) -> list[tuple[int, int]]:
    """Integer (dy, dx) offsets strictly inside radius `min_dist` (unit digitisation)."""
    r = int(np.ceil(min_dist))
    lim = min_dist * min_dist
    return [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
            if dy * dy + dx * dx < lim]


def dot_thin(mask: np.ndarray, min_dist: float, *, order: bool = False):
    """Poisson-disk thin a binary mask; optionally return per-pixel acceptance rank.

    Parameters
    ----------
    mask : (H, W) array-like of bool
        Candidate pixels (typically a 1-px ridge skeleton).
    min_dist : float
        Minimum Euclidean spacing in pixels (`<= 1.0` short-circuits to the input).
    order : bool
        If True, also return an int32 array where kept pixels hold their acceptance rank in
        `[0, n_kept)` and every other pixel holds `-1`.

    Returns
    -------
    kept : (H, W) bool ndarray
    rank : (H, W) int32 ndarray, only when ``order=True``
    """
    m = np.asarray(mask, bool)
    if m.ndim != 2:
        raise ValueError("2-D mask required")
    if min_dist <= 1.0 or not m.any():
        kept = m.copy()
        return (kept, np.where(kept, 0, -1).astype(np.int32)) if order else kept

    H, W = m.shape
    pad = int(np.ceil(min_dist)) + 1
    padded = np.zeros((H + 2 * pad, W + 2 * pad), bool)
    padded[pad:pad + H, pad:pad + W] = m
    kept = np.zeros_like(padded)
    blocked = np.zeros_like(padded)
    visited = np.zeros_like(padded)
    disc = disc_offsets(min_dist)

    comp, _ = label(padded, structure=np.ones((3, 3), int))
    order_idx = np.flatnonzero(comp.ravel())
    _, first = np.unique(comp.ravel()[order_idx], return_index=True)
    seeds = order_idx[np.sort(first)]

    tile = np.zeros_like(padded)
    rank_tile = np.full(padded.shape, -1, np.int32)
    accepted = 0
    h, w = padded.shape
    for seed in seeds.tolist():
        if visited.ravel()[seed]:
            continue
        visited.ravel()[seed] = 1
        q = deque((seed,))
        while q:
            c = q.popleft()
            cy, cx = divmod(c, w)
            if not blocked[cy, cx]:
                kept[cy, cx] = True
                rank_tile[cy, cx] = accepted
                accepted += 1
                for dy, dx in disc:
                    blocked[cy + dy, cx + dx] = True
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and padded[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        q.append(ny * w + nx)

    out = kept[pad:pad + H, pad:pad + W].copy()
    del tile
    if order:
        return out, rank_tile[pad:pad + H, pad:pad + W].copy()
    return out
