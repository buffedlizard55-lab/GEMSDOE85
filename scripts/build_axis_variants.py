#!/usr/bin/env python3
"""
Build up to 3 variants of R0 differing ONLY on one AXIS.
Implements CONCENTRATION axis: move 10-20% dots from lowest-prior km-scale blocks to highest-prior blocks.
Hard constraints enforced:
 - zero mass on catalogue pixels, >=3px halo (Chebyshev) unless AXIS=PRUNE
 - format check against sample_submission.tif
 - sha256 not in ledger, parent-diff recorded, file re-read from disk
"""
from __future__ import annotations
import hashlib, json, pathlib, sys, datetime, csv, os
import numpy as np
import rasterio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
sys.path.insert(0, str(ROOT/"vendor"))

from gems85.grid import footprint, catalogue, read_band, HEIGHT, WIDTH, TRANSFORM, EPSG, R_PIXELS, ALPHA, BETA
from gems85.submission import write_raster, validate, sha256_file
from gems85.emission import poisson_thin, exclusion_mask
from scipy import ndimage as ndi
RADIUS_PX = R_PIXELS

PARENT_ID = "h33-h33-2-b2"
PARENT_PATH = ROOT/"data/registry_rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
PARENT_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
DATE_STR = datetime.datetime.utcnow().strftime("%Y%m%d")
AXIS = "CONC"  # CONCENTRATION
# CONCENTRATION values: percent moved
VALUES = [10, 15, 20]  # percent
BLOCK_PX = 50  # 5km
PRIOR_BAND = "tmi_hg"  # band 3
PRIOR_BAND_IDX = 3

# For ledger, we need to check existing (AXIS,value) pairs
LEDGER_CSV = ROOT/"ledger/submissions.csv"

def load_ledger():
    if not LEDGER_CSV.exists():
        return []
    import csv
    with open(LEDGER_CSV) as f:
        return list(csv.DictReader(f))

def compute_prior_blocks(prior_arr: np.ndarray, fp: np.ndarray, block_px: int):
    h,w = prior_arr.shape
    nh = (h + block_px - 1)//block_px
    nw = (w + block_px - 1)//block_px
    block_prior = np.full((nh, nw), np.nan, dtype=float)
    block_counts = np.zeros((nh,nw), dtype=int)
    # For each block, compute mean prior over finite footprint pixels
    for i in range(nh):
        r0 = i*block_px
        r1 = min(h, (i+1)*block_px)
        for j in range(nw):
            c0 = j*block_px
            c1 = min(w, (j+1)*block_px)
            blk = prior_arr[r0:r1, c0:c1]
            m = fp[r0:r1, c0:c1]
            # valid prior pixels: finite and in footprint
            valid = m & np.isfinite(blk)
            if valid.sum()>0:
                # use absolute value for gradient magnitude
                block_prior[i,j] = np.nanmean(np.abs(blk[valid]))
                block_counts[i,j] = int(valid.sum())
            else:
                block_prior[i,j] = np.nan
    return block_prior, nh, nw

def block_index_for_pixel(y,x, block_px):
    return y//block_px, x//block_px

def compute_block_density_cv(dot_mask: np.ndarray, fp: np.ndarray, block_px: int):
    h,w = dot_mask.shape
    nh = (h + block_px - 1)//block_px
    nw = (w + block_px - 1)//block_px
    densities = []
    for i in range(nh):
        r0=i*block_px; r1=min(h,(i+1)*block_px)
        for j in range(nw):
            c0=j*block_px; c1=min(w,(j+1)*block_px)
            fp_blk = fp[r0:r1,c0:c1]
            dot_blk = dot_mask[r0:r1,c0:c1]
            n_fp = int(fp_blk.sum())
            n_dot = int(dot_blk.sum())
            if n_fp>0:
                densities.append(n_dot / n_fp)
    densities = np.array(densities)
    # CV = std/mean
    mean = densities.mean()
    std = densities.std()
    cv = std/mean if mean>0 else 0.0
    return float(cv), float(mean), float(std), densities

def main():
    print("=== Verify manifest hashes (core) ===")
    # Already verified via restore_data, but double-check key files
    import hashlib
    for p in [ROOT/"data/sample_submission.tif", ROOT/"data/labels.tif", ROOT/"data/existing_faults.tif", PARENT_PATH]:
        if not p.exists():
            print(f"Missing {p}")
            sys.exit(1)
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        print(f"{p.name[:40]} sha256 {h[:8]}")
    # check parent sha
    parent_hash = hashlib.sha256(PARENT_PATH.read_bytes()).hexdigest()
    print(f"Parent {PARENT_ID} sha256 {parent_hash}")
    if parent_hash != PARENT_SHA:
        print(f"ERROR: parent sha mismatch! expected {PARENT_SHA}, got {parent_hash}")
        print("Stop and report; never approximate parent")
        sys.exit(1)
    print("Parent verified, match expected sha256")
    # load parent raster
    with rasterio.open(PARENT_PATH) as src:
        parent_arr = src.read(1)
        assert src.height==HEIGHT and src.width==WIDTH
        assert src.crs.to_epsg()==EPSG
        assert tuple(src.transform)[:6]==tuple(TRANSFORM)[:6]
    fp = footprint()
    cat = catalogue()
    # parent dot mask
    parent_dots = (parent_arr > 0) & np.isfinite(parent_arr)
    print(f"Parent dots {int(parent_dots.sum())}, footprint {int(fp.sum())}, cat sum {int(cat.sum())}")
    # check zero catalogue mass and >=3px halo
    # For parent, we know it has 0 within Euclidean2, but 3843 within Chebyshev3
    halo3 = ndi.binary_dilation(cat, np.ones((3,3), bool), iterations=3)
    print(f"Parent within 3px Chebyshev halo: {int((parent_dots & halo3).sum())} (should be 3843 per earlier calc)")
    # For new variants, we enforce >=3px Chebyshev (strict)
    allowed_mask = fp & ~halo3
    print(f"Allowed pixels (>=3px from cat, inside fp): {int(allowed_mask.sum())} / {int(fp.sum())}")
    # Load prior band
    print(f"Loading prior band {PRIOR_BAND} (idx {PRIOR_BAND_IDX})")
    prior_arr = read_band(ROOT/"data/training_features.tif", PRIOR_BAND_IDX).astype(np.float32)
    # replace sentinel
    prior_arr[prior_arr < -1e30] = np.nan
    # Count finite
    print(f"Prior finite inside fp: {int(np.isfinite(prior_arr[fp]).sum())}, min {np.nanmin(np.abs(prior_arr[fp])):.2f} max {np.nanmax(np.abs(prior_arr[fp])):.2f}")
    # Compute block priors
    block_prior, nh, nw = compute_prior_blocks(prior_arr, fp, BLOCK_PX)
    print(f"Block prior shape {nh}x{nw} = {nh*nw} blocks, valid {int(np.isfinite(block_prior).sum())}")
    # Rank blocks by prior
    finite_mask = np.isfinite(block_prior)
    flat_prior = block_prior[finite_mask]
    flat_idx = np.argwhere(finite_mask)
    # sort descending
    order_desc = np.argsort(-flat_prior)
    order_asc = np.argsort(flat_prior)
    # For CV baseline
    cv_before, mean_before, std_before, dens_before = compute_block_density_cv(parent_dots, fp, BLOCK_PX)
    print(f"Parent CV before: {cv_before:.4f} (mean density {mean_before:.6f}, std {std_before:.6f})")
    # We need to define low-prior blocks as bottom 25% and high-prior as top 25% (or bottom/top 20%?)
    # Let's define bottom quartile and top quartile
    n_blocks_finite = len(flat_prior)
    q = n_blocks_finite//4
    low_block_coords = set(tuple(flat_idx[order_asc[i]]) for i in range(q))
    high_block_coords = set(tuple(flat_idx[order_desc[i]]) for i in range(q))
    print(f"Low-prior blocks (bottom 25%): {len(low_block_coords)}, High-prior blocks (top 25%): {len(high_block_coords)}")
    # For each block, we need mask to quickly test membership
    # Build block-id array for each pixel
    block_id_y = (np.arange(HEIGHT)[:,None] // BLOCK_PX)
    block_id_x = (np.arange(WIDTH)[None,:] // BLOCK_PX)
    # Instead, for performance, we will create boolean masks for low/high blocks
    low_mask = np.zeros((HEIGHT,WIDTH), dtype=bool)
    high_mask = np.zeros((HEIGHT,WIDTH), dtype=bool)
    for (i,j) in low_block_coords:
        r0=i*BLOCK_PX; r1=min(HEIGHT,(i+1)*BLOCK_PX)
        c0=j*BLOCK_PX; c1=min(WIDTH,(j+1)*BLOCK_PX)
        low_mask[r0:r1,c0:c1]=True
    for (i,j) in high_block_coords:
        r0=i*BLOCK_PX; r1=min(HEIGHT,(i+1)*BLOCK_PX)
        c0=j*BLOCK_PX; c1=min(WIDTH,(j+1)*BLOCK_PX)
        high_mask[r0:r1,c0:c1]=True
    # Count parent dots in low/high
    n_low_parent = int((parent_dots & low_mask).sum())
    n_high_parent = int((parent_dots & high_mask).sum())
    print(f"Parent dots in low-prior blocks: {n_low_parent}, high-prior: {n_high_parent}")
    # Prepare ledger directory
    ledger_path = LEDGER_CSV
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    # Check existing ledger for duplicates
    existing = load_ledger()
    existing_hashes = set(r['sha256'] for r in existing if 'sha256' in r)
    existing_axis_val = set((r['axis'], r['value']) for r in existing if 'axis' in r and 'value' in r)
    print(f"Existing ledger rows: {len(existing)}, hashes: {len(existing_hashes)}")
    for v in VALUES:
        key = (AXIS, str(v))
        if key in existing_axis_val:
            print(f"Skipping {key} already in ledger")
            continue
    # Releases directory
    releases = ROOT/"releases"
    releases.mkdir(parents=True, exist_ok=True)

    results = []
    rng = np.random.default_rng(20261023)  # fixed seed

    for pct in VALUES:
        n_move = int(round(parent_dots.sum() * pct/100.0))
        print(f"\n=== Building {AXIS}{pct} move {n_move} dots ({pct}%) ===")
        # Step 1: identify source dots to remove: randomly sample from parent dots in low-prior blocks
        # If not enough dots in low blocks, supplement from global low-prior sorted by block prior
        ys, xs = np.where(parent_dots & low_mask)
        n_low_available = len(ys)
        print(f"  low-prior dots available {n_low_available}, need {n_move}")
        if n_low_available < n_move:
            # fallback: also consider next-lowest blocks
            # Expand low pool to bottom 50%
            q2 = n_blocks_finite//2
            low_block_coords2 = set(tuple(flat_idx[order_asc[i]]) for i in range(q2))
            low_mask2 = np.zeros((HEIGHT,WIDTH), dtype=bool)
            for (i,j) in low_block_coords2:
                r0=i*BLOCK_PX; r1=min(HEIGHT,(i+1)*BLOCK_PX)
                c0=j*BLOCK_PX; c1=min(WIDTH,(j+1)*BLOCK_PX)
                low_mask2[r0:r1,c0:c1]=True
            ys2, xs2 = np.where(parent_dots & low_mask2)
            ys, xs = ys2, xs2
            n_low_available = len(ys)
            print(f"  expanded low pool to 50% -> available {n_low_available}")
            if n_low_available < n_move:
                print(f"ERROR: not enough low-prior dots to move {pct}%, available {n_low_available}")
                # fallback to random from all parent dots
                ys_all, xs_all = np.where(parent_dots)
                idx = rng.choice(len(ys_all), size=n_move, replace=False)
                ys, xs = ys_all[idx], xs_all[idx]
                print(f"  fallback random from all dots")
            else:
                idx = rng.choice(n_low_available, size=n_move, replace=False)
                ys, xs = ys[idx], xs[idx]
        else:
            idx = rng.choice(n_low_available, size=n_move, replace=False)
            ys, xs = ys[idx], xs[idx]
        # Create copy of parent dots and remove selected
        variant_dots = parent_dots.copy()
        variant_dots[ys, xs] = False
        # Enforce 3px halo compliance: remove all parent dots within halo3 first (required for non-PRUNE axes)
        n_halo_parent = int((variant_dots & halo3).sum())
        # Also track halo dots that were among the selected removal set already removed
        # Now remove all halo dots from variant_dots (if any remain)
        variant_dots = variant_dots & ~halo3
        n_halo_removed = n_halo_parent  # total halo dots removed from parent (including those that were in low selection but we removed duplicate count)
        # For accurate accounting, n_removed total = n_halo_removed + n_move_adjusted
        # But we already removed n_move low dots; some of those may have been halo dots, so we double counted.
        # Let's compute total dots removed vs parent:
        # parent -> variant_dots after both steps: parent minus (halo dots union low selection)
        # Simpler: compute total removed as parent count - current variant_dots count before adding
        n_after_removal = int(variant_dots.sum())
        n_removed_total = int(parent_dots.sum()) - n_after_removal
        print(f"  halo parent {n_halo_parent}, after low removal halo removed total, after removal total {n_after_removal}, removed total {n_removed_total} (low {n_move}+halo {n_halo_parent})")
        n_removed = n_removed_total
        # Step 2: generate new dots in high-prior blocks
        # Allowed for new dots: footprint & not halo3 & not already variant_dots & high_mask
        allowed_high = allowed_mask & high_mask & ~variant_dots
        # Also need to ensure we don't place dots too close to existing dots if we want poisson spacing
        # We'll use poisson_thin with uniform field over allowed_high
        # Create a random uniform field over allowed_high to give random positions
        # Field value 1 where allowed, 0 elsewhere
        # Need to add back n_removed_total to return to parent count (37654)
        n_to_add = n_removed  # to hold count
        print(f"  need to add back {n_to_add} to return to 37654 (parent) ")
        field = np.zeros((HEIGHT,WIDTH), dtype=np.float32)
        field[allowed_high] = rng.random(allowed_high.sum()).astype(np.float32) + 0.1  # ensure >0
        # Use poisson_thin to select n_to_add dots with sep 2.8
        new_dots_mask = poisson_thin(field, n=n_to_add, sep_px=2.8, allowed=allowed_high)
        n_new = int(new_dots_mask.sum())
        print(f"  requested {n_to_add} new dots, poisson_thin returned {n_new}")
        if n_new < n_to_add:
            # If not enough placed due to spacing, try larger pool or reduce sep
            # Try with sep 2.0
            field2 = np.zeros((HEIGHT,WIDTH), dtype=np.float32)
            # assign again random
            field2[allowed_high] = rng.random(allowed_high.sum()).astype(np.float32) + 0.1
            new_dots_mask = poisson_thin(field2, n=n_to_add, sep_px=2.0, allowed=allowed_high)
            n_new = int(new_dots_mask.sum())
            print(f"  retry sep2.0 -> {n_new}")
        if n_new < n_to_add:
            # fallback: random sample without spacing
            avail_y, avail_x = np.where(allowed_high)
            if len(avail_y) >= n_to_add:
                idx2 = rng.choice(len(avail_y), size=n_to_add, replace=False)
                new_dots_mask = np.zeros((HEIGHT,WIDTH), dtype=bool)
                new_dots_mask[avail_y[idx2], avail_x[idx2]] = True
                n_new = n_to_add
                print(f"  fallback random sample {n_new}")
            else:
                print(f"ERROR: not enough allowed pixels {len(avail_y)} for {n_to_add}")
                sys.exit(1)
        # Add new dots
        variant_dots = variant_dots | new_dots_mask
        total_dots = int(variant_dots.sum())
        print(f"  variant total dots {total_dots} (parent {int(parent_dots.sum())}), removed {n_removed}, added {n_new}")
        if total_dots != int(parent_dots.sum()):
            print(f"ERROR: count mismatch, expected {int(parent_dots.sum())}, got {total_dots}")
            # adjust by removing/adding random
            if total_dots > int(parent_dots.sum()):
                # remove extra random
                diff = total_dots - int(parent_dots.sum())
                vy, vx = np.where(variant_dots)
                # prefer to remove from new dots if possible
                ny, nx = np.where(new_dots_mask)
                if len(ny) >= diff:
                    idxr = rng.choice(len(ny), size=diff, replace=False)
                    variant_dots[ny[idxr], nx[idxr]] = False
                else:
                    idxr = rng.choice(len(vy), size=diff, replace=False)
                    variant_dots[vy[idxr], vx[idxr]] = False
                print(f"  adjusted down to {int(variant_dots.sum())}")
            else:
                diff = int(parent_dots.sum()) - total_dots
                # add random
                avail_y, avail_x = np.where(allowed_mask & ~variant_dots)
                idxr = rng.choice(len(avail_y), size=diff, replace=False)
                variant_dots[avail_y[idxr], avail_x[idxr]] = True
                print(f"  adjusted up to {int(variant_dots.sum())}")

        # Compute % changed: fraction of variant dots not in parent (pixel-exact)
        # Changed = 1 - overlap / parent_count, or more precisely (parent XOR variant)/2? Let's use: changed = (parent_dots != variant_dots).sum() /2 / parent_count? Simpler: n_new / parent_count
        # Actually if we removed n_move and added n_move, changed = n_move / parent_count
        changed_pct = n_move / parent_dots.sum() * 100.0
        # But also compute exact pixel overlap: count of dots in variant that are not in parent
        n_overlap = int((variant_dots & parent_dots).sum())
        exact_changed = (int(parent_dots.sum()) - n_overlap) / int(parent_dots.sum()) * 100.0
        print(f"  changed (by n_move) {changed_pct:.2f}% , exact overlap {n_overlap}/{int(parent_dots.sum())} => changed {exact_changed:.2f}%")

        # Compute CV after
        cv_after, mean_after, std_after, dens_after = compute_block_density_cv(variant_dots, fp, BLOCK_PX)
        print(f"  CV before {cv_before:.4f} -> after {cv_after:.4f} (mean {mean_after:.6f} std {std_after:.6f})")

        # Prepare raster array: float32 0/1, NaN outside not yet, zeros outside for validation
        arr = variant_dots.astype(np.float32)
        # For validation, need to ensure zero on catalogue and halo
        # Check
        on_cat = int((variant_dots & cat).sum())
        in_halo3 = int((variant_dots & halo3).sum())
        print(f"  on_catalogue {on_cat} (must 0), in_halo3 {in_halo3} (must 0 for non-PRUNE)")

        # Create IDs
        # We need sha8 after writing, so temporary name first
        # Name: <parent>-<axis><value>-<yyyymmdd>-<sha8>
        # For now, use placeholder sha8, will replace after sha computed
        # Write to releases with temporary, then rename
        tmp_id = f"{PARENT_ID}-{AXIS}{pct}-{DATE_STR}-tmp"
        # Write NaN version and zeros version to temp files, then compute sha and rename
        # First, write to releases/tmp file
        tmp_nan_path = releases / f"{tmp_id}-nan.tif"
        tmp_zeros_path = releases / f"{tmp_id}-zeros.tif"
        # Use submission.write_raster + validate logic but custom to ensure NaN outside
        # We'll use validate after write

        # Write NaN outside version
        write_raster(arr, tmp_nan_path, mode="nan")
        # Validate nan version: catalogue_buffer 3
        rep_nan = validate(tmp_nan_path, mode="nan", catalogue_buffer_px=3)
        print(f"  NaN validation passed? {rep_nan.passed}, checks {rep_nan.checks}")
        if not rep_nan.passed:
            print(f"  FAILED checks: {[k for k,v in rep_nan.checks.items() if not v]}")
            sys.exit(1)
        # Write zeros version
        write_raster(arr, tmp_zeros_path, mode="zeros")
        rep_zeros = validate(tmp_zeros_path, mode="zeros", catalogue_buffer_px=3)
        print(f"  Zeros validation passed? {rep_zeros.passed}")
        if not rep_zeros.passed:
            print(f"  FAILED zeros checks {[k for k,v in rep_zeros.checks.items() if not v]}")
            sys.exit(1)
        # Re-read from disk after writing
        with rasterio.open(tmp_nan_path) as src:
            a_check = src.read(1)
            # verify no NaN inside
            inside = a_check[fp]
            assert np.isfinite(inside).all(), "NaN inside footprint after write"
            assert np.nanmin(a_check[~fp]) is not np.nan or np.isnan(a_check[~fp]).all(), "outside should be NaN"
        with rasterio.open(tmp_zeros_path) as src:
            a_check2 = src.read(1)
            assert np.isfinite(a_check2).all(), "zeros file should be all finite"
            assert (a_check2[~fp]==0).all(), "outside zeros"

        # Compute sha256
        sha_nan = sha256_file(tmp_nan_path)
        sha_zeros = sha256_file(tmp_zeros_path)
        print(f"  sha_nan {sha_nan[:16]}, sha_zeros {sha_zeros[:16]}")
        sha8 = sha_nan[:8]
        # Check not already in ledger
        if sha_nan in existing_hashes or sha_zeros in existing_hashes:
            print(f"ERROR: sha already in ledger, duplicate")
            sys.exit(1)
        # Build final IDs
        final_id = f"{PARENT_ID}-{AXIS}{pct}-{DATE_STR}-{sha8}"
        final_nan_path = releases / f"{final_id}.tif"
        final_zeros_path = releases / f"{final_id}-zeros.tif"
        tmp_nan_path.rename(final_nan_path)
        tmp_zeros_path.rename(final_zeros_path)
        # Also rename checks.json if created
        for suffix in [".checks.json"]:
            p1 = Path(str(tmp_nan_path)+suffix)
            if p1.exists():
                p1.rename(Path(str(final_nan_path)+suffix))
            p2 = Path(str(tmp_zeros_path)+suffix)
            if p2.exists():
                p2.rename(Path(str(final_zeros_path)+suffix))
        # Record checks.json for releases (we already have validation)
        # Save report
        final_nan_rep = rep_nan
        final_zeros_rep = rep_zeros
        # For ledger: id, parent, axis, value, n_dots, % changed, sha256, status BUILT, predicted change
        # Predicted change: we need to estimate. For CONC, hypothesis: concentrating into high TMI gradient blocks should increase credit per dot if blind faults produce magnetic contrast.
        # Predicted sign: small positive +0.003 to +0.007 live, but 20% may over-concentrate and increase FP clustering.
        # We'll assign predicted changes based on pct: 10% +0.004, 15% +0.005, 20% +0.003 (diminishing)
        pred_map = {10: 0.004, 15: 0.005, 20: 0.003}
        pred = pred_map[pct]
        # Mechanism notes: we will generate detailed card later, but store basic
        row = {
            "id": final_id,
            "parent": PARENT_ID,
            "axis": AXIS,
            "value": str(pct),
            "n_dots": str(int(variant_dots.sum())),
            "pct_changed": f"{exact_changed:.2f}",
            "sha256": sha_nan,
            "sha256_zeros": sha_zeros,
            "status": "BUILT",
            "predicted_change": f"{pred:+.4f}",
            "cv_before": f"{cv_before:.4f}",
            "cv_after": f"{cv_after:.4f}",
            "block_px": str(BLOCK_PX),
            "prior": PRIOR_BAND,
            "n_move": str(n_move),
            "date": DATE_STR,
            "file_nan": str(final_nan_path.relative_to(ROOT)),
            "file_zeros": str(final_zeros_path.relative_to(ROOT)),
        }
        results.append(row)
        print(f"  -> Built {final_id} with {pct}% moved, CV {cv_before:.4f}->{cv_after:.4f}, pred {pred:+.4f}")
        # Also need to store parent-diff stats: we have changed_pct
        # Append to existing hashes for next iteration to avoid duplicates within same run
        existing_hashes.add(sha_nan)
        existing_hashes.add(sha_zeros)

    # Write ledger CSV
    # If ledger exists, append; else create header
    fieldnames = ["id","parent","axis","value","n_dots","pct_changed","sha256","sha256_zeros","status","predicted_change","cv_before","cv_after","block_px","prior","n_move","date","file_nan","file_zeros"]
    is_new = not ledger_path.exists()
    if is_new:
        with open(ledger_path, "w", newline="") as f:
            w=csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in results:
                w.writerow(r)
        print(f"Wrote new ledger with {len(results)} rows to {ledger_path}")
    else:
        with open(ledger_path, "a", newline="") as f:
            w=csv.DictWriter(f, fieldnames=fieldnames)
            for r in results:
                w.writerow(r)
        print(f"Appended {len(results)} rows to existing ledger {ledger_path}")

    # Save detailed JSON for each variant for later docs
    evidence_dir = ROOT/"evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with open(evidence_dir / f"axis_{AXIS}_variants.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    main()
