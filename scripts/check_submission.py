#!/usr/bin/env python3
"""Check a submission TIF against all 12 DrivenData validator checks."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from gems85.submission import audit_geotiff
import rasterio, numpy as np

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <tif_path>")
    sys.exit(1)

tif = Path(sys.argv[1])
sample = Path(__file__).resolve().parents[1]/"data/sample_submission.tif"
labels_p = Path(__file__).resolve().parents[1]/"data/labels.tif"
with rasterio.open(sample) as src:
    foot = np.isfinite(src.read(1))
with rasterio.open(labels_p) as src:
    labs = src.read(1)==1

audit = audit_geotiff(tif, foot, labs, mode="zeros" if "zeros" in tif.name else "nan")
print(f"{tif.name}: {audit['checks']}")
print(f"all_passed: {audit['all_checks_passed']}")
print(f"sha256: {audit['sha256']}")
print(f"emitted: {audit['emitted_positive_pixels']}, on_cat: {audit['on_catalogue_positive_pixels']}")
# Also check validator_range
import json
print(json.dumps(audit, indent=2))
