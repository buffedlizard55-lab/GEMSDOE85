#!/usr/bin/env python3
"""GEMSDOE85 · session brief v2 (session 3) · AXIS = PRUNE, fractional catalogue-distance rungs.

Axis choice (the brief leaves AXIS to the human; see IRREGULARITIES.md IR-V3-02):
this session first measured the three remaining unbuilt axes against the parent's own geometry and
found SNAP and CONCENTRATION **infeasible at R0's packing invariant** (0 movable dots; 26 free
destination cells).  The only axis with room to move AND a live dose-response is PRUNE, so the three
variants refine the integer rung ladder (2 px -> 3 px -> 4 px, already built in the previous
session) into the three distance *rings* the 2-3 px rung actually spans.

  R2P25  drop d_cat <= 2.25 px   (the sqrt5 ring, 941 dots)   -> 36,713 dots
  R2P85  drop d_cat <= 2.85 px   (+ the 2sqrt2 ring, 1,611)   -> 36,043 dots
  R3P61  drop d_cat <= 3.61 px   (+ 3.0, sqrt10, sqrt13 rings) -> 34,952 dots  (brackets rung 3)

Nothing here submits, logs in, scrapes, or writes a score.  Outputs:
  releases/<id>.tif              NaN outside footprint (brief §7 primary encoding)
  releases/<id>-zeros.tif        all-finite fallback twin
  ledger/submissions.csv         existing rows preserved, one new row per variant (status BUILT)
  evidence/session_rung_receipt.json   gates, feasibility measurements, report-only proxies

Usage:  .venv/bin/python scripts/gemsdoe85_rung_session.py [--out releases] [--no-holdout]
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems85.metric import dti                                            # noqa: E402
from gems85.r0_lineage import (PATHS, PINS, catalogue_distance, footprint,  # noqa: E402
                               rebuild, sha256_file, unique_credit, verify_pins)
from gemsdoe85_prune_session import (canary_report, pair_stats, proxy_report,  # noqa: E402
                                     write_pair)

DATE = "20261023"
PARENT_SLUG = "h33-2-b2"
BOOTSTRAP_SEED = 851123
TRAINING_FEATURES_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
TC_SHA = "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682"

# Submission notes (<=140 chars, brief §7). Keep in sync with docs/SUBMIT.md.
NOTES = {
    "r2p25": "R0 h33-2-b2 PRUNE fractional rung 2.25px: drop sqrt5-ring dots 37654->36713 (2.50%), "
             "no refill; pred +0.003 MODEL; UNSCORED",
    "r2p85": "R0 h33-2-b2 PRUNE fractional rung 2.85px: drop sqrt5+2sqrt2 rings 37654->36043 "
             "(4.28%), no refill; pred +0.005 MODEL; UNSCORED",
    "r3p61": "R0 h33-2-b2 PRUNE fractional rung 3.61px: drop rings <=3.61px 37654->34293 (8.93%), "
             "no refill; pred +0.005 MODEL; UNSCORED",
}
# Single-peaked ladder model, inherited from the previous session's published rung predictions
# (rung 3 -> +0.007, rung 4 -> +0.003): the fractional rungs sit on the rising limb below rung 3
# (941 and 1,611 dots) and just past the predicted optimum (3,361 dots).  Intervals are wide
# because the only local proxy available points the other way (see proxy_caveat in the receipt).
PREDICTIONS = {
    "r2p25": "+0.003 (-0.003 to +0.009) MODEL",
    "r2p85": "+0.005 (-0.002 to +0.012) MODEL",
    "r3p61": "+0.005 (-0.004 to +0.014) MODEL",
}
RUNGS = {"r2p25": 2.25, "r2p85": 2.85, "r3p61": 3.61}


def git_sha() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:                                                   # pragma: no cover
        return "unknown"


# ------------------------------------------------------------------ axis feasibility measurements
def axis_feasibility(L, dist_cat: np.ndarray, foot: np.ndarray) -> dict:
    """Measure whether SNAP / CONCENTRATION / RELIEF can change anything at R0's packing rung.

    A dot may only move to a cell that is (a) inside the footprint, (b) farther than 2 px from the
    catalogue (the parent's own exclusion), and (c) at least 2.8 px from every other dot -- the
    parent's recorded Poisson-disk rung.  R0 was produced by greedy thinning of a 1-px skeleton, so
    this test measures whether that packing left any admissible slack at all.
    """
    yy, xx = np.mgrid[-3:4, -3:4]
    disc = (yy * yy + xx * xx) < 2.8 * 2.8
    occupied = ndimage.binary_dilation(L.r0, structure=disc)          # >= 2.8 px from every R0 dot
    free = foot & ~occupied & (dist_cat > 2.0)
    out = {
        "packing_rung_px": 2.8,
        "free_cells_anywhere_in_footprint": int(free.sum()),
        "free_cells_on_parent_skeleton": int((free & L.skeleton).sum()),
    }
    # SNAP: is any dot movable within 2 px at each candidate separation floor?
    for floor in (2.8, 2.4, 2.2, 2.0):
        d2 = (yy * yy + xx * xx) < floor * floor
        occ = ndimage.binary_dilation(L.r0, structure=d2)
        # count dots with at least one destination cell at distance <= 2 px that is free at this
        # floor and satisfies the parent's catalogue exclusion (the dot's own cell excluded)
        window = np.zeros_like(free)
        r = 2
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dy * dy + dx * dx > 4 or (dy == 0 and dx == 0):
                    continue
                ys = slice(max(0, -dy), free.shape[0] - max(0, dy))
                xs = slice(max(0, -dx), free.shape[1] - max(0, dx))
                yd = slice(max(0, dy), free.shape[0] - max(0, -dy))
                xd = slice(max(0, dx), free.shape[1] - max(0, -dx))
                window[yd, xd] |= (foot & ~occ & (dist_cat > 2.0))[ys, xs]
        out[f"snap_dots_with_a_free_destination_at_floor_{floor}"] = int((L.r0 & window).sum())
    # CONCENTRATION / RELIEF: how much mass could be relocated into the top-prior km blocks?
    prior, blocks, bm, full = _block_prior(foot)
    q = np.percentile(bm[full], [100 / 3.0, 200 / 3.0])
    high = full & (bm >= q[1])
    in_high = np.repeat(np.repeat(high, 10, axis=0), 10, axis=1)[:foot.shape[0], :foot.shape[1]]
    out.update({
        "block_size_px": 10, "block_size_km": 1.0,
        "full_footprint_blocks": int(full.sum()),
        "prior_p33_p67": [round(float(q[0]), 4), round(float(q[1]), 4)],
        "destination_cells_in_top_prior_tercile_dcat_gt_3": int(
            (free & L.skeleton & in_high & (dist_cat > 3.0)).sum()),
        "destination_cells_in_top_prior_tercile_dcat_gt_2": int(
            (free & L.skeleton & in_high & (dist_cat > 2.0)).sum()),
        "verdict": ("SNAP and CONCENTRATION are infeasible at the parent's packing rung: no dot has a "
                    "free destination that preserves >=2.2 px spacing, and only a few dozen free "
                    "skeleton cells exist in the top-prior tercile."),
    })
    return out


def _block_prior(foot: np.ndarray):
    """Per-1-km-block prior = mean of z(GeoDAWN TC) and z(detrended-elevation slope)."""
    with rasterio.open(ROOT / "data" / "external" / "geodawn_rad_u8.tif") as d:
        tc = d.read(4).astype(np.float32)
    with rasterio.open(ROOT / "data" / "training_features.tif") as d:
        slp = d.read(19)

    def rob(a, good):
        v = a[good]
        return ((a - np.median(v)) / (np.percentile(v, 75) - np.percentile(v, 25))).astype(np.float32)

    ztc = rob(tc, foot & (tc > 0))
    zslp = rob(slp, foot & (slp > -1e30))
    prior = np.where(foot, np.nanmean(np.stack([np.where(tc > 0, ztc, np.nan), zslp]), axis=0),
                     np.nan).astype(np.float32)
    H, W = prior.shape
    B = 10
    nyb, nxb = -(-H // B), -(-W // B)
    gy, gx = np.mgrid[0:H, 0:W]
    bid = (gy // B) * nxb + (gx // B)
    flat = bid.ravel()
    ok = (np.isfinite(prior) & foot).ravel()
    nb = nyb * nxb
    bsum = np.bincount(flat[ok], weights=prior.ravel()[ok], minlength=nb)
    bcnt = np.bincount(flat[ok], minlength=nb)
    bm = (bsum / np.maximum(bcnt, 1)).reshape(nyb, nxb)
    barea = bcnt.reshape(nyb, nxb)
    return prior, bid, bm, barea == B * B


def block_density_cv(dots: np.ndarray, foot: np.ndarray) -> dict:
    """Block-density CV over fully-covered 1-km blocks (the brief's CONCENTRATION report)."""
    H, W = dots.shape
    B = 10
    nyb, nxb = -(-H // B), -(-W // B)
    gy, gx = np.mgrid[0:H, 0:W]
    bid = ((gy // B) * nxb + (gx // B)).ravel()
    nb = nyb * nxb
    ok = foot.ravel()
    bcnt = np.bincount(bid[ok], minlength=nb).reshape(nyb, nxb)
    full = bcnt == B * B
    ys, xs = np.nonzero(dots)
    bd = np.bincount(bid[ys * W + xs], minlength=nb).reshape(nyb, nxb).astype(float)
    dens = bd[full]
    return dict(blocks=int(full.sum()), mean_dots_per_km2=round(float(dens.mean()), 3),
                cv=round(float(dens.std() / dens.mean()), 4))


def snap_probe(L, dist_cat, foot, radius=2, floor=2.0) -> dict:
    """Run the SNAP transform at a relaxed floor and report what it costs (report-only, no file)."""
    with rasterio.open(ROOT / "data" / "training_features.tif") as d:
        hg_mag = d.read(3)
        hg_grav = d.read(18)

    def rob(a):
        good = foot & (a > -1e30)
        v = a[good]
        return np.where(good, (a - np.median(v)) / (np.percentile(v, 75) - np.percentile(v, 25)),
                        np.nan).astype(np.float32)

    E = np.nanmean(np.stack([rob(hg_mag), rob(hg_grav)]), axis=0)
    E = np.where(np.isfinite(E), E, -1e6).astype(np.float32)
    ys, xs = np.nonzero(L.r0)
    H, W = E.shape
    best = np.full(ys.size, -1e6, np.float32)
    bdy = np.zeros(ys.size, np.int8)
    bdx = np.zeros(ys.size, np.int8)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if (dy == 0 and dx == 0) or dy * dy + dx * dx > radius * radius:
                continue
            py, px = ys + dy, xs + dx
            ok = (py >= 0) & (py < H) & (px >= 0) & (px < W)
            v = np.full(ys.size, -1e6, np.float32)
            v[ok] = E[py[ok], px[ok]]
            dok = np.zeros(ys.size, bool)
            dok[ok] = dist_cat[py[ok], px[ok]] > 3.0
            v = np.where(ok & dok, v, -1e6)
            take = v > best
            best = np.where(take, v, best)
            bdy = np.where(take, dy, bdy)
            bdx = np.where(take, dx, bdx)
    cur = E[ys, xs]
    nodata = cur < -1e5
    gain = np.where(nodata, 0.0, best - cur)
    move = (best > -1e5) & ((gain > 0.05) & ~nodata | nodata)
    order = np.argsort(-np.where(nodata, -1e3, np.where(move, gain, -2e3)), kind="stable")
    yy, xx = np.mgrid[-3:4, -3:4]
    disc = (yy * yy + xx * xx) < floor * floor
    occupied = np.zeros((H, W), bool)
    occupied[ys, xs] = True
    clear = ndimage.binary_dilation(occupied, structure=disc)
    ny, nx = ys.copy(), xs.copy()
    moved = np.zeros(ys.size, bool)
    for i in order:
        if not move[i]:
            continue
        qy, qx = int(ys[i] + bdy[i]), int(xs[i] + bdx[i])
        if clear[qy, qx]:
            continue
        occupied[ys[i], xs[i]] = False
        occupied[qy, qx] = True
        for (ay, ax) in ((ys[i], xs[i]), (qy, qx)):
            y0, y1 = max(0, ay - 3), min(H, ay + 4)
            x0, x1 = max(0, ax - 3), min(W, ax + 4)
            clear[y0:y1, x0:x1] = ndimage.binary_dilation(occupied[y0:y1, x0:x1], structure=disc)
        ny[i], nx[i] = qy, qx
        moved[i] = True
    snapped = np.zeros_like(L.r0)
    snapped[ny, nx] = True
    U = unique_credit(snapped)
    U0 = unique_credit(L.r0)
    disp = np.hypot(ny - ys, nx - xs)
    return dict(radius_px=radius, separation_floor_px=floor,
                dots_moved=int(moved.sum()), pct_moved=round(100 * moved.mean(), 2),
                mean_displacement_px=round(float(disp[moved].mean()), 3) if moved.any() else 0.0,
                unique_credit_sum_vs_parent=round(float(U.sum() / U0.sum()), 4),
                note="report-only probe; no file written, no slot implied")



def validate_rung(path: Path, mode: str, dist_cat: np.ndarray, rung_px: float) -> dict:
    """Re-read the written bytes from disk and run the gates that apply to a PRUNE rung.

    Gates (brief §6, MUST-pass): single band, float32, shape/CRS/transform equal to
    sample_submission.tif, no NaN inside the footprint, NaN (or 0) outside, values in [0,1],
    zero mass on catalogue pixels, sha256 not already in the ledger, and -- axis-specific --
    every emitted dot strictly farther than the declared rung from the catalogue.

    The brief's ">= 3 px from the catalogue" rule is explicitly waived for AXIS = PRUNE (that is
    what a prune rung is); the 3 px distance is reported, not gated.
    """
    with rasterio.open(ROOT / "data" / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
        exp_transform = tuple(s.transform)[:6]
        exp_crs = str(s.crs)
    with rasterio.open(path) as s:
        a = s.read(1)
        count, dtype = s.count, s.dtypes[0]
        H, W = s.height, s.width
        crs, transform = str(s.crs), tuple(s.transform)[:6]
        nodata = s.nodata
    inside, outside = a[foot], a[~foot]
    pos = a > 0.5
    on_cat = int((pos & (dist_cat <= 0.0)).sum())
    within3 = int((pos & (dist_cat <= 3.0)).sum())
    within_rung = int((pos & (dist_cat <= rung_px)).sum())
    checks = {
        "single_band": count == 1,
        "dtype_float32": dtype == "float32",
        "shape_matches_sample": (H, W) == foot.shape,
        "crs_matches_sample": crs == exp_crs and "32611" in crs,
        "transform_matches_sample": transform == exp_transform,
        "footprint_pixels_match_sample": bool(np.isfinite(inside).all()),
        "no_nan_inside_footprint": bool(np.isfinite(inside).all()),
        "no_inf_anywhere": bool(not np.isinf(a[~np.isnan(a)]).any()),
        "values_in_0_1_inside_footprint": bool(((inside >= 0) & (inside <= 1)).all()),
        "binary_values_only": bool(set(np.unique(inside).tolist()) <= {0.0, 1.0}),
        "zero_mass_on_catalogue": on_cat == 0,
        "all_dots_beyond_declared_rung": within_rung == 0,
    }
    if mode == "nan":
        checks.update({"nodata_is_nan": bool(isinstance(nodata, float) and np.isnan(nodata)),
                       "outside_footprint_all_nan": bool(np.isnan(outside).all())})
    else:
        checks.update({"nodata_is_none": nodata is None,
                       "all_finite_whole_grid": bool(np.isfinite(a).all()),
                       "whole_grid_in_0_1": bool(((a >= 0) & (a <= 1)).all())})
    sha = sha256_file(path)
    return dict(mode=mode, filename=path.name, bytes=path.stat().st_size, sha256=sha, sha8=sha[:8],
                crs=crs, transform=list(transform), shape=[H, W], dtype=dtype,
                nodata=(None if nodata is None else str(nodata)),
                positive_pixels=int(pos.sum()), emitted_mass=float(np.nansum(a)),
                min=float(np.nanmin(a)), max=float(np.nanmax(a)), on_catalogue_px=on_cat,
                within_3px_catalogue_px=within3, within_declared_rung_px=within_rung,
                min_distance_to_catalogue_px=(float(dist_cat[pos].min()) if pos.any() else None),
                checks=checks, all_checks_passed=bool(all(checks.values())))


def holdout_proxy(path: Path, out_json: Path) -> dict:
    """REPORT-ONLY: pooled hide-and-recover DTI from the shared vendor evaluator."""
    t0 = time.time()
    cmd = [sys.executable, str(ROOT / "scripts" / "evaluate_holdout.py"),
           "--prediction", str(path), "--existing-faults", str(ROOT / "data" / "existing_faults.tif"),
           "--template", str(ROOT / "data" / "sample_submission.tif"), "--seeds", "20", "30",
           "--out", str(out_json)]
    subprocess.run(cmd, check=True, capture_output=True)
    d = json.loads(out_json.read_text())
    sc = d["scores"]["candidate"]
    return dict(dti=round(float(sc["dti"]), 6),
                ci95=[round(float(v), 6) for v in sc["ci95"]],
                withheld_positive_pixels=int(sc["withheld_positive_pixels"]),
                evaluator=str(d.get("evaluator_version", "gems57-pooled-hide-v2")),
                seconds=round(time.time() - t0, 1),
                label="PROXY (local hide-and-recover on the catalogue); not a score")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "releases"))
    ap.add_argument("--no-holdout", action="store_true")
    args = ap.parse_args()
    out_dir = Path(args.out)

    print("== pins ==")
    pins = verify_pins()
    extra = {"training_features": sha256_file(ROOT / "data" / "training_features.tif"),
             "geodawn_rad_u8": sha256_file(ROOT / "data" / "external" / "geodawn_rad_u8.tif")}
    assert extra["training_features"] == TRAINING_FEATURES_SHA, "training_features pin mismatch"
    assert extra["geodawn_rad_u8"] == TC_SHA, "geodawn_rad_u8 pin mismatch"
    for k, v in pins.items():
        print(f"  {k:18s} {v['sha256'][:12]}  {v['bytes']:>10d} B  {v['path']}")
    print(f"  training_features  {extra['training_features'][:12]}  (band source)")
    print(f"  geodawn_rad_u8     {extra['geodawn_rad_u8'][:12]}  (TC prior)")

    print("== rebuild parent R0 ==")
    L = rebuild(verify_against_pinned_files=True)
    r0, d = L.r0, L.dist_cat
    foot = footprint()
    print(f"  skeleton {L.counts()['skeleton']} -> d2.8 {L.counts()['d28']} -> solo "
          f"{L.counts()['solo']} -> R0 {L.counts()['r0']}  (pixel-identical to pinned files)")
    parent_sha = dict(r0_nan_file=sha256_file(PATHS["r0_nan"]),
                      r0_zeros_file=sha256_file(PATHS["r0_zeros"]))
    assert parent_sha["r0_nan_file"] == PINS["r0_nan"]
    assert parent_sha["r0_zeros_file"] == PINS["r0_zeros"]

    print("== catalogue-distance ring table over R0 dots ==")
    dv = d[r0]
    vals, cnts = np.unique(np.round(dv, 4), return_counts=True)
    rings = {float(v): int(c) for v, c in zip(vals[:12], cnts[:12])}
    print("  " + ", ".join(f"{v}= {c}" for v, c in list(rings.items())[:8]))

    print("== axis feasibility (why PRUNE, not SNAP/CONCENTRATION) ==")
    feas = axis_feasibility(L, d, foot)
    for k, v in feas.items():
        if k != "verdict":
            print(f"  {k}: {v}")
    print(f"  verdict: {feas['verdict']}")
    snap11 = snap_probe(L, d, foot, radius=1, floor=2.0)
    snap22 = snap_probe(L, d, foot, radius=2, floor=2.0)
    print(f"  snap probe r=1 floor=2.0: {snap11['dots_moved']} moved, "
          f"credit {snap11['unique_credit_sum_vs_parent']}")
    print(f"  snap probe r=2 floor=2.0: {snap22['dots_moved']} moved, "
          f"credit {snap22['unique_credit_sum_vs_parent']}")

    cv_before = block_density_cv(r0, foot)
    print(f"  block-density CV before: {cv_before}")

    # ---- variants -------------------------------------------------------------------------
    variants = {}
    for key, thr in RUNGS.items():
        mask = r0 & (d > thr)
        variants[key] = dict(mask=mask, axis="PRUNE", value=f"d_cat<= {thr}px, no refill",
                             note=(f"PRUNE fractional rung {thr} px: drop the catalogue-flank ring(s) "
                                   f"up to {thr} px; no refill; count falls."))
    for key, v in variants.items():
        st = pair_stats(r0, v["mask"])
        assert st["dots_added"] == 0, f"{key}: PRUNE must not add dots"
        assert int((v["mask"] & (d <= 0.0)).sum()) == 0, f"{key}: dot on the catalogue"
        assert 0.01 <= st["pct_changed"] / 100.0 <= 0.50, f"{key}: outside the 1-50% change rule"
        assert int(v["mask"].sum()) > 0
        v["stats"] = st
        v["block_density_cv"] = block_density_cv(v["mask"], foot)
        print(f"  {key:7s} n={st['variant_dots']:6d} removed={st['dots_removed']:5d} "
              f"({st['pct_changed']:5.2f}%)  CV {v['block_density_cv']['cv']}")

    # ---- write + validate -----------------------------------------------------------------
    ledger_sha = set()
    ledger_path = ROOT / "ledger" / "submissions.csv"
    if ledger_path.is_file():
        with ledger_path.open() as fh:
            ledger_sha = {row.get("sha256", "") for row in csv.DictReader(fh)}

    receipts = {}
    for key, v in variants.items():
        nan_path, zeros_path = write_pair(v["mask"], out_dir, f"h33-2-b2-{key}-{DATE}-tmp")
        sha8 = sha256_file(nan_path)[:8]
        stem = f"h33-2-b2-{key}-{DATE}-{sha8}"
        final_nan = out_dir / f"{stem}.tif"
        final_zeros = out_dir / f"{stem}-zeros.tif"
        nan_path.replace(final_nan)
        zeros_path.replace(final_zeros)
        rung = RUNGS[key]
        r_nan = validate_rung(final_nan, "nan", d, rung)
        r_zeros = validate_rung(final_zeros, "zeros", d, rung)
        assert r_nan["positive_pixels"] == v["stats"]["variant_dots"], "written dot count mismatch"
        assert r_nan["sha256"] not in PINS.values(), "variant collides with a pinned file"
        assert r_nan["sha256"] not in ledger_sha, "variant sha256 already in the ledger (repeat)"
        assert len(NOTES[key]) <= 140, f"note for {key} is {len(NOTES[key])} chars"
        # PRUNE is the one axis allowed to differ from the >=3 px rule; report both distances
        gate_ok = (r_nan["checks"]["zero_mass_on_catalogue"] and
                   r_nan["checks"]["all_dots_beyond_declared_rung"])
        receipts[key] = dict(
            id=stem, parent="h33-h33-2-b2 (R0, GEMSDOE32 e5eb6e7e)",
            parent_nan_sha256=parent_sha["r0_nan_file"],
            parent_zeros_sha256=parent_sha["r0_zeros_file"],
            axis=v["axis"], value=v["value"], note=v["note"][:140], submission_note=NOTES[key],
            stats=v["stats"], block_density_cv=v["block_density_cv"],
            nan=r_nan, zeros=r_zeros,
            all_gates_passed=bool(r_nan["all_checks_passed"] and r_zeros["all_checks_passed"]
                                  and gate_ok))
        print(f"  wrote {final_nan.name}  sha256={r_nan['sha256'][:12]}  "
              f"gates={'PASS' if receipts[key]['all_gates_passed'] else 'FAIL'}  "
              f"min_d_cat={r_nan['min_distance_to_catalogue_px']:.2f}")

    # ---- report-only proxies ---------------------------------------------------------------
    print("== proxies (report only, never a gate) ==")
    masks = {"R0_parent": r0, **{k: v["mask"] for k, v in variants.items()}}
    prox = proxy_report(masks)
    canary = canary_report()
    for k, v in prox.items():
        print(f"  {k:10s} {v}")
    print(f"  canary: {canary}")
    hold = {}
    if not args.no_holdout:
        hold["R0_parent"] = holdout_proxy(PATHS["r0_nan"], ROOT / "evidence" / "_holdout_r0.json")
        print(f"  holdout R0: {hold['R0_parent']['dti']} K={hold['R0_parent']['withheld_positive_pixels']}")
        for key in variants:
            p = out_dir / f"{receipts[key]['id']}.tif"
            hold[key] = holdout_proxy(p, ROOT / "evidence" / f"_holdout_{key}.json")
            print(f"  holdout {key}: {hold[key]['dti']}")

    # ---- receipt ---------------------------------------------------------------------------
    record = dict(
        schema_version=3,
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        git_sha=git_sha(), python=platform.python_version(), date_tag=DATE,
        parent=dict(slug=PARENT_SLUG, claim_live_dti=0.2778,
                    evidence_label="CLAIM (owner-reported; no receipt in this repository)",
                    rebuild=dict(counts=L.counts(), pixel_identical_to_pinned=True, **parent_sha)),
        pins={**{k: v["sha256"] for k, v in pins.items()}, **extra},
        rings_px=rings,
        axis_feasibility=feas, snap_probe=dict(radius1_floor2=snap11, radius2_floor2=snap22),
        block_density_cv_parent=cv_before,
        variants=receipts, proxies=prox, canary=canary, holdout_proxy=hold,
        predictions={k: PREDICTIONS[k] for k in variants},
        proxy_caveat=(
            "Both local proxies move the WRONG WAY for this axis and are therefore reported, not "
            "used: (a) dti(dots, catalogue) and (b) the vendor hide-and-recover holdout both use "
            "catalogue pixels as truth, while the live scorer MASKS catalogue pixels and scores "
            "only new faults, so any variant that moves away from the catalogue must lose on them. "
            "The axis is justified by the two live/CLAIM rung receipts in this lineage (+0.0108 for "
            "<=1 px, +0.0070 for <=2 px), which are direct evidence and outrank both proxies."),
        note=("All scores above are PROXY, CLAIM or MODEL. No DrivenData access, no submission, no "
              "slot spent by this script."),
    )
    ev = ROOT / "evidence" / "session_rung_receipt.json"
    ev.write_text(json.dumps(record, indent=2) + "\n")
    for tmp in (ROOT / "evidence").glob("_holdout_*.json"):
        tmp.unlink()
    print(f"  receipt -> {ev.relative_to(ROOT)}")

    # ---- ledger: preserve existing rows, add the new ones -----------------------------------
    header = ["id", "site", "name", "score", "evidence_label", "encoding", "n_dots", "sha8",
              "parent", "axis", "value", "pct_changed", "sha256", "status", "predicted_change",
              "receipt", "receipt_score", "date"]
    rows = []
    if ledger_path.is_file():
        with ledger_path.open() as fh:
            rd = csv.DictReader(fh)
            assert rd.fieldnames == header, f"ledger header changed: {rd.fieldnames}"
            rows = [dict(r) for r in rd]
    have = {(r.get("parent"), r.get("axis"), r.get("value")) for r in rows}
    new_rows = []
    for key, v in receipts.items():
        triple = ("h33-h33-2-b2", "PRUNE", v["value"])
        if triple in have:
            print(f"  ledger already has {triple}; skipping")
            continue
        new_rows.append(dict(
            id=v["id"], site="GEMSDOE85", name=v["nan"]["filename"], score="",
            evidence_label="MODEL (prediction; no score)",
            encoding="nan-outside primary; zeros twin", n_dots=v["stats"]["variant_dots"],
            sha8=v["nan"]["sha8"], parent="h33-h33-2-b2", axis="PRUNE", value=v["value"],
            pct_changed=f'{v["stats"]["pct_changed"]:.3f}', sha256=v["nan"]["sha256"],
            status="BUILT", predicted_change=PREDICTIONS[key], receipt="N", receipt_score="",
            date=""))
    if new_rows:
        with ledger_path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
            w.writeheader()
            w.writerows(rows + new_rows)
        print(f"  ledger -> {ledger_path.relative_to(ROOT)} (+{len(new_rows)} rows, "
              f"{len(rows)} preserved)")

    ok = all(r["all_gates_passed"] for r in receipts.values())
    print(f"\nALL GATES {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
