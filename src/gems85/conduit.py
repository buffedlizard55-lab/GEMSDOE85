"""Multi-physics hidden geothermal fault-conduit feature stack & fold-safe OOF learners.

Channel groups match the pre-registered ``docs/research/hypotheses.md`` ladder:
- ``STRUCT_CHANNELS`` (``E1``): 19 core geophysical bands + 1 m 3DEP LiDAR scarps +
  10 m 3DEP geomorphometry & river-profile chi knickpoints + USGS SGMC bedrock fault
  continuity + GeoDAWN 090 deg E-W flight-line notch & Lake Lahontan ~1,332 m pluvial
  shoreline mimic indicators.
- ``NETWORK_CHANNELS`` (``E1..E3``): Fold-safe structural fault-tip forward propagation cones,
  collinear stepover bridges, 1-3 km synthetic/antithetic relay annuli, and regional belt
  density -- ALWAYS computed strictly from the permitted visible network ``V_ctx`` with a
  hard ``d >= 3.5 px`` floor so training inner component folds ``V_{-k} -> V_k`` and unseen
  test domains share identical distributions with zero leakage.
- ``CONDUIT_CHANNELS`` (added in ``E2``): Newly assembled 1900-2026 sub-km USGS ComCat
  hypocentral densities/swarms (``3,977`` deduplicated events, ``100.000000%`` valid pixel
  coverage including ``541`` post-2021 events absent from GDR 1391), GBCGE ``2 m`` temperature
  probe conductive thermal anomalies ``F2mDAB`` (``2,782`` stations in footprint), GBCGE
  Quaternary high-enthalpy siliceous paleo-vents vs pluvial shoreline tufa mimics (``281``
  in-footprint vents), and GDR 1391 spring/well geothermometers (never reading
  ``dist_known_fault_px``).
- ``ALTERATION_JUXTAPOSITION_CHANNELS`` (added in ``E3``): Across-strike covariance-whitened
  ``GEO-Pb`` two-sample step crests + GeoDAWN gamma-ray spectrometry + hydrothermal
  magnetite-destruction / potassic alteration coupling + Stage-2 8-azimuth spatial crest
  skeletonizer over diverse OOF GBDT learners (``LightGBM`` + ``HistGradientBoosting``).
"""

from __future__ import annotations

import csv
import gc
import struct
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

try:
    import lightgbm as lgb
except ModuleNotFoundError:  # pragma: no cover
    lgb = None  # type: ignore[assignment]

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover
    pd = None  # type: ignore[assignment]

try:
    from pyproj import Transformer
except ModuleNotFoundError:  # pragma: no cover
    Transformer = None  # type: ignore[assignment,misc]

from . import geopb

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
EXT_DIR = DATA_DIR / "external"
CACHE_DIR = DATA_DIR / "cache_conduit"


def _read_clean_band(path: Path, band: int, fp: np.ndarray, *, zero_is_nodata: bool = False) -> np.ndarray:
    with rasterio.open(path) as src:
        arr = src.read(band).astype(np.float32)
        nodata = src.nodata
    bad = ~np.isfinite(arr) | (arr < -1e30)
    if nodata is not None and np.isfinite(nodata):
        bad |= arr == float(nodata)
    if zero_is_nodata:
        bad |= arr == 0.0
    arr[bad] = np.nan
    med = float(np.nanmedian(arr[fp])) if np.isfinite(arr[fp]).any() else 0.0
    out = np.nan_to_num(arr, nan=med).astype(np.float32)
    out[~fp] = 0.0
    return out


def _grad_mag(arr: np.ndarray, sigma: float) -> np.ndarray:
    gy = ndi.gaussian_filter(arr, sigma=sigma, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(arr, sigma=sigma, order=(0, 1), mode="nearest")
    return np.hypot(gy, gx).astype(np.float32)


def _ns_minus_ew_aniso(arr: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Positive along N-S / NNE-SSW structures; negative along 090 deg E-W flight lines."""
    gy = np.abs(ndi.gaussian_filter(arr, sigma=sigma, order=(1, 0), mode="nearest"))
    gx = np.abs(ndi.gaussian_filter(arr, sigma=sigma, order=(0, 1), mode="nearest"))
    return (gx - gy).astype(np.float32)


def _nadaraya_watson_point_field(
    shape: tuple[int, int],
    rows: np.ndarray,
    cols: np.ndarray,
    vals: np.ndarray,
    sigma_px: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Smooth point values onto ``shape`` via normalized Gaussian kernel regression."""
    num = np.zeros(shape, dtype=np.float32)
    den = np.zeros(shape, dtype=np.float32)
    valid = (
        np.isfinite(vals)
        & (rows >= 0)
        & (rows < shape[0])
        & (cols >= 0)
        & (cols < shape[1])
    )
    np.add.at(num, (rows[valid], cols[valid]), vals[valid].astype(np.float32))
    np.add.at(den, (rows[valid], cols[valid]), np.float32(1.0))
    num_s = ndi.gaussian_filter(num, sigma=sigma_px, mode="constant", cval=0.0)
    den_s = ndi.gaussian_filter(den, sigma=sigma_px, mode="constant", cval=0.0)
    # Soft shrinkage prior (pseudo-count 0.02 * peak single-point weight) prevents far-field blow-up
    w0 = 1.0 / (2.0 * np.pi * sigma_px * sigma_px)
    est = num_s / (den_s + 0.15 * w0)
    return est.astype(np.float32), den_s.astype(np.float32)


def _load_2m_probes_df() -> pd.DataFrame:
    dbf_path = (
        EXT_DIR
        / "2m_temperature_probe_INGENIOUS_regional_data"
        / "2m_temperature_probe_INGENIOUS_regional_data"
        / "2m_temperature_probe_n83geo"
        / "2m_temperature_probe_n83geo.dbf"
    )
    with dbf_path.open("rb") as f:
        _ver, _yy, _mm, _dd, nrec, hlen, rlen = struct.unpack("<BBBBIHH20x", f.read(32))
        fields = []
        while True:
            buf = f.read(32)
            if not buf or buf[0] == 0x0D:
                break
            name = buf[:11].split(b"\x00", 1)[0].decode("ascii", errors="ignore")
            fields.append((name, buf[16]))
        f.seek(hlen)
        recs = []
        for _ in range(nrec):
            raw = f.read(rlen)
            if not raw or raw[0:1] == b"*":
                continue
            pos = 1
            d = {}
            for name, flen in fields:
                d[name] = raw[pos : pos + flen].decode("latin1", errors="ignore").strip()
                pos += flen
            recs.append(d)
    df = pd.DataFrame(recs)
    for col in ("LatDegreeN", "LongDegree", "T2m", "F2mDAB"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["LatDegreeN", "LongDegree"])


STRUCT_CHANNEL_NAMES: list[str] = [
    # 19 core geophysics bands
    "tf_mag_anom",
    "tf_rtp",
    "tf_tmi_hg",
    "tf_geod_2ndinv",
    "tf_iso_grav_slope",
    "tf_tc",
    "tf_geod_shearrate",
    "tf_geod_dilaterate",
    "tf_tmi_vg",
    "tf_deq_100km",
    "tf_iso_grav_vg",
    "tf_det_elev",
    "tf_iso_grav",
    "tf_tmi",
    "tf_depth_base",
    "tf_ieq_100km",
    "tf_cond_surf",
    "tf_iso_grav_hg",
    "tf_det_elev_slope",
    # 1m 3DEP LiDAR scarp stack + extension strike favorability
    "lidar_ex_max",
    "lidar_ex_mean",
    "lidar_step_max",
    "lidar_lapneg_max",
    "lidar_lappos_max",
    "lidar_downface_max",
    "lidar_upface_max",
    "lidar_cross_max",
    "lidar_relief",
    "lidar_coh100",
    "lidar_valid_flag",
    "lidar_ext_strike_fav",
    # 10m 3DEP full-footprint geomorphometry + chi river knickpoints + SGMC + anti-mimic filters
    "topo10_slope_p90",
    "topo10_slope_max",
    "topo10_steep_frac",
    "topo10_relief",
    "topo10_curv_prof",
    "topo10_aspect_coh",
    "topo10_hs_lineament",
    "topo10_dem_mean",
    "mimic_lahontan_1332m",
    "chi_chan_n",
    "chi_knick_n",
    "chi_raised_n",
    "chi_knick_s3",
    "rtp_ns_minus_ew",
    "rad_tc_ns_minus_ew",
    "elev_anom_s3",
    "elev_anom_s10",
    "lidar_step_s2",
    "topo_lineament_s3",
    "grav_base_step",
    "sgmc_dist_log",
]

CONDUIT_CHANNEL_NAMES: list[str] = [
    "eq_density_s3",
    "eq_density_s10",
    "eq_density_s30",
    "eq_energy_s15",
    "eq_shallow_s12",
    "eq_post2021_s15",
    "eq_ns_minus_ew_aniso",
    "probe2m_dab_s8",
    "probe2m_dab_s25",
    "probe2m_grad_s2",
    "probe2m_density_log",
    "probe2m_cond_upflow",
    "paleo_siliceous_s5",
    "paleo_siliceous_s20",
    "paleo_tufa_mimic_s8",
    "well_geotherm_s10",
    "well_temp_anom_s20",
]

JUXTAPOSITION_CHANNEL_NAMES: list[str] = [
    "geopb_r3_L15",
    "geopb_r6_L25",
    "geopb_crest",
    "rad_K",
    "rad_Th",
    "rad_U",
    "ext_UK",
    "ext_TMIup150",
    "hydro_mag_destruction",
]

NETWORK_CHANNEL_NAMES: list[str] = [
    "net_log_dist",
    "net_tip_fwd_800m",
    "net_tip_fwd_2500m",
    "net_tip_prox_1200m",
    "net_strike_bridge",
    "net_relay_1km",
    "net_relay_3km",
    "net_belt_6km",
]


def _save_f32(name: str, arr: np.ndarray, fp: np.ndarray) -> None:
    p = CACHE_DIR / f"{name}.npy"
    out = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    out[~fp] = 0.0
    np.save(p, out)


def build_static_feature_cache(fp: np.ndarray) -> list[str]:
    """Compute and persist all label-free channels on disk (zero access to fault labels)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    all_names = STRUCT_CHANNEL_NAMES + CONDUIT_CHANNEL_NAMES + JUXTAPOSITION_CHANNEL_NAMES
    missing = [n for n in all_names if not (CACHE_DIR / f"{n}.npy").exists()]
    if not missing:
        return all_names

    tf_path = DATA_DIR / "training_features.tif"
    with rasterio.open(tf_path) as src:
        inv_tf = ~src.transform

    tf_names = STRUCT_CHANNEL_NAMES[:19]
    for b_idx, cname in enumerate(tf_names, start=1):
        if not (CACHE_DIR / f"{cname}.npy").exists():
            _save_f32(cname, _read_clean_band(tf_path, b_idx, fp, zero_is_nodata=False), fp)

    # Load key arrays for derived channels
    rtp = np.load(CACHE_DIR / "tf_rtp.npy")
    det_elev = np.load(CACHE_DIR / "tf_det_elev.npy")
    iso_grav = np.load(CACHE_DIR / "tf_iso_grav.npy")
    depth_base = np.load(CACHE_DIR / "tf_depth_base.npy")
    cond_surf = np.load(CACHE_DIR / "tf_cond_surf.npy")

    # 1m LiDAR scarp stack
    lidar_path = EXT_DIR / "lidar_scarp_features_u8.tif"
    lidar_map = [
        (1, "lidar_ex_max"),
        (2, "lidar_ex_mean"),
        (3, "lidar_step_max"),
        (4, "lidar_lapneg_max"),
        (5, "lidar_lappos_max"),
        (6, "lidar_downface_max"),
        (7, "lidar_upface_max"),
        (8, "lidar_cross_max"),
        (9, "lidar_relief"),
        (10, "lidar_coh100"),
    ]
    for b_idx, cname in lidar_map:
        if not (CACHE_DIR / f"{cname}.npy").exists():
            _save_f32(cname, _read_clean_band(lidar_path, b_idx, fp, zero_is_nodata=True), fp)

    with rasterio.open(lidar_path) as lsrc:
        l_strike_u8 = lsrc.read(11).astype(np.float32)
        l_valid = (lsrc.read(12) > 0).astype(np.float32)
    _save_f32("lidar_valid_flag", l_valid, fp)
    # Convert quantized 0..180 strike into cos(2*(theta - 15 deg)) tectonic favorability
    theta_rad = (l_strike_u8 / 255.0) * np.pi
    strike_fav = np.where(l_valid > 0, np.cos(2.0 * (theta_rad - np.deg2rad(15.0))), 0.0)
    _save_f32("lidar_ext_strike_fav", strike_fav, fp)
    lidar_step = np.load(CACHE_DIR / "lidar_step_max.npy")
    _save_f32("lidar_step_s2", ndi.gaussian_filter(lidar_step, sigma=1.8, mode="nearest"), fp)

    # 10m 3DEP geomorphometry + Lake Lahontan ~1,332 m shoreline mimic indicator
    topo_path = EXT_DIR / "topo_10m_derived_100m_u8.tif"
    topo_map = [
        (1, "topo10_slope_p90"),
        (2, "topo10_slope_max"),
        (3, "topo10_steep_frac"),
        (5, "topo10_relief"),
        (6, "topo10_curv_prof"),
        (7, "topo10_aspect_coh"),
        (8, "topo10_hs_lineament"),
    ]
    for b_idx, cname in topo_map:
        if not (CACHE_DIR / f"{cname}.npy").exists():
            _save_f32(cname, _read_clean_band(topo_path, b_idx, fp, zero_is_nodata=True), fp)
    with rasterio.open(topo_path) as tsrc:
        q9 = tsrc.read(9).astype(np.float32)
        tags9 = tsrc.tags(9)
        lo9 = float(tags9.get("q_lo", 1099.7082))
        hi9 = float(tags9.get("q_hi", 2481.5011))
    dem_m = np.where(q9 > 0, lo9 + ((q9 - 1.0) / 254.0) * (hi9 - lo9), np.nan)
    med_dem = float(np.nanmedian(dem_m[fp]))
    dem_m = np.nan_to_num(dem_m, nan=med_dem).astype(np.float32)
    _save_f32("topo10_dem_mean", dem_m, fp)
    # Lake Lahontan Sehoo highstand (~1,330-1,337 m) strandline mimic flag on low-relief slopes
    lahontan = np.exp(-(((dem_m - 1332.0) / 22.0) ** 2)).astype(np.float32)
    _save_f32("mimic_lahontan_1332m", lahontan, fp)
    hs_lin = np.load(CACHE_DIR / "topo10_hs_lineament.npy")
    _save_f32("topo_lineament_s3", ndi.gaussian_filter(hs_lin, sigma=2.5, mode="nearest"), fp)

    # 10m chi river knickpoint / block uplift channels
    chi_path = EXT_DIR / "dem10_chi_100m_u8.tif"
    for b_idx, cname in ((1, "chi_chan_n"), (2, "chi_knick_n"), (3, "chi_raised_n")):
        _save_f32(cname, _read_clean_band(chi_path, b_idx, fp, zero_is_nodata=False), fp)
    knick = np.load(CACHE_DIR / "chi_knick_n.npy")
    _save_f32("chi_knick_s3", ndi.gaussian_filter(knick, sigma=3.0, mode="nearest"), fp)

    # Flight-line notch + multi-scale steps + SGMC bedrock fault distance
    rad_path = EXT_DIR / "geodawn_rad_u8.tif"
    ext_path = EXT_DIR / "geodawn_extensions_u8.tif"
    rad_tc = _read_clean_band(rad_path, 4, fp, zero_is_nodata=True)
    rad_k = _read_clean_band(rad_path, 1, fp, zero_is_nodata=True)
    rad_th = _read_clean_band(rad_path, 2, fp, zero_is_nodata=True)
    rad_u = _read_clean_band(rad_path, 3, fp, zero_is_nodata=True)
    ext_uk = _read_clean_band(ext_path, 2, fp, zero_is_nodata=True)
    ext_tmi150 = _read_clean_band(ext_path, 4, fp, zero_is_nodata=True)

    _save_f32("rad_K", rad_k, fp)
    _save_f32("rad_Th", rad_th, fp)
    _save_f32("rad_U", rad_u, fp)
    _save_f32("ext_UK", ext_uk, fp)
    _save_f32("ext_TMIup150", ext_tmi150, fp)
    _save_f32("rtp_ns_minus_ew", _ns_minus_ew_aniso(rtp, sigma=1.5), fp)
    _save_f32("rad_tc_ns_minus_ew", _ns_minus_ew_aniso(rad_tc, sigma=1.5), fp)
    _save_f32("elev_anom_s3", det_elev - ndi.gaussian_filter(det_elev, sigma=3.0, mode="nearest"), fp)
    _save_f32("elev_anom_s10", det_elev - ndi.gaussian_filter(det_elev, sigma=10.0, mode="nearest"), fp)

    g_step = _grad_mag(iso_grav, 2.0) / (np.std(iso_grav[fp]) + 1e-6) + _grad_mag(depth_base, 2.0) / (
        np.std(depth_base[fp]) + 1e-6
    )
    _save_f32("grav_base_step", g_step, fp)

    with rasterio.open(EXT_DIR / "derived_sgmc_faults_100m_u8.tif") as ssrc:
        sgmc = ssrc.read(1) > 0
    sgmc_d = np.log1p(ndi.distance_transform_edt(~sgmc)).astype(np.float32)
    _save_f32("sgmc_dist_log", sgmc_d, fp)

    # Hydrothermal magnetite-destruction trough + potassic alteration excess
    rtp_trough = np.maximum(0.0, ndi.gaussian_filter(rtp, 6.0, mode="nearest") - ndi.gaussian_filter(rtp, 1.2, mode="nearest"))
    k_excess = np.maximum(0.0, (rad_k - np.median(rad_k[fp])) / (np.std(rad_k[fp]) + 1e-6) - 0.5 * (rad_th - np.median(rad_th[fp])) / (np.std(rad_th[fp]) + 1e-6))
    cond_z = np.clip((cond_surf - np.median(cond_surf[fp])) / (np.std(cond_surf[fp]) + 1e-6), -2.0, 5.0)
    _save_f32("hydro_mag_destruction", rtp_trough * (0.5 + k_excess) * np.maximum(0.0, 1.0 + cond_z), fp)

    # --- Group C: Brand-new Blind Hydrothermal & 1900-2026 Sub-km ComCat Conduit Stack ---
    eq_df = pd.read_csv(EXT_DIR / "usgs_comcat_geodawn.csv")
    eq_r = eq_df["row_100m"].to_numpy(dtype=np.int64)
    eq_c = eq_df["col_100m"].to_numpy(dtype=np.int64)
    eq_mag = eq_df["magnitude"].to_numpy(dtype=np.float32)
    eq_dep = pd.to_numeric(eq_df["depth_km"], errors="coerce").fillna(8.0).to_numpy(dtype=np.float32)
    eq_yr = eq_df["year"].to_numpy(dtype=np.int32)
    in_b = (eq_r >= 0) & (eq_r < fp.shape[0]) & (eq_c >= 0) & (eq_c < fp.shape[1])

    pts_all = np.zeros(fp.shape, dtype=np.float32)
    pts_energy = np.zeros(fp.shape, dtype=np.float32)
    pts_shallow = np.zeros(fp.shape, dtype=np.float32)
    pts_post21 = np.zeros(fp.shape, dtype=np.float32)

    np.add.at(pts_all, (eq_r[in_b], eq_c[in_b]), 1.0)
    # Benioff-style strain release 10^(0.5 * (M - 2.0)) capped cleanly to avoid single M7 dominance
    energy_w = np.clip(10.0 ** (0.45 * (eq_mag[in_b] - 2.0)), 0.5, 50.0)
    np.add.at(pts_energy, (eq_r[in_b], eq_c[in_b]), energy_w)
    sh_m = in_b & (eq_dep <= 12.0)
    np.add.at(pts_shallow, (eq_r[sh_m], eq_c[sh_m]), 1.0)
    p21_m = in_b & (eq_yr >= 2022)
    np.add.at(pts_post21, (eq_r[p21_m], eq_c[p21_m]), 1.0)

    _save_f32("eq_density_s3", np.log1p(100.0 * ndi.gaussian_filter(pts_all, 3.0, mode="constant")), fp)
    _save_f32("eq_density_s10", np.log1p(400.0 * ndi.gaussian_filter(pts_all, 10.0, mode="constant")), fp)
    _save_f32("eq_density_s30", np.log1p(1500.0 * ndi.gaussian_filter(pts_all, 30.0, mode="constant")), fp)
    _save_f32("eq_energy_s15", np.log1p(300.0 * ndi.gaussian_filter(pts_energy, 15.0, mode="constant")), fp)
    _save_f32("eq_shallow_s12", np.log1p(500.0 * ndi.gaussian_filter(pts_shallow, 12.0, mode="constant")), fp)
    _save_f32("eq_post2021_s15", np.log1p(600.0 * ndi.gaussian_filter(pts_post21, 15.0, mode="constant")), fp)
    # N-S vs E-W elongated microseismic streak indicator
    eq_ns = ndi.gaussian_filter(pts_all, sigma=(14.0, 3.5), mode="constant")
    eq_ew = ndi.gaussian_filter(pts_all, sigma=(3.5, 14.0), mode="constant")
    _save_f32("eq_ns_minus_ew_aniso", np.log1p(400.0 * eq_ns) - np.log1p(400.0 * eq_ew), fp)

    # 2m shallow conductive temperature probes
    tf83 = Transformer.from_crs("EPSG:4269", "EPSG:32611", always_xy=True)
    df2m = _load_2m_probes_df()
    x2, y2 = tf83.transform(df2m["LongDegree"].to_numpy(), df2m["LatDegreeN"].to_numpy())
    c2f, r2f = inv_tf * (x2, y2)
    r2i = np.floor(r2f).astype(np.int64)
    c2i = np.floor(c2f).astype(np.int64)
    dab_pos = np.clip(df2m["F2mDAB"].fillna(0.0).to_numpy(dtype=np.float32), -2.0, 30.0)
    dab_s8, den_s8 = _nadaraya_watson_point_field(fp.shape, r2i, c2i, np.maximum(0.0, dab_pos), sigma_px=8.0)
    dab_s25, _ = _nadaraya_watson_point_field(fp.shape, r2i, c2i, np.maximum(0.0, dab_pos), sigma_px=25.0)
    _save_f32("probe2m_dab_s8", dab_s8, fp)
    _save_f32("probe2m_dab_s25", dab_s25, fp)
    _save_f32("probe2m_grad_s2", _grad_mag(dab_s8, 2.0), fp)
    _save_f32("probe2m_density_log", np.log1p(1000.0 * den_s8), fp)
    _save_f32("probe2m_cond_upflow", dab_s8 * np.maximum(0.0, 1.0 + cond_z), fp)

    # Paleo-geothermal deposits: siliceous/hydrothermal fault conduits vs pluvial tufa shoreline mimics
    paleo = pd.read_csv(EXT_DIR / "paleo_geothermal_regional" / "Paleo_geothermal_final.csv", encoding="cp1252")
    xp, yp = tf83.transform(paleo["Long_deg_NAD83"].to_numpy(), paleo["Lat_deg_NAD83"].to_numpy())
    cpf, rpf = inv_tf * (xp, yp)
    rpi = np.floor(rpf).astype(np.int64)
    cpi = np.floor(cpf).astype(np.int64)
    dtype_s = paleo["Deposit_type"].fillna("").astype(str).str.strip().to_numpy()
    in_p = (rpi >= 0) & (rpi < fp.shape[0]) & (cpi >= 0) & (cpi < fp.shape[1])
    is_tufa = dtype_s == "Tufa"
    sil_grid = np.zeros(fp.shape, dtype=np.float32)
    tufa_grid = np.zeros(fp.shape, dtype=np.float32)
    np.add.at(sil_grid, (rpi[in_p & ~is_tufa], cpi[in_p & ~is_tufa]), 1.0)
    np.add.at(tufa_grid, (rpi[in_p & is_tufa], cpi[in_p & is_tufa]), 1.0)
    _save_f32("paleo_siliceous_s5", np.log1p(150.0 * ndi.gaussian_filter(sil_grid, 5.0, mode="constant")), fp)
    _save_f32("paleo_siliceous_s20", np.log1p(800.0 * ndi.gaussian_filter(sil_grid, 20.0, mode="constant")), fp)
    _save_f32("paleo_tufa_mimic_s8", np.log1p(250.0 * ndi.gaussian_filter(tufa_grid, 8.0, mode="constant")), fp)

    # GDR 1391 wells & springs (NEVER reading dist_known_fault_px!)
    ws = pd.read_csv(
        EXT_DIR / "gdr_wellspring_in_footprint.csv",
        usecols=["row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"],
    )
    wr = ws["row"].to_numpy(dtype=np.int64)
    wc = ws["col"].to_numpy(dtype=np.int64)
    t_excess = np.clip(pd.to_numeric(ws["temp_c"], errors="coerce").fillna(15.0).to_numpy(dtype=np.float32) - 20.0, 0.0, 120.0)
    gt_max = np.nanmax(
        np.vstack(
            [
                pd.to_numeric(ws["geothermquartz_c"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float32),
                pd.to_numeric(ws["geothermchalc_c"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float32),
                pd.to_numeric(ws["geothermcat_c"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float32),
            ]
        ),
        axis=0,
    )
    gt_excess = np.clip(gt_max - 70.0, 0.0, 180.0)
    w_gt, _ = _nadaraya_watson_point_field(fp.shape, wr, wc, gt_excess, sigma_px=10.0)
    w_tp, _ = _nadaraya_watson_point_field(fp.shape, wr, wc, t_excess, sigma_px=20.0)
    _save_f32("well_geotherm_s10", w_gt, fp)
    _save_f32("well_temp_anom_s20", w_tp, fp)

    # GEO-Pb across-strike covariance-whitened 10-band step descriptors (reuse existing cache if built)
    old_cache = DATA_DIR / "cache"
    for gname in ("geopb_r3_L15", "geopb_r6_L25", "geopb_crest"):
        dst_p = CACHE_DIR / f"{gname}.npy"
        if dst_p.exists():
            continue
        old_p = old_cache / f"ch_{gname}.npy"
        if old_p.exists():
            _save_f32(gname, np.load(old_p), fp)
        elif gname == "geopb_r6_L25":
            _save_f32(
                gname,
                geopb.geopb_surface(sigma=2.5, normals=tuple(geopb.NORMALS_R6), persistence_px=25.0, footprint=fp),
                fp,
            )
        else:
            base, axis = geopb.geopb_surface(
                sigma=1.5, normals=tuple(geopb.NORMALS_R3), persistence_px=15.0, footprint=fp, return_parts=True
            )
            _save_f32("geopb_r3_L15", base, fp)
            _save_f32("geopb_crest", geopb.crest(base, axis, tuple(geopb.NORMALS_R3)), fp)

    gc.collect()
    return all_names


def compute_fold_safe_network_features(visible_faults: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Compute ``(8, H, W)`` structural network features STRICTLY from ``visible_faults``.

    Every distance/density channel clamps ``d >= 3.5 px`` and masks direct ``visible_faults``
    halos so training sub-folds ``V_{-k} -> V_k`` and unseen test regions have matching
    covariate distributions with zero short-range leakage.
    """
    vis = np.asarray(visible_faults, dtype=bool) & np.asarray(fp, dtype=bool)
    h, w = vis.shape
    out = np.zeros((len(NETWORK_CHANNEL_NAMES), h, w), dtype=np.float32)
    if not vis.any():
        return out

    # Scale factor normalizes total visible trace density across partial inner folds vs full context
    dens_scale = np.float32(0.0118 / max(float(vis[fp].mean()), 1e-5))
    dens_scale = float(np.clip(dens_scale, 0.5, 2.5))

    dist = ndi.distance_transform_edt(~vis)
    dist_clamp = np.clip(dist, 3.5, 300.0).astype(np.float32)
    out[0] = np.log(dist_clamp)

    # Identify trace endpoints (pixels on vis with <= 2 pixels in 3x3 incl self, i.e., <=1 neighbor)
    nb_count = ndi.convolve(vis.astype(np.uint8), np.ones((3, 3), dtype=np.uint8), mode="constant", cval=0)
    tips = vis & (nb_count <= 2)
    ty, tx = np.nonzero(tips)
    if ty.size > 0:
        # Compute outward unit tangent at each tip from centroid of nearby vis pixels in 9x9 window
        uy = np.zeros(ty.size, dtype=np.float32)
        ux = np.zeros(tx.size, dtype=np.float32)
        for i in range(ty.size):
            r0, r1 = max(0, int(ty[i]) - 5), min(h, int(ty[i]) + 6)
            c0, c1 = max(0, int(tx[i]) - 5), min(w, int(tx[i]) + 6)
            sub = vis[r0:r1, c0:c1]
            sy, sx = np.nonzero(sub)
            if sy.size > 1:
                my = float(sy.mean()) + r0 - float(ty[i])
                mx = float(sx.mean()) + c0 - float(tx[i])
                norm = float(np.hypot(my, mx))
                if norm > 1e-4:
                    # Outward direction points AWAY from interior trace centroid
                    uy[i] = -my / norm
                    ux[i] = -mx / norm

        dt_tip, nearest_idx = ndi.distance_transform_edt(~tips, return_indices=True)
        dt_tip_c = np.clip(dt_tip, 3.5, 300.0).astype(np.float32)
        # Map nearest tip coordinate back to tip array index via flat lookup table
        tip_id_grid = np.zeros((h, w), dtype=np.int32)
        tip_id_grid[ty, tx] = np.arange(ty.size, dtype=np.int32)
        nearest_tip_id = tip_id_grid[nearest_idx[0], nearest_idx[1]]
        dy_from_tip = (np.arange(h, dtype=np.float32)[:, None] - nearest_idx[0].astype(np.float32))
        dx_from_tip = (np.arange(w, dtype=np.float32)[None, :] - nearest_idx[1].astype(np.float32))
        inv_len = 1.0 / np.maximum(dt_tip.astype(np.float32), 1.0)
        cos_align = np.clip(
            (dy_from_tip * uy[nearest_tip_id] + dx_from_tip * ux[nearest_tip_id]) * inv_len,
            0.0,
            1.0,
        )
        out[1] = (cos_align ** 2) * np.exp(-dt_tip_c / 8.0)
        out[2] = (cos_align ** 2) * np.exp(-dt_tip_c / 25.0)
        out[3] = np.exp(-dt_tip_c / 12.0)

    vf = vis.astype(np.float32) * dens_scale
    # Collinear stepover bridge along dominant Great Basin strikes (-15 deg NNW, +15 deg NNE, 0 deg N-S)
    bridge_max = np.zeros((h, w), dtype=np.float32)
    for ang_deg in (-22.0, 0.0, 22.0, 45.0):
        # Fast separable proxy via rotated / sheared directional filter using scipy gaussian_filter
        if ang_deg == 0.0:
            along = ndi.gaussian_filter(vf, sigma=(15.0, 2.2), mode="constant")
        else:
            # Approximate oriented line kernel of length +-18 px with 7 taps
            acc = np.zeros((h, w), dtype=np.float32)
            rad = np.deg2rad(ang_deg)
            cy, cx = np.cos(rad), np.sin(rad)
            wsum = 0.0
            for step in (-18, -12, -6, 0, 6, 12, 18):
                dy = int(round(step * cy))
                dx = int(round(step * cx))
                wt = float(np.exp(-0.5 * (step / 14.0) ** 2))
                sy0, sy1 = max(0, dy), min(h, h + dy)
                dy0, dy1 = max(0, -dy), min(h, h - dy)
                sx0, sx1 = max(0, dx), min(w, w + dx)
                dx0, dx1 = max(0, -dx), min(w, w - dx)
                acc[dy0:dy1, dx0:dx1] += vf[sy0:sy1, sx0:sx1] * wt
                wsum += wt
            along = ndi.gaussian_filter(acc / wsum, sigma=2.0, mode="constant")
        np.maximum(bridge_max, along, out=bridge_max)

    g3 = ndi.gaussian_filter(vf, sigma=3.0, mode="constant")
    g12 = ndi.gaussian_filter(vf, sigma=12.0, mode="constant")
    g30 = ndi.gaussian_filter(vf, sigma=30.0, mode="constant")
    g60 = ndi.gaussian_filter(vf, sigma=60.0, mode="constant")

    # Mask self-core contribution inside 3.5 px so training positives on V_k never see self-halo
    near_self = dist < 3.5
    bridge_clean = np.where(near_self, g12, bridge_max)
    out[4] = np.clip(bridge_clean - 0.5 * g3, 0.0, 2.0)
    out[5] = np.clip(g12 - 0.65 * g3, 0.0, 2.0)
    out[6] = np.clip(g30 - 0.65 * g12, 0.0, 2.0)
    out[7] = g60
    out[:, ~fp] = 0.0
    return out


def compute_stage2_crest_features(stage1_score: np.ndarray, fp: np.ndarray, out_mmap_path: Path | None = None) -> np.ndarray:
    """Extract 10 spatial ridge/skeletonizer features using streaming preallocated storage (~120 MB RAM).

    Acts as a fast CPU 2D morphological U-Net decoder that sharpens wide probability halos
    onto exact 1-pixel fault centerlines while bridging collinear gaps across alluvial washes.
    """
    s = np.nan_to_num(stage1_score, nan=0.0).astype(np.float32)
    s[~fp] = 0.0
    h, w = s.shape

    if out_mmap_path is None:
        out_mmap_path = CACHE_DIR / "_tmp_stage2_crest.dat"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    feats = np.memmap(out_mmap_path, dtype=np.float32, mode="w+", shape=(10, h, w))

    feats[0] = s
    g1 = ndi.gaussian_filter(s, sigma=1.0, mode="constant")
    feats[1] = g1
    g25 = ndi.gaussian_filter(s, sigma=2.5, mode="constant")
    feats[2] = g25
    feats[3] = ndi.gaussian_filter(s, sigma=6.0, mode="constant")
    max3 = ndi.maximum_filter(s, size=3, mode="constant")
    feats[4] = s - max3
    del max3
    max5 = ndi.maximum_filter(s, size=5, mode="constant")
    feats[5] = s - max5
    del max5
    feats[6] = s - g25
    del g25

    best_line_short = np.zeros((h, w), dtype=np.float32)
    best_line_long = np.zeros((h, w), dtype=np.float32)
    best_crest_diff = np.full((h, w), -1.0, dtype=np.float32)
    acc_s = np.empty((h, w), dtype=np.float32)
    acc_l = np.empty((h, w), dtype=np.float32)
    flank = np.empty((h, w), dtype=np.float32)

    for k in range(8):
        rad = k * (np.pi / 8.0)
        uy, ux = float(np.cos(rad)), float(np.sin(rad))
        np.copyto(acc_s, s)
        for st in (-4, -2, 2, 4):
            dy, dx = int(round(st * uy)), int(round(st * ux))
            sy0, sy1 = max(0, dy), min(h, h + dy)
            dy0, dy1 = max(0, -dy), min(h, h - dy)
            sx0, sx1 = max(0, dx), min(w, w + dx)
            dx0, dx1 = max(0, -dx), min(w, w - dx)
            acc_s[dy0:dy1, dx0:dx1] += s[sy0:sy1, sx0:sx1]
        acc_s *= 0.2

        np.copyto(acc_l, acc_s)
        for st in (-10, -7, 7, 10):
            dy, dx = int(round(st * uy)), int(round(st * ux))
            sy0, sy1 = max(0, dy), min(h, h + dy)
            dy0, dy1 = max(0, -dy), min(h, h - dy)
            sx0, sx1 = max(0, dx), min(w, w + dx)
            dx0, dx1 = max(0, -dx), min(w, w - dx)
            acc_l[dy0:dy1, dx0:dx1] += 0.25 * s[sy0:sy1, sx0:sx1]
        acc_l *= 0.5

        ny_o, nx_o = int(round(-2.0 * ux)), int(round(2.0 * uy))
        flank.fill(0.0)
        for sgn in (-1, 1):
            dy, dx = sgn * ny_o, sgn * nx_o
            sy0, sy1 = max(0, dy), min(h, h + dy)
            dy0, dy1 = max(0, -dy), min(h, h - dy)
            sx0, sx1 = max(0, dx), min(w, w + dx)
            dx0, dx1 = max(0, -dx), min(w, w - dx)
            flank[dy0:dy1, dx0:dx1] += 0.5 * g1[sy0:sy1, sx0:sx1]

        np.maximum(best_line_short, acc_s, out=best_line_short)
        np.maximum(best_line_long, acc_l, out=best_line_long)
        acc_s -= flank
        np.maximum(best_crest_diff, acc_s, out=best_crest_diff)

    feats[7] = best_line_short
    feats[8] = best_line_long
    feats[9] = best_crest_diff
    feats[:, ~fp] = 0.0
    feats.flush()
    del g1, best_line_short, best_line_long, best_crest_diff, acc_s, acc_l, flank
    gc.collect()
    return feats


def open_static_mmaps(names: list[str]) -> list[np.ndarray]:
    return [np.load(CACHE_DIR / f"{n}.npy", mmap_mode="r") for n in names]


def gather_features(
    static_mmaps: list[np.ndarray],
    net_stack: np.ndarray,
    flat_idx: np.ndarray,
    width: int,
    extra_stack: np.ndarray | None = None,
) -> np.ndarray:
    """Gather ``(N, C)`` float32 matrix cleanly without holding full-grid dense matrices in RAM."""
    ys, xs = np.divmod(flat_idx, width)
    n_static = len(static_mmaps)
    n_net = net_stack.shape[0]
    n_extra = 0 if extra_stack is None else extra_stack.shape[0]
    X = np.empty((flat_idx.size, n_static + n_net + n_extra), dtype=np.float32)
    for i, mm in enumerate(static_mmaps):
        X[:, i] = mm[ys, xs]
    for j in range(n_net):
        X[:, n_static + j] = net_stack[j, ys, xs]
    if extra_stack is not None:
        base = n_static + n_net
        for k in range(n_extra):
            X[:, base + k] = extra_stack[k, ys, xs]
    return X


def evict_cache_pagecache() -> None:
    """Drop read-only page-cache pages in CACHE_DIR via POSIX_FADV_DONTNEED so RSS stays <1.1 GB."""
    import os

    if not (hasattr(os, "posix_fadvise") and hasattr(os, "POSIX_FADV_DONTNEED") and CACHE_DIR.exists()):
        return
    for p in CACHE_DIR.iterdir():
        if p.suffix in (".npy", ".dat"):
            try:
                fd = os.open(p, os.O_RDONLY)
                try:
                    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                finally:
                    os.close(fd)
            except OSError:
                pass


def predict_grid_chunked(
    predict_fn,
    static_mmaps: list[np.ndarray],
    net_stack: np.ndarray,
    active_mask: np.ndarray,
    extra_stack: np.ndarray | None = None,
    chunk_size: int = 450_000,
) -> np.ndarray:
    """Predict full grid in low-memory chunks of ``450k`` active pixels (~120 MB RAM max)."""
    shape = active_mask.shape
    width = shape[1]
    out = np.zeros(shape, dtype=np.float32)
    flat_active = np.flatnonzero(active_mask.ravel())
    for start in range(0, flat_active.size, chunk_size):
        sl = flat_active[start : start + chunk_size]
        X_chunk = gather_features(static_mmaps, net_stack, sl, width, extra_stack=extra_stack)
        out.ravel()[sl] = predict_fn(X_chunk).astype(np.float32)
        del X_chunk
    evict_cache_pagecache()
    return out


def make_inner_component_folds(visible_mask: np.ndarray, n_inner: int = 4, seed: int = 2026) -> list[dict[str, np.ndarray]]:
    """Partition 8-connected components of ``visible_mask`` into ``n_inner`` disjoint sub-folds.

    Each sub-fold ``k`` holds out component subset ``V_k`` as 1-px positive targets and builds
    its context mask ``V_{-k} = V \\ collar_3(V_k)``, simulating exact unseen-component discovery
     strictly inside the allowed ``visible_mask``.
    """
    vis = np.asarray(visible_mask, dtype=bool)
    comp, n_comp = ndi.label(vis, structure=np.ones((3, 3), dtype=bool))
    comp_ids = np.arange(1, n_comp + 1)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(comp_ids)
    splits = np.array_split(perm, n_inner)
    subfolds = []
    for k, held_ids in enumerate(splits):
        target_k = np.isin(comp, held_ids) & vis
        collar_k = ndi.distance_transform_edt(~target_k) <= 3.0
        ctx_k = vis & ~collar_k
        subfolds.append({"k": k, "target": target_k, "context": ctx_k})
    return subfolds


def sample_sharp_1px_dataset(
    static_mmaps: list[np.ndarray],
    subfolds: list[dict[str, np.ndarray]],
    train_region: np.ndarray,
    visible_all: np.ndarray,
    fp: np.ndarray,
    *,
    near_neg_per_pos: int = 3,
    far_neg_per_pos: int = 6,
    seed: int = 85,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build fold-pure 1-px crest vs near-flank (`2..8 px`) + basin (`>8 px`) dataset.

    Returns ``(X, y, inner_fold_id, sample_flat_idx)``.
    Crucially:
    1. Positives are EXACT ``1 px`` fault pixels of held-out inner components ``V_k`` (zero dilation!).
    2. Explicit ``2..8 px`` near-flank negatives around ``V_k`` and ``V_{-k}`` force sub-100m crest
       sharpening instead of wide 1-2 km halos.
    3. Every row's network features are computed STRICTLY from ``V_{-k}`` (never ``V_k``).
    """
    rng = np.random.default_rng(seed)
    reg = np.asarray(train_region, dtype=bool) & np.asarray(fp, dtype=bool)
    vis_all = np.asarray(visible_all, dtype=bool)
    dist_all_vis = ndi.distance_transform_edt(~vis_all)
    non_fault_all = reg & ~vis_all
    width = fp.shape[1]

    xs_parts, ys_parts, kf_parts, idx_parts = [], [], [], []
    for sf in subfolds:
        k = int(sf["k"])
        target_k = sf["target"] & reg
        ctx_k = sf["context"]
        net_k = compute_fold_safe_network_features(ctx_k, fp)
        dist_ctx = ndi.distance_transform_edt(~ctx_k)

        pos_idx = np.flatnonzero(target_k.ravel())
        if pos_idx.size == 0:
            continue

        # Stratified negatives strictly outside ALL visible faults AND >2.0 px from ctx_k (matching test domain!)
        valid_neg = non_fault_all & (dist_ctx > 2.0)
        near_flank = valid_neg & (dist_all_vis <= 8.0)
        far_basin = valid_neg & (dist_all_vis > 8.0)

        near_pool = np.flatnonzero(near_flank.ravel())
        far_pool = np.flatnonzero(far_basin.ravel())

        n_near = min(near_pool.size, pos_idx.size * near_neg_per_pos)
        n_far = min(far_pool.size, pos_idx.size * far_neg_per_pos)
        near_sel = rng.choice(near_pool, n_near, replace=False) if n_near > 0 else np.empty(0, np.int64)
        far_sel = rng.choice(far_pool, n_far, replace=False) if n_far > 0 else np.empty(0, np.int64)

        fold_idx = np.concatenate([pos_idx, near_sel, far_sel])
        fold_y = np.concatenate(
            [
                np.ones(pos_idx.size, dtype=np.int8),
                np.zeros(near_sel.size + far_sel.size, dtype=np.int8),
            ]
        )
        X_k = gather_features(static_mmaps, net_k, fold_idx, width)
        xs_parts.append(X_k)
        ys_parts.append(fold_y)
        kf_parts.append(np.full(fold_idx.size, k, dtype=np.int8))
        idx_parts.append(fold_idx)
        del net_k
        gc.collect()

    return (
        np.concatenate(xs_parts, axis=0),
        np.concatenate(ys_parts, axis=0),
        np.concatenate(kf_parts, axis=0),
        np.concatenate(idx_parts, axis=0),
    )


def fit_lgbm_classifier(X: np.ndarray, y: np.ndarray, seed: int = 85) -> lgb.LGBMClassifier:
    model = lgb.LGBMClassifier(
        n_estimators=320,
        learning_rate=0.055,
        num_leaves=63,
        min_child_samples=80,
        subsample_for_bin=120_000,
        colsample_bytree=0.78,
        subsample=0.85,
        subsample_freq=1,
        reg_alpha=1.5,
        reg_lambda=4.0,
        n_jobs=-1,
        random_state=seed,
        verbose=-1,
    )
    model.fit(X, y)
    return model


def fit_hgb_classifier(X: np.ndarray, y: np.ndarray, seed: int = 185) -> HistGradientBoostingClassifier:
    if X.shape[0] > 175_000:
        rng = np.random.default_rng(seed)
        sub = rng.choice(X.shape[0], size=175_000, replace=False)
        X_fit, y_fit = X[sub], y[sub]
    else:
        X_fit, y_fit = X, y
    model = HistGradientBoostingClassifier(
        max_iter=190,
        learning_rate=0.065,
        max_leaf_nodes=47,
        min_samples_leaf=80,
        l2_regularization=3.0,
        early_stopping=False,
        random_state=seed,
    )
    model.fit(X_fit, y_fit)
    return model
