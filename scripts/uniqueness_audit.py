#!/usr/bin/env python3
"""Audit lane drift against local registry GeoTIFFs.

The registry is an input directory, not a copied submission.  Files with the
same bytes are deduplicated.  This tool reports both surface Spearman
correlation and the fraction of proposed/final dots within 3 pixels of each
registry's dots.  It exits non-zero if the parallel-run thresholds are
crossed: correlation > 0.90 or dot overlap > 0.70.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems85.grid import read_template, sha256_file  # noqa: E402


def iter_rasters(roots: list[Path], skip_names: tuple[str, ...] = ("sample_submission", "labels", "existing_faults")):
    seen: set[str] = set()
    for root in roots:
        root = Path(root)
        if root.is_file() and root.suffix.lower() in (".tif", ".tiff"):
            candidates = [root]
        else:
            candidates = sorted(root.rglob("*.tif")) + sorted(root.rglob("*.tiff"))
        for path in candidates:
            if any(token in path.name.lower() for token in skip_names):
                continue
            try:
                digest = sha256_file(path)
            except OSError:
                continue
            if digest in seen:
                continue
            seen.add(digest)
            yield path, digest


def _read_aligned(path: Path, template: dict) -> np.ndarray | None:
    try:
        with rasterio.open(path) as src:
            if src.shape != tuple(template["footprint"].shape):
                return None
            if src.crs != template["profile"]["crs"] or src.transform != template["profile"]["transform"]:
                return None
            arr = src.read(1).astype(np.float32)
    except Exception:
        return None
    arr[~np.isfinite(arr)] = 0.0
    return arr


def _sample_indices(footprint: np.ndarray, n: int = 60_000) -> np.ndarray:
    flat = np.flatnonzero(footprint.ravel())
    if flat.size <= n:
        return flat
    # Deterministic evenly spaced sample, independent of raster values.
    return flat[np.linspace(0, flat.size - 1, n, dtype=np.int64)]


def _dot_overlap(dots: np.ndarray, registry: np.ndarray, footprint: np.ndarray) -> tuple[int, int, float]:
    reg_dots = (registry > 0) & footprint
    n_dots = int(dots.sum())
    if n_dots == 0 or not reg_dots.any():
        return 0, n_dots, 0.0
    dist = distance_transform_edt(~reg_dots)
    hit = dots & (dist <= 3.0)
    count = int(hit.sum())
    return count, n_dots, float(count / n_dots)


def audit(surface: np.ndarray, proposed: np.ndarray, final: np.ndarray, template_path: Path,
          registry_roots: list[Path], sample_n: int = 60_000) -> dict:
    template = read_template(template_path)
    footprint = template["footprint"]
    idx = _sample_indices(footprint, sample_n)
    s_flat = np.asarray(surface, dtype=np.float32).ravel()
    rows = []
    max_corr = -1.0
    max_prop = -1.0
    max_final = -1.0
    for path, digest in iter_rasters(registry_roots):
        raster = _read_aligned(path, template)
        if raster is None:
            continue
        values = raster.ravel()[idx]
        surface_values = s_flat[idx]
        if np.all(values == values[0]) or np.all(surface_values == surface_values[0]):
            correlation = 0.0
        else:
            correlation = float(spearmanr(surface_values, values).statistic)
            if not np.isfinite(correlation):
                correlation = 0.0
        positive_fraction = float(((raster > 0.5) & footprint).sum() / max(int(footprint.sum()), 1))
        # Continuous probability/surface rasters are not dot registries. They
        # remain in the rank-correlation check, but treating every positive
        # float cell as a prior dot would make the overlap statistic meaningless.
        dot_registry = positive_fraction <= 0.15
        if dot_registry:
            prop_hit, prop_n, prop_fraction = _dot_overlap(proposed, raster, footprint)
            final_hit, final_n, final_fraction = _dot_overlap(final, raster, footprint)
            max_prop = max(max_prop, prop_fraction)
            max_final = max(max_final, final_fraction)
        else:
            prop_hit, prop_n, prop_fraction = 0, int(proposed.sum()), None
            final_hit, final_n, final_fraction = 0, int(final.sum()), None
        max_corr = max(max_corr, correlation)
        rows.append({
            "path": str(path),
            "sha256": digest,
            "surface_spearman_r": correlation,
            "registry_positive_fraction": positive_fraction,
            "dot_overlap_evaluated": dot_registry,
            "proposed_dot_hits_within_3px": prop_hit,
            "proposed_dot_count": prop_n,
            "proposed_overlap_fraction": prop_fraction,
            "final_dot_hits_within_3px": final_hit,
            "final_dot_count": final_n,
            "final_overlap_fraction": final_fraction,
        })
    def rank_key(row):
        overlap = row["final_overlap_fraction"] if row["final_overlap_fraction"] is not None else -1.0
        return max(abs(row["surface_spearman_r"]), overlap)
    rows.sort(key=rank_key, reverse=True)
    initial_gate_passed = max_corr <= 0.90 and max_prop <= 0.70
    final_gate_passed = max_corr <= 0.90 and max_final <= 0.70
    return {
        "label": "LANE-UNIQUENESS-AUDIT",
        "thresholds": {"surface_rank_correlation_le": 0.90, "dot_overlap_within_3px_le": 0.70},
        "registry_roots": [str(path) for path in registry_roots],
        "unique_aligned_registry_rasters": len(rows),
        "surface_sample_pixels": int(idx.size),
        "max_surface_spearman_r": max_corr,
        "max_proposed_dot_overlap_fraction": max_prop,
        "max_final_dot_overlap_fraction": max_final,
        "initial_surface_and_proposed_gate_passed": bool(initial_gate_passed),
        "final_gate_passed": bool(final_gate_passed),
        "passed": bool(final_gate_passed),
        "top_matches": rows[:25],
        "note": "Continuous rasters with positive fraction above 0.15 are treated as surfaces for overlap, not dot registries. This local audit cannot establish uniqueness against private organizer files.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", required=True, type=Path)
    parser.add_argument("--proposed", required=True, type=Path)
    parser.add_argument("--final", required=True, type=Path)
    parser.add_argument("--template", type=Path, default=ROOT / "data/raw/sample_submission.tif")
    parser.add_argument("--registry-root", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    def read(path: Path) -> np.ndarray:
        with rasterio.open(path) as src:
            return src.read(1)
    report = audit(read(args.surface), read(args.proposed) > 0.5, read(args.final) > 0.5,
                   args.template, args.registry_root)
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
