#!/usr/bin/env python3
"""Pre-registered 3-experiment campaign for session arena/7ded4c0a-gemsdoe85.

Pre-registration: `research/session-7ded4c0a-hypotheses.md`
Evaluator: `gems85-holdout-v1.0.0` (4 spatially-blocked segment folds, 60,988 withheld px,
alpha=0.2, beta=0.8, 300 m triangular kernel).
Budget cap: strictly 3 experiments (E1 H85-GAPVENT, E2 H85-SUBMOD300 + boundary test,
E3 H85-ORTHOFUSE).
"""

from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi, stats
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import emission, emitter, featurestack, gapvent, grid, holdout  # noqa: E402


def train_predict_ctxhgb30_fast(handles, fp, visible, rng, neg_per_pos=8, max_pos=120_000):
    """Exact same E2b (`CTXHGB-30`) specification, accelerated with stripwise mmap I/O."""
    pos_mask = ndi.binary_dilation(visible, np.ones((3, 3), bool), iterations=1) & fp
    far = ~ndi.binary_dilation(visible, np.ones((3, 3), bool), iterations=10) & fp
    pos_idx = np.flatnonzero(pos_mask.ravel())
    neg_pool = np.flatnonzero(far.ravel())
    if pos_idx.size > max_pos:
        pos_idx = rng.choice(pos_idx, max_pos, replace=False)
    neg_idx = rng.choice(neg_pool, min(neg_pool.size, pos_idx.size * neg_per_pos), replace=False)
    idx = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(pos_idx.size, np.int8), np.zeros(neg_idx.size, np.int8)])
    X = gapvent.gather_stripwise(handles, idx)
    clf = HistGradientBoostingClassifier(
        max_iter=180,
        learning_rate=0.08,
        max_leaf_nodes=31,
        min_samples_leaf=60,
        l2_regularization=1.0,
        random_state=20261022,
        early_stopping=False,
    )
    clf.fit(X, y)
    del X, y
    gc.collect()
    return gapvent.predict_stripwise(handles, fp, lambda Xc: clf.predict_proba(Xc)[:, 1])

WORK = ROOT / "work_session_7ded4c0a"
BUDGETS = (37_654, 60_000)


def rank01(a: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Tie-averaged rank normalization onto [0, 1] inside footprint."""
    v = a[fp].astype(np.float64)
    rk = (stats.rankdata(v, method="average") - 1.0) / max(1, v.size - 1)
    out = np.zeros(a.shape, np.float32)
    out[fp] = rk.astype(np.float32)
    return out


def pooled_oof_auc(per_fold: dict[str, np.ndarray], folds, fp: np.ndarray, seed: int = 7) -> float:
    pos_all, neg_all = [], []
    rng = np.random.default_rng(seed)
    for fold in folds:
        f = per_fold[fold.name]
        ok = fp & ~fold.visible & np.isfinite(f)
        pos_all.append(f[ok & fold.withheld])
        neg = f[ok & ~fold.withheld]
        if neg.size > 400_000:
            neg = rng.choice(neg, 400_000, replace=False)
        neg_all.append(neg)
    y = np.concatenate([np.ones(sum(p.size for p in pos_all)), np.zeros(sum(n.size for n in neg_all))])
    s = np.concatenate(pos_all + neg_all)
    return float(roc_auc_score(y, s))


def calibrate_sharp_prob(surface: np.ndarray, fp: np.ndarray, gamma: float) -> np.ndarray:
    """Map continuous kernel regression predictions to sharpened [0, 1] probabilities for submodular emit."""
    vals = surface[fp][::10]
    hi = max(float(np.percentile(vals, 99.95)), 1e-6)
    p = np.clip(surface / hi, 0.0, 1.0) ** gamma
    p[~fp] = 0.0
    return p.astype(np.float32)


def eval_poisson_arm(
    arm_name: str,
    per_fold: dict[str, np.ndarray],
    folds,
    fp: np.ndarray,
    results: dict,
    *,
    sep_px: float,
    exclude_px: int = 2,
    budgets=BUDGETS,
) -> None:
    results[arm_name] = {}
    for n in budgets:
        r = holdout.score_folds(
            lambda fold, n=n: emission.emit(
                per_fold[fold.name],
                footprint=fp,
                visible_catalogue=fold.visible,
                n=n,
                sep_px=sep_px,
                exclude_px=exclude_px,
            ),
            folds,
            domain=fp,
        )
        results[arm_name][str(n)] = r.as_dict()
        print(
            f"  {arm_name:34s} n={n:6d} sep={sep_px:.1f} exc={exclude_px} "
            f"HOLDOUT-DTI={r.pooled_dti:.5f} CI95[{r.ci95[0]:.5f},{r.ci95[1]:.5f}] "
            f"folds={[round(x.dti, 4) for x in r.folds]}",
            flush=True,
        )


def submod_emit_masked(
    surface: np.ndarray,
    fp: np.ndarray,
    visible: np.ndarray,
    *,
    n: int,
    gamma: float,
    exclude_px: int = 2,
    max_support: int = 120_000,
) -> np.ndarray:
    """Mask visible catalogue within `exclude_px`, calibrate/sharpen onto [0,1], confine to top support, and run lazy-greedy 300m submodular coverage."""
    elig = fp.copy()
    if exclude_px > 0 and np.any(visible):
        d_vis = ndi.distance_transform_edt(~visible)
        elig &= d_vis > exclude_px
    vals = surface[elig]
    if vals.size == 0:
        return np.zeros(fp.shape, dtype=np.float32)
    hi = max(float(np.percentile(vals[::8], 99.95)), 1e-6)
    p = np.zeros(fp.shape, dtype=np.float32)
    p[elig] = (np.clip(vals / hi, 0.0, 1.0) ** gamma).astype(np.float32)
    if vals.size > max_support:
        thr = float(np.partition(p[elig], vals.size - max_support)[vals.size - max_support])
        p[p < max(thr, 1e-7)] = 0.0
    mask, _ = emitter.emit(p, budget=n, prior_dti=0.0)
    return mask.astype(np.float32)


def eval_submod_arm(
    arm_name: str,
    per_fold: dict[str, np.ndarray],
    folds,
    fp: np.ndarray,
    results: dict,
    *,
    gamma: float,
    exclude_px: int = 2,
    budgets=(37_654,),
) -> None:
    results[arm_name] = {}
    for n in budgets:
        r = holdout.score_folds(
            lambda fold, n=n: submod_emit_masked(
                per_fold[fold.name],
                fp,
                fold.visible,
                n=n,
                gamma=gamma,
                exclude_px=exclude_px,
            ),
            folds,
            domain=fp,
        )
        results[arm_name][str(n)] = r.as_dict()
        print(
            f"  {arm_name:34s} n={n:6d} gamma={gamma:.1f} exc={exclude_px} "
            f"HOLDOUT-DTI={r.pooled_dti:.5f} CI95[{r.ci95[0]:.5f},{r.ci95[1]:.5f}] "
            f"folds={[round(x.dti, 4) for x in r.folds]}",
            flush=True,
        )


def main() -> int:
    t0 = time.time()
    WORK.mkdir(parents=True, exist_ok=True)
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)

    names57, handles57 = gapvent.build_all(fp)
    print(f"[{time.time()-t0:6.1f}s] Loaded {len(names57)} channels; withheld={[f.n_withheld for f in folds]}", flush=True)

    summary: dict = {
        "session_branch": "arena/7ded4c0a-gemsdoe85",
        "evaluator_version": holdout.EVALUATOR_VERSION,
        "n_withheld_positives": int(sum(f.n_withheld for f in folds)),
        "pre_registration": "research/session-7ded4c0a-hypotheses.md",
        "prior_records_37654": {
            "geopb_crest_sep40": 0.0747509441972475,
            "ctxhgb30_sep28": 0.08046432973219529,
            "ctxfus50_sep28": 0.08081805013412194,
        },
        "oof_auc": {},
        "arms": {},
    }

    out_path = ROOT / "evidence" / "session_7ded4c0a_experiments.json"
    if out_path.exists():
        saved = json.loads(out_path.read_text())
        summary["arms"].update(saved.get("arms", {}))
        summary["oof_auc"].update(saved.get("oof_auc", {}))

    def _ckpt() -> None:
        out_path.write_text(json.dumps(summary, indent=2) + "\n")

    # =========================================================================
    # EXPERIMENT 1: H85-GAPVENT + H85-VOLCDECONF (57-ch continuous kernel regressor)
    # =========================================================================
    print("\n=== E1: H85-GAPVENT 57-channel continuous 300m kernel-target regressor ===", flush=True)
    gv_pf: dict[str, np.ndarray] = {}
    for i, fold in enumerate(folds):
        cp = WORK / f"gapvent57_{fold.name}.npy"
        if cp.exists():
            gv_pf[fold.name] = np.load(cp)
            print(f"  [{time.time()-t0:6.1f}s] {fold.name} loaded from cache", flush=True)
        else:
            f = gapvent.train_predict_gapvent(
                handles57, fp, fold.visible, names=names57, seed=20261023 + 100 * i
            )
            np.save(cp, f)
            gv_pf[fold.name] = f
            gc.collect()
        ok = fp & ~fold.visible
        yy = fold.withheld[ok]
        sub = np.random.default_rng(1).choice(yy.size, min(600_000, yy.size), replace=False)
        fauc = float(roc_auc_score(yy[sub], gv_pf[fold.name][ok][sub]))
        print(f"  [{time.time()-t0:6.1f}s] {fold.name} withheld ROC-AUC = {fauc:.4f}", flush=True)

    summary["oof_auc"]["E1_gapvent57"] = pooled_oof_auc(gv_pf, folds, fp)
    print(f"  Pooled OOF ROC-AUC (E1_gapvent57): {summary['oof_auc']['E1_gapvent57']:.4f}", flush=True)

    if "E1_gapvent57_sep28_exc2" not in summary["arms"]:
        eval_poisson_arm("E1_gapvent57_sep28_exc2", gv_pf, folds, fp, summary["arms"], sep_px=2.8, exclude_px=2)
        _ckpt()
    if "E1_gapvent57_sep40_exc2" not in summary["arms"]:
        eval_poisson_arm("E1_gapvent57_sep40_exc2", gv_pf, folds, fp, summary["arms"], sep_px=4.0, exclude_px=2)
        _ckpt()

    # =========================================================================
    # EXPERIMENT 2: H85-SUBMOD300 (calibrated submodular marginal coverage + exclude_px=3 test)
    # =========================================================================
    print("\n=== E2: H85-SUBMOD300 calibrated 300m submodular allocator + boundary exclude_px=3 ===", flush=True)
    if "E2_submod300_g15_exc2" not in summary["arms"]:
        eval_submod_arm("E2_submod300_g15_exc2", gv_pf, folds, fp, summary["arms"], gamma=1.5, exclude_px=2, budgets=(37_654,))
        _ckpt()
    if "E2_submod300_g25_exc2" not in summary["arms"]:
        eval_submod_arm("E2_submod300_g25_exc2", gv_pf, folds, fp, summary["arms"], gamma=2.5, exclude_px=2, budgets=(37_654,))
        _ckpt()
    if "E2_submod300_g20_exc3" not in summary["arms"]:
        eval_submod_arm("E2_submod300_g20_exc3", gv_pf, folds, fp, summary["arms"], gamma=2.0, exclude_px=3, budgets=(37_654,))
        _ckpt()
    if "E2_poisson_sep28_exc3" not in summary["arms"]:
        eval_poisson_arm("E2_poisson_sep28_exc3", gv_pf, folds, fp, summary["arms"], sep_px=2.8, exclude_px=3, budgets=BUDGETS)
        _ckpt()
    if "E2_poisson_sep34_exc2" not in summary["arms"]:
        eval_poisson_arm("E2_poisson_sep34_exc2", gv_pf, folds, fp, summary["arms"], sep_px=3.4, exclude_px=2, budgets=BUDGETS)
        _ckpt()

    # =========================================================================
    # EXPERIMENT 3: H85-ORTHOFUSE (H85-GAPVENT + unsupervised GEO-Pb crest + CTXHGB-30)
    # =========================================================================
    print("\n=== E3: H85-ORTHOFUSE cross-mechanism ensemble ===", flush=True)
    base_ctx_names = names57[:30]  # 24 base + 6 context channels
    base_ctx_handles = handles57[:30]
    ctx_pf: dict[str, np.ndarray] = {}
    rng_ctx = np.random.default_rng(20261022)
    for fold in folds:
        cp = WORK / f"ctxhgb30_{fold.name}.npy"
        if cp.exists():
            ctx_pf[fold.name] = np.load(cp)
        else:
            f = train_predict_ctxhgb30_fast(base_ctx_handles, fp, fold.visible, rng_ctx)
            np.save(cp, f)
            ctx_pf[fold.name] = f
            gc.collect()
    summary["oof_auc"]["B1_ctxhgb30"] = pooled_oof_auc(ctx_pf, folds, fp)

    crest = np.asarray(np.load(featurestack.CACHE / "ch_geopb_crest.npy", mmap_mode="r"), dtype=np.float32)
    r_crest = rank01(crest, fp)

    orthofuse_pf: dict[str, np.ndarray] = {}
    orthoprob_pf: dict[str, np.ndarray] = {}
    orthofuse90_pf: dict[str, np.ndarray] = {}
    for fold in folds:
        r_gv = rank01(gv_pf[fold.name], fp)
        r_ctx = rank01(ctx_pf[fold.name], fp)
        # Rank-calibrated cross-mechanism blend (0.65 GAPVENT-57 + 0.20 CTXHGB-30 + 0.15 unsupervised GEO-Pb crest)
        orthofuse_pf[fold.name] = (0.65 * r_gv + 0.20 * r_ctx + 0.15 * r_crest).astype(np.float32)
        # High-purity GAPVENT + light unsupervised GEO-Pb crest tie-breaker (0.92 / 0.08)
        orthofuse90_pf[fold.name] = (0.92 * r_gv + 0.08 * r_crest).astype(np.float32)
        # Probability-space blend for submodular marginal coverage
        c_max = max(float(np.percentile(crest[fp][::10], 99.9)), 1e-6)
        c_prob = np.clip(crest / c_max, 0.0, 1.0)
        orthoprob_pf[fold.name] = (
            0.65 * calibrate_sharp_prob(gv_pf[fold.name], fp, 1.0)
            + 0.20 * np.clip(ctx_pf[fold.name], 0.0, 1.0)
            + 0.15 * c_prob
        ).astype(np.float32)

    summary["oof_auc"]["E3_orthofuse_rank"] = pooled_oof_auc(orthofuse_pf, folds, fp)
    summary["oof_auc"]["E3_orthofuse92_rank"] = pooled_oof_auc(orthofuse90_pf, folds, fp)
    summary["oof_auc"]["E3_orthofuse_prob"] = pooled_oof_auc(orthoprob_pf, folds, fp)
    print(
        f"  Pooled OOF ROC-AUC (E3_orthofuse_rank={summary['oof_auc']['E3_orthofuse_rank']:.4f}, "
        f"E3_orthofuse92_rank={summary['oof_auc']['E3_orthofuse92_rank']:.4f})",
        flush=True,
    )

    if "E3_orthofuse_sep28_exc2" not in summary["arms"]:
        eval_poisson_arm("E3_orthofuse_sep28_exc2", orthofuse_pf, folds, fp, summary["arms"], sep_px=2.8, exclude_px=2)
        _ckpt()
    if "E3_orthofuse92_sep28_exc3" not in summary["arms"]:
        eval_poisson_arm("E3_orthofuse92_sep28_exc3", orthofuse90_pf, folds, fp, summary["arms"], sep_px=2.8, exclude_px=3)
        _ckpt()
    if "E3_orthofuse_submod_g18_exc2" not in summary["arms"]:
        eval_submod_arm("E3_orthofuse_submod_g18_exc2", orthoprob_pf, folds, fp, summary["arms"], gamma=1.8, exclude_px=2, budgets=(37_654,))
        _ckpt()

    # Pick overall winner at N = 37,654
    best_arm, best_dti = None, -1.0
    for arm, d in summary["arms"].items():
        if "37654" in d and d["37654"]["pooled_holdout_dti"] > best_dti:
            best_arm = arm
            best_dti = d["37654"]["pooled_holdout_dti"]

    summary["winner_37654"] = {
        "arm": best_arm,
        "pooled_holdout_dti": best_dti,
        "beats_prior_record_008082": bool(best_dti > 0.08081805013412194),
        "delta_vs_ctxfus50": float(best_dti - 0.08081805013412194),
        "delta_vs_geopb_crest": float(best_dti - 0.0747509441972475),
    }
    summary["runtime_seconds"] = round(time.time() - t0, 2)

    out_path = ROOT / "evidence" / "session_7ded4c0a_experiments.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nWINNER @ 37,654: {best_arm} -> HOLDOUT-DTI = {best_dti:.5f} "
          f"(delta vs 0.08082 = {best_dti - 0.08081805:+.5f}) in {summary['runtime_seconds']:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
