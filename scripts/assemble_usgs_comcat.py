"""Assemble, splice, validate, and deduplicate USGS ComCat catalog over 100% of GeoDAWN.

Public-domain source (CC0 / 17 U.S.C. 105):
    USGS Earthquake Hazards Program FDSN Event Web Service v1 (`format=text`)
    https://earthquake.usgs.gov/fdsnws/event/1/query

All raw chunk transcripts in ``data/external/usgs_raw/`` are spliced per query group,
strictly validated against the 13-column FDSN pipe schema, deduplicated by ``EventID``,
projected to ``EPSG:32611`` (UTM Zone 11N WGS84), and verified to cover ``100.000000%``
(``5,165,852 / 5,165,852``) of valid GeoDAWN pixels in ``data/training_features.tif``.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

EXPECTED_HEADER = (
    "#EventID|Time|Latitude|Longitude|Depth/km|Author|Catalog|Contributor|"
    "ContributorID|MagType|Magnitude|MagAuthor|EventLocationName"
)

QUERY_GROUPS: list[tuple[str, list[str], dict[str, object]]] = [
    (
        "hist_1900_1950",
        ["hist_1900_1950_00_01.txt", "hist_1900_1950_02_03.txt"],
        {
            "starttime": "1900-01-01",
            "endtime": "1950-01-01",
            "minlatitude": 37.35,
            "maxlatitude": 40.75,
            "minlongitude": -120.01,
            "maxlongitude": -116.14,
            "minmagnitude": 3.5,
        },
    ),
    (
        "hist_1950_1980",
        ["hist_1950_1980_00_03.txt", "hist_1950_1980_04_09.txt"],
        {
            "starttime": "1950-01-01",
            "endtime": "1980-01-01",
            "minlatitude": 37.35,
            "maxlatitude": 40.75,
            "minlongitude": -120.01,
            "maxlongitude": -116.14,
            "minmagnitude": 3.0,
        },
    ),
    (
        "band4_m22",
        ["band4_m22_00_05.txt", "band4_m22_05.txt", "band4_m22_06_08.txt"],
        {
            "starttime": "1980-01-01",
            "endtime": "2026-10-20",
            "minlatitude": 39.64,
            "maxlatitude": 40.76,
            "minlongitude": -120.02,
            "maxlongitude": -116.13,
            "minmagnitude": 2.2,
        },
    ),
    (
        "band3_m24",
        ["band3_m24_00_05.txt", "band3_m24_06_10.txt"],
        {
            "starttime": "1980-01-01",
            "endtime": "2026-10-20",
            "minlatitude": 38.80,
            "maxlatitude": 39.65,
            "minlongitude": -119.50,
            "maxlongitude": -117.10,
            "minmagnitude": 2.4,
        },
    ),
    (
        "band3E_m24",
        ["band3E_m24_00_01.txt"],
        {
            "starttime": "1980-01-01",
            "endtime": "2026-10-20",
            "minlatitude": 38.80,
            "maxlatitude": 39.65,
            "minlongitude": -117.11,
            "maxlongitude": -116.13,
            "minmagnitude": 2.4,
        },
    ),
    (
        "band3W_m26",
        ["band3W_m26_00_01.txt", "band3W_m26_02_03.txt"],
        {
            "starttime": "1980-01-01",
            "endtime": "2026-10-20",
            "minlatitude": 38.80,
            "maxlatitude": 39.65,
            "minlongitude": -120.02,
            "maxlongitude": -119.49,
            "minmagnitude": 2.6,
        },
    ),
    (
        "band2_pre2020_m26",
        [
            "band2_pre2020_00_04.txt",
            "band2_pre2020_05_07.txt",
            "band2_pre2020_08_09.txt",
        ],
        {
            "starttime": "1980-01-01",
            "endtime": "2020-05-14",
            "minlatitude": 38.05,
            "maxlatitude": 38.81,
            "minlongitude": -118.90,
            "maxlongitude": -117.24,
            "minmagnitude": 2.6,
        },
    ),
    (
        "band2_post2020_m31",
        ["band2_post2020_00_03.txt", "band2_post2020_04_06.txt"],
        {
            "starttime": "2020-05-14",
            "endtime": "2026-10-20",
            "minlatitude": 38.05,
            "maxlatitude": 38.81,
            "minlongitude": -118.90,
            "maxlongitude": -117.24,
            "minmagnitude": 3.1,
        },
    ),
    (
        "band1N_m29",
        ["band1N_m29_00_01.txt", "band1N_m29_02_04.txt"],
        {
            "starttime": "1980-01-01",
            "endtime": "2026-10-20",
            "minlatitude": 37.75,
            "maxlatitude": 38.06,
            "minlongitude": -118.66,
            "maxlongitude": -117.24,
            "minmagnitude": 2.9,
        },
    ),
    (
        "band1S_m28",
        ["band1S_m28_00_01.txt"],
        {
            "starttime": "1980-01-01",
            "endtime": "2026-10-20",
            "minlatitude": 37.34,
            "maxlatitude": 37.76,
            "minlongitude": -118.25,
            "maxlongitude": -117.24,
            "minmagnitude": 2.8,
        },
    ),
    (
        "band1NW_m29",
        ["band1NW_m29_00.txt"],
        {
            "starttime": "1980-01-01",
            "endtime": "2026-10-20",
            "minlatitude": 37.64,
            "maxlatitude": 37.76,
            "minlongitude": -118.66,
            "maxlongitude": -118.24,
            "minmagnitude": 2.9,
        },
    ),
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    raw_dir = root / "data" / "external" / "usgs_raw"
    out_csv = root / "data" / "external" / "usgs_comcat_geodawn.csv"
    out_meta = root / "data" / "external" / "usgs_comcat_provenance.json"

    events: dict[str, dict[str, object]] = {}
    group_counts: dict[str, int] = {}
    file_hashes: dict[str, str] = {}

    for group_name, filenames, meta in QUERY_GROUPS:
        spliced = ""
        for fname in filenames:
            p = raw_dir / fname
            if not p.exists():
                raise FileNotFoundError(f"Missing raw ComCat file: {p}")
            file_hashes[fname] = sha256_file(p)
            txt = p.read_text(encoding="utf-8")
            # Strip trailing newline ONLY if the file ends mid-record (not a 13-col line)
            lines = txt.splitlines()
            if not lines:
                continue
            if spliced:
                prev_last = spliced.splitlines()[-1]
                next_first = lines[0]
                if len(prev_last.split("|")) < 13 or len(next_first.split("|")) < 13:
                    # Splice mid-line chunk boundary seamlessly (handles splits in cols 1..13)
                    spliced = spliced.rstrip("\r\n") + txt.lstrip("\r\n")
                else:
                    spliced = spliced.rstrip("\r\n") + "\n" + txt.lstrip("\r\n")
            else:
                spliced = txt

        parsed_in_group = 0
        for lineno, line in enumerate(spliced.splitlines(), start=1):
            line_s = line.strip()
            if not line_s:
                continue
            if line_s.startswith("#EventID|"):
                if line_s != EXPECTED_HEADER:
                    raise ValueError(f"{group_name}:{lineno} unexpected header: {line_s}")
                continue
            parts = line_s.split("|")
            if len(parts) != 13:
                raise ValueError(
                    f"{group_name}:{lineno} malformed record ({len(parts)} cols): {line_s!r}"
                )
            (
                ev_id,
                time_s,
                lat_s,
                lon_s,
                depth_s,
                author,
                catalog,
                contributor,
                contrib_id,
                mag_type,
                mag_s,
                mag_author,
                loc_name,
            ) = parts
            lat = float(lat_s)
            lon = float(lon_s)
            depth_km = float(depth_s) if depth_s != "" else np.nan
            mag = float(mag_s)
            year = int(time_s[:4])
            if not (1900 <= year <= 2026):
                raise ValueError(f"{group_name}:{lineno} invalid year {year}: {time_s}")
            if not (37.0 <= lat <= 41.0 and -120.5 <= lon <= -116.0):
                raise ValueError(f"{group_name}:{lineno} out-of-range coords ({lat}, {lon})")
            parsed_in_group += 1
            events[ev_id] = {
                "event_id": ev_id,
                "time_utc": time_s,
                "year": year,
                "latitude": lat,
                "longitude": lon,
                "depth_km": depth_km,
                "mag_type": mag_type,
                "magnitude": mag,
                "catalog": catalog,
                "source_group": group_name,
                "location_name": loc_name,
            }
        group_counts[group_name] = parsed_in_group

    rows = sorted(events.values(), key=lambda r: (str(r["time_utc"]), str(r["event_id"])))

    tf_fwd = Transformer.from_crs("EPSG:4326", "EPSG:32611", always_xy=True)
    lons_ev = np.array([float(r["longitude"]) for r in rows], dtype=np.float64)
    lats_ev = np.array([float(r["latitude"]) for r in rows], dtype=np.float64)
    xs_ev, ys_ev = tf_fwd.transform(lons_ev, lats_ev)

    with rasterio.open(root / "data" / "training_features.tif") as src:
        inv_tf = ~src.transform
        cols_f, rows_f = inv_tf * (xs_ev, ys_ev)
        r_idx = np.floor(rows_f).astype(np.int64)
        c_idx = np.floor(cols_f).astype(np.int64)
        b1 = src.read(1)
        nodata = src.nodata
        valid_mask = np.isfinite(b1) & (b1 != nodata) & (b1 > -1e30)
        in_grid = (
            (r_idx >= 0) & (r_idx < src.height) & (c_idx >= 0) & (c_idx < src.width)
        )
        in_valid = np.zeros(len(rows), dtype=bool)
        in_valid[in_grid] = valid_mask[r_idx[in_grid], c_idx[in_grid]]

        # Verify 100.000000% spatial box coverage over all valid pixels
        vr, vc = np.where(valid_mask)
        vx, vy = rasterio.transform.xy(src.transform, vr, vc)
        tf_inv = Transformer.from_crs("EPSG:32611", "EPSG:4326", always_xy=True)
        vlon, vlat = tf_inv.transform(np.asarray(vx), np.asarray(vy))

    modern_covered = np.zeros(len(vlat), dtype=bool)
    hist_covered = (
        (vlat >= 37.35) & (vlat <= 40.75) & (vlon >= -120.01) & (vlon <= -116.14)
    )
    for gname, _, meta in QUERY_GROUPS:
        if gname.startswith("hist_"):
            continue
        modern_covered |= (
            (vlat >= float(meta["minlatitude"]))
            & (vlat <= float(meta["maxlatitude"]))
            & (vlon >= float(meta["minlongitude"]))
            & (vlon <= float(meta["maxlongitude"]))
        )
    if not np.all(modern_covered) or not np.all(hist_covered):
        raise RuntimeError(
            f"Incomplete valid-pixel coverage: modern={modern_covered.sum()}/{len(vlat)}, "
            f"hist={hist_covered.sum()}/{len(vlat)}"
        )

    fieldnames = [
        "event_id",
        "time_utc",
        "year",
        "latitude",
        "longitude",
        "utm_x_m",
        "utm_y_m",
        "row_100m",
        "col_100m",
        "in_geodawn_valid",
        "depth_km",
        "mag_type",
        "magnitude",
        "catalog",
        "source_group",
        "location_name",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, r in enumerate(rows):
            writer.writerow(
                {
                    **r,
                    "utm_x_m": round(float(xs_ev[i]), 2),
                    "utm_y_m": round(float(ys_ev[i]), 2),
                    "row_100m": int(r_idx[i]),
                    "col_100m": int(c_idx[i]),
                    "in_geodawn_valid": int(in_valid[i]),
                    "depth_km": "" if np.isnan(float(r["depth_km"])) else r["depth_km"],
                }
            )

    csv_sha = sha256_file(out_csv)
    summary = {
        "source": "USGS Earthquake Hazards Program ComCat FDSN Event Web Service v1",
        "license": "Public Domain (17 U.S.C. 105 / CC0)",
        "endpoint": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=text",
        "retrieved_utc_date": "2026-10-22",
        "temporal_span": "1900-01-01 to 2026-10-20",
        "valid_geodawn_pixels_total": int(len(vlat)),
        "valid_geodawn_pixels_covered_modern": int(modern_covered.sum()),
        "valid_geodawn_pixels_covered_historical": int(hist_covered.sum()),
        "coverage_fraction": 1.0,
        "raw_records_parsed": int(sum(group_counts.values())),
        "unique_events_deduplicated": int(len(rows)),
        "events_in_raster_bbox": int(in_grid.sum()),
        "events_inside_valid_geodawn_footprint": int(in_valid.sum()),
        "events_m_ge_4_0": int(sum(float(r["magnitude"]) >= 4.0 for r in rows)),
        "events_m_ge_5_0": int(sum(float(r["magnitude"]) >= 5.0 for r in rows)),
        "events_post_2021_post_gdr1391_cutoff": int(sum(int(r["year"]) >= 2022 for r in rows)),
        "group_record_counts": group_counts,
        "output_csv": "data/external/usgs_comcat_geodawn.csv",
        "output_csv_sha256": csv_sha,
        "raw_chunk_sha256": file_hashes,
        "query_groups": [
            {"name": g, "files": fs, "parameters": m} for g, fs, m in QUERY_GROUPS
        ],
    }
    out_meta.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("raw_chunk_sha256", "query_groups")}, indent=2))


if __name__ == "__main__":
    main()
