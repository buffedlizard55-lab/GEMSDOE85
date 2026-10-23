#!/usr/bin/env python3
"""v2 format validator (brief section 6, MUST-pass gates only).

Validates a candidate GeoTIFF re-read from disk against the pinned
sample_submission.tif template and the pinned catalogue:

  CRS, shape, transform, dtype float32, one band, values in [0,1],
  no NaN inside the footprint, NaN outside (--expect nan) or zeros/finite
  outside (--expect zeros), zero mass on catalogue pixels.

Format PASS is not geological skill, slot approval, or organizer
acceptance. No correlation/overlap uniqueness thresholds are applied
(brief section 6). No network, no credentials.

Usage:
  python scripts/validate_v2_release.py PATH.tif --expect nan|zeros \
      [--sample data/sample_submission.tif] [--catalogue data/existing_faults.tif]
Exit code 0 iff every check passes. Prints a JSON receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

# Pinned template/catalogue bytes (registry/data_manifest.json).
SHA256_SAMPLE = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
SHA256_CATALOGUE = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(path: Path, sample: Path, catalogue: Path, expect: str) -> dict:
    if expect not in ("nan", "zeros"):
        raise ValueError(f"expect must be 'nan' or 'zeros', got {expect!r}")
    if sha256_file(sample) != SHA256_SAMPLE:
        raise ValueError("sample_submission.tif does not match its pin; refusing to validate")
    if sha256_file(catalogue) != SHA256_CATALOGUE:
        raise ValueError("catalogue does not match its pin; refusing to validate")
    with rasterio.open(sample) as tpl:
        tpl_shape = (tpl.height, tpl.width)
        tpl_crs = str(tpl.crs)
        tpl_transform = tuple(tpl.transform)[:6]
        footprint = np.isfinite(tpl.read(1))
    with rasterio.open(catalogue) as cds:
        cat = (cds.read(1) == 1) & footprint
    with rasterio.open(path) as ds:
        a = ds.read(1) if ds.count >= 1 else np.empty((0, 0), dtype=np.float32)
        checks = {
            "single_band": ds.count == 1,
            "dtype_float32": tuple(ds.dtypes) == ("float32",),
            "shape_matches_template": (ds.height, ds.width) == tpl_shape,
            "crs_matches_template": str(ds.crs) == tpl_crs,
            "crs_is_epsg32611": (ds.crs is not None and ds.crs.to_epsg() == 32611),
            "transform_matches_template": tuple(ds.transform)[:6] == tpl_transform,
            "resolution_100m": (abs(ds.transform.a) == 100.0 and abs(ds.transform.e) == 100.0),
        }
        prof = {k: str(ds.profile.get(k)) for k in
                ("driver", "dtype", "nodata", "compress", "tiled", "blockxsize", "blockysize")}
    inside = a[footprint]
    outside = a[~footprint]
    checks["no_nan_inside_footprint"] = bool(np.isfinite(inside).all())
    checks["values_in_0_1_inside"] = bool(
        np.isfinite(inside).all() and (inside >= 0).all() and (inside <= 1).all())
    if expect == "nan":
        checks["nan_outside_footprint"] = bool(np.isnan(outside).all())
    else:
        checks["finite_zeros_outside_footprint"] = bool((outside == 0).all())
    checks["zero_catalogue_mass"] = bool(
        np.nan_to_num(a[cat], nan=0.0).sum() == 0.0 and not (np.isfinite(a[cat]) & (a[cat] > 0)).any())
    checks["has_positive_predictions"] = bool((inside > 0).any())
    finite_pos = np.isfinite(a) & (a > 0)
    stats = {
        "n_dots_positive_pixels": int((finite_pos & footprint).sum()),
        "mass_inside": float(inside.sum()),
        "footprint_pixels": int(footprint.sum()),
        "unique_values_inside": [float(v) for v in np.unique(inside)][:10],
        "on_catalogue_positive_pixels": int((finite_pos & cat).sum()),
    }
    ok = bool(all(checks.values()) and a.shape == tpl_shape)
    return {
        "file": path.name,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "expect_outside": expect,
        "checks": checks,
        "format_ok": ok,
        "stats": stats,
        "profile": prof,
        "note": "Format-only receipt. Not geological skill, slot approval, or organizer acceptance.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tif", type=Path)
    ap.add_argument("--expect", choices=("nan", "zeros"), required=True)
    root = Path(__file__).resolve().parents[1]
    ap.add_argument("--sample", type=Path, default=root / "data/sample_submission.tif")
    ap.add_argument("--catalogue", type=Path, default=root / "data/existing_faults.tif")
    args = ap.parse_args()
    try:
        report = validate(args.tif, args.sample, args.catalogue, args.expect)
    except Exception as exc:  # fail closed with an explicit receipt
        report = {"file": str(args.tif), "format_ok": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report.get("format_ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
