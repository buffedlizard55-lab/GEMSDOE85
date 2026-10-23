#!/usr/bin/env python3
"""AXIS=SPACING, session 2026-10-23: same count, same mass, different arrangement.

Why this axis, and why now
    Every other listed axis is already built somewhere in the fleet (ledger: PRUNE x6,
    SNAP x3, CONCENTRATION x3, RELIEF x3, MASS x3 on this branch).  SPACING has no row.

The mechanism (the reason this is not a cosmetic reshuffle)
    DTI counts, per truth pixel, the BEST credit any dot gives it:
    T = sum_g max_x p(x) k(d).  R0's dots are packed at >= 2.828 px, so along any trace the
    best case alternates 1.0, 0.53, 0.0, 0.53 ... -- a truth pixel midway between two dots
    earns k(1.41) = 0.53 no matter how good the dot is.  Inserting one dot at that midpoint
    raises those pixels to ~1.0 while costing the denominator alpha*(1 - k_nearest).  Once a
    dot is on a real trace, halving the along-trace spacing is nearly free profit; the whole
    question is whether the strong traces are real and whether the dots feeding them can be
    paid for.  This axis measures exactly that, at fixed count and fixed mass.

Variants (count 37,654 before and after; only arrangement moves)
    spacing-infill10   remove the 3,765 lowest-ancestor-credit dots (all are credit ~1.0
                       isolates) and insert 3,765 dots at the midpoints of dot PAIRS that
                       are 2.83-3.0 px apart and whose midpoint lies on the ancestor field
                       -- i.e. exactly where a trace continues between two strong dots.
    spacing-infill20   same rule at 7,530 / 7,530 (21 % of the 7,903 gap sites that exist).
    spacing-fill10     ABLATION, matched on everything except the placement rule: same 3,765
                       removals, same freed mass, same pool (ancestor support, > 2 px from
                       the catalogue), but the new dots are placed by marginal field credit
                       at >= 2.0 px separation instead of in trace gaps.  If infill10 beats
                       fill10, the gain is geometry (trace continuity); if it does not, the
                       gain is just mass and the whole spacing story is dead.

Usage
    python scripts/build_spacing_axis.py --probe
    python scripts/build_spacing_axis.py
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
for sub in (ROOT / "src", ROOT / "scripts", ROOT):
    if str(sub) not in sys.path:
        sys.path.insert(0, str(sub))

import build_mass_axis as M  # noqa: E402  pinned loaders, ranking, parent rebuild, predictor
from gems85.metric import kernel_dilate  # noqa: E402
from gems85.submission import validate, write_raster  # noqa: E402

RELEASES = ROOT / "releases"
EVIDENCE = ROOT / "evidence"
TARGET_N = 37_654
FILL_MIN_SEP = 2.0          # the lineage's own finer packing (d1.5/d2.0 regime)
RANK_DECIMALS = 12

VARIANTS = [
    ("spacing-infill10", "infill10", 3_765, "infill"),
    ("spacing-infill20", "infill20", 7_530, "infill"),
    ("spacing-fill10", "fill10", 3_765, "fill"),
]


def gap_sites(ranked: dict, dots: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Midpoints of close dot pairs whose in-between pixel is on the field support.

    A pair is 'close' at 2.83-3.0 px: that is the parent's own packing rung (2.828) plus the
    kernel tolerance, so these are pairs that a continuous trace would have filled.
    """
    y, x = np.nonzero(dots)
    pts = np.c_[y, x]
    pairs = cKDTree(pts).query_pairs(r=3.0, output_type="ndarray")
    credit = np.zeros(len(pts))
    credit[ranked["order_weakest_first"]] = np.sort(ranked["credit"])
    seen: set[tuple[int, int]] = set()
    out, strength = [], []
    for a, b in pairs:
        m = (pts[a] + pts[b]) // 2
        key = (int(m[0]), int(m[1]))
        if key in seen:
            continue
        seen.add(key)
        if dots[m[0], m[1]] or not ranked["field"][m[0], m[1]]:
            continue
        if ranked["dcat"][m[0], m[1]] <= M.CATALOGUE_BUFFER_PX:
            continue
        out.append(key)
        strength.append(float(ranked["credit"][a] + ranked["credit"][b]))
    order = np.lexsort((np.array([k[1] for k in out]), np.array([k[0] for k in out]),
                        -np.asarray(strength)))
    return np.array(out, dtype=np.int64)[order], np.asarray(strength)[order]


def credit_pool(ranked: dict, kept: np.ndarray, need: int,
                banned: np.ndarray | None = None) -> np.ndarray:
    """Marginal-credit insertion at FILL_MIN_SEP: the ablation's placement rule.

    ``banned`` holds the pixels that were just removed; they are excluded from the pool, so a
    "new" dot can never be a re-placed old one (otherwise the ablation silently becomes a
    partial undo of its own removals -- caught by the added/dropped count disagreeing).
    """
    field, dcat = ranked["field"], ranked["dcat"]
    taken = kept.copy()
    current = kernel_dilate(taken.astype(np.float64))
    pool = field & ~taken & (dcat > M.CATALOGUE_BUFFER_PX)
    if banned is not None:
        pool &= ~banned
    pool &= ndi.distance_transform_edt(~taken) >= FILL_MIN_SEP
    py, px = np.nonzero(pool)
    cand = np.c_[py, px]
    fy, fx = np.nonzero(field)
    ftree = cKDTree(np.c_[fy, fx])
    disc = [(dy, dx, max(0.0, 1.0 - math.hypot(dy, dx) / 3.0))
            for dy in range(-3, 4) for dx in range(-3, 4) if math.hypot(dy, dx) <= 3.0]
    too_close = [(dy, dx) for dy in range(-3, 4) for dx in range(-3, 4)
                 if 0 < math.hypot(dy, dx) < FILL_MIN_SEP - 1e-9]
    h, w = taken.shape

    def gain(y: int, x: int) -> float:
        idx = ftree.query_ball_point((y, x), r=3.0)
        if not idx:
            return 0.0
        pts = ftree.data[idx]
        k = np.maximum(1.0 - np.hypot(pts[:, 0] - y, pts[:, 1] - x) / 3.0, 0.0)
        return float(np.maximum(k - current[pts[:, 0].astype(np.int64),
                                            pts[:, 1].astype(np.int64)], 0.0).sum())

    g0 = np.round([gain(int(y), int(x)) for y, x in cand], RANK_DECIMALS)
    heap = [(-g, int(y), int(x)) for (y, x), g in zip(cand, g0)]
    heapq.heapify(heap)
    added = 0
    while heap and added < need:
        neg, y, x = heapq.heappop(heap)
        if -neg <= 0.0:
            break
        g = round(gain(y, x), RANK_DECIMALS)
        if g > -neg:                                    # stale under lazy greedy
            heapq.heappush(heap, (-g, y, x))
            continue
        if g <= 0.0:
            continue
        if any(0 <= y + dy < h and 0 <= x + dx < w and taken[y + dy, x + dx]
               for dy, dx in too_close):
            continue
        taken[y, x] = True
        for dy, dx, k in disc:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                current[yy, xx] = max(current[yy, xx], k)
        added += 1
    if added < need:
        raise SystemExit(f"pool exhausted: placed {added} of {need}; refusing to loosen silently")
    return taken


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()

    inputs = M.load_pinned()
    info = M.rebuild_parent(inputs)
    if not info["pixels_identical"]:
        raise SystemExit("R0 not reproducible from its pinned inputs; stopping")
    parent = M.read_binary(inputs["parent"]["array"])
    ranked = M.rank_parent_dots(inputs, parent)
    ranked["_labels"] = M.read_binary(inputs["labels"]["array"])
    order, credit = ranked["order_weakest_first"], ranked["credit"]
    coords, dcat = ranked["coords"], ranked["dcat"]

    sites, strength = gap_sites(ranked, parent)
    print(f"gap sites: {len(sites)} | credit==1.0 isolates: {int((credit <= 1.0001).sum())}")
    if args.probe:
        return 0

    RELEASES.mkdir(exist_ok=True)
    EVIDENCE.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    results = {}

    for stem_id, value, k, kind in VARIANTS:
        keep_idx = np.sort(order[k:])                  # drop the k weakest-credit dots
        variant = np.zeros_like(parent)
        variant[coords[keep_idx, 0], coords[keep_idx, 1]] = True
        removed_credit_max = float(credit[order[:k]].max())

        if kind == "infill":
            if k > len(sites):
                raise SystemExit(f"infill{k} needs {k} gap sites, only {len(sites)} exist")
            ins = sites[:k]
            variant[ins[:, 0], ins[:, 1]] = True
            ins_credit = None
        else:
            removed_mask = np.zeros_like(parent)
            removed_mask[coords[order[:k], 0], coords[order[:k], 1]] = True
            variant = credit_pool(ranked, variant, k, banned=removed_mask)
            ins_credit = "marginal field credit at >= 2.0 px"

        assert variant.sum() == TARGET_N, (variant.sum(), TARGET_N)
        assert not (variant & ranked["_labels"]).any(), "mass on the catalogue"
        assert dcat[variant].min() > M.CATALOGUE_BUFFER_PX, "dot inside the Euclidean buffer"
        cheb2 = int((variant & ndi.binary_dilation(ranked["_labels"], np.ones((3, 3), bool),
                                                   iterations=2)).sum())
        added, dropped = int((variant & ~parent).sum()), int((parent & ~variant).sum())
        pct = 100.0 * (added + dropped) / TARGET_N
        assert 1.0 <= pct <= 50.0, f"{pct:.2f}% of positions changed"

        stem = f"{stem_id}-{stamp}"
        nan_tmp = RELEASES / f".{stem}.nan.tmp.tif"
        write_raster(variant, nan_tmp, mode="nan")
        rep_nan = validate(nan_tmp, mode="nan", catalogue_buffer_px=None)   # IR-85-MASS-02
        tmp = RELEASES / f".{stem}.tmp.tif"
        write_raster(variant, tmp, mode="zeros")
        rep = validate(tmp, mode="zeros", catalogue_buffer_px=None)
        if not (rep.passed and rep_nan.passed):
            raise SystemExit(f"{stem_id}: validation failed")
        sha8 = rep_nan.sha256[:8]
        fz = RELEASES / f"{stem}-{sha8}-zeros.tif"
        fn = RELEASES / f"{stem}-{sha8}.tif"
        tmp.replace(fz)
        nan_tmp.replace(fn)
        with rasterio.open(fz) as src:
            back = src.read(1)
            meta = {"crs": str(src.crs), "shape": (src.height, src.width),
                    "dtype": src.dtypes[0], "transform": tuple(src.transform)[:6]}
        assert np.array_equal(M.read_binary(back), variant), "re-read mismatch"
        assert M.sha256_file(fz) == rep.sha256, "sha drifted on rename"
        assert M.sha256_file(fn) == rep_nan.sha256, "nan sha drifted on rename"
        assert meta["transform"] == inputs["parent"]["transform"], "transform drifted"

        pred = M.predict(ranked, parent, variant, info)
        ys, xs = np.nonzero(variant)
        py, px = np.nonzero(parent)
        moved = cKDTree(np.c_[py, px])
        dd, _ = moved.query(np.c_[ys, xs], k=1)        # displacement to the nearest parent dot
        results[stem_id] = {
            "id": f"{stem}-{sha8}", "parent": "h33-h33-2-b2", "axis": "SPACING",
            "value": value, "n_dots": int(variant.sum()), "pct_changed": pct,
            "placement_rule": ("midpoint of 2.83-3.0 px dot pairs on the ancestor field"
                               if kind == "infill" else ins_credit),
            "sha256": rep_nan.sha256, "sha256_nan": rep_nan.sha256,
            "sha256_zeros": rep.sha256,
            "bytes_zeros": fz.stat().st_size, "bytes_nan": fn.stat().st_size,
            "file_zeros": str(fz.relative_to(ROOT)), "file_nan": str(fn.relative_to(ROOT)),
            "checks": rep.checks, "checks_nan": rep_nan.checks, "stats": rep_nan.stats, "meta": meta,
            "dots_in_chebyshev2_catalogue_buffer": cheb2,
            "diff": {
                "n_added": added, "n_dropped": dropped, "pixels_changed": added + dropped,
                "pct_changed": pct,
                "max_credit_removed": removed_credit_max,
                "min_dcat_variant": float(dcat[variant].min()),
                "mean_dcat_parent": float(dcat[parent].mean()),
                "mean_dcat_variant": float(dcat[variant].mean()),
                "inserted_mean_credit": (
                    float(M.kernel_credit_against(
                        cKDTree(np.c_[np.nonzero(ranked["field"])[0],
                                      np.nonzero(ranked["field"])[1]]),
                        np.c_[ys, xs])[~parent[ys, xs]].mean()) if added else 0.0),
                "inserted_mean_displacement_px": float(dd[dd > 0].mean()) if added else 0.0,
                "inserted_frac_within_2px_of_a_parent_dot": float((dd[dd > 0] <= 2.0).mean()),
            },
            "prediction": pred,
        }
        print(f"[built] {results[stem_id]['id']}  n={variant.sum()}  +{added}/-{dropped} "
              f"({pct:.2f}%)  sha256={rep_nan.sha256[:16]}  predicted "
              f"{pred['predicted_live_change']:+.4f}")

    (EVIDENCE / "spacing_axis.json").write_text(json.dumps({
        "session": "AXIS=SPACING", "parent": "h33-h33-2-b2",
        "parent_claim_dti": M.PARENT_CLAIM_DTI,
        "gap_sites_available": int(len(sites)),
        "isolates_credit_1p0": int((credit <= 1.0001).sum()),
        "fill_min_sep": FILL_MIN_SEP,
        "variants": results,
    }, indent=1) + "\n")
    print("wrote evidence/spacing_axis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
