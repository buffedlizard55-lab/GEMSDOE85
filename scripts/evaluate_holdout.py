#!/usr/bin/env python3
"""Evaluate a binary prediction with the auditable hide-and-recover split."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85.grid import read_catalogue, read_template  # noqa: E402
from gems85.holdout import score_holdout, withhold_segments  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prediction", type=Path)
    parser.add_argument("--template", type=Path, default=ROOT / "data/raw/sample_submission.tif")
    parser.add_argument("--catalogue", type=Path, default=ROOT / "data/raw/existing_faults.tif")
    parser.add_argument("--no-bootstrap", action="store_true")
    args = parser.parse_args(argv)
    template = read_template(args.template)
    catalogue = read_catalogue(args.catalogue, template["footprint"])
    with rasterio.open(args.prediction) as src:
        prediction = src.read(1) > 0.5
    split = withhold_segments(catalogue, template["footprint"])
    report = score_holdout(prediction, split, template["footprint"], bootstrap=not args.no_bootstrap)
    report["prediction"] = str(args.prediction)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
