"""Official DOE GDR 1391 geothermal-vent & USGS 3DEP 10 m morphometry features.

Every channel produced here is 100% independent of `existing_faults.tif` and
`labels.tif`. Where upstream tabular extracts include `dist_known_fault_px`
(`gdr_wellspring_in_footprint.csv`, `gdr_volcanic_vents_in_footprint.csv`), that
column is explicitly banned and never parsed.

Official free public sources verified in-session:
  1. DOE Geothermal Data Repository Submission 1391 (INGENIOUS Great Basin Regional
     Dataset Compilation, Ayling et al. 2022, CC BY 4.0, https://doi.org/10.15121/1881483):
     - `paleo_geothermal_regional.zip`: 281 in-footprint siliceous sinters (>175 C),
       silicified fault breccias/sands, hydrothermal explosion craters, travertines & tufas.
     - `2m_temperature_probe_INGENIOUS_regional_data.zip`: 2,782 in-footprint UNR/GBCGE
       shallow 2-m temperature probes with background-subtracted `F2mDAB` thermal plumes.
     - `gdr_wellspring_in_footprint.csv`: 12,570 in-footprint spring/well stations with
       discharge temperature excess and silica / Na-K-Ca cation geothermometers.
     - `gdr_volcanic_vents_in_footprint.csv`: Quaternary volcanic vents (confounder layer).
  2. USGS 3D Elevation Program (3DEP 1/3 arc-second, Public Domain):
     - `dem10_chi_100m_i16.tif`: cross-pixel chi disequilibrium steps & channel steepness k_sn.
     - `topo_10m_derived_100m_u8.tif`: 10 m slope, local relief, profile curvature,
       aspect coherence, hillshade lineaments, and absolute elevation (Lake Lahontan 1,335 m datum).
"""

from __future__ import annotations

import csv
import io
import struct
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as rio_transform
from scipy import ndimage as ndi

from . import geopb, grid

BANNED_COLUMNS = frozenset({"dist_known_fault_px"})

HIGH_ENTHALPY_PALEO_KEYWORDS = (
    "sinter",
    "explosion",
    "breccia",
    "silica-cemented",
    "silica vein",
    "silicified",
)


def _parse_point_shapefile_zip(
    zip_path: Path, shp_member: str, dbf_member: str
) -> tuple[list[tuple[float, float]], list[dict[str, str]]]:
    """Pure-stdlib ESRI Point Shapefile + dBASE III reader (zero extra pip deps)."""
    with zipfile.ZipFile(zip_path) as zf:
        shp = zf.read(shp_member)
        dbf = zf.read(dbf_member)

    pos = 100
    pts: list[tuple[float, float]] = []
    while pos < len(shp):
        _, content_len = struct.unpack(">ii", shp[pos : pos + 8])
        pos += 8
        rec_bytes = shp[pos : pos + content_len * 2]
        pos += content_len * 2
        shape_type = struct.unpack("<i", rec_bytes[:4])[0]
        if shape_type in (1, 11, 21):
            x, y = struct.unpack("<dd", rec_bytes[4:20])
            pts.append((x, y))
        else:
            pts.append((float("nan"), float("nan")))

    num_rec, hdr_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields: list[tuple[str, int]] = []
    fpos = 32
    while fpos < hdr_len - 1 and dbf[fpos] != 0x0D:
        fname = dbf[fpos : fpos + 11].split(b"\x00", 1)[0].decode("latin1")
        if fname in BANNED_COLUMNS:
            raise ValueError(f"Banned label-derived column encountered: {fname}")
        fields.append((fname, dbf[fpos + 16]))
        fpos += 32

    rows: list[dict[str, str]] = []
    rpos = hdr_len
    for _ in range(num_rec):
        if rpos + rec_len > len(dbf):
            break
        rec = dbf[rpos : rpos + rec_len]
        rpos += rec_len
        if rec[0:1] == b"*":
            continue
        off = 1
        d: dict[str, str] = {}
        for fname, flen in fields:
            d[fname] = rec[off : off + flen].decode("latin1", errors="replace").strip()
            off += flen
        rows.append(d)
    return pts, rows


def _nad83_to_grid_rc(lons: list[float], lats: list[float]) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = rio_transform("EPSG:4269", "EPSG:32611", lons, lats)
    T = grid.TRANSFORM
    cols = np.floor((np.asarray(xs, dtype=np.float64) - T.c) / T.a).astype(np.int32)
    rows = np.floor((np.asarray(ys, dtype=np.float64) - T.f) / T.e).astype(np.int32)
    return rows, cols


def load_paleo_geothermal_fields(
    ext_dir: Path, fp: np.ndarray
) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    """Build multi-scale hydrothermal vent fields from GDR 1391 paleo-geothermal deposits."""
    H, W = fp.shape
    zip_path = ext_dir / "paleo_geothermal_regional.zip"
    with zipfile.ZipFile(zip_path) as zf:
        reader = csv.DictReader(
            io.StringIO(zf.read("Paleo_geothermal_final.csv").decode("utf-8", errors="replace"))
        )
        rows = list(reader)

    lons = [float(r["Long_deg_NAD83"]) for r in rows]
    lats = [float(r["Lat_deg_NAD83"]) for r in rows]
    rr, cc = _nad83_to_grid_rc(lons, lats)

    impulse = np.zeros((H, W), dtype=np.float32)
    mask_pts = np.zeros((H, W), dtype=bool)
    type_counts: dict[str, int] = {}
    n_in_fp = 0
    for i, rec in enumerate(rows):
        r, c = int(rr[i]), int(cc[i])
        if 0 <= r < H and 0 <= c < W and fp[r, c]:
            n_in_fp += 1
            dtype = rec.get("Deposit_type", "Unknown").strip() or "Unknown"
            type_counts[dtype] = type_counts.get(dtype, 0) + 1
            low = dtype.lower()
            weight = 2.0 if any(k in low for k in HIGH_ENTHALPY_PALEO_KEYWORDS) else 1.25
            impulse[r, c] = max(impulse[r, c], weight)
            mask_pts[r, c] = True

    s4 = ndi.gaussian_filter(impulse, sigma=4.0, mode="constant") * (4.0 * 4.0)
    s12 = ndi.gaussian_filter(impulse, sigma=12.0, mode="constant") * (12.0 * 12.0)
    dist = ndi.distance_transform_edt(~mask_pts).astype(np.float32)
    log_prox = (-np.log1p(np.minimum(dist, 400.0))).astype(np.float32)

    out = {
        "paleo_vent_s4": geopb.robust_z(s4, fp, clip=6.0),
        "paleo_vent_s12": geopb.robust_z(s12, fp, clip=6.0),
        "paleo_vent_logprox": geopb.robust_z(log_prox, fp, clip=6.0),
    }
    stats = {
        "total_regional_records": len(rows),
        "in_footprint_records": n_in_fp,
        "deposit_types_in_footprint": type_counts,
    }
    return out, stats


def load_2m_probe_fields(
    ext_dir: Path, fp: np.ndarray
) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    """Build blind-plume shallow 2-meter temperature probe channels (Coolbaugh/Sladek GBCGE)."""
    H, W = fp.shape
    zip_path = ext_dir / "2m_temperature_probe_INGENIOUS_regional_data.zip"
    pts, rows = _parse_point_shapefile_zip(
        zip_path,
        "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.shp",
        "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf",
    )
    rr, cc = _nad83_to_grid_rc([p[0] for p in pts], [p[1] for p in pts])

    dab_max = np.zeros((H, W), dtype=np.float32)
    station_imp = np.zeros((H, W), dtype=np.float32)
    hot_mask = np.zeros((H, W), dtype=bool)
    n_in_fp = 0
    n_hot = 0

    for i, rec in enumerate(rows):
        r, c = int(rr[i]), int(cc[i])
        if 0 <= r < H and 0 <= c < W and fp[r, c]:
            n_in_fp += 1
            station_imp[r, c] += 1.0
            raw_dab = rec.get("F2mDAB", "")
            raw_t2m = rec.get("T2m", "")
            dab = float(raw_dab) if raw_dab else 0.0
            t2m = float(raw_t2m) if raw_t2m else 0.0
            excess = max(0.0, dab, (t2m - 24.0) * 0.5)
            if excess > 0.0:
                dab_max[r, c] = max(dab_max[r, c], min(excess, 25.0))
            if dab >= 2.0 or t2m >= 28.0:
                hot_mask[r, c] = True
                n_hot += 1

    dab_s5 = ndi.gaussian_filter(dab_max, sigma=5.0, mode="constant") * 25.0
    dab_s15 = ndi.gaussian_filter(dab_max, sigma=15.0, mode="constant") * 225.0
    dens_s10 = ndi.gaussian_filter(np.minimum(station_imp, 5.0), sigma=10.0, mode="constant") * 100.0
    dist_hot = ndi.distance_transform_edt(~hot_mask).astype(np.float32)
    log_hot = (-np.log1p(np.minimum(dist_hot, 400.0))).astype(np.float32)

    out = {
        "probe2m_dab_s5": geopb.robust_z(dab_s5, fp, clip=6.0),
        "probe2m_dab_s15": geopb.robust_z(dab_s15, fp, clip=6.0),
        "probe2m_survey_dens_s10": geopb.robust_z(dens_s10, fp, clip=6.0),
        "probe2m_hot_logprox": geopb.robust_z(log_hot, fp, clip=6.0),
    }
    stats = {
        "total_regional_stations": len(rows),
        "in_footprint_stations": n_in_fp,
        "in_footprint_hot_anomalies_ge_2C": n_hot,
    }
    return out, stats


def load_wellspring_and_volcanic_fields(
    ext_dir: Path, fp: np.ndarray
) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    """Build active geothermometry & volcanic vent fields while strictly banning label columns."""
    H, W = fp.shape
    temp_imp = np.zeros((H, W), dtype=np.float32)
    sio2_imp = np.zeros((H, W), dtype=np.float32)
    cat_imp = np.zeros((H, W), dtype=np.float32)
    hot_site_mask = np.zeros((H, W), dtype=bool)

    with (ext_dir / "gdr_wellspring_in_footprint.csv").open(newline="") as fh:
        reader = csv.DictReader(fh)
        allowed_cols = [c for c in (reader.fieldnames or []) if c not in BANNED_COLUMNS]
        assert "dist_known_fault_px" not in allowed_cols
        n_rows = 0
        for row in reader:
            n_rows += 1
            r = int(float(row["row"]))
            c = int(float(row["col"]))
            if not (0 <= r < H and 0 <= c < W and fp[r, c]):
                continue
            tc = float(row["temp_c"]) if row["temp_c"] and row["temp_c"] != "nan" else 0.0
            qtz = float(row["geothermquartz_c"]) if row["geothermquartz_c"] and row["geothermquartz_c"] != "nan" else 0.0
            chal = float(row["geothermchalc_c"]) if row["geothermchalc_c"] and row["geothermchalc_c"] != "nan" else 0.0
            cat = float(row["geothermcat_c"]) if row["geothermcat_c"] and row["geothermcat_c"] != "nan" else 0.0
            tclass = (row.get("thermalclass") or "").lower()
            if tc > 20.0:
                temp_imp[r, c] = max(temp_imp[r, c], min(tc - 20.0, 120.0))
            sio2 = max(qtz, chal)
            if sio2 > 65.0:
                sio2_imp[r, c] = max(sio2_imp[r, c], min(sio2 - 65.0, 200.0))
            if cat > 65.0:
                cat_imp[r, c] = max(cat_imp[r, c], min(cat - 65.0, 220.0))
            if "hot" in tclass or "warm" in tclass or tc >= 30.0:
                hot_site_mask[r, c] = True

    volc_imp = np.zeros((H, W), dtype=np.float32)
    n_volc = 0
    with (ext_dir / "gdr_volcanic_vents_in_footprint.csv").open(newline="") as fh:
        reader = csv.DictReader(fh)
        allowed_vcols = [c for c in (reader.fieldnames or []) if c not in BANNED_COLUMNS]
        assert "dist_known_fault_px" not in allowed_vcols
        for row in reader:
            r = int(float(row["row"]))
            c = int(float(row["col"]))
            if 0 <= r < H and 0 <= c < W and fp[r, c]:
                volc_imp[r, c] += 1.0
                n_volc += 1

    dist_hot = ndi.distance_transform_edt(~hot_site_mask).astype(np.float32)
    out = {
        "spring_temp_s8": geopb.robust_z(ndi.gaussian_filter(temp_imp, 8.0, mode="constant") * 64.0, fp, clip=6.0),
        "spring_temp_s20": geopb.robust_z(ndi.gaussian_filter(temp_imp, 20.0, mode="constant") * 400.0, fp, clip=6.0),
        "geotherm_sio2_s12": geopb.robust_z(ndi.gaussian_filter(sio2_imp, 12.0, mode="constant") * 144.0, fp, clip=6.0),
        "geotherm_nakca_s12": geopb.robust_z(ndi.gaussian_filter(cat_imp, 12.0, mode="constant") * 144.0, fp, clip=6.0),
        "spring_hot_logprox": geopb.robust_z((-np.log1p(np.minimum(dist_hot, 400.0))).astype(np.float32), fp, clip=6.0),
        "volcanic_vent_s20": geopb.robust_z(ndi.gaussian_filter(volc_imp, 20.0, mode="constant") * 400.0, fp, clip=6.0),
    }
    stats = {
        "wellspring_rows_read": n_rows,
        "unique_hot_warm_cells": int(hot_site_mask.sum()),
        "in_footprint_volcanic_vents": n_volc,
    }
    return out, stats


def load_3dep10m_chi_and_morph_fields(ext_dir: Path, fp: np.ndarray) -> dict[str, np.ndarray]:
    """Load 10 m USGS 3DEP chi tectonic disequilibrium, morphometry, & Lake Lahontan bench."""
    out: dict[str, np.ndarray] = {}

    with rasterio.open(ext_dir / "dem10_chi_100m_i16.tif") as ds:
        grid.assert_grid(ds, "dem10_chi_100m_i16.tif")
        step_max = ds.read(1).astype(np.float32)
        ksn_max = ds.read(3).astype(np.float32)
        zmean_m = ds.read(5).astype(np.float32)
    step_max[step_max <= -30000] = np.nan
    ksn_max[ksn_max <= -30000] = np.nan
    zmean_m[zmean_m <= -30000] = np.nan

    out["chi10_step_max"] = geopb.robust_z(np.log1p(np.maximum(step_max, 0.0)), fp)
    out["chi10_ksn_max"] = geopb.robust_z(np.log1p(np.maximum(ksn_max, 0.0)), fp)
    out["elev_abs_z"] = geopb.robust_z(zmean_m, fp)
    # Lake Lahontan ~1,335 m highstand shoreline bench indicator (Holocene tufa + fault gauge datum)
    lahontan = np.exp(-(((np.nan_to_num(zmean_m, nan=2500.0) - 1335.0) / 85.0) ** 2)).astype(np.float32)
    lahontan[~fp] = 0.0
    out["lahontan_1335m_prox"] = geopb.robust_z(lahontan, fp)
    del step_max, ksn_max, zmean_m, lahontan

    with rasterio.open(ext_dir / "topo_10m_derived_100m_u8.tif") as ds:
        grid.assert_grid(ds, "topo_10m_derived_100m_u8.tif")
        for bidx, bname in (
            (1, "topo10_slope_p90"),
            (5, "topo10_relief"),
            (6, "topo10_curv_prof"),
            (7, "topo10_aspect_coh"),
            (8, "topo10_hs_lineament"),
        ):
            a = ds.read(bidx).astype(np.float32)
            a[a == 0] = np.nan
            out[bname] = geopb.robust_z(a, fp)
            del a

    return out
