#!/usr/bin/env python3
"""Separate selector step after an H85 lane-drift stop.

This is not another geological experiment.  It takes the already evaluated H85
surface, enforces a per-registry 3-pixel overlap cap, and writes a **negative,
DO-NOT-SUBMIT** control if the original top surface was duplicated.  The
selector is intentionally kept separate from the holdout experiment and from
any live-slot decision.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, maximum_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems85.grid import read_catalogue, read_template  # noqa: E402
from gems85.holdout import score_holdout, withhold_segments  # noqa: E402
from gems85.emission import emit_peaks  # noqa: E402
from submission_writer import write_submission  # noqa: E402
from validate_submission import validate  # noqa: E402
from uniqueness_audit import _read_aligned, audit as uniqueness_audit, iter_rasters  # noqa: E402


def _candidate_peaks(surface: np.ndarray, eligible: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    score = np.where(eligible & np.isfinite(surface), surface, -np.inf).astype(np.float32)
    peak = np.isfinite(score) & (score == maximum_filter(score, size=7, mode="constant", cval=-np.inf))
    rows, cols = np.nonzero(peak)
    values = score[rows, cols]
    order = np.lexsort((cols, rows, -values))
    return rows[order], cols[order], values[order]


def _registry_hit_matrix(rows: np.ndarray, cols: np.ndarray, roots: list[Path], template: dict,
                         max_positive_fraction: float = 0.15) -> tuple[np.ndarray, list[str]]:
    hits: list[np.ndarray] = []
    names: list[str] = []
    for path, _digest in iter_rasters(roots):
        arr = _read_aligned(path, template)
        if arr is None:
            continue
        positive = (arr > 0.5) & template["footprint"]
        fraction = float(positive.sum() / max(int(template["footprint"].sum()), 1))
        # Treat a continuous probability/surface raster as a surface, not as
        # millions of registry dots. It is still checked by rank correlation.
        if fraction > max_positive_fraction:
            continue
        dist = distance_transform_edt(~positive)
        hits.append((dist[rows, cols] <= 3.0).astype(np.uint8))
        names.append(str(path))
    if not hits:
        return np.zeros((rows.size, 0), dtype=np.uint8), names
    return np.stack(hits, axis=1), names


def select_mask(surface: np.ndarray, eligible: np.ndarray, roots: list[Path], template: dict,
                budget: int = 60_000, cap_fraction: float = 0.70) -> tuple[np.ndarray, dict]:
    rows, cols, values = _candidate_peaks(surface, eligible)
    hit_matrix, names = _registry_hit_matrix(rows, cols, roots, template)
    cap = int(np.floor(float(cap_fraction) * int(budget)))
    counts = np.zeros(hit_matrix.shape[1], dtype=np.int32)
    keep: list[int] = []
    # Fixed final-budget caps make the selector deterministic and prevent a
    # late registry raster from crossing the lane threshold.
    for index in range(rows.size):
        hits = hit_matrix[index]
        if np.all(counts + hits <= cap):
            keep.append(index)
            counts += hits
            if len(keep) >= int(budget):
                break
    mask = np.zeros(surface.shape, dtype=bool)
    if keep:
        keep_arr = np.asarray(keep, dtype=np.int64)
        mask[rows[keep_arr], cols[keep_arr]] = True
    return mask, {
        "candidate_peak_count": int(rows.size),
        "registry_dot_raster_count": int(len(names)),
        "selected_count": int(mask.sum()),
        "budget": int(budget),
        "cap_fraction": float(cap_fraction),
        "cap_count": cap,
        "max_registry_hits": int(counts.max()) if counts.size else 0,
        "max_registry_overlap_fraction": float(counts.max() / max(int(mask.sum()), 1)) if counts.size else 0.0,
        "registry_paths": names,
    }


def _write_scratch(path: Path, values: np.ndarray, template: dict) -> None:
    profile = template["profile"].copy()
    profile.update(driver="GTiff", dtype="float32", count=1, nodata=None, compress="deflate")
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(values.astype(np.float32), 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", type=Path, default=ROOT / ".cache/h85-audit/surface.tif")
    parser.add_argument("--template", type=Path, default=ROOT / "data/raw/sample_submission.tif")
    parser.add_argument("--catalogue", type=Path, default=ROOT / "data/raw/existing_faults.tif")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "docs/downloads")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "evidence")
    parser.add_argument("--registry-root", action="append", type=Path, required=True)
    parser.add_argument("--stem", default="gems85-h85-scalescarp-persistence-20261022T220819Z-unique-selector-DO-NOT-SUBMIT")
    parser.add_argument("--budget", type=int, default=60_000)
    parser.add_argument("--selection-cap-fraction", type=float, default=0.40,
                        help=("absolute per-registry hit cap as a fraction of the requested "
                              "budget; final audit still enforces 0.70 of selected dots"))
    args = parser.parse_args(argv)
    if not 0.0 < args.selection_cap_fraction <= 0.70:
        parser.error("--selection-cap-fraction must be > 0 and <= 0.70")

    template = read_template(args.template)
    footprint = template["footprint"]
    catalogue = read_catalogue(args.catalogue, footprint)
    with rasterio.open(args.surface) as src:
        surface = src.read(1).astype(np.float32)
    eligible = footprint & ~catalogue
    naive = emit_peaks(surface, eligible, budget=args.budget)
    selected, selector = select_mask(surface, eligible, args.registry_root, template, args.budget,
                                     cap_fraction=args.selection_cap_fraction)

    output = args.out_dir / f"{args.stem}-zeros.tif"
    zip_path = args.out_dir / f"{args.stem}-zeros.zip"
    validator = write_submission(selected, args.template, args.catalogue, output, zip_path)
    strict_validator = validate(output, args.template, args.catalogue)

    # Evaluate the selected negative control on the identical holdout. It is
    # reported, not promoted: uniqueness was obtained only after the original
    # H85 surface was stopped for drift.
    split = withhold_segments(catalogue, footprint)
    selected_holdout = score_holdout(selected, split, footprint, bootstrap=True)
    selector_scratch = ROOT / ".cache" / "h85-selector"
    _write_scratch(selector_scratch / "naive.tif", naive.astype(np.float32), template)
    _write_scratch(selector_scratch / "selected.tif", selected.astype(np.float32), template)
    uniqueness = uniqueness_audit(surface, naive, selected, args.template, args.registry_root)

    run_card = {
        "label": "H85-SELECTOR-RUN-CARD",
        "hypothesis": "The preregistered H85 scale-space detrended-slope surface was evaluated first; its top dot emission crossed the registry overlap gate, so this separate selector produces a unique negative control rather than silently promoting it.",
        "mechanism": ("Selector-only per-registry dot cap; cap is an absolute hit limit "
                      "relative to the requested budget, not a geological method or score tune; "
                      "no live submission."),
        "named_non_fault_process_that_could_mimic_it": "The underlying H85 surface can be mimicked by paleoshorelines, terraces, roads, mines, and lithologic contacts.",
        "holdout": selected_holdout,
        "original_h85_surface_holdout": {"label": "HOLDOUT-DTI", "status": "see evidence/run_card.json", "note": "The preregistered four-scale arm scored 0.1078732951 before the selector."},
        "selector": selector,
        "selector_report_note": ("The internal cap is floor(0.40 × 60,000) = 24,000 hits per registry. "
                                 "Because the selector emitted 25,111 dots, the final audit denominator "
                                 "is smaller than the requested budget; the measured final overlap still "
                                 "fails the 0.70 gate."),
        "uniqueness": uniqueness,
        "raster_sha256": validator["sha256"],
        "validator_output": strict_validator,
        "submission_name": args.stem,
        "submission_note": (f"DO NOT SUBMIT: selector control; cap={args.selection_cap_fraction:.2f} of "
                            f"{args.budget:,}; {int(selected.sum()):,} dots; final overlap="
                            f"{uniqueness['max_final_dot_overlap_fraction']:.4f} > 0.70; HOLDOUT-DTI "
                            f"{selected_holdout['score']:.4f} [{selected_holdout['ci95'][0]:.4f},"
                            f"{selected_holdout['ci95'][1]:.4f}]")[:140],
        "live_organizer_score": {"label": "ORGANIZER-CONFIRMED", "status": "not submitted; no claim"},
        "verdict": "negative",
        "download_status": "format-valid but explicitly DO-NOT-SUBMIT; selector is not a promotion decision",
    }
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    (args.evidence_dir / "selector_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    print(json.dumps(run_card, indent=2))
    return 0 if strict_validator["passed"] and uniqueness.get("final_gate_passed", False) else 2


if __name__ == "__main__":
    raise SystemExit(main())
