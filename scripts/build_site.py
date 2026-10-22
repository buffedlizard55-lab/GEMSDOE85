#!/usr/bin/env python3
"""Build static site checks — verifies all downloads have valid audits."""
from pathlib import Path
import json, rasterio, numpy as np
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs/downloads"
DATA=ROOT/"data"
with rasterio.open(DATA/"sample_submission.tif") as s:
    foot=np.isfinite(s.read(1))
with rasterio.open(DATA/"labels.tif") as s:
    labs=s.read(1)==1
from src.gems85.submission import audit_geotiff
ok=True
for tif in DOCS.glob("*.tif"):
    mode="zeros" if "zeros" in tif.name else "nan"
    try:
        a=audit_geotiff(tif, foot, labs, mode=mode)
        print(f"PASS {tif.name} {a['emitted_positive_pixels']} dots sha {a['sha256'][:8]}")
    except Exception as e:
        print(f"FAIL {tif.name}: {e}")
        ok=False
if ok:
    print("All downloads PASS")
else:
    raise SystemExit(1)
