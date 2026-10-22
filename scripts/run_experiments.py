#!/usr/bin/env python3
"""EXPERIMENT 1-3: validate the GEO-Pb lane on the spatially-blocked hide-and-recover holdout.

Everything here is a HOLDOUT-DTI measurement.  No number produced by this script is, or may be
reported as, a leaderboard score.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import baselines, emission, geopb, grid, holdout  # noqa: E402

CACHE = ROOT / "data" / "cache"
OUT = ROOT / "evidence"


def cached(name: str, fn):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{name}.npy"
    if p.exists():
        return np.load(p)
    a = fn()
    np.save(p, a)
    return a


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    n_withheld = sum(f.n_withheld for f in folds)
    print(f"folds: {[f.n_withheld for f in folds]}  total withheld positives = {n_withheld}")

    # ---------------------------------------------------------------- surfaces (catalogue-free)
    print("building surfaces ...")
    surfaces = {
        "geopb_r3_L15":  lambda: geopb.geopb_surface(sigma=1.5, normals=tuple(geopb.NORMALS_R3),
                                                     persistence_px=15.0, footprint=fp),
        "geopb_r6_L25":  lambda: geopb.geopb_surface(sigma=2.5, normals=tuple(geopb.NORMALS_R6),
                                                     persistence_px=25.0, footprint=fp),
        "geopb_r3_L1":   lambda: geopb.geopb_surface(sigma=1.5, normals=tuple(geopb.NORMALS_R3),
                                                     persistence_px=1.0, footprint=fp),
        "ctrl_sato_elev": lambda: baselines.sato_ridge("det_elev", footprint=fp),
        "ctrl_grad_rtp":  lambda: baselines.gradient_magnitude("rtp", 2.0, footprint=fp),
        "ctrl_random":    lambda: baselines.uniform_random(fp, seed=20261022),
    }
    fields = {}
    for k, fn in surfaces.items():
        fields[k] = cached(k, fn)
        print(f"  [{time.time()-t0:6.1f}s] {k}")

    # fused: the two GEO-Pb scales combined by rank (declared in the preregistration)
    def rank01(a):
        v = a[fp]
        r = np.empty(a.shape, np.float32)
        order = np.argsort(v, kind="stable")
        rk = np.empty(v.size, np.float32)
        rk[order] = np.arange(v.size, dtype=np.float32) / max(1, v.size - 1)
        r[:] = 0.0
        r[fp] = rk
        return r

    fields["geopb_fused"] = cached(
        "geopb_fused", lambda: (0.5 * rank01(fields["geopb_r3_L15"])
                                + 0.5 * rank01(fields["geopb_r6_L25"])).astype(np.float32))
    print(f"  [{time.time()-t0:6.1f}s] geopb_fused")

    # ---------------------------------------------------------------- leakage canary
    print("\nLEAKAGE CANARY (AUC of each raw surface vs withheld positives; >0.90 = suspect)")
    canary = {}
    for k, f in fields.items():
        auc = holdout.feature_auc(f, folds, fp)
        canary[k] = auc
        flag = "  <-- SUSPECT LEAKAGE" if auc > 0.90 else ""
        print(f"  {k:16s} AUC = {auc:.4f}{flag}")

    # ---------------------------------------------------------------- holdout DTI at matched mass
    budgets = [20_000, 37_654, 60_000]
    results = {}
    print("\nHOLDOUT-DTI (pooled, 4 spatially-blocked folds, surfaces rebuilt per fold)")
    for k, f in fields.items():
        results[k] = {}
        for n in budgets:
            def surf(fold, f=f, n=n):
                return emission.emit(f, footprint=fp, visible_catalogue=fold.visible,
                                     n=n, sep_px=2.8, exclude_px=2)
            r = holdout.score_folds(surf, folds, domain=fp)
            results[k][n] = r.as_dict()
            print(f"  [{time.time()-t0:6.1f}s] {k:16s} n={n:6d}  "
                  f"pooled DTI = {r.pooled_dti:.5f}  CI95 [{r.ci95[0]:.5f},{r.ci95[1]:.5f}]  "
                  f"per-fold {[round(x.dti,4) for x in r.folds]}")

    # ---------------------------------------------------------------- confounder audit
    print("\nCONFOUNDER AUDIT")
    best, axis = geopb.geopb_surface(sigma=1.5, normals=tuple(geopb.NORMALS_R3),
                                     persistence_px=15.0, footprint=fp, return_parts=True)
    thr = np.percentile(best[fp], 99.0)
    hot = fp & (best >= thr)
    hist = np.bincount(axis[hot], minlength=8).astype(float)
    hist /= hist.sum()
    normals_deg = [round(float(np.degrees(np.arctan2(dx, dy))) % 180, 1)
                   for dy, dx in geopb.NORMALS_R3]
    print("  top-1% response azimuth histogram (normal azimuth deg : share)")
    for a, s in zip(normals_deg, hist):
        bar = "#" * int(round(s * 80))
        print(f"    {a:6.1f} : {s:6.3f} {bar}")
    seam_risk = float(hist.max())
    print(f"  max single-orientation share = {seam_risk:.3f} "
          f"({'OK (<0.35) -- no single azimuth dominates' if seam_risk < 0.35 else 'FLAG: possible acquisition-seam contamination'})")

    summary = {
        "evaluator_version": holdout.EVALUATOR_VERSION,
        "n_withheld_positives": n_withheld,
        "folds": [{"name": f.name, "n_withheld": f.n_withheld, "n_visible": f.n_visible}
                  for f in folds],
        "leakage_canary_auc": canary,
        "holdout_dti": {k: {str(n): v["pooled_holdout_dti"] for n, v in d.items()}
                        for k, d in results.items()},
        "holdout_detail": {k: {str(n): v for n, v in d.items()} for k, d in results.items()},
        "confounder_audit": {
            "top1pct_normal_azimuth_deg": normals_deg,
            "top1pct_share": hist.tolist(),
            "max_single_orientation_share": seam_risk,
            "verdict": "no single azimuth dominates" if seam_risk < 0.35 else "possible seam contamination",
        },
        "runtime_s": time.time() - t0,
    }
    (OUT / "experiments.json").write_text(json.dumps(summary, indent=2, default=float) + "\n")
    print(f"\n-> evidence/experiments.json  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
