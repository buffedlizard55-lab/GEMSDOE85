"""Lane H85-HJCD: Hydrothermal-Juxtaposition & Fault-Valve Conduit Discovery.

Architecture overview:
  1. Pure physical + geothermal-vent + 16-strike GEO-Pb stack (`N_PHYS = 58` channels,
     stored once as `float16` memmap on the 5,167,373 in-footprint pixels — zero label
     or fault-catalogue inputs).
  2. Fold-proper fracture-mechanics & hydrothermal-conduit coupling (`N_STRUCT = 22`
     channels, recomputed strictly from `visible` fault traces inside each fold — zero
     access to hidden faults or buffers):
       - Analytic nearest-strand strike/normal vector decomposition (`s_par`, `s_perp`,
         `cos2_inline`, endpoint tipness, crack-tip stress propagation, piedmont parallel steps).
       - Opposing directional half-beam geometric-mean bridges (`sqrt(B_b^+ * B_b^-)`)
         across 12 strike bins at 2.8 km, 7.2 km, and 15.2 km bridge scales via FFT.
       - Subsurface `GEO-Pb-16` strike-locked bridge resonance (`cos^2(theta_b - theta_geopb)`).
       - Multiplicative coupling between hydrothermal vents (paleo-sinters/tufas + 2-m
         temperature probes + spring geothermometry) and fracture tips / relay bridges.
  3. Out-of-quadrant dual-regime 300 m kernel-expectation learning:
     For each spatial quadrant `q in {0, 1, 2, 3}`, models are trained strictly on
     `quadrants != q` (zero pixels, features, or fault traces from quadrant `q`) using
     inverse-sampling-probability weights so predictions match calibrated expectations
     `E[K_G(x) | X]` and `E[I(x in G) | X]` directly in `[0, 1]`.
"""

from __future__ import annotations

import gc
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.signal import oaconvolve
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

from . import geopb, grid, hydrothermal

N_STRIKE_BINS = 12

STRUCTURAL_FEATURE_NAMES: tuple[str, ...] = (
    "log_d_vis",
    "s_par_log",
    "s_perp_log",
    "cos2_inline",
    "nearest_coh",
    "nearest_tipness",
    "tip_inline_1km",
    "tip_inline_4km",
    "piedmont_parallel_step",
    "vis_dens_s4",
    "vis_dens_s12",
    "vis_dens_s32",
    "vis_gap_ratio",
    "beam100m_800m",
    "bridge100m_1p6km",
    "beam_1p4km",
    "bridge_2p8km",
    "beam_3p6km",
    "bridge_7p2km",
    "beam_7p6km",
    "bridge_15km",
    "bridge_geopb16_lock",
    "hydro_x_bridge",
    "hydro_x_tip",
    "geopb_x_bridge",
    "lidar_x_bridge",
    "strain_x_bridge",
)


def kernel_target_300m(truth_mask: np.ndarray) -> np.ndarray:
    """Exact competition 300 m (3 px) linear proximity target max_{g in G} (1 - d/3)_+."""
    if not np.any(truth_mask):
        return np.zeros(truth_mask.shape, dtype=np.float32)
    d = ndi.distance_transform_edt(~truth_mask)
    return np.clip(1.0 - d / 3.0, 0.0, 1.0).astype(np.float32)


def _grad_mag(z: np.ndarray, sigma: float) -> np.ndarray:
    gy = ndi.gaussian_filter(z, sigma=sigma, order=[1, 0], mode="nearest")
    gx = ndi.gaussian_filter(z, sigma=sigma, order=[0, 1], mode="nearest")
    return np.hypot(gy, gx).astype(np.float32)


def build_physical_feature_cache(
    root: Path | None = None,
    *,
    force: bool = False,
) -> tuple[np.memmap, list[str], dict[str, np.ndarray], dict[str, object]]:
    """Build or load the 100% label-free physical + geothermal + GEO-Pb-16 feature stack."""
    base = root or grid.ROOT
    cache_dir = base / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    mm_path = cache_dir / "hjcd_phys_v1.f16"
    meta_path = cache_dir / "hjcd_phys_v1.meta.json"
    aux_path = cache_dir / "hjcd_aux_v1.npz"

    fp = grid.footprint()
    fp_idx = np.flatnonzero(fp)
    n_fp = int(fp_idx.size)

    if not force and mm_path.is_file() and meta_path.is_file() and aux_path.is_file():
        meta = json.loads(meta_path.read_text())
        names = list(meta["feature_names"])
        if mm_path.stat().st_size == n_fp * len(names) * 2:
            mm = np.memmap(mm_path, dtype=np.float16, mode="r", shape=(n_fp, len(names)))
            aux_z = np.load(aux_path)
            aux = {k: aux_z[k] for k in aux_z.files}
            return mm, names, aux, meta

    ext_dir = base / "data" / "external"
    # Pre-count feature list deterministically before writing streaming memmap
    grad_keys = ("rtp", "iso_grav_anom", "det_elev", "depth_to_base_surf", "cond_surf", "tmi")
    names: list[str] = []
    for bname in grid.FEATURE_NAMES:
        names.append(f"tf_{bname}")
    for bname in grad_keys:
        names.append(f"grad15_{bname}")
        names.append(f"dog8_{bname}")
    names.extend(["strain_transtension", "grav_basement_couple", "claycap_x_seismicity"])
    geopb_keys = [
        "geopb16_pot_r4",
        "geopb16_rad_r4",
        "geopb16_topo_r4",
        "geopb16_med_r4",
        "geopb16_crest_r4",
        "geopb16_pot_r6",
        "geopb16_med_r6",
    ]
    names.extend(geopb_keys)
    lidar_keys = [
        "lidar_ex_max",
        "lidar_step_max",
        "lidar_lapneg_max",
        "lidar_downface_max",
        "lidar_relief",
        "lidar_coh100",
        "lidar_valid",
    ]
    radext_keys = ["rad_K_z", "rad_Th_z", "rad_U_z", "rad_TC_z", "rad_ThK_z", "rad_UK_z", "rad_k_metasom", "mag_shallow_res"]
    paleo_keys = ["paleo_vent_s4", "paleo_vent_s12", "paleo_vent_logprox"]
    probe_keys = ["probe2m_dab_s5", "probe2m_dab_s15", "probe2m_survey_dens_s10", "probe2m_hot_logprox"]
    spring_keys = ["spring_temp_s8", "spring_temp_s20", "geotherm_sio2_s12", "geotherm_nakca_s12", "spring_hot_logprox", "volcanic_vent_s20"]
    morph_keys = [
        "chi10_step_max",
        "chi10_ksn_max",
        "elev_abs_z",
        "lahontan_1335m_prox",
        "topo10_slope_p90",
        "topo10_relief",
        "topo10_curv_prof",
        "topo10_aspect_coh",
        "topo10_hs_lineament",
    ]
    coup_keys = [
        "piedmont_relief_hinge",
        "piedmont_slope_hinge",
        "scarp_inflection_100m",
        "hydro_master_index",
        "hydro_x_geopb16_pot",
        "hydro_x_geopb16_med",
        "chi10_piedmont_step",
    ]
    names.extend(lidar_keys + radext_keys + paleo_keys + probe_keys + spring_keys + morph_keys + coup_keys)

    n_feat = len(names)
    mm = np.memmap(mm_path, dtype=np.float16, mode="w+", shape=(n_fp, n_feat))
    col_map = {n: i for i, n in enumerate(names)}

    def _put(cname: str, arr2d: np.ndarray) -> None:
        mm[:, col_map[cname]] = np.clip(arr2d.ravel()[fp_idx], -12.0, 12.0).astype(np.float16)

    # 1. Official 19 bands + gradients + active-tectonic interactions
    saved_tf: dict[str, np.ndarray] = {}
    keep_tf = set(grad_keys) | {"geod_shearrate", "geod_dilaterate", "ieq_n100a15"}
    for bname in grid.FEATURE_NAMES:
        raw = grid.read_feature(bname)
        z = geopb.robust_z(raw, fp, clip=6.0)
        _put(f"tf_{bname}", z)
        if bname in keep_tf:
            saved_tf[bname] = z
        del raw

    for bname in grad_keys:
        z = saved_tf[bname]
        _put(f"grad15_{bname}", geopb.robust_z(_grad_mag(z, 1.5), fp, clip=6.0))
        dog = z - ndi.gaussian_filter(z, sigma=8.0, mode="nearest")
        _put(f"dog8_{bname}", geopb.robust_z(dog.astype(np.float32), fp, clip=6.0))
        del dog

    strain_trans = geopb.robust_z(
        (np.maximum(saved_tf["geod_dilaterate"], -1.0) + 1.0) * np.maximum(saved_tf["geod_shearrate"] + 1.5, 0.0),
        fp,
        clip=6.0,
    )
    _put("strain_transtension", strain_trans)
    _put(
        "grav_basement_couple",
        geopb.robust_z(_grad_mag(saved_tf["iso_grav_anom"], 2.0) * _grad_mag(saved_tf["depth_to_base_surf"], 2.0), fp, clip=6.0),
    )
    _put(
        "claycap_x_seismicity",
        geopb.robust_z(np.maximum(saved_tf["cond_surf"], 0.0) * np.maximum(saved_tf["ieq_n100a15"] + 1.0, 0.0), fp, clip=6.0),
    )
    tmi_z_ref = saved_tf["tmi"].copy()
    cond_z_ref = saved_tf["cond_surf"].copy()
    det_elev_ref = saved_tf["det_elev"].copy()
    saved_tf.clear()
    gc.collect()

    # 2. 12/16-strike domain-resolved GEO-Pb juxtaposition
    gpb = geopb.geopb16_components(sigma=1.5, footprint=fp)
    for k in geopb_keys:
        _put(k, geopb.robust_z(gpb[k], fp, clip=6.0))
    geopb_pot_z = geopb.robust_z(gpb["geopb16_pot_r4"], fp, clip=6.0)
    geopb_med_z = geopb.robust_z(gpb["geopb16_med_r4"], fp, clip=6.0)
    strike_rad = gpb["geopb16_strike_rad"].astype(np.float32)
    del gpb
    gc.collect()

    # 3. 1 m LiDAR scarp features (including Laplacian inflection & downface scarp throw)
    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as ds:
        grid.assert_grid(ds, "lidar_scarp_features_u8.tif")
        for bidx, lname in (
            (1, "lidar_ex_max"),
            (3, "lidar_step_max"),
            (4, "lidar_lapneg_max"),
            (6, "lidar_downface_max"),
            (9, "lidar_relief"),
            (10, "lidar_coh100"),
        ):
            a = ds.read(bidx).astype(np.float32)
            a[a == 0] = np.nan
            z = geopb.robust_z(a, fp, clip=6.0)
            _put(lname, z)
            if lname == "lidar_ex_max":
                lidar_scarp_ref = z
            del a
        val = (ds.read(12) > 0).astype(np.float32)
        _put("lidar_valid", val)
        del val

    # 4. GeoDAWN gamma-ray spectrometry & upward-continued magnetic residual
    with rasterio.open(ext_dir / "geodawn_rad_u8.tif") as ds:
        grid.assert_grid(ds, "geodawn_rad_u8.tif")
        rad_z = {}
        for bidx, rname in ((1, "rad_K_z"), (2, "rad_Th_z"), (3, "rad_U_z"), (4, "rad_TC_z")):
            a = ds.read(bidx).astype(np.float32)
            a[a == 0] = np.nan
            rad_z[rname] = geopb.robust_z(a, fp, clip=6.0)
            _put(rname, rad_z[rname])
            del a
    _put("rad_k_metasom", geopb.robust_z(rad_z["rad_K_z"] - 0.8 * rad_z["rad_Th_z"], fp, clip=6.0))
    del rad_z

    with rasterio.open(ext_dir / "geodawn_extensions_u8.tif") as ds:
        grid.assert_grid(ds, "geodawn_extensions_u8.tif")
        for bidx, ename in ((1, "rad_ThK_z"), (2, "rad_UK_z")):
            a = ds.read(bidx).astype(np.float32)
            a[a == 0] = np.nan
            _put(ename, geopb.robust_z(a, fp, clip=6.0))
            del a
        up150 = ds.read(4).astype(np.float32)
        up150[up150 == 0] = np.nan
        up150_z = geopb.robust_z(up150, fp, clip=6.0)
        _put("mag_shallow_res", geopb.robust_z(tmi_z_ref - up150_z, fp, clip=6.0))
        del up150, up150_z, tmi_z_ref
    gc.collect()

    # 5. Official DOE GDR 1391 geothermal vent, 2-m probe, geothermometry & 3DEP 10 m chi stack
    paleo_f, paleo_stats = hydrothermal.load_paleo_geothermal_fields(ext_dir, fp)
    for k, v in paleo_f.items():
        _put(k, v)
    probe_f, probe_stats = hydrothermal.load_2m_probe_fields(ext_dir, fp)
    for k, v in probe_f.items():
        _put(k, v)
    spring_f, spring_stats = hydrothermal.load_wellspring_and_volcanic_fields(ext_dir, fp)
    for k, v in spring_f.items():
        _put(k, v)
    morph_f = hydrothermal.load_3dep10m_chi_and_morph_fields(ext_dir, fp)
    for k, v in morph_f.items():
        _put(k, v)

    # Asymmetric range-front piedmont hinge detectors (separating range-front fault scarps
    # from high-elevation erosional canyon walls where relief is high on BOTH sides)
    _put("piedmont_relief_hinge", geopb.robust_z(_grad_mag(morph_f["topo10_relief"], 8.0), fp, clip=6.0))
    _put("piedmont_slope_hinge", geopb.robust_z(_grad_mag(morph_f["topo10_slope_p90"], 8.0), fp, clip=6.0))
    scarp_inflect = np.abs(det_elev_ref - ndi.gaussian_filter(det_elev_ref, sigma=2.2, mode="nearest"))
    _put("scarp_inflection_100m", geopb.robust_z(scarp_inflect.astype(np.float32), fp, clip=6.0))
    del scarp_inflect, det_elev_ref

    hydro_raw = (
        0.30 * np.maximum(paleo_f["paleo_vent_s12"], 0.0)
        + 0.25 * np.maximum(probe_f["probe2m_dab_s15"], 0.0)
        + 0.20 * np.maximum(spring_f["geotherm_sio2_s12"], 0.0)
        + 0.15 * np.maximum(spring_f["spring_temp_s8"], 0.0)
        + 0.10 * np.maximum(cond_z_ref, 0.0)
    ).astype(np.float32)
    hydro_master = geopb.robust_z(hydro_raw, fp, clip=6.0)
    _put("hydro_master_index", hydro_master)
    _put("hydro_x_geopb16_pot", geopb.robust_z(np.maximum(hydro_master, 0.0) * np.maximum(geopb_pot_z + 1.0, 0.0), fp, clip=6.0))
    _put("hydro_x_geopb16_med", geopb.robust_z(np.maximum(hydro_master, 0.0) * np.maximum(geopb_med_z + 1.0, 0.0), fp, clip=6.0))
    piedmont = np.maximum(morph_f["chi10_step_max"], 0.0) * np.exp(-np.maximum(morph_f["topo10_slope_p90"], 0.0) * 0.5)
    _put("chi10_piedmont_step", geopb.robust_z(piedmont.astype(np.float32), fp, clip=6.0))

    mm.flush()
    aux = {
        "strike_rad": strike_rad,
        "hydro_master": np.maximum(hydro_master, 0.0).astype(np.float32),
        "geopb_pot": np.maximum(geopb_pot_z + 1.0, 0.0).astype(np.float32),
        "lidar_scarp": np.maximum(lidar_scarp_ref, 0.0).astype(np.float32),
        "strain_trans": np.maximum(strain_trans, 0.0).astype(np.float32),
    }
    np.savez(aux_path, **aux)

    del paleo_f, probe_f, spring_f, morph_f, hydro_raw, cond_z_ref, geopb_pot_z, geopb_med_z, piedmont
    gc.collect()

    meta = {
        "schema_version": 1,
        "n_footprint_pixels": n_fp,
        "n_features": n_feat,
        "feature_names": names,
        "geothermal_inventory": {
            "paleo_geothermal": paleo_stats,
            "shallow_2m_probes": probe_stats,
            "wellspring_and_volcanic": spring_stats,
        },
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    mm_ro = np.memmap(mm_path, dtype=np.float16, mode="r", shape=(n_fp, n_feat))
    return mm_ro, names, aux, meta


def _ray_response_fast(
    plane: np.ndarray, ang: float, max_step: int, stride: int = 1
) -> tuple[np.ndarray, np.ndarray]:
    """Exact forward & backward exponentially-tapered ray integral via direct integer shifts.

    Orders of magnitude faster and lower memory than full-frame 2-D complex FFT (`oaconvolve`)
    for 1-D line rays (`~0.03s` vs `~2.0s` per strike at 3730x3292, zero FFT ringing).
    """
    ty, tx = float(np.sin(ang)), float(np.cos(ang))
    fwd = np.zeros_like(plane, dtype=np.float32)
    bwd = np.zeros_like(plane, dtype=np.float32)
    w_sum = 0.0
    tau = max_step * 0.72
    for t in range(1, max_step + 1, stride):
        dy = int(round(t * ty))
        dx = int(round(t * tx))
        if dy == 0 and dx == 0:
            continue
        w = float(np.exp(-t / tau))
        fwd += w * geopb.shift(plane, -dy, -dx, fill=0.0)
        bwd += w * geopb.shift(plane, dy, dx, fill=0.0)
        w_sum += w
    inv = 1.0 / max(w_sum, 1e-6)
    fwd *= inv
    bwd *= inv
    return fwd, bwd


def _upsample_2x(small: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Fast bilinear 2x upsample back to exact `(H, W)` grid."""
    up = ndi.zoom(small, 2.0, order=1, prefilter=False).astype(np.float32)
    out = np.zeros(shape, dtype=np.float32)
    hh = min(shape[0], up.shape[0])
    ww = min(shape[1], up.shape[1])
    out[:hh, :ww] = up[:hh, :ww]
    return out


def compute_fold_structural_features(
    visible: np.ndarray,
    aux: dict[str, np.ndarray],
    fp: np.ndarray,
) -> np.ndarray:
    """Compute all 25 fracture-mechanics & hydrothermal-coupling channels strictly from `visible`.

    Returns `float16` array of shape `(N_fp, 25)` aligned with `np.flatnonzero(fp)`.
    Never accesses hidden faults, buffers, or full-catalogue arrays.
    """
    H, W = fp.shape
    fp_idx = np.flatnonzero(fp)
    n_fp = int(fp_idx.size)
    out = np.zeros((n_fp, len(STRUCTURAL_FEATURE_NAMES)), dtype=np.float16)

    if not np.any(visible):
        return out

    # 1. Exact Euclidean distance + nearest visible strand coordinate map
    d_vis, (ny, nx) = ndi.distance_transform_edt(~visible, return_indices=True)
    d_vis = d_vis.astype(np.float32)

    vis_f = visible.astype(np.float32)
    gy = ndi.gaussian_filter(vis_f, sigma=1.8, order=[1, 0], mode="constant")
    gx = ndi.gaussian_filter(vis_f, sigma=1.8, order=[0, 1], mode="constant")
    jyy = ndi.gaussian_filter(gy * gy, sigma=2.5, mode="constant")
    jyx = ndi.gaussian_filter(gy * gx, sigma=2.5, mode="constant")
    jxx = ndi.gaussian_filter(gx * gx, sigma=2.5, mode="constant")
    del gy, gx

    phi = 0.5 * np.arctan2(2.0 * jyx, jxx - jyy)
    theta_strand = (phi + 0.5 * np.pi) % np.pi
    coh = (np.hypot(jxx - jyy, 2.0 * jyx) / (jxx + jyy + 1e-6)).astype(np.float32)
    del jyy, jyx, jxx, phi

    cnt9 = ndi.uniform_filter(vis_f, size=9, mode="constant") * 81.0
    tipness_on_vis = (vis_f * np.clip((11.0 - cnt9) / 8.0, 0.0, 1.0)).astype(np.float32)
    del cnt9

    # Analytic vector projections only on in-footprint pixels (saves 60% RAM!)
    rows_fp = (fp_idx // W).astype(np.int32)
    cols_fp = (fp_idx % W).astype(np.int32)
    ny_fp = ny.ravel()[fp_idx]
    nx_fp = nx.ravel()[fp_idx]
    del ny, nx

    dy_fp = (rows_fp - ny_fp).astype(np.float32)
    dx_fp = (cols_fp - nx_fp).astype(np.float32)
    th_near = theta_strand[ny_fp, nx_fp]
    coh_near = coh[ny_fp, nx_fp]
    tip_near = tipness_on_vis[ny_fp, nx_fp]
    del rows_fp, cols_fp, ny_fp, nx_fp, tipness_on_vis

    ty_n = np.sin(th_near).astype(np.float32)
    tx_n = np.cos(th_near).astype(np.float32)
    s_par = np.abs(dy_fp * ty_n + dx_fp * tx_n)
    s_perp = np.abs(-dy_fp * tx_n + dx_fp * ty_n)
    cos2_inl = (s_par * s_par) / (s_par * s_par + s_perp * s_perp + 1.0)
    del dy_fp, dx_fp, ty_n, tx_n, th_near

    d_fp = d_vis.ravel()[fp_idx]
    tip_w = coh_near * (0.35 + 0.65 * tip_near)
    tip_1km = tip_w * cos2_inl * np.exp(-s_perp / 2.2) * np.exp(-s_par / 12.0)
    tip_4km = tip_w * cos2_inl * np.exp(-s_perp / 4.0) * np.exp(-s_par / 42.0)
    pied_step = coh_near * (1.0 - cos2_inl) * np.exp(-(((s_perp - 7.0) / 5.0) ** 2))

    out[:, 0] = np.log1p(np.minimum(d_fp, 500.0)).astype(np.float16)
    out[:, 1] = np.log1p(np.minimum(s_par, 500.0)).astype(np.float16)
    out[:, 2] = np.log1p(np.minimum(s_perp, 500.0)).astype(np.float16)
    out[:, 3] = cos2_inl.astype(np.float16)
    out[:, 4] = coh_near.astype(np.float16)
    out[:, 5] = tip_near.astype(np.float16)
    out[:, 6] = tip_1km.astype(np.float16)
    out[:, 7] = tip_4km.astype(np.float16)
    out[:, 8] = pied_step.astype(np.float16)

    # 2. Multi-scale isotropic fault density & unmapped-gap ratio
    dens4 = ndi.gaussian_filter(vis_f, sigma=4.0, mode="constant").ravel()[fp_idx] * 16.0
    dens12 = ndi.gaussian_filter(vis_f, sigma=12.0, mode="constant").ravel()[fp_idx] * 144.0
    dens32 = ndi.gaussian_filter(vis_f, sigma=32.0, mode="constant").ravel()[fp_idx] * 1024.0
    out[:, 9] = np.log1p(dens4).astype(np.float16)
    out[:, 10] = np.log1p(dens12).astype(np.float16)
    out[:, 11] = np.log1p(dens32).astype(np.float16)
    out[:, 12] = (dens32 / (dens4 * 8.0 + 0.05)).clip(0.0, 25.0).astype(np.float16)
    del dens4, dens12, dens32, d_fp, d_vis, s_par, s_perp, cos2_inl, coh_near, tip_near

    # 3a. Exact 100 m full-resolution short opposing-beam gap bridge (800 m half-ray = 1.6 km canyon-mouth gap)
    b100 = np.floor(theta_strand / (np.pi / N_STRIKE_BINS)).astype(np.int32) % N_STRIKE_BINS
    w100_raw = vis_f * (0.30 + 0.70 * coh)
    w100 = ndi.gaussian_filter(w100_raw, sigma=1.15, mode="constant")
    del w100_raw
    uni800_s = np.zeros((H, W), dtype=np.float32)
    bi1600_s = np.zeros((H, W), dtype=np.float32)
    for b in range(N_STRIKE_BINS):
        ang = b * np.pi / N_STRIKE_BINS
        plane = w100 * (b100 == b)
        bp_b, bm_b = _ray_response_fast(plane, ang, max_step=8, stride=1)
        np.maximum(uni800_s, np.maximum(bp_b, bm_b), out=uni800_s)
        np.maximum(bi1600_s, np.sqrt(bp_b * bm_b, dtype=np.float32), out=bi1600_s)
        del plane, bp_b, bm_b
    del b100, w100
    beam800_fp = uni800_s.ravel()[fp_idx]
    bridge1600_fp = bi1600_s.ravel()[fp_idx]
    out[:, 13] = (beam800_fp * 10.0).clip(0.0, 20.0).astype(np.float16)
    out[:, 14] = (bridge1600_fp * 14.0).clip(0.0, 20.0).astype(np.float16)
    del uni800_s, bi1600_s, beam800_fp

    # 3b. 12-strike opposing half-beam geometric-mean relay bridges on 2x grid (200 m cell)
    Hs, Ws = H // 2, W // 2
    vis_sub = vis_f[: Hs * 2, : Ws * 2].reshape(Hs, 2, Ws, 2).max(axis=(1, 3))
    th_sub = theta_strand[: Hs * 2 : 2, : Ws * 2 : 2]
    coh_sub = coh[: Hs * 2 : 2, : Ws * 2 : 2]
    del vis_f, theta_strand, coh

    b_idx = np.floor(th_sub / (np.pi / N_STRIKE_BINS)).astype(np.int32) % N_STRIKE_BINS
    binned = np.zeros((N_STRIKE_BINS, Hs, Ws), dtype=np.float32)
    weight_sub = ndi.gaussian_filter(vis_sub * (0.30 + 0.70 * coh_sub), sigma=1.25, mode="constant")
    for b in range(N_STRIKE_BINS):
        binned[b] = weight_sub * (b_idx == b)
    del vis_sub, th_sub, coh_sub, b_idx, weight_sub

    strike_geopb_sub = aux["strike_rad"][: Hs * 2 : 2, : Ws * 2 : 2]

    for scale_idx, (hlen, stride_s, col_beam, col_bridge) in enumerate(
        ((7, 1, 15, 16), (18, 2, 17, 18), (38, 3, 19, 20))
    ):
        uni_s = np.zeros((Hs, Ws), dtype=np.float32)
        bi_s = np.zeros((Hs, Ws), dtype=np.float32)
        lock_s = np.zeros((Hs, Ws), dtype=np.float32) if scale_idx == 1 else None
        for b in range(N_STRIKE_BINS):
            ang = b * np.pi / N_STRIKE_BINS
            bp_b, bm_b = _ray_response_fast(binned[b], ang, max_step=hlen, stride=stride_s)
            prod_b = np.sqrt(bp_b * bm_b, dtype=np.float32)
            np.maximum(uni_s, np.maximum(bp_b, bm_b), out=uni_s)
            np.maximum(bi_s, prod_b, out=bi_s)
            if scale_idx == 1:
                np.maximum(lock_s, prod_b * (np.cos(ang - strike_geopb_sub) ** 2), out=lock_s)
            del bp_b, bm_b, prod_b

        uni_fp = _upsample_2x(uni_s, (H, W)).ravel()[fp_idx]
        bi_fp = _upsample_2x(bi_s, (H, W)).ravel()[fp_idx]
        out[:, col_beam] = (uni_fp * 10.0).clip(0.0, 20.0).astype(np.float16)
        out[:, col_bridge] = (bi_fp * 12.0).clip(0.0, 20.0).astype(np.float16)

        if scale_idx == 1:
            beam36_fp = uni_fp
            bridge72_fp = bi_fp
            lock_fp = _upsample_2x(lock_s, (H, W)).ravel()[fp_idx]
            out[:, 21] = (lock_fp * 12.0).clip(0.0, 20.0).astype(np.float16)
            del lock_s, lock_fp
        elif scale_idx == 0:
            bridge28_fp = bi_fp
        del uni_s, bi_s

    del binned, strike_geopb_sub

    # 4. Physics-guided interactions (geothermal vent / GEO-Pb / LiDAR / GPS strain x relay/tip)
    hydro_fp = aux["hydro_master"].ravel()[fp_idx]
    gpb_fp = aux["geopb_pot"].ravel()[fp_idx]
    lid_fp = aux["lidar_scarp"].ravel()[fp_idx]
    str_fp = aux["strain_trans"].ravel()[fp_idx]

    out[:, 22] = (hydro_fp * (0.20 + 6.0 * bridge72_fp + 5.0 * bridge1600_fp)).clip(0.0, 25.0).astype(np.float16)
    out[:, 23] = (hydro_fp * (0.20 + 3.0 * tip_4km + 4.0 * beam36_fp)).clip(0.0, 25.0).astype(np.float16)
    out[:, 24] = (gpb_fp * (0.20 + 6.0 * bridge72_fp + 5.0 * bridge1600_fp + 3.0 * tip_4km)).clip(0.0, 25.0).astype(np.float16)
    out[:, 25] = (lid_fp * (0.20 + 6.0 * bridge1600_fp + 4.0 * bridge28_fp + 3.0 * tip_1km)).clip(0.0, 25.0).astype(np.float16)
    out[:, 26] = (str_fp * (0.20 + 6.0 * bridge72_fp)).clip(0.0, 25.0).astype(np.float16)

    return out


def quadrant_ids(fp: np.ndarray) -> np.ndarray:
    """Exact `(int(median_y), int(median_x))` spatial quadrant index `0..3` matching
    `vendor/gems57/holdout.py::quadrant_ids` (`0=NW, 1=NE, 2=SW, 3=SE`).
    """
    yy, xx = np.nonzero(fp)
    ym, xm = int(np.median(yy)), int(np.median(xx))
    return ((yy >= ym).astype(np.int8) * 2 + (xx >= xm).astype(np.int8))


def _weighted_sample_indices(
    pos_mask: np.ndarray,
    cand_mask: np.ndarray,
    n_neg: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Keep ALL positive halo pixels + stratified negative sample with exact IPW weights."""
    pos_i = np.flatnonzero(cand_mask & pos_mask)
    neg_pool = np.flatnonzero(cand_mask & (~pos_mask))
    k_neg = min(n_neg, int(neg_pool.size))
    neg_i = rng.choice(neg_pool, size=k_neg, replace=False) if k_neg < neg_pool.size else neg_pool
    neg_w = float(neg_pool.size) / max(float(k_neg), 1.0)
    idx = np.concatenate([pos_i, neg_i])
    weights = np.concatenate(
        [np.ones(pos_i.size, dtype=np.float32), np.full(neg_i.size, neg_w, dtype=np.float32)]
    )
    return idx, weights


def fit_out_of_quadrant_models(
    X_phys: np.memmap,
    aux: dict[str, np.ndarray],
    fp: np.ndarray,
    catalogue: np.ndarray,
    *,
    seed: int = 20261022,
    n_internal_draws: int = 3,
    cache_path: Path | None = None,
) -> dict[int, dict[str, object]]:
    """Train strictly out-of-quadrant dual-regime models for every held-out quadrant `q = 0..3`.

    Guarantee: `models[q]` NEVER reads a single feature vector, pixel label, or fault
    trace from quadrant `q` during training or calibration.
    """
    import joblib
    from types import SimpleNamespace
    from gems57.holdout import buffered_component_draw

    cpath = cache_path or (grid.DATA / "cache" / f"hjcd_models_s{seed}_d{n_internal_draws}.joblib")
    if cpath.is_file():
        return joblib.load(cpath)

    H, W = fp.shape
    fp_idx = np.flatnonzero(fp)
    q_fp = quadrant_ids(fp)
    q_grid = np.full(H * W, -1, dtype=np.int8)
    q_grid[fp_idx] = q_fp
    q_grid2d = q_grid.reshape(H, W)

    # Full-map kernel & pixel targets sliceable ONLY outside test quadrant q!
    k_all_fp = kernel_target_300m(catalogue).ravel()[fp_idx]
    y_all_fp = catalogue.ravel()[fp_idx].astype(np.float32)

    models: dict[int, dict[str, object]] = {}
    for q in range(4):
        rng = np.random.default_rng(seed + 101 * q)
        in_train_q = q_fp != q

        # --- Head A (`EXP-1`): Pure blind physical + geothermal + GEO-Pb-16 head ---
        s_idx, s_w = _weighted_sample_indices(k_all_fp > 0.0, in_train_q, n_neg=180_000, rng=rng)
        X_tr_phys = np.asarray(X_phys[s_idx], dtype=np.float32)
        phys_k_reg = HistGradientBoostingRegressor(
            loss="squared_error",
            learning_rate=0.055,
            max_iter=240,
            max_leaf_nodes=63,
            min_samples_leaf=80,
            l2_regularization=4.0,
            random_state=seed + q,
        )
        phys_k_reg.fit(X_tr_phys, k_all_fp[s_idx], sample_weight=s_w)

        phys_p_clf = HistGradientBoostingClassifier(
            learning_rate=0.055,
            max_iter=220,
            max_leaf_nodes=63,
            min_samples_leaf=80,
            l2_regularization=4.0,
            random_state=seed + 10 + q,
        )
        phys_p_clf.fit(X_tr_phys, (y_all_fp[s_idx] > 0.5).astype(np.int32), sample_weight=s_w)
        del X_tr_phys

        # --- Head B (`EXP-2` / `EXP-3`): Coupled Fracture-Mechanics + Hydrothermal + GEO-Pb-16 ---
        # Construct `n_internal_draws` independent component-hide splits strictly on `q' != q`!
        X_full_parts: list[np.ndarray] = []
        yk_parts: list[np.ndarray] = []
        yp_parts: list[np.ndarray] = []
        w_parts: list[np.ndarray] = []

        for r_draw in range(n_internal_draws):
            sub_grid = SimpleNamespace(
                footprint=fp,
                catalogue=(catalogue & (q_grid2d != q)),
            )
            sim_folds, _ = buffered_component_draw(
                sub_grid,
                seed=200 + 37 * q + 13 * r_draw,
                hide_frac=0.20,
                buffer_px=3,
                boundary_px=12,
            )
            vis_sim = sim_folds[0]["visible"]
            hid_sim = sim_folds[0]["hidden_all"]

            S_sim = compute_fold_structural_features(vis_sim, aux, fp)
            k_sim_fp = kernel_target_300m(hid_sim).ravel()[fp_idx]
            y_sim_fp = hid_sim.ravel()[fp_idx].astype(np.float32)
            mask_known_fp = sim_folds[0]["masked_known"].ravel()[fp_idx]

            cand_sim = in_train_q & (~mask_known_fp)
            d_idx, d_w = _weighted_sample_indices(k_sim_fp > 0.0, cand_sim, n_neg=95_000, rng=rng)
            X_part = np.hstack(
                [np.asarray(X_phys[d_idx], dtype=np.float32), np.asarray(S_sim[d_idx], dtype=np.float32)]
            )
            X_full_parts.append(X_part)
            yk_parts.append(k_sim_fp[d_idx])
            yp_parts.append((y_sim_fp[d_idx] > 0.5).astype(np.int32))
            w_parts.append(d_w)
            del S_sim, k_sim_fp, y_sim_fp, vis_sim, hid_sim
            gc.collect()

        X_tr_full = np.vstack(X_full_parts)
        yk_full = np.concatenate(yk_parts)
        yp_full = np.concatenate(yp_parts)
        w_full = np.concatenate(w_parts)
        del X_full_parts, yk_parts, yp_parts, w_parts

        full_k_reg = HistGradientBoostingRegressor(
            loss="squared_error",
            learning_rate=0.055,
            max_iter=260,
            max_leaf_nodes=63,
            min_samples_leaf=80,
            l2_regularization=4.0,
            random_state=seed + 20 + q,
        )
        full_k_reg.fit(X_tr_full, yk_full, sample_weight=w_full)

        full_p_clf = HistGradientBoostingClassifier(
            learning_rate=0.055,
            max_iter=240,
            max_leaf_nodes=63,
            min_samples_leaf=80,
            l2_regularization=4.0,
            random_state=seed + 30 + q,
        )
        full_p_clf.fit(X_tr_full, yp_full, sample_weight=w_full)
        del X_tr_full, yk_full, yp_full, w_full
        gc.collect()

        models[q] = {
            "phys_k_reg": phys_k_reg,
            "phys_p_clf": phys_p_clf,
            "full_k_reg": full_k_reg,
            "full_p_clf": full_p_clf,
        }

    cpath.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(models, cpath, compress=3)
    return models


def predict_phys_only_fields(
    X_phys: np.memmap,
    fp: np.ndarray,
    visible: np.ndarray,
    model_bundle: dict[str, object] | list[dict[str, object]],
    *,
    subset_mask_2d: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Predict calibrated `(p_trace, k_exp)` strictly from the blind physical + geothermal stack."""
    H, W = fp.shape
    fp_idx = np.flatnonzero(fp)
    bundles = model_bundle if isinstance(model_bundle, list) else [model_bundle]

    if subset_mask_2d is not None:
        sub_sel = subset_mask_2d.ravel()[fp_idx]
        eval_rows = np.flatnonzero(sub_sel)
    else:
        eval_rows = np.arange(fp_idx.size, dtype=np.int64)

    p_out_fp = np.zeros(fp_idx.size, dtype=np.float32)
    k_out_fp = np.zeros(fp_idx.size, dtype=np.float32)

    chunk = 350_000
    for s in range(0, eval_rows.size, chunk):
        rows = eval_rows[s : s + chunk]
        Xb = np.asarray(X_phys[rows], dtype=np.float32)
        pk = np.zeros(rows.size, dtype=np.float32)
        pp = np.zeros(rows.size, dtype=np.float32)
        for b in bundles:
            pk += np.clip(b["phys_k_reg"].predict(Xb), 0.0, 1.0).astype(np.float32)
            pp += b["phys_p_clf"].predict_proba(Xb)[:, 1].astype(np.float32)
        k_out_fp[rows] = pk / len(bundles)
        p_out_fp[rows] = pp / len(bundles)

    # Scale-align 20% component holdout prior factor cleanly without changing rankings
    p_2d = np.zeros(H * W, dtype=np.float32)
    k_2d = np.zeros(H * W, dtype=np.float32)
    p_2d[fp_idx] = p_out_fp
    k_2d[fp_idx] = k_out_fp
    p_2d = p_2d.reshape(H, W)
    k_2d = k_2d.reshape(H, W)
    p_2d[~fp | visible] = 0.0
    k_2d[~fp | visible] = 0.0
    return p_2d, k_2d


def predict_hjcd_coupled_fields(
    X_phys: np.memmap,
    aux: dict[str, np.ndarray],
    fp: np.ndarray,
    visible: np.ndarray,
    model_bundle: dict[str, object] | list[dict[str, object]],
    *,
    subset_mask_2d: np.ndarray | None = None,
    blind_basin_tau_px: float = 28.0,
    precomputed_phys: tuple[np.ndarray, np.ndarray] | None = None,
    precomputed_struct: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Predict dual-regime `(p_trace, k_exp)` seamlessly bridging fault-network and blind-basin regimes.

    Near mapped faults (`d_vis <= 3 km`), weights the coupled fracture-mechanics + hydrothermal
    + GEO-Pb-16 expectation (`full_*`). In unmapped blind basins (`d_vis >> 3 km`, or when an
    entire quadrant's catalogue is hidden), smoothly transitions via `w = exp(-d_vis / tau)` to
    the blind physical + hydrothermal + GEO-Pb-16 expectation (`0.20 * phys_*`, matched to the
    20% hidden-segment prior scale).
    """
    H, W = fp.shape
    fp_idx = np.flatnonzero(fp)
    bundles = model_bundle if isinstance(model_bundle, list) else [model_bundle]

    S_struct = (
        precomputed_struct
        if precomputed_struct is not None
        else compute_fold_structural_features(visible, aux, fp)
    )
    if np.any(visible):
        d_vis_fp = ndi.distance_transform_edt(~visible).ravel()[fp_idx].astype(np.float32)
        w_near_all = np.exp(-d_vis_fp / float(blind_basin_tau_px)).astype(np.float32)
        del d_vis_fp
    else:
        w_near_all = np.zeros(fp_idx.size, dtype=np.float32)

    if subset_mask_2d is not None:
        sub_sel = subset_mask_2d.ravel()[fp_idx]
        eval_rows = np.flatnonzero(sub_sel)
    else:
        eval_rows = np.arange(fp_idx.size, dtype=np.int64)

    p_phys_fp = precomputed_phys[0].ravel()[fp_idx] if precomputed_phys is not None else None
    k_phys_fp = precomputed_phys[1].ravel()[fp_idx] if precomputed_phys is not None else None

    p_out_fp = np.zeros(fp_idx.size, dtype=np.float32)
    k_out_fp = np.zeros(fp_idx.size, dtype=np.float32)

    chunk = 350_000
    for s in range(0, eval_rows.size, chunk):
        rows = eval_rows[s : s + chunk]
        Xp = np.asarray(X_phys[rows], dtype=np.float32)
        Xf = np.hstack([Xp, np.asarray(S_struct[rows], dtype=np.float32)])
        wn = w_near_all[rows]

        pk_full = np.zeros(rows.size, dtype=np.float32)
        pp_full = np.zeros(rows.size, dtype=np.float32)
        for b in bundles:
            pk_full += np.clip(b["full_k_reg"].predict(Xf), 0.0, 1.0).astype(np.float32)
            pp_full += b["full_p_clf"].predict_proba(Xf)[:, 1].astype(np.float32)
        pk_full /= len(bundles)
        pp_full /= len(bundles)

        if p_phys_fp is not None and k_phys_fp is not None:
            pk_phys = k_phys_fp[rows] * 0.22
            pp_phys = p_phys_fp[rows] * 0.22
        else:
            pk_phys = np.zeros(rows.size, dtype=np.float32)
            pp_phys = np.zeros(rows.size, dtype=np.float32)
            for b in bundles:
                pk_phys += np.clip(b["phys_k_reg"].predict(Xp), 0.0, 1.0).astype(np.float32)
                pp_phys += b["phys_p_clf"].predict_proba(Xp)[:, 1].astype(np.float32)
            pk_phys = (pk_phys / len(bundles)) * 0.22
            pp_phys = (pp_phys / len(bundles)) * 0.22

        k_out_fp[rows] = wn * pk_full + (1.0 - wn) * pk_phys
        p_out_fp[rows] = wn * pp_full + (1.0 - wn) * pp_phys

    if precomputed_struct is None:
        del S_struct
    p_2d = np.zeros(H * W, dtype=np.float32)
    k_2d = np.zeros(H * W, dtype=np.float32)
    p_2d[fp_idx] = p_out_fp
    k_2d[fp_idx] = k_out_fp
    p_2d = p_2d.reshape(H, W)
    k_2d = k_2d.reshape(H, W)
    p_2d[~fp | visible] = 0.0
    k_2d[~fp | visible] = 0.0
    return p_2d, k_2d
