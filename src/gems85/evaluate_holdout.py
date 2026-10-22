"""Protocol holdout evaluator (PARALLEL-RUN PROTOCOL §2, GEMSDOE85 implementation).

Hide-and-recover, exactly as specified in the session brief:
  * withhold WHOLE fault segments (8-connected components of ``labels.tif``) with a buffer;
  * every catalogue-based feature is derived only from the VISIBLE faults
    (in this lane the detector features contain no catalogue-derived channel at all;
    the only catalogue uses are (a) training labels and (b) the visible-fault masks,
    both recomputed per fold from visible faults only);
  * visible faults are masked PIXEL-EXACTLY in scoring (``known=visible``);
  * score POOLED DTI: alpha=0.2, beta=0.8, 300 m (3 px) triangular kernel,
    TP/FP/n_truth summed over all cells before the ratio is taken.

Cells = 4 spatial quadrants x 2 draws (seeds 20, 21).  The 95% CI is a cluster
bootstrap over the 8 cells (2000 resamples, seed 85) — labelled as such everywhere
it is reported; it is not a segment-level CI.

Evaluator version string: ``gems85-pooled-hide-v1``.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field

import numpy as np
from scipy import ndimage

from . import metric as M

EVALUATOR_VERSION = "gems85-pooled-hide-v1"
BUFFER_PX = 15          # 1.5 km buffer around withheld segments (excluded from training)
HIDE_FRAC = 0.20        # fraction of each quadrant's catalogue pixels withheld per draw
DRAWS = (20, 21)


def quadrant_ids(footprint: np.ndarray) -> np.ndarray:
    yy, xx = np.nonzero(footprint)
    ym, xm = int(np.median(yy)), int(np.median(xx))
    H, W = footprint.shape
    gy, gx = np.ogrid[:H, :W]
    q = np.full((H, W), -1, np.int8)
    q[(gy < ym) & (gx < xm) & footprint] = 0
    q[(gy < ym) & (gx >= xm) & footprint] = 1
    q[(gy >= ym) & (gx < xm) & footprint] = 2
    q[(gy >= ym) & (gx >= xm) & footprint] = 3
    return q


@dataclass
class Cell:
    key: str
    fold: int
    draw: int
    test_domain: np.ndarray      # quadrant pixels (footprint only)
    withheld: np.ndarray         # withheld segment pixels (truth)
    visible: np.ndarray          # all other catalogue pixels (masked pixel-exactly)
    train_mask: np.ndarray       # where a fold model may train (no test quad, no buffer)


@dataclass
class Holdout:
    foot: np.ndarray
    labels: np.ndarray
    quad: np.ndarray
    cells: list = dc_field(default_factory=list)


def make_holdout(labels: np.ndarray, foot: np.ndarray) -> Holdout:
    labels = labels & foot
    quad = quadrant_ids(foot)
    comp, n_comp = ndimage.label(labels, structure=np.ones((3, 3), int))
    comp_size = np.bincount(comp.ravel(), minlength=n_comp + 1)
    # component -> dominant quadrant (by pixel count)
    cells: list[Cell] = []
    for draw in DRAWS:
        for fold in range(4):
            qmask = quad == fold
            ids_in = np.unique(comp[qmask & labels])
            ids_in = ids_in[ids_in > 0]
            rng = np.random.default_rng(10_000 * (draw + 1) + fold)
            perm = rng.permutation(ids_in)
            target = HIDE_FRAC * float((labels & qmask).sum())
            cum = np.cumsum(comp_size[perm])
            k = int(np.searchsorted(cum, target)) + 1
            withheld_ids = perm[: min(k, perm.size)]
            withheld = np.isin(comp, withheld_ids) & labels
            visible = labels & ~withheld
            buffer = ndimage.binary_dilation(withheld, iterations=BUFFER_PX)
            train_mask = foot & ~qmask & ~buffer
            cells.append(Cell(key=f"draw{draw}_fold{fold}", fold=fold, draw=draw,
                              test_domain=qmask & foot, withheld=withheld,
                              visible=visible, train_mask=train_mask))
    return Holdout(foot=foot, labels=labels, quad=quad, cells=cells)


def score_mask_pooled(mask: np.ndarray, holdout: Holdout) -> dict:
    """Score one global candidate mask on every cell; return pooled DTI + per-cell parts."""
    mask = np.asarray(mask, bool)
    per_cell = {}
    TP = FP = G = 0.0
    emitted_total = 0
    for cell in holdout.cells:
        pred_cell = mask & cell.test_domain
        r = M.dti_binary(pred_cell, cell.withheld, valid=cell.test_domain,
                         known=cell.visible)
        per_cell[cell.key] = dict(tp=r["tp"], fp=r["fp"], n_truth=r["n_truth"],
                                  dti=r["dti"], emitted=int(pred_cell.sum()))
        TP += r["tp"]; FP += r["fp"]; G += r["n_truth"]
        emitted_total += int(pred_cell.sum())
    pooled = TP / (M.ALPHA * (TP + FP) + M.BETA * G + M.EPS) if G > 0 else 0.0
    # cluster bootstrap over cells
    keys = list(per_cell)
    rng = np.random.default_rng(85)
    boots = []
    tp_arr = np.array([per_cell[k]["tp"] for k in keys])
    fp_arr = np.array([per_cell[k]["fp"] for k in keys])
    g_arr = np.array([per_cell[k]["n_truth"] for k in keys], float)
    for _ in range(2000):
        idx = rng.integers(0, len(keys), len(keys))
        t, f, g = tp_arr[idx].sum(), fp_arr[idx].sum(), g_arr[idx].sum()
        boots.append(t / (M.ALPHA * (t + f) + M.BETA * g + M.EPS))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return dict(evaluator=EVALUATOR_VERSION, pooled_dti=float(pooled),
                ci95=[float(lo), float(hi)], tp=float(TP), fp=float(FP),
                n_withheld_positives=int(G), emitted_in_cells=int(emitted_total),
                per_cell=per_cell)


def score_fold_masks(fold_masks: dict, holdout: Holdout) -> dict:
    """Score per-cell masks (key -> mask restricted to that cell's test domain)."""
    per_cell = {}
    TP = FP = G = 0.0
    emitted_total = 0
    for cell in holdout.cells:
        pred_cell = np.asarray(fold_masks[cell.key], bool) & cell.test_domain
        r = M.dti_binary(pred_cell, cell.withheld, valid=cell.test_domain,
                         known=cell.visible)
        per_cell[cell.key] = dict(tp=r["tp"], fp=r["fp"], n_truth=r["n_truth"],
                                  dti=r["dti"], emitted=int(pred_cell.sum()))
        TP += r["tp"]; FP += r["fp"]; G += r["n_truth"]
        emitted_total += int(pred_cell.sum())
    pooled = TP / (M.ALPHA * (TP + FP) + M.BETA * G + M.EPS) if G > 0 else 0.0
    keys = list(per_cell)
    rng = np.random.default_rng(85)
    tp_arr = np.array([per_cell[k]["tp"] for k in keys])
    fp_arr = np.array([per_cell[k]["fp"] for k in keys])
    g_arr = np.array([per_cell[k]["n_truth"] for k in keys], float)
    boots = []
    for _ in range(2000):
        idx = rng.integers(0, len(keys), len(keys))
        t, f, g = tp_arr[idx].sum(), fp_arr[idx].sum(), g_arr[idx].sum()
        boots.append(t / (M.ALPHA * (t + f) + M.BETA * g + M.EPS))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return dict(evaluator=EVALUATOR_VERSION, pooled_dti=float(pooled),
                ci95=[float(lo), float(hi)], tp=float(TP), fp=float(FP),
                n_withheld_positives=int(G), emitted_in_cells=int(emitted_total),
                per_cell=per_cell)
