"""GEO-Pb: a multivariate *juxtaposition* detector for concealed faults.

-------------------------------------------------------------------------------------------
THE LANE (one paragraph, fixed before implementation -- see registry/preregistration.json)
-------------------------------------------------------------------------------------------
Every fault detector in the sibling GEMSDOE repositories is a **derivative** operator: Sato /
Frangi / Hessian ridges, tilt angle, horizontal gradient, Euler deconvolution, worms, gradient
coherence.  A derivative asks "is this field changing fast here?".  A fault, physically, is a
**juxtaposition**: it puts two different geological domains side by side.  The right question is
therefore the two-sample one -- "do the rocks on the two sides of this line have different joint
geophysical signatures?" -- which is the question an expert mapper actually answers, and which
fires even when no single band has a large gradient.  GEO-Pb implements that test directly: at
each pixel and each of eight candidate strike orientations it forms the vector of *offset
differences* of a covariance-whitened multi-physics stack across the candidate line (a windowed
Hotelling-style step statistic, the geophysical analogue of the Martin-Fowlkes-Malik half-disc
Pb boundary detector used in computer vision), requires **at least two of three independent
physics domains** -- potential-field/subsurface, airborne radiometric, topographic -- to agree by
taking the median of the three domain statistics, and then multiplies by an **along-strike
persistence** term so that only evidence that continues in a straight line for >= 1.5 km
survives.  A fault is planar and long; an alluvial-fan margin is lobate, a playa edge is closed,
and a single-band processing seam fails the two-of-three domain vote.

Why this should find faults the USGS/INGENIOUS catalogue lacks: that catalogue is dominated by
Quaternary-active structures mapped from *surface* evidence (scarps, offset landforms).  A fault
concealed beneath Holocene alluvium with no scarp, but which still juxtaposes different basement
susceptibility, different basin-fill thickness, and different surface geochemistry, produces a
small change in every band and a large change in the *joint* 10-vector.  That is exactly the
class a scarp-first catalogue under-samples and exactly the class a derivative-based detector
under-weights.

Named non-fault processes that can mimic the signature (declared in advance, measured in
scripts/run_experiments.py): (1) depositional contacts -- distal alluvial-fan margins and playa
shorelines (Lake Lahontan highstand), mitigated by the straightness term and the two-of-three
vote; (2) aeromagnetic/radiometric acquisition seams at the flight-line azimuth, mitigated by the
two-of-three vote and measured via the response azimuth histogram; (3) erosional volcanic
mesa/flow margins, which are straight and multi-domain and are *not* fully separable -- declared
as the principal irreducible confounder.
-------------------------------------------------------------------------------------------
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import grid

# Eight candidate strike orientations, expressed as integer *normal* offsets at radius ~3 px.
# Each (dy, dx) is the direction across which the two half-windows are compared; the trace runs
# perpendicular to it.  Offsets are integers so the operator is an exact array shift.
NORMALS_R3 = [(3, 0), (3, 1), (2, 2), (1, 3), (0, 3), (-1, 3), (-2, 2), (-3, 1)]
NORMALS_R6 = [(6, 0), (6, 2), (4, 4), (2, 6), (0, 6), (-2, 6), (-4, 4), (-6, 2)]

# Three independent physics domains.  (source, key) where source is "feat" (training_features.tif
# band name), "rad" (geodawn_rad_u8 band index) or "lidar" (lidar_scarp_features_u8 band index).
DOMAINS: dict[str, list[tuple[str, object]]] = {
    "potential_field": [("feat", "rtp"), ("feat", "iso_grav_anom"),
                        ("feat", "cond_surf"), ("feat", "depth_to_base_surf")],
    "radiometric":     [("rad", 1), ("rad", 2), ("rad", 4)],           # K, Th, TC
    "topographic":     [("feat", "det_elev"), ("feat", "det_elev_slope"), ("lidar", 3)],  # step_max
}


# ------------------------------------------------------------------ helpers


def shift(a: np.ndarray, dy: int, dx: int, fill: float = 0.0) -> np.ndarray:
    """Exact integer array shift; out-of-frame filled with `fill`."""
    out = np.full_like(a, fill)
    h, w = a.shape
    ys_src = slice(max(0, -dy), h - max(0, dy))
    ys_dst = slice(max(0, dy), h - max(0, -dy))
    xs_src = slice(max(0, -dx), w - max(0, dx))
    xs_dst = slice(max(0, dx), w - max(0, -dx))
    out[ys_dst, xs_dst] = a[ys_src, xs_src]
    return out


def robust_z(a: np.ndarray, mask: np.ndarray, clip: float = 5.0) -> np.ndarray:
    """(x - median)/(IQR/1.349) on `mask`, NaN -> 0, clipped. float32."""
    v = a[mask]
    v = v[np.isfinite(v)]
    if v.size > 2_000_000:
        v = v[:: v.size // 2_000_000 + 1]
    med = float(np.median(v))
    q1, q3 = np.percentile(v, [25, 75])
    scale = float(q3 - q1) / 1.349 or 1.0
    z = (a - med) / scale
    z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    np.clip(z, -clip, clip, out=z)
    return z


def load_domain_stack(domain: str, mask: np.ndarray, sigma: float) -> np.ndarray:
    """Smoothed, robustly-standardised stack for one physics domain: (n_band, H, W) float32."""
    import rasterio
    out = []
    for src, key in DOMAINS[domain]:
        if src == "feat":
            a = grid.read_feature(key)
        elif src == "rad":
            with rasterio.open(grid.DATA / "external" / "geodawn_rad_u8.tif") as ds:
                grid.assert_grid(ds, "geodawn_rad_u8")
                a = ds.read(int(key)).astype(np.float32)
            a[a == 0] = np.nan                       # file nodata is 0
        elif src == "lidar":
            with rasterio.open(grid.DATA / "external" / "lidar_scarp_features_u8.tif") as ds:
                grid.assert_grid(ds, "lidar_scarp_features_u8")
                a = ds.read(int(key)).astype(np.float32)
            a[a == 0] = np.nan
        else:
            raise ValueError(src)
        z = robust_z(a, mask)
        if sigma > 0:
            z = ndi.gaussian_filter(z, sigma, mode="nearest").astype(np.float32)
        out.append(z)
        del a
    return np.stack(out)


def whiten(stack: np.ndarray, normals, mask: np.ndarray, seed: int = 11) -> np.ndarray:
    """Return A @ stack where A whitens the covariance of the *step vectors* across `normals`.

    The step operator is linear, so whitening the bands with A is identical to whitening the
    steps -- but costs one pass instead of one per orientation.
    """
    nb = stack.shape[0]
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(mask)
    sel = rng.choice(ys.size, min(120_000, ys.size), replace=False)
    ys, xs = ys[sel], xs[sel]
    H, W = stack.shape[1:]
    deltas = []
    for dy, dx in normals:
        yp = np.clip(ys + dy, 0, H - 1); xp = np.clip(xs + dx, 0, W - 1)
        ym = np.clip(ys - dy, 0, H - 1); xm = np.clip(xs - dx, 0, W - 1)
        deltas.append(stack[:, yp, xp] - stack[:, ym, xm])
    D = np.concatenate(deltas, axis=1)               # (nb, n_samples*n_orient)
    cov = np.cov(D.astype(np.float64)) + 1e-6 * np.eye(nb)
    L = np.linalg.cholesky(cov)
    A = np.linalg.inv(L).astype(np.float32)
    return np.einsum("ij,jhw->ihw", A, stack, optimize=True).astype(np.float32)


def line_mean(a: np.ndarray, dy: int, dx: int, length_px: float) -> np.ndarray:
    """Mean of `a` along the straight line through each pixel in direction (dy,dx).

    The direction is normalised and sampled at unit steps (a digital line), so `length_px` is
    a true length in pixels regardless of the orientation.
    """
    n = float(np.hypot(dy, dx))
    uy, ux = dy / n, dx / n
    half = int(round(length_px / 2.0))
    acc = np.zeros_like(a)
    cnt = 0
    for t in range(-half, half + 1):
        sy, sx = int(round(t * uy)), int(round(t * ux))
        acc += shift(a, sy, sx)
        cnt += 1
    acc /= cnt
    return acc


# ------------------------------------------------------------------ the detector


def geopb_surface(
    *,
    sigma: float = 1.5,
    normals=tuple(NORMALS_R3),
    persistence_px: float = 15.0,
    footprint: np.ndarray | None = None,
    return_parts: bool = False,
):
    """The GEO-Pb field.

    Returns a float32 array, 0 outside the footprint, un-normalised (higher = stronger
    multi-domain straight juxtaposition).  No catalogue information is used anywhere in this
    function -- which is why it cannot leak the holdout answer.
    """
    fp = grid.footprint() if footprint is None else footprint
    names = list(DOMAINS)
    whitened = {d: whiten(load_domain_stack(d, fp, sigma), normals, fp) for d in names}

    best = np.zeros(fp.shape, dtype=np.float32)
    best_axis = np.zeros(fp.shape, dtype=np.int8)
    for j, (dy, dx) in enumerate(normals):
        # per-domain whitened step magnitude
        dom_resp = []
        for d in names:
            Y = whitened[d]
            s = np.zeros(fp.shape, dtype=np.float32)
            for k in range(Y.shape[0]):
                u = shift(Y[k], dy, dx) - shift(Y[k], -dy, -dx)
                s += u * u
            dom_resp.append(np.sqrt(s, out=s))
        # two-of-three vote == median of the three domain statistics
        r = np.median(np.stack(dom_resp), axis=0).astype(np.float32)
        del dom_resp
        # along-strike persistence: the trace runs perpendicular to the normal
        p = line_mean(r, -dx, dy, persistence_px)
        resp = np.sqrt(r * p, dtype=np.float32)      # geometric mean: local AND persistent
        upd = resp > best
        best[upd] = resp[upd]
        best_axis[upd] = j
        del r, p, resp
    best[~fp] = 0.0
    if return_parts:
        return best, best_axis
    return best


# ------------------------------------------------------------------ crest extraction


def _unit_steps(normals) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """For each normal, the 1-step and 2-step integer approximations of its unit vector."""
    out = []
    for dy, dx in normals:
        n = float(np.hypot(dy, dx))
        u1 = (int(round(dy / n)), int(round(dx / n)))
        u2 = (int(round(2 * dy / n)), int(round(2 * dx / n)))
        out.append((u1, u2))
    return out


def crest(field: np.ndarray, axis: np.ndarray, normals=tuple(NORMALS_R3)) -> np.ndarray:
    """Non-maximum suppression across each pixel's own best normal.

    GEO-Pb's offset-difference response is a *band* several pixels wide, so an un-thinned
    emission spends dots on the shoulders of a boundary instead of on it.  Suppressing every
    pixel that is not a local maximum along its own normal collapses the band onto the
    boundary itself, which is where the metric's 300 m kernel pays.
    """
    keep = np.ones(field.shape, dtype=bool)
    for j, (u1, u2) in enumerate(_unit_steps(normals)):
        sel = axis == j
        if not sel.any():
            continue
        for (sy, sx) in (u1, u2):
            if sy == 0 and sx == 0:
                continue
            a = shift(field, sy, sx)
            b = shift(field, -sy, -sx)
            keep &= ~(sel & ((field < a) | (field < b)))
    return (field * keep).astype(np.float32)
