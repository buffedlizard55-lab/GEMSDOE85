#!/usr/bin/env python3
"""Write the finite, zeros-outside GEMS GeoTIFF submission.

This writer deliberately produces the safer upload artifact: one float32 band,
all cells finite, every value in [0,1], and zeros outside the sample footprint.
It copies CRS, shape, and affine transform from the sample raster and zeroes
catalogue cells so no known fault pixels are emitted.
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85.grid import read_catalogue, read_template, sha256_file  # noqa: E402


def write_submission(mask: np.ndarray, template_path: Path, catalogue_path: Path,
                     output_path: Path, zip_path: Path | None = None) -> dict:
    template = read_template(Path(template_path))
    footprint = template["footprint"]
    catalogue = read_catalogue(Path(catalogue_path), footprint)
    if mask.shape != footprint.shape:
        raise ValueError(f"mask shape {mask.shape} != template shape {footprint.shape}")
    clean = np.asarray(mask, dtype=bool) & footprint & ~catalogue
    arr = np.where(footprint, clean.astype(np.float32), np.float32(0.0)).astype(np.float32)
    profile = template["profile"].copy()
    profile.update(driver="GTiff", dtype="float32", count=1, nodata=None, compress="deflate",
                   tiled=True, blockxsize=256, blockysize=256)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(arr, 1)
        dst.set_band_description(1, "fault_probability")
    if zip_path is None:
        zip_path = output_path.with_suffix(".zip")
    zip_path = Path(zip_path)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(output_path, arcname=output_path.name)

    with rasterio.open(output_path) as src:
        written = src.read(1)
        inside = written[footprint]
        outside = written[~footprint]
        checks = {
            "single_band": src.count == 1,
            "dtype_float32": src.dtypes[0] == "float32",
            "shape_match": src.shape == footprint.shape,
            "crs_match": src.crs == template["profile"]["crs"],
            "transform_match": src.transform == template["profile"]["transform"],
            "no_nan_inside_footprint": bool(np.isfinite(inside).all()),
            "values_in_0_1_inside": bool(((inside >= 0) & (inside <= 1)).all()),
            "all_pixels_finite": bool(np.isfinite(written).all()),
            "all_pixels_in_0_1": bool(((written >= 0) & (written <= 1)).all()),
            "outside_footprint_zero": bool((outside == 0).all()),
            "zero_catalogue_pixels": bool((written[catalogue] == 0).all()),
        }
        report = {
            "label": "VALIDATOR-RECEIPT",
            "path": str(output_path),
            "zip_path": str(zip_path),
            "sha256": sha256_file(output_path),
            "zip_sha256": sha256_file(zip_path),
            "bytes": output_path.stat().st_size,
            "zip_bytes": zip_path.stat().st_size,
            "shape": [int(src.height), int(src.width)],
            "crs": str(src.crs),
            "transform": [float(src.transform.a), float(src.transform.b), float(src.transform.c),
                          float(src.transform.d), float(src.transform.e), float(src.transform.f)],
            "dtype": src.dtypes[0],
            "nodata": src.nodata,
            "footprint_pixels": int(footprint.sum()),
            "positive_pixels": int((written[footprint] > 0).sum()),
            "unit_pixels": int((written[footprint] == 1).sum()),
            "catalogue_overlap_pixels": int((written[catalogue] > 0).sum()),
            "nan_inside_footprint": int((~np.isfinite(inside)).sum()),
            "min_value": float(np.min(written)),
            "max_value": float(np.max(written)),
            "checks": checks,
            "passed": bool(all(checks.values())),
        }
    report_path = output_path.with_suffix(".audit.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mask-tif", required=True, type=Path)
    parser.add_argument("--template", default=ROOT / "data/raw/sample_submission.tif", type=Path)
    parser.add_argument("--catalogue", default=ROOT / "data/raw/existing_faults.tif", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    args = parser.parse_args(argv)
    with rasterio.open(args.mask_tif) as src:
        mask = src.read(1) > 0.5
    report = write_submission(mask, args.template, args.catalogue, args.output, args.zip_path)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
