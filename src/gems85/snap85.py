"""SNAP axis: move each parent dot a bounded distance onto the strongest scarp/edge response.

Why this axis exists (mechanism, not decoration)
-----------------------------------------------
The parent's ridge was flown at 400 m line spacing (GeoDAWN Area 2, 150-200 m above terrain), so a
mapped lineament's *position* is uncertain by about one kernel radius (3 px = 300 m).  A uniform
unit-mass dot placed at the ridge pixel is only optimal if the ridge pixel is the best estimate of
the fault position.  If a higher-resolution surface (USGS 3DEP lidar scarps, or the upward-continued
TMI edge) locates the same structure better, then moving the dot a pixel or two toward that response
should raise the kernel credit it earns at truth pixels while its unit mass -- and therefore the
false-positive charge at non-truth pixels -- stays exactly the same.

What SNAP can and cannot change
-------------------------------
* count and mass are fixed (each dot is 1.0 before and after);
* a destination must be inside the survey footprint, must be at least as far from the catalogue as
  the dot's own parent position and at least `min_cat_dist` px from it (so the catalogue-mass and
  3-px rules can only improve), and must beat the dot's parent response (`>`, not `>=`);
* final dots keep a minimum separation `min_sep` from every *other* parent dot and from every
  already-placed dot, so the move cannot manufacture duplicate credit by stacking dots;
* dots outside a response field's support cannot move (lidar covers 75.4 % of the footprint, TMI
  covers all of it) -- that is reported, not hidden.

Determinism contract
--------------------
Offsets are enumerated in a fixed order; dots are treated in descending response gain then ascending
raster index; every candidate is tested against a precomputed parent-disc count and an incrementally
marked separation mask.  No RNG, no iteration-order dependence on numpy internals.
"""

from __future__ import annotations

import numpy as np
import rasterio
from scipy import ndimage

from .metric import kernel_dilate

__all__ = [
    "lidar_scarp_response",
    "tmi_edge_response",
    "disc_offsets",
    "parent_disc_count",
    "snap_dots",
    "support_coverage",
    "LIDAR_SCARP_BANDS",
]

# A priori choice of scarp-signature bands (fixed before looking at any score): a fault scarp is a
# step, a convex-up break, and a down-slope-facing escarpment in the 1 m DEM.  The averaging weights
# are not tuned to anything.
LIDAR_SCARP_BANDS = ("step_max", "lapneg_max", "downface_max")


def _read_band(path, band_name: str) -> np.ndarray:
    with rasterio.open(path) as ds:
        names = list(ds.descriptions)
        if band_name not in names:
            raise KeyError(f"{band_name!r} not in {names}")
        return ds.read(names.index(band_name) + 1).astype(np.float32)


def lidar_scarp_response(path) -> tuple[np.ndarray, np.ndarray, dict]:
    """Mean of the three a-priori scarp bands, in [0,1], zero where the lidar coverage is absent."""
    valid = (_read_band(path, "valid") > 0)
    acc = np.zeros(valid.shape, np.float32)
    per_band = {}
    for name in LIDAR_SCARP_BANDS:
        b = _read_band(path, name)
        per_band[name] = dict(mean_on_coverage=float(b[valid].mean()),
                              p99_on_coverage=float(np.percentile(b[valid], 99)))
        acc += b / 255.0
    resp = np.where(valid, acc / float(len(LIDAR_SCARP_BANDS)), 0.0).astype(np.float32)
    info = dict(field="lidar_scarp", bands=list(LIDAR_SCARP_BANDS),
                coverage_fraction=float(valid.mean()), per_band=per_band,
                definition="mean(step_max, lapneg_max, downface_max)/255 masked by band 'valid'")
    return resp, valid, info


def tmi_edge_response(path, *, sigma_px: float = 1.5) -> tuple[np.ndarray, np.ndarray, dict]:
    """|grad TMI_up150| after Gaussian smoothing, scaled by its p99 (clipped to [0,1]).

    The magnetic horizontal gradient is the standard edge detector for contacts and faults, but it
    peaks on the *edge*, which for a fault can be offset from the geomorphic trace -- the mechanism
    card states this confounder explicitly.
    """
    tmi = _read_band(path, "TMI_up150")
    inside = tmi > 0                     # the u8 grid uses 0 as nodata (0.1 % of the footprint)
    smooth = ndimage.gaussian_filter(np.where(inside, tmi, 0.0), sigma_px)
    gy, gx = np.gradient(smooth)
    mag = np.hypot(gy, gx)
    p99 = float(np.percentile(mag[inside], 99)) or 1.0
    resp = np.clip(mag / p99, 0.0, 1.0).astype(np.float32)
    resp[~inside] = 0.0
    # keep a 2-px collar around nodata out of the target set: the gradient there is a survey edge
    resp[ndimage.binary_dilation(~inside, np.ones((5, 5), bool))] = 0.0
    info = dict(field="tmi_edge", band="TMI_up150", sigma_px=sigma_px, p99=p99,
                coverage_fraction=float(inside.mean()),
                definition="|grad(gauss(TMI_up150, sigma=1.5 px))| / p99(in-footprint), nodata collar removed")
    return resp, inside, info


def disc_offsets(radius: float, *, inclusive: bool = False) -> list[tuple[int, int]]:
    """Integer offsets within `radius`, in a fixed (distance, dy, dx) order.

    `inclusive=False` means strictly inside (the packing/separation convention); `inclusive=True`
    means `|offset| <= radius` (the displacement-cap convention: "move <= 1 px" is the 4-neighbours).
    """
    r = int(np.ceil(radius))
    lim = radius * radius
    def keep(d2: float) -> bool:
        return 0.0 < d2 <= lim if inclusive else 0.0 < d2 < lim
    offs = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
            if keep(dy * dy + dx * dx)]
    offs.sort(key=lambda t: (t[0] * t[0] + t[1] * t[1], t[0], t[1]))
    return offs


def _disc_kernel(radius: float) -> np.ndarray:
    """Boolean kernel of every offset strictly inside `radius`, centre included."""
    c = int(np.ceil(radius))
    k = np.zeros((2 * c + 1, 2 * c + 1), np.float32)
    k[c, c] = 1.0
    for dy, dx in disc_offsets(radius):
        k[c + dy, c + dx] = 1.0
    return k


def parent_disc_count(dots: np.ndarray, radius: float) -> np.ndarray:
    """Number of parent dots strictly within `radius` of every pixel (centre counts as one)."""
    return ndimage.convolve(np.asarray(dots, np.float32), _disc_kernel(radius),
                            mode="constant", cval=0.0)


def snap_dots(
    dots: np.ndarray,
    response: np.ndarray,
    dist_cat: np.ndarray,
    footprint: np.ndarray,
    *,
    cap_px: float,
    min_sep: float = 2.0,
    min_cat_dist: float = 3.0,
    dest_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, dict]:
    """Move each dot <= cap_px onto the strongest strictly-better response, subject to the rules.

    `dest_mask` (optional) restricts admissible destinations to a pre-computed set -- the
    "confinement" variants pass a dilation of the parent's own ridge, so the dot can be refined
    within the parent support but cannot jump to a different feature.
    """
    dots = np.asarray(dots, bool)
    resp = np.asarray(response, np.float32)
    H, W = dots.shape
    ys, xs = np.nonzero(dots)
    v0 = resp[ys, xs]
    d0 = dist_cat[ys, xs]

    offs = disc_offsets(cap_px, inclusive=True)
    if not offs:
        raise ValueError("cap_px must be at least 1 px")
    if dest_mask is not None:
        dest_mask = np.asarray(dest_mask, bool)

    # best strictly-better destination for every dot (distance-safe, inside the footprint)
    best_v = v0.copy()
    best_off = np.zeros((ys.size, 2), np.int64)
    dist_ge = np.maximum(min_cat_dist, d0)
    for dy, dx in offs:
        yy, xx = ys + dy, xs + dx
        ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
        v = np.zeros(ys.size, np.float32)
        vc = np.zeros(ys.size, np.float32)
        v[ok] = resp[yy[ok], xx[ok]]
        vc[ok] = dist_cat[yy[ok], xx[ok]]
        foot_ok = np.zeros(ys.size, bool)
        foot_ok[ok] = footprint[yy[ok], xx[ok]]
        better = foot_ok & (vc >= dist_ge) & (v > best_v)
        best_v = np.where(better, v, best_v)
        best_off[better] = (dy, dx)

    gain = best_v - v0
    movers = np.flatnonzero(gain > 0)
    order = movers[np.lexsort((movers, -gain[movers]))]   # gain desc, then raster index asc

    # exact separation bookkeeping: cnt(p) = number of currently *placed* dots strictly within
    # min_sep of p; occ(p) = a placed dot occupies p.  A dot releases its own parent before it is
    # tested and re-places itself afterwards, so "cnt == 0" means ">= min_sep from every other dot"
    # and "occ == False" guarantees that two dots never collapse into one pixel.
    cnt = parent_disc_count(dots, min_sep)
    occ = dots.copy()
    sep_offsets = [(0, 0)] + disc_offsets(min_sep)

    # dots with no strictly-better destination stay where they are; only the others are re-placed
    mover_grid = np.zeros_like(dots)
    mover_grid[ys[movers], xs[movers]] = True
    out = dots & ~mover_grid
    moved = np.zeros(ys.size, bool)
    disp = np.zeros(ys.size, np.float64)
    n_sep_blocked = 0

    def _shift(m, y, x, delta):
        for dy, dx in sep_offsets:
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W:
                m[yy, xx] += delta

    for i in order:
        py, px = ys[i], xs[i]
        dmin = np.maximum(min_cat_dist, d0[i])
        occ[py, px] = False
        _shift(cnt, py, px, -1.0)
        chosen = None
        # candidates in descending response (the offsets are already in a fixed order)
        cand = []
        for dy, dx in offs:
            ny, nx = py + dy, px + dx
            if not (0 <= ny < H and 0 <= nx < W):
                continue
            if not footprint[ny, nx] or dist_cat[ny, nx] < dmin:
                continue
            if dest_mask is not None and not dest_mask[ny, nx]:
                continue
            if resp[ny, nx] <= v0[i]:
                continue
            cand.append((float(resp[ny, nx]), float(np.hypot(dy, dx)), dy, dx, ny, nx))
        cand.sort(key=lambda t: (-t[0], t[1], t[2], t[3]))
        for _v, dd, dy, dx, ny, nx in cand:
            if occ[ny, nx] or cnt[ny, nx] > 0.0:
                n_sep_blocked += 1
                continue
            chosen = (ny, nx, dd)
            break
        if chosen is None:
            ny, nx, dd = py, px, 0.0
        else:
            moved[i] = True
            disp[i] = dd
        out[ny, nx] = True
        occ[ny, nx] = True
        _shift(cnt, ny, nx, +1.0)

    n = ys.size
    info = dict(
        cap_px=cap_px, min_sep=min_sep, min_cat_dist=min_cat_dist,
        confined=dest_mask is not None,
        n_dots=int(n), n_moved=int(moved.sum()),
        pct_moved=round(100.0 * moved.sum() / n, 3),
        n_with_candidate=int(movers.size),
        pct_with_candidate=round(100.0 * movers.size / n, 3),
        n_blocked_by_separation=int(n_sep_blocked),
        mean_displacement_moved_px=round(float(disp[moved].mean()), 4) if moved.any() else 0.0,
        mean_displacement_all_px=round(float(disp.mean()), 4),
        max_displacement_px=round(float(disp.max()), 4),
        mean_response_gain_moved=round(float((best_v - v0)[moved].mean()), 6) if moved.any() else 0.0,
        mean_response_parent=round(float(v0.mean()), 6),
        mean_response_final=round(float(resp[out].mean()), 6),
        n_dots_response_supported=int((v0 > 0).sum()),
    )
    return out, info


def support_coverage(dots: np.ndarray, support: np.ndarray) -> float:
    """Mean kernel credit C(x) the dot set provides at the parent's own support pixels.

    C(x) = max_j k(x - d_j) is exactly the term the metric reads at a truth pixel, so this is a
    *label-free* proxy for how much of the parent's support a dot set still serves.  It uses no
    truth and no score; it answers "did the move keep the backbone covered?".
    """
    c = kernel_dilate(np.asarray(dots, np.float64))
    s = np.asarray(support, bool)
    return float(c[s].mean()) if s.any() else float("nan")
