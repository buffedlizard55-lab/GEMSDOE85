"""Multi-Repository Registry Audit, Full Uniqueness Gates, and High-Scoring Diagnostics."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from gems57.uniqueness import (
    OVERLAP_LIMIT,
    RHO_LIMIT,
    compare_array_to_registry,
    compare_to_registry,
    two_phase_summary,
)
try:
    from gems57.uniqueness import DENSE_HALO_FRACTION, binding_duplicate_decision
except ImportError:
    DENSE_HALO_FRACTION = 0.70

    def binding_duplicate_decision(rows, *, rho_limit: float = RHO_LIMIT, overlap_limit: float = OVERLAP_LIMIT) -> dict:
        checked = [r for r in rows if "error" not in r]
        disc = [r for r in checked if float(r.get("halo_coverage", 0.0)) < DENSE_HALO_FRACTION]
        space = [r for r in checked if r not in disc]
        fwd = [r for r in disc if r.get("forward_overlap") is not None]
        rho_key = "spearman_full_footprint" if any("spearman_full_footprint" in r for r in disc) else "spearman"
        rho = [r for r in disc if r.get(rho_key) is not None]
        worst_fwd = max(fwd, key=lambda r: r["forward_overlap"]) if fwd else None
        worst_rho = max(rho, key=lambda r: abs(r[rho_key])) if rho else None
        return dict(
            evidence_class="REGISTRY-MEASUREMENT",
            binding_rule="like-for-like",
            discriminating_priors=len(disc),
            space_filling_priors=len(space),
            space_filling_files=[r.get("file") or r.get("submission") for r in space],
            worst_forward_overlap=float(worst_fwd["forward_overlap"]) if worst_fwd else None,
            worst_forward_overlap_file=(worst_fwd.get("file") or worst_fwd.get("submission")) if worst_fwd else None,
            worst_abs_spearman=abs(float(worst_rho[rho_key])) if worst_rho else None,
            worst_abs_spearman_file=(worst_rho.get("file") or worst_rho.get("submission")) if worst_rho else None,
            overlap_limit=overlap_limit,
            rho_limit=rho_limit,
            duplicate=bool(
                (worst_fwd and worst_fwd["forward_overlap"] > overlap_limit)
                or (worst_rho and abs(float(worst_rho[rho_key])) > rho_limit)
            ),
        )
from gems57.validate import validate

from .paths import EVIDENCE_DIR, ROOT, resolve_raw_dir


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_all_reference_rasters(raw_dir: Path, work_dir: Path) -> dict[str, Path]:
    """Collect EVERY unique full-grid (3730x3292) scored & sibling GeoTIFF across raw_dir and /tmp/ref/*."""
    found: dict[str, Path] = {}
    seen_sha: set[str] = set()

    def _add_if_valid_grid(key: str, path: Path) -> None:
        try:
            with rasterio.open(path) as ds:
                if ds.shape != (3730, 3292) or ds.count != 1:
                    return
            digest = sha256_file(path)
            if digest in seen_sha:
                return
            seen_sha.add(digest)
            found[key] = path
        except Exception:
            pass

    scored_dir = raw_dir / "scored"
    if scored_dir.exists():
        for p in sorted(scored_dir.glob("*.tif")):
            _add_if_valid_grid(f"scored::{p.stem}", p)

    ref_root = Path("/tmp/ref")
    extract_dir = work_dir / "ref_extracted_tifs"
    extract_dir.mkdir(parents=True, exist_ok=True)
    if ref_root.exists():
        for repo_dir in sorted(ref_root.iterdir()):
            dl = repo_dir / "docs" / "downloads"
            if not dl.exists():
                continue
            for tp in sorted(dl.glob("*.tif")):
                _add_if_valid_grid(f"repo::{repo_dir.name}::{tp.stem}", tp)
            for zp in sorted(dl.glob("*.zip")):
                try:
                    with zipfile.ZipFile(zp) as zf:
                        for m in zf.namelist():
                            if not m.endswith(".tif"):
                                continue
                            stem = Path(m).stem
                            key = f"repo::{repo_dir.name}::{stem}"
                            if key in found:
                                continue
                            target = extract_dir / f"{repo_dir.name}__{Path(m).name}"
                            if not target.exists():
                                with zf.open(m) as src, target.open("wb") as out:
                                    while True:
                                        buf = src.read(1 << 20)
                                        if not buf:
                                            break
                                        out.write(buf)
                            _add_if_valid_grid(key, target)
                except Exception:
                    pass
    return found


def collect_historical_sha256_registry(ref_rasters: dict[str, Path]) -> dict[str, str]:
    """Gather all SHA-256 digests from prior rasters and multi-repo audit registries."""
    known_hashes: dict[str, str] = {}
    for label, p in ref_rasters.items():
        if p.exists():
            known_hashes[sha256_file(p)] = label

    ref_root = Path("/tmp/ref")
    if ref_root.exists():
        for jf in ref_root.glob("*/evidence/*.json"):
            try:
                txt = jf.read_text(errors="ignore")
                data = json.loads(txt)
                _harvest_hashes(data, known_hashes, jf.parent.parent.name)
            except Exception:
                pass
    return known_hashes


def _harvest_hashes(obj: Any, store: dict[str, str], tag: str) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v):
                store.setdefault(v, f"{tag}:{k}")
            else:
                _harvest_hashes(v, store, tag)
    elif isinstance(obj, list):
        for item in obj:
            _harvest_hashes(item, store, tag)


def compute_spatial_quality_diagnostics(
    sub_2d: np.ndarray,
    footprint: np.ndarray,
    existing_faults_2d: np.ndarray,
    lid_valid_2d: np.ndarray,
    elev_slope_2d: np.ndarray,
) -> dict[str, Any]:
    """Compute structural safety diagnostics protecting against known live-crash modes."""
    d_cat = distance_transform_edt(~existing_faults_2d)
    dots = footprint & np.isfinite(sub_2d) & (sub_2d >= 0.5)
    n_dots = int(dots.sum())
    fp_n = int(footprint.sum())
    lid_n = int(lid_valid_2d.sum())
    gap_mask = footprint & (~lid_valid_2d)
    gap_n = int(gap_mask.sum())

    if n_dots == 0:
        return {"n_dots": 0, "valid": False}

    dead_dots = int((dots & (d_cat <= 2.0)).sum())
    collar_2_6 = float((dots & (d_cat > 2.0) & (d_cat <= 6.0)).sum()) / n_dots
    mid_6_12 = float((dots & (d_cat > 6.0) & (d_cat <= 12.0)).sum()) / n_dots
    detached_gt12 = float((dots & (d_cat > 12.0)).sum()) / n_dots
    steep_frac = float((dots & (elev_slope_2d > 15.0)).sum()) / n_dots
    in_lid_frac = float((dots & lid_valid_2d).sum()) / n_dots

    lid_density = (float((dots & lid_valid_2d).sum()) / max(lid_n, 1)) * 1000.0
    gap_density = (float((dots & gap_mask).sum()) / max(gap_n, 1)) * 1000.0
    seam_density_ratio = gap_density / max(lid_density, 1e-9)

    return {
        "n_dots": n_dots,
        "footprint_pixels": fp_n,
        "dead_zone_dots_le_2px": dead_dots,
        "collar_frac_2_to_6px": round(collar_2_6, 5),
        "mid_field_frac_6_to_12px": round(mid_6_12, 5),
        "detached_discovery_frac_gt_12px": round(detached_gt12, 5),
        "mountain_steep_slope_frac_gt_15deg": round(steep_frac, 5),
        "in_1m_lidar_fraction": round(in_lid_frac, 5),
        "lidar_dots_per_1k_px": round(lid_density, 4),
        "gap_dots_per_1k_px": round(gap_density, 4),
        "gap_to_lidar_seam_density_ratio": round(seam_density_ratio, 4),
    }


def run_full_automated_gates(
    submission_path: Path,
    surface_2d: np.ndarray,
    raw_dir: Path,
    work_dir: Path,
    canary_report: dict[str, Any],
    holdout_summary: dict[str, Any],
) -> dict[str, Any]:
    """Run all 7 automated pre-submission & uniqueness gates without human intervention."""
    template_path = raw_dir / "sample_submission.tif"
    with rasterio.open(template_path) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(raw_dir / "existing_faults.tif") as ds:
        cat_2d = (ds.read(1) > 0) & footprint
    fmt_result = validate(submission_path, footprint, cat_2d)
    with rasterio.open(raw_dir / "external/lidar_scarp_features_u8.tif") as ds:
        lid_valid_2d = (ds.read(1) > 0) & footprint
    with rasterio.open(raw_dir / "training_features.tif") as ds:
        elev_slope_2d = ds.read(19).astype(np.float32)
        elev_slope_2d[(elev_slope_2d < -1e20) | ~np.isfinite(elev_slope_2d)] = 0.0
    with rasterio.open(submission_path) as ds:
        sub_2d = ds.read(1).astype(np.float32)

    in_vals = sub_2d[footprint]
    out_vals = sub_2d[~footprint]
    sub_sha = sha256_file(submission_path)

    ref_rasters = discover_all_reference_rasters(raw_dir, work_dir)
    hist_hashes = collect_historical_sha256_registry(ref_rasters)

    registry_records = [
        {"repo": label.split("::")[1] if "::" in label else "scored", "submission": label, "file": str(p)}
        for label, p in sorted(ref_rasters.items())
    ]
    sub_reg = compare_to_registry(submission_path, registry_records, footprint)
    sub_two_phase = two_phase_summary(sub_reg["rows"], int(footprint.sum()), expected_rasters=len(registry_records))

    surf_clean = np.where(footprint, np.clip(np.nan_to_num(surface_2d, nan=0.0), 0.0, 1.0), 0.0).astype(np.float32)
    surf_reg = compare_array_to_registry(surf_clean, registry_records, footprint)
    surf_two_phase = two_phase_summary(surf_reg["rows"], int(footprint.sum()), expected_rasters=len(registry_records))

    # Populate exact 3-px halo coverage (`surf_reg["rows"]` already computed exact halo coverage on `footprint`
    # since `surf_clean > 0` on 100% of `footprint` -> `my_dots_within_3px_of_theirs == halo_coverage(support, footprint)`!!)!
    halo_by_sub = {
        r["submission"]: float(r.get("my_dots_within_3px_of_theirs", 0.0))
        for r in surf_reg["rows"]
        if "error" not in r
    }
    enriched_rows = []
    for r in sub_reg["rows"]:
        if "error" in r:
            enriched_rows.append(r)
            continue
        hc = halo_by_sub.get(r["submission"], 1.0)
        enriched_rows.append({
            **r,
            "halo_coverage": hc,
            "forward_overlap": float(r["my_dots_within_3px_of_theirs"]),
        })
    binding_decision = binding_duplicate_decision(enriched_rows)

    spatial_diag = compute_spatial_quality_diagnostics(sub_2d, footprint, cat_2d, lid_valid_2d, elev_slope_2d)

    # Extract BOTH forward & reverse 3-px dot overlaps across ALL discriminating priors (`halo_coverage < 0.70`)!
    strict_bidirectional_rows = []
    worst_bidir_overlap = 0.0
    worst_bidir_name = None
    for r in enriched_rows:
        if "error" in r or float(r["halo_coverage"]) >= DENSE_HALO_FRACTION:
            continue
        rn = int(r.get("their_dots", 0))
        if rn == 0:
            continue
        ours_near_ref = float(r["my_dots_within_3px_of_theirs"])
        ref_near_ours = float(r["their_dots_within_3px_of_mine"])
        sym_max = max(ours_near_ref, ref_near_ours)
        name = str(r.get("submission"))
        strict_bidirectional_rows.append({
            "reference": name,
            "ref_dots": rn,
            "halo_coverage": round(float(r["halo_coverage"]), 5),
            "our_dots_within_3px_of_ref": round(ours_near_ref, 5),
            "ref_dots_within_3px_of_ours": round(ref_near_ours, 5),
            "bidirectional_max_3px_overlap": round(sym_max, 5),
        })
        if sym_max > worst_bidir_overlap:
            worst_bidir_overlap = sym_max
            worst_bidir_name = name
    strict_bidirectional_rows.sort(key=lambda r: r["bidirectional_max_3px_overlap"], reverse=True)

    surf_worst_rho = float(surf_two_phase["literal_reading"]["worst_spearman_full_footprint"] or 0.0)
    surf_worst_who = surf_two_phase["literal_reading"]["worst_spearman_submission"]
    dot_worst_fwd = float(binding_decision["worst_forward_overlap"] or 0.0)
    dot_worst_who = binding_decision["worst_forward_overlap_file"]
    dot_rho_worst = float(sub_two_phase["literal_reading"]["worst_spearman_full_footprint"] or 0.0)

    sha_collision = sub_sha in hist_hashes
    failed_checks = [k for k, v in fmt_result["checks"].items() if not v]
    gates = {
        "G1_geotiff_grid_crs_dtype": {
            "passed": bool(fmt_result["all_checks_passed"]),
            "detail": f"EPSG:32611, 3730x3292, float32, outside_fp_zero={fmt_result['checks']['outside_footprint_zero']}, failed_checks={failed_checks}",
        },
        "G2_strict_0_1_range_zero_nan": {
            "passed": bool(
                np.all(np.isfinite(in_vals))
                and float(in_vals.min()) >= 0.0
                and float(in_vals.max()) <= 1.0
                and int(np.sum(np.isfinite(out_vals) & ((out_vals < 0.0) | (out_vals > 1.0)))) == 0
            ),
            "detail": f"in_min={float(in_vals.min()):.6f}, in_max={float(in_vals.max()):.6f}, in_nan={int(np.isnan(in_vals).sum())}",
        },
        "G3_single_feature_leakage_canary": {
            "passed": bool(canary_report["passed"]) and float(canary_report["max_observed_symmetric_auc"]) <= 0.90,
            "detail": f"checked={canary_report['features_checked']} features, max_sym_AUC={canary_report['max_observed_symmetric_auc']:.5f} <= 0.90",
        },
        "G4_surface_rank_uniqueness_le_0p90": {
            "passed": abs(surf_worst_rho) <= 0.90 and abs(dot_rho_worst) <= 0.90,
            "detail": f"surface max |Spearman rho|={surf_worst_rho:.5f} vs {surf_worst_who}; dot-raster max |rho|={dot_rho_worst:.5f} (<= 0.90)",
        },
        "G5_dot_3px_uniqueness_le_0p70_and_sha256": {
            "passed": (not sha_collision) and (not binding_decision["duplicate"]) and dot_worst_fwd <= 0.70,
            "detail": (
                f"binding_discriminating_3px_max={dot_worst_fwd:.5f} vs {dot_worst_who} (<= 0.70 across {binding_decision['discriminating_priors']} priors; "
                f"{binding_decision['space_filling_priors']} space-filling halos >=70% documented per IR-H85-01); "
                f"bidir_max={worst_bidir_overlap:.5f} vs {worst_bidir_name}; unique_sha256={not sha_collision} against {len(hist_hashes)} hashes"
            ),
        },
        "G6_anti_collar_seam_and_slope_hygiene": {
            "passed": (
                spatial_diag["dead_zone_dots_le_2px"] == 0
                and spatial_diag["detached_discovery_frac_gt_12px"] >= 0.50
                and 0.55 <= spatial_diag["gap_to_lidar_seam_density_ratio"] <= 1.35
                and spatial_diag["mountain_steep_slope_frac_gt_15deg"] <= 0.20
            ),
            "detail": (
                f"dead_dots={spatial_diag['dead_zone_dots_le_2px']}, "
                f"detached_gt12px={spatial_diag['detached_discovery_frac_gt_12px']:.4f}, "
                f"seam_ratio={spatial_diag['gap_to_lidar_seam_density_ratio']:.4f}, "
                f"steep_gt15deg={spatial_diag['mountain_steep_slope_frac_gt_15deg']:.4f}"
            ),
        },
        "G7_holdout_dti_beats_h33_and_positive": {
            "passed": float(holdout_summary["mean_holdout_dti"]) > float(holdout_summary["h33_reference_holdout_dti"]),
            "detail": (
                f"E85_winner_HOLDOUT_DTI={holdout_summary['mean_holdout_dti']:.6f} > "
                f"H33_HOLDOUT_DTI={holdout_summary['h33_reference_holdout_dti']:.6f} "
                f"(+{float(holdout_summary['mean_holdout_dti']) - float(holdout_summary['h33_reference_holdout_dti']):.6f})"
            ),
        },
    }
    all_passed = all(g["passed"] for g in gates.values())
    verdict = "READY_TO_SUBMIT_PROMOTE" if all_passed else "STOP_REVIEW_FAILED_GATE"

    out = {
        "schema_version": "gems85-automated-gates-v1",
        "evidence_class": "AUTOMATED-SUBMISSION-AUDIT",
        "verdict": verdict,
        "ready_for_competition_upload": all_passed,
        "submission_file": submission_path.name,
        "submission_bytes": submission_path.stat().st_size,
        "submission_sha256": sub_sha,
        "historical_hashes_checked": len(hist_hashes),
        "reference_rasters_audited": len(ref_rasters),
        "gates": gates,
        "spatial_diagnostics": spatial_diag,
        "validator_raw": fmt_result,
        "surface_uniqueness_two_phase": surf_two_phase,
        "dot_uniqueness_two_phase": sub_two_phase,
        "binding_duplicate_decision": binding_decision,
        "top_10_bidirectional_dot_overlaps": strict_bidirectional_rows[:10],
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "automated_validation_and_uniqueness.json").write_text(json.dumps(out, indent=2) + "\n")
    return out
