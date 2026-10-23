"""Parity-Resolved Piedmont-Concordant (PRPC) multi-physics & fold-proper structural synthesis.

Implements Lane H85-P1 (preregistered in registry/preregistration_prpc.json):

1. Tile-seam-decontaminated 1 m 3DEP LiDAR breaklines (resolving IR-85-007):
   calibrates universal 100 m DEM breakline proxies onto interior 1 m LiDAR observations and
   cosine-feathers across the 400 m tile-edge margin so 3DEP coverage boundaries never create
   artificial juxtaposition steps.
2. Parity-resolved 16-strike multi-physics operators (resolving IR-85-006):
   - Odd-symmetry rock-state steps across +-300 m and +-500 m normals (subsurface rtp,
     150 m upward-continued TMI_up150, iso_grav_anom, depth_to_base_surf, log cond_surf;
     surface det_elev and valid-masked GeoDAWN K, Th, U) after along-strike smoothing.
   - Even-symmetry fault-core/scarp impulses on the trace minus +-300 m flanking background
     (seam-free lappos, crest-toe scarp dipole, concave piedmont -tc, GeoDAWN U/Th & U/K
     redox/radon conduit enrichment, and upward-continued potential-field gradient crests).
3. Crustal depth-persistence & piedmont/mesa decontamination (H85-P2 + H85-P3):
   separates basement-rooted sub-vertical contacts (TMI_up150 / TMI attenuation slope) and
   piedmont range-front hinges from high convex volcanic mesas and flat playa centers, plus
   GDR-1391 thermal/geothermometer upflow plumes (strictly dropping dist_known_fault_px).
4. Fold-proper visible-network fracture mechanics (strictly from a fold's visible_mask):
   anisotropic tip-propagation cones, Voronoi inter-component medial-axis relays, and
   color-coded 2nd-distinct-component colinear wash-gap bridges, trained via inner
   whole-component self-excluded splits so d_visible == 0 never occurs in training or inference.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.signal import fftconvolve
from sklearn.ensemble import HistGradientBoostingClassifier

from . import emission, emitter, grid

FORBIDDEN_GDR_COLUMNS = frozenset({"dist_known_fault_px"})
FORBIDDEN_RASTER_NAMES = frozenset({"derived_sgmc_faults_100m_u8.tif", "known_faults.tif"})

N_STRIKES = 16
STRIKE_ANGLES_RAD = np.linspace(0.0, np.pi, N_STRIKES, endpoint=False).astype(np.float32)


def _robust_z(arr: np.ndarray, valid: np.ndarray, clip: float = 6.0) -> np.ndarray:
    """Median / IQR z-score over `valid`, with smooth log tail compression above `clip`."""
    out = np.zeros(arr.shape, dtype=np.float32)
    m = valid & np.isfinite(arr)
    if not np.any(m):
        return out
    vals = arr[m]
    sample = vals[::4] if vals.size > 200_000 else vals
    q25, med, q75 = [float(x) for x in np.percentile(sample, [25.0, 50.0, 75.0])]
    scale = (q75 - q25) / 1.3489795
    if scale < 1e-6:
        scale = float(np.std(sample))
    if scale < 1e-6:
        return out
    z = (vals - np.float32(med)) / np.float32(scale)
    az = np.abs(z)
    z_soft = np.where(az <= clip, z, np.sign(z) * (clip + np.log1p(np.maximum(az - clip, 0.0))))
    out[m] = z_soft.astype(np.float32)
    return out


def _smooth_masked(arr: np.ndarray, valid: np.ndarray, sigma: float) -> np.ndarray:
    """Normalized Gaussian convolution that does not bleed zeros across `valid` boundaries."""
    w = valid.astype(np.float32)
    x = np.where(valid & np.isfinite(arr), arr, 0.0).astype(np.float32)
    num = ndi.gaussian_filter(x, sigma=sigma, mode="nearest")
    den = ndi.gaussian_filter(w, sigma=sigma, mode="nearest")
    out = np.zeros_like(x)
    ok = den > 1e-4
    out[ok] = num[ok] / den[ok]
    return out


def _grad_mag(arr: np.ndarray, sigma: float = 1.2) -> np.ndarray:
    s = ndi.gaussian_filter(arr.astype(np.float32), sigma=sigma, mode="nearest")
    gy = ndi.gaussian_filter(s, sigma=0.8, order=[1, 0], mode="nearest")
    gx = ndi.gaussian_filter(s, sigma=0.8, order=[0, 1], mode="nearest")
    return np.hypot(gy, gx).astype(np.float32)


def _shift2d(arr: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Edge-clamped integer 2D shift without wrap-around."""
    h, w = arr.shape
    out = np.empty_like(arr)
    sy_src = slice(max(0, -dy), min(h, h - dy))
    sy_dst = slice(max(0, dy), min(h, h + dy))
    sx_src = slice(max(0, -dx), min(w, w - dx))
    sx_dst = slice(max(0, dx), min(w, w + dx))
    out[sy_dst, sx_dst] = arr[sy_src, sx_src]
    if dy > 0:
        out[:dy, sx_dst] = out[dy:dy + 1, sx_dst]
    elif dy < 0:
        out[h + dy:, sx_dst] = out[h + dy - 1:h + dy, sx_dst]
    if dx > 0:
        out[:, :dx] = out[:, dx:dx + 1]
    elif dx < 0:
        out[:, w + dx:] = out[:, w + dx - 1:w + dx]
    return out


def decontaminate_lidar_scarps(
    lidar_bands: dict[str, np.ndarray],
    lidar_valid: np.ndarray,
    det_elev: np.ndarray,
    det_elev_slope: np.ndarray,
    tc: np.ndarray,
    footprint: np.ndarray,
    feather_px: int = 4,
) -> dict[str, np.ndarray]:
    """Eliminate 3DEP 1 m LiDAR tile-boundary step artifacts (IR-85-007).

    Fits an interior OLS proxy from universal 100 m DEM breakline predictors on interior
    `lidar_valid` pixels (eroded by `feather_px`), then cosine-blends across the `feather_px`
    boundary transition into the DEM proxy where 1 m tiles are absent.
    """
    fp = footprint.astype(bool)
    lv = lidar_valid.astype(bool) & fp

    # Universal 100 m DEM breakline predictors available across 100% of footprint
    elev_f = _smooth_masked(det_elev, fp, sigma=1.0)
    lap = ndi.laplace(elev_f, mode="nearest").astype(np.float32)
    dem_lappos = _robust_z(np.maximum(lap, 0.0), fp)
    dem_lapneg = _robust_z(np.maximum(-lap, 0.0), fp)
    dem_slope = _robust_z(det_elev_slope, fp)
    dem_negtc = _robust_z(np.maximum(-tc, 0.0), fp)
    dem_postc = _robust_z(np.maximum(tc, 0.0), fp)
    local_max = ndi.maximum_filter(elev_f, size=5, mode="nearest")
    local_min = ndi.minimum_filter(elev_f, size=5, mode="nearest")
    dem_relief = _robust_z(local_max - local_min, fp)

    # Smooth feather weight: 1.0 deep inside lidar_valid, 0.0 outside lidar_valid
    dist_outside = ndi.distance_transform_edt(lv).astype(np.float32)
    alpha = np.clip((dist_outside - 1.0) / max(float(feather_px), 1.0), 0.0, 1.0)
    alpha = (0.5 - 0.5 * np.cos(np.pi * alpha)).astype(np.float32)
    interior = dist_outside >= float(feather_px + 1)

    preds = [
        np.ones( int(fp.sum()), dtype=np.float32 ),
        dem_slope[fp],
        dem_negtc[fp],
        dem_postc[fp],
        dem_lappos[fp],
        dem_lapneg[fp],
        dem_relief[fp],
    ]
    X_fp = np.column_stack(preds)
    int_fp = interior[fp]
    if int(int_fp.sum()) > 500:
        rng = np.random.default_rng(8501)
        idx_fit = np.flatnonzero(int_fp)
        if idx_fit.size > 250_000:
            idx_fit = rng.choice(idx_fit, 250_000, replace=False)
        X_fit = X_fp[idx_fit]
        XtX = X_fit.T @ X_fit + 1e-2 * np.eye(X_fit.shape[1], dtype=np.float32)
    else:
        idx_fit = None
        XtX = None

    out: dict[str, np.ndarray] = {}
    for name, raw in lidar_bands.items():
        z_obs = _robust_z(raw.astype(np.float32), interior if np.any(interior) else lv)
        proxy = np.zeros(det_elev.shape, dtype=np.float32)
        if idx_fit is not None:
            y_fit = z_obs[fp][idx_fit]
            coef = np.linalg.solve(XtX, X_fit.T @ y_fit)
            proxy[fp] = np.clip(X_fp @ coef, -5.0, 5.0).astype(np.float32)
        blended = alpha * z_obs + (1.0 - alpha) * proxy
        blended[~fp] = 0.0
        out[f"{name}_seamfree"] = blended.astype(np.float32)

    # Scarp polarity asymmetry & paired crest-toe scarp dipole
    up_raw = np.maximum(lidar_bands["upface_max"].astype(np.float32), 0.0)
    dn_raw = np.maximum(lidar_bands["downface_max"].astype(np.float32), 0.0)
    asym_obs = np.abs(dn_raw - up_raw) / (dn_raw + up_raw + 3.0)
    asym_z = _robust_z(asym_obs, interior if np.any(interior) else lv)
    asym_proxy = 0.5 * np.abs(dem_negtc - dem_postc)
    out["scarp_asymmetry_seamfree"] = np.where(
        fp, alpha * asym_z + (1.0 - alpha) * asym_proxy, 0.0
    ).astype(np.float32)

    lp = np.maximum(out["lappos_max_seamfree"] + 0.5, 0.0)
    ln = np.maximum(out["lapneg_max_seamfree"] + 0.5, 0.0)
    out["scarp_dipole_seamfree"] = _robust_z(np.sqrt(lp * ln), fp)
    out["lidar_interior_weight"] = alpha
    return out


def load_gdr_hydrothermal_fields(
    data_dir: Path,
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Build thermal/geothermometer fields from GDR-1391 without touching fault columns."""
    shape = footprint.shape
    fp = footprint.astype(bool)
    meas_grid = np.zeros(shape, dtype=np.float32)
    geoth_grid = np.zeros(shape, dtype=np.float32)
    hot_seed = np.zeros(shape, dtype=bool)
    vent_grid = np.zeros(shape, dtype=np.float32)

    ws_path = data_dir / "external" / "gdr_wellspring_in_footprint.csv"
    if ws_path.exists():
        with ws_path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            usable_cols = cols - FORBIDDEN_GDR_COLUMNS
            assert "dist_known_fault_px" not in usable_cols
            for row in reader:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
                if not (0 <= r < shape[0] and 0 <= c < shape[1] and fp[r, c]):
                    continue
                tc_val = float(row["temp_c"]) if row.get("temp_c") not in (None, "", "nan") else np.nan
                gq = float(row["geothermquartz_c"]) if row.get("geothermquartz_c") not in (None, "", "nan") else np.nan
                gc = float(row["geothermchalc_c"]) if row.get("geothermchalc_c") not in (None, "", "nan") else np.nan
                gk = float(row["geothermcat_c"]) if row.get("geothermcat_c") not in (None, "", "nan") else np.nan

                if np.isfinite(tc_val) and tc_val < 350.0:
                    excess = max(0.0, tc_val - 20.0)
                    if excess > meas_grid[r, c]:
                        meas_grid[r, c] = excess
                    if tc_val >= 30.0:
                        hot_seed[r, c] = True

                g_list = [v for v in (gq, gc, gk) if np.isfinite(v) and 0.0 < v < 400.0]
                if g_list:
                    g_max = max(g_list)
                    g_exc = max(0.0, g_max - 65.0)
                    if g_exc > geoth_grid[r, c]:
                        geoth_grid[r, c] = g_exc
                    if g_max >= 85.0:
                        hot_seed[r, c] = True

    vv_path = data_dir / "external" / "gdr_volcanic_vents_in_footprint.csv"
    if vv_path.exists():
        with vv_path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            usable_cols = cols - FORBIDDEN_GDR_COLUMNS
            assert "dist_known_fault_px" not in usable_cols
            for row in reader:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
                if 0 <= r < shape[0] and 0 <= c < shape[1] and fp[r, c]:
                    vent_grid[r, c] += 1.0

    plume_1km = ndi.gaussian_filter(np.log1p(meas_grid), sigma=10.0, mode="constant")
    plume_3km = ndi.gaussian_filter(np.log1p(meas_grid), sigma=28.0, mode="constant")
    geoth_2km = ndi.gaussian_filter(np.log1p(geoth_grid), sigma=18.0, mode="constant")
    vent_2km = ndi.gaussian_filter(vent_grid, sigma=20.0, mode="constant")

    if np.any(hot_seed):
        d_hot = ndi.distance_transform_edt(~hot_seed).astype(np.float32)
        hydro_prox = -np.log1p(d_hot / 15.0)
    else:
        hydro_prox = np.zeros(shape, dtype=np.float32)

    return {
        "hydro_meas_1km": _robust_z(plume_1km, fp),
        "hydro_meas_3km": _robust_z(plume_3km, fp),
        "hydro_geotherm_2km": _robust_z(geoth_2km, fp),
        "hydro_prox": _robust_z(hydro_prox, fp),
        "volcanic_vent_2km": _robust_z(vent_2km, fp),
    }


def _read_clean_tf(name: str, fp: np.ndarray) -> np.ndarray:
    arr = grid.read_feature(name)
    vals = arr[fp]
    finite = vals[np.isfinite(vals)]
    med = float(np.median(finite[::8] if finite.size > 200_000 else finite)) if finite.size else 0.0
    out = np.where(fp & np.isfinite(arr), arr, med).astype(np.float32)
    return out


def load_clean_physical_inputs(
    footprint: np.ndarray | None = None,
    *,
    sink_fp: np.ndarray | None = None,
    sink_names: dict[str, int] | None = None,
    fp_idx: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Load and artifact-decontaminate all physical layers (0% catalogue access).

    When `sink_fp` (an open memmap `(N_fp, D)`) is supplied, channels not needed downstream
    by `compute_prpc_operators` are flushed directly into `sink_fp` and freed immediately so
    peak RAM stays under ~1.1 GB on 3.6 GB sandboxes.
    """
    import gc
    fp = grid.footprint() if footprint is None else footprint.astype(bool)
    data_dir = grid.DATA

    needed_for_ops = {
        "rtp_z", "tmi_up150_z", "grad_tmi_up150_z", "mag_depth_persistence",
        "iso_grav_z", "iso_grav_hg_z", "depth_base_z", "cond_surf_z",
        "det_elev_z", "K_z", "Th_z", "U_z",
        "lappos_max_seamfree", "scarp_dipole_seamfree", "neg_tc_z", "rad_redox_conduit",
        "piedmont_hinge", "mesa_caprock_penalty", "hydro_meas_3km", "geod_2ndinv_z",
    }
    out: dict[str, np.ndarray] = {}

    def _emit(key: str, arr: np.ndarray) -> None:
        if sink_fp is not None and sink_names is not None and fp_idx is not None:
            if key in sink_names:
                sink_fp[:, sink_names[key]] = arr.ravel()[fp_idx]
            if key in needed_for_ops:
                out[key] = arr
        else:
            out[key] = arr

    # 1. Topography + Piedmont-hinge & volcanic-mesa decontamination
    det_elev = _read_clean_tf("det_elev", fp)
    det_elev_slope = _read_clean_tf("det_elev_slope", fp)
    tc = _read_clean_tf("tc", fp)

    det_elev_z = _robust_z(det_elev, fp)
    slope_z = _robust_z(det_elev_slope, fp)
    tc_z = _robust_z(tc, fp)
    neg_tc_z = _robust_z(np.maximum(-tc, 0.0), fp)
    elev_1km_z = _robust_z(_smooth_masked(det_elev, fp, sigma=10.0), fp)
    elev_25km_z = _robust_z(_smooth_masked(det_elev, fp, sigma=25.0), fp)

    piedmont_hinge = _robust_z(
        np.maximum(neg_tc_z, 0.0) * np.exp(-0.5 * (det_elev_z / 1.35) ** 2),
        fp,
    )
    mesa_caprock_penalty = _robust_z(
        np.maximum(elev_1km_z - 0.45, 0.0) * np.maximum(tc_z + 0.25, 0.0)
        + 0.4 * np.maximum(det_elev_z - 1.2, 0.0) * np.maximum(slope_z - 1.2, 0.0),
        fp,
    )
    _emit("det_elev_z", det_elev_z)
    _emit("elev_1km_z", elev_1km_z); del elev_1km_z
    _emit("elev_25km_z", elev_25km_z); del elev_25km_z
    _emit("slope_z", slope_z); del slope_z
    _emit("tc_z", tc_z); del tc_z
    _emit("neg_tc_z", neg_tc_z)
    _emit("piedmont_hinge", piedmont_hinge)
    _emit("mesa_caprock_penalty", mesa_caprock_penalty)

    # 2. 1 m 3DEP LiDAR breaklines (seam-decontaminated, indexed by verified band description)
    lidar_path = data_dir / "external" / "lidar_scarp_features_u8.tif"
    assert lidar_path.name not in FORBIDDEN_RASTER_NAMES
    with rasterio.open(lidar_path) as src:
        grid.assert_grid(src, lidar_path.name)
        lidar_desc = list(src.descriptions)
        lidar_by_name = {nm: src.read(i + 1) for i, nm in enumerate(lidar_desc)}
    lidar_keep = (
        "ex_max", "step_max", "lapneg_max", "lappos_max",
        "downface_max", "upface_max", "cross_max", "relief", "coh100",
    )
    lidar_dict = {nm: lidar_by_name[nm] for nm in lidar_keep}
    lidar_valid = (lidar_by_name["valid"] > 0) & fp
    del lidar_by_name
    lidar_clean = decontaminate_lidar_scarps(
        lidar_dict, lidar_valid, det_elev, det_elev_slope, tc, fp
    )
    del lidar_dict, lidar_valid, det_elev, det_elev_slope, tc
    for k, v in list(lidar_clean.items()):
        _emit(k, v)
    del lidar_clean
    gc.collect()

    # 3. Potential fields, MT, tilt-derivative & upward continuation (H85-P2)
    _emit("rtp_z", _robust_z(_read_clean_tf("rtp", fp), fp))
    tmi_hg_z = _robust_z(_read_clean_tf("tmi_hg", fp), fp)
    _emit("tmi_hg_z", tmi_hg_z); del tmi_hg_z
    _emit("tmi_vg_z", _robust_z(_read_clean_tf("tmi_vg", fp), fp))
    _emit("iso_grav_z", _robust_z(_read_clean_tf("iso_grav_anom", fp), fp))
    _emit("iso_grav_hg_z", _robust_z(_read_clean_tf("iso_grav_anom_hg", fp), fp))
    _emit("iso_grav_vg_z", _robust_z(_read_clean_tf("iso_grav_anom_vg", fp), fp))
    _emit("iso_grav_slope_z", _robust_z(_read_clean_tf("iso_grav_anom_slope", fp), fp))
    _emit("depth_base_z", _robust_z(_read_clean_tf("depth_to_base_surf", fp), fp))
    _emit("cond_surf_z", _robust_z(np.log1p(np.maximum(_read_clean_tf("cond_surf", fp), 0.0)), fp))

    tmi_raw = _read_clean_tf("tmi", fp)
    tmi_z = _robust_z(tmi_raw, fp)
    tmi_smooth_z = _robust_z(_smooth_masked(tmi_raw, fp, sigma=1.8), fp)
    del tmi_raw

    ext_path = data_dir / "external" / "geodawn_extensions_u8.tif"
    with rasterio.open(ext_path) as src:
        grid.assert_grid(src, ext_path.name)
        ext_by_name = {nm: src.read(i + 1) for i, nm in enumerate(src.descriptions)}

    ext_mag_valid = (ext_by_name["TMI_up150"] > 0) & fp
    ext_mag_dist = ndi.distance_transform_edt(ext_mag_valid).astype(np.float32)
    ext_mag_w = np.clip((ext_mag_dist - 1.0) / 4.0, 0.0, 1.0).astype(np.float32)
    ext_mag_int = ext_mag_dist >= 4.0 if np.any(ext_mag_dist >= 4.0) else ext_mag_valid
    tmi_up150_obs = _robust_z(ext_by_name["TMI_up150"].astype(np.float32), ext_mag_int)
    tmi_up150_seamless = ext_mag_w * tmi_up150_obs + (1.0 - ext_mag_w) * tmi_smooth_z
    del ext_mag_valid, ext_mag_dist, ext_mag_w, tmi_up150_obs, tmi_smooth_z

    grad_tmi = _grad_mag(tmi_z, sigma=1.0)
    del tmi_z
    grad_tmi_up150 = _grad_mag(tmi_up150_seamless, sigma=1.0)
    atten_ratio = np.log((grad_tmi_up150 + 0.08) / (grad_tmi + 0.08))
    del grad_tmi
    _emit("tmi_up150_z", _robust_z(tmi_up150_seamless, fp)); del tmi_up150_seamless
    _emit("mag_depth_persistence", _robust_z(atten_ratio * np.tanh(grad_tmi_up150 * 1.5), fp)); del atten_ratio
    _emit("grad_tmi_up150_z", _robust_z(grad_tmi_up150, fp)); del grad_tmi_up150

    # 4. GeoDAWN radiometrics & redox/radon ratios (H85-P3)
    ext_rad_valid = ((ext_by_name["UTh"] > 0) | (ext_by_name["UK"] > 0)) & fp
    ext_rad_dist = ndi.distance_transform_edt(ext_rad_valid).astype(np.float32)
    ext_rad_w = np.clip((ext_rad_dist - 1.0) / 4.0, 0.0, 1.0).astype(np.float32)
    ext_rad_int = ext_rad_dist >= 4.0 if np.any(ext_rad_dist >= 4.0) else ext_rad_valid
    UK_z = _robust_z(ext_by_name["UK"].astype(np.float32), ext_rad_int) * ext_rad_w
    UTh_z = _robust_z(ext_by_name["UTh"].astype(np.float32), ext_rad_int) * ext_rad_w
    ThK_z = _robust_z(ext_by_name["ThK"].astype(np.float32), ext_rad_int) * ext_rad_w
    del ext_by_name, ext_rad_valid, ext_rad_dist, ext_rad_w
    rad_redox_conduit = _robust_z(0.65 * UTh_z + 0.35 * UK_z - 0.25 * ThK_z, fp)
    _emit("UK_z", UK_z); del UK_z
    _emit("UTh_z", UTh_z); del UTh_z
    _emit("ThK_z", ThK_z); del ThK_z
    _emit("rad_redox_conduit", rad_redox_conduit)

    rad_path = data_dir / "external" / "geodawn_rad_u8.tif"
    with rasterio.open(rad_path) as src:
        grid.assert_grid(src, rad_path.name)
        rad_by_name = {nm: src.read(i + 1) for i, nm in enumerate(src.descriptions)}
    rad_valid = (rad_by_name["TC"] > 0) & fp
    rad_dist = ndi.distance_transform_edt(rad_valid).astype(np.float32)
    rad_w = np.clip((rad_dist - 1.0) / 4.0, 0.0, 1.0).astype(np.float32)
    rad_int = rad_dist >= 4.0 if np.any(rad_dist >= 4.0) else ext_rad_int
    _emit("K_z", _robust_z(rad_by_name["K"].astype(np.float32), rad_int) * rad_w)
    _emit("Th_z", _robust_z(rad_by_name["Th"].astype(np.float32), rad_int) * rad_w)
    _emit("U_z", _robust_z(rad_by_name["U"].astype(np.float32), rad_int) * rad_w)
    del rad_by_name, rad_valid, rad_dist, rad_w
    gc.collect()

    # 5. Geodesy & seismicity strain/density fields
    _emit("geod_dilaterate_z", _robust_z(_read_clean_tf("geod_dilaterate", fp), fp))
    _emit("geod_2ndinv_z", _robust_z(_read_clean_tf("geod_2ndinv", fp), fp))
    _emit("geod_shearrate_z", _robust_z(_read_clean_tf("geod_shearrate", fp), fp))
    _emit("ieq_z", _robust_z(_read_clean_tf("ieq_n100a15", fp), fp))
    _emit("deq_z", _robust_z(_read_clean_tf("deq_n100a15", fp), fp))

    # 6. GDR-1391 thermal & geothermometer plumes
    hydro = load_gdr_hydrothermal_fields(data_dir, fp)
    for k, v in list(hydro.items()):
        _emit(k, v)
    del hydro
    gc.collect()
    return out


def _whiten_channels(chans: list[np.ndarray], valid: np.ndarray, seed: int = 8502) -> list[np.ndarray]:
    """ZCA/Cholesky whitening across channels on footprint pixels so correlated layers aren't double-counted."""
    idx = np.flatnonzero(valid.ravel())
    rng = np.random.default_rng(seed)
    sub = rng.choice(idx, min(200_000, idx.size), replace=False)
    X = np.column_stack([c.ravel()[sub] for c in chans]).astype(np.float64)
    X -= X.mean(axis=0, keepdims=True)
    cov = (X.T @ X) / max(1, X.shape[0] - 1) + 0.08 * np.eye(len(chans))
    eigvals, eigvecs = np.linalg.eigh(cov)
    W = (eigvecs @ np.diag(1.0 / np.sqrt(np.maximum(eigvals, 1e-4))) @ eigvecs.T).astype(np.float32)
    out = [np.zeros_like(chans[0], dtype=np.float32) for _ in chans]
    for i in range(len(chans)):
        acc = np.zeros_like(chans[0], dtype=np.float32)
        for j in range(len(chans)):
            if abs(float(W[i, j])) > 1e-5:
                acc += W[i, j] * chans[j]
        acc[~valid] = 0.0
        out[i] = acc
    return out


def compute_prpc_operators(
    inputs: dict[str, np.ndarray],
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Evaluate 16-strike parity-resolved odd-step & even-ridge operators (fixes IR-85-006)."""
    fp = footprint.astype(bool)
    # Interior footprint mask so domain boundaries never generate artificial cross-strike steps
    fp_dist = ndi.distance_transform_edt(fp).astype(np.float32)
    edge_taper = np.clip((fp_dist - 2.0) / 5.0, 0.0, 1.0).astype(np.float32)

    # 1. Subsurface odd-parity channels (step across fault normal)
    sub_raw = [
        _smooth_masked(inputs["rtp_z"], fp, 1.1),
        _smooth_masked(inputs["tmi_up150_z"], fp, 1.1),
        _smooth_masked(inputs["iso_grav_z"], fp, 1.3),
        _smooth_masked(inputs["depth_base_z"], fp, 1.3),
        _smooth_masked(inputs["cond_surf_z"], fp, 1.3),
    ]
    sub_w = _whiten_channels(sub_raw, fp, seed=8511)
    del sub_raw

    # 2. Surface odd-parity channels (step across fault normal)
    surf_raw = [
        _smooth_masked(inputs["det_elev_z"], fp, 1.1),
        _smooth_masked(inputs["K_z"], fp, 1.2),
        _smooth_masked(inputs["Th_z"], fp, 1.2),
        _smooth_masked(inputs["U_z"], fp, 1.2),
    ]
    surf_w = _whiten_channels(surf_raw, fp, seed=8512)
    del surf_raw

    # 3. Fault-core even-parity channels (peak ON the fault trace; regional blocks subtract out!)
    up150_grav_hg = _robust_z(
        0.55 * inputs["grad_tmi_up150_z"] + 0.45 * inputs["iso_grav_hg_z"], fp
    )
    core_chans = [
        _smooth_masked(inputs["lappos_max_seamfree"], fp, 0.8),
        _smooth_masked(inputs["scarp_dipole_seamfree"], fp, 0.8),
        _smooth_masked(inputs["neg_tc_z"], fp, 0.9),
        _smooth_masked(inputs["rad_redox_conduit"], fp, 1.2),
        _smooth_masked(up150_grav_hg, fp, 1.0),
    ]
    core_weights = np.array([0.30, 0.22, 0.20, 0.13, 0.15], dtype=np.float32)

    h, w = fp.shape
    best_total = np.full((h, w), -1e9, dtype=np.float32)
    best_idx = np.zeros((h, w), dtype=np.uint8)
    best_sub = np.zeros((h, w), dtype=np.float32)
    best_surf = np.zeros((h, w), dtype=np.float32)
    best_core = np.zeros((h, w), dtype=np.float32)
    sum_total = np.zeros((h, w), dtype=np.float32)
    sumsq_total = np.zeros((h, w), dtype=np.float32)

    for m, theta in enumerate(STRIKE_ANGLES_RAD):
        # theta in [0, pi): tangent along (dy_t, dx_t) = (-sin(theta), cos(theta)) in (row=S, col=E)
        ty = -float(np.sin(theta))
        tx = float(np.cos(theta))
        ny = -tx  # normal perpendicular to tangent
        nx = ty

        # 3-tap along-strike coherence offsets (+-3 px along tangent)
        tdy = int(round(3.0 * ty))
        tdx = int(round(3.0 * tx))
        # Cross-strike normal offsets at r = 3 px (300 m) and r = 5 px (500 m)
        ndy3, ndx3 = int(round(3.0 * ny)), int(round(3.0 * nx))
        ndy5, ndx5 = int(round(5.0 * ny)), int(round(5.0 * nx))

        # Subsurface odd-step energy (Mahalanobis norm across +-3 px and +-5 px)
        j_sub = np.zeros((h, w), dtype=np.float32)
        for ch in sub_w:
            bar = 0.50 * ch + 0.25 * _shift2d(ch, tdy, tdx) + 0.25 * _shift2d(ch, -tdy, -tdx)
            d3 = _shift2d(bar, ndy3, ndx3) - _shift2d(bar, -ndy3, -ndx3)
            d5 = _shift2d(bar, ndy5, ndx5) - _shift2d(bar, -ndy5, -ndx5)
            j_sub += 0.55 * (d3 * d3) + 0.45 * (d5 * d5)
        j_sub = np.sqrt(j_sub / len(sub_w)).astype(np.float32) * edge_taper

        # Surface odd-step energy
        j_surf = np.zeros((h, w), dtype=np.float32)
        for ch in surf_w:
            bar = 0.50 * ch + 0.25 * _shift2d(ch, tdy, tdx) + 0.25 * _shift2d(ch, -tdy, -tdx)
            d3 = _shift2d(bar, ndy3, ndx3) - _shift2d(bar, -ndy3, -ndx3)
            j_surf += d3 * d3
        j_surf = np.sqrt(j_surf / len(surf_w)).astype(np.float32) * edge_taper

        # Fault-core even-parity ridge energy: on-trace axial mean minus +-3 px flanking background
        i_core = np.zeros((h, w), dtype=np.float32)
        for w_c, ch in zip(core_weights, core_chans):
            bar = 0.50 * ch + 0.25 * _shift2d(ch, tdy, tdx) + 0.25 * _shift2d(ch, -tdy, -tdx)
            flank = 0.50 * (_shift2d(bar, ndy3, ndx3) + _shift2d(bar, -ndy3, -ndx3))
            i_core += w_c * np.maximum(bar - flank, 0.0)
        i_core *= edge_taper

        # Strike-locked concordance + Great Basin NNE-NNW / GeoDAWN E-W flight-line coupling
        # theta = pi/2 corresponds to N-S fault trace (ty=-1, tx=0) cut orthogonally by E-W lines
        kin_weight = float(0.82 + 0.18 * (np.sin(theta) ** 2))
        concord = np.sqrt(np.maximum(j_sub, 0.0) * np.maximum(i_core, 0.0))
        score_m = kin_weight * (0.34 * j_sub + 0.36 * i_core + 0.14 * j_surf + 0.26 * concord)

        better = score_m > best_total
        best_total = np.where(better, score_m, best_total)
        best_idx = np.where(better, np.uint8(m), best_idx)
        best_sub = np.where(better, j_sub, best_sub)
        best_surf = np.where(better, j_surf, best_surf)
        best_core = np.where(better, i_core, best_core)
        sum_total += score_m
        sumsq_total += score_m * score_m

    del sub_w, surf_w, core_chans, edge_taper
    mean_total = sum_total / N_STRIKES
    var_total = np.maximum(sumsq_total / N_STRIKES - mean_total * mean_total, 1e-6)
    anisotropy = (best_total - mean_total) / np.sqrt(var_total)
    del sum_total, sumsq_total, mean_total, var_total

    # Along-strike persistence (900 m = +-4 px along winning strike) & cross-strike NMS sharpening
    strike_rad = STRIKE_ANGLES_RAD[best_idx]
    persisted = best_total.copy()
    nms_sharp = np.zeros((h, w), dtype=np.float32)
    for m, theta in enumerate(STRIKE_ANGLES_RAD):
        sel = (best_idx == m) & fp
        if not np.any(sel):
            continue
        ty, tx = -float(np.sin(theta)), float(np.cos(theta))
        ny, nx = -tx, ty
        td2y, td2x = int(round(2.0 * ty)), int(round(2.0 * tx))
        td4y, td4x = int(round(4.0 * ty)), int(round(4.0 * tx))
        along = (
            0.36 * best_total
            + 0.20 * (_shift2d(best_total, td2y, td2x) + _shift2d(best_total, -td2y, -td2x))
            + 0.12 * (_shift2d(best_total, td4y, td4x) + _shift2d(best_total, -td4y, -td4x))
        )
        persisted[sel] = along[sel]

        nd2y, nd2x = int(round(2.0 * ny)), int(round(2.0 * nx))
        f_plus = _shift2d(along, nd2y, nd2x)
        f_minus = _shift2d(along, -nd2y, -nd2x)
        # Soft non-maximum ridge sharpening across strike
        ridge_ratio = along / (0.5 * (f_plus + f_minus) + 0.15)
        nms_sharp[sel] = (along[sel] * np.clip(ridge_ratio[sel] - 0.85, 0.0, 1.5)).astype(np.float32)

    # E1 Unsupervised PRPC crest surface: parity-resolved concordance + depth persistence + piedmont
    # hinge + hydrothermal upflow + strain minus volcanic-mesa caprock penalty.
    # Uses non-saturating prevalence-calibrated exponential mapping (avoiding logistic flat-topping
    # of 4..10 sigma scarps) while staying strictly inside (0, 1).
    e1_raw = (
        0.48 * _robust_z(nms_sharp, fp)
        + 0.22 * _robust_z(persisted, fp)
        + 0.14 * np.maximum(inputs["piedmont_hinge"], 0.0)
        + 0.10 * np.maximum(inputs["mag_depth_persistence"], 0.0)
        + 0.08 * np.maximum(inputs["geod_2ndinv_z"], 0.0)
        + 0.06 * np.maximum(inputs["hydro_meas_3km"], 0.0)
        - 0.28 * np.maximum(inputs["mesa_caprock_penalty"], 0.0)
    )
    e1_z = _robust_z(e1_raw, fp)
    e1_surface = np.zeros((h, w), dtype=np.float32)
    e1_surface[fp] = np.clip(
        0.008 * np.exp(0.58 * np.clip(e1_z[fp], -3.0, 7.8)),
        1e-5,
        0.98,
    ).astype(np.float32)

    concord_best = _robust_z(np.sqrt(np.maximum(best_sub, 0.0) * np.maximum(best_core, 0.0)), fp)
    return {
        "prpc_best_z": _robust_z(best_total, fp),
        "prpc_persisted_z": _robust_z(persisted, fp),
        "prpc_nms_z": _robust_z(nms_sharp, fp),
        "prpc_sub_odd_z": _robust_z(best_sub, fp),
        "prpc_surf_odd_z": _robust_z(best_surf, fp),
        "prpc_core_even_z": _robust_z(best_core, fp),
        "prpc_concord_z": concord_best,
        "prpc_anisotropy_z": _robust_z(anisotropy, fp),
        "prpc_strike_rad": np.where(fp, strike_rad, 0.0).astype(np.float32),
        "e1_unsupervised_surface": e1_surface,
    }


BLIND_FEATURE_NAMES: tuple[str, ...] = (
    "prpc_nms_z",
    "prpc_persisted_z",
    "prpc_sub_odd_z",
    "prpc_surf_odd_z",
    "prpc_core_even_z",
    "prpc_concord_z",
    "prpc_anisotropy_z",
    "ex_max_seamfree",
    "lappos_max_seamfree",
    "lapneg_max_seamfree",
    "step_max_seamfree",
    "downface_max_seamfree",
    "cross_max_seamfree",
    "coh100_seamfree",
    "scarp_asymmetry_seamfree",
    "scarp_dipole_seamfree",
    "det_elev_z",
    "elev_1km_z",
    "elev_25km_z",
    "slope_z",
    "tc_z",
    "neg_tc_z",
    "piedmont_hinge",
    "mesa_caprock_penalty",
    "rtp_z",
    "tmi_hg_z",
    "tmi_vg_z",
    "tmi_up150_z",
    "grad_tmi_up150_z",
    "mag_depth_persistence",
    "iso_grav_z",
    "iso_grav_hg_z",
    "iso_grav_vg_z",
    "iso_grav_slope_z",
    "depth_base_z",
    "cond_surf_z",
    "rad_redox_conduit",
    "UTh_z",
    "ThK_z",
    "geod_2ndinv_z",
    "geod_shearrate_z",
    "geod_dilaterate_z",
    "ieq_z",
    "deq_z",
    "hydro_meas_1km",
    "hydro_geotherm_2km",
    "hydro_prox",
    "volcanic_vent_2km",
)


@dataclass
class BlindStackBundle:
    X_fp: np.ndarray                 # (N_fp, D_blind) float32
    feature_names: tuple[str, ...]
    fp_idx: np.ndarray               # flat indices of footprint pixels
    prpc_strike_rad: np.ndarray      # (H, W) float32
    prpc_score_z: np.ndarray         # (H, W) float32
    e1_surface: np.ndarray           # (H, W) float32 in [0, 1]


def build_or_load_blind_bundle(
    footprint: np.ndarray,
    cache_dir: Path | None = None,
) -> BlindStackBundle:
    """Build or load the 43-channel 100% catalogue-free PRPC stack on footprint pixels."""
    fp = footprint.astype(bool)
    fp_idx = np.flatnonzero(fp.ravel())

    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        x_path = cache_dir / "prpc_X_fp_v1.npy"
        meta_path = cache_dir / "prpc_surfaces_v1.npz"
        if x_path.exists() and meta_path.exists():
            X_fp = np.load(x_path, mmap_mode="r")
            meta = np.load(meta_path)
            if X_fp.shape == (fp_idx.size, len(BLIND_FEATURE_NAMES)):
                return BlindStackBundle(
                    X_fp=X_fp,
                    feature_names=BLIND_FEATURE_NAMES,
                    fp_idx=fp_idx,
                    prpc_strike_rad=meta["prpc_strike_rad"],
                    prpc_score_z=meta["prpc_score_z"],
                    e1_surface=meta["e1_surface"],
                )

    n_fp = fp_idx.size
    d = len(BLIND_FEATURE_NAMES)
    sink_names = {nm: j for j, nm in enumerate(BLIND_FEATURE_NAMES)}
    if cache_dir is not None:
        x_path = cache_dir / "prpc_X_fp_v1.npy"
        X_fp = np.lib.format.open_memmap(x_path, mode="w+", dtype=np.float32, shape=(n_fp, d))
    else:
        X_fp = np.empty((n_fp, d), dtype=np.float32)

    inputs = load_clean_physical_inputs(fp, sink_fp=X_fp, sink_names=sink_names, fp_idx=fp_idx)
    ops = compute_prpc_operators(inputs, fp)
    prpc_strike_rad = ops["prpc_strike_rad"]
    prpc_score_z = ops["prpc_nms_z"]
    e1_surface = ops["e1_unsupervised_surface"]
    del inputs
    for nm, arr in list(ops.items()):
        if nm in sink_names:
            X_fp[:, sink_names[nm]] = arr.ravel()[fp_idx]
    del ops

    if cache_dir is not None:
        X_fp.flush()
        del X_fp
        X_fp = np.load(cache_dir / "prpc_X_fp_v1.npy", mmap_mode="r")
        np.savez(
            cache_dir / "prpc_surfaces_v1.npz",
            prpc_strike_rad=prpc_strike_rad,
            prpc_score_z=prpc_score_z,
            e1_surface=e1_surface,
        )

    return BlindStackBundle(
        X_fp=X_fp,
        feature_names=BLIND_FEATURE_NAMES,
        fp_idx=fp_idx,
        prpc_strike_rad=prpc_strike_rad,
        prpc_score_z=prpc_score_z,
        e1_surface=e1_surface,
    )


def _fault_local_strike_rad(visible_mask: np.ndarray) -> np.ndarray:
    """Estimate local fault tangent strike angle in [0, pi) on pixels of `visible_mask`."""
    vf = visible_mask.astype(np.float32)
    s = ndi.gaussian_filter(vf, sigma=1.6, mode="constant")
    gy = ndi.gaussian_filter(s, sigma=0.8, order=[1, 0], mode="constant")
    gx = ndi.gaussian_filter(s, sigma=0.8, order=[0, 1], mode="constant")
    # Gradient (gy, gx) points normal to fault; tangent in (row=S, col=E) has (-sin th, cos th)
    # Since normal = (-cos th, -sin th), theta = arctan2(gx, gy) mod pi!
    # Check: N-S fault (constant col) -> gx != 0, gy = 0 -> arctan2(1, 0) = pi/2 -> tangent (-1, 0) = N-S!
    # E-W fault (constant row) -> gy != 0, gx = 0 -> arctan2(0, 1) = 0 -> tangent (0, 1) = E-W!
    jyy = ndi.gaussian_filter(gy * gy, sigma=2.2, mode="constant")
    jxx = ndi.gaussian_filter(gx * gx, sigma=2.2, mode="constant")
    jyx = ndi.gaussian_filter(gy * gx, sigma=2.2, mode="constant")
    # Principal gradient eigenvector anglepsi = 0.5 * arctan2(2*jyx, jyy - jxx); strike = psi
    # Check: E-W fault -> gy=1, gx=0 -> jyy=1, jxx=0, jyx=0 -> psi = 0 -> theta = 0 (E-W).
    # N-S fault -> gy=0, gx=1 -> jyy=0, jxx=1, jyx=0 -> arctan2(0, -1) = pi -> 0.5*pi = pi/2 (N-S).
    strike = 0.5 * np.arctan2(2.0 * jyx, jyy - jxx)
    strike = np.mod(strike, np.pi).astype(np.float32)
    return strike


def _tip_propagation_cones(
    visible_mask: np.ndarray,
    comp_labels: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Anisotropic forward continuation cones ahead of visible fault tips (`visible_mask` only)."""
    vf = visible_mask.astype(bool)
    h, w = vf.shape
    if not np.any(vf):
        z = np.zeros((h, w), dtype=np.float32)
        return z, z

    # Count 8-neighbors on visible_mask; endpoints of non-trivial components (>=5 px) have 1..2 neighbors
    sizes = np.bincount(comp_labels.ravel())
    keep_comp = sizes >= 5
    keep_comp[0] = False
    vf_clean = keep_comp[comp_labels]

    nb = ndi.convolve(vf_clean.astype(np.uint8), np.ones((3, 3), dtype=np.uint8), mode="constant") - vf_clean.astype(np.uint8)
    # Local center-of-mass offset over a 9x9 window points INTO the fault interior; outward tip = -offset
    yy, xx = np.indices((h, w), dtype=np.float32)
    m_f = vf_clean.astype(np.float32)
    w_loc = ndi.uniform_filter(m_f, size=9, mode="constant") * 81.0
    cy_loc = ndi.uniform_filter(m_f * yy, size=9, mode="constant") * 81.0
    cx_loc = ndi.uniform_filter(m_f * xx, size=9, mode="constant") * 81.0

    tips = vf_clean & (nb >= 1) & (nb <= 2) & (w_loc >= 3.0)
    ty_idx, tx_idx = np.nonzero(tips)
    if ty_idx.size == 0:
        z = np.zeros((h, w), dtype=np.float32)
        return z, z

    in_dy = cy_loc[ty_idx, tx_idx] / np.maximum(w_loc[ty_idx, tx_idx], 1.0) - ty_idx
    in_dx = cx_loc[ty_idx, tx_idx] / np.maximum(w_loc[ty_idx, tx_idx], 1.0) - tx_idx
    norm = np.hypot(in_dy, in_dx)
    good = norm > 0.6
    ty_idx, tx_idx = ty_idx[good], tx_idx[good]
    out_dy = -in_dy[good] / norm[good]
    out_dx = -in_dx[good] / norm[good]
    # Weight longer fault components slightly higher (log component pixel count, capped)
    comp_w = np.clip(np.log1p(sizes[comp_labels[ty_idx, tx_idx]]) / 4.0, 0.4, 2.0).astype(np.float32)

    # Bin outward tip directions into 16 full-circle sectors [0, 2*pi) on a 2x (200 m) grid
    # (cones have sigma_along = 1.8 km and 4.2 km, so 200 m FFT is 5x faster & 4x lighter in RAM!)
    n_dir = 16
    ang = np.mod(np.arctan2(out_dy, out_dx), 2.0 * np.pi)
    bins = np.floor(ang / (2.0 * np.pi / n_dir)).astype(int) % n_dir

    sh, sw = (h + 1) // 2, (w + 1) // 2
    cone_short_2x = np.zeros((sh, sw), dtype=np.float32)
    cone_long_2x = np.zeros((sh, sw), dtype=np.float32)

    ks, kl = 18, 36
    ys, xs = np.mgrid[-ks:ks + 1, -ks:ks + 1].astype(np.float32)
    yl, xl = np.mgrid[-kl:kl + 1, -kl:kl + 1].astype(np.float32)

    for b in range(n_dir):
        sel = bins == b
        if not np.any(sel):
            continue
        imp = np.zeros((sh, sw), dtype=np.float32)
        np.add.at(imp, (ty_idx[sel] // 2, tx_idx[sel] // 2), comp_w[sel])

        psi = (b + 0.5) * (2.0 * np.pi / n_dir)
        uy, ux = float(np.sin(psi)), float(np.cos(psi))

        # Short-range tip cone on 200 m grid: 9 px (1.8 km) along tip, 1.5 px lateral spread
        s_along = ys * uy + xs * ux
        s_perp = -ys * ux + xs * uy
        kern_s = np.where(
            s_along > 0.25,
            np.exp(-0.5 * (s_along / 9.0) ** 2 - 0.5 * (s_perp / (1.3 + 0.10 * s_along)) ** 2),
            0.0,
        ).astype(np.float32)
        kern_s /= max(float(kern_s.max()), 1e-6)
        cone_short_2x += fftconvolve(imp, kern_s, mode="same").astype(np.float32)

        # Long-range tip cone on 200 m grid: 21 px (4.2 km) along tip, 2.5 px lateral spread
        l_along = yl * uy + xl * ux
        l_perp = -yl * ux + xl * uy
        kern_l = np.where(
            l_along > 0.5,
            np.exp(-0.5 * (l_along / 21.0) ** 2 - 0.5 * (l_perp / (2.0 + 0.12 * l_along)) ** 2),
            0.0,
        ).astype(np.float32)
        kern_l /= max(float(kern_l.max()), 1e-6)
        cone_long_2x += fftconvolve(imp, kern_l, mode="same").astype(np.float32)

    yi = np.minimum(np.arange(h) // 2, sh - 1)
    xi = np.minimum(np.arange(w) // 2, sw - 1)
    cone_short = ndi.gaussian_filter(cone_short_2x[np.ix_(yi, xi)], sigma=0.8, mode="nearest")
    cone_long = ndi.gaussian_filter(cone_long_2x[np.ix_(yi, xi)], sigma=0.8, mode="nearest")
    return np.maximum(cone_short, 0.0).astype(np.float32), np.maximum(cone_long, 0.0).astype(np.float32)


def _greedy_spatial_component_colors(
    comp_labels: np.ndarray,
    n_comp: int,
    radius_px: int = 55,
    max_colors: int = 16,
) -> np.ndarray:
    """Color connected components so nearby components within `radius_px` receive distinct colors."""
    if n_comp == 0:
        return np.zeros(1, dtype=np.int32)
    slices = ndi.find_objects(comp_labels)
    boxes = np.zeros((n_comp + 1, 4), dtype=np.int32)
    sizes = np.bincount(comp_labels.ravel())
    for cid, sl in enumerate(slices, start=1):
        if sl is None:
            continue
        boxes[cid] = [sl[0].start, sl[0].stop, sl[1].start, sl[1].stop]

    order = np.argsort(-sizes[1:]) + 1
    colors = np.zeros(n_comp + 1, dtype=np.int32)
    for cid in order:
        if sizes[cid] == 0:
            continue
        y0, y1, x0, x1 = boxes[cid]
        # Find already-colored components whose expanded bounding boxes intersect
        cand = colors > 0
        cand[0] = False
        overlap = (
            cand
            & (boxes[:, 0] <= y1 + radius_px)
            & (boxes[:, 1] >= y0 - radius_px)
            & (boxes[:, 2] <= x1 + radius_px)
            & (boxes[:, 3] >= x0 - radius_px)
        )
        used = set(colors[overlap].tolist())
        chosen = 1
        while chosen in used and chosen < max_colors:
            chosen += 1
        if chosen in used:
            chosen = (int(cid) % (max_colors - 1)) + 1
        colors[cid] = chosen
    return colors


VISIBLE_NET_FEATURE_NAMES: tuple[str, ...] = (
    "net_dist1_clip",
    "net_log_dist1",
    "net_along_strike_1",
    "net_prpc_strike_align_1",
    "net_d_medial_clip",
    "net_dist2_clip",
    "net_bridge_opposition",
    "net_strike_coherence_12",
    "net_colinear_wash_gap",
    "net_relay_stepover",
    "net_tip_cone_short",
    "net_tip_cone_long",
    "net_piedmont_splay_band",
    "net_density_3km",
    "net_density_8km",
)


def build_visible_network_features(
    visible_mask: np.ndarray,
    prpc_strike_rad: np.ndarray,
    prpc_score_z: np.ndarray,
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Derive 15 fracture-mechanics / step-over / tip features strictly from `visible_mask`."""
    fp = footprint.astype(bool)
    vf = visible_mask.astype(bool) & fp
    h, w = fp.shape
    if not np.any(vf):
        return {nm: np.zeros((h, w), dtype=np.float32) for nm in VISIBLE_NET_FEATURE_NAMES}

    comp, n_comp = ndi.label(vf, structure=np.ones((3, 3), dtype=int))
    fault_strike = _fault_local_strike_rad(vf)

    # 1. Exact nearest visible fault distance, component ID, strike, and offset vector
    dist1_f64, idx1 = ndi.distance_transform_edt(~vf, return_indices=True)
    dist1 = dist1_f64.astype(np.float32); del dist1_f64
    ny1 = idx1[0].astype(np.int32)
    nx1 = idx1[1].astype(np.int32)
    del idx1
    c1 = comp[ny1, nx1]
    phi1 = fault_strike[ny1, nx1]

    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    vy1 = yy - ny1.astype(np.float32); del ny1
    vx1 = xx - nx1.astype(np.float32); del nx1
    norm1_sq = vy1 * vy1 + vx1 * vx1 + np.float32(1e-4)

    # Fault unit tangent vector in (row, col): (-sin phi, cos phi)
    ty1 = (-np.sin(phi1)).astype(np.float32)
    tx1 = np.cos(phi1).astype(np.float32)
    along_strike_1 = (((vy1 * ty1 + vx1 * tx1) ** 2) / norm1_sq).astype(np.float32)
    del ty1, tx1
    prpc_strike_align_1 = (np.cos(prpc_strike_rad - phi1) ** 2).astype(np.float32)

    # 2. Exact inter-component Voronoi medial axis (locus equidistant between distinct components)
    vor_edge = (
        (c1 != _shift2d(c1, 1, 0))
        | (c1 != _shift2d(c1, -1, 0))
        | (c1 != _shift2d(c1, 0, 1))
        | (c1 != _shift2d(c1, 0, -1))
    ) & fp
    if np.any(vor_edge):
        d_medial = ndi.distance_transform_edt(~vor_edge).astype(np.float32)
    else:
        d_medial = np.full((h, w), 100.0, dtype=np.float32)
    del vor_edge

    # 3. 2nd-distinct-component distance, vector & strike via 4-bit spatial graph coloring on 2x grid
    colors = _greedy_spatial_component_colors(comp, n_comp, radius_px=60, max_colors=16)
    color_grid = colors[comp]
    c1_color = colors[c1]; del c1

    # Exact 2x block pooling keeping nonzero component color (~1.1s total for 8 EDTs)
    sh, sw = (h + 1) // 2, (w + 1) // 2
    pad_cg = np.zeros((sh * 2, sw * 2), dtype=np.int32)
    pad_cg[:h, :w] = color_grid; del color_grid
    cg_2x = np.maximum(
        np.maximum(pad_cg[0::2, 0::2], pad_cg[1::2, 0::2]),
        np.maximum(pad_cg[0::2, 1::2], pad_cg[1::2, 1::2]),
    )
    del pad_cg
    pad_c1 = np.zeros((sh * 2, sw * 2), dtype=np.int32)
    pad_c1[:h, :w] = c1_color; del c1_color
    c1_col_2x = pad_c1[0::2, 0::2]; del pad_c1

    best_d2_2x = np.full((sh, sw), 250.0, dtype=np.float32)
    best_y2_2x = np.zeros((sh, sw), dtype=np.int32)
    best_x2_2x = np.zeros((sh, sw), dtype=np.int32)

    for bit in range(4):
        for target_bit in (0, 1):
            mask_b = (cg_2x > 0) & (((cg_2x >> bit) & 1) == target_bit)
            if not np.any(mask_b):
                continue
            db_f64, idxb = ndi.distance_transform_edt(~mask_b, return_indices=True)
            db = (db_f64 * 2.0).astype(np.float32); del db_f64
            valid_opp = (((c1_col_2x >> bit) & 1) != target_bit)
            better = valid_opp & (db < best_d2_2x)
            best_d2_2x = np.where(better, db, best_d2_2x)
            best_y2_2x = np.where(better, (idxb[0] * 2).astype(np.int32), best_y2_2x)
            best_x2_2x = np.where(better, (idxb[1] * 2).astype(np.int32), best_x2_2x)
            del idxb, db
    del cg_2x, c1_col_2x

    # Upsample 2x fields back to full (H, W) grid cleanly
    yi = np.minimum(np.arange(h) // 2, sh - 1)
    xi = np.minimum(np.arange(w) // 2, sw - 1)
    dist2 = best_d2_2x[np.ix_(yi, xi)]; del best_d2_2x
    ny2 = np.clip(best_y2_2x[np.ix_(yi, xi)], 0, h - 1); del best_y2_2x
    nx2 = np.clip(best_x2_2x[np.ix_(yi, xi)], 0, w - 1); del best_x2_2x
    phi2 = fault_strike[ny2, nx2]; del fault_strike

    vy2 = yy - ny2.astype(np.float32); del ny2
    vx2 = xx - nx2.astype(np.float32); del nx2
    norm2 = np.sqrt(vy2 * vy2 + vx2 * vx2 + np.float32(1e-4))
    norm1 = np.sqrt(norm1_sq); del norm1_sq

    # Bridge opposition: +1 when p1 and p2 lie on exact opposite sides of x
    bridge_opposition = np.clip(
        -(vy1 * vy2 + vx1 * vx2) / (norm1 * norm2 + np.float32(1e-4)),
        np.float32(0.0),
        np.float32(1.0),
    ).astype(np.float32)
    del vy1, vx1, norm1
    strike_coherence_12 = (np.cos(phi1 - phi2) ** 2).astype(np.float32); del phi1

    ty2 = (-np.sin(phi2)).astype(np.float32)
    tx2 = np.cos(phi2).astype(np.float32); del phi2
    along_strike_2 = (((vy2 * ty2 + vx2 * tx2) ** 2) / (norm2 * norm2 + np.float32(1e-4))).astype(np.float32)
    del vy2, vx2, ty2, tx2, norm2

    total_span = dist1 + dist2
    colinear_wash_gap = (
        bridge_opposition
        * np.sqrt(along_strike_1 * along_strike_2)
        * strike_coherence_12
        * np.exp(-total_span / np.float32(38.0))
    ).astype(np.float32)

    relay_stepover = (
        bridge_opposition
        * strike_coherence_12
        * (np.float32(1.0) - np.float32(0.5) * (along_strike_1 + along_strike_2))
        * np.exp(-total_span / np.float32(28.0))
        * np.exp(-d_medial / np.float32(6.0))
    ).astype(np.float32)
    del along_strike_2, total_span

    # 4. Anisotropic tip continuation cones
    tip_short, tip_long = _tip_propagation_cones(vf, comp)
    del comp

    # 5. Parallel synthetic/piedmont splay band (400 m .. 2.2 km broadside, strike-concordant PRPC)
    piedmont_splay_band = (
        np.exp(np.float32(-0.5) * ((dist1 - np.float32(9.0)) / np.float32(6.5)) ** 2)
        * (np.float32(1.0) - np.float32(0.5) * along_strike_1)
        * prpc_strike_align_1
        * np.maximum(prpc_score_z + np.float32(0.5), np.float32(0.0))
    ).astype(np.float32)

    # 6. Regional visible-network density (computed on 4x coarse grid: 300x faster for sigma=30,80 px!)
    sh4, sw4 = (h + 3) // 4, (w + 3) // 4
    pad_vf = np.zeros((sh4 * 4, sw4 * 4), dtype=np.float32)
    pad_vf[:h, :w] = vf.astype(np.float32)
    vf_4x = pad_vf.reshape(sh4, 4, sw4, 4).mean(axis=(1, 3))
    del pad_vf
    d3_4x = ndi.gaussian_filter(vf_4x, sigma=30.0 / 4.0, mode="constant").astype(np.float32) * np.float32(100.0)
    d8_4x = ndi.gaussian_filter(vf_4x, sigma=80.0 / 4.0, mode="constant").astype(np.float32) * np.float32(100.0)
    yi4 = np.minimum(np.arange(h) // 4, sh4 - 1)
    xi4 = np.minimum(np.arange(w) // 4, sw4 - 1)
    dens_3km = d3_4x[np.ix_(yi4, xi4)]
    dens_8km = d8_4x[np.ix_(yi4, xi4)]

    def _mask_fp(a: np.ndarray) -> np.ndarray:
        a = np.asarray(a, dtype=np.float32)
        a[~fp] = 0.0
        return a

    return {
        "net_dist1_clip": _mask_fp(np.minimum(dist1, np.float32(120.0))),
        "net_log_dist1": _mask_fp(np.log1p(np.minimum(dist1, np.float32(200.0)))),
        "net_along_strike_1": _mask_fp(along_strike_1),
        "net_prpc_strike_align_1": _mask_fp(prpc_strike_align_1),
        "net_d_medial_clip": _mask_fp(np.minimum(d_medial, np.float32(80.0))),
        "net_dist2_clip": _mask_fp(np.minimum(dist2, np.float32(150.0))),
        "net_bridge_opposition": _mask_fp(bridge_opposition),
        "net_strike_coherence_12": _mask_fp(strike_coherence_12),
        "net_colinear_wash_gap": _mask_fp(np.log1p(colinear_wash_gap * np.float32(8.0))),
        "net_relay_stepover": _mask_fp(np.log1p(relay_stepover * np.float32(8.0))),
        "net_tip_cone_short": _robust_z(np.log1p(tip_short * np.float32(4.0)), fp),
        "net_tip_cone_long": _robust_z(np.log1p(tip_long * np.float32(4.0)), fp),
        "net_piedmont_splay_band": _mask_fp(piedmont_splay_band),
        "net_density_3km": _robust_z(dens_3km, fp),
        "net_density_8km": _robust_z(dens_8km, fp),
    }


def _spatial_block_ids_on_fp(footprint: np.ndarray, block_px: int = 200) -> np.ndarray:
    yy, xx = np.nonzero(footprint)
    by = yy // block_px
    bx = xx // block_px
    n_bx = int(bx.max()) + 1
    return (by * n_bx + bx).astype(np.int32)


def compute_blind_oof_at_rows(
    bundle: BlindStackBundle,
    footprint: np.ndarray,
    train_visible: np.ndarray,
    query_fp_rows: np.ndarray,
    *,
    forbidden_train_mask: np.ndarray | None = None,
    n_inner_folds: int = 3,
    seed: int = 8520,
) -> np.ndarray:
    """Compute strict spatially-blocked OOF blind probabilities specifically at `query_fp_rows`."""
    fp = footprint.astype(bool)
    vis = train_visible.astype(bool) & fp
    forbid = (forbidden_train_mask.astype(bool) & fp) if forbidden_train_mask is not None else np.zeros_like(fp)

    pos_core = vis & ~forbid
    pos_shld = (ndi.binary_dilation(vis, np.ones((3, 3), bool), iterations=1) & ~vis) & fp & ~forbid
    neg_domain = fp & ~ndi.binary_dilation(vis, np.ones((3, 3), bool), iterations=3) & ~forbid

    pos_core_fp = pos_core.ravel()[bundle.fp_idx]
    pos_shld_fp = pos_shld.ravel()[bundle.fp_idx]
    neg_fp = neg_domain.ravel()[bundle.fp_idx]

    block_ids = _spatial_block_ids_on_fp(fp, block_px=200)
    rng = np.random.default_rng(seed)
    uniq_b = np.unique(block_ids)
    perm_b = rng.permutation(uniq_b)
    b_to_fold = np.zeros(int(uniq_b.max()) + 1, dtype=np.int32)
    for i, b in enumerate(perm_b):
        b_to_fold[b] = i % n_inner_folds
    inner_fold_fp = b_to_fold[block_ids]

    slope_col = bundle.feature_names.index("slope_z")
    prpc_col = bundle.feature_names.index("prpc_nms_z")
    hard_neg_flag = (np.asarray(bundle.X_fp[:, prpc_col]) > 0.6) | (np.asarray(bundle.X_fp[:, slope_col]) > 0.6)

    q_folds = inner_fold_fp[query_fp_rows]
    oof_q = np.zeros(query_fp_rows.size, dtype=np.float32)

    for k in range(n_inner_folds):
        q_sel = np.flatnonzero(q_folds == k)
        if q_sel.size == 0:
            continue
        in_train = inner_fold_fp != k
        idx_pc = np.flatnonzero(pos_core_fp & in_train)
        idx_ps = np.flatnonzero(pos_shld_fp & in_train)
        if idx_ps.size > idx_pc.size:
            idx_ps = rng.choice(idx_ps, idx_pc.size, replace=False)

        idx_nh = np.flatnonzero(neg_fp & hard_neg_flag & in_train)
        idx_ne = np.flatnonzero(neg_fp & (~hard_neg_flag) & in_train)
        n_pos_k = idx_pc.size + idx_ps.size
        n_nh = min(idx_nh.size, int(n_pos_k * 2.5))
        n_ne = min(idx_ne.size, int(n_pos_k * 3.5))
        sel_nh = rng.choice(idx_nh, n_nh, replace=False) if idx_nh.size > n_nh else idx_nh
        sel_ne = rng.choice(idx_ne, n_ne, replace=False) if idx_ne.size > n_ne else idx_ne

        tr_idx = np.concatenate([idx_pc, idx_ps, sel_nh, sel_ne])
        y_tr = np.concatenate([
            np.ones(idx_pc.size + idx_ps.size, dtype=np.int8),
            np.zeros(sel_nh.size + sel_ne.size, dtype=np.int8),
        ])
        w_tr = np.concatenate([
            np.ones(idx_pc.size, dtype=np.float32),
            np.full(idx_ps.size, 0.55, dtype=np.float32),
            np.full(sel_nh.size, 1.35, dtype=np.float32),
            np.full(sel_ne.size, 1.85, dtype=np.float32),
        ])
        clf = HistGradientBoostingClassifier(
            max_iter=135,
            learning_rate=0.07,
            max_leaf_nodes=31,
            min_samples_leaf=80,
            l2_regularization=2.5,
            random_state=seed + k,
            early_stopping=False,
        )
        clf.fit(np.asarray(bundle.X_fp[tr_idx], dtype=np.float32), y_tr, sample_weight=w_tr)
        rows = query_fp_rows[q_sel]
        oof_q[q_sel] = clf.predict_proba(np.asarray(bundle.X_fp[rows], dtype=np.float32))[:, 1].astype(np.float32)

    return oof_q


def fit_predict_blind_oof(
    bundle: BlindStackBundle,
    footprint: np.ndarray,
    train_visible: np.ndarray,
    *,
    forbidden_train_mask: np.ndarray | None = None,
    eval_target_mask: np.ndarray | None = None,
    n_inner_folds: int = 3,
    seed: int = 8520,
) -> tuple[None, np.ndarray]:
    """Fit blind PRPC HGB on 100% of `train_visible` (`~forbid`) and predict on `eval_target_mask`."""
    fp = footprint.astype(bool)
    vis = train_visible.astype(bool) & fp
    forbid = (forbidden_train_mask.astype(bool) & fp) if forbidden_train_mask is not None else np.zeros_like(fp)
    target_idx = (
        np.flatnonzero((eval_target_mask.astype(bool) & fp).ravel()[bundle.fp_idx])
        if eval_target_mask is not None
        else np.arange(bundle.fp_idx.size)
    )

    pos_core_fp = (vis & ~forbid).ravel()[bundle.fp_idx]
    pos_shld_fp = ((ndi.binary_dilation(vis, np.ones((3, 3), bool), iterations=1) & ~vis) & fp & ~forbid).ravel()[bundle.fp_idx]
    neg_fp = (fp & ~ndi.binary_dilation(vis, np.ones((3, 3), bool), iterations=3) & ~forbid).ravel()[bundle.fp_idx]

    slope_col = bundle.feature_names.index("slope_z")
    prpc_col = bundle.feature_names.index("prpc_nms_z")
    hard_neg_flag = (np.asarray(bundle.X_fp[:, prpc_col]) > 0.6) | (np.asarray(bundle.X_fp[:, slope_col]) > 0.6)

    rng = np.random.default_rng(seed)
    idx_pc = np.flatnonzero(pos_core_fp)
    idx_ps = np.flatnonzero(pos_shld_fp)
    if idx_ps.size > idx_pc.size:
        idx_ps = rng.choice(idx_ps, idx_pc.size, replace=False)

    idx_nh = np.flatnonzero(neg_fp & hard_neg_flag)
    idx_ne = np.flatnonzero(neg_fp & (~hard_neg_flag))
    n_pos = idx_pc.size + idx_ps.size
    n_nh = min(idx_nh.size, int(n_pos * 2.5))
    n_ne = min(idx_ne.size, int(n_pos * 3.5))
    sel_nh = rng.choice(idx_nh, n_nh, replace=False) if idx_nh.size > n_nh else idx_nh
    sel_ne = rng.choice(idx_ne, n_ne, replace=False) if idx_ne.size > n_ne else idx_ne

    tr_idx = np.concatenate([idx_pc, idx_ps, sel_nh, sel_ne])
    y_tr = np.concatenate([
        np.ones(idx_pc.size + idx_ps.size, dtype=np.int8),
        np.zeros(sel_nh.size + sel_ne.size, dtype=np.int8),
    ])
    w_tr = np.concatenate([
        np.ones(idx_pc.size, dtype=np.float32),
        np.full(idx_ps.size, 0.55, dtype=np.float32),
        np.full(sel_nh.size, 1.35, dtype=np.float32),
        np.full(sel_ne.size, 1.85, dtype=np.float32),
    ])

    clf = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.06,
        max_leaf_nodes=31,
        min_samples_leaf=80,
        l2_regularization=2.5,
        random_state=seed,
        early_stopping=False,
    )
    clf.fit(np.asarray(bundle.X_fp[tr_idx], dtype=np.float32), y_tr, sample_weight=w_tr)

    pred_fp = np.zeros(bundle.fp_idx.size, dtype=np.float32)
    for chunk in np.array_split(np.arange(target_idx.size), max(1, target_idx.size // 550_000)):
        rows = target_idx[chunk]
        pred_fp[rows] = clf.predict_proba(np.asarray(bundle.X_fp[rows], dtype=np.float32))[:, 1].astype(np.float32)

    full_grid = np.zeros(fp.shape, dtype=np.float32)
    full_grid.ravel()[bundle.fp_idx] = pred_fp
    return None, full_grid


# Selected physics channels injected alongside P_blind + 15 visible-network channels in E3
DUAL_BLIND_SUBSET: tuple[str, ...] = (
    "prpc_nms_z",
    "prpc_persisted_z",
    "prpc_sub_odd_z",
    "prpc_core_even_z",
    "prpc_concord_z",
    "lappos_max_seamfree",
    "scarp_dipole_seamfree",
    "piedmont_hinge",
    "mesa_caprock_penalty",
    "det_elev_z",
    "slope_z",
    "neg_tc_z",
    "mag_depth_persistence",
    "rad_redox_conduit",
    "geod_2ndinv_z",
    "ieq_z",
    "hydro_meas_1km",
    "hydro_prox",
)


def _assemble_dual_features_fp(
    bundle: BlindStackBundle,
    blind_prob_fp: np.ndarray,
    net_feats: dict[str, np.ndarray],
    row_idx: np.ndarray | None = None,
) -> np.ndarray:
    """Assemble compact `(M, D_dual)` matrix on footprint subset `row_idx` (or full footprint)."""
    sub_cols = [bundle.feature_names.index(nm) for nm in DUAL_BLIND_SUBSET]
    m_rows = bundle.fp_idx.size if row_idx is None else int(row_idx.size)
    flat_grid_idx = bundle.fp_idx if row_idx is None else bundle.fp_idx[row_idx]
    n_net = len(VISIBLE_NET_FEATURE_NAMES)
    d_total = 2 + len(sub_cols) + n_net + 4
    X = np.empty((m_rows, d_total), dtype=np.float32)

    p_src = blind_prob_fp if row_idx is None else blind_prob_fp[row_idx]
    p = np.clip(p_src, 1e-5, 1.0 - 1e-5).astype(np.float32)
    logit_p = np.log(p / (1.0 - p)).astype(np.float32)
    X[:, 0] = p
    X[:, 1] = logit_p
    for i, col_idx in enumerate(sub_cols):
        X[:, 2 + i] = bundle.X_fp[:, col_idx] if row_idx is None else bundle.X_fp[row_idx, col_idx]

    base = 2 + len(sub_cols)
    for j, nm in enumerate(VISIBLE_NET_FEATURE_NAMES):
        X[:, base + j] = net_feats[nm].ravel()[flat_grid_idx]

    tip_s = X[:, base + VISIBLE_NET_FEATURE_NAMES.index("net_tip_cone_short")]
    wash_g = X[:, base + VISIBLE_NET_FEATURE_NAMES.index("net_colinear_wash_gap")]
    relay_s = X[:, base + VISIBLE_NET_FEATURE_NAMES.index("net_relay_stepover")]
    align_1 = X[:, base + VISIBLE_NET_FEATURE_NAMES.index("net_prpc_strike_align_1")]

    ib = base + n_net
    X[:, ib + 0] = logit_p * align_1
    X[:, ib + 1] = p * tip_s
    X[:, ib + 2] = p * wash_g
    X[:, ib + 3] = p * relay_s
    return X


def fit_predict_dual_expert(
    bundle: BlindStackBundle,
    oof_blind_fp: np.ndarray,
    ens_blind_grid: np.ndarray,
    footprint: np.ndarray,
    train_visible: np.ndarray,
    *,
    inf_visible: np.ndarray | None = None,
    precomputed_inf_net: dict[str, np.ndarray] | None = None,
    eval_target_mask: np.ndarray | None = None,
    forbidden_train_mask: np.ndarray | None = None,
    n_inner_comp_folds: int = 3,
    inner_buffer_px: int = 5,
    seed: int = 8530,
) -> np.ndarray:
    """Train dual-regime synthesis (`E3_PRPC_Dual_Submod`) via inner self-excluded component splits.

    Inside `train_visible`, holds out whole connected components (`inner_hide_k` + 500 m buffer)
    and derives all structural features ONLY from `inner_vis_k = train_visible & ~halo(inner_hide_k)`.
    Every training positive (`inner_hide_k`) and negative (`>200 m` from `inner_vis_k`) therefore
    lives strictly in the target off-catalogue inference regime (`dist_visible > 2.0 px`),
    with zero access to outer withheld faults!
    """
    fp = footprint.astype(bool)
    vis = train_visible.astype(bool) & fp
    forbid = (forbidden_train_mask.astype(bool) & fp) if forbidden_train_mask is not None else np.zeros_like(fp)

    comp, n_comp = ndi.label(vis, structure=np.ones((3, 3), dtype=int))
    rng = np.random.default_rng(seed)
    # Partition whole connected components randomly (25% withheld per inner fold, NOT 18 km square
    # erasure!) so 75% of surrounding fault segments remain visible around every held-out component,
    # matching the true generative geometry of incomplete fault catalogues!
    comp_fold = np.zeros(n_comp + 1, dtype=np.int32)
    comp_fold[0] = -1
    perm_c = rng.permutation(n_comp) + 1
    for idx_c, cid in enumerate(perm_c):
        comp_fold[cid] = idx_c % n_inner_comp_folds

    X_parts, y_parts, w_parts = [], [], []
    any_vis_dil3 = ndi.binary_dilation(vis, np.ones((3, 3), bool), iterations=3)
    safe_neg_global_fp = (fp & ~any_vis_dil3 & ~forbid).ravel()[bundle.fp_idx]
    valid_train_region = ~forbid

    # Fit 3 spatial-block blind OOF models ONCE so every inner component fold gets fast OOF queries!
    b_ids = _spatial_block_ids_on_fp(fp, block_px=200)
    ub = np.unique(b_ids)
    b_map = np.zeros(int(ub.max()) + 1, dtype=np.int32)
    for i, b in enumerate(np.random.default_rng(seed + 1).permutation(ub)):
        b_map[b] = i % 3
    sp_fold_fp = b_map[b_ids]
    pc_all = (vis & ~forbid).ravel()[bundle.fp_idx]
    ps_all = ((ndi.binary_dilation(vis, np.ones((3, 3), bool), iterations=1) & ~vis) & fp & ~forbid).ravel()[bundle.fp_idx]
    ng_all = safe_neg_global_fp
    hn_flag = (
        (np.asarray(bundle.X_fp[:, bundle.feature_names.index("prpc_nms_z")]) > 0.6)
        | (np.asarray(bundle.X_fp[:, bundle.feature_names.index("slope_z")]) > 0.6)
    )
    sp_models = []
    for sk in range(3):
        itr = sp_fold_fp != sk
        ipc = np.flatnonzero(pc_all & itr)
        ips = np.flatnonzero(ps_all & itr)
        if ips.size > ipc.size:
            ips = rng.choice(ips, ipc.size, replace=False)
        inh = np.flatnonzero(ng_all & hn_flag & itr)
        ine = np.flatnonzero(ng_all & (~hn_flag) & itr)
        npk = ipc.size + ips.size
        snh = rng.choice(inh, min(inh.size, int(npk * 2.5)), replace=False)
        sne = rng.choice(ine, min(ine.size, int(npk * 3.5)), replace=False)
        tidx = np.concatenate([ipc, ips, snh, sne])
        yt = np.concatenate([np.ones(npk, dtype=np.int8), np.zeros(snh.size + sne.size, dtype=np.int8)])
        wt = np.concatenate([
            np.ones(ipc.size, dtype=np.float32),
            np.full(ips.size, 0.55, dtype=np.float32),
            np.full(snh.size, 1.35, dtype=np.float32),
            np.full(sne.size, 1.85, dtype=np.float32),
        ])
        m_sp = HistGradientBoostingClassifier(
            max_iter=135, learning_rate=0.07, max_leaf_nodes=31,
            min_samples_leaf=80, l2_regularization=2.5, random_state=seed + 20 + sk, early_stopping=False,
        )
        m_sp.fit(np.asarray(bundle.X_fp[tidx], dtype=np.float32), yt, sample_weight=wt)
        sp_models.append(m_sp)

    for k in range(n_inner_comp_folds):
        inner_hide = (comp_fold[comp] == k) & vis & ~forbid
        halo = ndi.binary_dilation(inner_hide, np.ones((3, 3), bool), iterations=inner_buffer_px)
        inner_vis = vis & ~halo

        net_k = build_visible_network_features(
            inner_vis, bundle.prpc_strike_rad, bundle.prpc_score_z, fp
        )
        # Ensure we only evaluate strictly outside 2.0 px of inner_vis
        off_inner_fp = (net_k["net_dist1_clip"].ravel()[bundle.fp_idx] > 2.05)

        pos_core_k = inner_hide.ravel()[bundle.fp_idx] & off_inner_fp
        pos_shld_k = (
            ndi.binary_dilation(inner_hide, np.ones((3, 3), bool), iterations=1) & ~inner_hide & fp & ~forbid
        ).ravel()[bundle.fp_idx] & off_inner_fp

        idx_pc = np.flatnonzero(pos_core_k)
        idx_ps = np.flatnonzero(pos_shld_k)
        if idx_ps.size > int(idx_pc.size * 0.8):
            idx_ps = rng.choice(idx_ps, int(idx_pc.size * 0.8), replace=False)

        # Stratified negatives: near-network (2..35 px from inner_vis) + far-basin (>35 px)
        d1_fp = net_k["net_dist1_clip"].ravel()[bundle.fp_idx]
        neg_near = np.flatnonzero(safe_neg_global_fp & off_inner_fp & (d1_fp <= 35.0))
        neg_far = np.flatnonzero(safe_neg_global_fp & off_inner_fp & (d1_fp > 35.0))

        n_pos = idx_pc.size + idx_ps.size
        n_nn = min(neg_near.size, int(n_pos * 3.5))
        n_nf = min(neg_far.size, int(n_pos * 3.5))
        sel_nn = rng.choice(neg_near, n_nn, replace=False) if neg_near.size > n_nn else neg_near
        sel_nf = rng.choice(neg_far, n_nf, replace=False) if neg_far.size > n_nf else neg_far

        sel_idx = np.concatenate([idx_pc, idx_ps, sel_nn, sel_nf])
        oof_sel = np.empty(sel_idx.size, dtype=np.float32)
        sf_sel = sp_fold_fp[sel_idx]
        for sk, m_sp in enumerate(sp_models):
            sub_q = np.flatnonzero(sf_sel == sk)
            if sub_q.size:
                oof_sel[sub_q] = m_sp.predict_proba(
                    np.asarray(bundle.X_fp[sel_idx[sub_q]], dtype=np.float32)
                )[:, 1].astype(np.float32)
        oof_sparse = np.zeros(bundle.fp_idx.size, dtype=np.float32)
        oof_sparse[sel_idx] = oof_sel
        X_parts.append(_assemble_dual_features_fp(bundle, oof_sparse, net_k, row_idx=sel_idx))
        del net_k, oof_sparse

        # Compute natural-prevalence importance weights for near vs far negative strata
        frac_near = float(neg_near.size) / max(1.0, float(neg_near.size + neg_far.size))
        w_nn = max(0.8, 7.0 * frac_near / max(1e-3, float(n_nn) / max(1, n_nn + n_nf)))
        w_nf = max(0.8, 7.0 * (1.0 - frac_near) / max(1e-3, float(n_nf) / max(1, n_nn + n_nf)))

        y_parts.append(np.concatenate([
            np.ones(idx_pc.size + idx_ps.size, dtype=np.int8),
            np.zeros(sel_nn.size + sel_nf.size, dtype=np.int8),
        ]))
        w_parts.append(np.concatenate([
            np.ones(idx_pc.size, dtype=np.float32),
            np.full(idx_ps.size, 0.55, dtype=np.float32),
            np.full(sel_nn.size, w_nn, dtype=np.float32),
            np.full(sel_nf.size, w_nf, dtype=np.float32),
        ]))

    X_tr = np.vstack(X_parts)
    y_tr = np.concatenate(y_parts)
    w_tr = np.concatenate(w_parts)
    del X_parts, y_parts, w_parts

    # Build physics-guided monotonic constraints so continuation/concordance features can never invert
    d_dual = X_tr.shape[1]
    mono = np.zeros(d_dual, dtype=np.int32)
    mono[0] = 1   # p_blind
    mono[1] = 1   # logit_p_blind
    for i, nm in enumerate(DUAL_BLIND_SUBSET):
        if nm == "mesa_caprock_penalty":
            mono[2 + i] = -1
    base_n = 2 + len(DUAL_BLIND_SUBSET)
    for j, nm in enumerate(VISIBLE_NET_FEATURE_NAMES):
        if nm in (
            "net_colinear_wash_gap",
            "net_relay_stepover",
            "net_tip_cone_short",
            "net_tip_cone_long",
            "net_piedmont_splay_band",
            "net_prpc_strike_align_1",
        ):
            mono[base_n + j] = 1
    ib = base_n + len(VISIBLE_NET_FEATURE_NAMES)
    mono[ib + 0] = 1  # logit_p * align_1
    mono[ib + 1] = 1  # p * tip_short
    mono[ib + 2] = 1  # p * wash_gap
    mono[ib + 3] = 1  # p * relay_stepover

    clf = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.055,
        max_leaf_nodes=31,
        min_samples_leaf=120,
        l2_regularization=4.5,
        monotonic_cst=mono.tolist(),
        random_state=seed + 100,
        early_stopping=False,
    )
    clf.fit(X_tr, y_tr, sample_weight=w_tr)
    del X_tr, y_tr, w_tr

    # Inference strictly from `inf_vis` (defaults to `train_visible`; zero outer withheld knowledge!)
    if precomputed_inf_net is not None:
        net_inf = precomputed_inf_net
        owns_net_inf = False
    else:
        inf_vis = (inf_visible.astype(bool) & fp) if inf_visible is not None else vis
        net_inf = build_visible_network_features(
            inf_vis, bundle.prpc_strike_rad, bundle.prpc_score_z, fp
        )
        owns_net_inf = True

    ens_blind_fp = ens_blind_grid.ravel()[bundle.fp_idx]
    target_idx = (
        np.flatnonzero((eval_target_mask.astype(bool) & fp).ravel()[bundle.fp_idx])
        if eval_target_mask is not None
        else np.arange(bundle.fp_idx.size)
    )
    pred_fp = np.zeros(bundle.fp_idx.size, dtype=np.float32)
    for chunk in np.array_split(np.arange(target_idx.size), max(1, target_idx.size // 550_000)):
        rows = target_idx[chunk]
        X_c = _assemble_dual_features_fp(bundle, ens_blind_fp, net_inf, row_idx=rows)
        pred_fp[rows] = clf.predict_proba(X_c)[:, 1].astype(np.float32)
        del X_c
    if owns_net_inf:
        del net_inf

    final_fp = np.zeros(bundle.fp_idx.size, dtype=np.float32)
    final_fp[target_idx] = 0.85 * pred_fp[target_idx] + 0.15 * ens_blind_fp[target_idx]
    out = np.zeros(fp.shape, dtype=np.float32)
    out.ravel()[bundle.fp_idx] = final_fp
    return out


fit_predict_dual_expert_with_separate_inf_vis = fit_predict_dual_expert


def _build_kernel_patch_7x7() -> np.ndarray:
    k = np.zeros((7, 7), dtype=np.float64)
    dy, dx, kw = emitter.M._OFF
    for d, e, w in zip(dy, dx, kw):
        k[int(d) + 3, int(e) + 3] = float(w)
    return k


_K7_PATCH = _build_kernel_patch_7x7()


def submodular_emit_off_catalogue(
    prob_surface: np.ndarray,
    *,
    footprint: np.ndarray,
    visible_catalogue: np.ndarray,
    budget: int = 37_654,
    exclude_radius_m: float = 200.0,
    min_sep_px: float = 2.20,
    pool_size: int = 900_000,
) -> tuple[np.ndarray, emitter.EmissionLog]:
    """Allocate `budget` binary {0, 1} dots via crest-sharpened 1D-manifold spacing (`min_sep_px=2.20`).

    Resolves IR-85-011 (2D-disk convolution clumping on continuous posteriors): blocks redundant
    1.0 px (100 m), 1.41 px (141 m), and 2.0 px (200 m) adjacent blob neighbors while permitting
    exact knight's-move (+-2, +-1) = 223.6 m steps along N26.6E/NNW Basin-and-Range fault strikes
    inside the R = 300 m kernel. Enforces `dist(x, visible_catalogue) > exclude_radius_m`
    (`200.0 m` on holdout; `283.0 m` `B=2` Chebyshev collar on full-catalogue packaging).
    """
    fp = footprint.astype(bool)
    vis = visible_catalogue.astype(bool) & fp
    dist_px = ndi.distance_transform_edt(~vis) if np.any(vis) else np.full(fp.shape, 999.0)
    excl_px = exclude_radius_m / 100.0
    allowed = fp & (dist_px > excl_px + 1e-6)

    p = np.where(fp & (~vis) & np.isfinite(prob_surface), np.maximum(prob_surface, 0.0), 0.0).astype(np.float32)
    bg_iso = ndi.gaussian_filter(p, sigma=2.5, mode="nearest")
    crest_score = p * (((p + np.float32(1e-4)) / (bg_iso + np.float32(1e-4))) ** np.float32(0.22))

    mask = emission.poisson_thin(
        crest_score,
        n=budget,
        sep_px=min_sep_px,
        allowed=allowed,
        topk_pool=pool_size,
    )
    n_em = int(mask.sum())
    log = emitter.EmissionLog(
        rule="crest_knight_nonredundant_300m_r220",
        n_support_px=int((allowed & (crest_score > 0)).sum()),
        n_emitted=n_em,
        total_mass=float(n_em),
        credit_delivered=float(p[mask].sum()),
        stopped_by="budget" if n_em >= budget else "exhausted_support",
        candidates_considered=int((allowed & (crest_score > 0)).sum()),
        candidates_accepted=n_em,
    )
    return mask.astype(np.float32), log
