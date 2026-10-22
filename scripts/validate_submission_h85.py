#!/usr/bin/env python3
"""Standalone validator: python scripts/validate_submission.py <data_dir> <tif>
Re-reads the file from disk and prints the full receipt JSON (no human inspection).
Exit code 0 iff every check passes."""
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems85 import submission_writer as SW  # noqa: E402


def main() -> None:
    data, tif = Path(sys.argv[1]), Path(sys.argv[2])
    with rasterio.open(data / "labels.tif") as s:
        labels = s.read(1) >= 1
    receipt = SW.validate(tif, data / "sample_submission.tif", labels)
    print(json.dumps(receipt, indent=2))
    sys.exit(0 if receipt["all_checks_passed"] else 1)


if __name__ == "__main__":
    main()
