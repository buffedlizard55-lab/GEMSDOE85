"""58-Channel H85-TVFV Geophysical, Geomorphic & Geothermal Fault-Valve Tensor Engine.

Strict zero-leakage guarantees:
  1. ZERO prior submission rasters or sibling predictions are ever read or referenced.
  2. ZERO SGMC pre-Quaternary bedrock map contacts are used.
  3. ZERO fault-catalogue pixels, distances, or coordinates enter the static 58-channel matrix.
  4. Memory-mapped float32 storage keeps peak resident RAM < 900 MB on 3.8 GiB hardware.
"""
from __future__ import annotations

import csv
import gc
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import convolve, gaussian_filter, maximum_filter, uniform_filter

from .paths import EXTERNAL_REPO_DIR, resolve_raw_dir, resolve_work_dir

STATIC_FEATURE_SPECS: tuple[tuple[str, str], ...] = (
    # Domain I: 90-deg-Corrected 1m USGS 3DEP LiDAR Micro-Scarp Dipole & Fluvial De-Gullier (13 ch)
    ("d1_lid_valid", "D1_lidar1m"),
    ("d1_lid_step_max", "D1_lidar1m"),
    ("d1_lid_ex_max", "D1_lidar1m"),
    ("d1_lid_dipole_crest_toe", "D1_lidar1m"),
    ("d1_lid_tect_vs_fluv", "D1_lidar1m"),
    ("d1_lid_piedmont_step", "D1_lidar1m"),
    ("d1_lid_antislope_graben", "D1_lidar1m"),
    ("d1_lid_coh100", "D1_lidar1m"),
    ("d1_lid_contour_align_90fix", "D1_lidar1m"),
    ("d1_lid_step_anom15", "D1_lidar1m"),
    ("d1_lid_step_max5", "D1_lidar1m"),
    ("d1_lid_worm_1100m", "D1_lidar1m"),
    ("d1_lid_openness_hires", "D1_lidar1m"),
    # Domain II: 100%-Coverage 10m USGS 3DEP Micro-Topography & Seam-Free Cross-Scale Harmonizer (14 ch)
    ("d2_dem10_onesided", "D2_dem10m"),
    ("d2_dem10_onesided3", "D2_dem10m"),
    ("d2_dem10_steep_ratio", "D2_dem10m"),
    ("d2_dem10_curv_absmax", "D2_dem10m"),
    ("d2_dem10_resid_range", "D2_dem10m"),
    ("d2_dem10_resid_std", "D2_dem10m"),
    ("d2_dem10_hgm20", "D2_dem10m"),
    ("d2_dem10_hgm50", "D2_dem10m"),
    ("d2_dem10_hgm200", "D2_dem10m"),
    ("d2_dem10_slope_std", "D2_dem10m"),
    ("d2_dem10_piedmont_step", "D2_dem10m"),
    ("d2_dem10_worm_1100m", "D2_dem10m"),
    ("d2_seamfree_scarp_qnorm", "D2_dem10m"),
    ("d2_seamfree_worm_1300m", "D2_dem10m"),
    # Domain III: 3D Polar-Signed Hanging-Wall Dipole Coherence & Multi-Altitude Potential Fields (14 ch)
    ("d3_hw_base_dipole", "D3_geopotential_dipole"),
    ("d3_hw_grav_dipole", "D3_geopotential_dipole"),
    ("d3_hw_triple_concordance", "D3_geopotential_dipole"),
    ("d3_log_tmi_hg", "D3_geopotential_dipole"),
    ("d3_tmi_vg", "D3_geopotential_dipole"),
    ("d3_mag_tc", "D3_geopotential_dipole"),
    ("d3_rtp_hp15", "D3_geopotential_dipole"),
    ("d3_up150_grad", "D3_geopotential_dipole"),
    ("d3_fft_up500_persist", "D3_geopotential_dipole"),
    ("d3_grav_slope_hp", "D3_geopotential_dipole"),
    ("d3_verduzco_grav_tilt", "D3_geopotential_dipole"),
    ("d3_gallardo_crossgrad", "D3_geopotential_dipole"),
    ("d3_worm_mag_grav_1500m", "D3_geopotential_dipole"),
    ("d3_mt_cond_grad_safe36", "D3_geopotential_dipole"),
    # Domain IV: Local Strain Tensor, Seismicity & Orientation Observables (9 ch; regional stress fit OOF!)
    ("d4_strain_2ndinv", "D4_stress_strain"),
    ("d4_strain_shear", "D4_stress_strain"),
    ("d4_strain_dilate", "D4_stress_strain"),
    ("d4_strain_kostrov_ratio", "D4_stress_strain"),
    ("d4_seismic_ieq_log", "D4_stress_strain"),
    ("d4_seismic_deq_inv", "D4_stress_strain"),
    ("d4_elev_slope_raw", "D4_stress_strain"),
    ("d4_elev_slope_anom15", "D4_stress_strain"),
    ("d4_det_elev_lap7", "D4_stress_strain"),
    # Domain V: Sibson Fault-Valve Geothermal Enthalpy, Geothermometry, Borehole Heat Flow & Alteration (8 ch)
    ("d5_hf_convective_1km", "D5_geothermal_valve"),
    ("d5_hf_convective_3km", "D5_geothermal_valve"),
    ("d5_gdr_geotherm_upflow_1km", "D5_geothermal_valve"),
    ("d5_gdr_diseq_updip", "D5_geothermal_valve"),
    ("d5_probes2m_and_paleo_vents", "D5_geothermal_valve"),
    ("d5_potassic_k_th_alteration", "D5_geothermal_valve"),
    ("d5_hydro_demag_trough", "D5_geothermal_valve"),
    ("d5_road_valley_berm_flag", "D5_geothermal_valve"),
)

FEATURE_NAMES: tuple[str, ...] = tuple(n for n, _ in STATIC_FEATURE_SPECS)
FEATURE_DOMAINS: dict[str, str] = dict(STATIC_FEATURE_SPECS)
# Slope-confounded raw channels excluded from Expert A (Piedmont & Geothermal Fault-Valve Expert)
RAW_MOUNTAIN_SLOPE_COLS = frozenset({"d4_elev_slope_raw", "d1_lid_ex_max", "d2_dem10_resid_range", "d2_dem10_resid_std"})


def _dequant_lidar(band_name: str, q_arr: np.ndarray, q_meta: dict[str, Any]) -> np.ndarray:
    xmax, mode = q_meta[band_name]
    u = np.clip((q_arr.astype(np.float32) - 1.0) / 254.0, 0.0, 1.0)
    val = (u * u) * float(xmax) if mode == "sqrt" else u * float(xmax)
    return np.where(q_arr > 0, val, 0.0).astype(np.float32)


def compute_strike_worm_2d(
    edge_2d: np.ndarray, valid_2d: np.ndarray, half_len: int = 6, flank: int = 3
) -> np.ndarray:
    """6-azimuth strike-coherent line integral minus bilateral cross-strike flanks."""
    x = np.where(valid_2d, np.nan_to_num(edge_2d, nan=0.0, posinf=0.0, neginf=0.0), 0.0).astype(np.float32)
    loc_mean = uniform_filter(x, size=31)
    loc_sq = uniform_filter(x * x, size=31)
    loc_std = np.sqrt(np.maximum(loc_sq - loc_mean * loc_mean, 1e-6))
    z = np.clip((x - loc_mean) / (loc_std + 0.25), -3.0, 6.0)
    del loc_mean, loc_sq, loc_std

    best = np.full(x.shape, -1e9, dtype=np.float32)
    L = int(half_len)
    for deg in (0, 30, 60, 90, 120, 150):
        rad = np.radians(deg)
        dy_s, dx_s = np.sin(rad), np.cos(rad)
        py_s, px_s = -dx_s, dy_s
        k_mat = np.zeros((2 * L + 3, 2 * L + 3), dtype=np.float32)
        c = L + 1
        w0 = 1.0 / (2 * L + 1)
        for t in range(-L, L + 1):
            ry, rx = int(round(c + t * dy_s)), int(round(c + t * dx_s))
            if 0 <= ry < k_mat.shape[0] and 0 <= rx < k_mat.shape[1]:
                k_mat[ry, rx] += w0
            for sgn in (-1, 1):
                fy = int(round(c + t * dy_s + sgn * flank * py_s))
                fx = int(round(c + t * dx_s + sgn * flank * px_s))
                if 0 <= fy < k_mat.shape[0] and 0 <= fx < k_mat.shape[1]:
                    k_mat[fy, fx] -= 0.5 * w0
        resp = convolve(z, k_mat, mode="nearest")
        np.maximum(best, resp, out=best)
    return np.where(valid_2d, np.maximum(best, 0.0), 0.0).astype(np.float32)


def _fft_upward_continue(field_2d: np.ndarray, dz_m: float, dx_m: float = 100.0) -> np.ndarray:
    """Exact potential-field Laplace upward continuation exp(-2*pi*k*dz) in wavenumber space."""
    f = np.nan_to_num(field_2d, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    med = float(np.median(f))
    f0 = f - med
    ny, nx = f0.shape
    ky = np.fft.fftfreq(ny, d=dx_m).astype(np.float32)[:, None]
    kx = np.fft.rfftfreq(nx, d=dx_m).astype(np.float32)[None, :]
    kr = np.hypot(ky, kx)
    atten = np.exp(-2.0 * np.pi * kr * float(dz_m)).astype(np.float32)
    spec = np.fft.rfft2(f0) * atten
    return (np.fft.irfft2(spec, s=(ny, nx)).astype(np.float32) + med)


def build_or_load_feature_stack(raw_dir: str | Path | None = None, force: bool = False) -> dict[str, Any]:
    """Build or attach memory-mapped 58-channel float32 feature stack + orientation tensors."""
    raw = resolve_raw_dir(raw_dir)
    work = resolve_work_dir()
    meta_path = work / "h85_stack_meta.json"
    mmap_path = work / "h85_X_fp.f32.mmap"
    aux_path = work / "h85_orientation_aux.npz"

    with rasterio.open(raw / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    fp_idx = np.flatnonzero(footprint.ravel())
    n_fp = int(fp_idx.size)
    n_feat = len(FEATURE_NAMES)

    if not force and meta_path.exists() and mmap_path.exists() and aux_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta.get("feature_names") == list(FEATURE_NAMES) and meta.get("n_fp") == n_fp:
            X_mm = np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(n_fp, n_feat))
            aux = np.load(aux_path)
            return {
                "X": X_mm,
                "feature_names": FEATURE_NAMES,
                "footprint": footprint,
                "fp_idx": fp_idx,
                "lid_norm_az_deg": aux["lid_norm_az_deg"],
                "multi_norm_az_deg": aux["multi_norm_az_deg"],
                "multi_coherence": aux["multi_coherence"],
            }

    t0 = time.time()
    print(f"[H85-TVFV] Building {n_feat}-channel physical tensor stack across {n_fp:,} pixels...", flush=True)
    X_mm = np.memmap(mmap_path, dtype=np.float32, mode="w+", shape=(n_fp, n_feat))
    col_idx = {name: i for i, name in enumerate(FEATURE_NAMES)}

    def write_col(name: str, arr: np.ndarray, is_fp_vec: bool = False) -> None:
        v = arr if is_fp_vec else arr.ravel()[fp_idx]
        X_mm[:, col_idx[name]] = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    # --- Load core macro-topographic hanging-wall dip vector first ---
    with rasterio.open(raw / "training_features.tif") as src:
        det_elev = src.read(12).astype(np.float32)
        elev_slope = src.read(19).astype(np.float32)
    det_elev[(det_elev < -1e20) | ~np.isfinite(det_elev)] = 0.0
    elev_slope[(elev_slope < -1e20) | ~np.isfinite(elev_slope)] = 0.0

    # Macro 1.2 km hanging-wall unit dip vector u_dip = -grad(z_macro)/|grad(z_macro)|
    z_macro = gaussian_filter(det_elev, sigma=12.0)
    gzy, gzx = np.gradient(z_macro)
    gnorm = np.hypot(gzy, gzx) + 1e-6
    u_dip_y = (-gzy / gnorm).astype(np.float32)
    u_dip_x = (-gzx / gnorm).astype(np.float32)
    # Macro gradient normal azimuth in raster (y, x) image frame [0, 180) matching lidar Band 11!
    macro_norm_az_deg = ((np.rad2deg(np.arctan2(gzy, gzx)) + 180.0) % 180.0).astype(np.float32)
    del z_macro, gzy, gzx, gnorm

    # --- Domain I: 1m USGS 3DEP LiDAR + IR-85-LIDAR-NORMAL-90DEG Fix ---
    lid_meta = json.loads((raw / "external/lidar_scarp_features.json").read_text())["quantisation"]
    with rasterio.open(raw / "external/lidar_scarp_features_u8.tif") as src:
        bnames = list(src.descriptions)
        lid = {n: _dequant_lidar(n, src.read(i + 1), lid_meta) for i, n in enumerate(bnames)}

    lid_valid = (lid["valid"] > 0.5) & footprint
    lid_ok_fp = lid_valid.ravel()[fp_idx]
    dipole_1m = np.sqrt(np.maximum(lid["lapneg_max"] * lid["lappos_max"], 0.0))
    tect_fluv_1m = (np.maximum(lid["downface_max"], 1.35 * lid["upface_max"]) * (0.3 + lid["coh100"])) / (
        lid["cross_max"] + 0.08
    )
    pied_step_1m = lid["step_max"] / np.sqrt(lid["relief"] + 9.0)
    antislope_1m = lid["upface_max"] * (0.25 + lid["coh100"]) / (lid["cross_max"] + 0.10)

    # IR-85-LIDAR-NORMAL-90DEG fix: lid["strike"] is actually scarp face normal azimuth in [0, 180)!
    # True contour-parallel fault scarps align with macro_norm_az_deg (cos > 0), whereas down-fan gullies
    # run perpendicular (cos < 0).
    dtheta_1m = np.deg2rad(2.0 * (lid["strike"] - macro_norm_az_deg))
    contour_align_1m = np.cos(dtheta_1m) * lid["coh100"] * pied_step_1m
    lid_norm_az_fp = lid["strike"].ravel()[fp_idx].astype(np.float32)

    write_col("d1_lid_valid", lid_valid.astype(np.float32))
    write_col("d1_lid_step_max", lid["step_max"])
    write_col("d1_lid_ex_max", lid["ex_max"])
    write_col("d1_lid_dipole_crest_toe", np.where(lid_valid, dipole_1m, 0.0))
    write_col("d1_lid_tect_vs_fluv", np.where(lid_valid, tect_fluv_1m, 0.0))
    write_col("d1_lid_piedmont_step", np.where(lid_valid, pied_step_1m, 0.0))
    write_col("d1_lid_antislope_graben", np.where(lid_valid, antislope_1m, 0.0))
    write_col("d1_lid_coh100", lid["coh100"])
    write_col("d1_lid_contour_align_90fix", np.where(lid_valid, contour_align_1m, 0.0))
    write_col("d1_lid_step_anom15", np.where(lid_valid, lid["step_max"] - uniform_filter(lid["step_max"], size=15), 0.0))
    write_col("d1_lid_step_max5", np.where(lid_valid, maximum_filter(lid["step_max"], size=5), 0.0))
    write_col("d1_lid_worm_1100m", compute_strike_worm_2d(np.where(lid_valid, pied_step_1m, 0.0), footprint, half_len=5, flank=3))

    # EarthMRI high-prior 1m Openness & LRM tiles
    hires_2d = np.zeros(footprint.shape, dtype=np.float32)
    hires_npz = np.load(raw / "external/dem1m_high_prior_openness_lrm.npz")
    if "fp_indices" in hires_npz.files and "open_diff" in hires_npz.files:
        idx_h = hires_npz["fp_indices"]
        hires_fp = np.zeros(n_fp, dtype=np.float32)
        hires_fp[idx_h] = np.abs(hires_npz["open_diff"].astype(np.float32))
        write_col("d1_lid_openness_hires", hires_fp, is_fp_vec=True)
    else:
        first_arr = hires_npz[hires_npz.files[0]].astype(np.float32)
        if first_arr.size == n_fp:
            write_col("d1_lid_openness_hires", first_arr, is_fp_vec=True)
        else:
            write_col("d1_lid_openness_hires", hires_2d)

    lid1m_raw_fp = (
        0.35 * (X_mm[:, col_idx["d1_lid_tect_vs_fluv"]] / (np.std(X_mm[lid_ok_fp, col_idx["d1_lid_tect_vs_fluv"]]) + 1e-6))
        + 0.30 * (X_mm[:, col_idx["d1_lid_piedmont_step"]] / (np.std(X_mm[lid_ok_fp, col_idx["d1_lid_piedmont_step"]]) + 1e-6))
        + 0.20 * (X_mm[:, col_idx["d1_lid_dipole_crest_toe"]] / (np.std(X_mm[lid_ok_fp, col_idx["d1_lid_dipole_crest_toe"]]) + 1e-6))
        + 0.15 * (X_mm[:, col_idx["d1_lid_antislope_graben"]] / (np.std(X_mm[lid_ok_fp, col_idx["d1_lid_antislope_graben"]]) + 1e-6))
    ).astype(np.float32)
    del lid, dipole_1m, tect_fluv_1m, pied_step_1m, antislope_1m, dtheta_1m, contour_align_1m, hires_2d
    gc.collect()

    # --- Domain II: 100%-Coverage 10m USGS 3DEP Seamless DEM + Seam-Free Quantile Harmonizer ---
    dem10_map = [
        ("d2_dem10_onesided", "dem10_onesided"),
        ("d2_dem10_onesided3", "dem10_onesided3"),
        ("d2_dem10_steep_ratio", "dem10_steep_ratio_max"),
        ("d2_dem10_curv_absmax", "dem10_curv_absmax"),
        ("d2_dem10_resid_range", "dem10_resid_range"),
        ("d2_dem10_resid_std", "dem10_resid_std"),
        ("d2_dem10_hgm20", "dem10_hgm20_max"),
        ("d2_dem10_hgm50", "dem10_hgm50_max"),
        ("d2_dem10_hgm200", "dem10_hgm200_mean"),
        ("d2_dem10_slope_std", "dem10_slope_std"),
    ]
    for dst_col, fname in dem10_map:
        arr_fp = np.load(raw / "dem10" / f"{fname}.f32.npy").astype(np.float32)
        if arr_fp.size != n_fp:
            # Handle packed mask vs sample_submission finite mask if minor boundary diff exists
            v_valid = np.load(raw / "dem10/dem10_valid_frac.f32.npy")
            raise RuntimeError(f"Unexpected dem10 size {arr_fp.size} vs {n_fp} ({v_valid.size})")
        write_col(dst_col, arr_fp, is_fp_vec=True)

    d10_pied = X_mm[:, col_idx["d2_dem10_onesided3"]] / np.sqrt(np.maximum(X_mm[:, col_idx["d2_dem10_resid_range"]], 0.0) + 4.0)
    write_col("d2_dem10_piedmont_step", d10_pied, is_fp_vec=True)

    d10_os3_2d = np.zeros(footprint.shape, dtype=np.float32)
    d10_os3_2d.ravel()[fp_idx] = X_mm[:, col_idx["d2_dem10_onesided3"]]
    write_col("d2_dem10_worm_1100m", compute_strike_worm_2d(d10_os3_2d, footprint, half_len=5, flank=3))
    del d10_os3_2d

    dem10_raw_fp = (
        0.35 * (X_mm[:, col_idx["d2_dem10_onesided3"]] / (np.std(X_mm[:, col_idx["d2_dem10_onesided3"]]) + 1e-6))
        + 0.25 * (X_mm[:, col_idx["d2_dem10_onesided"]] / (np.std(X_mm[:, col_idx["d2_dem10_onesided"]]) + 1e-6))
        + 0.25 * (X_mm[:, col_idx["d2_dem10_steep_ratio"]] / (np.std(X_mm[:, col_idx["d2_dem10_steep_ratio"]]) + 1e-6))
        + 0.15 * (X_mm[:, col_idx["d2_dem10_curv_absmax"]] / (np.std(X_mm[:, col_idx["d2_dem10_curv_absmax"]]) + 1e-6))
    ).astype(np.float32)

    # Quantile-match gap distribution onto LiDAR-valid distribution for zero survey-boundary step!
    blended_lid = (0.72 * lid1m_raw_fp + 0.28 * dem10_raw_fp).astype(np.float32)
    q_grid = np.linspace(0.0, 1.0, 1001)
    gap_matched = np.interp(
        dem10_raw_fp[~lid_ok_fp],
        np.quantile(dem10_raw_fp[~lid_ok_fp], q_grid),
        np.quantile(blended_lid[lid_ok_fp], q_grid),
    ).astype(np.float32)
    seamfree_fp = np.empty(n_fp, dtype=np.float32)
    seamfree_fp[lid_ok_fp] = blended_lid[lid_ok_fp]
    seamfree_fp[~lid_ok_fp] = gap_matched
    write_col("d2_seamfree_scarp_qnorm", seamfree_fp, is_fp_vec=True)

    seamfree_2d = np.zeros(footprint.shape, dtype=np.float32)
    seamfree_2d.ravel()[fp_idx] = seamfree_fp
    write_col("d2_seamfree_worm_1300m", compute_strike_worm_2d(seamfree_2d, footprint, half_len=6, flank=3))

    # Multi-scale 100%-coverage structure tensor normal azimuth on seamfree_2d for Terzaghi-Morris mechanics
    sm_sf = gaussian_filter(seamfree_2d, sigma=1.5)
    sf_gy, sf_gx = np.gradient(sm_sf)
    jxx = gaussian_filter((sf_gx * sf_gx).astype(np.float32), sigma=3.0)
    jyy = gaussian_filter((sf_gy * sf_gy).astype(np.float32), sigma=3.0)
    jxy = gaussian_filter((sf_gx * sf_gy).astype(np.float32), sigma=3.0)
    multi_coh_2d = np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy * jxy, 0.0)) / (jxx + jyy + 1e-8)
    multi_norm_deg_2d = ((0.5 * np.rad2deg(np.arctan2(2.0 * jxy, jxx - jyy))) + 180.0) % 180.0
    multi_norm_fp = multi_norm_deg_2d.ravel()[fp_idx].astype(np.float32)
    multi_coh_fp = multi_coh_2d.ravel()[fp_idx].astype(np.float32)
    del seamfree_2d, sm_sf, sf_gy, sf_gx, jxx, jyy, jxy, multi_coh_2d, multi_norm_deg_2d, lid1m_raw_fp, dem10_raw_fp
    gc.collect()

    # --- Domain III & IV: 3D Hanging-Wall Polar Dipole + Potential Fields + Strain ---
    with rasterio.open(raw / "training_features.tif") as src:
        b_rtp = src.read(2).astype(np.float32)
        b_tmi_hg = src.read(3).astype(np.float32)
        b_geod_2nd = src.read(4).astype(np.float32)
        b_grav_slope = src.read(5).astype(np.float32)
        b_tc = src.read(6).astype(np.float32)
        b_geod_shear = src.read(7).astype(np.float32)
        b_geod_dil = src.read(8).astype(np.float32)
        b_tmi_vg = src.read(9).astype(np.float32)
        b_deq = src.read(10).astype(np.float32)
        b_grav_vg = src.read(11).astype(np.float32)
        b_grav = src.read(13).astype(np.float32)
        b_depth_base = src.read(15).astype(np.float32)
        b_ieq = src.read(16).astype(np.float32)
        b_cond = src.read(17).astype(np.float32)
        b_grav_hg = src.read(18).astype(np.float32)

    for a in (b_rtp, b_tmi_hg, b_geod_2nd, b_grav_slope, b_tc, b_geod_shear, b_geod_dil,
              b_tmi_vg, b_deq, b_grav_vg, b_grav, b_depth_base, b_ieq, b_cond, b_grav_hg):
        a[(a < -1e20) | ~np.isfinite(a)] = 0.0

    # Signed 3D normal-fault hanging-wall dipole projections:
    # Across a dipping normal fault, u_dip points footwall -> hanging wall:
    #   +grad(depth_to_base_surf) . u_dip > 0 (basin thickens into hanging wall)
    #   -grad(iso_grav_anom) . u_dip > 0 (density drops into hanging-wall alluvial wedge)
    by, bx = np.gradient(gaussian_filter(b_depth_base, sigma=4.0))
    hw_base = (bx * u_dip_x + by * u_dip_y).astype(np.float32)
    gy, gx = np.gradient(gaussian_filter(b_grav, sigma=4.0))
    hw_grav = (-gx * u_dip_x - gy * u_dip_y).astype(np.float32)

    z_micro = gaussian_filter(det_elev, sigma=1.5)
    my, mx = np.gradient(z_micro)
    hw_topo = (-mx * u_dip_x - my * u_dip_y).astype(np.float32)
    hw_triple = (
        np.sign(hw_topo) * np.sqrt(np.abs(hw_topo))
        * (0.5 + np.tanh(hw_base / (np.std(hw_base[footprint]) + 1e-6)))
        * (0.5 + np.tanh(hw_grav / (np.std(hw_grav[footprint]) + 1e-6)))
    ).astype(np.float32)

    write_col("d3_hw_base_dipole", hw_base)
    write_col("d3_hw_grav_dipole", hw_grav)
    write_col("d3_hw_triple_concordance", hw_triple)

    log_tmi_hg = np.log1p(np.maximum(b_tmi_hg, 0.0)).astype(np.float32)
    rtp_hp15 = (b_rtp - uniform_filter(b_rtp, size=15)).astype(np.float32)
    write_col("d3_log_tmi_hg", log_tmi_hg)
    write_col("d3_tmi_vg", b_tmi_vg)
    write_col("d3_mag_tc", b_tc)
    write_col("d3_rtp_hp15", rtp_hp15)

    with rasterio.open(raw / "external/geodawn_extensions_u8.tif") as src:
        uk_u8 = src.read(2).astype(np.float32)
        up150_u8 = src.read(4).astype(np.float32)
    up150_grad = np.hypot(*np.gradient(up150_u8)).astype(np.float32)
    write_col("d3_up150_grad", up150_grad)

    # Exact FFT upward continuation depth persistence at z = 500 m vs z = 100 m
    rtp_up100 = _fft_upward_continue(b_rtp, dz_m=100.0)
    rtp_up500 = _fft_upward_continue(b_rtp, dz_m=500.0)
    g100 = np.hypot(*np.gradient(rtp_up100))
    g500 = np.hypot(*np.gradient(rtp_up500))
    write_col("d3_fft_up500_persist", (g500 / (g100 + 2.0)) * np.log1p(g500))
    del rtp_up100, rtp_up500, g100, g500

    grav_edge = (b_grav_slope + 0.5 * np.abs(b_grav_hg)).astype(np.float32)
    write_col("d3_grav_slope_hp", grav_edge - uniform_filter(grav_edge, size=21))
    verduzco_tilt = np.arctan2(b_grav_vg, np.abs(b_grav_hg) + b_grav_slope + 1e-4)
    # Zero-contour proximity of Verduzco tilt angle identifies subvertical dipping contact edges!
    write_col("d3_verduzco_grav_tilt", np.exp(-np.abs(verduzco_tilt) / 0.35) * np.log1p(grav_edge))

    # Gallardo & Meju (2004) gravity x RTP magnetic gradient alignment operator
    ry, rx = np.gradient(gaussian_filter(b_rtp, sigma=2.5))
    gg_norm = np.hypot(gy, gx) + 1e-6
    rr_norm = np.hypot(ry, rx) + 1e-6
    cos_gm = np.abs(gx * rx + gy * ry) / (gg_norm * rr_norm)
    write_col("d3_gallardo_crossgrad", cos_gm * np.sqrt(np.log1p(gg_norm) * np.log1p(rr_norm)))

    w_mag = compute_strike_worm_2d(log_tmi_hg, footprint, half_len=7, flank=3)
    w_grav = compute_strike_worm_2d(grav_edge, footprint, half_len=7, flank=3)
    write_col("d3_worm_mag_grav_1500m", 0.55 * w_mag + 0.45 * w_grav)

    # Mesh-safe sigma=36 px de-aliased MT electrical conductivity boundary + basement step
    cond_safe = gaussian_filter(b_cond, sigma=36.0)
    cond_grad = np.hypot(*np.gradient(cond_safe))
    base_grad = np.hypot(*np.gradient(b_depth_base))
    write_col("d3_mt_cond_grad_safe36", 0.5 * (cond_grad / (np.std(cond_grad[footprint]) + 1e-6)) + 0.5 * np.log1p(base_grad))
    del w_mag, w_grav, cond_safe, cond_grad, base_grad, gy, gx, ry, rx, by, bx

    # Domain IV local strain & seismic observables
    write_col("d4_strain_2ndinv", b_geod_2nd)
    write_col("d4_strain_shear", b_geod_shear)
    write_col("d4_strain_dilate", b_geod_dil)
    write_col("d4_strain_kostrov_ratio", np.abs(b_geod_dil) / (b_geod_shear + 1e-5))
    write_col("d4_seismic_ieq_log", np.log1p(np.maximum(b_ieq, 0.0)))
    write_col("d4_seismic_deq_inv", 1.0 / (1.0 + np.maximum(b_deq, 0.0) / 15.0))
    write_col("d4_elev_slope_raw", elev_slope)
    write_col("d4_elev_slope_anom15", elev_slope - uniform_filter(elev_slope, size=15))
    write_col("d4_det_elev_lap7", det_elev - uniform_filter(det_elev, size=7))

    # --- Domain V: Sibson Fault-Valve Geothermal Enthalpy, Heat Flow & Hydrothermal Alteration ---
    hf_conv_grid = np.zeros(footprint.shape, dtype=np.float32)
    with (EXTERNAL_REPO_DIR / "usgs_heat_flow_wells_epsg32611.csv").open() as f:
        for row in csv.DictReader(f):
            r, c = int(row["row"]), int(row["col"])
            # Positive convective excess over regional conductive geotherm marks active fault upflow!
            excess = max(float(row["hf_resid_mw_m2"]), 0.0) + 0.25 * max(float(row["hf_meas_mw_m2"]) - 90.0, 0.0)
            if excess > hf_conv_grid[r, c]:
                hf_conv_grid[r, c] = excess
    write_col("d5_hf_convective_1km", np.log1p(gaussian_filter(hf_conv_grid, sigma=12.0) * 25.0))
    write_col("d5_hf_convective_3km", np.log1p(gaussian_filter(hf_conv_grid, sigma=35.0) * 80.0))
    del hf_conv_grid

    geotherm_grid = np.zeros(footprint.shape, dtype=np.float32)
    diseq_grid = np.zeros(footprint.shape, dtype=np.float32)
    with (raw / "external/gdr_wellspring_in_footprint.csv").open() as f:
        for row in csv.DictReader(f):
            try:
                r, c = int(float(row["row"])), int(float(row["col"]))
            except Exception:
                continue
            if not (0 <= r < footprint.shape[0] and 0 <= c < footprint.shape[1]):
                continue
            vals = []
            t_meas = 15.0
            for k in ("temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
                try:
                    v = float(row[k])
                    if np.isfinite(v) and 0.0 < v < 400.0:
                        vals.append(v)
                        if k == "temp_c":
                            t_meas = v
                except Exception:
                    pass
            if vals:
                t_max = max(vals)
                enthalpy = max(t_max - 20.0, 0.0)
                if enthalpy > geotherm_grid[r, c]:
                    geotherm_grid[r, c] = enthalpy
                # Conductive cooling loss along lateral outflow path -> project 800m upslope (-u_dip)!
                diseq = max(t_max - t_meas, 0.0)
                if diseq > 15.0:
                    up_r = int(np.clip(round(r - 8.0 * u_dip_y[r, c]), 0, footprint.shape[0] - 1))
                    up_c = int(np.clip(round(c - 8.0 * u_dip_x[r, c]), 0, footprint.shape[1] - 1))
                    if diseq > diseq_grid[up_r, up_c]:
                        diseq_grid[up_r, up_c] = diseq

    write_col("d5_gdr_geotherm_upflow_1km", np.log1p(gaussian_filter(geotherm_grid, sigma=10.0) * 30.0))
    write_col("d5_gdr_diseq_updip", np.log1p(gaussian_filter(diseq_grid, sigma=12.0) * 40.0))
    del geotherm_grid, diseq_grid

    with rasterio.open(raw / "external/derived_gdr_2m_probes_100m_u8.tif") as src:
        probes_2m = src.read(1).astype(np.float32) / 255.0
    with rasterio.open(raw / "external/derived_gdr_paleo_100m_u8.tif") as src:
        paleo_sinter = src.read(1).astype(np.float32) / 255.0
    vents_2d = np.zeros(footprint.shape, dtype=np.float32)
    with (raw / "external/gdr_volcanic_vents_in_footprint.csv").open() as f:
        for row in csv.DictReader(f):
            try:
                r, c = int(float(row["row"])), int(float(row["col"]))
                if 0 <= r < footprint.shape[0] and 0 <= c < footprint.shape[1]:
                    vents_2d[r, c] = 1.0
            except Exception:
                pass
    vents_sm = gaussian_filter(vents_2d, sigma=12.0) * 20.0
    write_col("d5_probes2m_and_paleo_vents", probes_2m + 1.4 * paleo_sinter + vents_sm)
    del probes_2m, paleo_sinter, vents_2d, vents_sm

    with rasterio.open(raw / "external/geodawn_rad_u8.tif") as src:
        k_u8 = src.read(1).astype(np.float32)
        th_u8 = src.read(2).astype(np.float32)
    non_playa = (elev_slope > 1.2).astype(np.float32)
    k_th = (k_u8 + 1.0) / (th_u8 + 10.0)
    write_col("d5_potassic_k_th_alteration", (k_th - uniform_filter(k_th, size=21)) * non_playa + 0.02 * (uk_u8 - uniform_filter(uk_u8, size=21)) * non_playa)
    write_col("d5_hydro_demag_trough", np.maximum(-rtp_hp15, 0.0) * log_tmi_hg * non_playa)

    with rasterio.open(raw / "external/tiger_road_distance_m.tif") as src:
        road_d = src.read(1).astype(np.float32)
    flat_non_geophys = (elev_slope < 1.8) & (grav_edge < np.percentile(grav_edge[footprint], 50))
    write_col("d5_road_valley_berm_flag", np.exp(-np.maximum(road_d, 0.0) / 60.0) * flat_non_geophys.astype(np.float32))

    X_mm.flush()
    np.savez(
        aux_path,
        lid_norm_az_deg=lid_norm_az_fp,
        multi_norm_az_deg=multi_norm_fp,
        multi_coherence=multi_coh_fp,
    )
    meta_path.write_text(json.dumps({
        "schema": "gems85-h85-tvfv-v1",
        "n_fp": n_fp,
        "n_features": n_feat,
        "feature_names": list(FEATURE_NAMES),
        "build_seconds": round(time.time() - t0, 2),
    }, indent=2) + "\n")
    print(f"[H85-TVFV] Built {n_feat} channels in {time.time() - t0:.1f}s.", flush=True)
    return {
        "X": np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(n_fp, n_feat)),
        "feature_names": FEATURE_NAMES,
        "footprint": footprint,
        "fp_idx": fp_idx,
        "lid_norm_az_deg": lid_norm_az_fp,
        "multi_norm_az_deg": multi_norm_fp,
        "multi_coherence": multi_coh_fp,
    }
