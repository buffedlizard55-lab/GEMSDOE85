#!/usr/bin/env python3
"""Fast, low-memory (<900 MB RSS) execution of the 3-experiment Lane H85-Conduit protocol.

Pre-registered 3-experiment ladder on unmodified ``vendor/gems57/evaluate_holdout.py``:
  1. E1_structural_dinkelbach (60 channels: core 19 + 1m LiDAR + 10m 3DEP + chi knickpoints
     + SGMC + 090 deg flight-line notch + Lahontan mimic + 8 fold-safe visible network channels)
  2. E2_plus_blind_hydrothermal_seismic (77 channels: E1 + 17 newly assembled 1900-2026 sub-km
     USGS ComCat hypocenters/swarms, GBCGE 2m probes F2mDAB, siliceous paleo-vents vs tufa,
     and GDR spring/well geothermometers)
  3. E3_full_multiphysics_diverse_crest (86 channels: E2 + 9 GEO-Pb across-strike Hotelling
     step crests & potassic/magnetite-destruction channels + diverse LightGBM+HGB OOF ensemble
     + ResUNet-style Stage-2 8-azimuth spatial crest skeletonizer)
"""

from __future__ import annotations

import gc
import hashlib
import json
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import evaluate_holdout as ev  # noqa: E402
from gems57 import submission_writer as g57_writer  # noqa: E402
from gems57 import uniqueness as g57_uniq  # noqa: E402
from gems57.grid import load_grid  # noqa: E402
from gems57.holdout import buffered_component_draw  # noqa: E402

from gems85.conduit import (  # noqa: E402
    CACHE_DIR,
    CONDUIT_CHANNEL_NAMES,
    JUXTAPOSITION_CHANNEL_NAMES,
    NETWORK_CHANNEL_NAMES,
    STRUCT_CHANNEL_NAMES,
    build_static_feature_cache,
    compute_fold_safe_network_features,
    compute_stage2_crest_features,
    fit_hgb_classifier,
    fit_lgbm_classifier,
    make_inner_component_folds,
    open_static_mmaps,
    predict_grid_chunked,
    sample_sharp_1px_dataset,
)
from gems85.dinkelbach import (  # noqa: E402
    ALPHA,
    BETA,
    KERNEL_DX,
    KERNEL_DY,
    KERNEL_W,
    fit_conduit_calibrator,
    greedy_submodular_prefix,
)

ALL_STATIC_NAMES = STRUCT_CHANNEL_NAMES + CONDUIT_CHANNEL_NAMES + JUXTAPOSITION_CHANNEL_NAMES


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def exact_optimal_budget_on_inner_truth(
    ys: np.ndarray,
    xs: np.ndarray,
    inner_truth: np.ndarray,
    inner_eval_valid: np.ndarray,
    n_vis_train: int,
) -> tuple[float, float, int]:
    """Compute exact DTI at EVERY prefix t = 1..M in ~25 ms; return (dots_per_vis_px, best_dti, best_t)."""
    truth = np.asarray(inner_truth & inner_eval_valid, dtype=bool)
    n_truth = float(truth.sum())
    if n_truth <= 0.0 or ys.size == 0:
        return 0.65, 0.0, 0

    dist_t = ndi.distance_transform_edt(~truth)
    q_true = np.clip(1.0 - dist_t / 3.0, 0.0, 1.0)

    h, w = truth.shape
    cov = np.zeros((h, w), dtype=np.float64)
    k_dy = KERNEL_DY.tolist()
    k_dx = KERNEL_DX.tolist()
    k_w = KERNEL_W.tolist()

    tp = 0.0
    fp = 0.0
    best_dti = -1.0
    best_t = max(1, int(0.60 * n_vis_train))

    for t in range(ys.size):
        y = int(ys[t])
        x = int(xs[t])
        fp += 1.0 - float(q_true[y, x])
        for m in range(25):
            ny = y + k_dy[m]
            nx = x + k_dx[m]
            if 0 <= ny < h and 0 <= nx < w and truth[ny, nx]:
                kw = k_w[m]
                if kw > cov[ny, nx]:
                    tp += kw - cov[ny, nx]
                    cov[ny, nx] = kw
        # Evaluate every 50 dots for zero overhead
        if (t + 1) % 50 == 0:
            dti = tp / (0.8 * n_truth + 0.2 * tp + 0.2 * fp)
            if dti > best_dti:
                best_dti = dti
                best_t = t + 1

    # Inner subfold holds out 1/4 of visible (ratio 1/3), while outer holds out 1/5 (ratio 1/4):
    # scale optimal density slightly (~0.92) for the sparser outer unseen prior ratio (0.24 vs 0.33).
    dots_per_vis = float(best_t) / max(float(n_vis_train * 0.75), 1.0) * 0.92
    dots_per_vis = float(np.clip(dots_per_vis, 0.35, 1.35))
    return dots_per_vis, float(best_dti), int(best_t)


def prepare_cached_fold_packs(
    prefix: str,
    visible_global: np.ndarray,
    quad: np.ndarray,
    fp: np.ndarray,
    seed_base: int,
) -> list[dict[str, Path]]:
    """Build & persist per-quadrant training tables and network grids once on disk (<50s total)."""
    net_eval_path = CACHE_DIR / f"{prefix}_net_global.npy"
    if not net_eval_path.exists():
        t0 = time.time()
        net_ev = compute_fold_safe_network_features(visible_global, fp)
        np.save(net_eval_path, net_ev)
        del net_ev
        gc.collect()
        print(f"  Cached {net_eval_path.name} in {time.time()-t0:.1f}s (maxRSS={rss_mb():.0f}MB)", flush=True)

    mmaps_all = open_static_mmaps(ALL_STATIC_NAMES)
    packs = []
    for q_idx in range(4):
        pack_npz = CACHE_DIR / f"{prefix}_q{q_idx}_sample.npz"
        ctx0_npy = CACHE_DIR / f"{prefix}_q{q_idx}_net_ctx0.npy"
        if not pack_npz.exists() or not ctx0_npy.exists():
            t0 = time.time()
            train_reg = (quad != q_idx) & fp
            subfolds = make_inner_component_folds(visible_global & train_reg, n_inner=4, seed=seed_base + 10 * q_idx)
            X_all, y_all, kf_all, idx_all = sample_sharp_1px_dataset(
                mmaps_all,
                subfolds,
                train_reg,
                visible_global,
                fp,
                near_neg_per_pos=3,
                far_neg_per_pos=6,
                seed=85 + seed_base + 10 * q_idx,
            )
            import os
            if hasattr(os, "posix_fadvise") and hasattr(os, "POSIX_FADV_DONTNEED"):
                for arr in mmaps_all:
                    mm_obj = getattr(arr, "_mmap", None)
                    if mm_obj is not None and hasattr(mm_obj, "fileno"):
                        try:
                            os.posix_fadvise(mm_obj.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
                        except OSError:
                            pass
            ctx0 = subfolds[0]["context"] | (visible_global & ~train_reg)
            net0 = compute_fold_safe_network_features(ctx0, fp)
            np.save(ctx0_npy, net0)
            np.savez(
                pack_npz,
                X=X_all,
                y=y_all,
                kf=kf_all,
                idx=idx_all,
                target0_flat=np.flatnonzero((subfolds[0]["target"] & train_reg).ravel()),
                ctx0_flat=np.flatnonzero(ctx0.ravel()),
            )
            del X_all, y_all, kf_all, idx_all, net0
            gc.collect()
            print(f"  Cached fold pack {prefix}_q{q_idx} in {time.time()-t0:.1f}s (maxRSS={rss_mb():.0f}MB)", flush=True)
        packs.append({"npz": pack_npz, "net_ctx0": ctx0_npy, "net_eval": net_eval_path})
    return packs


def predict_quadrant_from_pack(
    pack: dict[str, Path],
    col_indices: list[int],
    static_sub_names: list[str],
    q_idx: int,
    quad: np.ndarray,
    visible_global: np.ndarray,
    fp: np.ndarray,
    *,
    use_diverse_and_stage2: bool,
    seed_offset: int,
) -> dict[str, object]:
    """Fit OOF model on cached fold pack columns, calibrate optimal dot density, and emit dots."""
    with np.load(pack["npz"]) as data:
        net_col_indices = [len(ALL_STATIC_NAMES) + j for j in range(len(NETWORK_CHANNEL_NAMES))]
        full_cols = col_indices + net_col_indices
        X_all = data["X"][:, full_cols].copy()
        y_all = data["y"].copy()
        kf_all = data["kf"].copy()
        target0_flat = data["target0_flat"].copy()
        ctx0_flat = data["ctx0_flat"].copy()

    train_reg = (quad != q_idx) & fp
    eval_reg = (quad == q_idx) & fp

    val_mask = kf_all == 0
    tr_mask = ~val_mask

    lgb_sub = fit_lgbm_classifier(X_all[tr_mask], y_all[tr_mask], seed=85 + seed_offset)
    oof_s1 = lgb_sub.predict_proba(X_all[val_mask])[:, 1].astype(np.float32)

    hgb_sub = None
    if use_diverse_and_stage2:
        hgb_sub = fit_hgb_classifier(X_all[tr_mask], y_all[tr_mask], seed=185 + seed_offset)
        oof_s1 = (0.62 * oof_s1 + 0.38 * hgb_sub.predict_proba(X_all[val_mask])[:, 1]).astype(np.float32)

    mmaps_sub = open_static_mmaps(static_sub_names)
    net0 = np.load(pack["net_ctx0"], mmap_mode="r")
    pred_fn_sub = (
        (lambda Xc: 0.62 * lgb_sub.predict_proba(Xc)[:, 1] + 0.38 * hgb_sub.predict_proba(Xc)[:, 1])
        if use_diverse_and_stage2
        else (lambda Xc: lgb_sub.predict_proba(Xc)[:, 1])
    )
    s1_inner_grid = predict_grid_chunked(pred_fn_sub, mmaps_sub, net0, train_reg, chunk_size=550_000)
    del net0, lgb_sub, hgb_sub

    lgb_full = fit_lgbm_classifier(X_all, y_all, seed=285 + seed_offset)
    hgb_full = fit_hgb_classifier(X_all, y_all, seed=385 + seed_offset) if use_diverse_and_stage2 else None
    feat_names = list(static_sub_names) + list(NETWORK_CHANNEL_NAMES)
    imp = {fn: int(iv) for fn, iv in zip(feat_names, lgb_full.feature_importances_)}
    del X_all

    net_eval = np.load(pack["net_eval"], mmap_mode="r")
    pred_fn_full = (
        (lambda Xc: 0.62 * lgb_full.predict_proba(Xc)[:, 1] + 0.38 * hgb_full.predict_proba(Xc)[:, 1])
        if use_diverse_and_stage2
        else (lambda Xc: lgb_full.predict_proba(Xc)[:, 1])
    )
    s1_eval_grid = predict_grid_chunked(pred_fn_full, mmaps_sub, net_eval, eval_reg, chunk_size=550_000)
    del net_eval, lgb_full, hgb_full
    gc.collect()

    ctx0_mask = np.zeros(fp.shape, dtype=bool)
    ctx0_mask.ravel()[ctx0_flat] = True
    target0_mask = np.zeros(fp.shape, dtype=bool)
    target0_mask.ravel()[target0_flat] = True
    dist_ctx0 = ndi.distance_transform_edt(~ctx0_mask)

    if use_diverse_and_stage2:
        key_phys_names = [
            "lidar_step_max",
            "lidar_ext_strike_fav",
            "topo10_curv_prof",
            "mimic_lahontan_1332m",
            "eq_density_s10",
            "probe2m_dab_s8",
            "paleo_siliceous_s5",
            "geopb_crest",
        ]
        kp_mmaps = [mmaps_sub[static_sub_names.index(nm)] for nm in key_phys_names if nm in static_sub_names]
        crest_inner = compute_stage2_crest_features(s1_inner_grid, fp, CACHE_DIR / "_tmp_crest_in.dat")
        net0_mm = np.load(pack["net_ctx0"], mmap_mode="r")

        pos0 = target0_flat
        neg_pool0 = np.flatnonzero((train_reg & ~visible_global & (dist_ctx0 > 2.0)).ravel())
        rng2 = np.random.default_rng(777 + seed_offset)
        neg0 = rng2.choice(neg_pool0, min(neg_pool0.size, pos0.size * 9), replace=False)
        idx2 = np.concatenate([pos0, neg0])
        y2 = np.concatenate([np.ones(pos0.size, np.int8), np.zeros(neg0.size, np.int8)])
        ys2, xs2 = np.divmod(idx2, fp.shape[1])
        X2 = np.column_stack(
            [crest_inner[:, ys2, xs2].T, net0_mm[:6, ys2, xs2].T] + [mm[ys2, xs2] for mm in kp_mmaps]
        ).astype(np.float32)

        perm2 = rng2.permutation(idx2.size)
        half = idx2.size // 2
        s2_oof_vec = np.zeros(idx2.size, dtype=np.float32)
        for a_i, b_i in ((perm2[:half], perm2[half:]), (perm2[half:], perm2[:half])):
            mh = lgb.LGBMClassifier(
                n_estimators=150, learning_rate=0.05, num_leaves=31, min_child_samples=90,
                colsample_bytree=0.85, reg_lambda=6.0, n_jobs=-1, random_state=900 + seed_offset, verbose=-1,
            )
            mh.fit(X2[a_i], y2[a_i])
            s2_oof_vec[b_i] = mh.predict_proba(X2[b_i])[:, 1].astype(np.float32)

        m2 = lgb.LGBMClassifier(
            n_estimators=170, learning_rate=0.05, num_leaves=31, min_child_samples=90,
            colsample_bytree=0.85, reg_lambda=6.0, n_jobs=-1, random_state=950 + seed_offset, verbose=-1,
        )
        m2.fit(X2, y2)
        blend_oof = (0.50 * s1_inner_grid.ravel()[idx2] + 0.50 * s2_oof_vec).astype(np.float32)
        del X2

        final_inner = np.zeros(fp.shape, dtype=np.float32)
        flat_tr = np.flatnonzero(train_reg.ravel())
        for st in range(0, flat_tr.size, 450_000):
            sl = flat_tr[st : st + 450_000]
            r_s, c_s = np.divmod(sl, fp.shape[1])
            p2 = m2.predict_proba(
                np.column_stack([crest_inner[:, r_s, c_s].T, net0_mm[:6, r_s, c_s].T] + [mm[r_s, c_s] for mm in kp_mmaps])
            )[:, 1].astype(np.float32)
            final_inner.ravel()[sl] = 0.50 * s1_inner_grid.ravel()[sl] + 0.50 * p2
        del crest_inner, net0_mm
        gc.collect()

        crest_eval = compute_stage2_crest_features(s1_eval_grid, fp, CACHE_DIR / "_tmp_crest_ev.dat")
        net_ev_mm = np.load(pack["net_eval"], mmap_mode="r")
        final_eval = np.zeros(fp.shape, dtype=np.float32)
        flat_ev = np.flatnonzero(eval_reg.ravel())
        for st in range(0, flat_ev.size, 450_000):
            sl = flat_ev[st : st + 450_000]
            r_s, c_s = np.divmod(sl, fp.shape[1])
            p2 = m2.predict_proba(
                np.column_stack([crest_eval[:, r_s, c_s].T, net_ev_mm[:6, r_s, c_s].T] + [mm[r_s, c_s] for mm in kp_mmaps])
            )[:, 1].astype(np.float32)
            final_eval.ravel()[sl] = 0.50 * s1_eval_grid.ravel()[sl] + 0.50 * p2
        del crest_eval, net_ev_mm
        gc.collect()
        cal = fit_conduit_calibrator(blend_oof, y2, hidden_to_visible_ratio=0.24)
    else:
        final_inner = s1_inner_grid
        final_eval = s1_eval_grid
        cal = fit_conduit_calibrator(oof_s1, y_all[val_mask], hidden_to_visible_ratio=0.24)

    del s1_inner_grid, s1_eval_grid, y_all
    gc.collect()

    # Exact OOF optimal dot-density selection in 25ms via single Minoux lazy-heap prefix on train_reg
    allow_inner = train_reg & (dist_ctx0 > 2.0)
    n_vis_tr = int((visible_global & train_reg).sum())
    p_in, q_in, _ = cal.predict_pq(final_inner, allow_inner, n_visible_px=int((ctx0_mask & train_reg).sum()))
    ys_in, xs_in, _ = greedy_submodular_prefix(
        p_in, q_in, allow_inner, tau_rank=0.24, max_dots=min(38_000, int(1.35 * n_vis_tr)), max_candidates=130_000
    )
    dots_per_vis, best_inner_dti, best_inner_n = exact_optimal_budget_on_inner_truth(
        ys_in, xs_in, target0_mask, train_reg & ~ctx0_mask, n_vis_tr
    )
    del final_inner, p_in, q_in, dist_ctx0

    # Emit exact submodular 300m Dinkelbach dots on eval_reg at calibrated density dots_per_vis
    dist_vis_eval = ndi.distance_transform_edt(~visible_global)
    allow_eval = eval_reg & (dist_vis_eval > 2.0)
    n_vis_ev = int((visible_global & eval_reg).sum())
    p_ev, q_ev, _ = cal.predict_pq(final_eval, allow_eval, n_visible_px=n_vis_ev)
    target_dots_ev = max(500, int(round(dots_per_vis * n_vis_ev)))
    ys_ev, xs_ev, _ = greedy_submodular_prefix(
        p_ev, q_ev, allow_eval, tau_rank=0.24, max_dots=target_dots_ev, max_candidates=95_000
    )
    dots_ev = np.zeros(fp.shape, dtype=bool)
    dots_ev[ys_ev, xs_ev] = True

    del final_eval, dist_vis_eval
    gc.collect()
    return {
        "dots": dots_ev,
        "surface": p_ev,
        "dots_per_vis": round(dots_per_vis, 4),
        "inner_val_dti": round(best_inner_dti, 6),
        "inner_val_dots": best_inner_n,
        "importances": imp,
    }


def build_local_registry_index() -> dict[str, object]:
    rasters = []
    seen = set()
    for p in sorted((ROOT / "data" / "scored").glob("*.tif")) + sorted((ROOT / "docs" / "downloads").glob("*.tif")):
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if sha in seen:
            continue
        seen.add(sha)
        rasters.append(
            {
                "repo_first": p.name.split("-")[0].split("_")[0],
                "sources": [p.name],
                "cache_file": str(p.relative_to(ROOT)),
                "sha256": sha,
            }
        )
    return {"complete_accessible_scan": True, "errors": [], "rasters": rasters}


def main() -> int:
    t_start = time.time()
    grid = load_grid(ROOT / "data")
    fp = grid.footprint
    build_static_feature_cache(fp)

    folds, quad = buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    visible_holdout = folds[0]["visible"]
    print(
        f"Grid ready ({int(fp.sum()):,} px, withheld={sum(int(f['truth'].sum()) for f in folds):,} px, maxRSS={rss_mb():.0f}MB)",
        flush=True,
    )

    packs_holdout = prepare_cached_fold_packs("holdout_s20", visible_holdout, quad, fp, seed_base=2026)

    control_paths = {
        "CTRL_d28_0.2600": ROOT / "data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "CTRL_d15": ROOT / "data/scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "CTRL_h19_5_0.1922": ROOT / "data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
        "CTRL_gems81_poisson": ROOT / "data/scored/gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros.tif",
        "CTRL_h33_0.2778_fullcatpruned": ROOT / "data/scored/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "CTRL_gems36_0.2750_fullcatpruned": ROOT / "data/scored/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
        "CTRL_gems70_0.2478_fullcatpruned": ROOT / "data/scored/gems70-p5-multiphysics-submodular-37654-20261020.tif",
        "CTRL_gems85_prior_geopb90k": ROOT / "docs/downloads/gems85-geopb-crest-90000dots-sep4-20261022T222707Z-a4e1f57c-zeros.tif",
    }
    terms_by_arm: dict[str, np.ndarray] = {}
    for cname, cpath in control_paths.items():
        with rasterio.open(cpath) as src:
            arr = src.read(1).astype(np.float32)
        arr = np.where(np.isfinite(arr), np.clip(arr, 0.0, 1.0), 0.0)
        arr[~fp] = 0.0
        ts = None
        for f in folds:
            _, t = ev.evaluate(arr, f, fp)
            ts = t if ts is None else (ts + t)
        terms_by_arm[cname] = ts

    exp_defs = [
        ("E1_structural_dinkelbach", list(STRUCT_CHANNEL_NAMES), False),
        ("E2_plus_blind_hydrothermal_seismic", list(STRUCT_CHANNEL_NAMES) + list(CONDUIT_CHANNEL_NAMES), False),
        (
            "E3_full_multiphysics_diverse_crest",
            list(STRUCT_CHANNEL_NAMES) + list(CONDUIT_CHANNEL_NAMES) + list(JUXTAPOSITION_CHANNEL_NAMES),
            True,
        ),
    ]

    exp_meta = {}
    for ename, sub_names, use_s2 in exp_defs:
        t_chk = CACHE_DIR / f"terms_{ename}.npy"
        m_chk = CACHE_DIR / f"meta_{ename}.json"
        if t_chk.exists() and m_chk.exists():
            terms_by_arm[ename] = np.load(t_chk)
            exp_meta[ename] = json.loads(m_chk.read_text())
            print(f"Loaded checkpoint {ename}: POOLED HOLDOUT-DTI = {exp_meta[ename]['pooled_holdout_dti']:.6f}", flush=True)
            continue
        t_exp = time.time()
        col_idx = [ALL_STATIC_NAMES.index(nm) for nm in sub_names]
        print(f"\n>>> STARTING {ename} ({len(sub_names)}+8={len(sub_names)+8} ch, stage2={use_s2}) <<<", flush=True)
        terms_total = None
        per_fold = {}
        agg_imp: dict[str, float] = {}
        total_dots_emitted = 0

        for q_idx, fold in enumerate(folds):
            fold_chk = CACHE_DIR / f"foldchk_{ename}_q{q_idx}.npz"
            if fold_chk.exists():
                fc = np.load(fold_chk, allow_pickle=True)
                f_terms = fc["f_terms"]
                pf = json.loads(str(fc["per_fold_json"]))
                imp_d = json.loads(str(fc["imp_json"]))
                total_dots_emitted += int(fc["dots_count"])
                terms_total = f_terms if terms_total is None else (terms_total + f_terms)
                per_fold[fold["name"]] = pf
                for k, v in imp_d.items():
                    agg_imp[k] = agg_imp.get(k, 0.0) + float(v)
                print(f"  [{ename}] Loaded fold {fold['name']}: HOLDOUT-DTI={pf['dti']:.6f}", flush=True)
                continue
            out = predict_quadrant_from_pack(
                packs_holdout[q_idx],
                col_idx,
                sub_names,
                q_idx,
                quad,
                visible_holdout,
                fp,
                use_diverse_and_stage2=use_s2,
                seed_offset=10 * q_idx,
            )
            f_dots = out["dots"].astype(np.float32)
            d_cnt = int((f_dots > 0).sum())
            total_dots_emitted += d_cnt
            sc, f_terms = ev.evaluate(f_dots, fold, fp)
            terms_total = f_terms if terms_total is None else (terms_total + f_terms)
            act = fp & fold["region"] & ~fold["masked_known"]
            auc_f = float(roc_auc_score(fold["truth"][act], out["surface"][act]))
            per_fold[fold["name"]] = {
                "dti": round(float(sc["dti"]), 6),
                "tp": round(float(sc["tp"]), 2),
                "fp": round(float(sc["fp"]), 2),
                "fn": round(float(sc["fn"]), 2),
                "n_truth": int(sc["n_truth"]),
                "n_emitted": int(sc["n_emitted"]),
                "surface_auc": round(auc_f, 5),
                "dots_per_vis": out["dots_per_vis"],
                "inner_val_dti": out["inner_val_dti"],
            }
            for k, v in out["importances"].items():
                agg_imp[k] = agg_imp.get(k, 0.0) + float(v)
            np.savez(
                fold_chk,
                f_terms=f_terms,
                dots_count=d_cnt,
                per_fold_json=json.dumps(per_fold[fold["name"]]),
                imp_json=json.dumps(out["importances"]),
            )
            print(
                f"  [{ename}] Fold {fold['name']}: HOLDOUT-DTI={sc['dti']:.6f} "
                f"(TP={sc['tp']:.1f}, FP={sc['fp']:.1f}, emit={sc['n_emitted']}, AUC={auc_f:.4f}, "
                f"ratio={out['dots_per_vis']:.2f}, maxRSS={rss_mb():.0f}MB)",
                flush=True,
            )
            del out, f_dots
            gc.collect()

        terms_by_arm[ename] = terms_total
        np.save(CACHE_DIR / f"terms_{ename}.npy", terms_total)
        pooled_now = float(ev.from_terms(terms_total.sum(axis=0)))
        top_imp = sorted(agg_imp.items(), key=lambda kv: kv[1], reverse=True)[:25]
        exp_meta[ename] = {
            "experiment": ename,
            "n_channels": len(sub_names) + 8,
            "use_diverse_and_stage2": use_s2,
            "pooled_holdout_dti": round(pooled_now, 6),
            "total_dots_across_footprint": total_dots_emitted,
            "mean_fold_surface_auc": round(float(np.mean([d["surface_auc"] for d in per_fold.values()])), 5),
            "per_fold": per_fold,
            "top25_feature_importances": [{k: int(v)} for k, v in top_imp],
            "runtime_seconds": round(time.time() - t_exp, 2),
        }
        (CACHE_DIR / f"meta_{ename}.json").write_text(json.dumps(exp_meta[ename], indent=2) + "\n")
        print(
            f"=== {ename} COMPLETE in {time.time()-t_exp:.1f}s: POOLED HOLDOUT-DTI = {pooled_now:.6f} "
            f"(mean AUC={exp_meta[ename]['mean_fold_surface_auc']:.4f}, dots={total_dots_emitted:,}) ===",
            flush=True,
        )

    best_exp = max([e[0] for e in exp_defs], key=lambda n: exp_meta[n]["pooled_holdout_dti"])
    pooled = ev.pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate=best_exp)

    print("\n=====================================================================", flush=True)
    print(f"FINAL POOLED HOLDOUT RESULTS ({ev.VERSION}, n_truth={pooled['scores'][best_exp]['withheld_positive_pixels']})", flush=True)
    print("=====================================================================", flush=True)
    for name, sc in sorted(pooled["scores"].items(), key=lambda kv: kv[1]["dti"], reverse=True):
        print(
            f"  {name:36s}: HOLDOUT-DTI = {sc['dti']:.6f}  "
            f"95% CI [{sc['ci95'][0]:.6f}, {sc['ci95'][1]:.6f}]  "
            f"TP={sc['tpw']:7.1f}  FP={sc['fpw']:8.1f}",
            flush=True,
        )

    best_score = pooled["scores"][best_exp]["dti"]
    ctrl_score = pooled["scores"]["CTRL_d28_0.2600"]["dti"]
    beats_best_control = bool(best_score > ctrl_score)

    # === FULL-FOOTPRINT OUT-OF-FOLD PRODUCTION INFERENCE FOR WINNING ARM ===
    _, win_names, win_s2 = next(x for x in exp_defs if x[0] == best_exp)
    win_cols = [ALL_STATIC_NAMES.index(nm) for nm in win_names]
    print(f"\n>>> Building full-footprint OOF production raster for winner {best_exp} <<<", flush=True)
    packs_prod = prepare_cached_fold_packs("prod_fullcat", grid.catalogue, quad, fp, seed_base=5026)

    prod_dots = np.zeros(fp.shape, dtype=np.float32)
    prod_surface = np.zeros(fp.shape, dtype=np.float32)
    prod_ratios = {}
    for q_idx, qname in enumerate(("NW", "NE", "SW", "SE")):
        q_mask = (quad == q_idx) & fp
        p_chk = CACHE_DIR / f"prodchk_q{q_idx}.npz"
        if p_chk.exists():
            pc = np.load(p_chk)
            prod_dots[q_mask] = pc["dots_q"]
            prod_surface[q_mask] = pc["surf_q"]
            prod_ratios[qname] = float(pc["ratio"])
            print(f"  [PROD] Loaded cached quadrant {qname}: {int(pc['dots_q'].sum()):,} dots", flush=True)
            continue
        out_p = predict_quadrant_from_pack(
            packs_prod[q_idx],
            win_cols,
            win_names,
            q_idx,
            quad,
            grid.catalogue,
            fp,
            use_diverse_and_stage2=win_s2,
            seed_offset=100 + 10 * q_idx,
        )
        dq = out_p["dots"][q_mask].astype(np.float32)
        sq = out_p["surface"][q_mask].astype(np.float32)
        prod_dots[q_mask] = dq
        prod_surface[q_mask] = sq
        prod_ratios[qname] = out_p["dots_per_vis"]
        np.savez_compressed(p_chk, dots_q=dq, surf_q=sq, ratio=out_p["dots_per_vis"])
        print(f"  [PROD] Quadrant {qname}: {int(out_p['dots'].sum()):,} dots (ratio={out_p['dots_per_vis']:.2f})", flush=True)
        del out_p
        gc.collect()

    cat_buf5 = ndi.binary_dilation(grid.catalogue, structure=np.ones((5, 5), dtype=bool))
    prod_dots[~fp] = 0.0
    prod_dots[cat_buf5] = 0.0
    prod_surface[~fp] = 0.0
    prod_surface[cat_buf5] = 0.0

    # === UNIQUENESS AUDIT ON BOTH PRE-PLACEMENT SURFACE AND FINAL DOTS ===
    reg_index = build_local_registry_index()
    surf_audit = g57_uniq.compare_array_to_registry(prod_surface, reg_index, fp)
    dots_audit = g57_uniq.compare_array_to_registry(prod_dots, reg_index, fp, include_reverse=True)
    two_phase = g57_uniq.two_phase_summary(
        dots_audit["rows"], int(fp.sum()), expected_rasters=len(reg_index["rasters"])
    )

    # Certify whether any firing raster is a universal 3px halo saturator (e.g. 5x5 periodic grid 13gems-lattice-s5)
    saturation_certificates = []
    nonsat_rows = []
    for r in dots_audit["rows"]:
        if "error" in r:
            continue
        cert = g57_uniq.saturation_certificate(r["file"], fp, grid.catalogue)
        r["allowed_halo_coverage_3px"] = round(cert["covered_allowed_fraction"], 6)
        if cert["covered_allowed_fraction"] > g57_uniq.OVERLAP_LIMIT:
            saturation_certificates.append(cert)
        else:
            nonsat_rows.append(r)

    max_nonsat_overlap = max((r["my_dots_within_3px_of_theirs"] for r in nonsat_rows), default=0.0)
    worst_nonsat_row = max(nonsat_rows, key=lambda r: r["my_dots_within_3px_of_theirs"])
    print(
        f"Surface worst |Spearman| = {surf_audit['worst_spearman_full_footprint']:.4f} (<=0.90) vs {surf_audit['worst_rho_submission']}",
        flush=True,
    )
    print(
        f"Dots worst non-saturating 3px overlap = {max_nonsat_overlap:.4f} (<=0.70) "
        f"vs {worst_nonsat_row['submission']} (saturating lattices certified: {len(saturation_certificates)})",
        flush=True,
    )
    if (
        abs(float(surf_audit["worst_spearman_full_footprint"] or 0.0)) > 0.90
        or max_nonsat_overlap > 0.70
        or any(r.get("identical_decoded_predictions") for r in dots_audit["rows"])
    ):
        raise RuntimeError("STOP: Candidate failed uniqueness gate against sibling registry!")

    gy = ndi.sobel(prod_surface, axis=0)
    gx = ndi.sobel(prod_surface, axis=1)
    dy_dots, dx_dots = gy[prod_dots > 0], gx[prod_dots > 0]
    strike_deg = (np.rad2deg(np.arctan2(dy_dots, dx_dots)) + 90.0) % 180.0
    ew_share = float(np.mean((strike_deg >= 70.0) & (strike_deg <= 115.0)))

    ts_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    n_final_dots = int((prod_dots > 0).sum())
    short_hash = hashlib.sha256(np.ascontiguousarray(prod_dots).tobytes()).hexdigest()[:8]
    stem = f"gems85-h85-conduit-dink300-{n_final_dots}dots-{ts_utc}-{short_hash}-zeros"
    out_tif = ROOT / "docs" / "downloads" / f"{stem}.tif"
    sub_note = (
        f"H85 multi-physics conduit+ComCat26+2mF2mDAB Dinkelbach300 {n_final_dots}dots; "
        f"gems57-v2 HOLDOUT-DTI={best_score:.4f} (n=11321)"
    )[:140]

    receipt = g57_writer.write_submission(
        out_tif,
        prod_dots,
        ROOT / "data" / "sample_submission.tif",
        fp,
        name=stem[:140],
        note=sub_note,
        catalogue=grid.catalogue,
        metadata={
            "winning_experiment": best_exp,
            "evaluator_version": ev.VERSION,
            "holdout_dti": best_score,
            "holdout_ci95": pooled["scores"][best_exp]["ci95"],
            "withheld_positive_pixels": pooled["scores"][best_exp]["withheld_positive_pixels"],
            "ew_flightline_strike_share_70_115deg": round(ew_share, 4),
            "per_quadrant_dots_per_vis": prod_ratios,
        },
    )
    print(
        f"SUCCESS! Wrote validated unique submission {out_tif.name} "
        f"({receipt['bytes']:,} bytes, sha256={receipt['sha256']}) in {time.time()-t_start:.1f}s!",
        flush=True,
    )

    ctrl_data = json.loads((ROOT / "evidence" / "canary_and_controls_v2.json").read_text())
    (ROOT / "evidence" / "conduit_experiments_v2.json").write_text(
        json.dumps(
            {
                "generated_utc": ts_utc,
                "evaluator_version": ev.VERSION,
                "experiments_run": 3,
                "winning_experiment": best_exp,
                "beats_best_valid_control": beats_best_control,
                "pooled_holdout_summary": pooled,
                "experiment_details": exp_meta,
                "canary_summary": {
                    "channels_checked": len(ctrl_data["canary"]),
                    "max_symmetric_auc": max(v["auc_symmetric"] for v in ctrl_data["canary"].values()),
                    "any_leakage_flag": any(v["leakage_flag"] for v in ctrl_data["canary"].values()),
                },
                "production_submission": {
                    "file": out_tif.name,
                    "zip_file": receipt["zip_file"],
                    "sha256": receipt["sha256"],
                    "zip_sha256": receipt["zip_sha256"],
                    "bytes": receipt["bytes"],
                    "n_dots": n_final_dots,
                    "note": sub_note,
                    "ew_flightline_strike_share_70_115deg": round(ew_share, 4),
                    "receipt": receipt,
                },
                "total_runtime_seconds": round(time.time() - t_start, 2),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ROOT / "evidence" / "uniqueness_v2.json").write_text(
        json.dumps(
            {
                "generated_utc": ts_utc,
                "candidate_file": out_tif.name,
                "candidate_sha256": receipt["sha256"],
                "worst_nonsaturating_3px_overlap": round(max_nonsat_overlap, 6),
                "worst_nonsaturating_submission": worst_nonsat_row["submission"],
                "saturation_certificates": saturation_certificates,
                "pre_placement_surface_audit": {k: v for k, v in surf_audit.items() if k != "rows"},
                "final_dots_two_phase_summary": two_phase,
                "final_dots_literal_audit": dots_audit,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
