#!/usr/bin/env python3
"""Execute the preregistered 3-experiment validation for Lane H85-P1 (`PRPC-Submod`).

Supports `--stage {canary,gems57,gems85,merge,all}` so each instrument checkpoints cleanly.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "src"))

from gems57 import evaluate_holdout as eh57  # noqa: E402
from gems57 import holdout as ho57  # noqa: E402
from gems85 import emission, geopb, grid, holdout, prpc  # noqa: E402

CACHE_DIR = ROOT / ".cache" / "prpc"
EVIDENCE_DIR = ROOT / "evidence"
BUDGET = 37_654


def _fast_auc_folds85(values: np.ndarray, folds85: list[holdout.Fold], fp: np.ndarray, seed: int = 7) -> float:
    pos_l, neg_l = [], []
    rng = np.random.default_rng(seed)
    for fold in folds85:
        ok = fp & (~fold.visible) & np.isfinite(values)
        pos_l.append(values[ok & fold.withheld])
        neg = values[ok & (~fold.withheld)]
        if neg.size > 200_000:
            neg = rng.choice(neg, 200_000, replace=False)
        neg_l.append(neg)
    pos = np.concatenate(pos_l)
    neg = np.concatenate(neg_l)
    y = np.concatenate([np.ones(pos.size, dtype=np.int8), np.zeros(neg.size, dtype=np.int8)])
    return float(roc_auc_score(y, np.concatenate([pos, neg])))


def _fast_auc_on_mask(values: np.ndarray, pos_mask: np.ndarray, eval_mask: np.ndarray, seed: int = 7) -> float:
    ok = eval_mask & np.isfinite(values)
    pos = values[ok & pos_mask]
    neg = values[ok & (~pos_mask)]
    if pos.size == 0 or neg.size == 0:
        return 0.5
    rng = np.random.default_rng(seed)
    if neg.size > 400_000:
        neg = rng.choice(neg, 400_000, replace=False)
    y = np.concatenate([np.ones(pos.size, dtype=np.int8), np.zeros(neg.size, dtype=np.int8)])
    s = np.concatenate([pos, neg])
    return float(roc_auc_score(y, s))


def _eval_gems57_arm(prediction: np.ndarray, folds57: list[dict], fp: np.ndarray) -> tuple[np.ndarray, list[dict]]:
    acc_terms = None
    per_quad = []
    for f in folds57:
        res_q, terms_q = eh57.evaluate(prediction, f, fp, block_side=200)
        acc_terms = terms_q if acc_terms is None else (acc_terms + terms_q)
        per_quad.append({
            "quadrant": f["name"],
            "dti": float(res_q["dti"]),
            "n_truth": int(res_q["n_truth"]),
            "n_emitted_in_region": int(res_q["n_emitted"]),
        })
    return acc_terms, per_quad


def run_leakage_canary(
    bundle: prpc.BlindStackBundle,
    fp: np.ndarray,
    folds57: list[dict],
    folds85: list[holdout.Fold],
) -> dict:
    t0 = time.time()
    vis57 = folds57[0]["visible"]
    masked_known57 = folds57[0]["masked_known"]
    regions57 = np.zeros_like(fp)
    pos57 = np.zeros_like(fp)
    for f in folds57:
        regions57 |= f["region"]
        pos57 |= f["truth"]
    eval57 = fp & regions57 & (~masked_known57)

    blind_canaries = {}
    full_tmp = np.zeros(fp.shape, dtype=np.float32)
    for j, nm in enumerate(bundle.feature_names):
        full_tmp.fill(0.0)
        full_tmp.ravel()[bundle.fp_idx] = bundle.X_fp[:, j]
        auc57 = _fast_auc_on_mask(full_tmp, pos57, eval57, seed=17 + j)
        auc85 = _fast_auc_folds85(full_tmp, folds85, fp, seed=17 + j)
        sym = max(auc57, 1.0 - auc57, auc85, 1.0 - auc85)
        blind_canaries[nm] = {
            "auc_gems57": round(auc57, 5),
            "auc_gems85": round(auc85, 5),
            "max_symmetric_auc": round(sym, 5),
        }

    auc57_e1 = _fast_auc_on_mask(bundle.e1_surface, pos57, eval57, seed=99)
    auc85_e1 = _fast_auc_folds85(bundle.e1_surface, folds85, fp, seed=99)
    blind_canaries["e1_unsupervised_surface"] = {
        "auc_gems57": round(auc57_e1, 5),
        "auc_gems85": round(auc85_e1, 5),
        "max_symmetric_auc": round(max(auc57_e1, 1.0 - auc57_e1, auc85_e1, 1.0 - auc85_e1), 5),
    }

    net57 = prpc.build_visible_network_features(
        vis57, bundle.prpc_strike_rad, bundle.prpc_score_z, fp
    )
    net_canaries = {}
    for k_idx, (nm, arr) in enumerate(net57.items()):
        auc57 = _fast_auc_on_mask(arr, pos57, eval57, seed=200 + k_idx)
        sym = max(auc57, 1.0 - auc57)
        net_canaries[nm] = {
            "auc_gems57": round(auc57, 5),
            "max_symmetric_auc": round(sym, 5),
        }
    del net57
    gc.collect()

    all_syms = [d["max_symmetric_auc"] for d in blind_canaries.values()] + [
        d["max_symmetric_auc"] for d in net_canaries.values()
    ]
    max_sym = float(max(all_syms))
    worst_name = max(
        list(blind_canaries.items()) + list(net_canaries.items()),
        key=lambda kv: kv[1]["max_symmetric_auc"],
    )[0]
    passed = max_sym <= 0.90
    report = {
        "gate": "single_feature_holdout_auc_le_0.90",
        "passed": passed,
        "max_symmetric_auc": round(max_sym, 5),
        "highest_feature": worst_name,
        "n_blind_features_tested": len(blind_canaries),
        "n_visible_network_features_tested": len(net_canaries),
        "blind_features": blind_canaries,
        "visible_network_features": net_canaries,
        "runtime_s": round(time.time() - t0, 2),
    }
    (EVIDENCE_DIR / "prpc_leakage_canary.json").write_text(json.dumps(report, indent=2) + "\n")
    if not passed:
        raise RuntimeError(f"LEAKAGE CANARY FAILED: {worst_name} max_symmetric_auc={max_sym:.4f} > 0.90")
    return report


def _build_pr6_geopb_fused(fp: np.ndarray) -> np.ndarray:
    cache_p = CACHE_DIR / "pr6_geopb_fused.npy"
    if cache_p.exists():
        return np.load(cache_p)
    r3 = geopb.geopb_surface(sigma=1.5, normals=tuple(geopb.NORMALS_R3), persistence_px=15.0, footprint=fp)
    r6 = geopb.geopb_surface(sigma=2.5, normals=tuple(geopb.NORMALS_R6), persistence_px=25.0, footprint=fp)

    def _rk(a: np.ndarray) -> np.ndarray:
        v = a[fp]
        out = np.zeros(a.shape, dtype=np.float32)
        order = np.argsort(v, kind="stable")
        rk = np.empty(v.size, dtype=np.float32)
        rk[order] = np.arange(v.size, dtype=np.float32) / max(1, v.size - 1)
        out[fp] = rk
        return out

    fused = (0.5 * _rk(r3) + 0.5 * _rk(r6)).astype(np.float32)
    np.save(cache_p, fused)
    return fused


def _uniform_random_dots(fp: np.ndarray, vis: np.ndarray, n: int, seed: int = 8500) -> np.ndarray:
    dist = ndi.distance_transform_edt(~vis)
    allowed = np.flatnonzero((fp & (dist > 2.0)).ravel())
    rng = np.random.default_rng(seed)
    sel = rng.choice(allowed, min(n, allowed.size), replace=False)
    out = np.zeros(fp.shape, dtype=np.float32)
    out.ravel()[sel] = 1.0
    return out


def run_stage_gems57(bundle: prpc.BlindStackBundle, fp: np.ndarray, cat: np.ndarray, t0: float) -> dict:
    folds57, quad57 = ho57.buffered_component_draw(
        SimpleNamespace(catalogue=cat, footprint=fp),
        seed=20,
        hide_frac=0.20,
        buffer_px=3,  # canonical vendor/gems57 default
    )
    n_withheld_57 = sum(int(f["truth"].sum()) for f in folds57)
    vis57 = folds57[0]["visible"]
    collar57 = cat & (~vis57)

    regions57 = np.zeros_like(fp)
    pos57 = np.zeros_like(fp)
    for f in folds57:
        regions57 |= f["region"]
        pos57 |= f["truth"]
    eval57 = fp & regions57 & (~folds57[0]["masked_known"])

    geopb_fused = _build_pr6_geopb_fused(fp)
    pred57 = {}
    pred57["ctrl_uniform_38k"] = _uniform_random_dots(fp, vis57, BUDGET, seed=8500)
    pred57["ctrl_pr6_geopb_38k"] = emission.emit(
        geopb_fused, footprint=fp, visible_catalogue=vis57, n=BUDGET, sep_px=2.8, exclude_px=2
    )
    pred57["ctrl_pr6_geopb_90k"] = emission.emit(
        geopb_fused, footprint=fp, visible_catalogue=vis57, n=90_000, sep_px=2.8, exclude_px=2
    )

    p_e1_57, _ = prpc.submodular_emit_off_catalogue(
        bundle.e1_surface, footprint=fp, visible_catalogue=vis57, budget=BUDGET
    )
    pred57["E1_PRPC_Unsupervised"] = p_e1_57
    auc_e1_57 = _fast_auc_on_mask(bundle.e1_surface, pos57, eval57, seed=40)
    print(f"   [{time.time()-t0:6.1f}s] E1_PRPC_Unsupervised emitted (AUC={auc_e1_57:.4f})")

    loqo_e2_surface = np.zeros(fp.shape, dtype=np.float32)
    loqo_e3_surface = np.zeros(fp.shape, dtype=np.float32)
    net_vis57 = prpc.build_visible_network_features(
        vis57, bundle.prpc_strike_rad, bundle.prpc_score_z, fp
    )
    for q in range(4):
        q_t0 = time.time()
        q_mask = (quad57 == q) & fp
        forbid_q = collar57 | (quad57 == q)
        vis_train_q = vis57 & (quad57 != q)

        oof_bq, grid_bq = prpc.fit_predict_blind_oof(
            bundle, fp, vis_train_q,
            forbidden_train_mask=forbid_q,
            eval_target_mask=q_mask,
            n_inner_folds=3,
            seed=8520 + 10 * q,
        )
        loqo_e2_surface[q_mask] = grid_bq[q_mask]

        grid_dq = prpc.fit_predict_dual_expert(
            bundle, oof_bq, grid_bq, fp,
            train_visible=vis_train_q,
            inf_visible=vis57,
            precomputed_inf_net=net_vis57,
            eval_target_mask=q_mask,
            forbidden_train_mask=forbid_q,
            n_inner_comp_folds=3,
            inner_buffer_px=3,
            seed=8560 + 10 * q,
        )
        loqo_e3_surface[q_mask] = grid_dq[q_mask]
        print(f"   [{time.time()-t0:6.1f}s] LOQO quadrant {folds57[q]['name']} predicted ({time.time()-q_t0:.1f}s)")
        del oof_bq, grid_bq, grid_dq
        gc.collect()
    del net_vis57
    gc.collect()

    p_e2_57, _ = prpc.submodular_emit_off_catalogue(
        loqo_e2_surface, footprint=fp, visible_catalogue=vis57, budget=BUDGET
    )
    pred57["E2_PRPC_Blind_OOF"] = p_e2_57
    auc_e2_57 = _fast_auc_on_mask(loqo_e2_surface, pos57, eval57, seed=41)

    p_e3_57, _ = prpc.submodular_emit_off_catalogue(
        loqo_e3_surface, footprint=fp, visible_catalogue=vis57, budget=BUDGET
    )
    pred57["E3_PRPC_Dual_Submod"] = p_e3_57
    auc_e3_57 = _fast_auc_on_mask(loqo_e3_surface, pos57, eval57, seed=42)
    print(f"   [{time.time()-t0:6.1f}s] LOQO AUCs: E1={auc_e1_57:.4f}, E2={auc_e2_57:.4f}, E3={auc_e3_57:.4f}")

    terms57 = {}
    per_quad57 = {}
    for arm_name, arr in pred57.items():
        t_arm, pq = _eval_gems57_arm(arr, folds57, fp)
        terms57[arm_name] = t_arm
        per_quad57[arm_name] = pq
    summary57 = eh57.pooled_summary(terms57, draws=1000, seed=520810, candidate="E3_PRPC_Dual_Submod")
    for arm_name, sc in summary57["scores"].items():
        print(
            f"   [gems57-pooled-hide-v2] {arm_name:22s}: HOLDOUT-DTI = {sc['dti']:.5f} "
            f"CI95 [{sc['ci95'][0]:.5f}, {sc['ci95'][1]:.5f}]"
        )

    res = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": summary57["evaluator_version"],
        "withheld_positive_pixels": n_withheld_57,
        "feature_buffer_px": 3,
        "withheld_auc": {
            "E1_PRPC_Unsupervised": round(auc_e1_57, 5),
            "E2_PRPC_Blind_OOF": round(auc_e2_57, 5),
            "E3_PRPC_Dual_Submod": round(auc_e3_57, 5),
        },
        "per_quadrant": per_quad57,
        "summary": summary57,
        "published_family_comparators": {
            "GEMSDOE70_P8_OOF38k": {"dti": 0.1113, "live_dti": 0.2478},
            "GEMSDOE70_P9": {"dti": 0.1100},
        },
    }
    (EVIDENCE_DIR / "prpc_gems57.json").write_text(json.dumps(res, indent=2) + "\n")
    return res


def run_stage_gems85(bundle: prpc.BlindStackBundle, fp: np.ndarray, cat: np.ndarray, t0: float) -> dict:
    folds85 = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5, seed=20261022)
    geopb_fused = _build_pr6_geopb_fused(fp)

    folds_e1_preds, folds_e2_preds, folds_e3_preds = {}, {}, {}
    folds_geopb38_preds, folds_rand_preds = {}, {}
    aucs_e1_85, aucs_e2_85, aucs_e3_85 = [], [], []

    for f_idx, fold in enumerate(folds85):
        f_t0 = time.time()
        halo_f = ndi.binary_dilation(fold.withheld, np.ones((3, 3), bool), iterations=5)
        forbid_f = fold.withheld | halo_f
        eval_f = fp & (~fold.visible)

        folds_rand_preds[fold.name] = _uniform_random_dots(fp, fold.visible, BUDGET, seed=8600 + f_idx)
        folds_geopb38_preds[fold.name] = emission.emit(
            geopb_fused, footprint=fp, visible_catalogue=fold.visible, n=BUDGET, sep_px=2.8, exclude_px=2
        )

        p1, _ = prpc.submodular_emit_off_catalogue(
            bundle.e1_surface, footprint=fp, visible_catalogue=fold.visible, budget=BUDGET
        )
        folds_e1_preds[fold.name] = p1
        aucs_e1_85.append(_fast_auc_on_mask(bundle.e1_surface, fold.withheld, eval_f, seed=40 + f_idx))

        oof_bf, grid_bf = prpc.fit_predict_blind_oof(
            bundle, fp, fold.visible,
            forbidden_train_mask=forbid_f,
            eval_target_mask=eval_f,
            n_inner_folds=3,
            seed=8700 + 10 * f_idx,
        )
        p2, _ = prpc.submodular_emit_off_catalogue(
            grid_bf, footprint=fp, visible_catalogue=fold.visible, budget=BUDGET
        )
        folds_e2_preds[fold.name] = p2
        aucs_e2_85.append(_fast_auc_on_mask(grid_bf, fold.withheld, eval_f, seed=50 + f_idx))

        grid_df = prpc.fit_predict_dual_expert(
            bundle, oof_bf, grid_bf, fp,
            train_visible=fold.visible,
            inf_visible=fold.visible,
            eval_target_mask=eval_f,
            forbidden_train_mask=forbid_f,
            n_inner_comp_folds=3,
            inner_buffer_px=5,
            seed=8800 + 10 * f_idx,
        )
        p3, _ = prpc.submodular_emit_off_catalogue(
            grid_df, footprint=fp, visible_catalogue=fold.visible, budget=BUDGET
        )
        folds_e3_preds[fold.name] = p3
        aucs_e3_85.append(_fast_auc_on_mask(grid_df, fold.withheld, eval_f, seed=60 + f_idx))
        print(
            f"   [{time.time()-t0:6.1f}s] {fold.name} ({time.time()-f_t0:.1f}s): "
            f"AUC_E1={aucs_e1_85[-1]:.4f}, AUC_E2={aucs_e2_85[-1]:.4f}, AUC_E3={aucs_e3_85[-1]:.4f}"
        )
        del oof_bf, grid_bf, grid_df
        gc.collect()

    arms85_preds = {
        "ctrl_uniform_38k": folds_rand_preds,
        "ctrl_pr6_geopb_38k": folds_geopb38_preds,
        "E1_PRPC_Unsupervised": folds_e1_preds,
        "E2_PRPC_Blind_OOF": folds_e2_preds,
        "E3_PRPC_Dual_Submod": folds_e3_preds,
    }
    res85 = {}
    pooled_block_terms85 = {}
    for arm_name, fmap in arms85_preds.items():
        r = holdout.score_folds(lambda fold, m=fmap: m[fold.name], folds85, domain=fp)
        res85[arm_name] = r.as_dict()
        acc_terms = None
        for fold in folds85:
            fake_fold57 = {
                "region": fp,
                "visible": fold.visible,
                "masked_known": fold.visible,
                "truth": fold.withheld,
            }
            _, t_f = eh57.evaluate(fmap[fold.name], fake_fold57, fp, block_side=200)
            acc_terms = t_f if acc_terms is None else (acc_terms + t_f)
        pooled_block_terms85[arm_name] = acc_terms

    block_ci85 = eh57.pooled_summary(
        pooled_block_terms85, draws=1000, seed=520810, candidate="E3_PRPC_Dual_Submod"
    )
    for arm_name, d in res85.items():
        b_ci = block_ci85["scores"][arm_name]["ci95"]
        d["spatial_cluster_ci95"] = b_ci
        print(
            f"   [gems85-holdout-v1.0.0] {arm_name:22s}: HOLDOUT-DTI = {d['pooled_holdout_dti']:.5f} "
            f"fold-CI95 [{d['ci95'][0]:.5f}, {d['ci95'][1]:.5f}]  "
            f"cluster-CI95 [{b_ci[0]:.5f}, {b_ci[1]:.5f}]"
        )

    res = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": holdout.EVALUATOR_VERSION,
        "withheld_positive_pixels": int(sum(f.n_withheld for f in folds85)),
        "mean_withheld_auc": {
            "E1_PRPC_Unsupervised": round(float(np.mean(aucs_e1_85)), 5),
            "E2_PRPC_Blind_OOF": round(float(np.mean(aucs_e2_85)), 5),
            "E3_PRPC_Dual_Submod": round(float(np.mean(aucs_e3_85)), 5),
        },
        "arms": res85,
        "paired_spatial_cluster_summary": block_ci85,
        "static_registry_reference_note": {
            "d28_static_holdout_dti": 0.11153,
            "irregularity_ref": "IR-85-008",
            "explanation": "d28 (B=0) retains 100 m proximity dots next to fold.withheld whereas B=2 (200 m) methods zero visible faults to 200 m; matching or beating d28 under fold-proper B=2 is strictly stronger.",
        },
    }
    (EVIDENCE_DIR / "prpc_gems85.json").write_text(json.dumps(res, indent=2) + "\n")
    return res


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("canary", "gems57", "gems85", "merge", "all"), default="all")
    args = parser.parse_args()

    t0 = time.time()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    fp = grid.footprint()
    cat = grid.catalogue() & fp
    bundle = prpc.build_or_load_blind_bundle(fp, cache_dir=CACHE_DIR)
    print(f"[{time.time()-t0:6.1f}s] BlindStackBundle shape={bundle.X_fp.shape}")

    folds57, _ = ho57.buffered_component_draw(
        SimpleNamespace(catalogue=cat, footprint=fp), seed=20, hide_frac=0.20, buffer_px=3
    )
    folds85 = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5, seed=20261022)

    canary_path = EVIDENCE_DIR / "prpc_leakage_canary.json"
    if args.stage in ("canary", "all") or not canary_path.exists():
        print("Running single-feature Leakage Canary across all 64 channels ...")
        canary = run_leakage_canary(bundle, fp, folds57, folds85)
    else:
        canary = json.loads(canary_path.read_text())
        assert canary.get("passed") is True and canary.get("max_symmetric_auc", 1.0) <= 0.90
    print(f"[{time.time()-t0:6.1f}s] CANARY PASS: max_symmetric_auc={canary['max_symmetric_auc']:.4f} ({canary['highest_feature']})")

    if args.stage in ("gems57", "all"):
        print("\nRunning Stage gems57-pooled-hide-v2 (4-Quadrant LOQO) ...")
        run_stage_gems57(bundle, fp, cat, t0)

    if args.stage in ("gems85", "all"):
        print("\nRunning Stage gems85-holdout-v1.0.0 (4 Spatial Folds) ...")
        run_stage_gems85(bundle, fp, cat, t0)

    if args.stage in ("merge", "all") or (
        (EVIDENCE_DIR / "prpc_gems57.json").exists() and (EVIDENCE_DIR / "prpc_gems85.json").exists()
    ):
        g57 = json.loads((EVIDENCE_DIR / "prpc_gems57.json").read_text())
        g85 = json.loads((EVIDENCE_DIR / "prpc_gems85.json").read_text())

        hot = fp & (bundle.prpc_score_z >= np.percentile(bundle.prpc_score_z[fp], 99.0))
        strike_bins = np.round(bundle.prpc_strike_rad[hot] / (np.pi / prpc.N_STRIKES)).astype(int) % prpc.N_STRIKES
        hist = np.bincount(strike_bins, minlength=prpc.N_STRIKES).astype(float)
        hist /= max(1.0, hist.sum())
        max_az_share = float(hist.max())

        out_payload = {
            "schema_version": 1,
            "lane_id": "H85-P1",
            "lane_name": "PRPC-Submod",
            "budget_experiments_used": 3,
            "budget_experiments_max": 3,
            "dot_budget": BUDGET,
            "exclude_catalogue_radius_m": 200.0,
            "leakage_canary_summary": {
                "passed": canary["passed"],
                "max_symmetric_auc": canary["max_symmetric_auc"],
                "highest_feature": canary["highest_feature"],
            },
            "gems57_pooled_hide_v2": g57,
            "gems85_holdout_v1": g85,
            "confounder_audit": {
                "n_strike_bins": prpc.N_STRIKES,
                "strike_deg": [round(float(np.rad2deg(a)), 2) for a in prpc.STRIKE_ANGLES_RAD],
                "top1pct_share": [round(float(x), 5) for x in hist],
                "max_single_strike_share": round(max_az_share, 5),
                "passed": max_az_share < 0.35,
            },
            "runtime_s": round(time.time() - t0, 2),
        }
        out_file = EVIDENCE_DIR / "prpc_experiments.json"
        out_file.write_text(json.dumps(out_payload, indent=2) + "\n")
        print(f"\nMerged complete results -> {out_file.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
