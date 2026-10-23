"""SNAP axis: move each R0 dot <= r px onto the strongest local potential-field / scarp edge.

Mechanism under test
--------------------
The live metric credits a dot only through the 300 m (3 px) triangular kernel, so a 1 px
position error costs ~0.33 of that dot's maximum credit.  GeoDAWN Area 2 was flown at 400 m
line spacing, 150-200 m above terrain (USGS data release, DOI 10.5066/P93LGLVQ), i.e. about
1.5-2 px of positional uncertainty on any lineament the parent's ridge skeleton extracted.
SNAP asks a single question: *does snapping the parent's own dots onto the local maximum of
an independent edge field move them closer to the truth?*  It holds the dot count, the
catalogue exclusion and the packing rung fixed, so the only changed variable is position.

What it must not do
-------------------
1. Never place a dot closer to the catalogue than it started (the parent already paid for
   that exclusion; SNAP is not a PRUNE experiment in disguise).
2. Never pile dots up.  Two dots 1 px apart pay 0.2 of mass each while T (a max over dots)
   only keeps one of them, so a snap that collapses the 2.8 px packing rung is a loss by
   construction.  Destinations must keep >= 2.0 px from every stationary dot and from every
   already-accepted destination.
3. One dot per cell, count preserved exactly.

Everything here is a deterministic function of its inputs: no seed, no randomness, ties
broken by (improvement, dot index, offset index).
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

KERNEL_R = 3.0            # px, official 300 m triangular kernel mapped to the 100 m grid


# ----------------------------------------------------------------------------- offsets
def snap_offsets(max_px: float = 2.0) -> np.ndarray:
    """All (dy, dx) with 0 < hypot <= max_px, ordered deterministically."""
    r = int(np.floor(max_px))
    out = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
           if 0.0 < float(np.hypot(dy, dx)) <= max_px + 1e-9]
    return np.asarray(sorted(out), dtype=np.int64)


def separation_disc(min_sep: float = 2.0) -> tuple[np.ndarray, np.ndarray]:
    """Offsets strictly closer than `min_sep` (i.e. the cells a dot would block)."""
    r = int(np.ceil(min_sep))
    off = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
           if float(np.hypot(dy, dx)) < min_sep - 1e-9]
    a = np.asarray(sorted(off), dtype=np.int64).reshape(-1, 2)
    return a[:, 0], a[:, 1]


# ----------------------------------------------------------------------------- fields
def edge_field(band: np.ndarray, valid: np.ndarray, sigma: float = 1.0,
               pct: float = 99.0) -> np.ndarray:
    """Normalised |band| smoothed with a nodata-aware Gaussian; 1.0 == p99 inside `valid`.

    `valid` is the set of cells whose band value is real (finite and not the -3.4e38 nodata
    sentinel).  Normalised convolution keeps the 0.06 % nodata cells from dragging the
    filter to zero and creating false edge minima.
    """
    band = np.asarray(band, np.float64)
    valid = np.asarray(valid, bool)
    v = np.where(valid, np.abs(band), 0.0)
    num = ndimage.gaussian_filter(v, sigma, mode="nearest")
    den = ndimage.gaussian_filter(valid.astype(np.float64), sigma, mode="nearest")
    e = np.where(den > 1e-6, num / np.maximum(den, 1e-9), 0.0)
    ref = float(np.percentile(e[valid], pct)) if valid.any() else 1.0
    e = e / max(ref, 1e-12)
    return np.clip(e, 0.0, 1.0).astype(np.float32)


def consensus(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Geometric mean of two normalised edge fields (both must be strong)."""
    return np.sqrt(np.clip(a, 0, 1).astype(np.float64) * np.clip(b, 0, 1).astype(np.float64)
                   ).astype(np.float32)


# ----------------------------------------------------------------------------- credit
def kernel_credit(mask: np.ndarray, truth: np.ndarray, r: float = KERNEL_R) -> np.ndarray:
    """Per-dot max kernel credit to `truth`: k(d) = max(0, 1 - d/r), d in pixels."""
    dist = ndimage.distance_transform_edt(np.logical_not(np.asarray(truth, bool)))
    ys, xs = np.nonzero(np.asarray(mask, bool))
    d = dist[ys, xs]
    return np.maximum(0.0, 1.0 - d / float(r))


def mean_credit(mask: np.ndarray, truth: np.ndarray) -> float:
    c = kernel_credit(mask, truth)
    return float(c.mean()) if c.size else 0.0


# ----------------------------------------------------------------------------- snap
def snap(dots: np.ndarray, edge: np.ndarray, dist_cat: np.ndarray, foot: np.ndarray,
         max_px: float = 2.0, margin: float = 0.05, min_sep: float = 2.0,
         cat_floor_px: float = 2.0) -> tuple[np.ndarray, dict]:
    """Move dots to the strongest edge cell within `max_px` under three hard rules.

    1. every dot keeps `d_cat > cat_floor_px` (the parent's exclusion) and never ends closer
       to the catalogue than it started;
    2. the final set keeps `min_sep` px between dots (a dot may not be its own blocker);
    3. one dot per cell, count preserved, each dot moves at most once, and only when the
       destination edge beats its own by > `margin`.

    Returns (new_mask, diagnostics).  Deterministic: ties broken by (gain, dot index, offset).
    """
    dots = np.asarray(dots, bool)
    H, W = dots.shape
    ys, xs = np.nonzero(dots)
    n = ys.size
    empty = dict(n_dots=int(n), n_moved=0, pct_moved=0.0, mean_displacement_px=0.0,
                 p95_displacement_px=0.0, max_displacement_px=0.0, count_preserved=True,
                 candidates_considered=0, pairs=(np.empty(0, np.int64),) * 4)
    if n == 0:
        return dots.copy(), empty

    # dynamic neighbour count: how many dots sit strictly closer than `min_sep` to a cell
    oy, ox = separation_disc(min_sep)
    r = int(np.ceil(min_sep))
    kern = np.zeros((2 * r + 1, 2 * r + 1), np.int16)
    kern[oy + r, ox + r] = 1
    counts = ndimage.convolve(dots.astype(np.int16), kern, mode="constant", cval=0)
    occupied = dots.copy()

    offs = snap_offsets(max_px)
    src_e = edge[ys, xs].astype(np.float64)
    src_d = dist_cat[ys, xs].astype(np.float64)

    cand_dot, cand_off, cand_gain, cand_y, cand_x = [], [], [], [], []
    for k, (dy, dx) in enumerate(offs):
        py, px = ys + dy, xs + dx
        ok = (py >= 0) & (py < H) & (px >= 0) & (px < W)
        if not ok.any():
            continue
        idx = np.flatnonzero(ok)
        py2, px2 = py[idx], px[idx]
        gain = edge[py2, px2].astype(np.float64) - src_e[idx]
        keep = (gain > margin) & foot[py2, px2]
        keep &= (dist_cat[py2, px2] > cat_floor_px) & (dist_cat[py2, px2] >= src_d[idx] - 1e-9)
        idx = idx[keep]
        cand_dot.append(idx)
        cand_off.append(np.full(idx.size, k, np.int64))
        cand_gain.append(gain[keep])
        cand_y.append(py2[keep])
        cand_x.append(px2[keep])
    if not cand_dot:
        return dots.copy(), empty

    cand_dot = np.concatenate(cand_dot)
    cand_off = np.concatenate(cand_off)
    cand_gain = np.concatenate(cand_gain)
    cand_y = np.concatenate(cand_y)
    cand_x = np.concatenate(cand_x)
    order = np.lexsort((cand_off, cand_dot, -cand_gain))

    moved = np.zeros(n, bool)
    acc_y, acc_x, acc_disp, acc_idx = [], [], [], []
    dy0, dx0 = cand_y - ys[cand_dot], cand_x - xs[cand_dot]
    self_blocks = (np.abs(dy0) <= r) & (np.abs(dx0) <= r) & (np.hypot(dy0, dx0) < min_sep - 1e-9)
    for i in order:
        if moved[cand_dot[i]]:
            continue
        py, px = cand_y[i], cand_x[i]
        if occupied[py, px]:
            continue
        c = int(counts[py, px]) - int(self_blocks[i])
        if c > 0:
            continue
        di = cand_dot[i]
        sy, sx = ys[di], xs[di]
        occupied[sy, sx] = False
        occupied[py, px] = True
        for ddy, ddx in zip(oy, ox):
            qy, qx = sy + ddy, sx + ddx
            if 0 <= qy < H and 0 <= qx < W:
                counts[qy, qx] -= 1
            qy, qx = py + ddy, px + ddx
            if 0 <= qy < H and 0 <= qx < W:
                counts[qy, qx] += 1
        moved[di] = True
        acc_y.append(py); acc_x.append(px); acc_idx.append(di)
        acc_disp.append(float(np.hypot(py - sy, px - sx)))

    out = dots.copy()
    out[ys[moved], xs[moved]] = False
    out[np.asarray(acc_y, np.int64), np.asarray(acc_x, np.int64)] = True
    disp = np.asarray(acc_disp, np.float64)
    keys = np.asarray(acc_idx, np.int64)
    diag = dict(
        n_dots=int(n), n_moved=int(moved.sum()),
        pct_moved=round(100.0 * float(moved.sum()) / n, 3),
        mean_displacement_px=round(float(disp.mean()), 3) if disp.size else 0.0,
        p95_displacement_px=round(float(np.percentile(disp, 95)), 3) if disp.size else 0.0,
        max_displacement_px=round(float(disp.max()), 3) if disp.size else 0.0,
        count_preserved=bool(int(out.sum()) == n),
        min_sep_px=min_sep, max_px=max_px, margin=margin,
        candidates_considered=int(cand_gain.size),
        pairs=(ys[keys], xs[keys], np.asarray(acc_y, np.int64), np.asarray(acc_x, np.int64)),
    )
    return out, diag


def min_pair_distance(mask: np.ndarray, max_check: int = 200_000) -> float:
    """Nearest-neighbour distance inside a dot set (exact for <= max_check dots)."""
    ys, xs = np.nonzero(np.asarray(mask, bool))
    if ys.size < 2:
        return float("nan")
    from scipy.spatial import cKDTree
    pts = np.column_stack([ys, xs]).astype(np.float64)
    tree = cKDTree(pts)
    d, _ = tree.query(pts, k=2)
    return float(d[:, 1].min())
