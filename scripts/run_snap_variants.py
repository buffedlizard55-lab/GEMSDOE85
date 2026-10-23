#!/usr/bin/env python3
"""AXIS=SNAP session: rebuild R0 from its recipe, then build 3 snap variants + 1 control.

Pre-registration (written before any variant existed, and before any score, local or live,
was computed for them; see AI_USE.md for the one design change and why).

Parent R0 = ``h33-h33-2-b2`` (GEMSDOE32): 37,654 unit dots, claimed live 0.2778 = **CLAIM**
(no submission-page receipt exists anywhere in this repository).

Recipe verified here pixel-exactly: ``H27-4-solo-d28`` support (40,199 dots, pinned sha
07b6db44...) minus every dot with Euclidean distance <= 2.0 px to the mapped catalogue
= exactly the parent's 37,654 pixels.

Axis: SNAP, d = 2 px (the brief's cap), edge field
    E = mean(rank(band03 tmi_hg), rank(band18 iso_grav_anom_hg))
measured as a footprint percentile rank in [0,1] so the two systems are scale-free and
comparable.  A dot moves to the strongest eligible pixel in its <=2 px window only when the
edge gain ``E(best) - E(here)`` clears a threshold tau.  tau is the one knob:

    snapd2t20   tau = 0.20   only where the two systems strongly disagree with the parent
    snapd2t10   tau = 0.10   moderate
    snapd2t00   tau = 0.00   the brief's literal definition: every dot to the local argmax
    prune3      CONTROL, tau = inf: no snapping at all, only the >=3 px catalogue exclusion
                             (needed to attribute any live change to SNAP rather than to the
                             exclusion; PRUNE is NOT this session's assigned axis)

Every dot whose parent position lies within 3.0 px of the catalogue (1,611 dots, 4.28 %) is
ineligible and must move in all four files, so the control isolates exactly that.

Pre-registered predictions (live DTI), stated before the run:

    snapd2t20   +0.000 .. +0.008   few dots move, only where evidence is strong
    snapd2t10   +0.000 .. +0.012
    snapd2t00   -0.015 .. +0.015   replaces the parent's own localisation with a field whose
                                   best single-band AUC is ~0.57 (PROXY, measured elsewhere in
                                   this repo); sign genuinely unknown
    prune3      +0.000 .. +0.005   the parent already showed 2 px -> 3 px was worth ~0.007
                                   between 0.2708 and 0.2778; the remaining ring is thinner

Falsifier: a live change under 0.01 is no evidence (public chunks only; the private score
may differ).

Hard constraints enforced in code: zero mass on catalogue pixels and >= 3.0 px Euclidean from
every catalogue pixel (stricter than the parent, which keeps 941 dots at 2.236 px -- see
IRREGULARITIES.md IR-86-002); footprint = finite cells of sample_submission.tif; unit dots
only (binary is optimal: the metric is linear in p at fixed support); every raster re-read
from disk and re-validated after writing.
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
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
for _sub in (ROOT / "vendor", ROOT / "src"):
    if str(_sub) not in sys.path:
        sys.path.insert(0, str(_sub))

from gems57 import gates, grid as g57  # noqa: E402
from gems57.validate import validate  # noqa: E402
from gems85 import holdout as hold  # noqa: E402

TODAY = "20261023"
PARENT_ID = "h33-h33-2-b2"
PARENT_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
D28_SHA = "07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40"
CATALOGUE_CLEAR_PX = 3.0
SNAP_D_PX = 2.0

EDGE_BANDS = {"tmi_hg": 3, "iso_grav_anom_hg": 18, "det_elev_slope": 19}
PRIMARY_CHANNELS = ("tmi_hg", "iso_grav_anom_hg")

# variant -> gain threshold in footprint-rank units (None = control, move only if forced)
VARIANTS = {
    "snapd2t20": 0.20,
    "snapd2t10": 0.10,
    "snapd2t00": 0.00,
    "prune3": None,
}
PREDICTED = {
    "snapd2t20": dict(low=0.000, high=0.008,
                      text="few dots move (only where TMI-HG and gravity-HG both say the "
                           "parent dot is badly placed)"),
    "snapd2t10": dict(low=0.000, high=0.012, text="moderate number of dots move"),
    "snapd2t00": dict(low=-0.015, high=0.015,
                      text="every dot moves to the local argmax: replaces the parent's own "
                           "localisation with a ~0.57-AUC field, sign unknown"),
    "prune3": dict(low=0.000, high=0.005,
                   text="control: 3 px exclusion only, no snapping"),
}
NODATA_F32 = np.float32(-3.4028234663852886e38)


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def rank01(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Footprint percentile rank in [0, 1]. Scale-free, robust to the two bands' units."""
    order = np.sort(values[valid])
    r = np.searchsorted(order, values, side="left").astype(np.float32)
    return r / max(1, order.size)


def read_band_cached(path: Path, band: int) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(band).astype(np.float32)
    return np.where(a < NODATA_F32 * np.float32(0.5), np.float32(0.0), a)


def offsets_within(d: float) -> list[tuple[int, int, float]]:
    """Integer offsets with Euclidean distance <= d, nearest first; includes stay (0,0)."""
    offs = []
    r = int(np.floor(d))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            dist = float(np.hypot(dy, dx))
            if dist <= d + 1e-9:
                offs.append((dy, dx, dist))
    offs.sort(key=lambda t: (t[2], t[1], t[0]))
    return offs


def snap(dots_yx: np.ndarray, edge: np.ndarray, eligible: np.ndarray, d: float,
         tau: float | None, shape: tuple[int, int]) -> tuple[np.ndarray, dict]:
    """Greedy, injective snap of every dot to the strongest eligible edge within ``d`` px.

    A dot moves only if its own pixel is ineligible (forced by the >=3 px rule) or if the
    edge gain at its best eligible neighbour is at least ``tau``.  ``tau=None`` is the
    control: forbidden to move except when forced.  Dots are processed forced-first, then by
    descending gain, so a dot never takes a pixel another dot already owns.  The seek radius
    widens (2 -> 4 -> 6 px) only for dots that cannot be placed otherwise; that count is
    reported, never silently absorbed.
    """
    h, w = shape
    y, x = dots_yx[:, 0].astype(np.int64), dots_yx[:, 1].astype(np.int64)

    def gather(offs):
        vals = np.full((y.size, len(offs)), -1.0)
        ok = np.zeros((y.size, len(offs)), dtype=bool)
        for j, (dy, dx, _dist) in enumerate(offs):
            ny, nx = y + dy, x + dx
            inb = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
            yy, xx = np.where(inb, ny, 0), np.where(inb, nx, 0)
            vals[:, j] = np.where(inb, edge[yy, xx], -1.0)
            ok[:, j] = inb & eligible[yy, xx]
        return vals, ok

    offs = offsets_within(d)
    vals, ok = gather(offs)
    stay_col = next(j for j, o in enumerate(offs) if o[0] == 0 and o[1] == 0)
    vals[:, stay_col], ok[:, stay_col] = edge[y, x], eligible[y, x]
    best_val = np.where(ok, vals, -1.0).max(axis=1)
    gain = best_val - edge[y, x]
    forced = ~eligible[y, x]
    if tau is None:
        want_move = forced.copy()
    else:
        want_move = forced | (ok.any(axis=1) & (gain >= tau) & ~forced)
        want_move = forced | (ok.any(axis=1) & (gain >= tau))
    order = np.lexsort((x, y, ~forced, -gain))     # forced first, then biggest gain

    wide = {}                                       # lazy wider rings for the few stragglers
    taken = np.zeros(h * w, dtype=bool)
    out = np.empty_like(dots_yx)
    disp = np.zeros(y.size)
    n_moved = n_forced_moved = n_widened = n_dup = 0
    refill_px: list[float] = []
    for i in order:
        cols = np.where(ok[i] & ~taken[(y[i] + np.array([o[0] for o in offs])) * w
                                       + (x[i] + np.array([o[1] for o in offs]))])[0]
        move = want_move[i] or cols.size == 0
        if move and cols.size:
            j = cols[np.argmax(vals[i, cols])]
            dy, dx, _ = offs[j]
        elif cols.size and stay_col in cols and not want_move[i]:
            j = stay_col
            dy = dx = 0
        elif cols.size:
            j = cols[np.argmax(vals[i, cols])]
            dy, dx, _ = offs[j]
        else:                                        # no free cell in the 13-window
            placed = False
            for wd in (4.0, 6.0, 10.0):
                if wd not in wide:
                    wide[wd] = gather(offsets_within(wd))
                wv, wo = wide[wd]
                cand = np.where(wo[i] & ~taken[(y[i] + np.array(
                    [o[0] for o in offsets_within(wd)])) * w
                    + (x[i] + np.array([o[1] for o in offsets_within(wd)]))])[0]
                if cand.size:
                    jj = cand[np.argmax(wv[i, cand])]
                    dy, dx, _ = offsets_within(wd)[jj]
                    placed = True
                    n_widened += 1
                    refill_px.append(float(np.hypot(dy, dx)))
                    break
            if not placed:
                dy = dx = 0
                n_dup += 1
        out[i] = (y[i] + dy, x[i] + dx)
        taken[out[i, 0] * w + out[i, 1]] = True
        disp[i] = float(np.hypot(dy, dx))
        if disp[i] > 0:
            n_moved += 1
            if forced[i]:
                n_forced_moved += 1
    stats = dict(n_dots=int(y.size), n_moved=int(n_moved),
                 pct_moved=round(100.0 * n_moved / y.size, 3),
                 pct_dots_moved_incl_forced=round(100.0 * n_moved / y.size, 3),
                 n_dots_changed_vs_parent=int((out != dots_yx).any(axis=1).sum()),
                 n_moved_because_forced=int(n_forced_moved),
                 n_needed_wider_seek=int(n_widened), n_duplicate_placement=int(n_dup),
                 n_refilled_beyond_d=int(n_widened),
                 max_refill_px=round(float(max(refill_px)), 4) if refill_px else 0.0,
                 snap_cap_applies_to_pct=round(100.0 * (y.size - n_widened) / y.size, 3),
                 mean_displacement_px=round(float(disp.mean()), 4),
                 median_displacement_px=round(float(np.median(disp)), 4),
                 max_displacement_px=round(float(disp.max()), 4),
                 n_unique_targets=int(np.unique(out[:, 0] * w + out[:, 1]).size))
    return out, stats


def support_of(dots: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    m = np.zeros(shape, dtype=bool)
    m[dots[:, 0], dots[:, 1]] = True
    return m


def block_cv(support: np.ndarray, footprint: np.ndarray, block: int = 100) -> float:
    """Dot-density CV over 10 km blocks with >= 50 % footprint coverage."""
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


def write_twin(path: Path, arr: np.ndarray, outside: str) -> dict:
    """Write one submission twin on the pinned grid, then re-read it from disk."""
    prof = dict(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                dtype="float32", crs="EPSG:32611", transform=g57.TRANSFORM, tiled=True,
                blockxsize=256, blockysize=256, compress="deflate", predictor=2)
    if outside == "nan":
        prof["nodata"] = float("nan")
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(arr.astype(np.float32), 1)
        dst.set_band_description(1, "predicted_new_fault_probability")
    with rasterio.open(path) as src:                     # the re-read is the contract
        back = src.read(1)
        meta = dict(bands=src.count, dtype=src.dtypes[0], crs=str(src.crs),
                    shape=[src.height, src.width], transform=list(src.transform)[:6])
    inside = np.isfinite(back) if outside == "nan" else np.ones(back.shape, bool)
    return dict(path=str(path.relative_to(ROOT)), sha256=sha256(path), bytes=path.stat().st_size,
                meta=meta, n_positive=int((back > 0).sum()),
                min_inside=float(np.min(back[inside])) if inside.any() else None,
                max_inside=float(np.max(back[inside])) if inside.any() else None,
                reread_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", type=Path, default=ROOT / "work/h33-b2.tif")
    ap.add_argument("--d28", type=Path, default=ROOT / "work/d28.tif")
    ap.add_argument("--features", type=Path, default=ROOT / "data/training_features.tif")
    ap.add_argument("--out", type=Path, default=ROOT / "releases")
    ap.add_argument("--evidence", type=Path, default=ROOT / "evidence/session_snap.json")
    ap.add_argument("--skip-holdout", action="store_true")
    args = ap.parse_args()

    g = g57.load_grid()
    footprint, catalogue = g.footprint, g.catalogue
    shape = footprint.shape
    record: dict = dict(schema_version=1, session="arena/59608071-gemsdoe85", axis="SNAP",
                        built_utc=TODAY, git_sha=git_sha(), alpha=0.2, beta=0.8, kernel_px=3.0,
                        evaluator="gems85-holdout-v1.0.0", catalogue_clear_px=CATALOGUE_CLEAR_PX,
                        snap_max_px=SNAP_D_PX)

    # ---- 1. rebuild R0 from its recipe, never approximating it -----------------
    assert sha256(args.d28) == D28_SHA, "H27-4-solo-d28 is not the pinned file"
    assert sha256(args.parent) == PARENT_SHA, "parent raster is not the pinned h33-h33-2-b2"
    dcat = distance_transform_edt(~catalogue)
    with rasterio.open(args.d28) as src:
        d28 = np.nan_to_num(src.read(1), nan=0.0) > 0
    with rasterio.open(args.parent) as src:
        parent = src.read(1) > 0
    rebuilt = d28 & (dcat > 2.0)
    assert rebuilt.sum() == parent.sum() == 37654, (rebuilt.sum(), parent.sum())
    assert np.array_equal(rebuilt, parent), "recipe rebuild differs from the pinned parent"
    record["parent_rebuild"] = dict(
        recipe="H27-4-solo-d28 support minus dots with d(catalogue) <= 2.0 px",
        d28_sha256=D28_SHA, parent_sha256=PARENT_SHA, n_dots=37654, pixel_identical=True,
        container_sha256_identical=False,
        note="decoded pixels are identical cell-for-cell and the count matches; the container "
             "sha256 differs because the pinned file was encoded by another GDAL/zlib build "
             "(re-encoding the identical pixels here yields a different byte stream). "
             "IR-86-001.")
    parent_dots = np.argwhere(parent)

    # ---- 2. eligibility and the edge-response field ---------------------------
    eligible = footprint & (dcat >= CATALOGUE_CLEAR_PX)
    record["eligibility"] = dict(n_footprint=int(footprint.sum()), n_eligible=int(eligible.sum()),
                                 parent_dots_eligible=int(eligible[parent].sum()),
                                 parent_dots_ineligible=int((parent & ~eligible).sum()),
                                 pct_parent_dots_ineligible=round(
                                     100.0 * float((parent & ~eligible).sum()) / 37654, 3),
                                 parent_min_dist_catalogue_px=round(float(dcat[parent].min()), 4))
    ranks = {}
    for name, band in EDGE_BANDS.items():
        a = read_band_cached(args.features, band)
        ranks[name] = rank01(a, footprint & np.isfinite(a))
        del a
    edge = np.mean([ranks[c] for c in PRIMARY_CHANNELS], axis=0).astype(np.float32)
    edge[~footprint] = 0.0
    edge_scarp = np.mean([ranks[c] for c in (*PRIMARY_CHANNELS, "det_elev_slope")],
                         axis=0).astype(np.float32)
    edge_scarp[~footprint] = 0.0

    # how much new information would a DEM-scarp channel carry? (SLOT_PLAN input)
    offs = offsets_within(SNAP_D_PX)
    yy, xx = parent_dots[:, 0], parent_dots[:, 1]

    def argmax_target(e):
        v = np.stack([np.where(((yy + dy) >= 0) & ((yy + dy) < shape[0]) & ((xx + dx) >= 0)
                               & ((xx + dx) < shape[1]),
                               e[np.clip(yy + dy, 0, shape[0] - 1),
                                 np.clip(xx + dx, 0, shape[1] - 1)], -1.0) for dy, dx, _ in offs], 1)
        return v.argmax(1)

    ta, tb = argmax_target(edge), argmax_target(edge_scarp)
    record["scarp_channel_diagnostic"] = dict(
        note="report only; not used to build any variant",
        frac_parent_dots_whose_argmax_changes_if_scarp_added=round(float((ta != tb).mean()), 4))

    # ---- 3. build, write, gate ------------------------------------------------
    args.out.mkdir(parents=True, exist_ok=True)
    variants = []
    for vid, tau in VARIANTS.items():
        dots, st = snap(parent_dots, edge, eligible, SNAP_D_PX, tau, shape)
        sup = support_of(dots, shape)
        assert int(sup.sum()) == 37654, f"dot count drifted: {int(sup.sum())}"
        assert not (sup & catalogue).any(), "mass on the catalogue"
        assert float(dcat[sup].min()) >= CATALOGUE_CLEAR_PX - 1e-9, "broke the 3 px rule"
        assert not (sup & ~footprint).any(), "mass outside the footprint"
        vals = np.where(sup, np.float32(1.0), np.float32(0.0))
        nan_arr = np.where(footprint, vals, np.float32("nan"))

        slug = f"{PARENT_ID}-{vid}-{TODAY}"
        tmp0 = args.out / f".tmp-{vid}-zeros.tif"
        z = write_twin(tmp0, vals, "zeros")
        final0 = args.out / f"{slug}-{z['sha256'][:8]}-zeros.tif"
        tmp0.replace(final0)
        z = write_twin(final0, vals, "zeros")
        tmpn = args.out / f".tmp-{vid}-nan.tif"
        n = write_twin(tmpn, nan_arr, "nan")
        finaln = args.out / f"{slug}-{n['sha256'][:8]}-nan.tif"
        tmpn.replace(finaln)
        n = write_twin(finaln, nan_arr, "nan")

        fr = gates.format_report(final0, ROOT / "data/bridge/sample_submission.tif", footprint=footprint)
        lv = validate(final0, footprint, catalogue)
        frn = gates.format_report(finaln, ROOT / "data/bridge/sample_submission.tif", footprint=footprint)
        lvn = validate(finaln, footprint, catalogue) if frn["ok"] else dict(all_checks_passed=False)
        moves = dots.astype(np.int64) - parent_dots.astype(np.int64)
        stats = dict(
            **st,
            jaccard_vs_parent=round(float((sup & parent).sum() / (sup | parent).sum()), 6),
            n_voxels_changed=int((sup ^ parent).sum()),
            mean_edge_rank_before=round(float(edge[parent_dots[:, 0], parent_dots[:, 1]].mean()), 5),
            mean_edge_rank_after=round(float(edge[dots[:, 0], dots[:, 1]].mean()), 5),
            block_cv_10km_parent=round(block_cv(parent, footprint), 5),
            block_cv_10km_variant=round(block_cv(sup, footprint), 5),
            mean_dy_dx=[round(float(moves[:, 0].mean()), 4), round(float(moves[:, 1].mean()), 4)],
        )
        variants.append(dict(id=f"{slug}-{z['sha256'][:8]}", slug=slug, value=vid, tau=tau,
                             zeros=z, nan=n,
                             format_report=dict(ok=bool(fr["ok"]),
                                                problems=fr.get("problems", [])),
                             local_validate=dict(all_checks_passed=bool(lv["all_checks_passed"]),
                                                 problems=lv.get("problems", [])),
                             nan_format_ok=bool(frn["ok"]),
                             nan_local_ok=bool(lvn.get("all_checks_passed")),
                             stats=stats, predicted=PREDICTED[vid], support=sup))
        print(f"[built] {vid:10s} dots={stats['n_dots']} changed={stats['pct_moved']:6.2f}% "
              f"mean_disp={stats['mean_displacement_px']:.3f}px forced={stats['n_moved_because_forced']} "
              f"wide={stats['n_needed_wider_seek']} dup={stats['n_duplicate_placement']} "
              f"edge {stats['mean_edge_rank_before']:.3f}->{stats['mean_edge_rank_after']:.3f} "
              f"gates={fr['ok'] and lv['all_checks_passed']}", flush=True)

    # ---- 4. report-only instruments -------------------------------------------
    folds = hold.make_folds(catalogue)
    n_withheld = int(sum(f.n_withheld for f in folds))
    proxy = {}
    if not args.skip_holdout:
        for name, sup in [("parent_h33-2-b2", parent)] + [(v["value"], v["support"]) for v in variants]:
            r = hold.score_static(sup, folds, domain=footprint)
            proxy[name] = dict(pooled_holdout_dti=round(r.pooled_dti, 6),
                               ci95=[round(float(c), 6) for c in r.ci95],
                               n_withheld_positives=r.n_withheld_positives,
                               tp_w=round(r.tp_w, 3), fp_w=round(r.fp_w, 3), fn_w=round(r.fn_w, 3))
    canary = {name: round(float(hold.feature_auc(r, folds, footprint)), 5) for name, r in ranks.items()}
    sgmc_path = ROOT / "data/external/derived_sgmc_faults_100m_u8.tif"
    sgmc: dict = {}
    if sgmc_path.is_file():
        with rasterio.open(sgmc_path) as src:
            sm = src.read(1) > 0
        if sm.shape == shape and sm.any():
            dsg = distance_transform_edt(~sm)
            sgmc["n_sgmc_px"] = int(sm.sum())
            for name, sup in [("parent_h33-2-b2", parent)] + [(v["value"], v["support"]) for v in variants]:
                sgmc[name] = dict(mean_dist_px=round(float(dsg[sup].mean()), 4),
                                  frac_within_3px=round(float((dsg[sup] <= 3).mean()), 5),
                                  frac_within_1px=round(float((dsg[sup] <= 1).mean()), 5))
    else:
        sgmc["status"] = "external SGMC raster not restored; control not run"

    record["report_only"] = dict(
        note="REPORT ONLY, never a gate. The catalogue hide-and-recover proxy is expected to be "
             "near-zero and anti-correlated with live score for this lineage: the parent's whole "
             "design is to stay away from the catalogue while the proxy's truth IS the catalogue.",
        holdout_proxy=proxy, n_withheld_positives=n_withheld,
        leakage_canary_auc=canary, sgmc_control=sgmc)

    record["variants"] = [{k: v for k, v in d.items() if k != "support"} for d in variants]
    record["parent_support_stats"] = dict(n_dots=int(parent.sum()),
                                          block_cv_10km_parent=round(block_cv(parent, footprint), 5))
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(record, indent=2, default=float) + "\n")
    print(f"\n-> {args.evidence.relative_to(ROOT)}")
    for v in variants:
        print(f"{v['id']}: gates={v['format_report']['ok'] and v['local_validate']['all_checks_passed']} "
              f"sha={v['zeros']['sha256'][:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
