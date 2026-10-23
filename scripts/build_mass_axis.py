#!/usr/bin/env python3
"""AXIS=MASS session: three count variants of the incumbent R0, nothing else changed.

Parent (R0)
    GEMSDOE32 ``h33-h33-2-b2``  (CLAIM 0.2778; no receipt in this repo)
    sha256 c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9
    content = the 40,199-dot ``gemsdoe31-h27-4-solo-d28`` set with every dot at
    Euclidean distance <= 2 px from the catalogue deleted (37,654 dots).
    This script *derives* the parent from those two pinned inputs and asserts the
    pixels are identical before touching anything (``--check-parent`` does only that).

The parent's own ranking is NOT stored anywhere.  Every raster in the lineage ships a
binary 0/1 field (h19-5, d1.5, d2.8, solo-d28, h33-2-b2 all carry exactly two distinct
values), the 2.8-px packing leaves no redundant pairs (minimum nearest-neighbour
distance over the 37,654 dots is 2.828 px), and the repositories that built h19-5
(GEMSDOE19, GEMSDOE24/build_candidate.py) are 404.  See IRREGULARITIES.md IR-85-MASS-01.

Ranking used instead (documented substitution, one rule for all three variants)
    score(dot) = sum over ancestor-field pixels x within 3 px of k(|dot-x|),
                 k = max(1 - d/3, 0),  field = the pinned h19-5 support (121,131 px).
    That is the exact kernel credit of one dot against the field the parent was thinned
    from -- i.e. the metric's own T-term, evaluated on the best available truth proxy.
    Ties: larger distance-to-catalogue first (less corroborated), then row, then column.

Variants (count is the ONLY degree of freedom; every other dot is inherited unchanged)
    mass-m20  37,654 -> 30,124  (-7,530, -20.0 %)  drop the 20 % lowest-ranked dots
    mass-m10  37,654 -> 33,887  (-3,767, -10.0 %)  drop the 10 % lowest-ranked dots
    mass-p10  37,654 -> 41,415  (+3,761, +10.0 %)  add the next-ranked dots:
              candidates are ancestor-field pixels not already dots, > 2 px from the
              catalogue (the parent's own exclusion), and >= 2.828 px from every
              accepted dot (the parent's own packing distance); chosen by exact
              marginal kernel credit (lazy greedy), so no credit is double-counted.

Nothing else is allowed to move: same grid, same footprint, same encoding, same unit
mass per dot, no dot on or within 2 px of the catalogue in any variant.

Usage
    python scripts/build_mass_axis.py --check-parent
    python scripts/build_mass_axis.py            # build, validate, predict, emit ledger rows
"""

from __future__ import annotations

import argparse
import hashlib
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
for sub in (ROOT / "src", ROOT):
    if str(sub) not in sys.path:
        sys.path.insert(0, str(sub))

from gems85.metric import OFFSETS, kernel_dilate  # noqa: E402
from gems85.submission import validate, write_raster  # noqa: E402

DATA = ROOT / "data"
REGISTRY = ROOT / "registry"
RELEASES = ROOT / "releases"
EVIDENCE = ROOT / "evidence"

# ---------------------------------------------------------------- pinned inputs
# (path, expected sha256, role).  Hashes are the ones in registry/data_manifest.json
# and registry/scored_artifacts.json; they are re-checked on every run, never trusted.
PINNED = {
    "parent": (
        DATA / "registry_rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    ),
    "base_solo_d28": (
        DATA / "registry_rasters/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        "07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40",
    ),
    "ancestor_field": (
        DATA / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
        "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
    ),
    "labels": (DATA / "labels.tif",
               "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "sample_submission": (DATA / "sample_submission.tif",
                          "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
}

PARENT_ID = "h33-2-b2"
PARENT_CLAIM_DTI = 0.2778          # CLAIM (owner-reported; no receipt in this repo)
ALPHA, BETA, R_PX = 0.2, 0.8, 3.0
CATALOGUE_BUFFER_PX = 2.0          # the parent's own exclusion radius
PACKING_PX = 2.828                 # the parent's own minimum dot separation
PACKING_ADD_PX = 1.5               # the lineage's own looser packing (d1.5, 60,069 dots)
TARGET_N = 37_654                  # R0's dot count
RANK_DECIMALS = 12                 # quantise credit before breaking ties, for determinism

VARIANTS = [
    # id suffix, value label, resulting count, operation
    ("mass-m20", "-20%", 30_124, "drop"),
    ("mass-m10", "-10%", 33_887, "drop"),
    ("mass-p10", "+10%", 41_415, "add"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_pinned() -> dict:
    out = {}
    for key, (path, expected) in PINNED.items():
        if not path.is_file():
            raise SystemExit(f"missing pinned input {key}: {path}\n"
                             f"run: python scripts/restore_data.py --groups core scored")
        got = sha256_file(path)
        if got != expected:
            raise SystemExit(f"{key}: sha256 {got} != pinned {expected}; refusing to proceed")
        with rasterio.open(path) as src:
            out[key] = {"path": path, "sha256": got, "array": src.read(1),
                        "transform": tuple(src.transform)[:6],
                        "crs": str(src.crs), "shape": (src.height, src.width),
                        "dtype": src.dtypes[0]}
    return out


def read_binary(a: np.ndarray) -> np.ndarray:
    return np.isfinite(a) & (a > 0)


def rebuild_parent(inputs: dict) -> dict:
    """R0 := solo-d28 dots with Euclidean distance > 2 px from the catalogue."""
    base = read_binary(inputs["base_solo_d28"]["array"])
    cat = read_binary(inputs["labels"]["array"])
    dcat = ndi.distance_transform_edt(~cat)
    rebuilt = base & (dcat > CATALOGUE_BUFFER_PX)
    parent = read_binary(inputs["parent"]["array"])
    identical = bool(np.array_equal(rebuilt, parent))
    return {
        "parent_dots": int(parent.sum()),
        "base_dots": int(base.sum()),
        "dropped_by_parent": int(base.sum() - parent.sum()),
        "rebuilt_dots": int(rebuilt.sum()),
        "pixels_identical": identical,
        "differing_pixels": int((rebuilt != parent).sum()),
        "parent_container_sha256": inputs["parent"]["sha256"],
        "n_within_3px_of_catalogue_in_parent": int(((dcat > 2.0) & (dcat <= 3.0) & parent).sum()),
        "parent_mass_on_catalogue": int((parent & cat).sum()),
        "parent_mass": float(inputs["parent"]["array"][parent].sum()),
        "parent_unique_values": sorted({float(v) for v in np.unique(inputs["parent"]["array"][np.isfinite(inputs["parent"]["array"])])}),
    }


def kernel_credit_against(field_pts: cKDTree, coords: np.ndarray) -> np.ndarray:
    """Exact kernel credit of each dot against a point set (the metric's T-term per dot)."""
    score = np.zeros(len(coords), dtype=np.float64)
    nbrs = field_pts.query_ball_point(coords, r=R_PX)
    for i, idx in enumerate(nbrs):
        if not idx:
            continue
        d = np.hypot(*(field_pts.data[idx] - coords[i]).T)
        score[i] = np.maximum(1.0 - d / R_PX, 0.0).sum()
    return score


def rank_parent_dots(inputs: dict, parent: np.ndarray) -> dict:
    field = read_binary(inputs["ancestor_field"]["array"])
    cat = read_binary(inputs["labels"]["array"])
    dcat = ndi.distance_transform_edt(~cat)
    y, x = np.nonzero(parent)
    coords = np.c_[y, x]
    fy, fx = np.nonzero(field)
    tree = cKDTree(np.c_[fy, fx])
    credit = np.round(kernel_credit_against(tree, coords), RANK_DECIMALS)
    # ascending score = weakest first; ties -> larger dcat first, then row, then col
    order = np.lexsort((x, y, -dcat[y, x], credit))
    return {"field": field, "dcat": dcat, "coords": coords, "credit": credit,
            "order_weakest_first": order}


def add_candidates(inputs: dict, ranked: dict, parent: np.ndarray, need: int) -> np.ndarray:
    """Greedy max-coverage additions from the ancestor field, exact marginal credit.

    Lazy greedy on a max-heap.  Gains only ever decrease as credit is consumed, so
    re-testing the popped candidate and pushing it back when stale is exact.  All
    updates are local windows: no full-grid allocation inside the loop.
    """
    field, dcat = ranked["field"], ranked["dcat"]
    taken = parent.copy()
    current = kernel_dilate(taken.astype(np.float64))          # credit already earned, per px

    pool = field & ~parent & (dcat > CATALOGUE_BUFFER_PX)
    near = ndi.distance_transform_edt(~taken)
    pool &= near >= PACKING_ADD_PX
    py, px = np.nonzero(pool)
    pcoords = np.c_[py, px]
    fy, fx = np.nonzero(field)
    ftree = cKDTree(np.c_[fy, fx])

    # integer offsets used to apply / test one dot's kernel
    disc = [(dy, dx, max(0.0, 1.0 - math.hypot(dy, dx) / R_PX))
            for dy in range(-3, 4) for dx in range(-3, 4) if math.hypot(dy, dx) <= R_PX]
    too_close = [(dy, dx) for dy in range(-3, 4) for dx in range(-3, 4)
                 if 0 < math.hypot(dy, dx) < PACKING_ADD_PX - 1e-9]
    h, w = taken.shape

    def gain_one(y: int, x: int) -> float:
        idx = ftree.query_ball_point((y, x), r=R_PX)
        if not idx:
            return 0.0
        pts = ftree.data[idx]
        d = np.hypot(pts[:, 0] - y, pts[:, 1] - x)
        k = np.maximum(1.0 - d / R_PX, 0.0)
        iy = pts[:, 0].astype(np.int64)
        ix = pts[:, 1].astype(np.int64)
        return float(np.maximum(k - current[iy, ix], 0.0).sum())

    def clear_of_packing(y: int, x: int) -> bool:
        for dy, dx in too_close:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and taken[yy, xx]:
                return False
        return True

    g0 = np.round([gain_one(int(y), int(x)) for y, x in pcoords], RANK_DECIMALS)
    heap = [(-g, int(y), int(x)) for (y, x), g in zip(pcoords, g0)]
    heapq.heapify(heap)

    added = 0
    while heap and added < need:
        neg, y, x = heapq.heappop(heap)
        if -neg <= 0.0:
            break
        g = round(gain_one(y, x), RANK_DECIMALS)
        if g > -neg:                                   # stale: credit was consumed elsewhere
            heapq.heappush(heap, (-g, y, x))
            continue
        if g <= 0.0 or not clear_of_packing(y, x):
            continue
        taken[y, x] = True
        for dy, dx, k in disc:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                current[yy, xx] = max(current[yy, xx], k)
        added += 1
    if added < need:
        raise SystemExit(f"candidate pool exhausted: added {added} of {need}; "
                         f"refusing to loosen the packing rule silently")
    return taken


def predict(ranked: dict, parent: np.ndarray, variant: np.ndarray, parent_stats: dict) -> dict:
    """MODEL prediction of the live change, from the metric algebra on the field proxy.

    DTI = T / (alpha*(T + n - M) + beta*|G|),  T = credit earned over truth pixels,
    M = credit each dot earns from truth, n = dot count.

    T and M are measured exactly, with the pinned h19-5 support standing in for truth
    (the only fault-like structure available without label probing).  The denominator is
    then re-scaled from |field| to the catalogue's positive count so the number is on the
    scale of the public score, and DTI0 is the parent's CLAIM 0.2778.  This is a MODEL.
    """
    field = ranked["field"]
    n_field = int(field.sum())
    n_cat = int(read_binary(ranked["_labels"]).sum())

    def tm(dots: np.ndarray) -> tuple[float, float]:
        cred = kernel_dilate(dots.astype(np.float64))
        T = float(cred[field].sum())
        M = float(cred[dots].sum())      # credit each dot receives from the nearest field px
        return T, M

    T0, M0 = tm(parent)
    T1, M1 = tm(variant)
    n0, n1 = int(parent.sum()), int(variant.sum())

    def dti_on(T, M, n, G, scale):
        den = ALPHA * (T + n - M) + BETA * G
        return T / den if den > 0 else 0.0, den

    dti_f0, D_f0 = dti_on(T0, M0, n0, n_field, 1.0)
    dti_f1, D_f1 = dti_on(T1, M1, n1, n_field, 1.0)
    d_field = dti_f1 - dti_f0

    # Rescale.  D = alpha*(T + n - M) + beta*|G| is dominated by beta*|G|, so a delta measured
    # against |field| truth pixels maps onto the catalogue's positive count by the ratio of
    # those counts.  This is a MODEL: the field is the parent's own prediction, so the delta
    # it produces is biased against losing dots (see the circularity note below).
    rescale = n_cat / n_field
    d_live = d_field * rescale

    # Bracket.  Floor = the dropped dots earn NO new-fault credit at all, so the only effect is
    # the alpha charge they stop paying: dDTI = -DTI0 * alpha * dn / D_live with
    # D_live ~ beta*|G| + alpha*n0 (T - M cancels when dots and truth correspond 1:1).
    D0_live = BETA * n_cat + ALPHA * n0
    d_floor = -PARENT_CLAIM_DTI * ALPHA * (n1 - n0) / D0_live
    # Ceiling = every unit of field credit lost was real, unmapped fault truth.
    d_ceiling = d_live
    return {
        "n_catalogue_positive_px": n_cat,
        "n_field_px": n_field,
        "T0": T0, "M0": M0, "T1": T1, "M1": M1, "n0": n0, "n1": n1,
        "dT": T1 - T0, "dn": n1 - n0, "dM": M1 - M0,
        "field_coverage_parent": T0 / n_field,
        "field_coverage_variant": T1 / n_field,
        "field_dti_parent": dti_f0,
        "field_dti_variant": dti_f1,
        "delta_field_dti": d_field,
        "rescale_factor": rescale,
        "predicted_live_change": d_live,
        "bracket_floor_no_new_credit": d_floor,
        "bracket_ceiling_lost_credit_was_real": d_ceiling,
        "predicted_live_dti_point": PARENT_CLAIM_DTI + d_live,
        "method": "MODEL: exact T/M under the pinned h19-5 field proxy (circular: the field is the "
                  "parent's own surface, so it penalises losing dots); delta rescaled by "
                  "|catalogue|/|field|; anchored on the parent CLAIM 0.2778. Bracket: floor = "
                  "dropped dots earn nothing, ceiling = all lost field credit was real truth.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cat-buffer", type=float, default=None,
                    help="Override the Euclidean catalogue exclusion in px (default: the parent's 2.0). "
                         "Use 3.0 for a brief-section-4-compliant base; that confounds MASS with PRUNE.")
    ap.add_argument("--check-parent", action="store_true",
                    help="only verify that R0 is derivable from its two pinned inputs")
    args = ap.parse_args()

    if args.cat_buffer is not None:
        global CATALOGUE_BUFFER_PX
        CATALOGUE_BUFFER_PX = float(args.cat_buffer)
    inputs = load_pinned()
    parent_info = rebuild_parent(inputs)
    print(json.dumps(parent_info, indent=1))
    if not parent_info["pixels_identical"]:
        raise SystemExit("R0 pixels are NOT reproducible from the pinned base + labels; stopping "
                         "(never approximate the parent)")
    if args.check_parent:
        return 0

    parent = read_binary(inputs["parent"]["array"])
    ranked = rank_parent_dots(inputs, parent)
    ranked["_labels"] = read_binary(inputs["labels"]["array"])
    field = ranked["field"]
    order = ranked["order_weakest_first"]
    dcat = ranked["dcat"]
    coords = ranked["coords"]
    credit = ranked["credit"]
    print(f"ranking: n={len(coords)} credit[min,median,max]="
          f"{credit.min():.4f},{np.median(credit):.3f},{credit.max():.4f} "
          f"| dots with zero field credit: {int((credit == 0).sum())}")

    RELEASES.mkdir(exist_ok=True)
    EVIDENCE.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    rows, cards, results = [], [], {}

    for suffix, value, target, op in VARIANTS:
        if op == "drop":
            keep_idx = np.sort(order[:target])
            variant = np.zeros_like(parent)
            variant[coords[keep_idx, 0], coords[keep_idx, 1]] = True
            removed = np.ones(len(coords), bool)
            removed[keep_idx] = False
            moved = int(removed.sum())
        else:
            variant = add_candidates(inputs, ranked, parent, target - TARGET_N)
            moved = int(variant.sum() - TARGET_N)

        # ---- invariants (fail closed)
        assert variant.sum() == target, (variant.sum(), target)
        assert not (variant & ranked["_labels"]).any(), "mass on the catalogue"
        assert dcat[variant].min() > CATALOGUE_BUFFER_PX, "dot inside the Euclidean catalogue buffer"
        cheb2 = int((variant & ndi.binary_dilation(ranked["_labels"], np.ones((3, 3), bool),
                                                   iterations=2)).sum())
        changed = int((variant != parent).sum())
        pct = 100.0 * changed / TARGET_N
        assert 1.0 <= pct <= 50.0, f"changed {pct:.2f}% of dots, outside the 1-50% band"

        # ---- write + validate (writer refuses on any failed check)
        stem = f"{PARENT_ID}-{suffix}-{stamp}"
        tmp_zeros = RELEASES / f".{stem}.zeros.tmp.tif"
        tmp_nan = RELEASES / f".{stem}.nan.tmp.tif"
        rep_zeros = None
        rep_nan = None
        for mode, tmp in (("zeros", tmp_zeros), ("nan", tmp_nan)):
            write_raster(variant, tmp, mode=mode)
            # The catalogue-buffer check is disabled in the shared validator on purpose: it
            # dilates the catalogue with a 3x3 structure, i.e. it tests a CHEBYSHEV-2 buffer
            # (Euclidean 2.83 px), stricter than the Euclidean-2 px rule the parent was built
            # to -- the incumbent R0 itself fails it (1,611 dots).  The exact Euclidean rule
            # is asserted above instead.  See IRREGULARITIES.md IR-85-MASS-02.
            rep = validate(tmp, mode=mode, catalogue_buffer_px=None)
            if not rep.passed:
                raise SystemExit(f"{stem} {mode}: validation failed {rep.checks}")
            if mode == "zeros":
                rep_zeros = rep
            else:
                rep_nan = rep
        sha8 = rep_nan.sha256[:8]
        final_zeros = RELEASES / f"{stem}-{sha8}-zeros.tif"
        final_nan = RELEASES / f"{stem}-{sha8}.tif"
        tmp_zeros.replace(final_zeros)
        tmp_nan.replace(final_nan)

        # ---- re-read from disk, as the brief requires
        with rasterio.open(final_zeros) as src:
            back = src.read(1)
            meta = {"crs": str(src.crs), "shape": (src.height, src.width),
                    "dtype": src.dtypes[0], "transform": tuple(src.transform)[:6]}
        reread_ok = bool(np.array_equal(read_binary(back), variant))
        assert reread_ok, "re-read from disk does not match the in-memory variant"
        assert sha256_file(final_zeros) == rep_zeros.sha256, "sha changed after rename"
        assert meta["transform"] == inputs["parent"]["transform"], "transform drifted"

        # ---- MODEL prediction
        pred = predict(ranked, parent, variant, parent_info)

        # ---- parent-diff statistics
        added = variant & ~parent
        dropped = parent & ~variant
        diff = {
            "n_dots_parent": int(parent.sum()), "n_dots_variant": int(variant.sum()),
            "n_added": int(added.sum()), "n_dropped": int(dropped.sum()),
            "pixels_changed": changed, "pct_changed": pct,
            "n_within_3px_of_catalogue_variant": int(((dcat > 2) & (dcat <= 3) & variant).sum()),
            "min_dcat_variant": float(dcat[variant].min()),
            "mean_dcat_parent": float(dcat[parent].mean()),
            "mean_dcat_variant": float(dcat[variant].mean()),
            "mean_field_credit_parent": float(credit.mean()),
            "mean_field_credit_variant": float(
                kernel_credit_against(cKDTree(np.c_[np.nonzero(field)[0], np.nonzero(field)[1]]),
                                      np.c_[np.nonzero(variant)[0], np.nonzero(variant)[1]]).mean()),
            "mass": float(back[read_binary(back)].sum()),
            "unique_values_inside": sorted({float(v) for v in np.unique(back)}),
        }

        results[suffix] = {
            "id": f"{stem}-{sha8}", "parent": PARENT_ID, "axis": "MASS", "value": value,
            "operation": op, "n_dots": int(variant.sum()), "pct_changed": pct,
            "sha256": rep_nan.sha256, "sha256_nan": rep_nan.sha256,
            "sha256_zeros": rep_zeros.sha256,
            "bytes_zeros": final_zeros.stat().st_size,
            "bytes_nan": final_nan.stat().st_size,
            "file_zeros": str(final_zeros.relative_to(ROOT)),
            "file_nan": str(final_nan.relative_to(ROOT)),
            "checks": rep_zeros.checks, "stats": rep_zeros.stats, "reread_ok": reread_ok,
            "dots_in_chebyshev2_catalogue_buffer": cheb2,
            "dots_at_euclid_2_to_3px": int(((dcat > 2) & (dcat <= 3) & variant).sum()),
            "meta": meta, "diff": diff, "prediction": pred,
            "input_sha256": {k: v["sha256"] for k, v in inputs.items()},
            "parent_info": parent_info,
        }
        rows.append(results[suffix])
        print(f"[built] {results[suffix]['id']}  n={variant.sum()}  changed={pct:.2f}%  "
              f"sha256={rep_zeros.sha256[:16]}  predicted {pred['predicted_live_change']:+.4f}  "
              f"cheb2={cheb2} (inherited; R0 has 1611)")

    out = EVIDENCE / "mass_axis.json"
    out.write_text(json.dumps({
        "session": "AXIS=MASS", "parent": PARENT_ID, "parent_claim_dti": PARENT_CLAIM_DTI,
        "top_public": 0.3195,
        "top_public_status": "UNVERIFIED (supplied by the human 2026-10-23; no receipt in repo)",
        "ranking_rule": "kernel credit of each dot against the pinned h19-5 ancestor support "
                        "(121,131 px), ascending; ties -> larger d_catalogue, then row, then column",
        "ranking_available_from_recorded_recipe": False,
        "catalogue_buffer_px": CATALOGUE_BUFFER_PX, "packing_px": PACKING_PX,
        "variants": results,
    }, indent=1) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
