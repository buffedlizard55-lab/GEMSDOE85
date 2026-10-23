#!/usr/bin/env python3
"""Execute the strictly pre-registered 3-experiment H85-TVFV campaign (E85-1..3).

Workflow:
  0. SHA-256 verify all 40 core + external public datasets (`evidence/data_verification.json`).
  1. Build 58-channel static physical stack + 3 OOF Terzaghi-Morris channels (`61` features).
  2. Run Single-Feature Holdout Leakage Canary on ALL 61 features BEFORE training (`AUC <= 0.90`).
  3. Benchmark prior reference rasters (`H33`, `G63`, `G24`, `G70_P8`, `G49`, `H19_5`, etc.) via
     unmodified `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`, pooled seeds 20 & 30).
  4. Run strictly 3 experiments (`E85-1`, `E85-2`, `E85-3`) with strict zero-hidden-segment leakage
     on holdout draws AND full-catalogue training for live submission generation.
  5. Write final validated GeoTIFF + `.zip` + receipt via `vendor/gems57/submission_writer.py` and run
     all 7 automated validation + uniqueness gates across all historical & sibling rasters.
"""
from __future__ import annotations

import gc
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
for sub in (ROOT / "src", ROOT / "vendor"):
    if str(sub) not in sys.path:
        sys.path.insert(0, str(sub))

from gems57.evaluate_holdout import (  # noqa: E402
    VERSION as EVALUATOR_VERSION,
    evaluate,
    from_terms,
    implementation_hashes,
    pooled_summary,
)
from gems57.grid import load_grid  # noqa: E402
from gems57.holdout import buffered_component_draw  # noqa: E402
from gems57.submission_writer import write_submission  # noqa: E402
from gems85.canary import run_leakage_canary  # noqa: E402
from gems85.dinkelbach import (  # noqa: E402
    decode_exact_dinkelbach_300m,
    decode_greedy_fixed_disk_2d,
)
from gems85.forensics_and_audit import (  # noqa: E402
    discover_all_reference_rasters,
    run_full_automated_gates,
    sha256_file,
)
from gems85.models import (  # noqa: E402
    fit_oof_terzaghi_stress,
    fit_predict_stage1_dual_expert,
    fit_predict_stage2_curvilinear,
)
from gems85.paths import (  # noqa: E402
    DOCS_EVIDENCE_DIR,
    DOWNLOADS_DIR,
    EVIDENCE_DIR,
    resolve_raw_dir,
    resolve_work_dir,
)
from gems85.physics import FEATURE_NAMES, build_or_load_feature_stack  # noqa: E402


def main() -> int:
    t_start = time.time()
    raw_dir = resolve_raw_dir()
    work_dir = resolve_work_dir()
    template_tif = raw_dir / "sample_submission.tif"
    existing_tif = raw_dir / "existing_faults.tif"

    # Step 0: SHA-256 data verification
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "prepare_data.py"), "--data-dir", str(raw_dir), "--verify-only"],
        check=True,
    )

    # Step 1: Build or load 58-channel static stack + 3 OOF Terzaghi-Morris dynamic channels
    stack = build_or_load_feature_stack(raw_dir)
    X_static = stack["X"]
    footprint = stack["footprint"]
    fp_idx = stack["fp_idx"]

    c_idx = {n: i for i, n in enumerate(FEATURE_NAMES)}
    X_dyn, dyn_names = fit_oof_terzaghi_stress(
        footprint=footprint,
        fp_idx=fp_idx,
        lid_norm_az_deg=stack["lid_norm_az_deg"],
        multi_norm_az_deg=stack["multi_norm_az_deg"],
        multi_coherence=stack["multi_coherence"],
        lid_valid_fp=np.asarray(X_static[:, c_idx["d1_lid_valid"]], dtype=np.float32),
        hf_1km_fp=np.asarray(X_static[:, c_idx["d5_hf_convective_1km"]], dtype=np.float32),
        geotherm_1km_fp=np.asarray(X_static[:, c_idx["d5_gdr_geotherm_upflow_1km"]], dtype=np.float32),
    )

    # Step 2: Run Single-Feature Holdout Leakage Canary BEFORE training a single model!
    print("[Step 2] Running Single-Feature Holdout Leakage Canary across ALL 61 features...", flush=True)
    canary_report = run_leakage_canary(
        X=X_static,
        feature_names=FEATURE_NAMES,
        footprint=footprint,
        fp_idx=fp_idx,
        extra_named_vectors={dyn_names[i]: X_dyn[:, i] for i in range(len(dyn_names))},
        raw_dir=raw_dir,
        max_allowed_auc=0.90,
    )
    print(
        f"[Step 2 OK] Checked {canary_report['features_checked']} features; "
        f"max symmetric AUC = {canary_report['max_observed_symmetric_auc']:.5f} "
        f"({canary_report['top_feature']}) <= 0.90.",
        flush=True,
    )

    grid = load_grid(raw_dir)
    full_cat_2d = grid.catalogue

    def eval_draw(pred_2d: np.ndarray, fold_list: list[dict[str, Any]]) -> tuple[float, int, np.ndarray]:
        tot_terms = None
        for f_q in fold_list:
            _res_q, t_q = evaluate(pred_2d, f_q, footprint)
            tot_terms = t_q if tot_terms is None else (tot_terms + t_q)
        assert tot_terms is not None
        summed = tot_terms.sum(axis=0)
        return float(from_terms(summed)), int(round(summed[3])), tot_terms

    # Construct unmodified holdout folds for seeds 20 & 30 once so ALL reference and E85 arms
    # are scored on the exact same spatial blocks for paired bootstrap CIs!
    folds = {}
    for s in (20, 30):
        fold_list, _quad = buffered_component_draw(grid, seed=s)
        folds[s] = fold_list

    # Step 3: Benchmark key reference submissions on unmodified `evaluate_holdout.py`
    print("[Step 3] Benchmarking reference submissions on unmodified evaluate_holdout.py...", flush=True)
    ref_rasters = discover_all_reference_rasters(raw_dir, work_dir)
    priority_refs = [
        ("H33_RAW_LIVE_0p2778", "repo::GEMSDOE32::h33-h33-2-b2"),
        ("G24_D28_LIVE_0p2600", "scored::gems24-h25-1-dotted-h19-5-d2-8"),
        ("G63_CVAR_LIVE_0p2683", "repo::GEMSDOE63::gemsdoe63-cvarlw-thin-s3p17-54864"),
        ("G27_GAP_LIVE_0p2287", "scored::gems27-topo-gap-closure"),
        ("H19_5_LIVE_0p1922", "scored::gems19-h19-5-powerlaw"),
        ("H16_1_LIVE_0p1855", "scored::gems16-h16-1-topo-geophys"),
        ("G70_P8_LIVE_0p2478", "repo::GEMSDOE70::"),
        ("G49_GALLARDO_LIVE_0p2376", "repo::GEMSDOE49::"),
    ]
    pooled_terms_by_arm: dict[str, np.ndarray] = {}
    ref_per_seed: dict[str, dict[str, Any]] = {}
    for label, prefix in priority_refs:
        matches = [p for k, p in ref_rasters.items() if k.startswith(prefix)]
        if not matches:
            continue
        rp = matches[0]
        with rasterio.open(rp) as ds:
            arr = ds.read(1).astype(np.float32)
        arr_clean = np.where(footprint & np.isfinite(arr), np.clip(arr, 0.0, 1.0), 0.0)
        dti20, k20, t20 = eval_draw(arr_clean, folds[20])
        dti30, k30, t30 = eval_draw(arr_clean, folds[30])
        pooled_terms_by_arm[label] = t20 + t30
        ref_per_seed[label] = {
            "file": rp.name,
            "sha256": sha256_file(rp),
            "seed_20_dti": round(dti20, 6),
            "seed_20_withheld_positives": k20,
            "seed_30_dti": round(dti30, 6),
            "seed_30_withheld_positives": k30,
        }
        print(f"  [Ref] {label:28s}: seed20={dti20:.5f} (K={k20:,}), seed30={dti30:.5f} (K={k30:,})", flush=True)

    # Also evaluate exact fold-masked H33 rule (`D2.8` masked strictly by `d_vis <= 2.0 px` on each seed,
    # i.e., exact H33 algorithm evaluated cleanly without post-hoc hidden-catalogue erasure!):
    from scipy.ndimage import distance_transform_edt as _edt
    d28_matches = [p for k, p in ref_rasters.items() if k.startswith("scored::gems24-h25-1-dotted-h19-5-d2-8")]
    if d28_matches:
        with rasterio.open(d28_matches[0]) as ds:
            d28_arr = np.where(footprint & np.isfinite(ds.read(1)), np.clip(ds.read(1), 0.0, 1.0), 0.0)
        h33_f20 = np.where(_edt(~folds[20][0]["visible"]) > 2.0, d28_arr, 0.0)
        h33_f30 = np.where(_edt(~folds[30][0]["visible"]) > 2.0, d28_arr, 0.0)
        dti20_h33f, k20_h, t20_h = eval_draw(h33_f20, folds[20])
        dti30_h33f, k30_h, t30_h = eval_draw(h33_f30, folds[30])
        pooled_terms_by_arm["H33_FOLD_EQUIVALENT_0p2778"] = t20_h + t30_h
        ref_per_seed["H33_FOLD_EQUIVALENT_0p2778"] = {
            "file": "gems24-d2.8 + fold-clean H33 (d_vis > 2.0px) dead-zone filter",
            "sha256": sha256_file(d28_matches[0]),
            "seed_20_dti": round(dti20_h33f, 6),
            "seed_20_withheld_positives": k20_h,
            "seed_30_dti": round(dti30_h33f, 6),
            "seed_30_withheld_positives": k30_h,
        }
        print(f"  [Ref] {'H33_FOLD_EQUIVALENT_0p2778':28s}: seed20={dti20_h33f:.5f} (K={k20_h:,}), seed30={dti30_h33f:.5f} (K={k30_h:,})", flush=True)

    def get_or_fit_stages(tag: str, known_2d: np.ndarray, s1_seed: int, s2_seed: int) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
        cache_f = work_dir / f"oof_stages_{tag}.npz"
        meta_f = work_dir / f"oof_stages_{tag}_meta.json"
        if cache_f.exists() and meta_f.exists():
            z = np.load(cache_f)
            return z["s1"], z["s2"], json.loads(meta_f.read_text())
        s1, m1 = fit_predict_stage1_dual_expert(X_static, X_dyn, dyn_names, footprint, fp_idx, known_2d, seed=s1_seed)
        s2, _m2 = fit_predict_stage2_curvilinear(
            s1, m1["expert_a_fp"], m1["expert_b_fp"], X_static, X_dyn, footprint, fp_idx, known_2d, seed=s2_seed
        )
        m_save = {k: v for k, v in m1.items() if k not in ("expert_a_fp", "expert_b_fp")}
        np.savez(cache_f, s1=s1.astype(np.float32), s2=s2.astype(np.float32))
        meta_f.write_text(json.dumps(m_save, indent=2) + "\n")
        return s1, s2, m_save

    # Calibrate Dinkelbach scalar `M` STRICTLY on separate tuning draw `seed=10` (NEVER touching 20 or 30)!
    print("[Pre-Exp Calibration] Tuning scalar M strictly on held-aside seed=10...", flush=True)
    folds10, _ = buffered_component_draw(grid, seed=10)
    vis10 = folds10[0]["visible"]
    s1_10, s2_10, _info1_10 = get_or_fit_stages("seed10_pure_v1", vis10, 850, 950)
    best_m_cfg = None
    best_s10_score = -1.0
    for m_cand, gam_cand in ((26500.0, 0.91), (28500.0, 0.96), (31500.0, 1.03)):
        sub10, meta10 = decode_exact_dinkelbach_300m(
            s2_10, footprint, vis10, expected_fault_mass_m=m_cand, gamma_power=gam_cand, n_outer_iters=3, swap_passes=1
        )
        dti10, k10, _ = eval_draw(sub10, folds10)
        print(
            f"  [Seed=10 Tune] M={m_cand:.0f}, gamma={gam_cand:.2f} -> dots={meta10['placed_dots']:,}, "
            f"seed10_HOLDOUT_DTI={dti10:.6f} (K={k10:,})",
            flush=True,
        )
        if dti10 > best_s10_score:
            best_s10_score = dti10
            best_m_cfg = (m_cand, gam_cand, meta10["placed_dots"])

    m_star, gam_star, target_n_dots = best_m_cfg
    del s1_10, s2_10
    gc.collect()
    print(f"[Locked Pre-Test Hyperparameters from Seed=10] M*={m_star:.0f}, gamma*={gam_star:.2f}, N_greedy={target_n_dots:,}", flush=True)

    # =========================================================================
    # STRICT 3-EXPERIMENT CAMPAIGN ON SEEDS 20 & 30 (ZERO HIDDEN-LABEL LEAKAGE!)
    # =========================================================================
    exp_records: dict[str, dict[str, Any]] = {
        "E85-1": {
            "experiment_id": "E85-1",
            "name": "Stage-1 61-Channel H85-TVFV Dual-Expert Slope-Deconfounded LOQO + Greedy 2.8px Disk",
            "hypothesis_tested": "H85-1..4 (90deg-fixed 1m LiDAR + 10m 3DEP seam harmonization + 3D polar hanging-wall dipoles + OOF Terzaghi-Morris + borehole convective heat flow & silica geothermometry)",
            "seeds": {},
        },
        "E85-2": {
            "experiment_id": "E85-2",
            "name": "E85-1 + Stage-2 Out-of-Quadrant 12-Azimuth Multi-Scale Steerable Curvilinear Propagation (100% Zero-Catalogue Features) + Greedy 2.8px Disk",
            "hypothesis_tested": "H85-5a (0.7/1.7/3.5 km steerable line-integral vs bilateral flank inhibition + Bayes empirical regime tail calibration across 1m-LiDAR seam & mountain slope)",
            "seeds": {},
        },
        "E85-3": {
            "experiment_id": "E85-3",
            "name": "E85-2 + Exact Fractional Dinkelbach 300 m Expected-DTI Solver (Minoux CELF + Exact O(29x29) Prune & 1-Swap Coordinate Ascent)",
            "hypothesis_tested": "H85-5b (Variable posterior-adaptive submodular dot packing under exact alpha=0.2, beta=0.8, R=300 m triangular kernel)",
            "seeds": {},
        },
    }
    exp_terms = {eid: None for eid in ("E85-1", "E85-2", "E85-3")}

    for hold_seed in (20, 30):
        print(f"\n[Holdout Seed {hold_seed}] Training strictly on VISIBLE faults (0 hidden pixels seen in training!)...", flush=True)
        vis_s = folds[hold_seed][0]["visible"]
        hid_s = folds[hold_seed][0]["hidden_all"]
        assert int((vis_s & hid_s).sum()) == 0

        s1_s, s2_s, _s1_meta_s = get_or_fit_stages(f"seed{hold_seed}_pure_v1", vis_s, 85 + hold_seed, 185 + hold_seed)
        # Experiment E85-1
        sub_e1, dec_e1 = decode_greedy_fixed_disk_2d(
            s1_s, footprint, vis_s, n_dots=target_n_dots, min_spacing_px=2.8, dead_zone_px=2.0
        )
        dti_e1, k_e1, t_e1 = eval_draw(sub_e1, folds[hold_seed])
        exp_terms["E85-1"] = t_e1 if exp_terms["E85-1"] is None else (exp_terms["E85-1"] + t_e1)
        exp_records["E85-1"]["seeds"][str(hold_seed)] = {"dti": round(dti_e1, 6), "n_truth": k_e1, "decoder": dec_e1}
        print(f"  [E85-1 | seed={hold_seed}] HOLDOUT-DTI = {dti_e1:.6f} (K={k_e1:,}, dots={dec_e1['placed_dots']:,})", flush=True)

        # Experiment E85-2
        sub_e2, dec_e2 = decode_greedy_fixed_disk_2d(
            s2_s, footprint, vis_s, n_dots=target_n_dots, min_spacing_px=2.8, dead_zone_px=2.0
        )
        dti_e2, k_e2, t_e2 = eval_draw(sub_e2, folds[hold_seed])
        exp_terms["E85-2"] = t_e2 if exp_terms["E85-2"] is None else (exp_terms["E85-2"] + t_e2)
        exp_records["E85-2"]["seeds"][str(hold_seed)] = {"dti": round(dti_e2, 6), "n_truth": k_e2, "decoder": dec_e2}
        print(f"  [E85-2 | seed={hold_seed}] HOLDOUT-DTI = {dti_e2:.6f} (K={k_e2:,}, dots={dec_e2['placed_dots']:,})", flush=True)

        # Experiment E85-3
        sub_e3, dec_e3 = decode_exact_dinkelbach_300m(
            s2_s, footprint, vis_s, expected_fault_mass_m=m_star, gamma_power=gam_star, n_outer_iters=3, swap_passes=2
        )
        dti_e3, k_e3, t_e3 = eval_draw(sub_e3, folds[hold_seed])
        exp_terms["E85-3"] = t_e3 if exp_terms["E85-3"] is None else (exp_terms["E85-3"] + t_e3)
        exp_records["E85-3"]["seeds"][str(hold_seed)] = {"dti": round(dti_e3, 6), "n_truth": k_e3, "decoder": dec_e3}
        print(f"  [E85-3 | seed={hold_seed}] HOLDOUT-DTI = {dti_e3:.6f} (K={k_e3:,}, dots={dec_e3['placed_dots']:,})", flush=True)

        del s1_s, s2_s
        gc.collect()

    for eid in ("E85-1", "E85-2", "E85-3"):
        pooled_terms_by_arm[eid] = exp_terms[eid]

    # Compute exact pooled summary + 1,000-draw 20 km spatial-cluster paired bootstrap CIs!
    prelim = pooled_summary(exp_terms, draws=1000, candidate="E85-3")
    winner_id = max(("E85-1", "E85-2", "E85-3"), key=lambda k: prelim["scores"][k]["dti"])
    full_pooled = pooled_summary(pooled_terms_by_arm, draws=1000, candidate=winner_id)

    for eid in ("E85-1", "E85-2", "E85-3"):
        sc = full_pooled["scores"][eid]
        exp_records[eid]["pooled_holdout_dti"] = round(sc["dti"], 6)
        exp_records[eid]["pooled_ci95"] = [round(x, 6) for x in sc["ci95"]]
        exp_records[eid]["withheld_positive_pixels"] = sc["withheld_positive_pixels"]
        print(
            f"[Pooled K={sc['withheld_positive_pixels']:,}] {eid}: HOLDOUT-DTI = {sc['dti']:.6f} "
            f"(95% CI [{sc['ci95'][0]:.6f}, {sc['ci95'][1]:.6f}])",
            flush=True,
        )

    print(f"\n[Winner Selected] {winner_id}!", flush=True)

    # Step 5: Fit full-catalogue LOQO posterior & emit final live GeoTIFF + ZIP via submission_writer.py!
    print("[Step 5] Fitting full-catalogue Out-of-Quadrant posterior for live submission generation...", flush=True)
    s1_full, s2_full, s1_full_meta = get_or_fit_stages("full_pure_v1", full_cat_2d, 85, 185)
    if winner_id == "E85-1":
        final_surface = s1_full
        final_sub, final_dec_meta = decode_greedy_fixed_disk_2d(
            s1_full, footprint, full_cat_2d, n_dots=target_n_dots, min_spacing_px=2.8, dead_zone_px=2.0
        )
    elif winner_id == "E85-2":
        final_surface = s2_full
        final_sub, final_dec_meta = decode_greedy_fixed_disk_2d(
            s2_full, footprint, full_cat_2d, n_dots=target_n_dots, min_spacing_px=2.8, dead_zone_px=2.0
        )
    else:
        final_surface = s2_full
        final_sub, final_dec_meta = decode_exact_dinkelbach_300m(
            s2_full, footprint, full_cat_2d,
            expected_fault_mass_m=m_star, gamma_power=gam_star, n_outer_iters=3, swap_passes=2
        )

    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    sub_stem = f"gems85-h85-tvfv-{winner_id.lower()}-20261022-zeros"
    sub_tif = DOWNLOADS_DIR / f"{sub_stem}.tif"
    for old_ext in (".tif", ".zip", ".json"):
        p_old = sub_tif.with_suffix(old_ext)
        if p_old.exists():
            p_old.unlink()

    sub_note = (
        f"GEMSDOE85 {winner_id}: 90deg-fixed 1m/10m scarp + 3D dipole + OOF Terzaghi valve + Dinkelbach 300m"
    )
    assert len(sub_note) <= 140
    write_receipt = write_submission(
        path=sub_tif,
        prediction=final_sub,
        sample=template_tif,
        footprint=footprint,
        note=sub_note,
        name=sub_stem,
        catalogue=full_cat_2d,
        metadata={"lane_id": "H85-TVFV", "winner_experiment": winner_id},
    )
    for ext in (".tif", ".zip", ".json"):
        sub_tif.with_suffix(ext).chmod(0o644)

    # Also evaluate the exact emitted live GeoTIFF via CLI (`scripts/evaluate_holdout.py`)!
    cli_json_path = EVIDENCE_DIR / "cli_evaluate_holdout_receipt.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_holdout.py"),
            "--prediction",
            str(sub_tif),
            "--existing-faults",
            str(existing_tif),
            "--template",
            str(template_tif),
            "--seeds",
            "20",
            "30",
            "--draws",
            "1000",
            "--out",
            str(cli_json_path),
        ],
        check=True,
    )
    cli_live_eval = json.loads(cli_json_path.read_text())

    h33_key = "H33_FOLD_EQUIVALENT_0p2778" if "H33_FOLD_EQUIVALENT_0p2778" in full_pooled["scores"] else "H33_RAW_LIVE_0p2778"
    h33_score = full_pooled["scores"][h33_key]["dti"]
    winner_score = full_pooled["scores"][winner_id]["dti"]

    holdout_summary = {
        "schema_version": "gems85-experiments-summary-v1",
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": EVALUATOR_VERSION,
        "implementation_sha256": implementation_hashes(),
        "strict_budget_experiments_run": 3,
        "winner_experiment_id": winner_id,
        "mean_holdout_dti": round(winner_score, 6),
        "pooled_ci95": [round(x, 6) for x in full_pooled["scores"][winner_id]["ci95"]],
        "withheld_positive_pixels": full_pooled["scores"][winner_id]["withheld_positive_pixels"],
        "h33_reference_key": h33_key,
        "h33_reference_holdout_dti": round(h33_score, 6),
        "delta_vs_h33_holdout_dti": round(full_pooled["paired_differences"][h33_key]["delta"], 6),
        "delta_vs_h33_ci95": [round(x, 6) for x in full_pooled["paired_differences"][h33_key]["ci95"]],
        "live_emitted_raster_cli_holdout": cli_live_eval["scores"]["candidate"],
        "seed10_pre_test_calibration": {
            "seed": 10,
            "m_star": m_star,
            "gamma_star": gam_star,
            "target_n_dots": target_n_dots,
            "seed10_holdout_dti": round(best_s10_score, 6),
        },
        "experiments": exp_records,
        "pooled_all_arms": full_pooled,
        "reference_per_seed": ref_per_seed,
        "stage1_top_features": s1_full_meta["top_15_features"],
        "final_decoder_metadata": final_dec_meta,
        "submission_receipt": write_receipt,
        "total_runtime_seconds": round(time.time() - t_start, 2),
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "experiments_holdout_summary.json").write_text(json.dumps(holdout_summary, indent=2) + "\n")

    # Step 6: Run ALL 7 Automated Pre-Submission & Uniqueness Gates!
    audit_report = run_full_automated_gates(
        submission_path=sub_tif,
        surface_2d=final_surface,
        raw_dir=raw_dir,
        work_dir=work_dir,
        canary_report=canary_report,
        holdout_summary=holdout_summary,
    )
    np.save(work_dir / "final_surface_2d.npy", final_surface.astype(np.float32))
    print(f"\n[AUTOMATED GATE VERDICT] {audit_report['verdict']}", flush=True)
    for gname, ginfo in audit_report["gates"].items():
        print(f"  [{'PASS' if ginfo['passed'] else 'FAIL'}] {gname}: {ginfo['detail']}", flush=True)
    print(f"[Total Runtime] {time.time() - t_start:.1f}s ({(time.time() - t_start)/60.0:.2f} min)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
