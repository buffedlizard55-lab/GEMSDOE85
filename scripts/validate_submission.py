#!/usr/bin/env python3
"""Validate the exact GeoTIFF conditions that prevent the range error."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems85.grid import read_catalogue, read_template, sha256_file  # noqa: E402


def validate(prediction: Path, template_path: Path, catalogue_path: Path) -> dict:
    template = read_template(template_path)
    footprint = template["footprint"]
    catalogue = read_catalogue(catalogue_path, footprint)
    checks: dict[str, bool] = {}
    notes: list[str] = []
    with rasterio.open(prediction) as src:
        arr = src.read(1)
        inside = arr[footprint]
        outside = arr[~footprint]
        checks["single_band"] = src.count == 1
        checks["dtype_float32"] = src.dtypes[0] == "float32"
        checks["shape_match"] = src.shape == tuple(footprint.shape)
        checks["crs_match"] = src.crs == template["profile"]["crs"]
        checks["transform_match"] = src.transform == template["profile"]["transform"]
        checks["no_nan_inside_footprint"] = bool(np.isfinite(inside).all())
        checks["values_in_0_1_inside"] = bool(np.isfinite(inside).all() and ((inside >= 0) & (inside <= 1)).all())
        checks["all_pixels_finite"] = bool(np.isfinite(arr).all())
        checks["values_in_0_1_entire_raster"] = bool(np.isfinite(arr).all() and ((arr >= 0) & (arr <= 1)).all())
        checks["outside_footprint_zero"] = bool((outside == 0).all())
        checks["zero_catalogue_pixels"] = bool((arr[catalogue] == 0).all())
        if not checks["values_in_0_1_entire_raster"]:
            notes.append("Predicted values are not all in the inclusive [0,1] range.")
        report = {
            "label": "VALIDATOR-RECEIPT",
            "path": str(prediction),
            "sha256": sha256_file(prediction),
            "bytes": prediction.stat().st_size,
            "shape": [int(src.height), int(src.width)],
            "crs": str(src.crs),
            "transform": [float(src.transform.a), float(src.transform.b), float(src.transform.c),
                          float(src.transform.d), float(src.transform.e), float(src.transform.f)],
            "dtype": src.dtypes[0],
            "count": int(src.count),
            "nodata": src.nodata,
            "footprint_pixels": int(footprint.sum()),
            "positive_pixels": int((inside > 0).sum()),
            "unit_pixels": int((inside == 1).sum()),
            "nan_inside_footprint": int((~np.isfinite(inside)).sum()),
            "nan_total": int((~np.isfinite(arr)).sum()),
            "min_value": float(np.nanmin(arr)),
            "max_value": float(np.nanmax(arr)),
            "catalogue_overlap_positive_pixels": int((arr[catalogue] > 0).sum()),
            "checks": checks,
            "notes": notes,
            "passed": bool(all(checks.values())),
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prediction", type=Path)
    parser.add_argument("--template", type=Path, default=ROOT / "data/raw/sample_submission.tif")
    parser.add_argument("--catalogue", type=Path, default=ROOT / "data/raw/existing_faults.tif")
    args = parser.parse_args(argv)
    report = validate(args.prediction, args.template, args.catalogue)
    destination = args.prediction.with_suffix(".validate.json")
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
