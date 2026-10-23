#!/usr/bin/env python3
"""GEMSDOE85 · session brief v2 · AXIS = SNAP on parent R0 (`h33-h33-2-b2`).

Three variants, all a controlled edit of the verified parent, all at fixed count and fixed mass:

  S-ON-L   on-ridge (destination must be a parent-skeleton pixel), <= 2 px, lidar scarp response
  S-ON-T   on-ridge, <= 2 px, TMI-upward-continued edge response
  S-OFF-L  free window, <= 2 px, lidar scarp response   (the literal brief definition, as control)

The on-ridge pair tests the *positive* mechanism (the trace is right, but the dots sit at arbitrary
points along it while the 400 m line spacing leaves along-strike position uncertain); the free-window
variant isolates the cost of leaving the ridge, because the same field and the same displacement cap
are used and only the confinement differs.

Nothing here submits, logs in, scrapes or writes a score.  Outputs:
  releases/<id>.tif                    NaN outside footprint (brief §7 primary)
  releases/<id>-zeros.tif              all-finite fallback twin
  evidence/session_snap_receipt.json   gates + report-only proxies
  ledger/submissions.csv               one appended row per variant, status BUILT

Usage:  .venv/bin/python scripts/gemsdoe85_snap_session.py [--out releases]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import holdout                                          # noqa: E402
from gems85.metric import dti                                      # noqa: E402
from gems85.r0_lineage import (PATHS, PINS, catalogue_distance, footprint,  # noqa: E402
                               rebuild, sha256_file, verify_pins)
from gems85.snap85 import (LIDAR_SCARP_BANDS, disc_offsets, lidar_scarp_response,  # noqa: E402
                           snap_dots, support_coverage, tmi_edge_response)

DATE = "20261023"
PARENT_SLUG = "h33-h33-2-b2"
LIDAR = ROOT / "data" / "external" / "lidar_scarp_features_u8.tif"
EXT = ROOT / "data" / "external" / "geodawn_extensions_u8.tif"
SGMC = ROOT / "data" / "external" / "derived_sgmc_faults_100m_u8.tif"
TRAIN = ROOT / "data" / "training_features.tif"
CAP_PX = 2.0
MIN_SEP = 2.0
MIN_CAT = 3.0

# Submission notes (<=140 chars, brief §7). Keep in sync with docs/SUBMIT.md.
NOTES = {
    "snap-ridge-lidar2": "R0 h33-2-b2 SNAP: 22% dots slide <=2px along ridge to peak lidar-scarp "
                         "response; count/mass fixed; pred +0.001 MODEL; UNSCORED",
    "snap-ridge-tmi2": "R0 h33-2-b2 SNAP: 30% dots slide <=2px along ridge to peak TMI-edge "
                       "response; count/mass fixed; pred 0.000 MODEL; UNSCORED",
    "snap-free-lidar2": "R0 h33-2-b2 SNAP control: 57% dots move <=2px to lidar-scarp peak "
                        "anywhere in window; count fixed; pred -0.004 MODEL; UNSCORED",
}


# ----------------------------------------------------------------------------- helpers
def git_sha() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:                                          # pragma: no cover
        return "unknown"


def read_sample_profile():
    with rasterio.open(PATHS["sample_submission"]) as s:
        prof = s.profile.copy()
        foot = np.isfinite(s.read(1))
        transform = tuple(s.transform)[:6]
        crs = str(s.crs)
    return prof, foot, transform, crs


def write_pair(mask: np.ndarray, out_dir: Path, stem: str) -> tuple[Path, Path]:
    """Write `<stem>.tif` (NaN outside footprint) and `<stem>-zeros.tif`."""
    prof, foot, _, _ = read_sample_profile()
    clean = (np.asarray(mask, bool) & foot).astype(np.float32)
    base = prof.copy()
    base.update(driver="GTiff", dtype="float32", count=1, compress="deflate",
                predictor=3, zlevel=9, tiled=True, blockxsize=256, blockysize=256)
    out_dir.mkdir(parents=True, exist_ok=True)
    nan_path = out_dir / f"{stem}.tif"
    zeros_path = out_dir / f"{stem}-zeros.tif"
    p = base.copy(); p.update(nodata=np.nan)
    with rasterio.open(nan_path, "w", **p) as dst:
        dst.write(np.where(foot, clean, np.float32(np.nan)).astype(np.float32), 1)
    p = base.copy(); p.update(nodata=None)
    with rasterio.open(zeros_path, "w", **p) as dst:
        dst.write(np.where(foot, clean, np.float32(0.0)).astype(np.float32), 1)
    return nan_path, zeros_path


def _validate(path: Path, mode: str, dist_cat: np.ndarray) -> dict:
    """Re-read the written bytes and run the brief's MUST gates. Self-contained."""
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
        "values_in_0_1_inside_footprint": bool(((inside >= 0) & (inside <= 1)).all()),
        "binary_values_only": bool(set(np.unique(inside).tolist()) <= {0.0, 1.0}),
        "zero_mass_on_catalogue": on_cat == 0,
    }
    if mode == "nan":
        checks.update({"nodata_is_nan": bool(isinstance(nodata, float) and np.isnan(nodata)),
                       "outside_footprint_all_nan": bool(np.isnan(outside).all())})
    else:
        checks.update({"nodata_is_none": nodata is None,
                       "all_finite_whole_grid": bool(np.isfinite(a).all()),
                       "whole_grid_in_0_1": bool(((a >= 0) & (a <= 1)).all())})
    return dict(mode=mode, filename=path.name, bytes=path.stat().st_size,
                sha256=sha256_file(path), sha8=sha256_file(path)[:8], crs=crs,
                transform=list(transform), shape=[H, W], dtype=dtypes,
                nodata=(None if nodata is None else str(nodata)),
                positive_pixels=int(pos.sum()), emitted_mass=float(np.nansum(a)),
                min=float(np.nanmin(a)), max=float(np.nanmax(a)),
                on_catalogue_px=on_cat, within_2px_catalogue_px=within2,
                within_3px_catalogue_px=within3,
                min_distance_to_catalogue_px=(float(dist_cat[pos].min()) if pos.any() else None),
                checks=checks, all_checks_passed=bool(all(checks.values())))


def pair_stats(parent: np.ndarray, variant: np.ndarray) -> dict:
    p = int(parent.sum()); v = int(variant.sum())
    removed = int((parent & ~variant).sum()); added = int((~parent & variant).sum())
    union = int((parent | variant).sum())
    t = cKDTree(np.argwhere(variant))
    q, _ = t.query(np.argwhere(variant), k=2)
    return dict(parent_dots=p, variant_dots=v, dots_removed=removed, dots_added=added,
                unchanged=int((parent & variant).sum()),
                pct_changed=round(100.0 * (removed + added) / p, 3),
                jaccard=round(union and (p + v - union) / union or 0.0, 4),
                min_inter_dot_px=round(float(q[:, 1].min()), 4),
                mean_nn_px=round(float(q[:, 1].mean()), 4))


def dilate(mask: np.ndarray, radius: float) -> np.ndarray:
    c = int(np.ceil(radius))
    k = np.zeros((2 * c + 1, 2 * c + 1), bool)
    k[c, c] = True
    for dy, dx in disc_offsets(radius, inclusive=True):
        k[c + dy, c + dx] = True
    return ndimage.binary_dilation(mask, k)


def sgmc_report(masks: dict[str, np.ndarray], dist_cat: np.ndarray) -> dict:
    """PROXY ONLY (never a gate): DTI against the SGMC fault map, full and off-catalogue."""
    with rasterio.open(SGMC) as d:
        sgmc = d.read(1) > 0
    sgmc_new = sgmc & (dist_cat > 3)
    out = {}
    for name, m in masks.items():
        r_all = dti(m.astype(np.float64), sgmc)
        r_new = dti(m.astype(np.float64), sgmc_new)
        out[name] = dict(sgmc=round(r_all.dti, 5), sgmc_minus_catalogue_3px=round(r_new.dti, 5))
    return out


def catalogue_proxy(parent: np.ndarray, response: dict[str, np.ndarray], footprint_m: np.ndarray,
                    *, n_folds: int = 4) -> dict:
    """Hide-and-recover PROXY (report only) with the snap rebuilt from `visible` catalogue only.

    For every fold we recompute the catalogue-distance field from that fold's *visible* catalogue and
    re-run the same snap rule, so no withheld catalogue pixel influences the candidate.  The parent
    dot set itself is fixed (it is a given input); only the constraint is fold-specific.
    """
    with rasterio.open(PATHS["labels"]) as d:
        cat = d.read(1) == 1
    folds = holdout.make_folds(cat, n_folds=n_folds)
    results = {}
    for name, spec in response.items():
        tp = fp = fn = 0.0
        per_fold = []
        n_pos = 0
        for fold in folds:
            if spec.get("identity"):
                m = parent
            else:
                dist_vis = ndimage.distance_transform_edt(~fold.visible)
                m, _ = snap_dots(parent, spec["field"], dist_vis, footprint_m, cap_px=spec["cap"],
                                 min_sep=MIN_SEP, min_cat_dist=MIN_CAT, dest_mask=spec["mask"])
            pred = np.where(m, 1.0, 0.0)
            pred[fold.visible] = 0.0
            r = dti(pred, fold.withheld, domain=footprint_m)
            per_fold.append(r.dti)
            tp += r.tp_w; fp += r.fp_w; fn += r.fn_w; n_pos += r.n_truth
        pooled = tp / (tp + 0.2 * fp + 0.8 * fn) if (tp + 0.2 * fp + 0.8 * fn) > 0 else 0.0
        arr = np.array(per_fold)
        se = arr.std(ddof=1) / np.sqrt(arr.size) if arr.size > 1 else float("nan")
        results[name] = dict(pooled=round(float(pooled), 5), n_withheld_positives=int(n_pos),
                             per_fold=[round(float(v), 5) for v in per_fold],
                             ci95=[round(float(pooled - 1.96 * se), 5),
                                   round(float(pooled + 1.96 * se), 5)])
    return results


def canary(n_bg: int = 200_000, extra: dict[str, np.ndarray] | None = None) -> dict:
    """Report-only leakage canary: best single-feature AUC against the catalogue."""
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(20261023)
    with rasterio.open(PATHS["labels"]) as d:
        cat = d.read(1) == 1
    foot = footprint()
    pos = np.flatnonzero(cat.ravel())
    neg_pool = np.flatnonzero((foot & ~cat).ravel())
    neg = rng.choice(neg_pool, size=min(n_bg, neg_pool.size), replace=False)
    idx = np.concatenate([pos, neg])
    y = np.concatenate([np.ones(pos.size), np.zeros(neg.size)])
    best = (None, 0.0)
    rows = {}
    if TRAIN.is_file():
        with rasterio.open(TRAIN) as d:
            names = list(d.descriptions)
            for b in range(1, d.count + 1):
                v = d.read(b).ravel()[idx]
                ok = np.isfinite(v)
                if ok.sum() < 1000 or len(np.unique(v[ok])) < 3:
                    continue
                auc = float(roc_auc_score(y[ok], v[ok]))
                auc = max(auc, 1 - auc)
                rows[f"train:{names[b - 1]}"] = round(auc, 4)
                if auc > best[1]:
                    best = (f"train:{names[b - 1]}", auc)
    for name, field in (extra or {}).items():
        v = field.ravel()[idx]
        ok = np.isfinite(v)
        auc = float(roc_auc_score(y[ok], v[ok]))
        auc = max(auc, 1 - auc)
        rows[f"response:{name}"] = round(auc, 4)
        if auc > best[1]:
            best = (f"response:{name}", auc)
    return dict(n_positives=int(pos.size), n_background=int(neg.size),
                best_single_feature=best[0], best_single_feature_auc=round(best[1], 4),
                threshold=0.90, verdict="CLEAN" if best[1] < 0.90 else "STOP_AND_INVESTIGATE",
                features_scored=rows,
                note=("Report only. A feature derived from the full catalogue would score ~1.0; "
                      "0.90 is the stop threshold."))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "releases"))
    args = ap.parse_args()
    out_dir = Path(args.out)

    print("== pins ==")
    pins = verify_pins()
    for k, v in pins.items():
        print(f"  {k:18s} {v['sha256'][:12]}  {v['bytes']:>10d} B  {v['path']}")
    manifest = {f["id"]: f for f in json.loads((ROOT / "registry" / "data_manifest.json").read_text())["files"]}
    ext_pins = {}
    for eid, path in (("ext_lidar_scarp_features_u8", LIDAR), ("ext_geodawn_extensions_u8", EXT),
                      ("ext_derived_sgmc_faults_100m_u8", SGMC), ("training_features", TRAIN)):
        got = sha256_file(path)
        assert got == manifest[eid]["sha256"], f"{eid}: sha256 {got} != pinned"
        ext_pins[eid] = dict(path=str(path.relative_to(ROOT)), sha256=got,
                             bytes=path.stat().st_size)
        print(f"  {eid:32s} {got[:12]}  {path.stat().st_size:>10d} B")

    print("== rebuild parent R0 ==")
    L = rebuild(verify_against_pinned_files=True)
    foot = footprint()
    r0, d, skel = L.r0, L.dist_cat, L.skeleton
    print(f"  skeleton {L.counts()['skeleton']} -> d2.8 {L.counts()['d28']} -> solo "
          f"{L.counts()['solo']} -> R0 {L.counts()['r0']}  (pixel-identical to pinned files)")
    print(f"  pinned R0 nan sha256={sha256_file(PATHS['r0_nan'])}")
    print(f"  pinned R0 zeros sha256={sha256_file(PATHS['r0_zeros'])}")

    print("== response fields ==")
    r_lidar, lidar_valid, lidar_info = lidar_scarp_response(LIDAR)
    r_tmi, tmi_valid, tmi_info = tmi_edge_response(EXT)
    for info in (lidar_info, tmi_info):
        inside = float((info["field"] == "lidar_scarp" and lidar_valid[foot].mean())
                       or (tmi_valid[foot].mean()))
        info["coverage_fraction_of_footprint"] = round(inside, 4)
        print(f"  {info['field']:11s} grid coverage {info['coverage_fraction']:.3f}  "
              f"footprint coverage {inside:.3f}")
    base_cov = support_coverage(r0, skel)
    print(f"  parent support coverage C(skeleton) = {base_cov:.5f}")

    # ---- variants ----------------------------------------------------------------
    specs = {
        "snap-ridge-lidar2": dict(field=r_lidar, cap=CAP_PX, mask=skel, axis="SNAP",
                                  value="on-ridge (dest subset of parent skeleton), cap 2 px, lidar scarp",
                                  field_name="lidar_scarp"),
        "snap-ridge-tmi2": dict(field=r_tmi, cap=CAP_PX, mask=skel, axis="SNAP",
                                value="on-ridge (dest subset of parent skeleton), cap 2 px, TMI edge",
                                field_name="tmi_edge"),
        "snap-free-lidar2": dict(field=r_lidar, cap=CAP_PX, mask=None, axis="SNAP",
                                 value="free window (brief-literal), cap 2 px, lidar scarp",
                                 field_name="lidar_scarp"),
    }
    masks, infos = {}, {}
    for name, s in specs.items():
        m, info = snap_dots(r0, s["field"], d, foot, cap_px=s["cap"], min_sep=MIN_SEP,
                            min_cat_dist=MIN_CAT, dest_mask=s["mask"])
        masks[name] = m
        infos[name] = info
        info["support_coverage_parent"] = round(base_cov, 5)
        info["support_coverage_variant"] = round(support_coverage(m, skel), 5)
        info["support_coverage_delta_pct"] = round(
            100.0 * (info["support_coverage_variant"] / base_cov - 1.0), 3)
        st = pair_stats(r0, m)
        info["pair"] = st
        print(f"  {name:18s} n={st['variant_dots']:6d} moved={info['pct_moved']:6.2f}% "
              f"mean_disp={info['mean_displacement_moved_px']:.3f} px "
              f"cov={info['support_coverage_variant']:.4f} ({info['support_coverage_delta_pct']:+.1f}%) "
              f"minsep={st['min_inter_dot_px']:.2f}")
        assert st["variant_dots"] == int(r0.sum()), f"{name}: dot count changed"
        assert not (m & ~foot).any(), f"{name}: dot outside footprint"
        assert int((m & (d <= 2.0)).sum()) == 0, f"{name}: dot within 2 px of catalogue"
        assert st["min_inter_dot_px"] >= MIN_SEP - 1e-9, f"{name}: separation rule violated"
        assert 0.01 <= info["pct_moved"] / 100.0 <= 0.90, f"{name}: moved fraction out of range"

    # ---- write + validate ---------------------------------------------------------
    print("== write + gates ==")
    receipts = {}
    for name, s in specs.items():
        tmp = f"{name}-{DATE}-tmp"
        nan_path, zeros_path = write_pair(masks[name], out_dir, tmp)
        sha8 = sha256_file(nan_path)[:8]
        stem = f"{name}-{DATE}-{sha8}"
        final_nan = out_dir / f"{stem}.tif"
        final_zeros = out_dir / f"{stem}-zeros.tif"
        nan_path.replace(final_nan); zeros_path.replace(final_zeros)
        r_nan = _validate(final_nan, "nan", d)
        r_zeros = _validate(final_zeros, "zeros", d)
        assert r_nan["positive_pixels"] == int(r0.sum()), "written dot count mismatch"
        assert r_nan["sha256"] not in PINS.values(), "variant collides with a pinned file"
        assert len(NOTES[name]) <= 140, f"note for {name} is {len(NOTES[name])} chars"
        receipts[name] = dict(
            id=stem, parent="h33-h33-2-b2 (R0, GEMSDOE32 e5eb6e7e)",
            parent_nan_sha256=sha256_file(PATHS["r0_nan"]),
            parent_zeros_sha256=sha256_file(PATHS["r0_zeros"]),
            axis=s["axis"], value=s["value"], field=s["field_name"],
            snap=infos[name], nan=r_nan, zeros=r_zeros,
            submission_note=NOTES[name],
            all_gates_passed=bool(r_nan["all_checks_passed"] and r_zeros["all_checks_passed"]))
        print(f"  {final_nan.name}  sha256={r_nan['sha256'][:12]}  "
              f"gates={'PASS' if receipts[name]['all_gates_passed'] else 'FAIL'}")
        for k, v in r_nan["checks"].items():
            if not v:
                print(f"    FAILED CHECK: {k}")

    # ---- report-only proxies ------------------------------------------------------
    print("== proxies (report only, never a gate) ==")
    prox_masks = {"R0_parent": r0, **masks}
    sg = sgmc_report(prox_masks, d)
    for k, v in sg.items():
        print(f"  SGMC {k:18s} {v}")
    cat_proxy = catalogue_proxy(r0, {"R0_parent": dict(identity=True),
                                     **{k: dict(field=specs[k]["field"], cap=specs[k]["cap"],
                                                mask=specs[k]["mask"]) for k in specs}}, foot)
    for k, v in cat_proxy.items():
        print(f"  catalogue-proxy {k:18s} pooled={v['pooled']:.5f} "
              f"CI={v['ci95']} n_pos={v['n_withheld_positives']}")
    can = canary(extra={"lidar_scarp": r_lidar, "tmi_edge": r_tmi})
    print(f"  canary: best={can['best_single_feature']} AUC={can['best_single_feature_auc']} "
          f"-> {can['verdict']}")

    # ---- ledger rows ---------------------------------------------------------------
    predictions = {
        "snap-ridge-lidar2": "+0.001 (-0.006 to +0.008) MODEL",
        "snap-ridge-tmi2": "0.000 (-0.008 to +0.008) MODEL",
        "snap-free-lidar2": "-0.004 (-0.012 to +0.004) MODEL",
    }
    record = dict(
        schema_version=2, generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        git_sha=git_sha(), python=platform.python_version(), date_tag=DATE,
        pins=pins, external_pins=ext_pins,
        parent_rebuild=dict(counts=L.counts(), pixel_identical_to_pinned=True,
                            r0_nan_sha256=sha256_file(PATHS["r0_nan"]),
                            r0_zeros_sha256=sha256_file(PATHS["r0_zeros"])),
        response_fields=dict(lidar=lidar_info, tmi=tmi_info, lidar_bands=list(LIDAR_SCARP_BANDS)),
        variants=receipts, sgmc_proxy=sg, catalogue_hide_and_recover_proxy=cat_proxy,
        canary=can, predictions=predictions,
        note=("Proxies are local holdouts reported for context; they are not scores. No DrivenData "
              "access, no submission, no slot spent by this script."))
    ev = ROOT / "evidence" / "session_snap_receipt.json"
    ev.write_text(json.dumps(record, indent=2, default=float) + "\n")
    print(f"  receipt -> {ev.relative_to(ROOT)}")

    ledger = ROOT / "ledger" / "submissions.csv"
    header = ["id", "site", "name", "score", "evidence_label", "encoding", "n_dots", "sha8",
              "parent", "axis", "value", "pct_changed", "sha256", "status", "predicted_change",
              "receipt", "receipt_score", "date"]
    existing = []
    if ledger.is_file():
        with ledger.open(newline="") as fh:
            existing = list(csv.DictReader(fh))
    existing_by_sha = {row["sha256"]: row for row in existing}
    rows = []
    for name, v in receipts.items():
        prev = existing_by_sha.get(v["nan"]["sha256"])
        if prev is not None:
            # idempotent rerun: the same bytes must map to the same ledger id, never a second row.
            # Prediction/value text is refreshed from this script so the ledger cannot go stale.
            assert prev["id"] == v["id"], f"{name}: sha256 in ledger under a different id"
            prev["predicted_change"] = predictions[name]
            prev["parent"] = PARENT_SLUG
            prev["value"] = v["value"]
            prev["pct_changed"] = f'{v["snap"]["pct_moved"]:.3f}'
            print(f"  ledger: {v['id']} already recorded, refreshed in place")
            continue
        rows.append(dict(
            id=v["id"], site="GEMSDOE85", name=v["nan"]["filename"], score="",
            evidence_label="MODEL (prediction; no score)",
            encoding="nan-outside primary; zeros twin",
            n_dots=v["snap"]["pair"]["variant_dots"], sha8=v["nan"]["sha8"],
            parent=PARENT_SLUG, axis=v["axis"], value=v["value"],
            pct_changed=f'{v["snap"]["pct_moved"]:.3f}', sha256=v["nan"]["sha256"],
            status="BUILT", predicted_change=predictions[name], receipt="N",
            receipt_score="", date=""))
    with ledger.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
        w.writeheader()
        w.writerows(existing + rows)
    print(f"  ledger -> {ledger.relative_to(ROOT)} (+{len(rows)} rows, {len(existing)} kept)")

    ok = all(r["all_gates_passed"] for r in receipts.values())
    print(f"\nALL GATES {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
