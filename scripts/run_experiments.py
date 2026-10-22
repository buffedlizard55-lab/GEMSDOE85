#!/usr/bin/env python3
"""Run the three preregistered H85 experiments and build one format-valid evidence TIF.

The experiment budget is deliberately fixed at three.  The candidate is not
sent to DrivenData by this script; it only writes a local evidence artifact and
receipts for a separate selector step. A registry-overlap failure leaves the
artifact negative and blocked rather than submission-ready.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems85.emission import emit_peaks  # noqa: E402
from gems85.features import METHOD_ID, SIGMAS, build_scale_space  # noqa: E402
from gems85.grid import read_catalogue, read_template  # noqa: E402
from gems85.holdout import leakage_canary, score_holdout, withhold_segments  # noqa: E402
from gems85.metric import EVALUATOR_VERSION  # noqa: E402
from submission_writer import write_submission  # noqa: E402
from validate_submission import validate  # noqa: E402
from uniqueness_audit import audit as uniqueness_audit  # noqa: E402


HYPOTHESIS = (
    "A fault scarp that is expressed as a break in detrended slope should persist as a "
    "high edge response across several 50–300 m Gaussian scales; the maximum scale "
    "envelope should recover catalogue-missing structural traces better than one scale."
)
MECHANISM = (
    "Normal-fault throw and lithologic relief create a narrow slope discontinuity. "
    "Scale persistence favors a coherent scarp over a one-pixel processing artifact."
)
MIMIC = "Pleistocene paleoshoreline benches and fluvial/road-cut risers can create the same slope edge."


def _write_bool_raster(path: Path, mask: np.ndarray, template: dict) -> None:
    profile = template["profile"].copy()
    profile.update(driver="GTiff", dtype="uint8", count=1, nodata=0, compress="deflate")
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(mask.astype(np.uint8), 1)


def _write_float_raster(path: Path, values: np.ndarray, template: dict) -> None:
    profile = template["profile"].copy()
    profile.update(driver="GTiff", dtype="float32", count=1, nodata=0, compress="deflate")
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(values.astype(np.float32), 1)


def _note(score: float, ci: list[float]) -> str:
    text = f"H85 scale-space det_elev_slope persistence; 60000 binary dots; HOLDOUT-DTI {score:.4f} [{ci[0]:.4f},{ci[1]:.4f}]"
    return text[:140]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, default=ROOT / "data/training_features.tif")
    parser.add_argument("--template", type=Path, default=ROOT / "data/raw/sample_submission.tif")
    parser.add_argument("--catalogue", type=Path, default=ROOT / "data/raw/existing_faults.tif")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "docs/downloads")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "evidence")
    parser.add_argument("--registry-root", type=Path, action="append", default=[])
    parser.add_argument("--stem", default="gems85-h85-scalescarp-persistence-20261022T220819Z")
    args = parser.parse_args(argv)

    if not args.features.is_file():
        raise SystemExit(f"feature stack missing: {args.features}; run scripts/restore_feature_stack.sh")
    template = read_template(args.template)
    footprint = template["footprint"]
    catalogue = read_catalogue(args.catalogue, footprint)
    split = withhold_segments(catalogue, footprint)
    stack = build_scale_space(args.features, args.template, SIGMAS)

    # Exactly three preregistered arms.  E3 is the only candidate eligible for
    # the local deliverable; it is not a live-slot selection.
    plans = [
        ("E1-single-scale", (1.0,), 50_000),
        ("E2-two-scale-envelope", (1.0, 2.0), 50_000),
        ("E3-four-scale-persistence-envelope", SIGMAS, 60_000),
    ]
    experiments = []
    for name, sigma_tuple, budget in plans:
        fields = [stack["features"][f"sigma_{sigma:g}_px"] for sigma in sigma_tuple]
        surface = np.maximum.reduce(fields).astype(np.float32)
        pred = emit_peaks(surface, footprint & ~split["visible"], budget=budget)
        result = score_holdout(pred, split, footprint, bootstrap=False)
        experiments.append({
            "experiment": name,
            "sigmas_px": list(sigma_tuple),
            "budget": budget,
            "method_id": METHOD_ID,
            "result": result,
        })

    top = max(experiments, key=lambda row: float(row["result"]["score"]))
    if top["experiment"] != "E3-four-scale-persistence-envelope":
        raise RuntimeError("pre-registered E3 did not win; no submission artifact may be promoted")

    # CI and leakage canary are computed only for the promoted arm.
    top_surface = stack["surface"]
    top_holdout_mask = emit_peaks(top_surface, footprint & ~split["visible"], budget=60_000)
    top_holdout = score_holdout(top_holdout_mask, split, footprint, bootstrap=True)
    canary = leakage_canary(stack["features"], split, footprint)

    # Full-catalogue inference and artifact writing happen only after the top
    # arm has beaten E1 on the same hidden split.
    baseline_score = float(experiments[0]["result"]["score"])
    if float(top_holdout["score"]) <= baseline_score:
        raise RuntimeError("top candidate did not beat the current holdout best; not writing a deliverable")
    final_mask = emit_peaks(top_surface, footprint & ~catalogue, budget=60_000)
    output_path = args.out_dir / f"{args.stem}-zeros.tif"
    zip_path = args.out_dir / f"{args.stem}-zeros.zip"
    validator = write_submission(final_mask, args.template, args.catalogue, output_path, zip_path)
    strict_validator = validate(output_path, args.template, args.catalogue)
    if not strict_validator["passed"]:
        raise RuntimeError("submission writer produced a failed validator receipt")

    # Write scratch rasters under .cache for the independent registry audit.
    scratch = ROOT / ".cache" / "h85-audit"
    surface_path = scratch / "surface.tif"
    proposed_path = scratch / "proposed-peaks.tif"
    final_path = scratch / "final-mask.tif"
    _write_float_raster(surface_path, top_surface, template)
    _write_bool_raster(proposed_path, top_holdout_mask, template)
    _write_bool_raster(final_path, final_mask, template)
    registry_report = uniqueness_audit(top_surface, top_holdout_mask, final_mask, args.template, args.registry_root) if args.registry_root else {
        "label": "LANE-UNIQUENESS-AUDIT", "passed": False,
        "note": "No registry root supplied; uniqueness gate was not run.",
        "unique_aligned_registry_rasters": 0,
    }
    initial_duplicate = bool(args.registry_root and not registry_report.get("initial_surface_and_proposed_gate_passed", False))
    # A duplicate is a hard stop for promotion, not a reason to hide the
    # artifact.  The separate selector step may build a negative, unique
    # control; this experiment receipt remains the scientifically evaluated
    # surface and records the duplicate exactly.

    ci = top_holdout["ci95"] or [float("nan"), float("nan")]
    run_card = {
        "label": "H85-RUN-CARD",
        "hypothesis": HYPOTHESIS,
        "mechanism": MECHANISM,
        "named_non_fault_process_that_could_mimic_it": MIMIC,
        "method_id": METHOD_ID,
        "feature_stack": {
            "path": str(args.features),
            "band": 19,
            "description": stack["description"],
            "sigmas_px": list(SIGMAS),
            "catalogue_used_in_surface": False,
        },
        "experiment_budget": {"max_experiments": 3, "run_count": 3},
        "experiments": experiments,
        "current_holdout_best_before_e3": {"label": "HOLDOUT-DTI", "score": baseline_score},
        "holdout": top_holdout,
        "leakage_canary": canary,
        "uniqueness": registry_report,
        "duplicate_stop": initial_duplicate,
        "raster_sha256": validator["sha256"],
        "validator_output": strict_validator,
        "submission_name": args.stem,
        "submission_note": _note(float(top_holdout["score"]), ci),
        "live_organizer_score": {"label": "ORGANIZER-CONFIRMED", "status": "not submitted; no claim"},
        "verdict": "promote" if canary["passed"] and validator["passed"] and registry_report.get("initial_surface_and_proposed_gate_passed", False) else "negative",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    (args.evidence_dir / "experiments.json").write_text(json.dumps({"experiments": experiments}, indent=2) + "\n")
    (args.evidence_dir / "leakage_canary.json").write_text(json.dumps(canary, indent=2) + "\n")
    (args.evidence_dir / "uniqueness_audit.json").write_text(json.dumps(registry_report, indent=2) + "\n")
    (args.evidence_dir / "submission_validation.json").write_text(json.dumps(strict_validator, indent=2) + "\n")
    (args.evidence_dir / "run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    (ROOT / "docs" / "run-card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    print(json.dumps(run_card, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
