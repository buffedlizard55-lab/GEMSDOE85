#!/usr/bin/env python3
"""E2b — bugfix ablation of E2 (session arena/22847afd).

E2 included the per-fold RELAY field as an HGB channel.  Post-hoc diagnostics
(evidence/session_22847afd_experiments.json discussion in the session report)
show that channel is a train/test reversal: relay is built FROM the visible
mask and smoothed along it, so on fold0 its mean is 0.090 on training positives
vs 0.006 on withheld positives and 0.004 on far negatives — in training it
separates positives almost by construction ("near the visible network"), while
against withheld truth its canary AUC is 0.457 (anti-correlated).  The HGB
therefore learned to fire around the visible network, where holdout truth is
absent.  E2b removes the relay channel and keeps everything else identical
(24 base + 6 context channels, same folds, same PU protocol, same budgets),
isolating the actual E2 hypothesis: does line context help?

Logged as a bugfix ablation of experiment 2, not a fourth hypothesis
(same precedent as build_submission.py's logged emission refinement).
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
sys.path.insert(0, str(ROOT / "scripts"))

from gems85 import emission, featurestack, grid, holdout  # noqa: E402
from run_session_experiments import (  # noqa: E402
    SEED, WORK, build_context_channels, pooled_auc, rank01, score_arm)


def train_predict(handles, fp, visible, width, rng, neg_per_pos=8, max_pos=120_000):
    pos_mask = ndi.binary_dilation(visible, np.ones((3, 3), bool), iterations=1) & fp
    far = ~ndi.binary_dilation(visible, np.ones((3, 3), bool), iterations=10) & fp
    pos_idx = np.flatnonzero(pos_mask.ravel())
    neg_pool = np.flatnonzero(far.ravel())
    if pos_idx.size > max_pos:
        pos_idx = rng.choice(pos_idx, max_pos, replace=False)
    neg_idx = rng.choice(neg_pool, min(neg_pool.size, pos_idx.size * neg_per_pos),
                         replace=False)
    idx = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(pos_idx.size, np.int8), np.zeros(neg_idx.size, np.int8)])
    X = featurestack.gather(handles, idx, width)
    clf = HistGradientBoostingClassifier(
        max_iter=180, learning_rate=0.08, max_leaf_nodes=31, min_samples_leaf=60,
        l2_regularization=1.0, random_state=SEED, early_stopping=False)
    clf.fit(X, y)
    out = np.zeros(fp.shape, dtype=np.float32)
    for chunk in np.array_split(np.flatnonzero(fp.ravel()), 12):
        out.ravel()[chunk] = clf.predict_proba(
            featurestack.gather(handles, chunk, width))[:, 1].astype(np.float32)
    return out


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    chan_names = featurestack.build(fp) + build_context_channels(fp)
    handles = featurestack.open_stack(chan_names)
    print(f"E2b channels ({len(chan_names)}, NO relay): {chan_names}", flush=True)

    pf, rng, aucs = {}, np.random.default_rng(SEED), []
    for fold in folds:
        cache_p = WORK / f"ctxhgb2_{fold.name}.npy"
        if cache_p.exists():
            pf[fold.name] = np.load(cache_p)
            print(f"  [{time.time()-t0:6.1f}s] {fold.name} cached", flush=True)
        else:
            f = train_predict(handles, fp, fold.visible, grid.WIDTH, rng)
            np.save(cache_p, f)
            pf[fold.name] = f
        ok = fp & ~fold.visible
        yy = fold.withheld[ok]
        sub = np.random.default_rng(1).choice(yy.size, min(600_000, yy.size), replace=False)
        aucs.append(float(roc_auc_score(yy[sub], pf[fold.name][ok][sub])))
        print(f"  [{time.time()-t0:6.1f}s] {fold.name} withheld-AUC {aucs[-1]:.4f}", flush=True)

    res = {"evaluator_version": holdout.EVALUATOR_VERSION,
           "n_withheld_positives": int(sum(f.n_withheld for f in folds)),
           "note": "E2b bugfix ablation: E2 minus relay channel (train/test reversal).",
           "channels": chan_names, "withheld_auc_per_fold": aucs,
           "mean_withheld_auc": float(np.mean(aucs)),
           "canary_auc_field": pooled_auc(pf, folds, fp), "arms": {}}
    score_arm("E2b_ctxhgb_norelay", pf, folds, fp, res["arms"])
    # sep4 at the gate budget, directly comparable with the 0.07475 reference
    tmp = {}
    score_arm("E2b_ctxhgb_norelay__sep40", pf, folds, fp, tmp, sep=4.0, budgets=(37_654,))
    res["arms"].update(tmp)
    # rank fusion with crest only (no gated component) as the E3-analogue for E2b
    crest = np.load(featurestack.CACHE / "ch_geopb_crest.npy")
    rcrest = rank01(crest, fp)
    fus = {f.name: (0.5 * rank01(pf[f.name], fp) + 0.5 * rcrest).astype(np.float32)
           for f in folds}
    score_arm("E3b_fusion_e2b_crest5050", fus, folds, fp, res["arms"])
    tmp = {}
    score_arm("E3b_fusion_e2b_crest5050__sep40", fus, folds, fp, tmp, sep=4.0,
              budgets=(37_654,))
    res["arms"].update(tmp)
    res["runtime_s"] = time.time() - t0
    (ROOT / "evidence" / "session_22847afd_e2b.json").write_text(
        json.dumps(res, indent=2, default=float) + "\n")
    print(f"-> evidence/session_22847afd_e2b.json ({time.time()-t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    from preflight import experiment_gate
    blocked = experiment_gate(ROOT)
    if blocked:
        raise SystemExit(blocked)
    raise SystemExit(main())
