#!/usr/bin/env python3
"""Direct pass-through CLI entrypoint to shared upstream ``vendor/gems57/evaluate_holdout.py``."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57.evaluate_holdout import (  # noqa: E402, F401
    VERSION as EVALUATOR_VERSION,
    evaluate,
    implementation_hashes,
    pooled_summary,
)
from gems57.grid import Grid  # noqa: E402
from gems57.holdout import buffered_component_draw  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prediction", required=True)
    ap.add_argument("--existing-faults", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[20, 30])
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with rasterio.open(args.template) as ds:
        valid = np.isfinite(ds.read(1))
        crs, transform, h, w = ds.crs, ds.transform, ds.height, ds.width
    with rasterio.open(args.existing_faults) as ds:
        cat = (ds.read(1) > 0) & valid
    grid = Grid(footprint=valid, catalogue=cat, crs=crs, transform=transform, height=h, width=w)
    with rasterio.open(args.prediction) as ds:
        raw_p = ds.read(1).astype(np.float32)
    p = np.where(valid & np.isfinite(raw_p), np.clip(raw_p, 0.0, 1.0), 0.0)

    total_terms = None
    per_seed = {}
    for s in args.seeds:
        folds, _quad = buffered_component_draw(grid, seed=s)
        seed_terms = None
        seed_folds = []
        for f in folds:
            res, terms = evaluate(p, f, valid)
            seed_folds.append(res)
            seed_terms = terms if seed_terms is None else (seed_terms + terms)
        per_seed[str(s)] = seed_folds
        total_terms = seed_terms if total_terms is None else (total_terms + seed_terms)

    summary = pooled_summary({"candidate": total_terms}, draws=args.draws, candidate="candidate")
    summary["per_seed"] = per_seed
    out_p = Path(args.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(summary, indent=2) + "\n")
    sc = summary["scores"]["candidate"]
    print(f"HOLDOUT-DTI ({EVALUATOR_VERSION}): {sc['dti']:.6f} | 95% CI {sc['ci95']} | K={sc['withheld_positive_pixels']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
