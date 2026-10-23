#!/usr/bin/env python3
"""Session arena/22847afd experiments E1-E3 (pre-registered in
research/session-22847afd-hypotheses.md, written before any result was seen).

E1  RELAY geometry alone + RELAY-gated GEO-Pb crest.
E2  CTXHGB: 24-ch stack + line-context channels + per-fold RELAY channel,
    HistGradientBoosting trained per fold on visible catalogue only.
E3  Fusion 0.5*rank(E2) + 0.25*rank(crest) + 0.25*rank(RELAY-gated crest),
    emitted by (a) Poisson-thin sep2.8 and (b) Poisson-thin sep2.8 on the
    kernel-blurred (coverage-credit) field.

Evaluator: gems85-holdout-v1.0.0 (src/gems85/holdout.py), 4 spatially-blocked
folds, 60,988 withheld positives, pooled DTI alpha 0.2 beta 0.8 R=300 m.
Every number is HOLDOUT-DTI.  Reference to beat @37,654: GEO-Pb crest
0.06953 (sep2.8) / 0.07475 (sep4) from evidence/budget_sweep.json.
Per-fold fields are cached in work/ so a re-run does not retrain.
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

from gems85 import emission, featurestack, geopb, grid, holdout, relay  # noqa: E402
from gems85.emission_duplex import coverage_credit  # noqa: E402

WORK = ROOT / "work"
WORK.mkdir(exist_ok=True)
SEED = 20261022
BUDGETS = (37_654, 60_000)


def rank01(a: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Tie-averaged percentile rank inside the footprint.

    BUGFIX (session log): the first version used a stable argsort, which assigns
    *raster-order* ranks to tied values.  Sparse fields (RELAY is 0 on ~64% of
    the footprint; the crest is 0 on most of it) thereby acquired a fake
    north-west-to-south-east rank gradient.  The buggy E1 gated numbers
    (0.03683 @37,654) are recorded in the session log as superseded; all arms
    below use tie-averaged ranks via scipy.stats.rankdata.
    """
    from scipy import stats
    v = a[fp].astype(np.float64)
    rk = (stats.rankdata(v, method="average") - 1.0) / max(1, v.size - 1)
    out = np.zeros(a.shape, np.float32)
    out[fp] = rk.astype(np.float32)
    return out


def pooled_auc(per_fold_fields, folds, fp, seed=7, neg_cap=400_000):
    """Canary AUC for a field that is rebuilt per fold (visible-only inputs)."""
    pos_all, neg_all = [], []
    rng = np.random.default_rng(seed)
    for fold in folds:
        f = per_fold_fields[fold.name]
        ok = fp & ~fold.visible & np.isfinite(f)
        pos_all.append(f[ok & fold.withheld])
        neg = f[ok & ~fold.withheld]
        if neg.size > neg_cap:
            neg = rng.choice(neg, neg_cap, replace=False)
        neg_all.append(neg)
    y = np.concatenate([np.ones(sum(p.size for p in pos_all)),
                        np.zeros(sum(n.size for n in neg_all))])
    s = np.concatenate(pos_all + neg_all)
    return float(roc_auc_score(y, s))


def score_arm(name, per_fold_fields, folds, fp, out, sep=2.8, budgets=BUDGETS):
    out[name] = {}
    for n in budgets:
        r = holdout.score_folds(
            lambda fold, n=n: emission.emit(
                per_fold_fields[fold.name], footprint=fp,
                visible_catalogue=fold.visible, n=n, sep_px=sep, exclude_px=2),
            folds, domain=fp)
        out[name][str(n)] = r.as_dict()
        print(f"  {name:26s} n={n:6d} sep={sep}  DTI={r.pooled_dti:.5f} "
              f"CI95[{r.ci95[0]:.5f},{r.ci95[1]:.5f}] folds={[round(x.dti,4) for x in r.folds]}",
              flush=True)
    return out


def build_context_channels(fp):
    """Catalogue-free context channels, cached like featurestack channels."""
    cache = featurestack.CACHE
    crest = np.load(cache / "ch_geopb_crest.npy")
    step = np.load(cache / "ch_lidar_step_max.npy")
    grtp = np.load(cache / "ch_grad_rtp_s2.npy")
    g3 = np.load(cache / "ch_geopb_r3_L15.npy")

    def save(name, a):
        p = cache / f"ch_{name}.npy"
        if not p.exists():
            a = np.asarray(a, dtype=np.float32)
            a[~fp] = 0.0
            np.save(p, a)
        return name

    names = []
    # along-strike line support: max over 8 orientations of 1.5 km line mean of geopb_r3
    p = cache / "ch_ctx_linemax.npy"
    if not p.exists():
        best = np.zeros(fp.shape, np.float32)
        for dy, dx in geopb.NORMALS_R3:          # trace dir is perpendicular to normal
            lm = geopb.line_mean(g3, -dx, dy, 15.0)
            np.maximum(best, lm, out=best)
        save("ctx_linemax", best)
    names.append("ctx_linemax")
    names.append(save("ctx_crest_s3", ndi.gaussian_filter(crest, 3.0, mode="nearest")))
    names.append(save("ctx_crest_s9", ndi.gaussian_filter(crest, 9.0, mode="nearest")))
    names.append(save("ctx_step_s3", ndi.gaussian_filter(step, 3.0, mode="nearest")))
    names.append(save("ctx_grtp_s9", ndi.gaussian_filter(grtp, 9.0, mode="nearest")))
    # corroboration count: how many of 5 line fields exceed their 90th percentile here
    p = cache / "ch_ctx_corrob.npy"
    if not p.exists():
        fields = [crest, step, grtp,
                  np.load(cache / "ch_grad_grav_s2.npy"),
                  np.load(cache / "ch_sato_det_elev.npy")]
        cnt = np.zeros(fp.shape, np.float32)
        for f in fields:
            cnt += (f >= np.percentile(f[fp], 90.0)).astype(np.float32)
        save("ctx_corrob", cnt)
    names.append("ctx_corrob")
    return names


def train_predict_fold(handles, extra, fp, visible, width, rng,
                       neg_per_pos=8, max_pos=120_000):
    """Previous lane's PU-style protocol (run_supervised.train_predict), plus a
    per-fold in-memory extra channel (RELAY)."""
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
    X = featurestack.gather(handles + [extra], idx, width)
    clf = HistGradientBoostingClassifier(
        max_iter=180, learning_rate=0.08, max_leaf_nodes=31, min_samples_leaf=60,
        l2_regularization=1.0, random_state=SEED, early_stopping=False)
    clf.fit(X, y)
    out = np.zeros(fp.shape, dtype=np.float32)
    all_idx = np.flatnonzero(fp.ravel())
    for chunk in np.array_split(all_idx, 12):
        out.ravel()[chunk] = clf.predict_proba(
            featurestack.gather(handles + [extra], chunk, width))[:, 1].astype(np.float32)
    return out


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    crest = np.load(featurestack.CACHE / "ch_geopb_crest.npy")
    print(f"[{time.time()-t0:6.1f}s] folds withheld={[f.n_withheld for f in folds]}", flush=True)

    res = {"evaluator_version": holdout.EVALUATOR_VERSION,
           "n_withheld_positives": int(sum(f.n_withheld for f in folds)),
           "reference_crest_sep28": {"37654": 0.0695264471015082, "60000": 0.08512630984995147},
           "reference_crest_sep40": {"37654": 0.0747509441972475, "60000": 0.08970713087363252},
           "arms": {}, "canary_auc": {}}

    # ---------------------------------------------------------- E1 RELAY
    print("\nE1: RELAY field per fold (visible only) ...", flush=True)
    relay_pf, gated_pf, crest_pf = {}, {}, {}
    rcrest = rank01(crest, fp)
    for fold in folds:
        cache_p = WORK / f"relay_{fold.name}.npy"
        if cache_p.exists():
            rf = np.load(cache_p)
        else:
            rf = relay.relay_field(fold.visible, fp)
            np.save(cache_p, rf)
        relay_pf[fold.name] = rf
        gated_pf[fold.name] = (rcrest * (0.25 + 0.75 * rank01(rf, fp))).astype(np.float32)
        crest_pf[fold.name] = crest
        print(f"  [{time.time()-t0:6.1f}s] {fold.name} tips={relay.tip_table(fold.visible)}",
              flush=True)

    res["canary_auc"]["relay"] = pooled_auc(relay_pf, folds, fp)
    res["canary_auc"]["relay_gated_crest"] = pooled_auc(gated_pf, folds, fp)
    res["canary_auc"]["geopb_crest_static"] = holdout.feature_auc(crest, folds, fp)
    print(f"CANARY AUC: {res['canary_auc']}  (flag if > 0.90)", flush=True)

    score_arm("E1_relay_alone", relay_pf, folds, fp, res["arms"])
    score_arm("E1_gated_crest", gated_pf, folds, fp, res["arms"])
    score_arm("E1_crest_reference_remeasure", crest_pf, folds, fp, res["arms"])

    # ---------------------------------------------------------- E2 CTXHGB
    print("\nE2: context channels + per-fold HGB ...", flush=True)
    base_names = featurestack.build(fp)
    ctx_names = build_context_channels(fp)
    chan_names = base_names + ctx_names
    print(f"  channels ({len(chan_names)}+relay): {chan_names}", flush=True)
    handles = featurestack.open_stack(chan_names)
    for nm in ctx_names:  # context canaries (static, catalogue-free by construction)
        res["canary_auc"][nm] = holdout.feature_auc(
            np.load(featurestack.CACHE / f"ch_{nm}.npy"), folds, fp)
    print(f"  ctx canaries done [{time.time()-t0:6.1f}s]", flush=True)

    hgb_pf = {}
    rng = np.random.default_rng(SEED)
    for fold in folds:
        cache_p = WORK / f"ctxhgb_{fold.name}.npy"
        if cache_p.exists():
            hgb_pf[fold.name] = np.load(cache_p)
            print(f"  [{time.time()-t0:6.1f}s] {fold.name} cached", flush=True)
            continue
        f = train_predict_fold(handles, relay_pf[fold.name], fp, fold.visible,
                               grid.WIDTH, rng)
        np.save(cache_p, f)
        hgb_pf[fold.name] = f
        ok = fp & ~fold.visible
        yy = fold.withheld[ok]
        sub = np.random.default_rng(1).choice(yy.size, min(600_000, yy.size), replace=False)
        print(f"  [{time.time()-t0:6.1f}s] {fold.name} withheld-AUC "
              f"{roc_auc_score(yy[sub], f[ok][sub]):.4f}", flush=True)
    res["canary_auc"]["ctxhgb_field"] = pooled_auc(hgb_pf, folds, fp)
    score_arm("E2_ctxhgb", hgb_pf, folds, fp, res["arms"])

    # ---------------------------------------------------------- E3 fusion
    print("\nE3: fusion 0.5/0.25/0.25 + emission variants ...", flush=True)
    fus_pf, fus_blur_pf = {}, {}
    for fold in folds:
        fus = (0.5 * rank01(hgb_pf[fold.name], fp) + 0.25 * rcrest
               + 0.25 * rank01(gated_pf[fold.name], fp)).astype(np.float32)
        fus_pf[fold.name] = fus
        fus_blur_pf[fold.name] = coverage_credit(rank01(fus, fp), fp).astype(np.float32)
    res["canary_auc"]["fusion"] = pooled_auc(fus_pf, folds, fp)
    score_arm("E3_fusion_poisson28", fus_pf, folds, fp, res["arms"])
    score_arm("E3_fusion_blurred_poisson28", fus_blur_pf, folds, fp, res["arms"])

    # winning arm re-measured at sep 4.0 @37,654 for the pre-registered gate
    best_name, best_val = None, -1.0
    for k, v in res["arms"].items():
        val = v["37654"]["pooled_holdout_dti"]
        if val > best_val:
            best_name, best_val = k, val
    fields_by_arm = {"E1_relay_alone": relay_pf, "E1_gated_crest": gated_pf,
                     "E1_crest_reference_remeasure": crest_pf, "E2_ctxhgb": hgb_pf,
                     "E3_fusion_poisson28": fus_pf, "E3_fusion_blurred_poisson28": fus_blur_pf}
    print(f"\nbest @37,654 sep2.8: {best_name} = {best_val:.5f}; re-measuring at sep4 ...",
          flush=True)
    tmp = {}
    score_arm(f"{best_name}__sep40", fields_by_arm[best_name], folds, fp, tmp,
              sep=4.0, budgets=(37_654,))
    res["arms"].update(tmp)
    res["best_arm_sep28"] = {"name": best_name, "dti_37654": best_val}
    res["channels"] = chan_names + ["relay(per-fold)"]
    res["runtime_s"] = time.time() - t0
    (ROOT / "evidence" / "session_22847afd_experiments.json").write_text(
        json.dumps(res, indent=2, default=float) + "\n")
    print(f"\n-> evidence/session_22847afd_experiments.json ({time.time()-t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    from preflight import experiment_gate
    blocked = experiment_gate(ROOT)
    if blocked:
        raise SystemExit(blocked)
    raise SystemExit(main())
