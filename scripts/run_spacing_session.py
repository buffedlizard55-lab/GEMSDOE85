#!/usr/bin/env python3
"""AXIS=SPACING session: redundancy-thinning with matched-count refill on the parent's own ridge.

Axis chosen by the agent (the human removed the choice this session).  Checked against
``ledger/submissions.csv`` on ``main`` first: PRUNE (6 rungs), SNAP (3), CONCENTRATION (3) and
RELIEF (3) are already built on this parent; MASS was rejected by a merged sibling session on its
own measurements (IR-V2-08: mass-down hurts monotonically, the low-priority dots are the backbone).
SPACING was unbuilt.  No ``(parent, axis, value)`` pair below exists in the ledger.

Design
------
The parent's dots are the H19-5 skeleton thinned to a 2.8 px packing rung.  That rung is a spacing
choice, not a geological one, and the metric charges 0.2 for every unit of mass that is not within
300 m of truth.  Two dots closer than 3 px also *share* truth credit: the second one is largely
redundant.  The redundancy is measurable exactly and without labels:

    C(x)   = max_j k(x - d_j)                      k(d) = (1 - d/3)_+
    U_i    = sum_x [ k(x - d_i) - max_{j != i} k(x - d_j) ]_+      ("unique credit" of dot i)

``U_i`` is the credit dot i supplies that no other dot supplies; the metric's true-positive term
reads exactly ``C`` at truth pixels, so a dot with low ``U_i`` is the one to drop.  This is the
parent's own geometry -- no truth, no geophysics, no seed.

Each variant then (a) removes the lowest-``U`` dots and (b) refills the **same count** at the
cells that add the most *new* credit against the kept roster, chosen greedily by exact marginal
credit and restricted to the parent's own skeleton, the footprint, ``d_cat >= 3.0 px``, at least
1.42 px from any kept dot, and not adjacent to a removed cell (so a refill can never simply undo a
removal).

    space10    10 % removed (3,765), refill from the whole residual ridge
    space20    20 % removed (7,530), refill from the whole residual ridge
    space10s   as space10, but refill cells must sit inside a continuous trace: at least 4
               skeleton pixels in the 5 x 5 window (a trace interior), which excludes stubs,
               trace tips and isolated skeleton pixels.  A structure-tensor coherence guard was
               tried first and is degenerate on a 1-px binary skeleton (zero pass), so the
               morphological definition is used instead.

Pre-registered predictions (live DTI), written before any file existed:

    space10    +0.000 .. +0.010   removes 10 % of the FP tax, spends it where coverage is thin
    space20    -0.005 .. +0.010   twice the intervention; the capacity at 2 px is only 4,311 cells
                                  with the full roster present, so 7,530 refills need the holes it
                                  opens -- an internal consistency test of the rung
    space10s   +0.000 .. +0.012   the mechanism version: redundancy out, strike-coherent mass in

Falsifier for all three: a live change under 0.01 is no evidence (public chunks only).  A *loss*
while the count is held says the parent's redundancy is insurance against the ~300 m positional
uncertainty of the 400 m-spaced survey, and spacing should be left alone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
for _sub in (ROOT / "vendor", ROOT / "src"):
    if str(_sub) not in sys.path:
        sys.path.insert(0, str(_sub))

from gems57 import gates, grid as g57  # noqa: E402
from gems57.metric import OFF_DX, OFF_DY, OFF_K  # noqa: E402
from gems57.validate import validate  # noqa: E402

TODAY = "20261023"
PARENT_ID = "h33-h33-2-b2"
PARENT_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
D28_SHA = "07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40"
H19_SHA = "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d"
CATALOGUE_CLEAR_PX = 3.0
MIN_SEP_PX = 1.42
VARIANTS = {"space10": (0.10, False), "space20": (0.20, False), "space10s": (0.10, True)}
PREDICTED = {
    "space10": dict(low=0.000, high=0.010,
                    text="10 % of the most redundant dots traded for coverage where the ridge is "
                         "unserved; FP tax falls by 0.2 x 3,765 mass units"),
    "space20": dict(low=-0.005, high=0.010,
                    text="20 %: refill must reuse the holes it opens (capacity 4,311 cells vs "
                         "7,530 refills), so the file mixes thinning with re-packing"),
    "space10s": dict(low=0.000, high=0.012,
                     text="as space10 but refill restricted to strike-coherent skeleton cells "
                          "(coherence >= 0.5), i.e. onto traces rather than tips and rims"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def dilate_max(shape, y, x) -> np.ndarray:
    """C(x) = max_j k(x - d_j) over the given dots, ignoring boundary wrap."""
    c = np.zeros(shape, np.float32)
    h, w = shape
    for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):
        ny, nx = y + dy, x + dx
        inb = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        np.maximum.at(c, (ny[inb], nx[inb]), np.float32(k))
    return c


def unique_credit(shape, y, x) -> np.ndarray:
    """Exact U_i: credit dot i supplies that no other dot does.

    Uses the best and second-best kernel contribution at every cell, so the whole field is
    computed in two passes over the 29-cell kernel instead of one pass per dot.
    """
    h, w = shape
    best = np.zeros(shape, np.float32)
    arg = np.full(shape, -1, np.int32)
    for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):
        ny, nx = y + dy, x + dx
        inb = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        yy, xx, ii = ny[inb], nx[inb], np.nonzero(inb)[0]
        v, upd = np.float32(k), np.float32(k) > best[yy, xx]
        arg[yy[upd], xx[upd]] = ii[upd]
        best[yy[upd], xx[upd]] = v
    second = np.zeros(shape, np.float32)
    for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):
        ny, nx = y + dy, x + dx
        inb = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        yy, xx, ii = ny[inb], nx[inb], np.nonzero(inb)[0]
        m = arg[yy, xx] != ii
        np.maximum.at(second, (yy[m], xx[m]), np.float32(k))
    uniq = np.clip(best - second, 0.0, None)
    return np.bincount(arg[arg >= 0], weights=uniq[arg >= 0], minlength=y.size)


def greedy_refill(shape, cand_mask, kept_y, kept_x, n_add, forbid, min_sep=MIN_SEP_PX):
    """Add n_add cells one at a time, each the cell adding the most new kernel credit.

    Exact in the same sense as the metric: the gain of adding cell p is
    ``sum_offsets (k - C(neighbour))_+`` against the current roster.
    """
    c = dilate_max(shape, kept_y, kept_x)
    cy, cx = np.nonzero(cand_mask)
    gain = np.zeros(cy.size, np.float64)
    h, w = shape
    for j, (dy, dx, k) in enumerate(zip(OFF_DY, OFF_DX, OFF_K)):
        ny, nx = cy + dy, cx + dx
        inb = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        cur = np.where(inb, c[np.clip(ny, 0, h - 1), np.clip(nx, 0, w - 1)], 0.0)
        gain += np.where(inb, np.maximum(np.float32(k) - cur, 0.0), 0.0)
    order = np.argsort(-gain, kind="stable")
    taken = np.zeros(h * w, bool)
    taken[kept_y * w + kept_x] = True
    offs = [(dy, dx) for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K) if k > 0]
    sep_sq = min_sep ** 2
    near_offsets = [(dy, dx) for dy in range(-2, 3) for dx in range(-2, 3)
                    if dy * dy + dx * dx <= sep_sq]
    chosen: list[tuple[int, int]] = []
    for idx in order:
        if len(chosen) >= n_add:
            break
        py, px = int(cy[idx]), int(cx[idx])
        if forbid[py, px] or taken[py * w + px]:
            continue
        ok = True
        for dy, dx in near_offsets:                     # minimum separation from the roster
            qy, qx = py + dy, px + dx
            if 0 <= qy < h and 0 <= qx < w and taken[qy * w + qx] and (dy or dx):
                ok = False
                break
        if not ok:
            continue
        taken[py * w + px] = True
        chosen.append((py, px))
        for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):    # update the credit field locally
            qy, qx = py + dy, px + dx
            if 0 <= qy < h and 0 <= qx < w:
                c[qy, qx] = max(c[qy, qx], np.float32(k))
    return np.array(chosen, dtype=np.int64).reshape(-1, 2), float(gain[order[0]]) if gain.size else 0.0


def coherence(skeleton: np.ndarray, sigma: float = 2.0) -> np.ndarray:
    gx = ndi.gaussian_filter(skeleton.astype(np.float32), sigma, order=(0, 1), mode="nearest")
    gy = ndi.gaussian_filter(skeleton.astype(np.float32), sigma, order=(1, 0), mode="nearest")
    jxx = ndi.gaussian_filter(gx * gx, sigma, mode="nearest")
    jyy = ndi.gaussian_filter(gy * gy, sigma, mode="nearest")
    jxy = ndi.gaussian_filter(gx * gy, sigma, mode="nearest")
    tr = jxx + jyy + 1e-12
    return (np.sqrt(np.maximum(((jxx - jyy) * 0.5) ** 2 + jxy ** 2, 0.0)) / tr).astype(np.float32)


def write_twin(path: Path, arr: np.ndarray, outside: str) -> dict:
    prof = dict(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                dtype="float32", crs="EPSG:32611", transform=g57.TRANSFORM, tiled=True,
                blockxsize=256, blockysize=256, compress="deflate", predictor=2)
    if outside == "nan":
        prof["nodata"] = float("nan")
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(arr.astype(np.float32), 1)
        dst.set_band_description(1, "predicted_new_fault_probability")
    with rasterio.open(path) as src:                    # the re-read is the contract
        back = src.read(1)
        meta = dict(bands=src.count, dtype=src.dtypes[0], crs=str(src.crs),
                    shape=[src.height, src.width], transform=list(src.transform)[:6])
    inside = np.isfinite(back) if outside == "nan" else np.ones(back.shape, bool)
    return dict(path=str(path.relative_to(ROOT)), sha256=sha256(path), bytes=path.stat().st_size,
                meta=meta, n_positive=int((back > 0).sum()),
                min_inside=float(np.min(back[inside])) if inside.any() else None,
                max_inside=float(np.max(back[inside])) if inside.any() else None, reread_ok=True)


def nn_stats(shape, y, x) -> dict:
    pts = np.stack([y, x], 1)
    if pts.shape[0] > 6000:
        rng = np.random.default_rng(20261023)
        pts = pts[rng.choice(pts.shape[0], 6000, replace=False)]
    d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    nn = d.min(1)
    return dict(mean_nn_px=round(float(nn.mean()), 4), median_nn_px=round(float(np.median(nn)), 4),
                frac_nn_lt_3px=round(float((nn < 3.0).mean()), 4),
                sampled=int(pts.shape[0]))



def _mask(shape, y, x) -> np.ndarray:
    m = np.zeros(shape, bool)
    m[y, x] = True
    return m


def _block_cv(support: np.ndarray, footprint: np.ndarray, block: int = 100) -> float:
    h, w = support.shape
    dens = []
    for by in range(0, h, block):
        for bx in range(0, w, block):
            fp = footprint[by:by + block, bx:bx + block]
            nfp = int(fp.sum())
            if nfp < 0.5 * block * block:
                continue
            dens.append(int((support[by:by + block, bx:bx + block] & fp).sum()) / nfp)
    d = np.asarray(dens)
    return float(d.std() / d.mean()) if d.mean() > 0 else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", type=Path, default=ROOT / "work/h33-b2.tif")
    ap.add_argument("--d28", type=Path, default=ROOT / "work/d28.tif")
    ap.add_argument("--skeleton", type=Path, default=ROOT / "data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif")
    ap.add_argument("--out", type=Path, default=ROOT / "releases")
    ap.add_argument("--evidence", type=Path, default=ROOT / "evidence/session_spacing.json")
    args = ap.parse_args()

    g = g57.load_grid()
    footprint, catalogue = g.footprint, g.catalogue
    shape = footprint.shape
    rec: dict = dict(schema_version=1, session="arena/59608071-gemsdoe85", axis="SPACING",
                     built_utc=TODAY, git_sha=git_sha(), alpha=0.2, beta=0.8, kernel_px=3.0,
                     catalogue_clear_px=CATALOGUE_CLEAR_PX, min_sep_px=MIN_SEP_PX,
                     min_amount_separation_px=round(float(np.sqrt(2)), 3))

    # ---- 1. parent rebuild gate (pixel identity) ------------------------------
    assert sha256(args.d28) == D28_SHA and sha256(args.parent) == PARENT_SHA
    dcat = distance_transform_edt(~catalogue)
    with rasterio.open(args.d28) as src:
        d28 = np.nan_to_num(src.read(1), nan=0.0) > 0
    with rasterio.open(args.parent) as src:
        parent = src.read(1) > 0
    assert np.array_equal(d28 & (dcat > 2.0), parent)
    with rasterio.open(args.skeleton) as src:
        skel_raw = src.read(1)
    assert sha256(args.skeleton) == H19_SHA
    skel = np.nan_to_num(skel_raw, nan=0.0) > 0
    y0, x0 = np.nonzero(parent)
    rec["parent_rebuild"] = dict(n_dots=int(parent.sum()), pixel_identical=True,
                                 skeleton_sha256=H19_SHA,
                                 dots_on_skeleton=int((parent & skel).sum()),
                                 skeleton_px=int(skel.sum()))

    U = unique_credit(shape, y0, x0)
    rec["unique_credit"] = dict(mean=round(float(U.mean()), 4), min=round(float(U.min()), 4),
                                p10=round(float(np.percentile(U, 10)), 4),
                                median=round(float(np.median(U)), 4),
                                p90=round(float(np.percentile(U, 90)), 4),
                                n_fully_redundant=int((U <= 0).sum()))

    d_parent = distance_transform_edt(~parent)
    sk_density = ndi.uniform_filter(skel.astype(np.float32), size=5) * 25.0
    free = skel & footprint & (dcat >= CATALOGUE_CLEAR_PX)
    rec["candidate_capacity"] = {f"sep_{m}px": int((free & (d_parent > m)).sum())
                                 for m in (1.5, 2.0, 2.8)}

    # ---- 2. build ------------------------------------------------------------
    args.out.mkdir(parents=True, exist_ok=True)
    out_variants = []
    ineligible = parent & (dcat < CATALOGUE_CLEAR_PX)             # mandatory >= 3 px collar
    n_collar = int(ineligible.sum())
    rec["collar"] = dict(n_dots_below_3px=n_collar,
                         note="R0 keeps dots at 2.236/2.828 px; every non-PRUNE axis in this "
                              "repository applies the collar first (IR-86-002 / IR-V2-03). The "
                              "collar is identical in all three variants and in main's PRUNE and "
                              "RELIEF builds, so it cancels in the comparison and is reported "
                              "separately from the axis part.")
    cand_order = np.argsort(-U, kind="stable")
    for vid, (frac, coherent_only) in VARIANTS.items():
        n_rm = max(int(round(frac * y0.size)), n_collar)
        collar_idx = np.nonzero(ineligible[y0, x0])[0]
        rest = [i for i in cand_order if i not in set(collar_idx.tolist())]
        axis_idx = np.array(rest[:max(0, n_rm - n_collar)], dtype=np.int64)
        rm_idx = np.concatenate([collar_idx, axis_idx])
        keep_mask = np.ones(y0.size, bool)
        keep_mask[rm_idx] = False
        keep_idx = np.nonzero(keep_mask)[0]
        ky, kx = y0[keep_idx], x0[keep_idx]
        ry, rx = y0[rm_idx], x0[rm_idx]

        forbid = np.zeros(shape, bool)                            # never undo a removal
        forbid[np.clip(ry - 1, 0, shape[0] - 1), rx] = True
        forbid[ry, np.clip(rx - 1, 0, shape[1] - 1)] = True
        forbid[np.clip(ry + 1, 0, shape[0] - 1), rx] = True
        forbid[ry, np.clip(rx + 1, 0, shape[1] - 1)] = True
        forbid[ry, rx] = True

        d_keep = distance_transform_edt(~_mask(shape, ky, kx))
        cand = free & (d_keep > MIN_SEP_PX) & ~forbid
        if coherent_only:
            cand &= sk_density >= 4.0          # trace interior, see module docstring
        added, _ = greedy_refill(shape, cand, ky, kx, n_rm, forbid)
        ay, ax = (added[:, 0], added[:, 1]) if added.size else (np.array([], int), np.array([], int))
        fy = np.concatenate([ky, ay]).astype(np.int64)
        fx = np.concatenate([kx, ax]).astype(np.int64)

        sup = np.zeros(shape, bool)
        sup[fy, fx] = True
        assert int(sup.sum()) == int(parent.sum()), f"count not matched: {int(sup.sum())}"
        assert not (sup & catalogue).any(), "mass on the catalogue"
        assert float(dcat[sup].min()) >= CATALOGUE_CLEAR_PX - 1e-9, "broke the 3 px rule"
        assert not (sup & ~footprint).any(), "mass outside the footprint"

        vals = np.where(sup, np.float32(1.0), np.float32(0.0))
        nan_arr = np.where(footprint, vals, np.float32("nan"))
        slug = f"{PARENT_ID}-{vid}-{TODAY}"
        tmp0 = args.out / f".tmp-{vid}-z.tif"
        z = write_twin(tmp0, vals, "zeros")
        final0 = args.out / f"{slug}-{z['sha256'][:8]}-zeros.tif"
        tmp0.replace(final0)
        z = write_twin(final0, vals, "zeros")
        tmpn = args.out / f".tmp-{vid}-n.tif"
        n = write_twin(tmpn, nan_arr, "nan")
        finaln = args.out / f"{slug}-{n['sha256'][:8]}-nan.tif"
        tmpn.replace(finaln)
        n = write_twin(finaln, nan_arr, "nan")

        fr = gates.format_report(final0, ROOT / "data/bridge/sample_submission.tif", footprint=footprint)
        lv = validate(final0, footprint, catalogue)
        frn = gates.format_report(finaln, ROOT / "data/bridge/sample_submission.tif", footprint=footprint)
        lvn = validate(finaln, footprint, catalogue) if frn["ok"] else dict(all_checks_passed=False)

        added_edge = d_parent[ay, ax] if ay.size else np.array([np.inf])
        stats = dict(
            n_dots=int(sup.sum()), n_removed=int(n_rm), n_added=int(ay.size),
            n_collar_removed=int(n_collar), n_axis_removed=int(axis_idx.size),
            pct_dots_changed=round(100.0 * int((sup ^ parent).sum()) / 2 / parent.sum(), 3),
            jaccard_vs_parent=round(float((sup & parent).sum() / (sup | parent).sum()), 6),
            n_voxels_changed=int((sup ^ parent).sum()),
            U_removed_mean=round(float(U[rm_idx].mean()), 4),
            U_kept_mean=round(float(U[keep_idx].mean()), 4),
            added_min_dist_parent_px=round(float(added_edge.min()), 3),
            added_median_dist_parent_px=round(float(np.median(added_edge)), 3),
            added_on_skeleton_pct=round(100.0 * float(skel[ay, ax].mean()) if ay.size else 0.0, 2),
            spacing_before=nn_stats(shape, y0, x0),
            spacing_after=nn_stats(shape, fy, fx),
            block_cv_10km_parent=round(_block_cv(parent, footprint), 4),
            block_cv_10km_variant=round(_block_cv(sup, footprint), 4),
        )
        out_variants.append(dict(id=f"{slug}-{z['sha256'][:8]}", slug=slug, value=vid,
                                 fraction=frac, coherent_only=coherent_only, zeros=z, nan=n,
                                 format_report=dict(ok=bool(fr["ok"]), problems=fr.get("problems", [])),
                                 local_validate=dict(all_checks_passed=bool(lv["all_checks_passed"])),
                                 nan_format_ok=bool(frn["ok"]),
                                 nan_local_ok=bool(lvn.get("all_checks_passed")),
                                 stats=stats, predicted=PREDICTED[vid], support=sup))
        print(f"[built] {vid:9s} n={stats['n_dots']} rm={n_rm} add={ay.size} "
              f"changed={stats['pct_dots_changed']:5.2f}% jac={stats['jaccard_vs_parent']:.3f} "
              f"nn {stats['spacing_before']['mean_nn_px']:.2f}->{stats['spacing_after']['mean_nn_px']:.2f} "
              f"gates={fr['ok'] and lv['all_checks_passed']}", flush=True)

    rec["variants"] = [{k: v for k, v in d.items() if k != "support"} for d in out_variants]
    rec["parent_stats"] = dict(n_dots=int(parent.sum()), spacing=nn_stats(shape, y0, x0),
                               block_cv_10km=round(_block_cv(parent, footprint), 4))
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(rec, indent=2, default=float) + "\n")
    print(f"\n-> {args.evidence.relative_to(ROOT)}")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
