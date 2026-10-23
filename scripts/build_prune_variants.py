#!/usr/bin/env python3
"""Build the three v2 PRUNE-axis variants of parent R0 (h33-h33-2-b2).

Single-axis controlled edits of one named parent. Nothing here trains a
model, reads labels beyond the pinned catalogue, contacts a network, or
submits anything. The human competitor submits from their own account.

Recorded parent recipe (GEMSDOE32 @ 780a5a53, audit JSON description +
evidence/h33_removal_rule_scan.json R1-flankB2), verified bit-exactly in
this run before any variant is written:

    R0 dots == {h27-4-solo-d28 dots with Euclidean EDT to catalogue > 2 px}
    h27-4   == {dotted-h19-5-d2.8 dots with EDT > 1 px}   (also re-verified)

Variants (all unit-mass dots on the sample grid; human decision
2026-10-23: content-exact rebuild clears the start gate; untouched dots
keep the parent >2 px exclusion):

  prune3         R0 dots with d_cat > 3          (pure removal, no refill)
  r2p85          R0 dots with d_cat >= 3         (keeps the exactly-300 m ring)
  prune3fill20   prune3 + refill to 37,654 dots from the H19-5 support

  Post-merge note: parallel sessions on main built the same two pure arms
  (scripts/gemsdoe85_prune_session.py, gemsdoe85_rung_session.py); under the
  merged lock (rasterio 1.4.4) this builder reproduces their tracked files
  byte-for-byte. The refill arm is new in this session.
                 (pool: support & footprint & d_cat > 3 & >2.0 px from every
                 dot; order: tier [in d1.5 thinning, else in H19-4 support,
                 else rest], then distance-to-nearest-kept-dot desc, then
                 (row, col); single greedy pass, deterministic, no RNG).
                 Refill at the parent 2.8 px spacing is infeasible (only
                 611 pool pixels exist; measured, see evidence JSON), so
                 the refill spacing is 2.0 px -- a declared confounder.
                 Refill order is a lineage proxy, NOT the parent's field
                 ranking (no continuous ranking field is pinned anywhere;
                 H19-5/H19-4 on disk are binary).

Outputs (releases/, tracked by this repo since the rung sessions;
publication-permission flag IR-V2-04/10 stands):
  <id>.tif        NaN outside footprint (brief spec)
  <id>-zeros.tif  zeros outside footprint (fallback; upload only one)
  id = h33-2-b2-<value>-<yyyymmdd>-<NaN file sha8>  (repo convention)
plus one evidence JSON (--evidence). Idempotent: an existing output is
kept iff its bytes are identical; different bytes fail closed.

Inputs must already exist locally and match their pins (fail closed):
  data/sample_submission.tif, data/existing_faults.tif  (data_manifest.json)
  data/learning/h33-b2.tif                              (learning_manifest.json)
  data/scored/gemsdoe31-h27-4-solo-d28-...-nan.tif      (scored_artifacts.json)
  data/scored/gems24-h25-1-dotted-h19-5-d2-8-...-nan.tif
  data/scored/gems24-h25-1-dotted-h19-5-d1-5-...-nan.tif
  data/scored/gems19-h19-5-...-nan.tif, data/scored/gems19-h19-4.tif
Restore commands are in docs/SUBMIT.md. No input is downloaded here.
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
sys.path.insert(0, str(ROOT / "scripts"))
from validate_v2_release import sha256_file, validate  # noqa: E402

PINS = {
    "sample": ("data/sample_submission.tif",
               "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
    "catalogue": ("data/existing_faults.tif",
                  "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "r0": ("data/learning/h33-b2.tif",
           "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "h27": ("data/scored/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
            "07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40"),
    "d28": ("data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
            "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"),
    "d15": ("data/scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
            "68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310"),
    "h19_5": ("data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
              "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d"),
    "h19_4": ("data/scored/gems19-h19-4.tif",
              "89109a3bd2cd3b12e7a0f388113c519843acfc9c4f46825affefc3e63dd99b22"),
}
DATE_TAG = "20261023"
PARENT = "h33-h33-2-b2"
PARENT_N = 37_654
REFILL_SPACING_PX = 2.0  # parent spacing is >2.8 px; see docstring (infeasible for refill)


def read_dots(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.isfinite(a) & (a > 0)


def content_digest8(mask: np.ndarray) -> str:
    """Lineage writer's content tag: sha256(packbits(mask))[:8] (GEMSDOE32)."""
    return hashlib.sha256(np.packbits(mask)).hexdigest()[:8]


def disc_offsets(radius: float) -> list[tuple[int, int]]:
    r = int(np.ceil(radius))
    return [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
            if float(np.hypot(dy, dx)) <= radius]


def greedy_refill(pool: np.ndarray, kept: np.ndarray, order: np.ndarray,
                  need: int, spacing: float) -> np.ndarray:
    """Single deterministic pass over pre-ordered candidate flat indices.

    A candidate is accepted iff >`spacing` px (Euclidean) from every kept
    dot (guaranteed by pool construction) and every already-accepted dot
    (enforced by stamping a blocked disc of radius `spacing`).
    """
    h, w = pool.shape
    blocked = ~pool.copy()  # everything not in the pool is unavailable
    accepted = np.zeros_like(pool)
    offs = disc_offsets(spacing)
    n = 0
    flat_blocked = blocked.ravel()
    for idx in order:
        if n >= need:
            break
        if flat_blocked[idx]:
            continue
        y, x = divmod(int(idx), w)
        accepted[y, x] = True
        n += 1
        for dy, dx in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                blocked[yy, xx] = True
    return accepted


def write_pair(mask: np.ndarray, footprint: np.ndarray, sample_path: Path,
               out_dir: Path, stem_prefix: str) -> tuple[str, dict]:
    """Write the NaN/zeros pair under the repo id convention.

    id = <stem_prefix>-<NaN file sha8>. Files are staged under a pending
    name, hashed, then renamed. Idempotent: an existing file with identical
    bytes is kept; different bytes under the final name fail closed.
    Returns (variant_id, {encoding: {path, sha256, bytes}}).
    """
    with rasterio.open(sample_path) as tpl:
        profile = tpl.profile.copy()
    profile.update(driver="GTiff", dtype="float32", count=1, compress="deflate",
                   predictor=3, zlevel=9, tiled=True, blockxsize=256,
                   blockysize=256, nodata=None)
    values = mask.astype(np.float32)
    staged: dict[str, Path] = {}
    for suffix, expect, nodata, outside in (
            ("", "nan", float("nan"), np.nan), ("-zeros", "zeros", None, 0.0)):
        tmp = out_dir / f".{stem_prefix}-pending{suffix}.tif"
        if tmp.exists():
            tmp.unlink()
        arr = np.where(footprint, values, outside).astype(np.float32)
        with rasterio.open(tmp, "w", **dict(profile, nodata=nodata)) as ds:
            ds.write(arr, 1)
        with rasterio.open(tmp) as ds:  # re-read from disk; dots must round-trip
            back = ds.read(1)
        if not bool(((np.isfinite(back) & (back > 0)) == (mask & footprint)).all()):
            tmp.unlink(missing_ok=True)
            raise ValueError(f"disk round-trip changed the dot set for {tmp.name}")
        staged[expect] = tmp
    nan_sha = sha256_file(staged["nan"])
    vid = f"{stem_prefix}-{nan_sha[:8]}"
    written = {}
    for expect, tmp in staged.items():
        suffix = "" if expect == "nan" else "-zeros"
        path = out_dir / f"{vid}{suffix}.tif"
        digest = sha256_file(tmp)
        if path.exists():
            if sha256_file(path) != digest:
                tmp.unlink(missing_ok=True)
                raise FileExistsError(f"{path} exists with different bytes; refusing")
            tmp.unlink()
        else:
            tmp.replace(path)
        try:
            rel = str(path.relative_to(ROOT))
        except ValueError:
            rel = str(path)
        written[expect] = dict(path=rel, sha256=digest, bytes=path.stat().st_size)
    return vid, written


def diff_stats(mask: np.ndarray, parent: np.ndarray, dist: np.ndarray) -> dict:
    removed = parent & ~mask
    added = mask & ~parent
    dd = dist[mask]
    return {
        "n_dots": int(mask.sum()),
        "removed_vs_parent": int(removed.sum()),
        "added_vs_parent": int(added.sum()),
        "pct_changed_turnover": round(
            100.0 * float(removed.sum() + added.sum()) / float(parent.sum()), 3),
        "min_catalogue_distance_px": float(dd.min()) if dd.size else None,
        "dots_lt3px": int((dd < 3).sum()),
        "dots_le3px": int((dd <= 3).sum()),
        "dots_on_catalogue": int((mask & (dist == 0)).sum()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "releases")
    ap.add_argument("--evidence", type=Path,
                    default=ROOT / "evidence/v2-prune-builds.json")
    args = ap.parse_args()

    # 1. Verify every pinned input before use; fail closed.
    paths, input_receipts = {}, {}
    for key, (rel, pin) in PINS.items():
        p = ROOT / rel
        if not p.is_file():
            raise SystemExit(f"MISSING pinned input {rel}; restore it first (docs/SUBMIT.md)")
        digest = sha256_file(p)
        if digest != pin:
            raise SystemExit(f"SHA-256 MISMATCH for {rel}: {digest} != pinned {pin}")
        paths[key] = p
        input_receipts[key] = dict(path=rel, sha256=digest, bytes=p.stat().st_size)

    with rasterio.open(paths["sample"]) as ds:
        footprint = np.isfinite(ds.read(1))
    catalogue = read_dots(paths["catalogue"]) & footprint
    r0 = read_dots(paths["r0"])
    h27 = read_dots(paths["h27"])
    d28 = read_dots(paths["d28"])
    d15 = read_dots(paths["d15"])
    s5 = read_dots(paths["h19_5"])
    s4 = read_dots(paths["h19_4"])
    dist = distance_transform_edt(~catalogue)

    # 2. Rebuild gate, re-verified in this run (content-exact; human-approved
    #    2026-10-23). File-byte identity is NOT claimed (GDAL/zlib version).
    rebuild = {
        "r0_equals_prune_h27_gt2px": bool(((h27 & (dist > 2)) == r0).all()),
        "h27_equals_prune_d28_gt1px": bool(((d28 & (dist > 1)) == h27).all()),
        "r0_content_digest8": content_digest8(r0),
        "r0_content_digest8_matches_filename_tag_e5eb6e7e":
            content_digest8(r0) == "e5eb6e7e",
        "r0_dots": int(r0.sum()),
        "subset_chain_r0_in_h27_in_d28_in_h19_5": bool(
            not (r0 & ~h27).any() and not (h27 & ~d28).any() and not (d28 & ~s5).any()),
    }
    if not (rebuild["r0_equals_prune_h27_gt2px"] and rebuild["r0_dots"] == PARENT_N):
        raise SystemExit(f"REBUILD GATE FAILED: {rebuild}")
    parent = r0 & footprint
    if int(parent.sum()) != PARENT_N or bool((parent & catalogue).any()):
        raise SystemExit("parent mask sanity failed (count or catalogue mass)")

    # 3. Variant masks: PRUNE axis only.
    pure = parent & (dist > 3)
    ge = parent & (dist >= 3)
    need = PARENT_N - int(pure.sum())
    d_kept = distance_transform_edt(~pure)
    pool_parent_spacing = s5 & footprint & (dist > 3) & ~pure & (d_kept > 2.8)
    pool = s5 & footprint & (dist > 3) & ~pure & (d_kept > REFILL_SPACING_PX)
    tier = np.where(d15, 0, np.where(s4, 1, 2)).astype(np.int16)
    cand = np.flatnonzero(pool)
    # deterministic order: tier asc, distance-to-kept desc, then (row, col)
    keys = np.lexsort((cand % pool.shape[1], cand // pool.shape[1],
                       -d_kept.ravel()[cand], tier.ravel()[cand]))
    refill = greedy_refill(pool, pure, cand[keys], need, REFILL_SPACING_PX)
    masks = {
        "prune3": pure,
        "r2p85": ge,
        "prune3fill20": pure | refill,
    }
    refill_diag = {
        "needed": int(need),
        "accepted": int(refill.sum()),
        "pool_at_parent_spacing_gt2p8_px": int(pool_parent_spacing.sum()),
        "pool_at_refill_spacing_gt2p0_px": int(pool.sum()),
        "pool_no_spacing": int((s5 & footprint & (dist > 3) & ~pure).sum()),
        "accepted_by_tier": {f"tier{t}": int((refill & (tier == t)).sum()) for t in (0, 1, 2)},
        "refill_min_dist_to_kept_px": float(d_kept[refill].min()) if refill.any() else None,
    }
    if refill_diag["accepted"] != need:
        raise SystemExit(f"refill shortfall: {refill_diag}")

    # spacing verification for the refill variant (mutual NN over all dots)
    from scipy.spatial import cKDTree
    yx = np.column_stack(np.nonzero(masks["prune3fill20"]))
    nn, _ = cKDTree(yx).query(yx, k=2)
    refill_diag["refill_variant_min_mutual_nn_px"] = float(nn[:, 1].min())
    yx0 = np.column_stack(np.nonzero(parent))
    nn0, _ = cKDTree(yx0).query(yx0, k=2)
    refill_diag["parent_min_mutual_nn_px"] = float(nn0[:, 1].min())

    # 4. Write + validate each pair (validator re-reads from disk).
    args.out_dir.mkdir(parents=True, exist_ok=True)
    variants = {}
    for value, mask in masks.items():
        mask = mask & footprint
        stats = diff_stats(mask, parent, dist)
        if mask.shape != footprint.shape or bool((mask & catalogue).any()):
            raise SystemExit(f"{value}: catalogue mass or shape failure")
        if not (1.0 <= stats["pct_changed_turnover"] <= 50.0):
            raise SystemExit(f"{value}: turnover outside the brief 1-50% band: {stats}")
        vid, files = write_pair(mask, footprint, paths["sample"], args.out_dir,
                                f"h33-2-b2-{value}-{DATE_TAG}")
        receipts = {enc: validate(ROOT / f["path"], paths["sample"],
                                   paths["catalogue"], enc)
                    for enc, f in files.items()}
        if not all(r["format_ok"] for r in receipts.values()):
            raise SystemExit(f"{value}: FORMAT GATE FAILED: {receipts}")
        variants[value] = dict(id=vid, axis="PRUNE", parent=PARENT,
                               content_digest8=content_digest8(mask),
                               diff_vs_parent=stats, files=files,
                               format_receipts={k: dict(checks=v["checks"], format_ok=v["format_ok"])
                                                for k, v in receipts.items()})
        print(f"BUILT {vid}: dots={stats['n_dots']} turnover={stats['pct_changed_turnover']}% "
              f"nan_sha={files['nan']['sha256'][:12]} zeros_sha={files['zeros']['sha256'][:12]}")

    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        git_sha = None
    evidence = {
        "purpose": "v2 PRUNE-axis variant builds from parent R0; BUILT, not submitted",
        "git_sha_at_build": git_sha,
        "seed": "none (fully deterministic; no RNG)",
        "environment": {"rasterio": rasterio.__version__, "gdal": rasterio.__gdal_version__,
                        "numpy": np.__version__},
        "inputs_verified": input_receipts,
        "rebuild_gate": rebuild,
        "refill_diagnostics": refill_diag,
        "variants": variants,
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
    print(f"wrote {args.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
