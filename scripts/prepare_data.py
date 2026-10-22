#!/usr/bin/env python3
"""Check placement and geometry of the competition inputs.

The feature stack is intentionally not committed because it is about 419 MB.
Run ``scripts/restore_feature_stack.sh`` to restore it from the pinned GitHub
bridge when an unrestricted GitHub connection is available.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems85.grid import EXPECTED_CRS, EXPECTED_SHAPE, read_catalogue, read_template, sha256_file  # noqa: E402

EXPECTED = {
    "labels.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}


def inspect(path: Path) -> dict:
    with rasterio.open(path) as ds:
        return {
            "path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path),
            "shape": [int(ds.height), int(ds.width)], "count": int(ds.count),
            "dtype": ds.dtypes[0], "crs": str(ds.crs),
            "transform": [float(ds.transform.a), float(ds.transform.b), float(ds.transform.c),
                          float(ds.transform.d), float(ds.transform.e), float(ds.transform.f)],
            "nodata": ds.nodata,
            "descriptions": list(ds.descriptions),
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/raw")
    parser.add_argument("--features", type=Path, default=ROOT / "data/training_features.tif")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/data_receipt.json")
    args = parser.parse_args(argv)
    data_dir = args.data_dir
    report = {"label": "DATA-PLACEMENT-RECEIPT", "files": {}, "irregularities": [], "passed": False}
    errors = []
    for name, expected_hash in EXPECTED.items():
        path = data_dir / name
        if not path.is_file():
            errors.append(f"missing {path}")
            continue
        row = inspect(path)
        row["sha256_expected"] = expected_hash
        row["sha256_match"] = row["sha256"] == expected_hash
        report["files"][name] = row
        if not row["sha256_match"]:
            errors.append(f"sha256 mismatch for {path}")
    if (data_dir / "labels.tif").is_file() and (data_dir / "existing_faults.tif").is_file():
        with rasterio.open(data_dir / "labels.tif") as a, rasterio.open(data_dir / "existing_faults.tif") as b:
            if not np.array_equal(a.read(1), b.read(1)):
                errors.append("labels.tif and existing_faults.tif differ; this project expects the supplied catalogue mirror")
    if (data_dir / "sample_submission.tif").is_file():
        template = read_template(data_dir / "sample_submission.tif")
        if tuple(template["footprint"].shape) != EXPECTED_SHAPE:
            errors.append("sample_submission shape differs from the pinned competition grid")
        if str(template["profile"]["crs"]) != EXPECTED_CRS:
            errors.append("sample_submission CRS differs from EPSG:32611")
        report["template_footprint_pixels"] = int(template["footprint"].sum())
    feature_path = args.features
    if feature_path.is_file():
        feature = inspect(feature_path)
        report["features"] = feature
        report["feature_stack_present"] = True
        if feature["count"] != 19:
            errors.append(f"expected 19 feature bands, found {feature['count']}")
        if feature["shape"] != list(EXPECTED_SHAPE):
            errors.append("feature stack shape differs from the pinned competition grid")
    else:
        report["feature_stack_present"] = False
        report["feature_stack_expected_path"] = str(feature_path)
        report["irregularities"].append("feature stack is not committed; restore_feature_stack.sh is required for H85 generation")
        errors.append(f"missing feature stack {feature_path}")
    report["errors"] = errors
    report["passed"] = not errors
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
