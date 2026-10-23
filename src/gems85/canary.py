"""Single-Feature Holdout Leakage Canary (Rule 4 Hard Gate).

Evaluates every static physical feature AND every dynamic fold feature individually
on withheld fault segments (`gems57-pooled-hide-v2`, seeds 20 & 30) BEFORE trusting
any model score. Any feature with symmetric AUC `max(AUC, 1 - AUC) > 0.90` triggers
an immediate hard failure.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from sklearn.metrics import roc_auc_score

from gems57.grid import load_grid
from gems57.holdout import buffered_component_draw

from .paths import EVIDENCE_DIR, resolve_raw_dir
from .physics import FEATURE_DOMAINS


class LeakageCanaryError(RuntimeError):
    """Raised when any single feature violates the max symmetric AUC <= 0.90 gate."""


def _fast_sym_auc(y_bin: np.ndarray, x_val: np.ndarray) -> tuple[float, float]:
    raw_auc = float(roc_auc_score(y_bin, x_val))
    return raw_auc, float(max(raw_auc, 1.0 - raw_auc))


def run_leakage_canary(
    X: np.ndarray,
    feature_names: tuple[str, ...] | list[str],
    footprint: np.ndarray,
    fp_idx: np.ndarray,
    extra_named_vectors: dict[str, np.ndarray] | None = None,
    raw_dir: str | Path | None = None,
    max_allowed_auc: float = 0.90,
    eval_stride: int = 4,
    out_path: Path | None = None,
) -> dict[str, Any]:
    """Run single-feature holdout AUC audit across seeds 20 (K=11,321) and 30 (K=11,342)."""
    t0 = time.time()
    raw = resolve_raw_dir(raw_dir)
    grid = load_grid(raw)

    draws = []
    for seed in (20, 30):
        folds, _quad = buffered_component_draw(grid, seed=seed)
        eval_region = folds[0]["region"] | folds[1]["region"] | folds[2]["region"] | folds[3]["region"]
        masked_known = folds[0]["masked_known"]
        hid = folds[0]["hidden_all"] & eval_region
        eval_mask_fp = (eval_region & ~masked_known).ravel()[fp_idx]
        y_hid_fp = hid.ravel()[fp_idx][eval_mask_fp].astype(np.uint8)
        sub = np.arange(0, y_hid_fp.size, eval_stride, dtype=np.int64)
        draws.append({
            "seed": seed,
            "withheld_positive_pixels": int(hid.sum()),
            "eval_mask_fp": eval_mask_fp,
            "sub": sub,
            "y_sub": y_hid_fp[sub],
        })

    rows = []
    violations = []

    def check_vec(name: str, domain: str, col_fp: np.ndarray) -> None:
        clean = np.nan_to_num(col_fp, nan=0.0, posinf=0.0, neginf=0.0)
        per_seed = {}
        worst_sym = 0.0
        for d in draws:
            vals = clean[d["eval_mask_fp"]][d["sub"]]
            raw_auc, sym_auc = _fast_sym_auc(d["y_sub"], vals)
            per_seed[str(d["seed"])] = {
                "raw_auc": round(raw_auc, 5),
                "symmetric_auc": round(sym_auc, 5),
            }
            worst_sym = max(worst_sym, sym_auc)
        passed = worst_sym <= max_allowed_auc
        rec = {
            "feature": name,
            "domain": domain,
            "seed_20_raw_auc": per_seed["20"]["raw_auc"],
            "seed_20_sym_auc": per_seed["20"]["symmetric_auc"],
            "seed_30_raw_auc": per_seed["30"]["raw_auc"],
            "seed_30_sym_auc": per_seed["30"]["symmetric_auc"],
            "max_symmetric_auc": round(worst_sym, 5),
            "passed": passed,
        }
        rows.append(rec)
        if not passed:
            violations.append(rec)

    for j, fname in enumerate(feature_names):
        check_vec(fname, FEATURE_DOMAINS.get(fname, "static"), np.asarray(X[:, j], dtype=np.float32))

    if extra_named_vectors:
        for fname, vec in extra_named_vectors.items():
            check_vec(fname, "dynamic_fold_physics", np.asarray(vec, dtype=np.float32))

    rows.sort(key=lambda r: r["max_symmetric_auc"], reverse=True)
    report = {
        "schema_version": "gems85-leakage-canary-v1",
        "evidence_class": "LEAKAGE-CANARY",
        "evaluator_id": "gems57-pooled-hide-v2",
        "seeds": [20, 30],
        "withheld_positive_pixels": {"seed_20": draws[0]["withheld_positive_pixels"], "seed_30": draws[1]["withheld_positive_pixels"]},
        "max_allowed_symmetric_auc": max_allowed_auc,
        "features_checked": len(rows),
        "max_observed_symmetric_auc": rows[0]["max_symmetric_auc"] if rows else 0.0,
        "top_feature": rows[0]["feature"] if rows else None,
        "violations_count": len(violations),
        "passed": len(violations) == 0,
        "elapsed_seconds": round(time.time() - t0, 2),
        "features": rows,
    }
    dest = out_path or (EVIDENCE_DIR / "leakage_canary.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2) + "\n")
    if violations:
        raise LeakageCanaryError(
            f"Leakage canary FAILED on {len(violations)} feature(s) (> {max_allowed_auc}): "
            + ", ".join(f"{v['feature']}={v['max_symmetric_auc']}" for v in violations)
        )
    return report
