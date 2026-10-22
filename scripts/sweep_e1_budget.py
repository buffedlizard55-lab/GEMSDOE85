#!/usr/bin/env python3
"""Operating-point sweep INSIDE Experiment 1 (not a new experiment): reuse the
saved fold fields (field_e1_fold*.npy) and vary only the global-equivalent
emission budget.  Bar: CTRL_d28 pooled HOLDOUT-DTI from evidence/holdout_experiments.json.
Usage: sweep_e1_budget.py <data_dir> <cache_dir>"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems85 import emitter, fields, evaluate_holdout as EH  # noqa: E402


def read_bool(p):
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def main():
    data, cache = Path(sys.argv[1]), Path(sys.argv[2])
    t0 = time.time()
    with rasterio.open(data / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    labels = read_bool(data / "labels.tif") & foot
    holdout = EH.make_holdout(labels, foot)
    union_withheld = {}
    for fold in range(4):
        u = np.zeros_like(labels)
        for c in holdout.cells:
            if c.fold == fold:
                u |= c.withheld
        union_withheld[fold] = u

    results = {}
    for budget_global in [20000, 25000, 44090, 55000]:
        fold_masks = {}
        for fold in range(4):
            cells = [c for c in holdout.cells if c.fold == fold]
            surf = np.load(cache / f"field_e1_fold{fold}.npy")
            visible_fold = labels & ~union_withheld[fold]
            d_vis = ndimage.distance_transform_edt(~visible_fold)
            allowed = cells[0].test_domain & foot & (d_vis > 2.0)
            budget = int(round(budget_global * float(cells[0].test_domain.sum()) / float(foot.sum())))
            support_n = int(round(150000 * float(cells[0].test_domain.sum()) / float(foot.sum())))
            sup = fields.top_n_support(surf, allowed, support_n)
            mask, log = emitter.emit(np.where(sup, surf, 0.0).astype(np.float32),
                                     budget=budget, prior_dti=0.0)
            for c in cells:
                fold_masks[c.key] = mask
        r = EH.score_fold_masks(fold_masks, holdout)
        results[str(budget_global)] = r
        print(f"budget {budget_global}: HOLDOUT-DTI pooled={r['pooled_dti']:.6f} CI={r['ci95']} ({time.time()-t0:.0f}s)", flush=True)
    out = dict(experiment="E1_supervised_hgb", sweep=results)
    (ROOT / "evidence" / "e1_budget_sweep.json").write_text(json.dumps(out, indent=2, default=float))
    print("DONE")


if __name__ == "__main__":
    main()
