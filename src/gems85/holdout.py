"""Whole-segment buffered hide-and-recover evaluation.

The split is made from connected components of the catalogue.  A held segment
and a three-pixel collar are removed from the visible catalogue before any
catalogue-derived operation.  The evaluator then masks visible catalogue
pixels exactly and scores only the withheld positives.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, label

from .metric import ALPHA, BETA, EVALUATOR_VERSION, dti_binary, dti_from_components, kernel

HOLD_FRAC = 0.30
BUFFER_PX = 3
BOOTSTRAP_N = 1000
BOOTSTRAP_SEED = 20261021


def connected_components(catalogue: np.ndarray) -> tuple[np.ndarray, int]:
    component, n = label(catalogue, structure=np.ones((3, 3), dtype=np.uint8))
    return component.astype(np.int32), int(n)


def withhold_segments(catalogue: np.ndarray, footprint: np.ndarray, hold_frac: float = HOLD_FRAC,
                      buffer_px: int = BUFFER_PX, seed: int = BOOTSTRAP_SEED) -> dict:
    cat = np.asarray(catalogue, dtype=bool) & np.asarray(footprint, dtype=bool)
    component, n_components = connected_components(cat)
    if n_components == 0:
        raise ValueError("catalogue contains no connected components")
    sizes = np.bincount(component.ravel(), minlength=n_components + 1)
    rng = np.random.default_rng(seed)
    order = rng.permutation(np.arange(1, n_components + 1))
    target = float(cat.sum()) * float(hold_frac)
    accumulated = 0
    held_ids: list[int] = []
    for cid in order:
        held_ids.append(int(cid))
        accumulated += int(sizes[cid])
        if accumulated >= target and len(held_ids) >= max(1, int(0.15 * n_components)):
            break
    held = np.isin(component, np.asarray(held_ids, dtype=np.int32))
    hidden_buffer = binary_dilation(held, iterations=int(buffer_px)) if buffer_px else held.copy()
    visible = cat & ~hidden_buffer
    return {
        "n_components": n_components,
        "held_ids": np.asarray(held_ids, dtype=np.int32),
        "component": component,
        "hidden": held & footprint,
        "hidden_buffer": hidden_buffer & footprint,
        "visible": visible,
        "n_hidden_px": int((held & footprint).sum()),
        "n_visible_px": int(visible.sum()),
        "hold_frac_pixels": float((held & footprint).sum()) / float(cat.sum()),
        "hold_frac": float(hold_frac),
        "buffer_px": int(buffer_px),
        "seed": int(seed),
    }


def _voronoi_component_vectors(pred: np.ndarray, split: dict, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return additive TP, FP, FN vectors, one entry for each held component."""
    hidden = split["hidden"] & footprint
    pred = np.asarray(pred, dtype=bool) & footprint
    held_ids = split["held_ids"]
    component = split["component"]
    m = int(held_ids.size)
    lut = np.full(int(component.max()) + 1, -1, dtype=np.int32)
    lut[held_ids] = np.arange(m, dtype=np.int32)

    d_pred = distance_transform_edt(~pred)
    comp_at_truth = lut[component[hidden]]
    tp_vec = np.bincount(comp_at_truth, weights=kernel(d_pred[hidden]), minlength=m).astype(np.float64)
    size_vec = np.bincount(comp_at_truth, minlength=m).astype(np.float64)
    fn_vec = size_vec - tp_vec

    # Assign every prediction cell to its nearest hidden component for additive FP.
    d_hidden, nearest = distance_transform_edt(~hidden, return_indices=True)
    owner = lut[component[nearest[0], nearest[1]]]
    p_rows, p_cols = np.nonzero(pred)
    owner_p = np.clip(owner[p_rows, p_cols], 0, m - 1)
    fp_weights = np.where(d_hidden[p_rows, p_cols] < 3.0, d_hidden[p_rows, p_cols] / 3.0, 1.0)
    fp_vec = np.bincount(owner_p, weights=fp_weights, minlength=m).astype(np.float64)
    return tp_vec, fp_vec, fn_vec


def bootstrap_dti_ci(pred: np.ndarray, split: dict, footprint: np.ndarray,
                     n_boot: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED) -> tuple[float, float]:
    """Multinomial component bootstrap; each held segment remains a cluster."""
    held_ids = split["held_ids"]
    if held_ids.size == 0:
        return (float("nan"), float("nan"))
    tp, fp, fn = _voronoi_component_vectors(pred, split, footprint)
    rng = np.random.default_rng(seed)
    m = int(held_ids.size)
    multiplicity = rng.multinomial(m, np.full(m, 1.0 / m), size=int(n_boot)).astype(np.float64)
    tp_b = multiplicity @ tp
    fp_b = multiplicity @ fp
    fn_b = multiplicity @ fn
    denom = tp_b + ALPHA * fp_b + BETA * fn_b + 1e-12
    scores = np.divide(tp_b, denom, out=np.zeros_like(tp_b), where=denom > 0)
    return float(np.percentile(scores, 2.5)), float(np.percentile(scores, 97.5))


def quadrant_breakdown(pred: np.ndarray, truth: np.ndarray, footprint: np.ndarray) -> dict[str, float]:
    rows, cols = np.nonzero(footprint)
    r_mid = int(np.median(rows))
    c_mid = int(np.median(cols))
    rr, cc = np.indices(footprint.shape)
    masks = {
        "NW": footprint & (rr < r_mid) & (cc < c_mid),
        "NE": footprint & (rr < r_mid) & (cc >= c_mid),
        "SW": footprint & (rr >= r_mid) & (cc < c_mid),
        "SE": footprint & (rr >= r_mid) & (cc >= c_mid),
    }
    return {name: float(dti_binary(pred, truth, valid=mask)["DTI"]) for name, mask in masks.items()}


def score_holdout(prediction: np.ndarray, split: dict, footprint: np.ndarray, bootstrap: bool = True) -> dict:
    """Mask visible faults pixel-exactly, then evaluate only held segments."""
    pred = np.asarray(prediction, dtype=bool) & footprint & ~split["visible"]
    truth = split["hidden"] & footprint
    result = dti_binary(pred, truth, valid=footprint)
    ci = bootstrap_dti_ci(pred, split, footprint) if bootstrap else None
    return {
        "label": "HOLDOUT-DTI",
        "evaluator_version": EVALUATOR_VERSION,
        "withheld_positive_count": int(truth.sum()),
        "n_components_total": int(split["n_components"]),
        "n_components_held": int(split["held_ids"].size),
        "hold_frac_pixels": float(split["hold_frac_pixels"]),
        "buffer_px": int(split["buffer_px"]),
        "score": float(result["DTI"]),
        "ci95": list(ci) if ci is not None else None,
        "TP_w": float(result["TP_w"]),
        "FP_w": float(result["FP_w"]),
        "FN_w": float(result["FN_w"]),
        "n_pred_after_visible_mask": int(pred.sum()),
        "spatial_quadrant_dti": quadrant_breakdown(pred, truth, footprint),
    }


def leakage_canary(features: dict[str, np.ndarray], split: dict, footprint: np.ndarray,
                    seed: int = 20261021, max_neg: int = 200_000, auc_limit: float = 0.90) -> dict:
    """Evaluate every candidate feature alone before accepting the surface."""
    from .metric import auc_mannwhitney

    evaluation = footprint & ~split["visible"]
    positives = np.flatnonzero((split["hidden"] & evaluation).ravel())
    neg_pool = np.flatnonzero((~split["hidden"] & evaluation).ravel())
    rng = np.random.default_rng(seed)
    negatives = rng.choice(neg_pool, size=min(int(max_neg), int(neg_pool.size)), replace=False)
    indices = np.concatenate([positives, negatives])
    y = np.concatenate([np.ones(positives.size, dtype=np.int8), np.zeros(negatives.size, dtype=np.int8)])
    rows = []
    for name, feature in features.items():
        values = np.nan_to_num(np.asarray(feature).ravel()[indices], nan=0.0, posinf=0.0, neginf=0.0)
        auc = float(auc_mannwhitney(values, y))
        effective = max(auc, 1.0 - auc)
        rows.append({"feature": name, "auc": auc, "effective_auc": effective, "leakage": bool(effective > auc_limit)})
    rows.sort(key=lambda row: row["effective_auc"], reverse=True)
    return {
        "label": "LEAKAGE-CANARY",
        "threshold_auc": float(auc_limit),
        "max_effective_auc": float(rows[0]["effective_auc"]) if rows else float("nan"),
        "flagged_features": [row for row in rows if row["leakage"]],
        "passed": not any(row["leakage"] for row in rows),
        "features": rows,
        "withheld_positive_count_tested": int(positives.size),
        "background_count_tested": int(negatives.size),
    }
