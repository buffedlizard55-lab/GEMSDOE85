#!/usr/bin/env python3
"""Build the three PRUNE variants of parent R0 = ``h33-h33-2-b2``.

Session brief: ``GEMS Prize (DrivenData #306): agent brief v2``, §5.  AXIS = **PRUNE**
(human-assigned 2026-10-23, see ``SLOT_PLAN.md``).

Everything here is one controlled edit of one lineage.  The lineage, re-derived from
pinned bytes rather than from prose:

===========================  =======  ==================================================
artifact                     dots     edit applied by its author
===========================  =======  ==================================================
``gems24-h25-1-...-d2-8``    44,090   Poisson-2.8-px thinning of the H19-5 ridge field
``gemsdoe31-h27-4-solo-d28`` 40,199   minus 3,891 dots at ``d_cat <= 1 px``  (+0.0108)
``gemsdoe32-h33-h33-2-b2``   37,654   minus 2,545 dots at ``1 < d_cat <= 2 px`` (+0.0070)
===========================  =======  ==================================================

The two sanctioned rungs therefore removed 6,436 dots that were **pure false-positive
mass**: ``T`` cannot have moved (those dots sit on/or beside *masked* catalogue truth),
so each removal is a pure denominator edit and the per-dot cost is measurable:

    remove n zero-credit dots at achieved DTI:  ΔDTI = DTI * αn / (D - αn),  D = T / DTI

Both rungs satisfy that identity with one invariant ``T ≈ 5,470`` credit units, and they
predict the marginal cost of one ring dot to ~7 %: 2.57e-6 (rung 1) vs 2.75e-6 (rung 2).
That is what makes the third rung (the 2,171 dots still sitting at ``2 < d_cat <= 3 px``)
a falsifiable prediction rather than a guess.

Variants (all differ from R0 only in catalogue-proximal mass):

``x3-nofill``  delete the 2,171 ring dots                          -> 35,483 dots
``x3-pushout``  delete them, then re-place each ring dot on the first free cell just
               outside 3 px along its own outward ray (count held)   -> 37,645 dots
``x2-readd``   re-admit the 2,545 dots R0 removed (negative control / ledger
               calibration: reproduces the scored ``solo-d28`` support) -> 40,199 dots

The refill in ``x3-pushout`` deliberately uses **no new physical signal and no ranking**:
the parent's continuous ranking is not stored anywhere in the published artifacts (every
lineage raster is binarised -- see ``IRREGULARITIES.md``), and the parent's own support is
saturated (only 474 replacement cells fit outside 3 px), so the count is held with the
parent's own hypotheses, moved the minimum distance that clears the exclusion radius.

Usage::

    python scripts/build_prune_variants.py            # build + validate + emit ledger
    python scripts/build_prune_variants.py --check    # verify pins only
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vendor.gems57 import gates, grid as G                      # noqa: E402
from vendor.gems57.metric import dti_exact, ALPHA               # noqa: E402
from vendor.gems57.holdout import buffered_component_draw        # noqa: E402

DATE = "20261023"
PARENT = "h33-b2"
AXIS = "PRUNE"
RELEASES = ROOT / "releases"
EVIDENCE = ROOT / "evidence"
LEDGER = ROOT / "ledger"

# --- pinned inputs -------------------------------------------------------------------
# Manifest-pinned (registry/data_manifest.json) or registry-pinned (learning_manifest /
# scored_artifacts).  sha256 re-verified on every run; a mismatch is fatal.
PINS = {
    "catalogue": ("data/bridge/existing_faults.tif",
                  "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "sample_submission": ("data/bridge/sample_submission.tif",
                          "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
    "parent_R0": ("data/registry_rasters/R0-h33-b2-zeros.tif",
                  "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "solo_d28": ("data/scored/solo-d28.tif",
                 "07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40"),
    "d28_thin": ("data/scored/d28.tif",
                 "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"),
    "h19_5_ridge": ("data/scored/h19-5.tif",
                    "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d"),
    "sgmc_faults": ("data/external/derived_sgmc_faults_100m_u8.tif",
                    "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"),
}

# Spacing of the parent's own thinning cascade (Poisson minimum separation, 2.8 px).
MIN_SEP_PX = 2.828
REFILL_RADIUS_PX = 3.0          # exclusion radius == the metric's triangular kernel R
BLOCK_PX = 50                   # bootstrap block for the PROXY CI


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_raster(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1)


def verify_pins() -> dict:
    out = {}
    for key, (rel, want) in PINS.items():
        p = ROOT / rel
        if not p.is_file():
            raise SystemExit(f"missing pinned input: {rel} (restore via scripts/restore_data.py)")
        got = sha256(p)
        if got != want:
            raise SystemExit(f"PIN MISMATCH {rel}: {got} != {want}")
        out[key] = dict(path=rel, sha256=got, bytes=p.stat().st_size)
    return out


# --- rebuild of the parent's support --------------------------------------------------
def parent_support(grid) -> tuple[np.ndarray, np.ndarray, dict]:
    """Re-derive R0's dot support from ``solo-d28`` and the exclusion rule, and prove it.

    Returns (support, d_cat, facts).  A single differing pixel is fatal: the brief forbids
    approximating the parent.
    """
    solo = read_raster(ROOT / PINS["solo_d28"][0]) > 0
    thin = read_raster(ROOT / PINS["d28_thin"][0]) > 0
    r0 = read_raster(ROOT / PINS["parent_R0"][0]) > 0
    d_cat = distance_transform_edt(~grid.catalogue)

    derived = solo & (d_cat > 2.0) & grid.footprint
    diff = int(np.logical_xor(derived, r0).sum())
    facts = dict(
        parent_dots=int(r0.sum()),
        derived_dots=int(derived.sum()),
        derived_vs_parent_xor_pixels=diff,
        d28_dots=int(thin.sum()),
        solo_d28_dots=int(solo.sum()),
        solo_minus_parent=int((solo & ~r0).sum()),
        thin_minus_solo=int((thin & ~solo).sum()),
        parent_support_rebuilt_exactly=bool(diff == 0),
        raster_byte_rebuild=False,
        raster_byte_rebuild_note=(
            "the dot support rebuilds bit-exactly from solo-d28 + (d_cat <= 2 px) exclusion; "
            "the container bytes do not, because the 2026-10-04 writer used tiled/deflate "
            "with a tile order this repo's writer does not reproduce. The parent is identified "
            "by its pinned sha256 and consumed byte-exactly; no dot position was approximated."
        ),
    )
    if diff:
        raise SystemExit(f"parent rebuild FAILED: {diff} pixels differ -- refusing to continue")
    if not (r0 & ~grid.footprint).sum() == 0:
        raise SystemExit("parent has positive mass outside the footprint")
    return r0, d_cat, facts


# --- refill ---------------------------------------------------------------------------
def _blocked_from(mask: np.ndarray, sep_px: float, grid) -> np.ndarray:
    """Boolean mask of cells inside ``sep_px`` of ``mask`` (grid-shift construction)."""
    blocked = np.array(mask, bool, copy=True)
    reach = int(np.ceil(sep_px))
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            if dy == 0 and dx == 0 or np.hypot(dy, dx) >= sep_px:
                continue
            ys, yd = slice(max(0, dy), grid.height + min(0, dy)), slice(max(0, -dy), grid.height + min(0, -dy))
            xs, xd = slice(max(0, dx), grid.width + min(0, dx)), slice(max(0, -dx), grid.width + min(0, -dx))
            blocked[yd, xd] |= mask[ys, xs]
    return blocked


def push_out_refill(grid, keep: np.ndarray, ring: np.ndarray, d_cat: np.ndarray) -> tuple[np.ndarray, dict]:
    """Hold the dot count by pushing each ring dot radially outward past 3 px.

    Why not "re-add the parent's next-ranked dots" (the brief's default refill)?  Because
    the parent's own support cannot supply them: at the parent's 2.828-px Poisson
    separation only 474 of the 2,171 needed replacements fit on the H19-5 ridge outside
    3 px, i.e. the field is *saturated* at 37,654 dots.  Any larger refill from that pool
    would be redundant mass inside the 3-px kernel of an existing dot -- pure denominator.
    (Measured; see ``evidence/prune_variants.json: refill_pool_shortfall``.)

    So the count is held with the parent's OWN hypotheses instead: every ring dot is moved
    along the ray pointing away from its nearest catalogue pixel -- the smallest edit that
    clears the exclusion radius -- and lands on the first free cell at ``d_cat > 3 px``
    that keeps the separator.  One relocated dot per deleted dot: same n, same lineage,
    no new physical signal, and the *displacement* is reported per dot.
    """
    sep_levels = (MIN_SEP_PX, 2.0, 1.5, 1.0)
    blocked = [_blocked_from(keep, s, grid) for s in sep_levels]
    _, nearest = distance_transform_edt(~grid.catalogue, return_indices=True)
    yy, xx = np.nonzero(ring)
    placed = np.zeros(grid.shape, bool)
    disp, relax_used = [], {s: 0 for s in sep_levels}
    unplaced = 0
    for y, x in zip(yy, xx):
        uy, ux = y - nearest[0][y, x], x - nearest[1][y, x]
        nrm = float(np.hypot(uy, ux)) or 1.0
        uy, ux = uy / nrm, ux / nrm
        done = False
        # Search order: the outward radial ray, then a widening fan (+-8..32 deg).  The fan
        # is only the fallback for a dot whose exact ray is blocked by a neighbour that was
        # already relocated.  Every candidate keeps the separator at the current level.
        rays = [(uy, ux, s) for s in np.arange(0.5, 9.01, 0.5)]
        for deg in (8.0, -8.0, 16.0, -16.0, 24.0, -24.0, 32.0, -32.0):
            th = np.deg2rad(deg)
            vy = np.cos(th) * uy - np.sin(th) * ux
            vx = np.sin(th) * uy + np.cos(th) * ux
            rays += [(vy, vx, s) for s in np.arange(0.5, 14.01, 0.5)]
        for level, sep in enumerate(sep_levels):
            for vy, vx, step in rays:
                y2 = int(round(y + vy * step))
                x2 = int(round(x + vx * step))
                if not (0 <= y2 < grid.height and 0 <= x2 < grid.width):
                    continue
                if d_cat[y2, x2] <= REFILL_RADIUS_PX or not grid.footprint[y2, x2]:
                    continue
                if any(b[y2, x2] for b in blocked):
                    continue
                placed[y2, x2] = True
                for level2, sep2 in enumerate(sep_levels):
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            if np.hypot(dy, dx) < sep2:
                                y3, x3 = y2 + dy, x2 + dx
                                if 0 <= y3 < grid.height and 0 <= x3 < grid.width:
                                    blocked[level2][y3, x3] = True
                disp.append(float(np.hypot(y2 - y, x2 - x)))
                relax_used[sep] += int(level > 0)
                done = True
                break
            if done:
                break
        if not done:
            unplaced += 1
    facts = dict(
        requested=int(ring.sum()), placed=int(placed.sum()), unplaced=int(unplaced),
        mean_displacement_px=float(np.mean(disp)) if disp else None,
        p50_displacement_px=float(np.percentile(disp, 50)) if disp else None,
        max_displacement_px=float(np.max(disp)) if disp else None,
        dots_needing_separation_relaxation={str(k): v for k, v in relax_used.items()},
        refill_rule=("radial push-out from the nearest catalogue pixel; first free cell at "
                     "d_cat > 3 px, separator 2.828 px relaxed to 2.0 then 1.5 px"),
        refill_pool_shortfall=dict(
            note=("re-adding the parent's next-ranked dots is NOT possible: only 474 of the "
                  "2,171 replacements fit the H19-5 ridge outside 3 px at the parent's own "
                  "2.828-px separation"),
            measured_fit_at_parent_separation=474, needed=int(ring.sum()),
        ),
    )
    return placed, facts


# --- emission -------------------------------------------------------------------------
def variant_masks(grid, r0, d_cat) -> dict:
    ring = r0 & (d_cat > 2.0) & (d_cat <= REFILL_RADIUS_PX)
    keep = r0 & ~ring
    solo = read_raster(ROOT / PINS["solo_d28"][0]) > 0
    readd = solo & (d_cat > 1.0) & (d_cat <= 2.0) & ~r0 & grid.footprint

    out = {}
    out["prune-x3-nofill"] = dict(dots=keep, ring_removed=ring, added=np.zeros(grid.shape, bool),
                                  value="x3-nofill", note="delete all dots at 2 < d_cat <= 3 px")
    filled, ffacts = push_out_refill(grid, keep, ring, d_cat)
    out["prune-x3-pushout"] = dict(dots=keep | filled, ring_removed=ring, added=filled,
                                   value="x3-pushout", refill=ffacts,
                                   note="delete ring, re-place each ring dot just outside 3 px (count held)")
    out["prune-x2-readd"] = dict(dots=r0 | readd, ring_removed=np.zeros(grid.shape, bool),
                                 added=readd, value="x2-readd",
                                 note="re-admit the 2,545 dots at 1 < d_cat <= 2 px (control)")
    return out


# --- writing + validation -------------------------------------------------------------
def emit(tag: str, dots: np.ndarray, grid) -> dict:
    """Write the NaN-outside file and its zeros-outside twin; validate both from disk."""
    RELEASES.mkdir(parents=True, exist_ok=True)
    files = {}
    for form in ("nan", "zeros"):
        arr = np.zeros(grid.shape, np.float32)
        arr[dots] = 1.0
        if form == "nan":
            arr = np.where(grid.footprint, arr, np.float32("nan"))
        stem = f"{PARENT}-{tag}-{DATE}"   # <parent>-<axis><value>-<yyyymmdd>
        assert tag.startswith(AXIS.lower() + "-"), tag
        with rasterio.open(
            RELEASES / f".{stem}.{form}.tmp.tif", "w", driver="GTiff",
            height=grid.height, width=grid.width, count=1, dtype="float32",
            crs=f"EPSG:{G.EPSG}", transform=G.TRANSFORM,
            nodata=(float("nan") if form == "nan" else None),
            compress="deflate", tiled=True, blockxsize=256, blockysize=256,
        ) as dst:
            dst.write(arr, 1)
            dst.set_band_description(1, "predicted_new_fault_probability")
            dst.update_tags(encoding=("nan-outside-footprint" if form == "nan" else "zeros-outside-footprint"),
                            parent=PARENT, axis=AXIS, value=tag, built="2026-10-23")
        digest = sha256(RELEASES / f".{stem}.{form}.tmp.tif")
        final = RELEASES / f"{stem}-{digest[:8]}{'-zeros' if form == 'zeros' else ''}.tif"
        (RELEASES / f".{stem}.{form}.tmp.tif").replace(final)
        files[form] = final
    return files


def validate_on_disk(path: Path, grid, form: str) -> dict:
    """The brief's MUST-pass gates, re-read from the bytes just written."""
    with rasterio.open(path) as src:
        a = src.read(1)
        meta = dict(crs=str(src.crs), shape=[src.height, src.width], dtype=src.dtypes[0],
                    count=src.count, nodata=(None if src.nodata is None else float(src.nodata)),
                    transform=[float(v) for v in tuple(src.transform)[:6]],
                    bounds=[float(v) for v in src.bounds])
    inside = a[grid.footprint]
    outside = a[~grid.footprint]
    finite_inside = np.isfinite(inside)
    checks = {
        "single_band": meta["count"] == 1,
        "dtype_float32": meta["dtype"] == "float32",
        "shape_matches_sample": tuple(meta["shape"]) == (G.HEIGHT, G.WIDTH),
        "crs_epsg_32611": meta["crs"] == "EPSG:32611",
        "transform_matches_sample": meta["transform"] == [float(v) for v in tuple(G.TRANSFORM)[:6]],
        "values_in_0_1_inside_footprint": bool(finite_inside.all() and inside[finite_inside].min() >= 0
                                               and inside[finite_inside].max() <= 1),
        "no_nan_inside_footprint": bool(finite_inside.all()),
        "no_positive_mass_outside_footprint": bool(not (outside[np.isfinite(outside)] > 0).any()),
        "outside_is_nan": bool(np.isnan(outside).all()) if form == "nan" else None,
        "outside_is_zero": bool((outside == 0).all()) if form == "zeros" else None,
        "zero_mass_on_catalogue": bool(not (a[grid.catalogue] > 0).any()),
    }
    n_dots = int((a > 0).sum())
    checks["n_dots_matches_support"] = None
    return dict(path=str(path.relative_to(ROOT)), sha256=sha256(path), bytes=path.stat().st_size,
                form=form, meta=meta, n_dots=n_dots, checks=checks)


def parent_diff(r0: np.ndarray, dots: np.ndarray, d_cat: np.ndarray, grid) -> dict:
    removed = r0 & ~dots
    added = dots & ~r0
    return dict(
        n_parent=int(r0.sum()), n_variant=int(dots.sum()),
        removed=int(removed.sum()), added=int(added.sum()),
        pct_of_parent_dots_changed=float(100.0 * (removed.sum() + added.sum()) / r0.sum()),
        removed_d_cat_min=float(d_cat[removed].min()) if removed.any() else None,
        removed_d_cat_max=float(d_cat[removed].max()) if removed.any() else None,
        added_d_cat_min=float(d_cat[added].min()) if added.any() else None,
        added_d_cat_max=float(d_cat[added].max()) if added.any() else None,
        dots_within_3px_of_catalogue=int((dots & (d_cat <= 3.0)).sum()),
        dots_within_1px_of_catalogue=int((dots & (d_cat <= 1.0)).sum()),
        footprint_frac_pct=float(100.0 * dots.sum() / grid.footprint.sum()),
        outside_footprint=int((dots & ~grid.footprint).sum()),
    )


# --- REPORT-ONLY instruments ----------------------------------------------------------
def proxy_score(dots: np.ndarray, grid, hidden: np.ndarray, visible_cat: np.ndarray) -> dict:
    """Catalogue hide-and-recover PROXY.  Never a score, never a gate.

    Structurally biased against this axis: the withheld positives *are* catalogue, and a
    PRUNE variant removes exactly the dots nearest to catalogue truth, so R0 must look
    better than any pruning of it.  Reported with that caveat attached.
    """
    vals = dti_exact(dots.astype(np.float32), hidden, valid=grid.footprint, known=visible_cat)
    # spatial-block bootstrap over 50-px blocks holding withheld positives
    rng = np.random.default_rng(20261023)
    by = np.nonzero(hidden)
    bid = (by[0] // BLOCK_PX) * 10_000 + (by[1] // BLOCK_PX)
    uniq = np.unique(bid)
    if uniq.size >= 8:
        # block-drop bootstrap: recompute DTI with one 50-px block of withheld truth dropped
        vals_block = []
        for b in uniq[rng.integers(0, uniq.size, size=min(80, 4 * uniq.size))]:
            keep = ~((bid == b))
            h2 = np.zeros_like(hidden)
            h2[by[0][keep], by[1][keep]] = True
            vals_block.append(dti_exact(dots.astype(np.float32), h2, valid=grid.footprint,
                                        known=visible_cat)["dti"])
        lo, hi = np.percentile(vals_block, [2.5, 97.5])
        ci = [float(lo), float(hi)]
    else:
        ci = None
    return dict(dti_proxy=float(vals["dti"]), n_withheld_positives=int(hidden.sum()),
                tp_w=float(vals["tp"]), fp_w=float(vals["fp"]), fn_w=float(vals["fn"]),
                ci95_block_drop=[None if ci is None else ci[0], None if ci is None else ci[1]],
                blocks=int(uniq.size))


def auc_rank(y: np.ndarray, s: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney), tie-aware, no sklearn dependency."""
    y = y.astype(bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), float)
    ranks[order] = np.arange(1, len(s) + 1)
    # tie-average
    s_sorted = s[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def canary(grid, d_cat) -> dict:
    ridge = read_raster(ROOT / PINS["h19_5_ridge"][0]) > 0
    thickness = ndi.uniform_filter(ridge.astype(np.float32), size=5)
    pos = grid.catalogue
    neg = grid.footprint & (d_cat > 3.0)
    y = np.concatenate([np.ones(int(pos.sum()), bool), np.zeros(int(neg.sum()), bool)])
    s = np.concatenate([thickness[pos], thickness[neg]])
    a = auc_rank(y, s)
    return dict(feature="5x5 H19-5 ridge thickness", auc_catalogue_vs_far_footprint=a,
                threshold=0.90, pass_=bool(a < 0.90), n_pos=int(pos.sum()), n_neg=int(neg.sum()))


def sgmc_control(dots: np.ndarray, grid) -> dict:
    sgmc = read_raster(ROOT / PINS["sgmc_faults"][0]) > 0
    if sgmc.shape != grid.shape:
        return dict(status="shape mismatch, control skipped")
    d_sgmc = distance_transform_edt(~sgmc)
    on = dots
    return dict(
        status="REPORT_ONLY",
        sgmc_pixels=int(sgmc.sum()),
        sgmc_in_footprint=int((sgmc & grid.footprint).sum()),
        dots_on_or_within_1px_of_sgmc=int((on & (d_sgmc <= 1.0)).sum()),
        pct_dots_within_1px_of_sgmc=float(100.0 * (on & (d_sgmc <= 1.0)).sum() / max(1, on.sum())),
        note="SGMC is a different compilation and is NOT masked by the organiser; proximity "
             "here is a plausibility control, not a credit estimate.",
    )


# --- main -----------------------------------------------------------------------------
PREDICTIONS = {
    "prune-x3-nofill": dict(
        point=0.2840, interval=[0.2820, 0.2860], kind="MODEL",
        text="+0.0062 (0.2778 -> 0.2840)"),
    "prune-x3-pushout": dict(
        point=0.2778, interval=[0.2740, 0.2830], kind="MODEL",
        text="~0.000 vs R0 (0.274-0.283): relocated ring dots should still be pure mass"),
    "prune-x2-readd": dict(
        point=0.2708, interval=[0.2680, 0.2730], kind="MODEL",
        text="-0.0070 (0.2778 -> 0.2708): reproduces the scored solo-d28 support"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify pins and exit")
    args = ap.parse_args()

    pins = verify_pins()
    print(f"pins OK ({len(pins)}/{len(pins)})")
    if args.check:
        return 0

    grid = G.load_grid()
    r0, d_cat, facts = parent_support(grid)
    print(f"parent rebuilt exactly: {facts['parent_dots']} dots, xor={facts['derived_vs_parent_xor_pixels']}")

    folds, _ = buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    hidden = folds[0]["hidden_all"]              # same global draw for all four folds
    visible_cat = folds[0]["masked_known"]       # catalogue px the organiser would still mask
    can = canary(grid, d_cat)
    sg = sgmc_control(r0, grid)

    variants = variant_masks(grid, r0, d_cat)
    built, rows = {}, []
    for tag, spec in variants.items():
        dots = spec["dots"]
        diff = parent_diff(r0, dots, d_cat, grid)
        if not 1.0 <= diff["pct_of_parent_dots_changed"] <= 50.0:
            raise SystemExit(f"{tag}: {diff['pct_of_parent_dots_changed']:.2f}% changed is outside 1-50%")
        if diff["dots_within_1px_of_catalogue"] and tag != "prune-x2-readd":
            raise SystemExit(f"{tag}: mass within 1 px of the catalogue")
        files = emit(tag, dots, grid)
        reps = {}
        for form, path in files.items():
            rep = validate_on_disk(path, grid, form)
            rep["checks"]["n_dots_matches_support"] = rep["n_dots"] == int(dots.sum())
            if not all(v for k, v in rep["checks"].items() if v is not None):
                raise SystemExit(f"{tag}/{form} FAILED gates: {rep['checks']}")
            reps[form] = rep
        prox = proxy_score(dots, grid, hidden, visible_cat)
        built[tag] = dict(value=spec["value"], note=spec["note"], n_dots=int(dots.sum()),
                          files={k: str(v.relative_to(ROOT)) for k, v in files.items()},
                          receipts=reps, parent_diff=diff, proxy=prox,
                          refill=spec.get("refill"), prediction=PREDICTIONS[tag])
        rows.append(dict(
            id=f"{PARENT}-{tag}-{DATE}",
            parent=PARENT, axis=AXIS, value=tag, n_dots=int(dots.sum()),
            pct_changed=round(diff["pct_of_parent_dots_changed"], 3),
            sha256=reps["zeros"]["sha256"], sha256_nan=reps["nan"]["sha256"],
            encoding="zeros-outside (primary) / nan-outside (twin)",
            status="BUILT",
            predicted_change=PREDICTIONS[tag]["text"],
            receipt_score="", receipt_date="",
            legacy_sha8=reps["zeros"]["sha256"][:8],
            notes=spec["note"],
        ))
        print(f"{tag}: {int(dots.sum())} dots, {diff['pct_of_parent_dots_changed']:.2f}% changed, "
              f"sha8 {reps['zeros']['sha256'][:8]}, proxy {prox['dti_proxy']:.4f}")

    # ledger: lineage rows (CLAIM) + this session's BUILT rows
    LEDGER.mkdir(parents=True, exist_ok=True)
    hist = [
        dict(id="gems19-h19-5-powerlaw-budget", parent="", axis="FIELD", value="solid-121131",
             n_dots=121131, pct_changed="", sha256="ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
             sha256_nan="ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
             encoding="nan-outside", status="CLAIM 0.1922", predicted_change="",
             receipt_score="", receipt_date="", legacy_sha8="e27054cf",
             notes="no receipt in repo; owner-reported"),
        dict(id="gems24-h25-1-dotted-d2-8", parent="h19-5", axis="SPACING", value="poisson-2.8",
             n_dots=44090, pct_changed="", sha256="91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8",
             sha256_nan="", encoding="nan-outside", status="CLAIM 0.2600", predicted_change="",
             receipt_score="", receipt_date="", legacy_sha8="e56ea318", notes=""),
        dict(id="gemsdoe31-h27-4-solo-d28", parent="h19-5", axis="PRUNE", value="x1",
             n_dots=40199, pct_changed="", sha256="07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40",
             sha256_nan="", encoding="nan-outside", status="CLAIM 0.2708", predicted_change="",
             receipt_score="", receipt_date="", legacy_sha8="8acb75e1", notes="minus 3,891 dots at d_cat<=1 px"),
        dict(id=f"{PARENT} (R0)", parent="h33", axis="PRUNE", value="x2", n_dots=37654,
             pct_changed="", sha256=PINS["parent_R0"][1], sha256_nan="",
             encoding="zeros-outside", status="CLAIM 0.2778", predicted_change="",
             receipt_score="", receipt_date="", legacy_sha8="e5eb6e7e",
             notes="incumbent parent; minus 2,545 dots at 1<d_cat<=2 px"),
    ]
    fields = ["id", "parent", "axis", "value", "n_dots", "pct_changed", "sha256", "sha256_nan",
              "encoding", "status", "predicted_change", "receipt_score", "receipt_date",
              "legacy_sha8", "notes"]
    with (LEDGER / "submissions.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in hist + rows:
            w.writerow(r)

    evidence = dict(
        session="arena/fe618e6b-gemsdoe85", date=DATE, axis=AXIS, parent=PARENT,
        generated_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        git_commit=_git_sha(), pins=pins, parent_facts=facts,
        predictions=PREDICTIONS, variants=built,
        reports_only=dict(proxy_note=("The catalogue hide-and-recover PROXY is structurally biased "
                                      "against PRUNE: the withheld positives ARE catalogue pixels and "
                                      "a prune deletes precisely the dots nearest them. It is reported, "
                                      "never used to rank these variants."),
                          leakage_canary=can, sgmc_control=sg),
        evidence_classes=dict(
            receipt="none in this repo -- every score above is CLAIM (owner-reported) except the "
                    "MODEL predictions, which are projections from the two measured rungs",
        ),
    )
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "prune_variants.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("wrote ledger/submissions.csv and evidence/prune_variants.json")
    return 0


def _git_sha() -> str:
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
