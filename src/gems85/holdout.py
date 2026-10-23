"""Hide-and-recover holdout: the only instrument this repo is allowed to quote.

Protocol (fixed before any candidate was written; see registry/preregistration.json):

  1. The given catalogue is split into connected fault **segments** (8-connectivity).
  2. Segments are assigned to folds by **spatial block**, so a whole region of the map is
     hidden at once -- never individual pixels, never a random scatter.
  3. For each fold: `withheld` = that fold's segments.  Every catalogue pixel within
     `buffer_px` of a withheld pixel is *also* removed from `visible` (the buffer stops an
     adjacent visible pixel from trivially revealing the hidden trace).
  4. Any catalogue-derived feature is recomputed from `visible` only.
  5. The candidate prediction is masked to 0 **pixel-exactly on `visible`** -- mass on a
     known fault earns nothing and is charged alpha, exactly as the live scorer charges it.
  6. The fold's DTI uses truth = `withheld`, domain = the survey footprint.
  7. Folds are pooled: TP_w, FP_w, FN_w are summed across folds and ONE DTI is formed from
     the pooled sums ("pooled DTI"), so a tiny fold cannot dominate the mean.

Every number produced here is a HOLDOUT-DTI proxy. It is never an organizer score.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from . import grid
from .metric import ALPHA, BETA, dti, kernel_dilate

EVALUATOR_VERSION = "gems85-holdout-v1.0.0"


@dataclass
class Fold:
    name: str
    withheld: np.ndarray            # bool, truth for this fold
    visible: np.ndarray             # bool, catalogue the method is allowed to see
    n_withheld: int
    n_visible: int


@dataclass
class FoldScore:
    name: str
    dti: float
    tp_w: float
    fp_w: float
    fn_w: float
    n_truth: int
    pred_pixels: int


@dataclass
class HoldoutResult:
    evaluator_version: str
    pooled_dti: float
    tp_w: float
    fp_w: float
    fn_w: float
    n_withheld_positives: int
    folds: list[FoldScore] = field(default_factory=list)
    ci95: tuple[float, float] = (float("nan"), float("nan"))

    def as_dict(self) -> dict:
        return {
            "evaluator_version": self.evaluator_version,
            "pooled_holdout_dti": self.pooled_dti,
            "ci95": list(self.ci95),
            "n_withheld_positives": self.n_withheld_positives,
            "tp_w": self.tp_w, "fp_w": self.fp_w, "fn_w": self.fn_w,
            "folds": [f.__dict__ for f in self.folds],
        }


def make_folds(
    catalogue: np.ndarray,
    *,
    n_folds: int = 4,
    block_px: int = 200,
    buffer_px: int = 5,
    seed: int = 20261022,
) -> list[Fold]:
    """Spatially-blocked, segment-level folds. Deterministic in `seed`."""
    cat = catalogue.astype(bool)
    lab, n_seg = ndi.label(cat, structure=np.ones((3, 3), dtype=int))
    if n_seg == 0:
        raise ValueError("empty catalogue")

    # Segment centroid -> coarse spatial block -> fold.
    cy, cx = np.array(ndi.center_of_mass(cat, lab, range(1, n_seg + 1))).T
    by = (cy // block_px).astype(int)
    bx = (cx // block_px).astype(int)
    n_bx = int(bx.max()) + 1
    block_id = by * n_bx + bx

    rng = np.random.default_rng(seed)
    uniq = np.unique(block_id)
    block_fold = {b: int(f) for b, f in zip(uniq, rng.permutation(len(uniq)) % n_folds)}
    seg_fold = np.array([block_fold[b] for b in block_id])

    folds: list[Fold] = []
    struct = np.ones((3, 3), dtype=bool)
    for f in range(n_folds):
        keep = np.isin(lab, np.nonzero(seg_fold == f)[0] + 1)
        withheld = keep & cat
        if buffer_px > 0:
            halo = ndi.binary_dilation(withheld, structure=struct, iterations=buffer_px)
        else:
            halo = withheld
        visible = cat & ~halo
        folds.append(Fold(f"fold{f}", withheld, visible, int(withheld.sum()), int(visible.sum())))
    return folds


def score_folds(
    surface_fn,
    folds: list[Fold],
    *,
    domain: np.ndarray,
    alpha: float = ALPHA,
    beta: float = BETA,
) -> HoldoutResult:
    """`surface_fn(fold) -> float array in [0,1]` is called once per fold.

    The function must build its prediction using ONLY `fold.visible` for anything
    catalogue-derived.  Masking on `visible` and the domain restriction are applied here,
    so a candidate cannot forget them.
    """
    tp = fp = fn = 0.0
    n_pos = 0
    out: list[FoldScore] = []
    for fold in folds:
        pred = np.asarray(surface_fn(fold), dtype=np.float64)
        pred = np.nan_to_num(pred, nan=0.0, posinf=0.0, neginf=0.0)
        pred = np.clip(pred, 0.0, 1.0)
        pred[fold.visible] = 0.0                      # step 5: pixel-exact mask
        pred = np.where(domain, pred, 0.0)
        r = dti(pred, fold.withheld, domain=domain, alpha=alpha, beta=beta)
        out.append(FoldScore(fold.name, r.dti, r.tp_w, r.fp_w, r.fn_w, r.n_truth, r.pred_pixels))
        tp += r.tp_w; fp += r.fp_w; fn += r.fn_w; n_pos += r.n_truth
    pooled = tp / (tp + alpha * fp + beta * fn) if (tp + alpha * fp + beta * fn) > 0 else 0.0
    per_fold = np.array([f.dti for f in out], dtype=float)
    if len(per_fold) > 1:
        se = per_fold.std(ddof=1) / np.sqrt(len(per_fold))
        ci = (float(pooled - 1.96 * se), float(pooled + 1.96 * se))
    else:
        ci = (float("nan"), float("nan"))
    return HoldoutResult(EVALUATOR_VERSION, float(pooled), tp, fp, fn, n_pos, out, ci)


def score_static(surface: np.ndarray, folds, *, domain, **kw) -> HoldoutResult:
    """Score a *fixed* raster (e.g. a registry artifact) under the same protocol."""
    return score_folds(lambda fold: surface, folds, domain=domain, **kw)


def feature_auc(feature: np.ndarray, folds: list[Fold], domain: np.ndarray,
                *, dilate_truth: int = 0) -> float:
    """Leakage canary: AUC of one raw feature against the withheld positives.

    Computed by the rank/Mann-Whitney identity, pooled over folds, on in-domain pixels that
    are not visible catalogue.  AUC > 0.90 means the feature is suspected of leaking the
    answer (e.g. it was derived from the full catalogue) until proven otherwise.
    """
    f = np.asarray(feature, dtype=np.float64)
    pos_vals, neg_vals = [], []
    for fold in folds:
        ok = domain & ~fold.visible & np.isfinite(f)
        tr = fold.withheld
        if dilate_truth:
            tr = ndi.binary_dilation(tr, np.ones((3, 3), bool), iterations=dilate_truth)
        pos_vals.append(f[ok & tr])
        neg = f[ok & ~tr]
        # subsample negatives for tractability; deterministic
        rng = np.random.default_rng(7)
        if neg.size > 400_000:
            neg = rng.choice(neg, 400_000, replace=False)
        neg_vals.append(neg)
    pos = np.concatenate(pos_vals); neg = np.concatenate(neg_vals)
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    allv = np.concatenate([pos, neg])
    ranks = allv.argsort().argsort().astype(np.float64) + 1.0
    # average ranks for ties
    order = np.argsort(allv, kind="mergesort")
    sv = allv[order]
    i = 0
    while i < sv.size:
        j = i
        while j + 1 < sv.size and sv[j + 1] == sv[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + j + 2) / 2.0
        i = j + 1
    rsum = ranks[: pos.size].sum()
    n1, n2 = float(pos.size), float(neg.size)
    return float((rsum - n1 * (n1 + 1) / 2.0) / (n1 * n2))


def save(result: HoldoutResult, path: Path | str, extra: dict | None = None) -> None:
    d = result.as_dict()
    if extra:
        d.update(extra)
    Path(path).write_text(json.dumps(d, indent=2, default=float) + "\n")
