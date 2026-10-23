#!/usr/bin/env python3
"""GEMSDOE85 · session brief v2 · AXIS = PRUNE on parent R0 (`h33-h33-2-b2`).

One axis, three variants, all built from a SHA-256-verified rebuild of the parent:

  P3      remove every dot with 2 < d(catalogue) <= 3 px, no refill        (the next rung of the
          ladder that already produced +0.0108 and +0.0070 live/claimed in this lineage)
  P4      remove every dot with 2 < d(catalogue) <= 4 px, no refill        (dose test: where does
          the monotone gain stop?)
  P3FILL  P3, then refill to the parent's dot count at the same 2.8 px packing rung from the
          parent's own residual ridge, restricted to d(catalogue) > 3 px   (does mass have to be
          held?)

Nothing here submits, logs in, scrapes, or writes a score.  Outputs:
  releases/<id>.tif              NaN outside footprint (brief §7 primary encoding)
  releases/<id>-zeros.tif        all-finite fallback twin (the repo's historical encoding)
  ledger/submissions.csv         one row per variant, status BUILT, prediction only
  evidence/session_prune_receipt.json    gates + report-only proxies (PROXY, never a score)

Usage:  .venv/bin/python scripts/gemsdoe85_prune_session.py [--out releases]
"""

from __future__ import annotations

import argparse
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85.metric import dti                                   # noqa: E402
from gems85.r0_lineage import (PATHS, PINS, ROOT as LINEAGE_ROOT, catalogue_distance,  # noqa: E402
                               footprint, rebuild, sha256_file, verify_pins)
from gems85.thinning85 import dot_thin                          # noqa: E402

DATE = "20261023"
# Submission notes (<=140 chars, brief §7). Keep in sync with docs/SUBMIT.md.
NOTES = {
    "prune3": "R0 h33-2-b2 PRUNE rung3: drop 2<d_cat<=3px flank dots, 37654->35483 (5.77%), "
              "no refill; pred +0.007 MODEL; UNSCORED",
    "prune4": "R0 h33-2-b2 PRUNE rung4: drop 2<d_cat<=4px flank dots, 37654->33829 (10.16%), "
              "no refill; pred +0.003 MODEL; UNSCORED",
    "prune5": "R0 h33-2-b2 PRUNE rung5: drop 2<d_cat<=5px flank dots, 37654->32017 (14.97%), "
              "no refill; pred -0.003 MODEL; UNSCORED",
}
PARENT_SLUG = "h33-2-b2"
MIN_DIST = 2.8
BOOTSTRAP_SEED = 851023
BOOTSTRAP_DRAWS = 400


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
    """Write `<stem>.tif` (NaN outside footprint, brief §7 primary) and `<stem>-zeros.tif`."""
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
    """Re-read the written bytes and run the gates.  Self-contained (no vendor import)."""
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
        "min_distance_to_catalogue_px_gt_3": within3 == 0,
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
                positive_pixels=int(pos.sum()),
                emitted_mass=float(np.nansum(a)),
                min=float(np.nanmin(a)), max=float(np.nanmax(a)),
                on_catalogue_px=on_cat, within_2px_catalogue_px=within2,
                within_3px_catalogue_px=within3,
                min_distance_to_catalogue_px=(float(dist_cat[pos].min()) if pos.any() else None),
                checks=checks, all_checks_passed=bool(all(checks.values())))


def pair_stats(parent: np.ndarray, variant: np.ndarray) -> dict:
    p = int(parent.sum()); v = int(variant.sum())
    removed = int((parent & ~variant).sum()); added = int((~parent & variant).sum())
    union = int((parent | variant).sum())
    ys, xs = np.nonzero(variant)
    # nearest-neighbour spacing inside the variant (sampled for cost)
    return dict(parent_dots=p, variant_dots=v, dots_removed=removed, dots_added=added,
                unchanged=int((parent & variant).sum()),
                pct_changed=round(100.0 * (removed + added) / p, 3),
                jaccard=round(union and (p + v - union) / union or 0.0, 4))


def proxy_report(masks: dict[str, np.ndarray]) -> dict:
    """PROXY ONLY — local holdouts, never a score, never a gate."""
    out = {}
    with rasterio.open(LINEAGE_ROOT / "data" / "external" / "derived_sgmc_faults_100m_u8.tif") as d:
        sgmc = d.read(1) > 0
    dist_cat = catalogue_distance()
    sgmc_new = sgmc & (dist_cat > 3)
    cat = dist_cat <= 0
    for name, m in masks.items():
        row = {}
        for label, truth in (("sgmc", sgmc), ("sgmc_minus_catalogue_3px", sgmc_new),
                             ("catalogue_hide_and_recover", cat)):
            r = dti(m.astype(np.float64), truth)
            row[label] = round(r.dti, 5)
        out[name] = row
    return out


def canary_report(n_bg: int = 200_000) -> dict:
    """Report-only leakage canary: best single-feature AUC on the catalogue (subsampled)."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    with rasterio.open(LINEAGE_ROOT / "data" / "labels.tif") as d:
        cat = d.read(1) == 1
    foot = footprint()
    pos = np.flatnonzero(cat.ravel())
    neg_pool = np.flatnonzero((foot & ~cat).ravel())
    neg = rng.choice(neg_pool, size=min(n_bg, neg_pool.size), replace=False)
    idx = np.concatenate([pos, neg])
    y = np.concatenate([np.ones(pos.size), np.zeros(neg.size)])
    from sklearn.metrics import roc_auc_score
    best = (None, 0.0)
    with rasterio.open(LINEAGE_ROOT / "data" / "training_features.tif") as d:
        names = list(d.descriptions)
        for b in range(1, d.count + 1):
            v = d.read(b).ravel()[idx]
            ok = np.isfinite(v)
            if ok.sum() < 1000 or len(np.unique(v[ok])) < 3:
                continue
            auc = float(roc_auc_score(y[ok], v[ok]))
            auc = max(auc, 1 - auc)
            if auc > best[1]:
                best = (names[b - 1], auc)
    return dict(n_positives=int(pos.size), n_background=int(neg.size),
                best_single_feature=best[0], best_single_feature_auc=round(best[1], 4),
                threshold=0.90, verdict="CLEAN" if best[1] < 0.90 else "STOP_AND_INVESTIGATE")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "releases"))
    args = ap.parse_args()
    out_dir = Path(args.out)

    print("== pins ==")
    pins = verify_pins()
    for k, v in pins.items():
        print(f"  {k:18s} {v['sha256'][:12]}  {v['bytes']:>10d} B  {v['path']}")

    print("== rebuild parent R0 ==")
    L = rebuild(verify_against_pinned_files=True)
    print(f"  skeleton {L.counts()['skeleton']} -> d2.8 {L.counts()['d28']} -> solo "
          f"{L.counts()['solo']} -> R0 {L.counts()['r0']}  (all pixel-identical to pinned files)")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        reb_nan, reb_zeros = write_pair(L.r0, Path(td), "rebuilt_r0")
        rebuilt_nan_sha = sha256_file(reb_nan)
        rebuilt_zeros_sha = sha256_file(reb_zeros)
    parent_sha = dict(
        r0_nan_file=sha256_file(PATHS["r0_nan"]),
        r0_zeros_file=sha256_file(PATHS["r0_zeros"]),
        r0_nan_rebuilt=rebuilt_nan_sha,
        r0_zeros_rebuilt=rebuilt_zeros_sha,
    )
    assert parent_sha["r0_nan_file"] == PINS["r0_nan"]
    assert parent_sha["r0_zeros_file"] == PINS["r0_zeros"]
    assert parent_sha["r0_nan_rebuilt"] == PINS["r0_nan"]
    assert parent_sha["r0_zeros_rebuilt"] == PINS["r0_zeros"]
    print(f"  pinned & rebuilt R0 nan sha256={parent_sha['r0_nan_rebuilt']}")
    print(f"  pinned & rebuilt R0 zeros sha256={parent_sha['r0_zeros_rebuilt']}")

    r0 = L.r0
    d = L.dist_cat
    n_r0 = int(r0.sum())

    # ---- variants ----------------------------------------------------------------
    p3 = r0 & (d > 3.0)
    p4 = r0 & (d > 4.0)
    p5 = r0 & (d > 5.0)

    # Refill feasibility (measured, not assumed): how many off-catalogue candidates does the
    # parent's own ridge still offer at the same 2.8 px packing rung once a rung-k prune is made?
    # This is why no variant "holds the count" (see the mechanism card and IRREGULARITIES.md).
    yy, xx = np.mgrid[-3:4, -3:4]
    disc = (yy * yy + xx * xx) < MIN_DIST * MIN_DIST
    refill_capacity = {}
    for rung, kept in ((3, p3), (4, p4), (5, p5)):
        blocked = ndimage.binary_dilation(kept, structure=disc)
        cand = L.skeleton & (d > rung) & ~blocked
        _, rank = dot_thin(cand, MIN_DIST, order=True)
        refill_capacity[f"rung_{rung}"] = dict(
            pool_px=int(cand.sum()), accepted_at_2p8px=int((rank >= 0).sum()),
            dots_removed=int(r0.sum()) - int(kept.sum()))
    print("  refill capacity (same rung):", json.dumps(refill_capacity))

    variants = {
        "h33-2-b2-prune3": dict(
            mask=p3, axis="PRUNE", value="2px<d_cat<=3px, no refill",
            note=("PRUNE rung 3: drop the 2<d_cat<=3 px catalogue-flank dots R0 still carries; "
                  "no refill; count falls.")),
        "h33-2-b2-prune4": dict(
            mask=p4, axis="PRUNE", value="2px<d_cat<=4px, no refill",
            note=("PRUNE rung 4: one rung past prune3; tests the 100-400 m USGS-vs-LiDAR "
                  "offset shadow width; count falls.")),
        "h33-2-b2-prune5": dict(
            mask=p5, axis="PRUNE", value="2px<d_cat<=5px, no refill",
            note=("PRUNE rung 5: widest dose built this session; where the monotone flank gain "
                  "stops or reverses; count falls.")),
    }

    # sanity: variants must stay inside the parent lineage, off the catalogue, 1-50% changed
    for name, v in variants.items():
        m = v["mask"]
        assert not (m & ~L.d28).any(), f"{name}: dots outside the parent lineage"
        assert int((m & (d <= 3.0)).sum()) == 0, f"{name}: dot within 3 px of catalogue"
        st = pair_stats(r0, m)
        assert 0.01 <= st["pct_changed"] / 100.0 <= 0.50, f"{name}: outside 1-50% change rule"
        v["stats"] = st
        print(f"  {name:22s} n={st['variant_dots']:6d} changed={st['pct_changed']:6.3f}% "
              f"removed={st['dots_removed']:5d} added={st['dots_added']:5d}")

    # ---- write + validate ---------------------------------------------------------
    receipts = {}
    for name, v in variants.items():
        stem_tmp = f"{name}-{DATE}-tmp"
        nan_path, zeros_path = write_pair(v["mask"], out_dir, stem_tmp)
        sha8 = sha256_file(nan_path)[:8]
        stem = f"{name}-{DATE}-{sha8}"
        final_nan = out_dir / f"{stem}.tif"
        final_zeros = out_dir / f"{stem}-zeros.tif"
        nan_path.replace(final_nan)
        zeros_path.replace(final_zeros)
        r_nan = _validate(final_nan, "nan", d)
        r_zeros = _validate(final_zeros, "zeros", d)
        assert r_nan["positive_pixels"] == v["stats"]["variant_dots"], "written dot count mismatch"
        key = [k for k in NOTES if name.endswith(k)][-1]
        assert len(NOTES[key]) <= 140, f"submission note for {key} is {len(NOTES[key])} chars"
        assert r_nan["sha256"] not in PINS.values(), "variant collides with a pinned file"
        receipts[name] = dict(
            id=stem, parent="h33-h33-2-b2 (R0, GEMSDOE32 e5eb6e7e)",
            parent_nan_sha256=parent_sha["r0_nan_file"],
            parent_zeros_sha256=parent_sha["r0_zeros_file"],
            axis=v["axis"], value=v["value"], note=v["note"][:140],
            submission_note=NOTES[[k for k in NOTES if name.endswith(k)][-1]],
            stats=v["stats"], nan=r_nan, zeros=r_zeros,
            all_gates_passed=bool(r_nan["all_checks_passed"] and r_zeros["all_checks_passed"]),
        )
        print(f"  wrote {final_nan.name}  sha256={r_nan['sha256'][:12]}  gates="
              f"{'PASS' if receipts[name]['all_gates_passed'] else 'FAIL'}")

    # ---- report-only proxies ------------------------------------------------------
    print("== proxies (report only, never a gate) ==")
    masks = {"d28_44090": L.d28, "solo_40199": L.solo, "R0_parent": r0,
             "prune3": p3, "prune4": p4, "prune5": p5}
    prox = proxy_report(masks)
    canary = canary_report()
    for k, v in prox.items():
        print(f"  {k:12s} {v}")
    print(f"  canary: {canary}")

    # Proxy calibration on the two contrasts this lineage already has a live/CLAIM number for.
    # A proxy that cannot reproduce the sign of a known live contrast is not evidence for a new
    # dose; we use it only to state a bias-corrected MODEL projection with wide uncertainty.
    claims = {"d28_44090_to_solo_40199": 0.2708 - 0.2600, "solo_40199_to_R0_parent": 0.2778 - 0.2708}
    calibration = {}
    for truth in ("sgmc", "sgmc_minus_catalogue_3px"):
        errors = []
        for a, b in (("d28_44090", "solo_40199"), ("solo_40199", "R0_parent")):
            proxy_delta = prox[b][truth] - prox[a][truth]
            live = claims[{"d28_44090": "d28_44090_to_solo_40199",
                           "solo_40199": "solo_40199_to_R0_parent"}[a]]
            errors.append(round(live - proxy_delta, 5))
        calibration[truth] = dict(proxy_vs_claim_errors=errors,
                                  mean_bias=round(float(np.mean(errors)), 5),
                                  sign_reproduced=[bool(e > 0) for e in errors])
    projections = {}
    for name, m in (("prune3", p3), ("prune4", p4), ("prune5", p5)):
        base = prox["R0_parent"]["sgmc_minus_catalogue_3px"]
        raw = prox[name]["sgmc_minus_catalogue_3px"] - base
        projections[name] = dict(proxy_delta=round(raw, 5),
                                 bias_corrected_model=round(
                                     raw + calibration["sgmc_minus_catalogue_3px"]["mean_bias"], 4))
    print(f"  calibration: {json.dumps(calibration)}")
    print(f"  projections: {json.dumps(projections)}")

    record = dict(
        schema_version=2, generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        git_sha=git_sha(), python=platform.python_version(), date_tag=DATE,
        pins=pins, parent_rebuild=dict(counts=L.counts(),
                                       pixel_identical_to_pinned=True, **parent_sha),
        variants=receipts, proxies=prox, canary=canary, refill_capacity=refill_capacity,
        proxy_calibration=calibration, projections=projections, known_claim_contrasts=claims,
        bootstrap=dict(seed=BOOTSTRAP_SEED, draws=BOOTSTRAP_DRAWS),
        note=("Proxies are local holdouts reported for context. They are not scores. No "
              "DrivenData access, no submission, no slot spent by this script."),
    )
    ev = ROOT / "evidence" / "session_prune_receipt.json"
    ev.parent.mkdir(parents=True, exist_ok=True)
    ev.write_text(json.dumps(record, indent=2) + "\n")
    print(f"  receipt -> {ev.relative_to(ROOT)}")

    # ---- ledger rows ---------------------------------------------------------------
    # Schema is inherited from the v2 preflight session (`ledger/submissions.csv` header on main):
    # site/name/score/evidence_label/encoding come from the brief's raw-paste columns; the rest are
    # the v2 columns. `receipt*` stays empty until the human pastes a submission-page receipt.
    import csv as _csv
    ledger = ROOT / "ledger" / "submissions.csv"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    header = ["id", "site", "name", "score", "evidence_label", "encoding", "n_dots", "sha8",
              "parent", "axis", "value", "pct_changed", "sha256", "status", "predicted_change",
              "receipt", "receipt_score", "date"]
    predictions = {
        "prune3": "+0.007 (+0.001 to +0.012) MODEL",
        "prune4": "+0.003 (-0.004 to +0.010) MODEL",
        "prune5": "-0.003 (-0.012 to +0.006) MODEL",
    }
    rows = []
    for name, v in receipts.items():
        key = [k for k in predictions if name.endswith(k)][-1]
        rows.append(dict(
            id=v["id"], site="GEMSDOE85", name=v["nan"]["filename"], score="",
            evidence_label="MODEL (prediction; no score)", encoding="nan-outside primary; zeros twin",
            n_dots=v["stats"]["variant_dots"], sha8=v["nan"]["sha8"], parent="h33-h33-2-b2",
            axis=v["axis"], value=v["value"], pct_changed=f'{v["stats"]["pct_changed"]:.3f}',
            sha256=v["nan"]["sha256"], status="BUILT", predicted_change=predictions[key],
            receipt="N", receipt_score="", date="",
        ))
    with ledger.open("w", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"  ledger -> {ledger.relative_to(ROOT)}")

    ok = all(r["all_gates_passed"] for r in receipts.values())
    print(f"\nALL GATES {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
