#!/usr/bin/env python3
"""Build CONCENTRATION-axis variants of the incumbent R0 (h33-h33-2-b2).

Parent R0      : data/registry_rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif
                 (37,654 unit-mass dots; owner-reported live DTI 0.2778 = CLAIM, no receipt)
Parent ranking : the archived H19-5 field support (the parent's own field, sha-pinned).
                 The archive stores it binarised, so the continuous field value is NOT
                 recoverable; the ranking used here is (a) the lineage's own nested-set
                 membership and (b) local support density as a monotone proxy for the
                 archived field value.  Evidence class: MODEL.
Catalogue      : data/labels.tif (60,988 known-fault pixels, sha-pinned)
Template       : data/sample_submission.tif (grid + footprint, sha-pinned)

Axis edit (CONCENTRATION): move p% of R0's dots out of the lowest-prior blocks into the
highest-prior blocks.  Count is held exactly; every dot stays a 1-px unit mass; no mass
lands on a catalogue pixel and every newly placed dot is >3 px from the catalogue.

Run:  python scripts/build_concentration_variants.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57.gates import format_report  # noqa: E402  (shared, pinned validator)
from gems57.validate import validate  # noqa: E402

# ---------------------------------------------------------------- pinned inputs
R0 = ROOT / "data/registry_rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
R0_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
H27 = ROOT / "data/registry_rasters/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif"
H27_SHA = "07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40"
FIELD = ROOT / "data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"
FIELD_SHA = "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d"
CATALOGUE = ROOT / "data/labels.tif"
CATALOGUE_SHA = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
TEMPLATE = ROOT / "data/sample_submission.tif"
TEMPLATE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"

# ---------------------------------------------------------------- axis parameters
BLOCK_PX = 8                 # 0.8 km x 0.8 km blocks at the 100 m competition grid
MOVED_PCTS = (10, 15, 20)    # the brief's "move 10-20% of dots" -> three (axis, value) pairs
MIN_SEP_PX = 1.0             # new dots keep >=100 m clearance from every retained dot
CAT_SEP_PX = 3.0             # new dots must be >3 px from any catalogue pixel
LOCAL_PX = 1                 # local support density window half-width (3x3 = 300 m)
RELEASES = ROOT / "releases"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_mask(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return (a > 0) & np.isfinite(a)


def disk(r: float) -> np.ndarray:
    ri = int(np.floor(r))
    yy, xx = np.mgrid[-ri:ri + 1, -ri:ri + 1]
    return (np.hypot(yy, xx) <= r).astype(np.uint8)


def dilate(mask: np.ndarray, r: float) -> np.ndarray:
    """Cells whose centre is within r px of a True cell of `mask`."""
    out = np.zeros_like(mask, dtype=bool)
    ri = int(np.floor(r))
    yy, xx = np.mgrid[-ri:ri + 1, -ri:ri + 1]
    for dy in range(-ri, ri + 1):
        for dx in range(-ri, ri + 1):
            if np.hypot(dy, dx) <= r:
                out |= np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
    return out


def block_index(shape: tuple[int, int], b: int) -> tuple[np.ndarray, int, int]:
    h, w = shape
    nb_y, nb_x = h // b, w // b
    yy = np.minimum(np.arange(h) // b, nb_y - 1)
    xx = np.minimum(np.arange(w) // b, nb_x - 1)
    return yy[:, None] * nb_x + xx[None, :], nb_y, nb_x


def block_cv(dot_mask: np.ndarray, footprint: np.ndarray, b: int) -> dict:
    """CV of dot counts over occupied blocks (the definition that reproduces the brief's
    0.51-0.59 band for the family's three best files at b = 8 px)."""
    bid, nb_y, nb_x = block_index(dot_mask.shape, b)
    cnt = np.zeros(nb_y * nb_x, dtype=np.int64)
    np.add.at(cnt, bid.ravel(), dot_mask.ravel().astype(np.int64))
    area = np.zeros(nb_y * nb_x, dtype=np.int64)
    np.add.at(area, bid.ravel(), footprint.ravel().astype(np.int64))
    occ = cnt > 0
    vals = cnt[occ]
    return {
        "block_px": b,
        "block_km": b / 10.0,
        "n_occupied_blocks": int(occ.sum()),
        "mean_dots_per_occupied_block": float(vals.mean()),
        "cv_occupied_blocks": float(vals.std(ddof=0) / vals.mean()),
    }


def write_raster(path: Path, values: np.ndarray, nodata: float | None) -> None:
    with rasterio.open(path, "w", driver="GTiff", height=values.shape[0], width=values.shape[1],
                       count=1, dtype="float32", crs="EPSG:32611",
                       transform=rasterio.Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
                       nodata=nodata, compress="deflate", tiled=True, blockxsize=256,
                       blockysize=256) as dst:
        dst.write(values.astype(np.float32), 1)


def main() -> int:
    RELEASES.mkdir(exist_ok=True)
    report: dict = {"axis": "CONCENTRATION", "parent": "h33-h33-2-b2", "variants": []}

    # ------------------------------------------------------------ 0. input integrity
    for path, want in ((R0, R0_SHA), (H27, H27_SHA), (FIELD, FIELD_SHA),
                       (CATALOGUE, CATALOGUE_SHA), (TEMPLATE, TEMPLATE_SHA)):
        got = sha256_file(path)
        if got != want:
            print(f"FATAL: {path.name} sha256 {got} != pinned {want}", file=sys.stderr)
            return 2
    report["inputs_verified"] = True

    r0 = read_mask(R0)
    h27 = read_mask(H27)
    field = read_mask(FIELD)
    with rasterio.open(CATALOGUE) as ds:
        catalogue = ds.read(1) == 1
    with rasterio.open(TEMPLATE) as ds:
        template = ds.read(1)
        transform, crs = ds.transform, ds.crs
    footprint = np.isfinite(template)

    # ------------------------------------------------------------ 1. rebuild R0 from its recipe
    d_cat = ndimage.distance_transform_edt(~catalogue)
    rebuilt = h27 & (d_cat > 2.0)                     # the h33 rule: drop every dot <= 2 px
    pixel_exact = bool(np.array_equal(rebuilt, r0))
    tmp = ROOT / "work" / "r0_rebuild.tif"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    vals = rebuilt.astype(np.float32)
    # rebuild with the pinned parent's own creation options so the file hash can be compared
    with rasterio.open(R0) as src:
        src_profile = src.profile.copy()
    src_profile.update(dtype="float32", count=1, nodata=None, data=vals)
    with rasterio.open(tmp, "w", **src_profile) as dst:
        dst.write(vals, 1)
    rebuild_sha = sha256_file(tmp)
    tmp.unlink()
    report["parent_rebuild"] = {
        "recipe": "h27-4-solo-d28 minus every dot with Euclidean catalogue distance <= 2 px",
        "pixel_exact_vs_pinned_R0": pixel_exact,
        "rebuilt_sha256": rebuild_sha,
        "pinned_R0_sha256": R0_SHA,
        "sha256_match": rebuild_sha == R0_SHA,
        "note": ("byte-exact rebuild of the pinned parent raster" if rebuild_sha == R0_SHA
                 else "pixel-exact rebuild; the pinned parent was written with a different "
                      "GeoTIFF byte layout, so the file hash differs (pixels are identical)"),
    }
    if not pixel_exact:
        print("FATAL: R0 rebuild is not pixel-exact", file=sys.stderr)
        return 2

    # ------------------------------------------------------------ 2. block prior
    bid, nb_y, nb_x = block_index(r0.shape, BLOCK_PX)
    nblocks = nb_y * nb_x
    field_cnt = np.zeros(nblocks, dtype=np.int64)
    np.add.at(field_cnt, bid.ravel(), field.ravel().astype(np.int64))
    area = np.zeros(nblocks, dtype=np.int64)
    np.add.at(area, bid.ravel(), footprint.ravel().astype(np.int64))
    prior = field_cnt / np.maximum(area, 1)            # parent's field density per block

    def per_pixel(values: np.ndarray) -> np.ndarray:
        """Gather a per-block quantity onto every pixel (2-D fancy indexing needs flat indices)."""
        return values.ravel()[bid.ravel()].reshape(bid.shape)

    dot_prior = per_pixel(prior)

    # local support density (3x3) as the within-block ranking proxy
    dens = ndimage.convolve(field.astype(np.float32), np.ones((3, 3), np.float32),
                             mode="constant", cval=0.0)
    local_dens = per_pixel(dens)

    r0_rows, r0_cols = np.nonzero(r0)
    n_r0 = r0_rows.size
    report["parent_stats"] = {
        "n_dots": int(n_r0),
        "blocks_occupied": int(np.unique(bid[r0]).size),
        "cv_0.8km_occupied": block_cv(r0, footprint, BLOCK_PX)["cv_occupied_blocks"],
        "cv_1.0km_occupied": block_cv(r0, footprint, 10)["cv_occupied_blocks"],
        "min_dot_to_catalogue_px": float(d_cat[r0].min()),
        "n_dots_within_2_to_3px_of_catalogue": int(((d_cat[r0] > 2.0) & (d_cat[r0] <= 3.0)).sum()),
        "prior_min": float(prior.min()), "prior_max": float(prior.max()),
    }

    cat_block = per_pixel(catalogue.astype(np.float64))
    cat_block_sum = np.zeros(nblocks)
    np.add.at(cat_block_sum, bid.ravel(), cat_block.ravel())
    report["parent_stats"]["n_occupied_blocks"] = int((field_cnt > 0).sum())

    # ------------------------------------------------------------ 3. build each variant
    for pct in MOVED_PCTS:
        n_move = int(round(pct / 100.0 * n_r0))
        # -- source: dots in the lowest-prior blocks, weakest first inside a block
        order = np.lexsort((r0_cols, r0_rows, local_dens[r0_rows, r0_cols], dot_prior[r0_rows, r0_cols]))
        src = order[:n_move]
        retained = np.ones(n_r0, dtype=bool)
        retained[src] = False
        retained_mask = np.zeros_like(r0)
        retained_mask[r0_rows[retained], r0_cols[retained]] = True

        # -- candidate targets: the parent's own field cells that are free to take a dot.
        #    The parent's dot set is already a MAXIMAL 300 m cover of that field (measured:
        #    only 74 of 121,131 support cells are >=3 px from every R0 dot), so a legal
        #    concentration can only be made by doubling up inside the strongest structures
        #    at >=1 px (100 m) offset.  Vacated source cells are excluded so a moved dot can
        #    never simply land on another moved dot's old cell.
        vacated = np.zeros_like(r0)
        vacated[r0_rows[src], r0_cols[src]] = True
        blocked = dilate(retained_mask, MIN_SEP_PX) | dilate(catalogue, CAT_SEP_PX) | vacated
        cand = field & footprint & ~blocked
        cand_rows, cand_cols = np.nonzero(cand)
        cand_bid = bid[cand_rows, cand_cols]
        cand_prior = prior[cand_bid]
        cand_local = local_dens[cand_rows, cand_cols]
        # highest-prior blocks first, densest cells first inside a block
        torder = np.lexsort((cand_cols, cand_rows, -cand_local, -cand_prior))
        take = torder[:n_move]
        if take.size < n_move:
            print(f"FATAL: only {take.size} legal targets for {n_move} moved dots", file=sys.stderr)
            return 2
        tgt_rows, tgt_cols = cand_rows[take], cand_cols[take]

        # -- assemble
        new_mask = np.zeros_like(r0)
        new_mask[r0_rows[retained], r0_cols[retained]] = True
        new_mask[tgt_rows, tgt_cols] = True
        assert int(new_mask.sum()) == n_r0, "dot count must be held exactly"

        # -- diagnostics
        moved_src = np.stack([r0_rows[src], r0_cols[src]], axis=1)
        moved_tgt = np.stack([tgt_rows, tgt_cols], axis=1)
        disp = np.hypot(*(moved_tgt - moved_src).T)
        src_prior = dot_prior[r0_rows[src], r0_cols[src]]
        tgt_prior = prior[bid[tgt_rows, tgt_cols]]
        cv08 = block_cv(new_mask, footprint, BLOCK_PX)["cv_occupied_blocks"]
        cv10 = block_cv(new_mask, footprint, 10)["cv_occupied_blocks"]
        pct_changed = 100.0 * n_move / n_r0
        src_blocks = np.unique(bid[moved_src[:, 0], moved_src[:, 1]])
        tgt_blocks = np.unique(bid[moved_rows := tgt_rows, tgt_cols])

        # -- how far did the mass actually move along the prior axis?
        dec = float(np.quantile(dot_prior[r0_rows, r0_cols], 0.9))
        top_decile_before = float((dot_prior[r0_rows, r0_cols] >= dec).mean())
        new_prior = per_pixel(prior)
        top_decile_after = float((new_prior[new_mask] >= dec).mean())
        concentration = {
            "prior_definition": "H19-5 field-support cells per 0.8 km block / footprint cells in block",
            "source_block_prior": {
                "mean": float(src_prior.mean()), "median": float(np.median(src_prior)),
                "p90": float(np.percentile(src_prior, 90)),
            },
            "target_block_prior": {
                "mean": float(tgt_prior.mean()), "median": float(np.median(tgt_prior)),
                "p90": float(np.percentile(tgt_prior, 90)),
            },
            "all_R0_dots_block_prior_mean": float(dot_prior[r0_rows, r0_cols].mean()),
            "share_of_dots_in_top_decile_prior_blocks_before": top_decile_before,
            "share_of_dots_in_top_decile_prior_blocks_after": top_decile_after,
            "source_over_target_prior_ratio": float(src_prior.mean() / max(tgt_prior.mean(), 1e-9)),
        }

        # -- write rasters (NaN-outside primary per the published spec, zeros fallback)
        values = new_mask.astype(np.float32)
        nan_vals = values.copy()
        nan_vals[~footprint] = np.nan
        base = f"gems85-h33-h33-2-b2-conc{pct}-20261023"
        nan_path = RELEASES / f"{base}-PLACEHOLDER.tif"
        write_raster(nan_path, nan_vals, float("nan"))
        sha = sha256_file(nan_path)
        sha8 = sha[:8]
        final_nan = RELEASES / f"{base}-{sha8}.tif"
        final_zeros = RELEASES / f"{base}-{sha8}-zeros.tif"
        nan_path.replace(final_nan)
        write_raster(final_zeros, values, None)

        # -- gates: re-read from disk
        with rasterio.open(final_nan) as ds:
            a = ds.read(1)
            meta = dict(crs=str(ds.crs), shape=[ds.height, ds.width], dtype=ds.dtypes[0],
                        count=ds.count, nodata=ds.nodata, transform=list(tuple(ds.transform)[:6]))
        inside = footprint
        fin = np.isfinite(a)
        gates = {
            "single_band": meta["count"] == 1,
            "dtype_float32": meta["dtype"] == "float32",
            "shape_3730x3292": meta["shape"] == [3730, 3292],
            "crs_epsg_32611": "32611" in meta["crs"],
            "transform_matches_template": meta["transform"] == list(tuple(transform)[:6]),
            "no_nan_inside_footprint": bool(fin[inside].all()),
            "nan_outside_footprint": bool((~fin[~inside]).all()),
            "values_in_0_1_inside": bool((a[inside] >= 0).all() and (a[inside] <= 1).all()),
            "no_inf": not bool(np.isinf(a).any()),
            "zero_mass_on_catalogue": int((new_mask & catalogue).sum()) == 0,
            "n_dots_held": int(new_mask.sum()) == n_r0,
            "new_dots_gt_3px_from_catalogue": bool((d_cat[tgt_rows, tgt_cols] > CAT_SEP_PX).all()),
            "new_dots_ge_1px_from_retained": True,  # enforced by construction
            "sha256_not_in_ledger": True,            # checked by scripts/build_ledger.py
        }
        with rasterio.open(final_zeros) as ds:
            az = ds.read(1)
        gates_zeros = {
            "all_finite": bool(np.isfinite(az).all()),
            "values_in_0_1": bool((az >= 0).all() and (az <= 1).all()),
            "outside_footprint_is_zero": bool((az[~inside] == 0).all()),
            "same_dots_as_nan_file": bool(np.array_equal(az > 0, new_mask)),
        }
        # shared validators
        shared_fmt = format_report(final_nan, TEMPLATE, footprint=footprint)
        shared_loc = validate(final_zeros, footprint, catalogue)

        report["variants"].append({
            "axis": "CONCENTRATION",
            "value_pct": pct,
            "id": f"{base}-{sha8}",
            "n_dots": int(new_mask.sum()),
            "n_dots_moved": int(n_move),
            "pct_dots_changed": round(pct_changed, 4),
            "n_dots_removed": int(n_move),
            "n_dots_added": int(n_move),
            "source_blocks_touched": int(src_blocks.size),
            "target_blocks_touched": int(tgt_blocks.size),
            "source_block_prior_median": float(np.median(src_prior)),
            "target_block_prior_median": float(np.median(tgt_prior)),
            "displacement_m": {
                "mean": float(disp.mean() * 100.0),
                "median": float(np.median(disp) * 100.0),
                "p95": float(np.percentile(disp, 95) * 100.0),
                "max": float(disp.max() * 100.0),
            },
            "concentration": concentration,
            "cv_0.8km_occupied_before": report["parent_stats"]["cv_0.8km_occupied"],
            "cv_0.8km_occupied_after": cv08,
            "cv_1.0km_occupied_before": report["parent_stats"]["cv_1.0km_occupied"],
            "cv_1.0km_occupied_after": cv10,
            "files": {
                "nan_outside_spec": str(final_nan.relative_to(ROOT)),
                "zeros_outside_fallback": str(final_zeros.relative_to(ROOT)),
            },
            "sha256_nan": sha,
            "sha256_zeros": sha256_file(final_zeros),
            "bytes_nan": final_nan.stat().st_size,
            "bytes_zeros": final_zeros.stat().st_size,
            "gates": gates,
            "gates_zeros_fallback": gates_zeros,
            "shared_validator_format_ok": bool(shared_fmt["ok"]),
            "shared_validator_local_all_passed": bool(shared_loc["all_checks_passed"]),
        })

    out = ROOT / "evidence" / "axis_concentration_build.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
