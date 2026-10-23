"""H85-GAPVENT + H85-VOLCDECONF: 58-channel multi-physics concealed-fault & blind-vent stack.

All 27 new channels (`GAPVENT_CHANNELS`) + 6 multiscale context channels (`CTX_CHANNELS`)
+ 25 base `featurestack` channels are 100% catalogue-free: neither `labels.tif`,
`existing_faults.tif`, nor `dist_known_fault_px` is ever read during feature construction.

Physical families added here (see `research/session-7ded4c0a-hypotheses.md`):
  1. Seamless 10 m USGS 3DEP morphology + explicit LiDAR validity mask (`IR-85-018`) +
     unused 1 m LiDAR scarp bands (`lapneg`, `upface`, `cross`) + relief-normalized
     piedmont scarp persistence across 100% of the footprint (closing the 24.63% LiDAR gap).
  2. Seamless 10 m USGS 3DEP fluvial `chi`-integral & knickpoint step channels (`knick_n`,
     `step_max`, high-pass `ksn_max`, uplifted-footwall `raised_n / valid_n`).
  3. Blind geothermal upflow corridors (DOE GDR 1391 INGENIOUS): 195 non-tufa hydrothermal
     paleo-vents (`Tufa` explicitly excluded to prevent Lake Lahontan shoreline mimicry),
     464 shallow 2 m temperature-probe anomalies (`F2mDAB >= 2 C` or `T2m >= 25 C`),
     deep-equilibrated chemical geothermometer wells/springs (`>= 110 C` or `temp >= 37 C`,
     `dist_known_fault_px` strictly banned), and a 2.5 km 8-strike Radon collinearity corridor.
  4. Potential-field & Andersonian mechanics: shallow hydrothermal magnetite-destruction
     residual (`robust_z(TMI) - robust_z(TMI_up150)`), unit-calibrated Miller & Singh (1994)
     magnetic tilt-angle vertical-contact sharpness, and Andersonian 60-deg normal-fault
     up-dip basement-gravity back-projection onto the surface trace.
  5. Rank-4 mimic deconfounders (`H85-VOLCDECONF`): orthometric elevation `zmean_m` (m ASL),
     Lake Lahontan 1,335 m Sehoo shoreline wave-cut bench indicator, and elevated magnetic
     volcanic-mesa caprock rim indicator.
"""

from __future__ import annotations

import csv
import gc
import io
import struct
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingRegressor

from . import featurestack, geopb, grid

EXT = grid.DATA / "external"
LIDAR_TIF = EXT / "lidar_scarp_features_u8.tif"
EXT_TIF = EXT / "geodawn_extensions_u8.tif"
TOPO10_TIF = EXT / "topo_10m_derived_100m_u8.tif"
CHI10_U8_TIF = EXT / "dem10_chi_100m_u8.tif"
CHI10_I16_TIF = EXT / "dem10_chi_100m_i16.tif"
PALEO_ZIP = EXT / "paleo_geothermal_regional.zip"
PROBE2M_ZIP = EXT / "2m_temperature_probe_INGENIOUS_regional_data.zip"
WELLSPRING_CSV = EXT / "gdr_wellspring_in_footprint.csv"

CTX_CHANNELS: list[str] = [
    "ctx_linemax",
    "ctx_crest_s3",
    "ctx_crest_s9",
    "ctx_step_s3",
    "ctx_grtp_s9",
    "ctx_corrob",
]

GAPVENT_CHANNELS: list[str] = [
    # 1. LiDAR validity + unused 1 m scarp bands + seamless 10 m USGS 3DEP scarp bridge
    "gv_lidar_valid",
    "gv_lidar_lapneg",
    "gv_lidar_upface",
    "gv_lidar_cross",
    "gv_dem10_slope_p90",
    "gv_dem10_steep_frac",
    "gv_dem10_slope_std",
    "gv_dem10_relief",
    "gv_dem10_curv_prof",
    "gv_dem10_aspect_coh",
    "gv_dem10_hs_line",
    "gv_dem10_piedmont_scarp",
    "gv_dem10_line_s15",
    # 2. Fluvial chi-integral & knickpoint step channels (Perron & Royden 2013)
    "gv_chi_knick_dens",
    "gv_chi_step_pos",
    "gv_chi_ksn_resid",
    "gv_chi_raised_asym",
    # 3. Blind geothermal paleo-vent, 2 m probe & geothermometer corridors (Faulds & Hinz 2015)
    "gv_vent_hydro_prox",
    "gv_probe2m_anom_prox",
    "gv_geotherm_deep_prox",
    "gv_vent_radon_corridor",
    # 4. Shallow demagnetization, Miller-Singh tilt zero-crossing & Anderson 60-deg back-projection
    "gv_mag_demag_shallow",
    "gv_mag_tilt_contact",
    "gv_anderson60_grav",
    # 5. Orthometric elevation + Lahontan 1335 m shoreline & volcanic-mesa rim deconfounders
    "gv_zmean_m",
    "gv_mimic_lahontan",
    "gv_mimic_volc_mesa",
]


def _save(name: str, arr: np.ndarray, fp: np.ndarray) -> Path:
    featurestack.CACHE.mkdir(parents=True, exist_ok=True)
    p = featurestack.CACHE / f"ch_{name}.npy"
    clean = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32, copy=False)
    clean[~fp] = 0.0
    np.save(p, clean)
    return p


def _exists(*names: str) -> bool:
    return all((featurestack.CACHE / f"ch_{n}.npy").exists() for n in names)


def _read_u8(path: Path, band: int) -> np.ndarray:
    with rasterio.open(path) as src:
        grid.assert_grid(src, str(path))
        return src.read(band).astype(np.float32)


def _read_i16(path: Path, band: int, fill_mode: str = "zero", fp: np.ndarray | None = None) -> np.ndarray:
    with rasterio.open(path) as src:
        grid.assert_grid(src, str(path))
        raw = src.read(band)
    bad = raw == -32768
    out = raw.astype(np.float32)
    if np.any(bad):
        if fill_mode == "median" and fp is not None:
            med = float(np.median(out[fp & ~bad]))
            out[bad] = med
        else:
            out[bad] = 0.0
    return out


def _robust_z_fp(arr: np.ndarray, fp: np.ndarray) -> np.ndarray:
    vals = arr[fp & np.isfinite(arr)][::8]
    med = float(np.median(vals))
    q25, q75 = np.percentile(vals, [25.0, 75.0])
    iqr = max(float(q75 - q25), 1e-6)
    z = (np.nan_to_num(arr, nan=med) - med) / iqr
    return np.clip(z, -12.0, 12.0).astype(np.float32)


def _utm_to_rc(utm_e: float, utm_n: float) -> tuple[int, int]:
    col = int((utm_e - float(grid.TRANSFORM.c)) // float(grid.TRANSFORM.a))
    row = int((float(grid.TRANSFORM.f) - utm_n) // abs(float(grid.TRANSFORM.e)))
    return row, col


def _multiscale_prox(mask: np.ndarray, s_near: float, s_far: float) -> np.ndarray:
    if not np.any(mask):
        return np.zeros(mask.shape, dtype=np.float32)
    d = ndi.distance_transform_edt(~mask).astype(np.float32)
    return (0.60 * np.exp(-d / s_near) + 0.40 * np.exp(-d / s_far)).astype(np.float32)


def _load_hydrothermal_paleo_points(fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Load non-tufa Quaternary hydrothermal paleo-vents from DOE GDR 1391 zip."""
    mask = np.zeros(fp.shape, dtype=bool)
    imp = np.zeros(fp.shape, dtype=np.float32)
    with zipfile.ZipFile(PALEO_ZIP) as zf:
        csv_member = next(n for n in zf.namelist() if n.endswith("Paleo_geothermal_final.csv"))
        txt = zf.read(csv_member).decode("utf-8-sig", errors="replace")
    lons: list[float] = []
    lats: list[float] = []
    weights: list[float] = []
    for row in csv.DictReader(io.StringIO(txt)):
        dtype = (row.get("Deposit_type") or row.get("deposit_type") or "").strip()
        if not dtype or dtype.lower() == "tufa":
            continue
        try:
            lon = float(row["Long_deg_NAD83"])
            lat = float(row["Lat_deg_NAD83"])
        except (KeyError, ValueError):
            continue
        lons.append(lon)
        lats.append(lat)
        hi = dtype in {"Sinter", "Travertine", "Explosion craters", "Silicified fault breccia"}
        weights.append(2.0 if hi else 1.3)
    if lons:
        xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
        for e, n, w in zip(xs, ys, weights):
            r, c = _utm_to_rc(float(e), float(n))
            if 0 <= r < grid.HEIGHT and 0 <= c < grid.WIDTH and fp[r, c]:
                mask[r, c] = True
                imp[r, c] = max(imp[r, c], w)
    assert int(mask.sum()) >= 100, f"Expected >=100 hydrothermal paleo-vent cells in fp, got {int(mask.sum())}"
    return mask, imp


def _parse_dbf_records(raw: bytes) -> list[dict[str, str]]:
    """Minimal stdlib dBase III+ parser."""
    num_rec, hdr_len, rec_len = struct.unpack("<IHH", raw[4:12])
    fields: list[tuple[str, int]] = []
    pos = 32
    while pos < hdr_len - 1 and raw[pos] != 0x0D:
        fname = raw[pos : pos + 11].split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        flen = raw[pos + 16]
        fields.append((fname, flen))
        pos += 32
    out: list[dict[str, str]] = []
    offset = hdr_len
    for _ in range(num_rec):
        rec = raw[offset : offset + rec_len]
        offset += rec_len
        if not rec or rec[0:1] == b"*":
            continue
        p = 1
        d: dict[str, str] = {}
        for fname, flen in fields:
            d[fname] = rec[p : p + flen].decode("latin1", errors="ignore").strip()
            p += flen
        out.append(d)
    return out


def _load_probe2m_anomalies(fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Load shallow 2 m temperature-probe positive anomalies (F2mDAB >= 2 C or T2m >= 25 C)."""
    mask = np.zeros(fp.shape, dtype=bool)
    imp = np.zeros(fp.shape, dtype=np.float32)
    with zipfile.ZipFile(PROBE2M_ZIP) as zf:
        dbf_member = next(n for n in zf.namelist() if n.endswith("2m_temperature_probe_n83geo.dbf"))
        dbf_bytes = zf.read(dbf_member)
    recs = _parse_dbf_records(dbf_bytes)
    lons: list[float] = []
    lats: list[float] = []
    weights: list[float] = []
    for r in recs:
        try:
            lon = float(r["LongDegree"])
            lat = float(r["LatDegreeN"])
        except (KeyError, ValueError):
            continue
        t2m = float(r["T2m"]) if r.get("T2m", "") not in {"", "NA", "None"} else -999.0
        dab = float(r["F2mDAB"]) if r.get("F2mDAB", "") not in {"", "NA", "None"} else -999.0
        if (dab > -900 and dab >= 2.0) or (t2m > -900 and t2m >= 25.0):
            lons.append(lon)
            lats.append(lat)
            w = 1.5 if (dab >= 3.5 or t2m >= 32.0) else 1.0
            weights.append(w)
    if lons:
        xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
        for e, n, w in zip(xs, ys, weights):
            rr, cc = _utm_to_rc(float(e), float(n))
            if 0 <= rr < grid.HEIGHT and 0 <= cc < grid.WIDTH and fp[rr, cc]:
                mask[rr, cc] = True
                imp[rr, cc] = max(imp[rr, cc], w)
    assert int(mask.sum()) >= 80, f"Expected >=80 2m-probe anomaly cells in fp, got {int(mask.sum())}"
    return mask, imp


def _load_deep_geotherm_points(fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Load deep-equilibrated thermal wells/springs; strictly bans `dist_known_fault_px`."""
    ALLOWED_COLS = {"row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"}
    BANNED_COL = "dist_known_fault_px"
    mask = np.zeros(fp.shape, dtype=bool)
    imp = np.zeros(fp.shape, dtype=np.float32)
    with WELLSPRING_CSV.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert BANNED_COL not in ALLOWED_COLS
        for row in reader:
            vals = {k: row[k] for k in ALLOWED_COLS if k in row}
            try:
                rr = int(float(vals["row"]))
                cc = int(float(vals["col"]))
            except (KeyError, ValueError):
                continue
            if not (0 <= rr < grid.HEIGHT and 0 <= cc < grid.WIDTH and fp[rr, cc]):
                continue

            def _num(key: str) -> float:
                s = (vals.get(key) or "").strip()
                if not s or s.lower() in {"nan", "na", "none"}:
                    return -999.0
                try:
                    return float(s)
                except ValueError:
                    return -999.0

            tc = _num("temp_c")
            qtz = _num("geothermquartz_c")
            cat = _num("geothermcat_c")
            chal = _num("geothermchalc_c")
            gmax = max(qtz, cat, chal)
            if tc >= 37.0 or gmax >= 110.0:
                mask[rr, cc] = True
                w = 1.6 if (tc >= 60.0 or gmax >= 150.0) else 1.0
                imp[rr, cc] = max(imp[rr, cc], w)
    return mask, imp


def build_context_channels(fp: np.ndarray) -> list[str]:
    """Build or reuse the 6 multiscale context channels from `run_session_experiments.py`."""
    featurestack.build(fp)
    cache = featurestack.CACHE
    if not _exists(*CTX_CHANNELS):
        crest = np.load(cache / "ch_geopb_crest.npy", mmap_mode="r")
        step = np.load(cache / "ch_lidar_step_max.npy", mmap_mode="r")
        grtp = np.load(cache / "ch_grad_rtp_s2.npy", mmap_mode="r")
        g3 = np.load(cache / "ch_geopb_r3_L15.npy", mmap_mode="r")

        if not _exists("ctx_linemax"):
            best = np.zeros(fp.shape, np.float32)
            g3_arr = np.asarray(g3, dtype=np.float32)
            for dy, dx in geopb.NORMALS_R3:
                lm = geopb.line_mean(g3_arr, -dx, dy, 15.0)
                np.maximum(best, lm, out=best)
            _save("ctx_linemax", best, fp)
            del best, g3_arr
        if not _exists("ctx_crest_s3"):
            _save("ctx_crest_s3", ndi.gaussian_filter(np.asarray(crest), 3.0, mode="nearest"), fp)
        if not _exists("ctx_crest_s9"):
            _save("ctx_crest_s9", ndi.gaussian_filter(np.asarray(crest), 9.0, mode="nearest"), fp)
        if not _exists("ctx_step_s3"):
            _save("ctx_step_s3", ndi.gaussian_filter(np.asarray(step), 3.0, mode="nearest"), fp)
        if not _exists("ctx_grtp_s9"):
            _save("ctx_grtp_s9", ndi.gaussian_filter(np.asarray(grtp), 9.0, mode="nearest"), fp)
        if not _exists("ctx_corrob"):
            fields = [
                np.asarray(crest),
                np.asarray(step),
                np.asarray(grtp),
                np.asarray(np.load(cache / "ch_grad_grav_s2.npy", mmap_mode="r")),
                np.asarray(np.load(cache / "ch_sato_det_elev.npy", mmap_mode="r")),
            ]
            cnt = np.zeros(fp.shape, np.float32)
            for f in fields:
                cnt += (f >= np.percentile(f[fp][::10], 90.0)).astype(np.float32)
            _save("ctx_corrob", cnt, fp)
            del fields, cnt
    return list(CTX_CHANNELS)


def build_all(fp: np.ndarray | None = None) -> tuple[list[str], list[np.ndarray]]:
    """Build (if uncached) and return `(names, mmap_handles)` for all 58 channels."""
    if fp is None:
        fp = grid.footprint()
    grid.unpack_raw19()
    base_names = featurestack.build(fp)
    ctx_names = build_context_channels(fp)

    # --- Group 1: LiDAR validity + unused 1 m scarp bands + 10 m 3DEP seamless morphology ---
    g1 = [
        "gv_lidar_valid", "gv_lidar_lapneg", "gv_lidar_upface", "gv_lidar_cross",
        "gv_dem10_slope_p90", "gv_dem10_steep_frac", "gv_dem10_slope_std", "gv_dem10_relief",
        "gv_dem10_curv_prof", "gv_dem10_aspect_coh", "gv_dem10_hs_line",
        "gv_dem10_piedmont_scarp", "gv_dem10_line_s15",
    ]
    if not _exists(*g1):
        with rasterio.open(LIDAR_TIF) as ds:
            grid.assert_grid(ds, str(LIDAR_TIF))
            _save("gv_lidar_valid", (ds.read(12) > 0).astype(np.float32), fp)
            _save("gv_lidar_lapneg", ds.read(4).astype(np.float32), fp)
            _save("gv_lidar_upface", ds.read(7).astype(np.float32), fp)
            _save("gv_lidar_cross", ds.read(8).astype(np.float32), fp)
        gc.collect()

        _save("gv_dem10_slope_p90", _read_u8(TOPO10_TIF, 1), fp)
        _save("gv_dem10_steep_frac", _read_u8(TOPO10_TIF, 3), fp)
        _save("gv_dem10_slope_std", _read_u8(TOPO10_TIF, 4), fp)
        rel = _read_u8(TOPO10_TIF, 5)
        _save("gv_dem10_relief", rel, fp)
        curv = _read_u8(TOPO10_TIF, 6)
        _save("gv_dem10_curv_prof", curv, fp)
        acoh = _read_u8(TOPO10_TIF, 7)
        _save("gv_dem10_aspect_coh", acoh, fp)
        hsl = _read_u8(TOPO10_TIF, 8)
        _save("gv_dem10_hs_line", hsl, fp)

        rel_bg = ndi.gaussian_filter(rel, 8.0).astype(np.float32)
        pied = (curv * (acoh / 255.0) / (rel_bg + 12.0)).astype(np.float32)
        _save("gv_dem10_piedmont_scarp", pied, fp)
        del rel, rel_bg, curv, acoh, hsl

        line15 = np.zeros(fp.shape, dtype=np.float32)
        for dy, dx in geopb.NORMALS_R3:
            lm = geopb.line_mean(pied, -dx, dy, 15.0)
            np.maximum(line15, lm, out=line15)
        _save("gv_dem10_line_s15", line15, fp)
        del pied, line15
        gc.collect()

    # --- Group 2: Seamless 10 m USGS 3DEP fluvial chi-integral & knickpoints ---
    g2 = ["gv_chi_knick_dens", "gv_chi_step_pos", "gv_chi_ksn_resid", "gv_chi_raised_asym"]
    if not _exists(*g2):
        knick = _read_u8(CHI10_U8_TIF, 2)
        _save("gv_chi_knick_dens", ndi.gaussian_filter(knick, 2.0).astype(np.float32), fp)
        del knick

        raised = _read_u8(CHI10_U8_TIF, 3)
        valid_n = _read_u8(CHI10_U8_TIF, 4)
        asym = ndi.gaussian_filter(raised / (valid_n + 1.0), 3.0).astype(np.float32)
        _save("gv_chi_raised_asym", asym, fp)
        del raised, valid_n, asym

        step_pos = np.maximum(0.0, _read_i16(CHI10_I16_TIF, 1, "zero") * 0.001)
        _save("gv_chi_step_pos", ndi.gaussian_filter(step_pos, 2.0).astype(np.float32), fp)
        del step_pos

        ksn = _read_i16(CHI10_I16_TIF, 3, "median", fp)
        ksn_res = (ksn - ndi.gaussian_filter(ksn, 10.0)).astype(np.float32)
        _save("gv_chi_ksn_resid", ksn_res, fp)
        del ksn, ksn_res
        gc.collect()

    # --- Group 3: Hydrothermal paleo-vents, 2 m probes, geothermometers & Radon corridor ---
    g3 = ["gv_vent_hydro_prox", "gv_probe2m_anom_prox", "gv_geotherm_deep_prox", "gv_vent_radon_corridor"]
    if not _exists(*g3):
        m_hydro, imp_hydro = _load_hydrothermal_paleo_points(fp)
        _save("gv_vent_hydro_prox", _multiscale_prox(m_hydro, 5.0, 18.0), fp)

        m_p2m, imp_p2m = _load_probe2m_anomalies(fp)
        _save("gv_probe2m_anom_prox", _multiscale_prox(m_p2m, 4.0, 15.0), fp)

        m_geo, imp_geo = _load_deep_geotherm_points(fp)
        _save("gv_geotherm_deep_prox", _multiscale_prox(m_geo, 5.0, 18.0), fp)

        imp_all = ndi.gaussian_filter(imp_hydro + imp_p2m + imp_geo, 1.5).astype(np.float32)
        del m_hydro, imp_hydro, m_p2m, imp_p2m, m_geo, imp_geo
        radon = np.zeros(fp.shape, dtype=np.float32)
        for dy, dx in geopb.NORMALS_R3:
            lm = geopb.line_mean(imp_all, -dx, dy, 25.0)
            np.maximum(radon, lm, out=radon)
        _save("gv_vent_radon_corridor", radon, fp)
        del imp_all, radon
        gc.collect()

    # --- Group 4 & 5: Potential-field demag, tilt zero-crossing, Anderson 60-deg & deconfounders ---
    g45 = [
        "gv_mag_demag_shallow", "gv_mag_tilt_contact", "gv_anderson60_grav",
        "gv_zmean_m", "gv_mimic_lahontan", "gv_mimic_volc_mesa",
    ]
    if not _exists(*g45):
        tmi = grid.read_feature("tmi")
        tmi_up = _read_u8(EXT_TIF, 4)
        demag = (_robust_z_fp(tmi, fp) - _robust_z_fp(tmi_up, fp)).astype(np.float32)
        _save("gv_mag_demag_shallow", ndi.gaussian_filter(demag, 1.2).astype(np.float32), fp)
        del tmi, tmi_up, demag

        tmi_hg = np.nan_to_num(grid.read_feature("tmi_hg"), nan=0.0)
        tmi_vg = np.nan_to_num(grid.read_feature("tmi_vg"), nan=0.0)
        iqr_hg = max(float(np.subtract(*np.percentile(tmi_hg[fp][::10], [75, 25]))), 1e-6)
        iqr_vg = max(float(np.subtract(*np.percentile(tmi_vg[fp][::10], [75, 25]))), 1e-6)
        hg_n = np.maximum(0.0, tmi_hg / iqr_hg)
        vg_n = tmi_vg / iqr_vg
        theta = np.arctan2(vg_n, hg_n + 1e-3)
        tilt_contact = (np.exp(-np.abs(theta) / 0.35) * np.tanh(hg_n)).astype(np.float32)
        _save("gv_mag_tilt_contact", tilt_contact, fp)
        del tmi_vg, vg_n, theta, tilt_contact

        zbase = np.clip(np.nan_to_num(grid.read_feature("depth_to_base_surf"), nan=0.0), 0.0, 5000.0)
        z_sm = ndi.gaussian_filter(zbase, 4.0)
        gy, gx = np.gradient(z_sm)
        gn = np.hypot(gy, gx) + 1e-6
        uy, ux = gy / gn, gx / gn
        shift_px = np.clip(z_sm / (100.0 * np.tan(np.deg2rad(60.0))), 0.0, 12.0)
        grav_slope = np.nan_to_num(grid.read_feature("iso_grav_anom_slope"), nan=0.0).astype(np.float32)
        yy, xx = np.indices(fp.shape, dtype=np.float32)
        coords = np.array([
            np.clip(yy + shift_px * uy, 0.0, grid.HEIGHT - 1.0),
            np.clip(xx + shift_px * ux, 0.0, grid.WIDTH - 1.0),
        ])
        del zbase, z_sm, gy, gx, gn, uy, ux, shift_px, yy, xx
        grav_updip = ndi.map_coordinates(grav_slope, coords, order=1, mode="nearest").astype(np.float32)
        del coords
        _save("gv_anderson60_grav", grav_updip, fp)
        del grav_updip

        zmean = _read_i16(CHI10_I16_TIF, 5, "median", fp)
        _save("gv_zmean_m", zmean, fp)
        iqr_gs = max(float(np.subtract(*np.percentile(grav_slope[fp][::10], [75, 25]))), 1e-6)
        gs_n = grav_slope / iqr_gs
        lahontan = (np.exp(-((zmean - 1335.0) / 14.0) ** 2) / (1.0 + 1.5 * gs_n)).astype(np.float32)
        _save("gv_mimic_lahontan", lahontan, fp)
        del zmean, lahontan

        det_el = np.nan_to_num(grid.read_feature("det_elev"), nan=0.0)
        elev_gate = 1.0 / (1.0 + np.exp(-np.clip((det_el - 80.0) / 60.0, -15.0, 15.0)))
        volc_mesa = ((hg_n / (1.0 + 1.5 * gs_n)) * elev_gate).astype(np.float32)
        _save("gv_mimic_volc_mesa", volc_mesa, fp)
        del tmi_hg, hg_n, grav_slope, gs_n, det_el, elev_gate, volc_mesa
        gc.collect()

    all_names = base_names + ctx_names + GAPVENT_CHANNELS
    return all_names, featurestack.open_stack(all_names)


# Long-wavelength regional/basin-coordinate channels excluded from raw tree splits
# (IR-85-023: prevents Positive-Unlabeled trees from memorizing which 20 km basins/blocks
# have sparser mapped faults, while keeping their local gradients, Radon corridors, and
# mimic deconfounders active).
BASIN_ID_CHANNELS: set[str] = {
    "depth_to_base",
    "cond_surf",
    "rad_K",
    "rad_Th",
    "rad_TC",
    "gv_zmean_m",
    "gv_vent_hydro_prox",
    "gv_probe2m_anom_prox",
    "gv_geotherm_deep_prox",
}


def gather_stripwise(handles: list[np.ndarray], flat_idx: np.ndarray, strip_rows: int = 512) -> np.ndarray:
    """Sequential row-strip gather across memmaps (avoids OS mmap page-thrashing on 3.8 GB RAM)."""
    order = np.argsort(flat_idx, kind="mergesort")
    sorted_idx = flat_idx[order]
    ys, xs = np.divmod(sorted_idx, grid.WIDTH)
    X_sorted = np.empty((flat_idx.size, len(handles)), dtype=np.float32)

    n_cols = len(handles)
    pos = 0
    total = ys.size
    for r0 in range(0, grid.HEIGHT, strip_rows):
        if pos >= total:
            break
        r1 = min(grid.HEIGHT, r0 + strip_rows)
        end = int(np.searchsorted(ys, r1, side="left"))
        if end <= pos:
            continue
        sub_y = ys[pos:end] - r0
        sub_x = xs[pos:end]
        for c in range(n_cols):
            blk = handles[c][r0:r1, :]
            X_sorted[pos:end, c] = blk[sub_y, sub_x]
        pos = end

    X = np.empty_like(X_sorted)
    X[order] = X_sorted
    return X


def predict_stripwise(handles: list[np.ndarray], fp: np.ndarray, pred_fn, strip_rows: int = 256) -> np.ndarray:
    """Predict across all footprint pixels via contiguous row strips (~3s vs ~500s random mmap)."""
    out = np.zeros(fp.shape, dtype=np.float32)
    n_cols = len(handles)
    for r0 in range(0, grid.HEIGHT, strip_rows):
        r1 = min(grid.HEIGHT, r0 + strip_rows)
        sub_fp = fp[r0:r1, :]
        ys_sub, xs_sub = np.nonzero(sub_fp)
        if ys_sub.size == 0:
            continue
        Xc = np.empty((ys_sub.size, n_cols), dtype=np.float32)
        for c in range(n_cols):
            Xc[:, c] = handles[c][r0:r1, :][ys_sub, xs_sub]
        out[r0:r1, :][ys_sub, xs_sub] = pred_fn(Xc).astype(np.float32)
        del Xc
    return out


def select_local_tree_stack(names: list[str], handles: list[np.ndarray]) -> tuple[list[str], list[np.ndarray]]:
    keep = [(n, h) for n, h in zip(names, handles) if n not in BASIN_ID_CHANNELS]
    return [k[0] for k in keep], [k[1] for k in keep]


def train_predict_gapvent(
    handles: list[np.ndarray],
    fp: np.ndarray,
    visible_faults: np.ndarray,
    *,
    names: list[str] | None = None,
    seed: int = 20261023,
) -> np.ndarray:
    """Fold-proper PU continuous 300 m kernel-target regressor (`y = max(0, 1 - d_vis/3)`).

    Uses ONLY `visible_faults` and `fp` (zero knowledge of `withheld` faults):
      1. Surveyed-corridor PU negative sampling (`4 <= d_vis <= 45 px`) avoids treating
         unmapped quadrangles / withheld blocks (`d_vis > 45 px`) as verified negatives (`IR-85-023`).
      2. Translation-invariant local scarp, fluvial-chi, potential-field, dip-projection,
         Radon-corridor, and mimic-deconfounder channels (`48` local channels) prevent basin-ID
         memorization while preserving full multi-physics discrimination.
    """
    if names is not None:
        _, tree_handles = select_local_tree_stack(names, handles)
    else:
        tree_handles = handles

    rng = np.random.default_rng(seed)
    d_vis = ndi.distance_transform_edt(~visible_faults).astype(np.float32)
    flat_d = d_vis.ravel()
    flat_fp = fp.ravel()

    trace_idx = np.flatnonzero(flat_fp & (flat_d == 0.0))
    halo_idx = np.flatnonzero(flat_fp & (flat_d > 0.0) & (flat_d <= 2.25))
    near_idx = np.flatnonzero(flat_fp & (flat_d >= 4.0) & (flat_d <= 12.0))
    surv_idx = np.flatnonzero(flat_fp & (flat_d > 12.0) & (flat_d <= 45.0))

    def _pick(idx: np.ndarray, k: int) -> np.ndarray:
        return idx if idx.size <= k else rng.choice(idx, k, replace=False)

    sel = np.concatenate([
        _pick(trace_idx, 65_000),
        _pick(halo_idx, 35_000),
        _pick(near_idx, 180_000),
        _pick(surv_idx, 520_000),
    ])
    y_target = np.clip(1.0 - flat_d[sel] / 3.0, 0.0, 1.0).astype(np.float32)
    del d_vis, flat_d

    perm = rng.permutation(sel.size)
    sel = sel[perm]
    y_target = y_target[perm]
    X = gather_stripwise(tree_handles, sel)

    m_pois = HistGradientBoostingRegressor(
        loss="poisson",
        max_iter=200,
        learning_rate=0.06,
        max_leaf_nodes=31,
        min_samples_leaf=120,
        l2_regularization=4.0,
        random_state=seed + 11,
        early_stopping=False,
    )
    m_l2 = HistGradientBoostingRegressor(
        loss="squared_error",
        max_iter=200,
        learning_rate=0.06,
        max_leaf_nodes=31,
        min_samples_leaf=120,
        l2_regularization=4.0,
        random_state=seed + 29,
        early_stopping=False,
    )
    m_pois.fit(X, y_target)
    m_l2.fit(X, y_target)
    del X, y_target
    gc.collect()

    return predict_stripwise(
        tree_handles,
        fp,
        lambda Xc: 0.55 * np.clip(m_pois.predict(Xc), 0.0, 1.0)
        + 0.45 * np.clip(m_l2.predict(Xc), 0.0, 1.0),
    )
