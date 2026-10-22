"""Lane-H85 candidate surfaces (label-free unless stated).

Stack channel indices follow ``features.CHANNELS``:
 0-18 = official bands 1-19 (band01 mag_anom, band02 rtp, band04 geod_2ndinv idx3,
 band07 geod_shearrate idx6, band08 geod_dilaterate idx7, band12 det_elev idx11,
 band13 iso_grav_anom idx12, band14 tmi idx13, band15 depth_to_base idx14,
 band17 cond_surf idx16), 19 curv_s1, 20 curv_s2, 21-23 ridge_s1..s3,
 24 relief5, 25 tophat2, 26 tmi_edge, 27 rtp_edge, 28 grav_edge, 29 cond_edge,
 30 depth_grad, 31 coherence_s2, 32 strike_cos, 33 strike_sin, 34 footprint.
External uint8 stacks are appended after index 34 by the experiment runner
(lidar 12, rad 4, extensions 4) — the supervised model consumes them; the
label-free surfaces below use only the 35-channel stack.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def robust_unit(a: np.ndarray, foot: np.ndarray, pct: float = 99.5) -> np.ndarray:
    """Median/IQR robust rescale to [0, 1] inside the footprint (label-free)."""
    out = np.zeros(a.shape, dtype=np.float32)
    v = foot & np.isfinite(a)
    if not v.any():
        return out
    vals = a[v]
    med = float(np.median(vals))
    q25, q75 = np.percentile(vals, [25.0, 75.0])
    scale = max(float(q75 - q25) / 1.349, 1e-9)
    z = (a - med) / scale
    hi = max(float(np.percentile(z[v], pct)), 1e-6)
    out[v] = np.clip(z[v] / hi, 0.0, 1.0)
    return out


def line_response(a: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Both-polarity Hessian line response: -(eigenvalue of least |.|) with ridge sign.

    Positive on a curvilinear ridge OR valley of either polarity.
    """
    axx = ndimage.gaussian_filter(a, sigma, order=(0, 2), mode="nearest")
    ayy = ndimage.gaussian_filter(a, sigma, order=(2, 0), mode="nearest")
    axy = ndimage.gaussian_filter(a, sigma, order=(1, 1), mode="nearest")
    tmp = np.sqrt(np.maximum(((axx - ayy) * 0.5) ** 2 + axy ** 2, 0.0))
    l1 = (axx + ayy) * 0.5 + tmp
    l2 = (axx + ayy) * 0.5 - tmp
    small = np.where(np.abs(l1) >= np.abs(l2), l2, l1)
    return (-small).astype(np.float32)


def structure_orientation(a: np.ndarray, sigma: float = 1.5):
    gx = ndimage.gaussian_filter(a, sigma, order=(0, 1), mode="nearest")
    gy = ndimage.gaussian_filter(a, sigma, order=(1, 0), mode="nearest")
    jxx = ndimage.gaussian_filter(gx * gx, sigma, mode="nearest")
    jyy = ndimage.gaussian_filter(gy * gy, sigma, mode="nearest")
    jxy = ndimage.gaussian_filter(gx * gy, sigma, mode="nearest")
    tr = jxx + jyy + 1e-12
    coh = np.sqrt(np.maximum(((jxx - jyy) * 0.5) ** 2 + jxy ** 2, 0.0)) / tr
    theta = 0.5 * np.arctan2(2 * jxy, (jxx - jyy) + 1e-12)
    return theta.astype(np.float32), coh.astype(np.float32)


def surface_orientation_consensus(stack: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """H85-B: multi-physics orientation order parameter x OR-fused line response.

    Physics used: det_elev (idx11), rtp (idx1), tmi (idx13), iso_grav (idx12),
    cond_surf (idx16).  A pixel scores only if the independent fields agree on a
    strike (order parameter R = |mean w*e^{2i*theta}|) AND at least one responds.
    Non-fault mimic: a lithologic contact train / shoreline / road grid that is
    straight in several fields at once.
    """
    idxs = [11, 1, 13, 12, 16]
    wsum = np.zeros(foot.shape, np.float32)
    re = np.zeros(foot.shape, np.float32)
    im = np.zeros(foot.shape, np.float32)
    or_fuse = np.zeros(foot.shape, np.float32)
    for i in idxs:
        a = np.asarray(stack[:, :, i], dtype=np.float32)
        lr = robust_unit(line_response(a), foot)
        theta, coh = structure_orientation(a)
        w = lr * (0.25 + 0.75 * coh)
        wsum += w
        re += w * np.cos(2 * theta)
        im += w * np.sin(2 * theta)
        or_fuse = np.maximum(or_fuse, lr)
        del a, lr, theta, coh
    R = np.sqrt(re * re + im * im) / np.maximum(wsum, 1e-9)
    return (R * or_fuse * foot).astype(np.float32)


def surface_strain_gated(stack: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """H85-C: strain-gated lineament (this lane's genuinely new surface).

    Layers: geod_dilaterate (idx7), geod_2ndinv (idx3), geod_shearrate (idx6)
    form a *gate* for currently-extending crust; det_elev (idx11) and rtp (idx1)
    Hessian line responses supply the geometry.  Rationale: a fault that is
    missing from the catalogue but is *actively extending* should sit where
    geodetic dilatation is locally high AND a line exists; a fossil lineament in
    non-extending crust is de-prioritised.  The supplied strain bands are smooth
    (they cannot locate a fault alone) — they only re-weight line geometry.
    Non-fault mimic: basin-range topographic lineaments inside a broad
    dilatation high (the gate is smooth, so it can promote a whole range front).
    """
    dem = np.asarray(stack[:, :, 11], dtype=np.float32)
    rtp = np.asarray(stack[:, :, 1], dtype=np.float32)
    line = np.maximum(robust_unit(line_response(dem), foot),
                      robust_unit(line_response(rtp), foot))
    dil = robust_unit(np.clip(np.asarray(stack[:, :, 7], dtype=np.float32), 0, None), foot)
    inv = robust_unit(np.asarray(stack[:, :, 3], dtype=np.float32), foot)
    shr = robust_unit(np.asarray(stack[:, :, 6], dtype=np.float32), foot)
    gate = 0.30 + 0.70 * (0.5 * dil + 0.3 * inv + 0.2 * shr)
    return (line * gate * foot).astype(np.float32)


def top_n_support(field: np.ndarray, allowed: np.ndarray, n: int) -> np.ndarray:
    """Boolean support = the n highest-field pixels inside ``allowed``."""
    f = np.where(allowed, field, -np.inf).astype(np.float32)
    flat = f.ravel()
    if n >= int(allowed.sum()):
        return allowed.copy()
    idx = np.argpartition(flat, -n)[-n:]
    out = np.zeros(flat.size, bool)
    out[idx] = True
    return out.reshape(f.shape)
