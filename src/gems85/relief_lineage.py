"""AXIS = RELIEF controlled tercile-mass exchange on parent R0 (`h33-h33-2-b2`).

Builds deterministic, fixed-count (`37,654` dots) variants of R0 that shift 10–15 % of dot mass
between Basin / Piedmont / Range-front terciles derived from the two competition detrended-elevation
bands (`det_elev` Band 12 and `det_elev_slope` Band 19 of `training_features.tif`).

Hard-constraint invariants enforced on every emitted variant:
  1. Every input file is SHA-256 verified against `registry/data_manifest.json`,
     `registry/learning_manifest.json`, and `src/gems85/r0_lineage.PINS` before reading.
  2. Parent R0 (`37,654` dots) is recipe-rebuilt from the pinned H19-5 skeleton and verified
     both pixel-for-pixel AND byte-for-byte (SHA-256 of written NaN and zeros GeoTIFFs matches
     `baeae321...` and `c55bafc4...`).
  3. Zero mass on catalogue pixels AND `d_cat > 3.0 px` (`min >= sqrt(10) = 3.1623 px`) on 100 %
     of emitted pixels (Hard Constraint #4). Non-source terciles replace their `d_cat <= 3.0`
     parent flank dots 1-for-1 inside their own tercile so tercile mass changes ONLY by the
     commanded inter-tercile shift `delta_by_tercile`.
  4. Total dot count is held strictly fixed (`sum(delta_by_tercile.values()) == 0`, `37,654` on R0),
     and every newly placed dot honors R0's `2.8 px` Euclidean spacing rung.
  5. Zero label leakage: physical ridge ranking uses only geophysical/topographic bands and
     pinned ancestor skeletons (`H19-5`, `H19-4`, `H16-1`); `dist_to_cat` is passed explicitly so
     spatially-blocked hide-and-recover evaluation uses `dist_to_visible` with withheld faults unseen.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

from .r0_lineage import (
    DATA,
    MIN_DIST,
    PATHS,
    PINS,
    ROOT,
    Lineage,
    footprint,
    rebuild,
    sha256_file,
    verify_pins,
)

TRAINING_FEATURES_SHA256 = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
H19_4_SHA256 = "89109a3bd2cd3b12e7a0f388113c519843acfc9c4f46825affefc3e63dd99b22"
H16_1_SHA256 = "055309694ed499ca3d87e76b3f5e81c292aef6e39c418d33ff5a817aa1309bea"
SGMC_SHA256 = "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"

EXTRA_PATHS = {
    "training_features": DATA / "training_features.tif",
    "h19_4": DATA / "scored" / "gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif",
    "h16_1": DATA / "scored" / "gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif",
    "sgmc": DATA / "external" / "derived_sgmc_faults_100m_u8.tif",
}
EXTRA_PINS = {
    "training_features": TRAINING_FEATURES_SHA256,
    "h19_4": H19_4_SHA256,
    "h16_1": H16_1_SHA256,
    "sgmc": SGMC_SHA256,
}

TERCILE_NAMES = ("basin", "piedmont", "range")
COLLAR_PX = 3.0
OFFS_28 = [
    (dy, dx)
    for dy in range(-3, 4)
    for dx in range(-3, 4)
    if dy * dy + dx * dx < MIN_DIST * MIN_DIST
]


def verify_manifest_hashes() -> dict:
    """Verify SHA-256 of all entries in data_manifest.json, learning_manifest.json, and R0 pins."""
    report: dict[str, dict] = {}
    for manifest_name, base_dir in (
        ("data_manifest.json", DATA),
        ("learning_manifest.json", DATA / "learning"),
    ):
        mpath = ROOT / "registry" / manifest_name
        entries = json.loads(mpath.read_text())["files"]
        verified = []
        for entry in entries:
            p = base_dir / entry["dest"]
            if not p.is_file():
                raise FileNotFoundError(
                    f"{manifest_name}:{entry['id']} missing at {p.relative_to(ROOT)}"
                )
            got = sha256_file(p)
            sz = p.stat().st_size
            if got != entry["sha256"] or ("bytes" in entry and sz != entry["bytes"]):
                raise ValueError(
                    f"{manifest_name}:{entry['id']} mismatch: got {sz}B/{got}, "
                    f"expected {entry.get('bytes')}B/{entry['sha256']}"
                )
            verified.append(
                dict(
                    id=entry["id"],
                    path=str(p.relative_to(ROOT)),
                    bytes=sz,
                    sha256=got,
                )
            )
        report[manifest_name] = dict(count=len(verified), all_verified=True, files=verified)

    r0_pins = verify_pins()
    for k, exp in EXTRA_PINS.items():
        p = EXTRA_PATHS[k]
        if not p.is_file():
            raise FileNotFoundError(f"{k}: missing pinned file {p.relative_to(ROOT)}")
        got = sha256_file(p)
        if got != exp:
            raise ValueError(f"{k}: sha256 {got} != pinned {exp}")
        r0_pins[k] = dict(path=str(p.relative_to(ROOT)), sha256=got, bytes=p.stat().st_size)

    report["lineage_and_feature_pins"] = r0_pins
    return report


def rebuild_and_verify_r0_bytes() -> tuple[Lineage, dict]:
    """Rebuild R0 from the H19-5 skeleton and assert byte-identical GeoTIFF SHA-256 on both encodings."""
    L = rebuild(verify_against_pinned_files=True)
    foot = footprint()
    with rasterio.open(PATHS["sample_submission"]) as s:
        prof = s.profile.copy()
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
    clean = (L.r0 & foot).astype(np.float32)
    rebuilt_shas = {}
    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        for mode, pin_key in (("nan", "r0_nan"), ("zeros", "r0_zeros")):
            out_p = tmp / f"rebuilt_{pin_key}.tif"
            p = base.copy()
            if mode == "nan":
                p.update(nodata=np.nan)
                arr = np.where(foot, clean, np.float32(np.nan)).astype(np.float32)
            else:
                p.update(nodata=None)
                arr = np.where(foot, clean, np.float32(0.0)).astype(np.float32)
            with rasterio.open(out_p, "w", **p) as dst:
                dst.write(arr, 1)
            got = sha256_file(out_p)
            if got != PINS[pin_key]:
                raise AssertionError(
                    f"Rebuilt {pin_key} GeoTIFF sha256 {got} != pinned {PINS[pin_key]}"
                )
            rebuilt_shas[pin_key] = got

    return L, dict(
        counts=L.counts(),
        pixel_identical_to_pinned=True,
        byte_identical_geotiff_rebuild=True,
        rebuilt_r0_nan_sha256=rebuilt_shas["r0_nan"],
        rebuilt_r0_zeros_sha256=rebuilt_shas["r0_zeros"],
    )


def _deterministic_pct_rank(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Within-footprint percentile rank in [0, 1] with deterministic row-major tie-breaking.

    Invalid/nodata cells inside the footprint receive median 0.50 prior to exact footprint ranking
    so the three footprint terciles partition `foot` completely and disjointly.
    """
    filled = np.where(np.isfinite(arr) & foot, arr, np.nan)
    med = float(np.nanmedian(filled[foot]))
    vals = np.where(np.isfinite(filled), filled, med)[foot]
    # Primary sort on value, secondary tie-break on flat footprint position (0..N_foot-1)
    idx_tie = np.arange(vals.size, dtype=np.int64)
    order = np.lexsort((idx_tie, vals))
    ranks = np.empty(vals.size, dtype=np.float64)
    ranks[order] = np.linspace(0.0, 1.0, vals.size)
    out = np.zeros(arr.shape, dtype=np.float64)
    out[foot] = ranks
    return out


def _local_prominence(rank_field: np.ndarray, size: int = 9) -> np.ndarray:
    return rank_field - ndimage.uniform_filter(rank_field, size=size)


@dataclass(frozen=True)
class ReliefFields:
    foot: np.ndarray
    relief_index: np.ndarray
    terciles: dict[str, np.ndarray]
    tercile_summary: dict[str, dict]
    dot_rank_score: np.ndarray
    cand_pool: np.ndarray
    cand_score_range: np.ndarray
    cand_score_basin: np.ndarray
    ancestor_union: np.ndarray


def build_relief_fields(skeleton_h19_5: np.ndarray | None = None) -> ReliefFields:
    """Compute Basin/Piedmont/Range-front terciles and label-free physical ridge scores."""
    foot = footprint()
    if skeleton_h19_5 is None:
        with rasterio.open(PATHS["h19_5"]) as ds:
            skeleton_h19_5 = (np.nan_to_num(ds.read(1), nan=0.0) > 0.5) & foot
    else:
        skeleton_h19_5 = np.asarray(skeleton_h19_5, bool) & foot

    with rasterio.open(EXTRA_PATHS["h19_4"]) as ds:
        h19_4 = (np.nan_to_num(ds.read(1), nan=0.0) > 0.5) & foot
    with rasterio.open(EXTRA_PATHS["h16_1"]) as ds:
        h16_1 = (np.nan_to_num(ds.read(1), nan=0.0) > 0.5) & foot

    with rasterio.open(EXTRA_PATHS["training_features"]) as ds:
        names = [desc.split(" - ")[0] for desc in ds.descriptions]
        bmap = {n: i + 1 for i, n in enumerate(names)}
        det_elev = ds.read(bmap["det_elev"]).astype(np.float64)
        det_slope = ds.read(bmap["det_elev_slope"]).astype(np.float64)
        tmi_hg = ds.read(bmap["tmi_hg"]).astype(np.float64)
        grav_slope = ds.read(bmap["iso_grav_anom_slope"]).astype(np.float64)
        tc = ds.read(bmap["tc"]).astype(np.float64)
        geod_2nd = ds.read(bmap["geod_2ndinv"]).astype(np.float64)

    for a in (det_elev, det_slope, tmi_hg, grav_slope, tc, geod_2nd):
        a[(~np.isfinite(a)) | (a <= -1e30) | (~foot)] = np.nan

    r_elev = _deterministic_pct_rank(det_elev, foot)
    r_slope = _deterministic_pct_rank(det_slope, foot)
    r_tmi = _deterministic_pct_rank(tmi_hg, foot)
    r_grav = _deterministic_pct_rank(grav_slope, foot)
    r_tc = _deterministic_pct_rank(tc, foot)
    r_geod = _deterministic_pct_rank(geod_2nd, foot)

    # Composite structural-relief index from the two detrended-elevation bands, partitioned into
    # exact equal-area footprint terciles via deterministic rank order.
    raw_relief = 0.70 * r_elev + 0.30 * r_slope
    relief_rank = _deterministic_pct_rank(raw_relief, foot)
    n_foot = int(foot.sum())
    n_t1 = n_foot // 3
    n_t2 = (2 * n_foot) // 3
    f_vals = raw_relief[foot]
    f_order = np.lexsort((np.arange(n_foot, dtype=np.int64), f_vals))
    t_code_flat = np.empty(n_foot, dtype=np.int8)
    t_code_flat[f_order[:n_t1]] = 0
    t_code_flat[f_order[n_t1:n_t2]] = 1
    t_code_flat[f_order[n_t2:]] = 2
    t_grid = np.full(foot.shape, -1, dtype=np.int8)
    t_grid[foot] = t_code_flat

    terciles = {
        "basin": t_grid == 0,
        "piedmont": t_grid == 1,
        "range": t_grid == 2,
    }
    tercile_summary = {}
    for tname, tmask in terciles.items():
        ev_v = det_elev[tmask & np.isfinite(det_elev)]
        sl_v = det_slope[tmask & np.isfinite(det_slope)]
        tercile_summary[tname] = dict(
            footprint_pixels=int(tmask.sum()),
            footprint_share=round(float(tmask.sum()) / n_foot, 6),
            det_elev_median_m=round(float(np.median(ev_v)), 2),
            det_elev_iqr_m=[round(float(x), 2) for x in np.quantile(ev_v, [0.25, 0.75])],
            det_elev_slope_median=round(float(np.median(sl_v)), 3),
        )

    # Label-free physical ridge prominence (900 m x 900 m high-pass)
    p_subsurf = (
        0.40 * _local_prominence(r_tmi, 9)
        + 0.35 * _local_prominence(r_grav, 9)
        + 0.15 * _local_prominence(r_tc, 9)
        + 0.10 * (r_geod - 0.50)
    )
    p_scarp = _local_prominence(r_slope, 9)
    p_phys = 0.50 * p_scarp + 0.50 * p_subsurf

    anc_count = (
        skeleton_h19_5.astype(np.float64)
        + h19_4.astype(np.float64)
        + h16_1.astype(np.float64)
    )
    ancestor_union = (anc_count > 0) & foot
    dot_rank_score = p_phys + 0.15 * anc_count

    # 4-azimuth 1-px non-maximum suppression for off-skeleton physical ridge crests
    nms = np.zeros_like(foot)
    for dy, dx in ((1, 0), (0, 1), (1, 1), (1, -1)):
        s1 = np.roll(p_phys, (dy, dx), axis=(0, 1))
        s2 = np.roll(p_phys, (-dy, -dx), axis=(0, 1))
        nms |= (p_phys >= s1) & (p_phys > s2)
    nms &= foot & (p_phys > 0.04)

    cand_pool = (ancestor_union | nms) & foot
    anc_bonus = 0.50 * ancestor_union.astype(np.float64) + 0.15 * anc_count
    cand_score_range = p_phys + anc_bonus
    # In alluvial basins, weight subsurface magnetic/gravity horizontal gradients higher to target
    # blind step-overs beneath Quaternary playafill rather than shoreline micro-scarps.
    cand_score_basin = 0.30 * p_scarp + 0.70 * p_subsurf + anc_bonus

    return ReliefFields(
        foot=foot,
        relief_index=relief_rank,
        terciles=terciles,
        tercile_summary=tercile_summary,
        dot_rank_score=dot_rank_score,
        cand_pool=cand_pool,
        cand_score_range=cand_score_range,
        cand_score_basin=cand_score_basin,
        ancestor_union=ancestor_union,
    )


def shift_relief_terciles(
    base_dots: np.ndarray,
    dist_to_cat: np.ndarray,
    rf: ReliefFields,
    delta_by_tercile: dict[str, int],
    *,
    collar_px: float = COLLAR_PX,
) -> tuple[np.ndarray, dict]:
    """Shift exact dot counts `delta_by_tercile` across Basin/Piedmont/Range-front terciles.

    Total dot count is held strictly constant (`sum(delta_by_tercile.values()) == 0`), every
    emitted dot satisfies `dist_to_cat > collar_px`, and every newly added dot respects the
    `2.8 px` Euclidean spacing disc relative to all kept dots.
    """
    base = np.asarray(base_dots, bool) & rf.foot
    H, W = base.shape
    if set(delta_by_tercile) != set(TERCILE_NAMES):
        raise ValueError(f"delta_by_tercile keys must be {TERCILE_NAMES}")
    if sum(int(v) for v in delta_by_tercile.values()) != 0:
        raise ValueError(f"RELIEF shift must preserve count (sum != 0): {delta_by_tercile}")

    kept = np.zeros_like(base)
    need_add: dict[str, int] = {}
    before_counts: dict[str, int] = {}
    collar_cleared: dict[str, int] = {}

    for tname in TERCILE_NAMES:
        tmask = rf.terciles[tname]
        d_t = base & tmask
        n_orig = int(d_t.sum())
        before_counts[tname] = n_orig
        n_target = n_orig + int(delta_by_tercile[tname])
        if n_target < 0:
            raise ValueError(f"{tname}: target count {n_target} < 0")
        valid_d = d_t & (dist_to_cat > collar_px)
        n_valid = int(valid_d.sum())
        collar_cleared[tname] = n_orig - n_valid

        if n_valid >= n_target:
            n_drop = n_valid - n_target
            if n_drop > 0:
                ys, xs = np.nonzero(valid_d)
                sc = rf.dot_rank_score[ys, xs]
                order = np.lexsort((xs, ys, sc))  # ascending score, row-major tie-break
                keep_idx = order[n_drop:]
                kept[ys[keep_idx], xs[keep_idx]] = True
            else:
                kept |= valid_d
            need_add[tname] = 0
        else:
            kept |= valid_d
            need_add[tname] = n_target - n_valid

    yy, xx = np.mgrid[-3:4, -3:4]
    disc28 = (yy * yy + xx * xx) < MIN_DIST * MIN_DIST
    added_from_ancestor: dict[str, int] = {}
    added_from_nms: dict[str, int] = {}

    for tname in TERCILE_NAMES:
        n_add = need_add[tname]
        added_from_ancestor[tname] = 0
        added_from_nms[tname] = 0
        if n_add <= 0:
            continue
        blocked = ndimage.binary_dilation(kept, structure=disc28)
        cmask = rf.terciles[tname] & rf.cand_pool & (dist_to_cat > collar_px) & (~blocked)
        cy, cx = np.nonzero(cmask)
        sc_field = rf.cand_score_basin if tname == "basin" else rf.cand_score_range
        cs = sc_field[cy, cx]
        order = np.lexsort((cx, cy, -cs))  # descending score, row-major tie-break
        added = 0
        anc_hits = 0
        for idx_c in order:
            y, x = int(cy[idx_c]), int(cx[idx_c])
            if any(
                0 <= y + dy < H and 0 <= x + dx < W and kept[y + dy, x + dx]
                for dy, dx in OFFS_28
            ):
                continue
            kept[y, x] = True
            added += 1
            if rf.ancestor_union[y, x]:
                anc_hits += 1
            if added == n_add:
                break
        if added != n_add:
            raise RuntimeError(f"{tname}: candidate shortfall ({added}/{n_add} added)")
        added_from_ancestor[tname] = anc_hits
        added_from_nms[tname] = added - anc_hits

    after_counts = {tname: int((kept & rf.terciles[tname]).sum()) for tname in TERCILE_NAMES}
    assert int(kept.sum()) == int(base.sum()), "fixed-count invariant violated"
    assert int((kept & (dist_to_cat <= collar_px)).sum()) == 0, "collar invariant violated"

    detail = dict(
        before_tercile_dots=before_counts,
        after_tercile_dots=after_counts,
        commanded_delta=delta_by_tercile,
        collar_le3_cleared_by_tercile=collar_cleared,
        added_from_pinned_ancestors_by_tercile=added_from_ancestor,
        added_from_physical_nms_by_tercile=added_from_nms,
    )
    return kept, detail
