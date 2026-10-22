"""Distance-weighted Tversky evaluator used by the local holdout."""
from __future__ import annotations

import math

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA = 0.2
BETA = 0.8
RADIUS_PX = 3.0  # 300 m at the 100 m competition grid
RADIUS_M = 300.0
EPS = 1e-12
EVALUATOR_VERSION = "GEMSDOE85-evaluate_holdout.py-v1 (alpha=0.2 beta=0.8 R=300m triangular)"


def kernel(distance: np.ndarray | float, radius: float = RADIUS_PX) -> np.ndarray:
    return np.maximum(1.0 - np.asarray(distance, dtype=np.float64) / radius, 0.0)


def dti_from_components(tp: float, fp: float, fn: float) -> float:
    return float(tp / (tp + ALPHA * fp + BETA * fn + EPS))


def dti_binary(prediction: np.ndarray, truth: np.ndarray, valid: np.ndarray | None = None) -> dict:
    """Evaluate binary predictions with the competition's triangular distance kernel."""
    # Copy because the optional valid mask must not mutate the caller's arrays;
    # quadrant diagnostics call this function repeatedly on one prediction.
    pred = np.asarray(prediction, dtype=bool).copy()
    truth = np.asarray(truth, dtype=bool).copy()
    if valid is not None:
        valid = np.asarray(valid, dtype=bool)
        pred &= valid
        truth &= valid
    n_truth = int(truth.sum())
    n_pred = int(pred.sum())
    if n_truth == 0:
        return {"TP_w": 0.0, "FP_w": float(n_pred), "FN_w": 0.0, "DTI": 0.0}
    if n_pred == 0:
        return {"TP_w": 0.0, "FP_w": 0.0, "FN_w": float(n_truth), "DTI": 0.0}

    dist_to_pred = distance_transform_edt(~pred)
    tp = float(kernel(dist_to_pred[truth]).sum())
    fn = float(n_truth) - tp
    dist_to_truth = distance_transform_edt(~truth)
    fp = float(np.where(dist_to_truth[pred] < RADIUS_PX, dist_to_truth[pred] / RADIUS_PX, 1.0).sum())
    return {"TP_w": tp, "FP_w": fp, "FN_w": fn, "DTI": dti_from_components(tp, fp, fn)}


def dti_continuous(prediction: np.ndarray, truth: np.ndarray, valid: np.ndarray | None = None) -> dict:
    """Evaluate [0,1] predictions; useful for diagnostics, not a promotion score."""
    p = np.where(np.isfinite(prediction), np.clip(prediction, 0.0, 1.0), 0.0).astype(np.float64)
    g = np.asarray(truth, dtype=bool)
    if valid is not None:
        valid = np.asarray(valid, dtype=bool)
        p = np.where(valid, p, 0.0)
        g &= valid
    pos = p > 0.0
    n_truth = int(g.sum())
    if n_truth == 0:
        return {"TP_w": 0.0, "FP_w": float(p[pos].sum()), "FN_w": 0.0, "DTI": 0.0}
    if not pos.any():
        return {"TP_w": 0.0, "FP_w": 0.0, "FN_w": float(n_truth), "DTI": 0.0}

    local_max = np.zeros_like(p, dtype=np.float64)
    r = int(math.ceil(RADIUS_PX))
    padded = np.pad(p, r, mode="constant", constant_values=0.0)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = math.hypot(dy, dx)
            if d < RADIUS_PX:
                local_max = np.maximum(local_max, padded[r + dy:r + dy + p.shape[0], r + dx:r + dx + p.shape[1]] * (1.0 - d / RADIUS_PX))
    tp = float(local_max[g].sum())
    fn = float(n_truth) - tp
    dg = distance_transform_edt(~g)
    fp = float((p[pos] * np.where(dg[pos] < RADIUS_PX, dg[pos] / RADIUS_PX, 1.0)).sum())
    return {"TP_w": tp, "FP_w": fp, "FN_w": fn, "DTI": dti_from_components(tp, fp, fn)}


def auc_mannwhitney(scores: np.ndarray, labels: np.ndarray) -> float:
    """AUC without adding another dependency; ties receive average ranks."""
    s = np.asarray(scores, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int8)
    good = np.isfinite(s) & np.isfinite(y)
    s, y = s[good], y[good]
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    sorted_s = s[order]
    ranks = np.empty(s.size, dtype=np.float64)
    start = 0
    while start < s.size:
        end = start
        while end + 1 < s.size and sorted_s[end + 1] == sorted_s[start]:
            end += 1
        ranks[order[start:end + 1]] = 0.5 * ((start + 1) + (end + 1))
        start = end + 1
    u = float(ranks[y == 1].sum()) - n_pos * (n_pos + 1) / 2.0
    return float(u / (n_pos * n_neg))
