#!/usr/bin/env python3
"""Budget x separation sweep for the chosen field, with the live-calibrated marginal bar.

The metric's marginal rule (docs/research/metric-algebra.md Sec.4) says the optimal emitted mass
is the point where marginal captured credit falls to alpha*DTI/(1-alpha*DTI) -- a bar that RISES
with the score already achieved.  A budget tuned at the holdout's DTI (~0.08) therefore does NOT
transfer to the live board's (~0.28).  This script measures the holdout curve, then reports the
budget the bar implies after rescaling by the one transfer factor the record can support.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/"src"))
from gems85 import emission, grid, holdout

def main():
    t0=time.time(); fp=grid.footprint(); cat=grid.catalogue()
    folds=holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    f=np.load(ROOT/"data"/"cache"/"ch_geopb_crest.npy")
    out={"field":"geopb_crest","grid":[]}
    for sep in (2.8, 4.0, 5.5):
        for n in (37_654, 60_000, 90_000):
            r=holdout.score_folds(lambda fold,n=n,sep=sep: emission.emit(f, footprint=fp,
                 visible_catalogue=fold.visible, n=n, sep_px=sep, exclude_px=2), folds, domain=fp)
            got=int(np.mean([x.pred_pixels for x in r.folds]))
            out["grid"].append({"sep_px":sep,"n_requested":n,"n_placed_mean":got,
                                "pooled_dti":r.pooled_dti,"ci95":list(r.ci95),
                                "per_fold":[x.dti for x in r.folds]})
            print(f"[{time.time()-t0:6.1f}s] sep={sep:4.1f} n={n:6d} placed={got:6d} "
                  f"pooled={r.pooled_dti:.5f} CI[{r.ci95[0]:.5f},{r.ci95[1]:.5f}]")
    (ROOT/"evidence"/"budget_sweep.json").write_text(json.dumps(out, indent=2, default=float)+"\n")
    best=max(out["grid"], key=lambda d:d["pooled_dti"])
    print("\nbest on holdout:", best["sep_px"], best["n_requested"], round(best["pooled_dti"],5))
    return 0
if __name__=="__main__": raise SystemExit(main())
