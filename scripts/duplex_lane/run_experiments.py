#!/usr/bin/env python3
"""GEMSDOE85 experiments: 3 candidate fields on the protocol holdout + controls.

E1 (H85-A, top candidate): fold-proper HistGradientBoosting detector on the
    35-channel template stack + 20 external uint8 channels.  NO catalogue-derived
    feature (no distance-to-catalogue).  Trained per fold on visible faults only.
E2 (H85-B): label-free multi-physics orientation-consensus surface.
E3 (H85-C): label-free strain-gated lineament surface.
Controls: the ORGANIZER-CONFIRMED 0.2600 d2.8 raster and the 0.2778 h33-2-b2
    raster, scored as-is on the same holdout (they are registry rasters, never
    candidates).  Promotion bar = best control pooled HOLDOUT-DTI.

Emission for every candidate: support = top-150k field pixels (pro-rated per
fold), lazy-greedy max-coverage (template emitter), budget pro-rated from the
37654-dot global operating point, allowed = footprint & EDT(visible) > 2 px.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from gems85 import evaluate_holdout as EH          # noqa: E402
from gems85 import emitter, fields                 # noqa: E402
from gems85.features import CHANNELS               # noqa: E402

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data"
CACHE = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/gems85_cache")
GLOBAL_BUDGET = 37654
SUPPORT_GLOBAL = 150000
SEED = 85


def read_bool(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> None:
    t0 = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    stack_path = CACHE / "feature_stack.npy"
    if not stack_path.exists():
        from gems85 import features as F
        receipt = F.build(DATA / "training_features.tif", stack_path, log=lambda m: print(m, flush=True))
        (CACHE / "feature_receipt.json").write_text(json.dumps(receipt, indent=2))
    stack = np.lib.format.open_memmap(stack_path, mode="r")
    print(f"stack {stack.shape} ({time.time()-t0:.0f}s)", flush=True)

    with rasterio.open(DATA / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    labels = read_bool(DATA / "labels.tif") & foot

    ext = []
    ext_names = []
    for rel, names in [("external/lidar_scarp_features_u8.tif",
                        [f"lidar_{n}" for n in ["ex_max","ex_mean","step_max","lapneg_max","lappos_max","downface_max","upface_max","cross_max","relief","coh100","strike","valid"]]),
                       ("external/geodawn_rad_u8.tif", ["rad_K", "rad_Th", "rad_U", "rad_TC"]),
                       ("external/geodawn_extensions_u8.tif", ["ext_ThK", "ext_UK", "ext_UTh", "ext_TMIup150"])]:
        with rasterio.open(DATA / rel) as s:
            for i, nm in enumerate(names, start=1):
                ext.append(s.read(i))
                ext_names.append(nm)
    ext_arr = np.stack(ext, axis=-1)  # uint8 HxWx20
    print(f"ext {ext_arr.shape} ({time.time()-t0:.0f}s)", flush=True)

    def sample_X(ys, xs):
        X35 = np.asarray(stack[ys, xs, :], dtype=np.float32)
        Xe = ext_arr[ys, xs, :].astype(np.float32) / 255.0
        return np.concatenate([X35, Xe], axis=1)

    feature_names = list(CHANNELS) + ext_names

    holdout = EH.make_holdout(labels, foot)
    n_withheld = int(sum(c.withheld.sum() for c in holdout.cells))
    print(f"holdout cells={len(holdout.cells)} withheld_px_total={n_withheld} ({time.time()-t0:.0f}s)", flush=True)

    # union withheld per fold (segment-leakage guard for fold training)
    union_withheld = {}
    for fold in range(4):
        u = np.zeros_like(labels)
        for c in holdout.cells:
            if c.fold == fold:
                u |= c.withheld
        union_withheld[fold] = u

    rng = np.random.default_rng(SEED)
    results = {}

    # ---------- label-free fields (computed once, globally) ----------
    print("building H85-B orientation consensus...", flush=True)
    surf_b = fields.surface_orientation_consensus(stack, foot)
    np.save(CACHE / "surf_h85b.npy", surf_b)
    print(f"  done ({time.time()-t0:.0f}s)", flush=True)
    print("building H85-C strain-gated...", flush=True)
    surf_c = fields.surface_strain_gated(stack, foot)
    np.save(CACHE / "surf_h85c.npy", surf_c)
    print(f"  done ({time.time()-t0:.0f}s)", flush=True)

    # ---------- per-fold supervised models + emissions ----------
    fold_masks = {"E1_supervised_hgb": {}, "E2_orientation_consensus": {}, "E3_strain_gated": {}}
    fold_field_e1 = {}
    canary_rows = []   # (feature_name, values_pos, values_neg) accumulated later
    canary_pos_X, canary_neg_X, canary_pos_field, canary_neg_field = [], [], {}, {}
    dist_labels = ndimage.distance_transform_edt(~labels)

    for fold in range(4):
        cells = [c for c in holdout.cells if c.fold == fold]
        train_mask = cells[0].train_mask
        visible_train = labels & train_mask & ~union_withheld[fold]
        pos_ys, pos_xs = np.nonzero(visible_train)
        neg_pool = np.argwhere(train_mask & ~labels & (dist_labels > 1))
        neg_idx = rng.choice(len(neg_pool), size=min(3 * len(pos_ys), len(neg_pool)), replace=False)
        neg_ys, neg_xs = neg_pool[neg_idx, 0], neg_pool[neg_idx, 1]
        ys = np.concatenate([pos_ys, neg_ys]); xs = np.concatenate([pos_xs, neg_xs])
        y = np.concatenate([np.ones(len(pos_ys), np.int8), np.zeros(len(neg_ys), np.int8)])
        X = sample_X(ys, xs)
        clf = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08,
                                             max_leaf_nodes=63, min_samples_leaf=40,
                                             l2_regularization=1.0, random_state=SEED)
        clf.fit(X, y)
        print(f"fold{fold}: trained pos={len(pos_ys)} neg={len(neg_ys)} ({time.time()-t0:.0f}s)", flush=True)

        # predict this fold's test quadrant in row blocks
        test_mask = cells[0].test_domain
        rows = np.flatnonzero(test_mask.any(axis=1))
        field_e1 = np.zeros(labels.shape, np.float32)
        for r0 in range(int(rows.min()), int(rows.max()) + 1, 128):
            r1 = min(r0 + 128, labels.shape[0])
            blk = test_mask[r0:r1]
            by, bx = np.nonzero(blk)
            if len(by) == 0:
                continue
            Xb = sample_X(by + r0, bx)
            field_e1[by + r0, bx] = clf.predict_proba(Xb)[:, 1].astype(np.float32)
        fold_field_e1[fold] = field_e1
        np.save(CACHE / f"field_e1_fold{fold}.npy", field_e1)

        # canary samples for this fold (from draw20 cell)
        cell = cells[0]
        py, px = np.nonzero(cell.withheld & cell.test_domain)
        neg_candidates = np.argwhere(cell.test_domain & ~labels & (dist_labels > 3))
        nidx = rng.choice(len(neg_candidates), size=min(len(py), len(neg_candidates)), replace=False)
        ny, nx = neg_candidates[nidx, 0], neg_candidates[nidx, 1]
        canary_pos_X.append(sample_X(py, px)); canary_neg_X.append(sample_X(ny, nx))
        for nm, surf in [("E1_supervised_hgb", field_e1), ("E2_orientation_consensus", surf_b),
                         ("E3_strain_gated", surf_c)]:
            canary_pos_field.setdefault(nm, []).append(surf[py, px])
            canary_neg_field.setdefault(nm, []).append(surf[ny, nx])

        # emissions per experiment for this fold (scored against both draws)
        visible_fold = labels & ~union_withheld[fold]
        d_vis = ndimage.distance_transform_edt(~visible_fold)
        for nm, surf in [("E1_supervised_hgb", field_e1), ("E2_orientation_consensus", surf_b),
                         ("E3_strain_gated", surf_c)]:
            allowed = cells[0].test_domain & foot & (d_vis > 2.0)
            budget = int(round(GLOBAL_BUDGET * float(cells[0].test_domain.sum()) / float(foot.sum())))
            support_n = int(round(SUPPORT_GLOBAL * float(cells[0].test_domain.sum()) / float(foot.sum())))
            sup = fields.top_n_support(surf, allowed, support_n)
            f2 = np.where(sup, surf, 0.0).astype(np.float32)
            mask, log = emitter.emit(f2, budget=budget, prior_dti=0.0)
            for c in cells:
                fold_masks[nm][c.key] = mask
            print(f"fold{fold} {nm}: emitted={int(mask.sum())} budget={budget} ({time.time()-t0:.0f}s)", flush=True)

    for nm, fm in fold_masks.items():
        results[nm] = EH.score_fold_masks(fm, holdout)
        r = results[nm]
        print(f"{nm}: HOLDOUT-DTI pooled={r['pooled_dti']:.6f} CI={r['ci95']} n={r['n_withheld_positives']}", flush=True)

    # ---------- controls (registry rasters, scored as-is) ----------
    controls = {}
    for nm, p in [("CTRL_d28_0.2600", DATA / "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"),
                  ("CTRL_h33_0.2778", Path("/tmp/g32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"))]:
        if p.exists():
            m = read_bool(p)
            controls[nm] = EH.score_mask_pooled(m, holdout)
            print(f"{nm}: HOLDOUT-DTI pooled={controls[nm]['pooled_dti']:.6f} CI={controls[nm]['ci95']}", flush=True)

    # ---------- leakage canary: every feature alone ----------
    Xp = np.concatenate(canary_pos_X); Xn = np.concatenate(canary_neg_X)
    canary = {}
    for j, nm in enumerate(feature_names):
        v = np.concatenate([Xp[:, j], Xn[:, j]])
        yy = np.concatenate([np.ones(len(Xp)), np.zeros(len(Xn))])
        ok = np.isfinite(v)
        auc = float(roc_auc_score(yy[ok], v[ok])) if ok.sum() > 10 else None
        canary[nm] = dict(auc=auc, leakage_flag=bool(auc is not None and max(auc, 1 - auc) > 0.90))
    for nm in canary_pos_field:
        vp = np.concatenate(canary_pos_field[nm]); vn = np.concatenate(canary_neg_field[nm])
        v = np.concatenate([vp, vn]); yy = np.concatenate([np.ones(len(vp)), np.zeros(len(vn))])
        auc = float(roc_auc_score(yy, v))
        canary[nm] = dict(auc=auc, leakage_flag=bool(max(auc, 1 - auc) > 0.90))

    out = dict(evaluator=EH.EVALUATOR_VERSION, global_budget=GLOBAL_BUDGET,
               support_global=SUPPORT_GLOBAL, n_withheld_positives=n_withheld,
               experiments=results, controls=controls, canary=canary,
               feature_names=feature_names, seconds=time.time() - t0)
    (ROOT / "evidence" / "holdout_experiments.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({k: (v["pooled_dti"], v["ci95"]) for k, v in {**results, **controls}.items()}, indent=2))
    print(f"DONE {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
