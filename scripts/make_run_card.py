#!/usr/bin/env python3
"""Assemble evidence/run_card.json (PARALLEL-RUN PROTOCOL §5) from the evidence files."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "evidence"

exp = json.loads((E / "holdout_experiments.json").read_text())
fb = json.loads((E / "final_build.json").read_text())
audit = json.loads((E / "final_audit.json").read_text())
uniq = json.loads((E / "uniqueness.json").read_text())
e1 = exp["experiments"]["E1_supervised_hgb"]
ctrl = exp["controls"]["CTRL_d28_0.2600"]
comparable = [r for r in uniq["registry"]
              if r.get("registry_dots", 10**9) <= 50000 and "dot_overlap_within_3px" in r]
worst_comp = max(comparable, key=lambda r: r["dot_overlap_within_3px"])
max_rho = max(abs(r["spearman_rho_surface_vs_raster"]) for r in uniq["registry"]
              if "spearman_rho_surface_vs_raster" in r)
note = (f"H85-A fold-proper HGB maxcov 37654; HOLDOUT-DTI {e1['pooled_dti']:.4f} vs ctrl "
        f"{ctrl['pooled_dti']:.4f}; NEGATIVE-do-not-submit")
assert len(note) <= 140, len(note)
card = {
    "hypothesis": "H85-A: a fold-proper supervised detector (HistGradientBoosting on the 35-channel "
                  "template stack + 20 external channels, no catalogue-derived feature) ranks unmapped "
                  "fault traces well enough that metric-exact max-coverage emission at 37,654 dots beats "
                  "the H19-5 dotted-ridge family on hide-and-recover holdout.",
    "mechanism": "Detector learns the multi-physics appearance of mapped faults per spatial fold; "
                 "lazy-greedy max-coverage emission places binary dots only where expected marginal "
                 "kernel credit is highest, confined to >2px from the catalogue.",
    "named_non_fault_mimic": "Young alluvial/cultural lineaments (roads, canals, field boundaries) "
                             "with fault-like multi-physics line expression.",
    "holdout": {
        "label": "HOLDOUT-DTI",
        "evaluator": exp["evaluator"],
        "candidate_E1": e1["pooled_dti"],
        "candidate_E1_ci95": e1["ci95"],
        "control_d28": ctrl["pooled_dti"],
        "control_d28_ci95": ctrl["ci95"],
        "control_h33_invalid_bar_note": "CTRL_h33 HOLDOUT-DTI 0.0046 is an artifact (pruned vs full catalogue); see IR-85-08.",
        "n_withheld_positives": e1["n_withheld_positives"],
        "experiments": {k: dict(dti=v["pooled_dti"], ci95=v["ci95"])
                        for k, v in exp["experiments"].items()},
        "leakage_canary": "no feature AUC > 0.90 (max single channel 0.600; E1 field AUC 0.673)",
    },
    "organizer_confirmed_reference_scores": {
        "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros": 0.2778,
        "dotted-h19-5-d2-8": 0.2600,
        "leaderboard_high_unattributed": 0.4413,
        "note": "Copied from submission-page receipts in the brief; no hash crosswalk available (IR-85-04). Not local measurements.",
    },
    "correlation_overlap_vs_registry": {
        "max_abs_spearman_surface_vs_any_registry_raster": max_rho,
        "worst_overlap_within_3px_comparable_budgets": worst_comp,
        "strict_reading_drift_rasters": [r["name"] for r in uniq["registry"] if r.get("drift")],
        "verdict": "PASS vs comparable dotted submissions; FAIL under strict any-raster reading (IR-85-07)",
    },
    "raster_sha256": audit["zeros"]["sha256"],
    "validator_output": audit["zeros"],
    "submission_name": fb["zeros_name"],
    "submission_note_max_140_chars": note,
    "submission_note_chars": len(note),
    "verdict": "negative",
    "verdict_reason": "E1 pooled HOLDOUT-DTI 0.0984 [0.079, 0.118] does not beat the valid control "
                      "0.1023 [0.085, 0.122] at any swept budget (20k-55k); uniqueness ambiguous under "
                      "the strict protocol reading. Do not spend a submission slot.",
}
(E / "run_card_h85.json").write_text(json.dumps(card, indent=2))
print(json.dumps(card, indent=2))
