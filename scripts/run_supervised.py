#!/usr/bin/env python3
"""EXPERIMENT 3: does GEO-Pb add credit on top of the family's derivative descriptors?

Protocol: identical hide-and-recover folds.  For each fold a gradient-boosted classifier is
trained on **that fold's visible catalogue only** and scored on the withheld segments, so the
model never sees the answer.  Two arms differ by one thing only -- whether the three GEO-Pb
channels are in the stack.  That is the ablation that isolates the lane's contribution.

Every number is HOLDOUT-DTI.  None is a leaderboard score.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import emission, featurestack, grid, holdout  # noqa: E402

GEOPB = ["geopb_r3_L15", "geopb_r6_L25", "geopb_crest"]
SEED = 20261022


def train_predict(handles, fp, visible, width, rng, *, neg_per_pos=8, max_pos=120_000):
    """PU-style training set from `visible` only; returns a full-grid probability field."""
    pos_mask = ndi.binary_dilation(visible, np.ones((3, 3), bool), iterations=1) & fp
    far = ~ndi.binary_dilation(visible, np.ones((3, 3), bool), iterations=10) & fp
    pos_idx = np.flatnonzero(pos_mask.ravel())
    neg_pool = np.flatnonzero(far.ravel())
    if pos_idx.size > max_pos:
        pos_idx = rng.choice(pos_idx, max_pos, replace=False)
    n_neg = min(neg_pool.size, pos_idx.size * neg_per_pos)
    neg_idx = rng.choice(neg_pool, n_neg, replace=False)
    idx = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(pos_idx.size, np.int8), np.zeros(neg_idx.size, np.int8)])
    X = featurestack.gather(handles, idx, width)
    clf = HistGradientBoostingClassifier(
        max_iter=180, learning_rate=0.08, max_leaf_nodes=31, min_samples_leaf=60,
        l2_regularization=1.0, random_state=SEED, early_stopping=False)
    clf.fit(X, y)

    out = np.zeros(fp.shape, dtype=np.float32)
    all_idx = np.flatnonzero(fp.ravel())
    for chunk in np.array_split(all_idx, 12):
        out.ravel()[chunk] = clf.predict_proba(
            featurestack.gather(handles, chunk, width))[:, 1].astype(np.float32)
    return out, clf


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    W = grid.WIDTH
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)

    names = featurestack.build(fp)
    print(f"[{time.time()-t0:6.1f}s] {len(names)} channels cached")
    arms = {"with_geopb": names, "without_geopb": [n for n in names if n not in GEOPB]}

    out = {"evaluator_version": holdout.EVALUATOR_VERSION, "channels": names, "arms": {}}
    fields = {}
    for arm, chans in arms.items():
        handles = featurestack.open_stack(chans)
        rng = np.random.default_rng(SEED)
        per_fold_fields, aucs = {}, []
        for fold in folds:
            f, clf = train_predict(handles, fp, fold.visible, W, rng)
            per_fold_fields[fold.name] = f
            ok = fp & ~fold.visible
            yy = fold.withheld[ok]
            sub = np.random.default_rng(1).choice(yy.size, min(600_000, yy.size), replace=False)
            aucs.append(float(roc_auc_score(yy[sub], f[ok][sub])))
            print(f"[{time.time()-t0:6.1f}s] {arm} {fold.name}: withheld-AUC {aucs[-1]:.4f}")
        fields[arm] = per_fold_fields
        res = {}
        for n in (37_654, 60_000, 100_000):
            r = holdout.score_folds(
                lambda fold, n=n: emission.emit(per_fold_fields[fold.name], footprint=fp,
                                                visible_catalogue=fold.visible, n=n,
                                                sep_px=2.8, exclude_px=2),
                folds, domain=fp)
            res[str(n)] = r.as_dict()
            print(f"[{time.time()-t0:6.1f}s] {arm:14s} n={n:6d}  pooled DTI = {r.pooled_dti:.5f}"
                  f"  CI95 [{r.ci95[0]:.5f},{r.ci95[1]:.5f}]"
                  f"  folds {[round(x.dti,4) for x in r.folds]}")
        out["arms"][arm] = {"channels": chans, "withheld_auc_per_fold": aucs,
                            "mean_withheld_auc": float(np.mean(aucs)), "holdout": res}
        del handles

    a, b = out["arms"]["with_geopb"], out["arms"]["without_geopb"]
    out["geopb_ablation"] = {
        str(n): {
            "with": a["holdout"][str(n)]["pooled_holdout_dti"],
            "without": b["holdout"][str(n)]["pooled_holdout_dti"],
            "delta": a["holdout"][str(n)]["pooled_holdout_dti"]
                     - b["holdout"][str(n)]["pooled_holdout_dti"],
            "folds_positive": sum(
                1 for x, y in zip(a["holdout"][str(n)]["folds"], b["holdout"][str(n)]["folds"])
                if x["dti"] > y["dti"]),
        } for n in (37_654, 60_000, 100_000)
    }
    out["mean_auc_delta"] = a["mean_withheld_auc"] - b["mean_withheld_auc"]
    out["runtime_s"] = time.time() - t0
    (ROOT / "evidence" / "supervised_ablation.json").write_text(
        json.dumps(out, indent=2, default=float) + "\n")
    print("\nGEO-Pb ABLATION (with minus without, matched mass, same folds)")
    for n, d in out["geopb_ablation"].items():
        print(f"  n={n:>6s}: {d['with']:.5f} - {d['without']:.5f} = {d['delta']:+.5f}"
              f"   ({d['folds_positive']}/4 folds positive)")
    print(f"  mean withheld-AUC delta = {out['mean_auc_delta']:+.4f}")
    print(f"-> evidence/supervised_ablation.json  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    from preflight import experiment_gate
    blocked = experiment_gate(ROOT)
    if blocked:
        raise SystemExit(blocked)
    raise SystemExit(main())
