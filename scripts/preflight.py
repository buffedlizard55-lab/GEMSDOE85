#!/usr/bin/env python3
"""Fail-closed preflight for this repository's current release state.

This command does not run a geological experiment, generate a raster, validate a
candidate, choose a submission slot, or contact DrivenData. A blocked preflight
returns exit code 2 so automation cannot mistake the absence of a candidate for
release approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "scripts"))

from restore_data import sha256_file  # noqa: E402

REQUIRED_CORE_IDS = {"training_features", "labels", "existing_faults", "sample_submission"}
EVALUATOR_VERSION = "gems57-pooled-hide-v2"


def _read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def verify_template(root: Path = ROOT) -> list[str]:
    """Return pinned shared files that are absent or do not match their SHA-256."""
    pin = _read_json(root / "registry/template_pin.json", {}) or {}
    mismatches = []
    for name, expected in pin.get("files", {}).items():
        path = root / "vendor/gems57" / name
        if not path.is_file() or sha256_file(path) != expected:
            mismatches.append(name)
    if not pin.get("files"):
        mismatches.append("<empty template pin>")
    return mismatches


def _core_integrity(root: Path, manifest: dict) -> tuple[bool, bool, list[dict]]:
    entries = [e for e in manifest.get("files", []) if e.get("group", "core") == "core"]
    identities_ok = {e.get("id") for e in entries} == REQUIRED_CORE_IDS and len(entries) == len(REQUIRED_CORE_IDS)
    rows = []
    for entry in entries:
        path = root / "data" / str(entry.get("dest", ""))
        present = path.is_file()
        size_ok = present and path.stat().st_size == entry.get("bytes")
        hash_ok = size_ok and sha256_file(path) == entry.get("sha256")
        rows.append({
            "id": entry.get("id"),
            "path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
            "present": present,
            "size_matches_manifest": bool(size_ok),
            "sha256_matches_manifest": bool(hash_ok),
            "ok": bool(hash_ok),
        })
    all_ok = identities_ok and len(rows) == len(REQUIRED_CORE_IDS) and all(r["ok"] for r in rows)
    return identities_ok, all_ok, rows


def _cache_integrity(root: Path, manifest: dict) -> tuple[bool, list[dict]]:
    cache_rows = manifest.get("cache_files", [])
    checks = []
    for row in cache_rows:
        path = root / row.get("path", "")
        present = path.is_file()
        matches = present and sha256_file(path) == row.get("sha256")
        checks.append({"path": row.get("path"), "present": present,
                       "sha256_matches_manifest": bool(matches), "ok": bool(matches)})
    available = manifest.get("status") == "available" and bool(cache_rows) and all(r["ok"] for r in checks)
    return available, checks


def _recorded_saturation(root: Path, template_intact: bool) -> dict:
    """Load the binding prior certificate; re-check only if its witness is local.

    Absence of the witness does not turn a recorded universal-overlap certificate
    into clearance. It is reported as not revalidated in this checkout and remains
    a blocking condition, as required by AGENTS.md.
    """
    path = root / "evidence/saturation_certificate.json"
    cert = _read_json(path, {}) or {}
    if not cert:
        return {"status": "missing certificate", "universal_overlap_blocker": None,
                "evidence_class": "REGISTRY-MEASUREMENT"}

    witness_name = cert.get("witness_file")
    manifest = _read_json(root / "registry/learning_manifest.json", {}) or {}
    witness_id = Path(str(witness_name)).name if witness_name else None
    manifest_entry = next((entry for entry in manifest.get("files", [])
                           if entry.get("id") == witness_id), None)
    manifest_path = (root / "data/learning" / str(manifest_entry.get("dest"))) if manifest_entry else None
    manifest_relative = manifest_path.relative_to(root).as_posix() if manifest_path else None
    witness_path_matches_manifest = bool(witness_name and manifest_relative == Path(witness_name).as_posix())
    result = {
        "evidence_class": cert.get("evidence_class", "REGISTRY-MEASUREMENT"),
        "source_file": str(path.relative_to(root)),
        "witness_file": witness_name,
        "manifest_restore_path": manifest_relative,
        "witness_path_matches_manifest": witness_path_matches_manifest,
        "witness_path_mismatch": bool(witness_name and manifest_entry and not witness_path_matches_manifest),
        "witness_sha256": cert.get("witness_sha256"),
        "positive_pixels": cert.get("positive_pixels"),
        "allowed_pixels": cert.get("allowed_pixels"),
        "uncovered_allowed_pixels": cert.get("uncovered_allowed_pixels"),
        "covered_allowed_fraction": cert.get("covered_allowed_fraction"),
        "overlap_limit": cert.get("overlap_limit"),
        "support_definition": cert.get("support_definition"),
        "universal_overlap_blocker": cert.get("universal_overlap_blocker"),
        "status": "recorded certificate; witness not locally revalidated",
        "local_revalidation": False,
    }

    witness = root / witness_name if witness_name else None
    if result["witness_path_mismatch"]:
        result["status"] = "recorded certificate; witness path differs from learning-manifest restore destination"
    elif witness and witness.is_file() and template_intact:
        if manifest_entry and sha256_file(witness) == manifest_entry.get("sha256") == cert.get("witness_sha256"):
            try:
                from gems57.grid import load_grid
                from gems57.uniqueness import saturation_certificate
                grid = load_grid(root / "data")
                measured = saturation_certificate(
                    witness, grid.footprint, grid.catalogue,
                    expected_grid=(grid.shape, grid.crs, grid.transform))
                result["local_revalidation"] = True
                result["status"] = "locally revalidated against the pinned shared implementation"
                result["local_measurement"] = measured
                if bool(measured.get("universal_overlap_blocker")) != bool(cert.get("universal_overlap_blocker")):
                    result["certificate_mismatch"] = True
            except (OSError, ValueError, KeyError, ImportError) as exc:
                result["local_revalidation_error"] = str(exc)
    return result


def review(root: Path = ROOT) -> dict:
    """Return a deterministic, evidence-labelled negative preflight run card."""
    root = Path(root)
    blockers: list[str] = []

    template_mismatches = verify_template(root)
    template_intact = not template_mismatches
    if not template_intact:
        blockers.append("Pinned shared template files are missing or modified: " + ", ".join(template_mismatches))

    lane = _read_json(root / "registry/lane.json", {}) or {}
    lane_assigned = lane.get("status") == "assigned" and bool(str(lane.get("method_paragraph") or "").strip())
    if not lane_assigned:
        blockers.append("No explicit single-method paragraph is assigned; research proposals are not lane assignments.")

    data_manifest = _read_json(root / "registry/data_manifest.json", {}) or {}
    manifest_ok, core_ok, core_rows = _core_integrity(root, data_manifest)
    if not manifest_ok:
        blockers.append("The core data manifest does not identify exactly the four required competition inputs.")
    if not core_ok:
        missing = [r["id"] for r in core_rows if not r["ok"]]
        blockers.append("Core inputs are unavailable or fail pinned size/hash checks: " + ", ".join(missing or ["manifest mismatch"]) + ".")

    cache_manifest = _read_json(root / "registry/cache_manifest.json", {}) or {}
    cache_ok, cache_rows = _cache_integrity(root, cache_manifest)
    if not cache_ok:
        blockers.append("The pinned transformed feature-stack cache is unavailable; raw competition rasters are not a substitute.")

    saturation = _recorded_saturation(root, template_intact)
    saturation_blocked = saturation.get("universal_overlap_blocker") is True
    if saturation.get("witness_path_mismatch"):
        blockers.append("The saturation certificate witness path differs from the pinned learning-manifest restore path; preserve the certificate and resolve provenance before attempting revalidation.")
    if saturation_blocked:
        blockers.append("The binding literal registry-saturation certificate blocks every nonempty candidate in the allowed domain; the 70% overlap rule is not waived.")
    elif saturation.get("universal_overlap_blocker") is None:
        blockers.append("No valid saturation certificate is available; uniqueness cannot be cleared.")

    # No surface or raster exists to compare. Do not infer uniqueness from historical artifacts.
    blockers.append("Pre-placement surface correlation and final-dot overlap were not run because no candidate was authorized or generated.")
    blockers.append("No comparable same-evaluator current-best holdout receipt is available for a paired promotion test.")
    blockers.append("Organizer submission receipts and account-specific weekly quota are unavailable; no submission slot is selected.")

    return {
        "schema_version": 2,
        "run_id": "gems85-preflight-20261023",
        "evidence_class": "FAIL-CLOSED-PREFLIGHT; not a geological experiment and not a competition score",
        "hypothesis": "No candidate was selected or run because the explicit method paragraph is absent and registry/lane.json remains unassigned. Proposal rank 1 for future consideration only: paired basin-interface flexure.",
        "mechanism": "Proposal only, not tested: directional, detrended profiles require an ordered signed depth/curvature pair with a consistent gravity response across a basin interface; a buried basement step beneath fill could persist where no continuous scarp is exposed.",
        "named_non_fault_process_that_could_mimic_it": "Proposal only, not tested: lateral sedimentary facies change or erosional basement relief could mimic paired basin-interface flexure.",
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": EVALUATOR_VERSION,
            "value": None,
            "ci95": None,
            "n_withheld_positives": None,
            "status": "NOT RUN — prerequisites and strict uniqueness gate block candidate evaluation",
        },
        "leakage_canary": {
            "status": "NOT RUN — no feature surface evaluated",
            "feature_auc": None,
            "threshold": 0.90,
        },
        "correlation_overlap_vs_registry": {
            "status": "NOT RUN — no candidate surface or final dots",
            "max_abs_spearman_surface": None,
            "max_dot_overlap_within_3px": None,
            "thresholds": {"abs_spearman_max": 0.90, "dot_overlap_max": 0.70},
            "phase_surface_before_placement": "not run",
            "phase_final_dots": "not run",
            "unique": False,
            "saturation_certificate": saturation,
        },
        "raster_sha256": None,
        "validator_output": {
            "status": "NOT RUN — no candidate raster exists",
            "no_nan_inside_footprint": None,
            "values_in_0_1": None,
            "crs_shape_transform_match": None,
        },
        "submission_name": None,
        "submission_note": "BLOCKED; no candidate generated. Do not submit historical rasters.",
        "verdict": "negative",
        "verdict_reason": "Negative preflight only; not a geological negative. No unique candidate is currently cleared for download or submission.",
        "budget": {"experiments_run": 0, "experiment_limit": 3, "hours_used": 0.0, "hours_limit": 2.0, "stop_rule": "Stop after 3 experiments or 2 hours, whichever occurs first.", "submission_slots_used": 0},
        "gates": {
            "lane_assigned": lane_assigned,
            "template_unmodified": template_intact,
            "template_mismatches": template_mismatches,
            "core_manifest_valid": manifest_ok,
            "core_inputs_available": core_ok,
            "core_integrity": core_rows,
            "cached_feature_stack_available": cache_ok,
            "cache_integrity": cache_rows,
            "literal_saturation_blocker": saturation_blocked,
            "uniqueness_cleared": False,
            "paired_holdout_incumbent_available": False,
            "holdout_gate_passed": False,
            "format_gate_passed": False,
            "experiment_authorized": False,
        },
        "blockers": blockers,
        "safe_to_download": False,
        "safe_to_submit": False,
        "promoted": False,
        "submission_slots_used": 0,
        "experiment_status": "NOT RUN",
    }


def experiment_gate(root: Path = ROOT) -> int:
    """Fail closed for historical CLI experiment runners until all prerequisites clear.

    This guard does not select a lane or judge a hypothesis. It ensures that invoking
    a legacy run_* script cannot run research under an unassigned lane, missing cache,
    saturated literal overlap policy, or absent paired holdout incumbent.
    """
    card = review(root)
    gates = card["gates"]
    failed = []
    if not gates["lane_assigned"]:
        failed.append("method lane is unassigned")
    if not gates["template_unmodified"]:
        failed.append("pinned shared template is not intact")
    if not gates["core_inputs_available"]:
        failed.append("required core inputs are unavailable or unverified")
    if not gates["cached_feature_stack_available"]:
        failed.append("transformed feature cache is unavailable")
    saturation = card["correlation_overlap_vs_registry"].get("saturation_certificate", {})
    if gates["literal_saturation_blocker"] or saturation.get("universal_overlap_blocker") is not False:
        failed.append("binding literal overlap-saturation blocker is unresolved or cannot be cleared")
    if not gates["paired_holdout_incumbent_available"]:
        failed.append("no same-evaluator paired holdout incumbent is available")
    budget = card["budget"]
    if budget["experiments_run"] >= budget["experiment_limit"] or budget["hours_used"] >= budget["hours_limit"]:
        failed.append("the three-experiment/two-hour research budget is exhausted")
    if failed:
        print("BLOCKED: no experiment ran; resolve protocol prerequisites first:")
        for item in failed:
            print(f"- {item}")
        print("No lane selected, cache rebuilt, TIFF emitted, or submission slot used.")
        return 2
    return 0


def blocked_submission_registry(card: dict) -> dict:
    return {
        "schema_version": 2,
        "status": "blocked",
        "hypothesis_id": None,
        "primary": None,
        "alternates": [],
        "note": card["submission_note"],
        "safe_to_download": False,
        "safe_to_submit": False,
        "experiments_run": card["budget"]["experiments_run"],
        "submission_slots_used": card["budget"]["submission_slots_used"],
        "blockers": card["blockers"],
        "historical_artifacts": "submissions/quarantine/ (research only; not cleared for submission)",
    }


def write_preflight_state(root: Path = ROOT) -> dict:
    """Write the canonical negative run card and blocked submission registry."""
    root = Path(root)
    card = review(root)
    for relative, payload in (
        ("evidence/run_card.json", card),
        ("registry/submission.json", blocked_submission_registry(card)),
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return card


def main() -> int:
    card = write_preflight_state(ROOT)
    print(json.dumps(card, indent=2, allow_nan=False))
    return 2 if card["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
