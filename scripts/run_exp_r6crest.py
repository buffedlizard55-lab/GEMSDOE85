#!/usr/bin/env python3
"""EXP (this session): GEO-Pb radius-6, persistence retired (L=1), crest-thinned with R6 normals.

Pre-registered comparison: same evaluator (gems85-holdout-1, 4 spatially-blocked folds,
60,988 withheld positives), same emission (sep 4 px, exclude 2 px) as the shipped
geopb_crest field. Promotion bar: pooled HOLDOUT-DTI at 90,000 dots must exceed the
shipped field's 0.09838 with a CI that does not overlap it. Negative results are deliverables.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from gems85 import emission, geopb, grid, holdout  # noqa: E402

def main() -> int:
    t0 = time.time(); fp = grid.footprint(); cat = grid.catalogue()
    cache = ROOT / "data" / "cache"; cache.mkdir(parents=True, exist_ok=True)
    cp = cache / "ch_geopb_r6crest_L1.npy"
    if cp.exists():
        field = np.load(cp)
    else:
        surf, axis = geopb.geopb_surface(sigma=2.5, normals=tuple(geopb.NORMALS_R6),
                                         persistence_px=1.0, footprint=fp, return_parts=True)
        field = geopb.crest(surf, axis, normals=tuple(geopb.NORMALS_R6))
        np.save(cp, field)
    print(f"surface ready [{time.time()-t0:.0f}s] nonzero={int((field>0).sum())}")
    # leakage canary: single-surface AUC vs catalogue on a fixed footprint subsample
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(7)
    idx = rng.choice(np.flatnonzero(fp.ravel()), 400_000, replace=False)
    auc = float(roc_auc_score(cat.ravel()[idx], field.ravel()[idx]))
    print(f"leakage canary AUC (vs full catalogue, subsample) = {auc:.4f}  (>0.90 would flag leakage)")
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    out = {"experiment": "geopb_r6_L1_crest", "evaluator": "gems85-holdout-1",
           "n_withheld_positives": int(sum(f.n_withheld for f in folds)),
           "leakage_canary_auc_subsample": auc, "grid": []}
    for n in (37_654, 60_000, 90_000):
        r = holdout.score_folds(lambda fold, n=n: emission.emit(
            field, footprint=fp, visible_catalogue=fold.visible, n=n, sep_px=4.0, exclude_px=2),
            folds, domain=fp)
        out["grid"].append({"n_requested": n, "pooled_dti": r.pooled_dti, "ci95": list(r.ci95),
                            "per_fold": [x.dti for x in r.folds]})
        print(f"n={n} pooled={r.pooled_dti:.5f} CI[{r.ci95[0]:.5f},{r.ci95[1]:.5f}] [{time.time()-t0:.0f}s]")
    out["shipped_reference"] = {"field": "geopb_crest r3 L15 sep4", "dti_90000": 0.09838,
                                "ci95": [0.09022, 0.10654]}
    (ROOT / "evidence" / "exp_r6crest.json").write_text(json.dumps(out, indent=2) + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
