"""Deterministic sparse placement for the GEMS distance-weighted metric."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import maximum_filter


def emit_peaks(surface: np.ndarray, eligible: np.ndarray, budget: int = 60_000,
               min_distance_px: float = 2.8) -> np.ndarray:
    """Select high-scoring local peaks with Euclidean spacing.

    The competition kernel has a 3-pixel radius.  A 2.8-pixel spacing avoids
    almost duplicate dots while allowing the integer-grid distance 3 cells.
    Ties are deterministic because candidates are sorted by score, row, col.
    """
    if surface.shape != eligible.shape:
        raise ValueError("surface and eligible masks must have identical shapes")
    if budget <= 0:
        return np.zeros(surface.shape, dtype=bool)
    score = np.where(eligible & np.isfinite(surface), surface, -np.inf).astype(np.float32)
    local_max = maximum_filter(score, size=7, mode="constant", cval=-np.inf)
    is_peak = np.isfinite(score) & (score == local_max)
    rows, cols = np.nonzero(is_peak)
    if rows.size == 0:
        return np.zeros(surface.shape, dtype=bool)
    values = score[rows, cols]
    # lexsort's last key is primary: descending score, then ascending location.
    order = np.lexsort((cols, rows, -values))
    rows, cols = rows[order], cols[order]

    h, w = surface.shape
    blocked = np.zeros((h, w), dtype=bool)
    result = np.zeros((h, w), dtype=bool)
    radius = float(min_distance_px)
    ceil_r = int(np.ceil(radius))
    selected = 0
    for row, col in zip(rows.tolist(), cols.tolist()):
        if blocked[row, col]:
            continue
        result[row, col] = True
        selected += 1
        r0, r1 = max(0, row - ceil_r), min(h, row + ceil_r + 1)
        c0, c1 = max(0, col - ceil_r), min(w, col + ceil_r + 1)
        for dr in range(r0 - row, r1 - row):
            for dc in range(c0 - col, c1 - col):
                if float(dr * dr + dc * dc) < radius * radius:
                    blocked[row + dr, col + dc] = True
        if selected >= int(budget):
            break
    return result
