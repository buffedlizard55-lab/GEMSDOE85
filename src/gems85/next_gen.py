"""Next-generation fault-discovery detectors for GEMSDOE85 (Session 6: H85-S6-1, H85-S6-2, H85-S6-3).

Directly executes the prioritized next steps documented in README.md Sec.5 and
knowledge/geothermal-vent-discovery.md Sec.4, and fixes two physics/geometry defects
discovered in the earlier GEO-Pb and supervised implementations:

1. IR-85-006 (GEO-Pb split-halo defect):
   In src/gems85/geopb.py, DOMAINS["topographic"] applied the two-sample across-line step
   difference `Y(x + d*n) - Y(x - d*n)` (d = 3 px = 300 m) to `det_elev_slope` (band 19)
   and 1 m LiDAR `step_max` (lidar band 3).  Both are non-negative edge/scarp magnitudes
   that peak ON the fault trace (x = 0) and are near zero on both sides.  Differencing a
   positive impulse across +/-3 px gives ZERO on the fault trace (x = 0) and two false
   peaks at x = +/-3 px (+/-300 m, where the 300 m triangular kernel k(300 m) = 0).
   Fix: separate STATE variables (bulk block properties differenced across +/-d*n) from
   INTERFACE variables (on-fault scarp/gradient properties evaluated directly at x = 0).

2. IR-85-007 (2D ribbon blob-clumping & missing near-field negatives in supervised emission):
   In scripts/run_supervised.py, negatives were sampled only at >10 px from visible faults,
   so the model predicted a 20-px-wide ribbon across range fronts, and `poisson_thin` packed
   dots in 2D across that ribbon (4-10 px off-fault) rather than along 1D fault centerlines.
   Fix: (a) include near-field shoulder negatives (4..12 px from visible faults) alongside
   regional negatives so the classifier resolves the 1-px fault trace from the piedmont
   shoulder; and (b) convolve predicted probabilities with the official 300 m triangular
   kernel `k(d) = (1 - d/3)+` to form exact expected kernel credit `C(x) = (P * k)(x)`, then
   apply Hessian-normal non-maximum suppression to extract the 1-px axial centerline crest.
"""

from __future__ import annotations

import numpy as np
import rasterio
from scipy import ndimage as ndi

from . import geopb, grid, metric

# 16 candidate strike orientations (normal offsets at radius ~3 px, upgrading from 8 strikes
# per README.md Sec.5 Next Step #2, while retiring the null 1.5 km persistence blur).
NORMALS_16_R3 = [
    (3, 0), (3, 1), (3, 2), (2, 2),
    (2, 3), (1, 3), (0, 3), (-1, 3),
    (-2, 3), (-2, 2), (-3, 2), (-3, 1),
    (4, 1), (1, 4), (-1, 4), (-4, 1),
]

# State domains ONLY (bulk block properties that jump across a fault; never edge magnitudes).
STATE_DOMAINS: dict[str, list[tuple[str, object]]] = {
    "potential_subsurface": [
        ("feat", "rtp"),
        ("feat", "tmi"),
        ("feat", "iso_grav_anom"),
        ("feat", "depth_to_base_surf"),
        ("feat", "cond_surf"),
        ("ext", 4),  # TMI_up150
    ],
    "radiometric_geochem": [
        ("rad", 1),  # K
        ("rad", 2),  # Th
        ("rad", 3),  # U
        ("ext", 1),  # ThK
        ("ext", 2),  # UK
        ("ext", 3),  # UTh
    ],
    "elevation_block": [
        ("feat", "det_elev"),
    ],
}


def _read_ext_u8(fname: str, band: int) -> np.ndarray:
    with rasterio.open(grid.DATA / "external" / fname) as ds:
        grid.assert_grid(ds, fname)
        a = ds.read(int(band)).astype(np.float32)
    a[a == 0] = np.nan
    return a


def _load_state_domain(domain: str, mask: np.ndarray, sigma: float = 1.2) -> np.ndarray:
    out = []
    for src, key in STATE_DOMAINS[domain]:
        if src == "feat":
            a = grid.read_feature(key)
        elif src == "rad":
            a = _read_ext_u8("geodawn_rad_u8.tif", int(key))
        elif src == "ext":
            a = _read_ext_u8("geodawn_extensions_u8.tif", int(key))
        else:
            raise ValueError(src)
        z = geopb.robust_z(a, mask)
        if sigma > 0:
            z = ndi.gaussian_filter(z, sigma, mode="nearest").astype(np.float32)
        out.append(z)
        del a
    return np.stack(out)


def _positive_unit(a: np.ndarray, mask: np.ndarray, q_lo: float = 50.0, q_hi: float = 99.2) -> np.ndarray:
    """Map a physical response into [0, 1] over `mask`, clipping at [q_lo, q_hi] percentiles."""
    v = a[mask & np.isfinite(a)]
    if v.size == 0:
        return np.zeros_like(a, dtype=np.float32)
    if v.size > 1_500_000:
        v = v[:: v.size // 1_500_000 + 1]
    lo, hi = np.percentile(v, [q_lo, q_hi])
    scale = float(hi - lo) or 1.0
    out = np.clip((np.nan_to_num(a, nan=lo) - lo) / scale, 0.0, 1.0).astype(np.float32)
    out[~mask] = 0.0
    return out


def geothermal_upflow_prior(fp: np.ndarray) -> np.ndarray:
    """Catalogue-free geothermal upflow proximity field from GDR 1391 well/spring chemistry.

    Implements knowledge/geothermal-vent-discovery.md Sec.4:
      - Uses ONLY physical site coordinates (`row`, `col`), `thermalclass`, `temp_c`, and
        `geothermcat_c`.  The `dist_known_fault_px` column in the CSV is NEVER read.
      - Combines a 1.5 km (15 px) exponential kernel around all 1,839 Hot/Warm sites
        (where measured fault enrichment is 1.50x) with a 2.5 km (25 px) kernel around
        high-temperature geothermometer upflow sites (temp_c >= 50 C or geothermcat_c >= 120 C).
    """
    import pandas as pd  # Optional table dependency; synthetic geometry tests do not need it.

    ws = pd.read_csv(
        grid.DATA / "external" / "gdr_wellspring_in_footprint.csv",
        usecols=["row", "col", "thermalclass", "temp_c", "geothermcat_c"],
    )
    sites = ws.drop_duplicates(subset=["row", "col"])
    H, W = fp.shape

    hot_mask = np.zeros((H, W), dtype=bool)
    hi_mask = np.zeros((H, W), dtype=bool)

    tc = sites["thermalclass"].astype(str)
    is_hot = tc.str.contains("Hot|Warm", case=False, na=False) | (sites["temp_c"].fillna(0) >= 30.0)
    is_hi = (sites["temp_c"].fillna(0) >= 50.0) | (sites["geothermcat_c"].fillna(0) >= 120.0)

    r_hot = np.clip(sites.loc[is_hot, "row"].to_numpy(int), 0, H - 1)
    c_hot = np.clip(sites.loc[is_hot, "col"].to_numpy(int), 0, W - 1)
    hot_mask[r_hot, c_hot] = True

    r_hi = np.clip(sites.loc[is_hi, "row"].to_numpy(int), 0, H - 1)
    c_hi = np.clip(sites.loc[is_hi, "col"].to_numpy(int), 0, W - 1)
    hi_mask[r_hi, c_hi] = True

    d_hot = ndi.distance_transform_edt(~hot_mask).astype(np.float32)
    d_hi = ndi.distance_transform_edt(~hi_mask).astype(np.float32)

    g = 0.65 * np.exp(-d_hot / 15.0) + 0.35 * np.exp(-d_hi / 25.0)
    g[~fp] = 0.0
    return g.astype(np.float32)


def expected_kernel_credit(p: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Exact expected 300 m triangular-kernel credit: C(x) = sum_{|d|<=3} p(x+d) * (1 - |d|/3)."""
    f = np.where(fp & np.isfinite(p), np.clip(p, 0.0, None), 0.0).astype(np.float32)
    out = np.zeros_like(f, dtype=np.float32)
    for dy, dx, k in metric.OFFSETS:
        if k <= 0.0:
            continue
        out += geopb.shift(f, -dy, -dx, fill=0.0) * np.float32(k)
    out[~fp] = 0.0
    return out


def hessian_normal_crest(field: np.ndarray, fp: np.ndarray, sigma: float = 1.2,
                         keep_floor: float = 0.15) -> np.ndarray:
    """Extract the 1-px axial centerline crest of a 2D belief field via Hessian-normal NMS.

    At every pixel, computes the direction of strongest negative curvature (across the ridge)
    from the smoothed Hessian, quantizes it to 8 integer normal directions, and suppresses
    shoulder pixels that are smaller than their +/-1 px or +/-2 px across-ridge neighbours.
    """
    sm = ndi.gaussian_filter(field.astype(np.float32), sigma, mode="nearest")
    gyy = ndi.gaussian_filter(sm, 0, order=(2, 0), mode="nearest")
    gxx = ndi.gaussian_filter(sm, 0, order=(0, 2), mode="nearest")
    gxy = ndi.gaussian_filter(sm, 0, order=(1, 1), mode="nearest")

    # Normal angle of the most-negative Hessian eigenvalue (perpendicular to the ridge axis)
    theta = 0.5 * np.arctan2(2.0 * gxy, gxx - gyy)
    # Map angle in [-pi/2, pi/2] to 8 integer normal sectors
    sector = (np.round((theta + np.pi / 2.0) / (np.pi / 8.0)).astype(np.int32)) % 8
    unit_normals = [
        (1, 0), (1, 1), (1, 1), (0, 1),
        (0, 1), (-1, 1), (-1, 1), (1, 0),
    ]
    # Exact 8-direction quantized unit & 2-step normals
    dirs1 = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    dirs2 = [(2, 0), (2, 2), (0, 2), (-2, 2), (-2, 0), (-2, -2), (0, -2), (2, -2)]

    keep = np.ones(field.shape, dtype=bool)
    for s in range(8):
        sel = (sector == s) & fp
        if not sel.any():
            continue
        dy1, dx1 = dirs1[s]
        dy2, dx2 = dirs2[s]
        a1 = geopb.shift(sm, dy1, dx1)
        b1 = geopb.shift(sm, -dy1, -dx1)
        a2 = geopb.shift(sm, dy2, dx2)
        b2 = geopb.shift(sm, -dy2, -dx2)
        is_max1 = (sm >= a1) & (sm >= b1)
        is_max2 = (sm >= a2) & (sm >= b2)
        keep &= ~(sel & ~(is_max1 & is_max2))

    # Retain the sharp 1-px crest plus a small fraction of the smooth field so ties break by
    # expected kernel credit rather than arbitrary raster order.
    out = np.where(keep, field, field * keep_floor).astype(np.float32)
    out[~fp] = 0.0
    return out


def geopb_v2_surface(fp: np.ndarray | None = None, *, lambda_thermal: float = 0.35) -> np.ndarray:
    """H85-S6-1: State-vs-Interface Corrected 16-Strike GEO-Pb + Piedmont Scarp + Geothermal Prior.

    100% catalogue-free (never reads labels.tif or existing_faults.tif).
    """
    fp = grid.footprint() if fp is None else fp

    # 1. State juxtaposition across 16 strikes (ONLY true state variables, fixing IR-85-006)
    whitened = {
        d: geopb.whiten(_load_state_domain(d, fp, sigma=1.2), NORMALS_16_R3, fp)
        for d in STATE_DOMAINS
    }
    jux_best = np.zeros(fp.shape, dtype=np.float32)
    for dy, dx in NORMALS_16_R3:
        dom_s = []
        for d, Y in whitened.items():
            s = np.zeros(fp.shape, dtype=np.float32)
            for k in range(Y.shape[0]):
                u = geopb.shift(Y[k], dy, dx) - geopb.shift(Y[k], -dy, -dx)
                s += u * u
            dom_s.append(np.sqrt(s, out=s) / np.sqrt(float(Y.shape[0])))
        # Weighted combination across the 3 state domains (median + mean for robustness)
        stack_d = np.stack(dom_s, axis=0)
        resp = 0.6 * np.median(stack_d, axis=0) + 0.4 * np.mean(stack_d, axis=0)
        np.maximum(jux_best, resp.astype(np.float32), out=jux_best)
    del whitened
    jux_norm = _positive_unit(jux_best, fp, q_lo=30.0, q_hi=99.2)

    # 2. On-line fault-interface score (evaluated AT (y,x), never differenced across +/-3 px)
    lappos = _positive_unit(_read_ext_u8("lidar_scarp_features_u8.tif", 5), fp, 40, 99.2)
    lapneg = _positive_unit(_read_ext_u8("lidar_scarp_features_u8.tif", 4), fp, 40, 99.2)
    step_m = _positive_unit(_read_ext_u8("lidar_scarp_features_u8.tif", 3), fp, 40, 99.2)
    ex_m = _positive_unit(_read_ext_u8("lidar_scarp_features_u8.tif", 1), fp, 40, 99.2)
    l_rel = _positive_unit(_read_ext_u8("lidar_scarp_features_u8.tif", 9), fp, 40, 99.2)
    lidar_if = 0.25 * lappos + 0.22 * lapneg + 0.23 * step_m + 0.15 * ex_m + 0.15 * l_rel

    slope = _positive_unit(grid.read_feature("det_elev_slope"), fp, 35, 99.0)
    neg_tc = _positive_unit(-grid.read_feature("tc"), fp, 40, 99.0)
    grav_sl = _positive_unit(grid.read_feature("iso_grav_anom_slope"), fp, 35, 99.0)
    tmi_hg = _positive_unit(grid.read_feature("tmi_hg"), fp, 35, 99.0)
    strain = 0.5 * _positive_unit(grid.read_feature("geod_2ndinv"), fp, 20, 99.0) + \
             0.5 * _positive_unit(grid.read_feature("geod_shearrate"), fp, 20, 99.0)

    interface = 0.45 * lidar_if + 0.20 * slope + 0.15 * neg_tc + 0.10 * grav_sl + 0.10 * tmi_hg

    # 3. Volcanic mesa / flat plateau suppressor (README.md Sec.5 Next Step #5)
    elev = geopb.robust_z(grid.read_feature("det_elev"), fp)
    rtp_hg = geopb.robust_z(grid.read_feature("tmi_hg"), fp)
    mesa_penalty = np.where((elev > 1.3) & (rtp_hg > 1.5) & (grav_sl < 0.25), 0.65, 1.0).astype(np.float32)

    # 4. Combine state juxtaposition + on-line interface + tectonic strain gate + geothermal prior
    g_therm = geothermal_upflow_prior(fp)
    combined = (0.35 * jux_norm + 0.45 * interface + 0.20 * np.sqrt(jux_norm * interface))
    combined = combined * (0.75 + 0.25 * strain) * mesa_penalty * (1.0 + lambda_thermal * g_therm)
    combined[~fp] = 0.0

    # 5. Expected 300 m kernel credit + Hessian-normal 1-px crest extraction
    ecredit = expected_kernel_credit(combined, fp)
    return hessian_normal_crest(ecredit, fp, sigma=1.1, keep_floor=0.05)


def mag_continuation_alteration_surface(fp: np.ndarray | None = None) -> np.ndarray:
    """H85-S6-3: Shallow-vs-Deep Magnetic Continuation Residual + Hydrothermal K/U/Th Alteration.

    Targets intrabasin concealed faults where hydrothermal fluid flow destroys magnetite
    (negative vertical gradient / shallow continuation residual) and alters K/U/Th ratios
    along conductive clay-altered fault planes.  100% catalogue-free.
    """
    fp = grid.footprint() if fp is None else fp

    z_tmi = geopb.robust_z(grid.read_feature("tmi"), fp)
    z_up150 = geopb.robust_z(_read_ext_u8("geodawn_extensions_u8.tif", 4), fp)
    # Shallow magnetic source residual (attenuated by 150 m upward continuation)
    shallow_res = np.abs(z_tmi - z_up150)
    shallow_grad = np.hypot(
        ndi.gaussian_filter(z_tmi - z_up150, 1.5, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(z_tmi - z_up150, 1.5, order=(0, 1), mode="nearest"),
    )
    mag_destruct = _positive_unit(-grid.read_feature("tmi_vg"), fp, 45, 99.2)
    tmi_hg = _positive_unit(grid.read_feature("tmi_hg"), fp, 40, 99.2)
    mag_score = 0.35 * _positive_unit(shallow_grad, fp, 40, 99.2) + \
                0.25 * _positive_unit(shallow_res, fp, 40, 99.2) + \
                0.20 * mag_destruct + 0.20 * tmi_hg

    # Radiometric hydrothermal mobility (U/Th, U/K enrichment + piedmont K/TC contrast)
    uk = _positive_unit(_read_ext_u8("geodawn_extensions_u8.tif", 2), fp, 40, 99.0)
    uth = _positive_unit(_read_ext_u8("geodawn_extensions_u8.tif", 3), fp, 40, 99.0)
    low_k = _positive_unit(-geopb.robust_z(_read_ext_u8("geodawn_rad_u8.tif", 1), fp), fp, 40, 99.0)
    rad_score = 0.40 * uth + 0.35 * uk + 0.25 * low_k

    # Subsurface conductivity + gravity step + piedmont scarp corroboration
    cond_z = geopb.robust_z(grid.read_feature("cond_surf"), fp)
    cond_step = _positive_unit(np.hypot(
        ndi.gaussian_filter(cond_z, 2.0, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(cond_z, 2.0, order=(0, 1), mode="nearest"),
    ), fp, 40, 99.0)
    grav_sl = _positive_unit(grid.read_feature("iso_grav_anom_slope"), fp, 40, 99.0)
    scarp = 0.5 * _positive_unit(_read_ext_u8("lidar_scarp_features_u8.tif", 5), fp, 40, 99.2) + \
            0.5 * _positive_unit(grid.read_feature("det_elev_slope"), fp, 40, 99.0)

    raw = (0.35 * mag_score + 0.25 * rad_score + 0.15 * cond_step + 0.10 * grav_sl + 0.15 * scarp)
    raw[~fp] = 0.0
    ecredit = expected_kernel_credit(raw, fp)
    return hessian_normal_crest(ecredit, fp, sigma=1.2, keep_floor=0.05)


def crest_1step(field: np.ndarray, fp: np.ndarray, sigma: float = 1.0,
                keep_floor: float = 0.04) -> np.ndarray:
    """1-step Hessian-normal axial crest extraction.

    Suppresses shoulder pixels that are smaller than either of their +/-1 px neighbours along
    the direction of strongest negative Hessian curvature (perpendicular to the fault axis),
    collapsing 2D probability ribbons onto 1-px fault centerlines without fragmenting step-over
    segments.
    """
    sm = ndi.gaussian_filter(field.astype(np.float32), sigma, mode="nearest")
    gyy = ndi.gaussian_filter(sm, 0, order=(2, 0), mode="nearest")
    gxx = ndi.gaussian_filter(sm, 0, order=(0, 2), mode="nearest")
    gxy = ndi.gaussian_filter(sm, 0, order=(1, 1), mode="nearest")
    theta = 0.5 * np.arctan2(2.0 * gxy, gxx - gyy)
    sector = (np.round((theta + np.pi / 2.0) / (np.pi / 8.0)).astype(np.int32)) % 8
    dirs1 = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    keep = np.ones(field.shape, dtype=bool)
    for s in range(8):
        sel = (sector == s) & fp
        if not sel.any():
            continue
        dy1, dx1 = dirs1[s]
        a1 = geopb.shift(sm, dy1, dx1)
        b1 = geopb.shift(sm, -dy1, -dx1)
        keep &= ~(sel & ~((sm >= a1) & (sm >= b1)))
    out = np.where(keep, field, field * keep_floor).astype(np.float32)
    out[~fp] = 0.0
    return out


def fuse_oof_geopb_thermal(
    p_oof: np.ndarray,
    cr0: np.ndarray,
    s1: np.ndarray,
    s3: np.ndarray,
    g_th: np.ndarray,
    fp: np.ndarray,
) -> np.ndarray:
    """H85-S6-2: Fuse translation-invariant OOF fault probability with GEO-Pb v2, alteration & thermal prior."""
    s1_n = s1 / (float(np.percentile(s1[fp], 99)) + 1e-9)
    s3_n = s3 / (float(np.percentile(s3[fp], 99)) + 1e-9)
    cr0_pos = cr0[fp & (cr0 > 0)]
    cr0_scale = float(np.percentile(cr0_pos, 95)) if cr0_pos.size else 1.0
    cr0_n = np.clip(cr0 / (cr0_scale + 1e-9), 0.0, 2.0)
    combined = (
        p_oof.astype(np.float32)
        * (1.0 + 0.30 * cr0_n + 0.40 * s1_n + 0.25 * s3_n)
        * (1.0 + 0.30 * g_th)
    ).astype(np.float32)
    return crest_1step(combined, fp, sigma=1.0, keep_floor=0.04)
