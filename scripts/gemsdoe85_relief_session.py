#!/usr/bin/env python3
"""GEMSDOE85 · session brief v2 · AXIS = RELIEF on parent R0 (`h33-h33-2-b2`).

Builds 3 controlled, fixed-count (`37,654` dots) variants of R0 differing on AXIS = RELIEF
(tercile-mass shifts across Basin / Piedmont / Range-front terciles from `det_elev` +
`det_elev_slope`), while enforcing Hard Constraint #4 (`0` catalogue mass and `d_cat > 3.0 px`
globally across every emitted pixel):

  reliefp2r10    shift 10.0 % of R0 mass (-3,765 Piedmont -> +3,765 Range-front), count=37,654
  reliefbp2r15   shift 15.0 % of R0 mass (-1,883 Basin, -3,765 Piedmont -> +5,648 Range-front), count=37,654
  reliefr2bp10   shift 10.0 % of R0 mass (+1,883 Basin, +1,882 Piedmont <- -3,765 Range-front), count=37,654

Also computes an unshipped diagnostic control (`ctrl_collar3`, 0 % tercile shift) that isolates
the `d_cat <= 3.0 px` in-tercile collar replacement from the pure inter-tercile RELIEF shift.

Nothing here submits, logs in, scrapes, or contacts drivendata.org / dropbox.com.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
for sub in (ROOT / "src", ROOT / "vendor"):
    if str(sub) not in sys.path:
        sys.path.insert(0, str(sub))

from gems57 import evaluate_holdout as ev57                      # noqa: E402
from gems57.grid import Grid, TRANSFORM                          # noqa: E402
from gems57.holdout import buffered_component_draw               # noqa: E402
from gems85.metric import dti, kernel_dilate                     # noqa: E402
from gems85.r0_lineage import (                                  # noqa: E402
    PATHS,
    PINS,
    catalogue_distance,
    footprint,
    load_catalogue,
    sha256_file,
)
from gems85.relief_lineage import (                              # noqa: E402
    EXTRA_PATHS,
    EXTRA_PINS,
    build_relief_fields,
    rebuild_and_verify_r0_bytes,
    shift_relief_terciles,
    verify_manifest_hashes,
)

DATE = "20261023"
BOOTSTRAP_SEED = 851023
BOOTSTRAP_DRAWS = 400
HOLDOUT_SEED = 20

NOTES = {
    "reliefp2r10": (
        "R0 h33-2-b2; RELIEF piedmont->range +10% (3765 dots, d_cat>3px, n=37654 fixed); "
        "pred +0.008 (+0.001..+0.015) MODEL"
    ),
    "reliefbp2r15": (
        "R0 h33-2-b2; RELIEF basin+piedmont->range +15% (5648 dots, d_cat>3px, n=37654 fixed); "
        "pred +0.006 (-0.002..+0.014) MODEL"
    ),
    "reliefr2bp10": (
        "R0 h33-2-b2; RELIEF range->basin+piedmont +10% (3765 dots, d_cat>3px, n=37654 fixed); "
        "pred -0.002 (-0.010..+0.007) MODEL"
    ),
}
PREDICTIONS = {
    "reliefp2r10": "+0.008 (+0.001 to +0.015) MODEL",
    "reliefbp2r15": "+0.006 (-0.002 to +0.014) MODEL",
    "reliefr2bp10": "-0.002 (-0.010 to +0.007) MODEL",
}


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:  # pragma: no cover
        return "unknown"


def read_sample_profile():
    with rasterio.open(PATHS["sample_submission"]) as s:
        prof = s.profile.copy()
        foot = np.isfinite(s.read(1))
        transform = tuple(s.transform)[:6]
        crs = str(s.crs)
    return prof, foot, transform, crs


def write_pair(mask: np.ndarray, out_dir: Path, stem: str) -> tuple[Path, Path]:
    prof, foot, _, _ = read_sample_profile()
    clean = (np.asarray(mask, bool) & foot).astype(np.float32)
    base = prof.copy()
    base.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        compress="deflate",
        predictor=3,
        zlevel=9,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    nan_path = out_dir / f"{stem}.tif"
    zeros_path = out_dir / f"{stem}-zeros.tif"

    p = base.copy()
    p.update(nodata=np.nan)
    with rasterio.open(nan_path, "w", **p) as dst:
        dst.write(np.where(foot, clean, np.float32(np.nan)).astype(np.float32), 1)

    p = base.copy()
    p.update(nodata=None)
    with rasterio.open(zeros_path, "w", **p) as dst:
        dst.write(np.where(foot, clean, np.float32(0.0)).astype(np.float32), 1)

    return nan_path, zeros_path


def validate_written_raster(path: Path, mode: str, dist_cat: np.ndarray, expected_dots: int) -> dict:
    """Re-read the GeoTIFF from disk and run all format + hard-constraint gates."""
    _, foot, exp_transform, exp_crs = read_sample_profile()
    with rasterio.open(path) as s:
        a = s.read(1)
        count, dtypes = s.count, s.dtypes[0]
        H, W = s.height, s.width
        crs, transform = str(s.crs), tuple(s.transform)[:6]
        nodata = s.nodata

    inside = a[foot]
    outside = a[~foot]
    pos = a > 0.5
    on_cat = int((pos & (dist_cat <= 0.0)).sum())
    within2 = int((pos & (dist_cat <= 2.0)).sum())
    lt3 = int((pos & (dist_cat < 3.0)).sum())
    within3 = int((pos & (dist_cat <= 3.0)).sum())

    checks = {
        "single_band": count == 1,
        "dtype_float32": dtypes == "float32",
        "shape_matches_sample": (H, W) == foot.shape,
        "crs_matches_sample": crs == exp_crs and "32611" in crs,
        "transform_matches_sample": transform == exp_transform,
        "footprint_pixels_match_sample": bool(np.isfinite(inside).all()),
        "no_nan_inside_footprint": bool(np.isfinite(inside).all()),
        "no_inf_anywhere": bool(not np.isinf(a[~np.isnan(a)]).any()),
        "values_in_0_1_inside_footprint": bool(((inside >= 0.0) & (inside <= 1.0)).all()),
        "binary_values_only": bool(set(np.unique(inside).tolist()) <= {0.0, 1.0}),
        "fixed_count_matches_parent": int(pos.sum()) == int(expected_dots),
        "zero_mass_on_catalogue": on_cat == 0,
        "min_distance_to_catalogue_px_ge_3": lt3 == 0,
        "min_distance_to_catalogue_px_gt_3": within3 == 0,
    }
    if mode == "nan":
        checks.update(
            {
                "nodata_is_nan": bool(isinstance(nodata, float) and np.isnan(nodata)),
                "outside_footprint_all_nan": bool(np.isnan(outside).all()),
            }
        )
    else:
        checks.update(
            {
                "nodata_is_none": nodata is None,
                "all_finite_whole_grid": bool(np.isfinite(a).all()),
                "whole_grid_in_0_1": bool(((a >= 0.0) & (a <= 1.0)).all()),
            }
        )

    sha = sha256_file(path)
    return dict(
        mode=mode,
        filename=path.name,
        bytes=path.stat().st_size,
        sha256=sha,
        sha8=sha[:8],
        crs=crs,
        transform=list(transform),
        shape=[H, W],
        dtype=dtypes,
        nodata=(None if nodata is None else str(nodata)),
        positive_pixels=int(pos.sum()),
        emitted_mass=float(np.nansum(a)),
        min=float(np.nanmin(a)),
        max=float(np.nanmax(a)),
        on_catalogue_px=on_cat,
        within_2px_catalogue_px=within2,
        lt_3px_catalogue_px=lt3,
        within_3px_catalogue_px=within3,
        min_distance_to_catalogue_px=(float(dist_cat[pos].min()) if pos.any() else None),
        checks=checks,
        all_checks_passed=bool(all(checks.values())),
    )


def parent_diff_stats(parent: np.ndarray, variant: np.ndarray, shifted_dots: int) -> dict:
    p = int(parent.sum())
    v = int(variant.sum())
    removed = int((parent & ~variant).sum())
    added = int((~parent & variant).sum())
    unchanged = int((parent & variant).sum())
    union = int((parent | variant).sum())
    # `pct_changed` = max(removed, added) / parent_dots * 100: equals removed/p for pure prunes AND
    # equals fraction of R0's dots replaced when count is fixed (never exceeds 100%).
    pct_changed = round(100.0 * max(removed, added) / p, 3)
    pct_symmetric = round(100.0 * (removed + added) / p, 3)
    return dict(
        parent_dots=p,
        variant_dots=v,
        dots_removed=removed,
        dots_added=added,
        unchanged=unchanged,
        commanded_tercile_shift_dots=int(shifted_dots),
        pct_tercile_mass_shifted=round(100.0 * shifted_dots / p, 3),
        pct_changed=pct_changed,
        pct_symmetric_diff=pct_symmetric,
        jaccard=round((unchanged / union) if union else 0.0, 4),
    )


def sgmc_bootstrap_report(masks: dict[str, np.ndarray], dist_cat: np.ndarray, foot: np.ndarray) -> dict:
    """Report-only SGMC control with 20 km spatial-block 95 % bootstrap CIs."""
    with rasterio.open(EXTRA_PATHS["sgmc"]) as ds:
        sgmc = (ds.read(1) > 0) & foot
    sgmc_new = sgmc & (dist_cat > 3.0)
    cat = (dist_cat <= 0.0) & foot

    H, W = foot.shape
    bside = 200  # 20 km blocks
    nr, nc = (H + bside - 1) // bside, (W + bside - 1) // bside
    nb_tot = nr * nc

    q_sgmc_new = kernel_dilate(sgmc_new.astype(np.float64))
    gy_t, gx_t = np.nonzero(sgmc_new)
    t_blk = (gy_t // bside) * nc + (gx_t // bside)

    raw_rows = {}
    terms_by_arm = {}
    for name, m in masks.items():
        mf = m.astype(np.float64)
        r_all = dti(mf, sgmc)
        r_new = dti(mf, sgmc_new)
        r_cat = dti(mf, cat)
        raw_rows[name] = dict(
            sgmc=round(r_all.dti, 5),
            sgmc_n_positives=int(sgmc.sum()),
            sgmc_minus_catalogue_3px=round(r_new.dti, 5),
            sgmc_minus_catalogue_3px_n_positives=int(sgmc_new.sum()),
            static_catalogue_overlap_dti=round(r_cat.dti, 5),
        )
        cov = kernel_dilate(mf)[gy_t, gx_t]
        terms = np.zeros((nb_tot, 4), np.float64)
        terms[:, 0] = np.bincount(t_blk, weights=cov, minlength=nb_tot)
        terms[:, 2] = np.bincount(t_blk, weights=1.0 - cov, minlength=nb_tot)
        terms[:, 3] = np.bincount(t_blk, minlength=nb_tot)
        py, px = np.nonzero(m)
        p_blk = (py // bside) * nc + (px // bside)
        terms[:, 1] = np.bincount(p_blk, weights=1.0 - q_sgmc_new[py, px], minlength=nb_tot)
        terms_by_arm[name] = terms

    active = np.any(np.stack([t.sum(axis=1) > 0 for t in terms_by_arm.values()]), axis=0)
    nb = int(active.sum())
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    picks = rng.integers(0, nb, size=(BOOTSTRAP_DRAWS, nb))
    for name, t in terms_by_arm.items():
        ta = t[active]
        boots = ev57.from_terms(ta[picks].sum(axis=1))
        raw_rows[name]["sgmc_minus_catalogue_3px_ci95"] = [
            round(float(x), 5) for x in np.quantile(boots, [0.025, 0.975])
        ]
    return raw_rows


def hide_and_recover_report(L, rf) -> dict:
    """Report-only spatially-blocked whole-component hide-and-recover PROXY (n withheld, 95 % CI)."""
    cat = load_catalogue() & rf.foot
    grid = Grid(rf.foot, cat, None, TRANSFORM, *rf.foot.shape)
    folds, _ = buffered_component_draw(grid, seed=HOLDOUT_SEED, hide_frac=0.20, buffer_px=3)
    vis = folds[0]["visible"]
    dist_vis = ndimage.distance_transform_edt(~vis)

    r0_fold = L.d28 & (dist_vis > 2.0) & rf.foot
    p3_fold = L.d28 & (dist_vis > 3.0) & rf.foot
    n0f = int(r0_fold.sum())
    f10 = int(round(0.10 * n0f))
    f15 = int(round(0.15 * n0f))
    f15_b = int(round(0.05 * n0f))

    ctrl_fold, _ = shift_relief_terciles(
        r0_fold, dist_vis, rf, {"basin": 0, "piedmont": 0, "range": 0}
    )
    p2r10_fold, _ = shift_relief_terciles(
        r0_fold, dist_vis, rf, {"basin": 0, "piedmont": -f10, "range": +f10}
    )
    bp2r15_fold, _ = shift_relief_terciles(
        r0_fold, dist_vis, rf, {"basin": -f15_b, "piedmont": -(f15 - f15_b), "range": +f15}
    )
    r2bp10_fold, _ = shift_relief_terciles(
        r0_fold, dist_vis, rf, {"basin": +(f10 - f10 // 2), "piedmont": +(f10 // 2), "range": -f10}
    )

    arms = {
        "R0_parent_rule": r0_fold,
        "prune3_rule": p3_fold,
        "ctrl_collar3_0pct": ctrl_fold,
        "reliefp2r10": p2r10_fold,
        "reliefbp2r15": bp2r15_fold,
        "reliefr2bp10": r2bp10_fold,
    }
    terms_by_arm = {}
    for arm_name, pred in arms.items():
        tot = None
        for f in folds:
            _, t = ev57.evaluate(pred.astype(np.float64), f, rf.foot)
            tot = t if tot is None else (tot + t)
        terms_by_arm[arm_name] = tot

    summary = ev57.pooled_summary(
        terms_by_arm, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED, candidate="reliefp2r10"
    )
    compact = {}
    for arm_name, sc in summary["scores"].items():
        compact[arm_name] = dict(
            evidence_label="PROXY (gems57-pooled-hide-v2; never a gate)",
            dti=round(sc["dti"], 5),
            ci95=[round(x, 5) for x in sc["ci95"]],
            withheld_positive_pixels=sc["withheld_positive_pixels"],
        )
    return dict(
        evaluator_version=summary["evaluator_version"],
        withheld_positive_pixels=summary["scores"]["R0_parent_rule"]["withheld_positive_pixels"],
        bootstrap_clusters_20km=summary["bootstrap"]["clusters"],
        bootstrap_draws=BOOTSTRAP_DRAWS,
        arms=compact,
    )


def canary_report(foot: np.ndarray, n_bg: int = 200_000) -> dict:
    """Report-only single-feature leakage canary on all 19 competition bands."""
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    cat = load_catalogue() & foot
    pos = np.flatnonzero(cat.ravel())
    neg_pool = np.flatnonzero((foot & ~cat).ravel())
    neg = rng.choice(neg_pool, size=min(n_bg, neg_pool.size), replace=False)
    idx = np.concatenate([pos, neg])
    y = np.concatenate([np.ones(pos.size), np.zeros(neg.size)])

    per_band = {}
    best = (None, 0.0)
    with rasterio.open(EXTRA_PATHS["training_features"]) as ds:
        names = [desc.split(" - ")[0] for desc in ds.descriptions]
        for b in range(1, ds.count + 1):
            v = ds.read(b).ravel()[idx]
            ok = np.isfinite(v) & (v > -1e30)
            if ok.sum() < 1000 or len(np.unique(v[ok])) < 3:
                continue
            auc = float(roc_auc_score(y[ok], v[ok]))
            auc = max(auc, 1.0 - auc)
            per_band[names[b - 1]] = round(auc, 4)
            if auc > best[1]:
                best = (names[b - 1], auc)

    return dict(
        n_positives=int(pos.size),
        n_background=int(neg.size),
        bands_tested=len(per_band),
        best_single_feature=best[0],
        best_single_feature_auc=round(best[1], 4),
        per_band_auc=per_band,
        threshold=0.90,
        verdict="CLEAN" if best[1] < 0.90 else "STOP_AND_INVESTIGATE",
    )


def known_external_hashes(ledger_rows_prior: list[dict], exclude_stems: set[str]) -> set[str]:
    known: set[str] = set(PINS.values()) | set(EXTRA_PINS.values())
    for r in ledger_rows_prior:
        if r.get("sha256"):
            known.add(r["sha256"])
    for jpath in (ROOT / "registry").glob("*.json"):
        data = json.loads(jpath.read_text())
        if isinstance(data, dict):
            for field in ("files", "artifacts"):
                val = data.get(field, [])
                seq = val.values() if isinstance(val, dict) else (val if isinstance(val, list) else [])
                for item in seq:
                    if isinstance(item, dict) and item.get("sha256"):
                        known.add(item["sha256"])
                    elif isinstance(item, str) and len(item) == 64:
                        known.add(item)
    for folder in (ROOT / "docs" / "downloads", ROOT / "releases"):
        if folder.is_dir():
            for tif in folder.glob("*.tif"):
                if any(tif.name.startswith(st) for st in exclude_stems):
                    continue
                known.add(sha256_file(tif))
    return known


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "releases"))
    args = ap.parse_args()
    out_dir = Path(args.out)

    print("== [1/6] verify manifest & lineage SHA-256 pins ==")
    manifest_report = verify_manifest_hashes()
    print(
        f"  data_manifest: {manifest_report['data_manifest.json']['count']}/23 verified; "
        f"learning_manifest: {manifest_report['learning_manifest.json']['count']}/2 verified; "
        f"lineage+feature pins: {len(manifest_report['lineage_and_feature_pins'])} verified"
    )

    print("== [2/6] rebuild parent R0 & assert byte-identical GeoTIFF SHA-256 ==")
    L, r0_rebuild_report = rebuild_and_verify_r0_bytes()
    print(
        f"  counts={L.counts()} | rebuilt R0 nan={r0_rebuild_report['rebuilt_r0_nan_sha256'][:12]} "
        f"zeros={r0_rebuild_report['rebuilt_r0_zeros_sha256'][:12]} (EXACT BYTE MATCH)"
    )

    r0 = L.r0
    d_cat = L.dist_cat
    n_r0 = int(r0.sum())
    n10 = int(round(0.10 * n_r0))     # 3,765 dots (10.00 %)
    n15 = int(round(0.15 * n_r0))     # 5,648 dots (15.00 %)
    n05 = n15 - n10                   # 1,883 dots (5.00 %)

    print("== [3/6] build Basin / Piedmont / Range-front terciles & 3 RELIEF variants ==")
    rf = build_relief_fields(L.skeleton)
    for tname, tinfo in rf.tercile_summary.items():
        print(f"  tercile {tname:9s}: {tinfo}")

    ctrl_collar, ctrl_detail = shift_relief_terciles(
        r0, d_cat, rf, {"basin": 0, "piedmont": 0, "range": 0}
    )

    variant_specs = [
        (
            "h33-2-b2-reliefp2r10",
            "reliefp2r10",
            "piedmont->range +10% (3765 dots), collar>3px, fixed 37654",
            {"basin": 0, "piedmont": -n10, "range": +n10},
            n10,
        ),
        (
            "h33-2-b2-reliefbp2r15",
            "reliefbp2r15",
            "basin+piedmont->range +15% (5648 dots), collar>3px, fixed 37654",
            {"basin": -n05, "piedmont": -n10, "range": +n15},
            n15,
        ),
        (
            "h33-2-b2-reliefr2bp10",
            "reliefr2bp10",
            "range->basin+piedmont +10% (3765 dots), collar>3px, fixed 37654",
            {"basin": +(n10 - n10 // 2), "piedmont": +(n10 // 2), "range": -n10},
            n10,
        ),
    ]

    ledger_path = ROOT / "ledger" / "submissions.csv"
    prior_rows: list[dict] = []
    if ledger_path.is_file():
        with ledger_path.open(newline="") as fh:
            for row in csv.DictReader(fh):
                if row["axis"] != "RELIEF":
                    prior_rows.append(row)

    prior_pairs = {(r["parent"], r["axis"], r["value"]) for r in prior_rows}
    exclude_stems = {f"{v[0]}-{DATE}-" for v in variant_specs}
    # Clean any stale RELIEF outputs from an earlier run of this same script before re-writing
    if out_dir.is_dir():
        for old_f in out_dir.glob("h33-2-b2-relief*-*.tif"):
            old_f.unlink()
    seen_hashes = known_external_hashes(prior_rows, exclude_stems)

    built_masks = {
        "R0_parent": r0,
        "prune3_ref": r0 & (d_cat > 3.0),
        "ctrl_collar3_0pct": ctrl_collar,
    }
    receipts = {}

    print("== [4/6] write GeoTIFF pairs, re-read from disk & enforce MUST-PASS gates ==")
    for stem_prefix, key, val_desc, delta_map, n_shifted in variant_specs:
        assert ("h33-h33-2-b2", "RELIEF", val_desc) not in prior_pairs, (
            f"Duplicate (parent, axis, value): {val_desc}"
        )
        m, detail = shift_relief_terciles(r0, d_cat, rf, delta_map)
        st = parent_diff_stats(r0, m, n_shifted)
        assert 1.0 <= st["pct_changed"] <= 50.0, f"{stem_prefix}: pct_changed={st['pct_changed']} outside [1,50]"
        assert 1.0 <= st["pct_symmetric_diff"] <= 50.0, (
            f"{stem_prefix}: pct_symmetric_diff={st['pct_symmetric_diff']} outside [1,50]"
        )

        tmp_stem = f"{stem_prefix}-{DATE}-tmp"
        nan_tmp, zeros_tmp = write_pair(m, out_dir, tmp_stem)
        sha8 = sha256_file(nan_tmp)[:8]
        final_stem = f"{stem_prefix}-{DATE}-{sha8}"
        final_nan = out_dir / f"{final_stem}.tif"
        final_zeros = out_dir / f"{final_stem}-zeros.tif"
        nan_tmp.replace(final_nan)
        zeros_tmp.replace(final_zeros)

        r_nan = validate_written_raster(final_nan, "nan", d_cat, n_r0)
        r_zeros = validate_written_raster(final_zeros, "zeros", d_cat, n_r0)
        assert r_nan["sha256"] not in seen_hashes, f"{final_stem}: sha256 already in ledger/registry"
        assert r_zeros["sha256"] not in seen_hashes, f"{final_stem}-zeros: sha256 already in ledger/registry"
        seen_hashes.add(r_nan["sha256"])
        seen_hashes.add(r_zeros["sha256"])

        note = NOTES[key]
        assert len(note) <= 140, f"{key}: form note length {len(note)} > 140"

        built_masks[key] = m
        receipts[stem_prefix] = dict(
            id=final_stem,
            parent="h33-h33-2-b2",
            parent_nan_sha256=PINS["r0_nan"],
            parent_zeros_sha256=PINS["r0_zeros"],
            axis="RELIEF",
            value=val_desc,
            submission_note=note,
            predicted_change=PREDICTIONS[key],
            stats=st,
            tercile_detail=detail,
            nan=r_nan,
            zeros=r_zeros,
            all_gates_passed=bool(r_nan["all_checks_passed"] and r_zeros["all_checks_passed"]),
        )
        print(
            f"  {final_nan.name:44s} dots={st['variant_dots']} "
            f"changed={st['pct_changed']:6.3f}% (sym={st['pct_symmetric_diff']:6.3f}%) "
            f"min_dcat={r_nan['min_distance_to_catalogue_px']:.3f}px "
            f"gates={'PASS' if receipts[stem_prefix]['all_gates_passed'] else 'FAIL'}"
        )

    print("== [5/6] report-only proxies & leakage canary (never gates) ==")
    sgmc_prox = sgmc_bootstrap_report(built_masks, d_cat, rf.foot)
    hide_prox = hide_and_recover_report(L, rf)
    canary = canary_report(rf.foot)
    for k, v in sgmc_prox.items():
        print(f"  SGMC {k:18s}: {v}")
    for k, v in hide_prox["arms"].items():
        print(f"  HIDE {k:18s}: {v}")
    print(
        f"  CANARY: best={canary['best_single_feature']} "
        f"AUC={canary['best_single_feature_auc']} ({canary['verdict']})"
    )
    if canary["verdict"] != "CLEAN":
        raise RuntimeError(f"Leakage canary triggered: {canary}")

    print("== [6/6] write receipt, mirror for check_site.py, and update ledger/submissions.csv ==")
    ctrl_stats = parent_diff_stats(r0, ctrl_collar, 0)
    record = dict(
        schema_version=2,
        session_branch="arena/3dd0b94c-gemsdoe85",
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        git_sha=git_sha(),
        python=platform.python_version(),
        date_tag=DATE,
        axis="RELIEF",
        manifest_verification=dict(
            data_manifest_verified=manifest_report["data_manifest.json"]["count"],
            learning_manifest_verified=manifest_report["learning_manifest.json"]["count"],
            lineage_and_feature_pins=manifest_report["lineage_and_feature_pins"],
        ),
        parent_rebuild=r0_rebuild_report,
        relief_terciles=dict(
            formula="0.70 * pct_rank(det_elev) + 0.30 * pct_rank(det_elev_slope), equal-area footprint terciles",
            summary=rf.tercile_summary,
        ),
        collar_control_unshipped=dict(
            purpose=(
                "Isolates Hard Constraint #4 (d_cat > 3.0 px in-tercile replacement) from "
                "inter-tercile RELIEF shifts at fixed 37,654 dot count."
            ),
            stats=ctrl_stats,
            tercile_detail=ctrl_detail,
        ),
        variants=receipts,
        report_only_proxies=dict(
            sgmc_control=sgmc_prox,
            catalogue_hide_and_recover=hide_prox,
            leakage_canary=canary,
        ),
        note=(
            "All proxies are local holdouts labelled PROXY and never used as promotion gates. "
            "No DrivenData or Dropbox access, no credentials, no submission."
        ),
    )
    ev_path = ROOT / "evidence" / "session_relief_receipt.json"
    ev_path.parent.mkdir(parents=True, exist_ok=True)
    ev_path.write_text(json.dumps(record, indent=2) + "\n")
    docs_ev = ROOT / "docs" / "evidence" / "session_relief_receipt.json"
    docs_ev.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ev_path, docs_ev)

    header = [
        "id",
        "site",
        "name",
        "score",
        "evidence_label",
        "encoding",
        "n_dots",
        "sha8",
        "parent",
        "axis",
        "value",
        "pct_changed",
        "sha256",
        "status",
        "predicted_change",
        "receipt",
        "receipt_score",
        "date",
    ]
    new_rows = []
    for stem_prefix, key, val_desc, _, _ in variant_specs:
        v = receipts[stem_prefix]
        new_rows.append(
            dict(
                id=v["id"],
                site="GEMSDOE85",
                name=v["nan"]["filename"],
                score="",
                evidence_label="MODEL (prediction; no score)",
                encoding="nan-outside primary; zeros twin",
                n_dots=v["stats"]["variant_dots"],
                sha8=v["nan"]["sha8"],
                parent="h33-h33-2-b2",
                axis="RELIEF",
                value=val_desc,
                pct_changed=f"{v['stats']['pct_changed']:.3f}",
                sha256=v["nan"]["sha256"],
                status="BUILT",
                predicted_change=PREDICTIONS[key],
                receipt="N",
                receipt_score="",
                date="",
            )
        )

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(prior_rows + new_rows)

    all_ok = all(v["all_gates_passed"] for v in receipts.values())
    print(f"  receipt -> {ev_path.relative_to(ROOT)} (mirrored to {docs_ev.relative_to(ROOT)})")
    print(f"  ledger  -> {ledger_path.relative_to(ROOT)} ({len(prior_rows) + len(new_rows)} total rows)")
    print(f"\nALL GATES {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
