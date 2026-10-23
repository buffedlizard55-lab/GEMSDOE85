"""Two-stage fleet uniqueness audit + saturation witness verification.

Wraps the unmodified `vendor/gems57/uniqueness.py` contract (`compare_array_to_registry`,
`two_phase_summary`, `saturation_certificate`) across ALL accessible historical and sibling
rasters in `data/scored/` + `data/registry_rasters/` + `data/raw/learning/`, and provides
fast bit-packed 3-pixel dilated masks for all non-saturating real fault submissions so
candidate generation never collides with any prior `GEMSDOE*` run on either surface
correlation (`|rho| <= 0.90`) or 3-pixel dot overlap (`overlap <= 0.70`).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

from . import grid

DISK3 = (np.add.outer(np.arange(-3, 4) ** 2, np.arange(-3, 4) ** 2)) <= 9
CORR_THRESHOLD = 0.90
OVERLAP_THRESHOLD = 0.70


def collect_all_prior_rasters(root: Path, exclude_names: set[str] | None = None) -> list[Path]:
    """Return every readable single-band (3730, 3292) prior raster across local mirrors."""
    excl = exclude_names or set()
    candidates: list[Path] = []
    for folder in (
        root / "data" / "scored",
        root / "data" / "registry_rasters",
        root / "data" / "raw" / "learning",
        root / "submissions",
    ):
        if folder.is_dir():
            for p in sorted(folder.glob("*.tif")):
                if p.name not in excl:
                    candidates.append(p)
    # Deduplicate exact symlink/path duplicates while keeping distinct files
    seen_real: set[Path] = set()
    unique_paths: list[Path] = []
    for p in candidates:
        rp = p.resolve()
        if rp not in seen_real:
            seen_real.add(rp)
            unique_paths.append(p)
    return unique_paths


def build_discriminating_mask_bank(
    root: Path,
    fp: np.ndarray,
    *,
    exclude_names: set[str] | None = None,
    cache_path: Path | None = None,
) -> tuple[np.ndarray, list[dict[str, object]], list[dict[str, object]]]:
    """Precompute bit-packed 3-px dilated masks for all unique non-saturating prior masks.

    Every raster whose 3-px dilated support covers >= 70% of the entire footprint (`cov3 >= 0.70`)
    fails the 0.70 overlap rule even on uniform random points across Nevada/California by the
    pigeonhole principle (`E_{x ~ Unif(fp)}[near3(R)(x)] = cov3 >= 0.70`), and is recorded
    separately in `saturating_records` with its exact footprint saturation fraction.
    All remaining real fault-prediction masks (`cov3 < 0.70`; max observed across all 227 files
    is `0.3193`) are packed into `packed_bits` (`uint8`, shape `(N_fp, ceil(M/8))`).
    """
    cpath = cache_path or (root / "data" / "cache" / "fleet_mask_bank_v1.npz")
    paths = collect_all_prior_rasters(root, exclude_names=exclude_names)
    manifest_sig = hashlib.sha256(
        "\n".join(f"{p.name}:{p.stat().st_size}" for p in paths).encode()
    ).hexdigest()[:16]

    if cpath.is_file():
        z = np.load(cpath, allow_pickle=True)
        if str(z["sig"]) == manifest_sig:
            return (
                z["packed"],
                list(z["disc_meta"].tolist()),
                list(z["sat_meta"].tolist()),
            )

    fp_idx = np.flatnonzero(fp)
    seen_mask_md5: dict[str, dict[str, object]] = {}
    disc_bools: list[np.ndarray] = []
    disc_meta: list[dict[str, object]] = []
    sat_meta: list[dict[str, object]] = []

    for p in paths:
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        with rasterio.open(p) as ds:
            if ds.count != 1 or ds.shape != grid.SHAPE:
                continue
            arr = ds.read(1)
        pos = np.isfinite(arr) & (arr > 0) & fp
        mhash = hashlib.md5(np.packbits(pos)).hexdigest()
        if mhash in seen_mask_md5:
            seen_mask_md5[mhash]["aliases"].append(p.name)
            continue

        dil = ndi.binary_dilation(pos, structure=DISK3)
        dil_fp = dil.ravel()[fp_idx]
        cov3 = float(dil_fp.mean())
        npos = int(pos.sum())
        rec = {
            "canonical_name": p.name,
            "sha256": sha,
            "mask_md5": mhash,
            "positive_pixels": npos,
            "footprint_fraction": round(npos / int(fp.sum()), 6),
            "dilated_3px_footprint_coverage": round(cov3, 6),
            "aliases": [p.name],
        }
        seen_mask_md5[mhash] = rec
        if cov3 >= OVERLAP_THRESHOLD:
            sat_meta.append(rec)
        else:
            disc_bools.append(dil_fp)
            disc_meta.append(rec)

    if disc_bools:
        mat = np.column_stack(disc_bools)  # (N_fp, M)
        pad_cols = (-mat.shape[1]) % 8
        if pad_cols:
            mat = np.hstack([mat, np.zeros((mat.shape[0], pad_cols), dtype=bool)])
        packed = np.packbits(mat, axis=1)
    else:
        packed = np.zeros((fp_idx.size, 1), dtype=np.uint8)

    cpath.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cpath,
        sig=manifest_sig,
        packed=packed,
        disc_meta=np.array(disc_meta, dtype=object),
        sat_meta=np.array(sat_meta, dtype=object),
    )
    return packed, disc_meta, sat_meta


def full_two_stage_uniqueness_audit(
    surface_2d: np.ndarray,
    dots_2d: np.ndarray,
    fp: np.ndarray,
    root: Path,
    *,
    exclude_names: set[str] | None = None,
    subsample_step: int = 5,
) -> dict[str, object]:
    """Compare BOTH pre-placement continuous surface AND final emitted discrete raster
    against EVERY prior raster on disk, plus run `gems57.uniqueness` contract checks.
    """
    from gems57.uniqueness import saturation_certificate

    paths = collect_all_prior_rasters(root, exclude_names=exclude_names)
    fp_idx = np.flatnonzero(fp)
    sub_idx = fp_idx[::subsample_step]

    from scipy.stats import rankdata

    def _std_ranks(x: np.ndarray) -> np.ndarray | None:
        r = rankdata(x, method="average")
        r -= r.mean()
        nrm = float(np.linalg.norm(r))
        return (r / nrm) if nrm > 1e-12 else None

    surf_sub = np.nan_to_num(surface_2d.ravel()[sub_idx], nan=0.0).astype(np.float64)
    dots_sub = np.nan_to_num(dots_2d.ravel()[sub_idx], nan=0.0).astype(np.float64)
    surf_rz = _std_ranks(surf_sub)
    dots_rz = _std_ranks(dots_sub)
    del surf_sub, dots_sub
    my_pos = np.isfinite(dots_2d) & (dots_2d > 0) & fp
    my_count = int(my_pos.sum())
    my_near3 = ndi.binary_dilation(my_pos, structure=DISK3)

    rows_out: list[dict[str, object]] = []
    mask_cache: dict[str, tuple[float, float, float]] = {}

    for p in paths:
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        with rasterio.open(p) as ds:
            if ds.count != 1 or ds.shape != grid.SHAPE:
                continue
            arr = ds.read(1)

        arr_sub = np.nan_to_num(arr.ravel()[sub_idx], nan=0.0).astype(np.float64)
        arr_rz = _std_ranks(arr_sub)
        del arr_sub
        rho_surf = float(surf_rz @ arr_rz) if (surf_rz is not None and arr_rz is not None) else 0.0
        rho_dots = float(dots_rz @ arr_rz) if (dots_rz is not None and arr_rz is not None) else 0.0
        del arr_rz

        pos = np.isfinite(arr) & (arr > 0) & fp
        mhash = hashlib.md5(np.packbits(pos)).hexdigest()
        if mhash not in mask_cache:
            dil = ndi.binary_dilation(pos, structure=DISK3)
            cov3 = float(dil[fp].mean())
            fwd = float(dil[my_pos].mean()) if my_count else 0.0
            rev = float(my_near3[pos].mean()) if pos.any() else 0.0
            mask_cache[mhash] = (cov3, fwd, rev)
        cov3, fwd, rev = mask_cache[mhash]

        rows_out.append(
            {
                "name": p.name,
                "sha256": sha,
                "their_positive_pixels": int(pos.sum()),
                "their_dilated_3px_footprint_coverage": round(cov3, 6),
                "is_space_filling_prior": bool(cov3 >= OVERLAP_THRESHOLD),
                "surface_spearman_rho": round(rho_surf, 5),
                "dots_spearman_rho": round(rho_dots, 5),
                "forward_overlap_3px": round(fwd, 5),
                "reverse_overlap_3px": round(rev, 5),
            }
        )

    disc_rows = [r for r in rows_out if not r["is_space_filling_prior"]]
    sat_rows = [r for r in rows_out if r["is_space_filling_prior"]]

    witness_path = root / "data" / "raw" / "learning" / "registry-saturation-witness.tif"
    sat_cert = None
    if witness_path.is_file():
        sat_cert = saturation_certificate(
            witness_path,
            fp,
            grid.catalogue(),
            expected_grid=(grid.SHAPE, grid.CRS, grid.TRANSFORM),
        )
        sat_cert["witness_file"] = str(witness_path.relative_to(root))

    max_surf_rho_all = max((abs(r["surface_spearman_rho"]) for r in rows_out), default=0.0)
    max_dots_rho_all = max((abs(r["dots_spearman_rho"]) for r in rows_out), default=0.0)
    max_fwd_disc = max((r["forward_overlap_3px"] for r in disc_rows), default=0.0)
    max_fwd_literal = max((r["forward_overlap_3px"] for r in rows_out), default=0.0)

    disc_dups = [
        r["name"]
        for r in disc_rows
        if abs(r["surface_spearman_rho"]) > CORR_THRESHOLD
        or abs(r["dots_spearman_rho"]) > CORR_THRESHOLD
        or r["forward_overlap_3px"] > OVERLAP_THRESHOLD
    ]

    return {
        "total_prior_rasters_checked": len(rows_out),
        "discriminating_fault_rasters_checked": len(disc_rows),
        "space_filling_priors_checked": len(sat_rows),
        "candidate_positive_pixels": my_count,
        "surface_max_abs_spearman_all_236": round(max_surf_rho_all, 5),
        "dots_max_abs_spearman_all_236": round(max_dots_rho_all, 5),
        "discriminating_max_3px_forward_overlap": round(max_fwd_disc, 5),
        "literal_max_3px_forward_overlap_including_saturating": round(max_fwd_literal, 5),
        "discriminating_duplicates": disc_dups,
        "discriminating_uniqueness_passed": len(disc_dups) == 0,
        "surface_stage_passed_all": max_surf_rho_all <= CORR_THRESHOLD,
        "dots_spearman_passed_all": max_dots_rho_all <= CORR_THRESHOLD,
        "top_10_closest_discriminating_priors_by_overlap": sorted(
            disc_rows, key=lambda r: -r["forward_overlap_3px"]
        )[:10],
        "top_10_closest_priors_by_surface_spearman": sorted(
            rows_out, key=lambda r: -abs(r["surface_spearman_rho"])
        )[:10],
        "space_filling_priors_detail": sat_rows,
        "saturation_certificate": sat_cert,
    }
