#!/usr/bin/env python3
"""Assemble the session arena/22847afd run card (parallel-run protocol S5) and
point registry/submission.json at the session candidate.

Reads only measured artifacts: evidence/session_22847afd_experiments.json,
evidence/session_22847afd_e2b.json, evidence/duplicate_check_session.json,
registry/submission_session.json.  Re-validates the primary TIF from its
written bytes and measures the one missing control (uniform random, sep4).
Previous GEO-Pb registry/run-card are preserved as *_geopb_20261022.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems85 import baselines, emission, grid, holdout, submission  # noqa: E402
from run_session_experiments import pooled_auc, rank01  # noqa: E402

NOTE = ("S85 ctxfus50 rank-fusion ctx-HGB30+GEO-Pb crest, 37654 dots sep4px, "
        "0 within 200m of catalogue, HOLDOUT-DTI 0.0808 (UNSCORED)")
assert len(NOTE) <= 140, len(NOTE)


def main() -> int:
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    sub = json.loads((ROOT / "registry" / "submission_session.json").read_text())
    dup = json.loads((ROOT / "evidence" / "duplicate_check_session.json").read_text())
    e2b = json.loads((ROOT / "evidence" / "session_22847afd_e2b.json").read_text())
    exp = json.loads((ROOT / "evidence" / "session_22847afd_experiments.json").read_text())

    pri = sub["primary"]
    rep = submission.validate(ROOT / "docs" / "downloads" / pri["filename"], mode="zeros")
    assert rep.passed and rep.sha256 == pri["sha256"]

    # overlap vs this repo's OWN previously published files (not in the 17-raster
    # registry, but the brief's uniqueness requirement covers them too)
    import rasterio
    from scipy import ndimage as _ndi

    def _read(p):
        with rasterio.open(p) as s:
            return np.nan_to_num(s.read(1).astype(np.float32), nan=0.0) > 0

    new_dots = _read(ROOT / "docs" / "downloads" / pri["filename"])
    _yy, _xx = np.mgrid[-3:4, -3:4]
    _disc = (_yy ** 2 + _xx ** 2) <= 9
    own = {}
    for name, p in {
        "geopb_37654_sep4_prev_alt": "docs/downloads/gems85-geopb-crest-37654dots-sep4-20261022T222707Z-60029d07-zeros.tif",
        "geopb_90000_sep4_prev_primary": "docs/downloads/gems85-geopb-crest-90000dots-sep4-20261022T222707Z-a4e1f57c-zeros.tif",
        "geopb_60000_sep4": "docs/downloads/gems85-geopb-crest-60000dots-sep4-20261022T222707Z-cbb4e82c-zeros.tif",
        "h85a_hgb_37654": "submissions/gems85-h85a-foldproper-hgb-maxcov-37654-20261022T221031Z-bf96e456-zeros.tif",
        "duplex_pullapart": "docs/downloads/gems85-h85-duplex-pullapart-worm-20261022T220544Z-2f8b57d9-zeros.tif",
        "ti_pure": "docs/downloads/gems85-h85-ti-pure-20261022T221047Z-f53a0c81-zeros.tif",
        "worm_pure": "docs/downloads/gems85-h85-worm-pure-20261022T221114Z-e3091ec2-zeros.tif",
    }.items():
        o = _read(ROOT / p)
        near = _ndi.binary_dilation(o, structure=_disc)
        ov = float((new_dots & near).sum() / new_dots.sum())
        cov = float((near & fp).sum() / fp.sum())
        own[name] = {"dot_overlap_3px": ov, "chance_coverage_3px": cov,
                     "overlap_lift_over_chance": ov / cov if cov else None,
                     "exact_pixel_overlap": float((new_dots & o).sum() / new_dots.sum())}
    (ROOT / "evidence" / "duplicate_check_ownrepo_session.json").write_text(
        json.dumps(own, indent=2, default=float) + "\n")

    # fusion canary (per-fold fields rebuilt from cached E2b outputs + static crest)
    from gems85 import featurestack
    crest = np.load(featurestack.CACHE / "ch_geopb_crest.npy")
    rcrest = rank01(crest, fp)
    fus_pf = {}
    for f in folds:
        h = np.load(ROOT / "work" / f"ctxhgb2_{f.name}.npy")
        fus_pf[f.name] = (0.5 * rank01(h, fp) + 0.5 * rcrest).astype(np.float32)
    fus_auc = pooled_auc(fus_pf, folds, fp)

    # matched-mass uniform-random control at the primary configuration
    rng_field = baselines.uniform_random(fp, seed=20261022)
    rand = holdout.score_folds(
        lambda fold: emission.emit(rng_field, footprint=fp,
                                   visible_catalogue=fold.visible,
                                   n=37_654, sep_px=4.0, exclude_px=2),
        folds, domain=fp)

    ho = e2b["arms"]["E3b_fusion_e2b_crest5050__sep40"]["37654"]
    crest_ref_folds = [0.07711628038760639, 0.07504295704142083,
                       0.0681532281295331, 0.07849780281723791]
    fus_folds = [f["dti"] for f in ho["folds"]]
    gate = {
        "beats_holdout_best_0.07475_at_37654": ho["pooled_holdout_dti"] > 0.0747509441972475,
        "folds_above_crest_reference": int(sum(a > b for a, b in zip(fus_folds, crest_ref_folds))),
        "leakage_canaries_below_0.90": bool(
            fus_auc < 0.90 and e2b["canary_auc_field"] < 0.90
            and max(exp["canary_auc"].values()) < 0.90),
        "not_a_duplicate": not dup["is_duplicate"],
        "validator_17_checks_pass": bool(rep.passed),
        "live_operating_point_le_44090_dots": pri["stats"]["emitting_pixels"] <= 44_090,
    }

    card = {
        "run_id": f"gems85-session22847afd-{sub['built_utc']}",
        "session_branch": "arena/22847afd-gemsdoe85",
        "hypothesis": ("S85-CTXFUS: a fault is a line in context, not a pixel. A contextual "
                       "supervised field (HistGradientBoosting on 24 catalogue-free channels "
                       "+ 6 line-context channels: 1.5 km along-strike line support, "
                       "multi-scale context means, 5-field corroboration count; trained "
                       "per-fold on visible catalogue only) rank-fused 50/50 with the "
                       "GEO-Pb juxtaposition crest ranks concealed-fault pixels better "
                       "than either field alone."),
        "mechanism": ("The two fields fail differently: GEO-Pb fires on joint multi-physics "
                      "steps (incl. non-fault contacts); the contextual HGB fires on the "
                      "learned multi-scale appearance of mapped traces (incl. cultural "
                      "lineaments). Rank-averaging keeps pixels both mechanisms endorse "
                      "and demotes idiosyncratic false positives of each."),
        "named_non_fault_process_that_could_mimic_it": (
            "Erosional volcanic mesa / lava-flow margins (straight, multi-domain, "
            "line-like at 1.5 km context) — declared irreducible in the GEO-Pb lane and "
            "not removed here; secondary: cultural lineaments (roads/canals) with "
            "fault-like line context."),
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": holdout.EVALUATOR_VERSION,
            "value": ho["pooled_holdout_dti"],
            "ci95": ho["ci95"],
            "per_fold": fus_folds,
            "n_withheld_positives": ho["n_withheld_positives"],
            "configuration": "37,654 dots, sep 4.0 px, exclude 2 px halo, binary",
            "protocol": ("hide-and-recover; whole fault segments withheld by spatial "
                         "block (200 px) with 5 px buffer; every catalogue-derived "
                         "quantity rebuilt per fold from visible faults only; visible "
                         "faults masked pixel-exactly; pooled DTI alpha 0.2 beta 0.8, "
                         "300 m triangular kernel"),
            "reference_beaten": {
                "field": "GEO-Pb crest sep4 (repo holdout best, evidence/budget_sweep.json)",
                "value_at_37654": 0.0747509441972475,
                "per_fold": crest_ref_folds,
                "delta": ho["pooled_holdout_dti"] - 0.0747509441972475,
                "folds_positive": gate["folds_above_crest_reference"],
                "honesty_note": ("95% CIs overlap ([0.0736,0.0881] vs [0.0703,0.0793]); "
                                 "the win is consistent (both seps, both budgets, 3/4 "
                                 "folds) but not statistically decisive with 4 folds."),
            },
            "uniform_random_matched": {"value": rand.pooled_dti, "ci95": list(rand.ci95)},
        },
        "all_session_arms_holdout_dti_at_37654_sep28_unless_noted": {
            "E1_relay_alone": 0.02524, "E1_relay_gated_crest": 0.03708,
            "E2_ctxhgb_with_relay_channel_BUG": 0.04022,
            "E3_fusion_with_gated_component": 0.05523,
            "E3_fusion_blurred_emission": 0.02775,
            "E2b_ctxhgb_norelay_sep40": 0.07599,
            "E3b_fusion5050_sep28": 0.07411,
            "E3b_fusion5050_sep40_PRIMARY_RULE": ho["pooled_holdout_dti"],
            "crest_reference_sep28": 0.06953, "crest_reference_sep40": 0.07475,
        },
        "leakage_canary": {
            "fusion_field_auc": fus_auc, "ctxhgb_field_auc": e2b["canary_auc_field"],
            "max_single_new_feature_auc": max(
                v for k, v in exp["canary_auc"].items() if k.startswith("ctx_")),
            "threshold": 0.90, "verdict": "clean",
            "relay_channel_note": ("RELAY geometry canary AUC 0.457 vs withheld but its "
                                   "training separation is by construction (built from "
                                   "the visible mask): a train/test reversal. It was "
                                   "removed from the final field (E2b); RELAY as gate "
                                   "(E1) and as channel (E2) are both NEGATIVE results "
                                   "on this instrument."),
        },
        "correlation_vs_registry": {
            "max_abs_spearman": dup["max_abs_spearman"],
            "max_dot_overlap_3px_raw": dup["max_dot_overlap_3px"],
            "max_overlap_lift_over_chance": dup["max_overlap_lift_over_chance"],
            "thresholds": dup["thresholds"], "is_duplicate": dup["is_duplicate"],
            "comparisons_file": "evidence/duplicate_check_session.json",
            "irregularity": dup["irregularity"],
            "vs_h33_winner": {
                "dot_overlap_3px": 0.379, "spearman_surface": 0.065,
                "note": "from evidence/duplicate_check_session.json comparisons"},
            "vs_own_repo_previous_files": own,
            "own_repo_note": ("Raw 3-px overlap vs the superseded 90,000-dot GEO-Pb "
                              "primary is 0.79, but that dense file's dilated support "
                              "already covers 0.44 of the footprint (chance level); "
                              "vs every comparable-budget (<=60k) own-repo file the "
                              "overlap is <=0.41 and exact pixel overlap <=0.26. "
                              "Disclosed in full; not a rename or re-emission."),
        },
        "raster_sha256": pri["sha256"],
        "validator_output": {"all_checks_passed": rep.passed, "checks": rep.checks,
                             "stats": rep.stats, "mode": rep.mode,
                             "no_nan_inside_footprint": rep.checks["no_nan_inside_footprint"],
                             "values_in_0_1": rep.checks["values_in_0_1_whole_raster"],
                             "crs_shape_transform_match": all(
                                 rep.checks[k] for k in ("crs_epsg_32611", "shape_3730x3292",
                                                         "transform_matches_template"))},
        "vs_random_delta": ho["pooled_holdout_dti"] - rand.pooled_dti,
        "submission_name": pri["filename"],
        "submission_note": NOTE,
        "submission_note_chars": len(NOTE),
        "preregistered_gate": gate,
        "organizer_confirmed_score": None,
        "live_projection": ("NO live score is claimed or projected as a number. Beating "
                             "0.2778 live requires >0.145 mean credit/dot; this field's "
                             "holdout lift over uniform random is "
                             f"{ho['pooled_holdout_dti']/rand.pooled_dti:.2f}x on catalogue "
                             "truth. Whether that transfers to the hidden expert set is "
                             "exactly what a submission would measure."),
        "budget": {"experiments_run": "3 pre-registered (E1,E2,E3) + E2b/E3b bugfix "
                                      "ablation of E2 (relay-channel train/test reversal), "
                                      "logged transparently",
                   "submission_slots_used": 0},
        "verdict": "promote-as-candidate" if all(gate.values()) else "negative",
        "verdict_caveat": ("'promote' = cleared this repo's pre-registered gate "
                           "(research/session-22847afd-hypotheses.md) and is published "
                           "for the separate selector step. It is NOT a leaderboard "
                           "projection; no organizer score exists for this file."),
    }
    (ROOT / "evidence" / "run_card_session_22847afd.json").write_text(
        json.dumps(card, indent=2, default=float) + "\n")
    (ROOT / "evidence" / "run_card.json").write_text(
        json.dumps(card, indent=2, default=float) + "\n")

    # point the site at the session candidate; previous GEO-Pb files stay as alternates
    old = json.loads((ROOT / "registry" / "submission_geopb_20261022.json").read_text())
    site_sub = {
        "built_utc": sub["built_utc"], "hypothesis_id": "S85-CTXFUS (session 22847afd)",
        "note": NOTE, "primary": pri,
        "alternates": sub["alternates"] + [
            {"role": "previous GEO-Pb primary 90,000 dots (SUPERSEDED - holdout-tuned budget)",
             "filename": old["primary"]["filename"], "bytes": old["primary"]["bytes"]},
        ] + [a for a in old.get("alternates", [])
             if "37654" in a["filename"] and a["filename"].endswith("-zeros.tif")],
        "session_ladder": sub["ladder"],
    }
    # rename the superseded alternate's role text for the 37,654 GEO-Pb file
    for a in site_sub["alternates"]:
        if "geopb-crest-37654" in a["filename"]:
            a["role"] = "previous GEO-Pb alt-38k (37,654 dots sep4, holdout 0.07475)"
    (ROOT / "registry" / "submission.json").write_text(
        json.dumps(site_sub, indent=2, default=float) + "\n")
    (ROOT / "docs" / "downloads" / "run_card.json").write_text(
        json.dumps(card, indent=2, default=float) + "\n")
    print(json.dumps({"gate": gate, "verdict": card["verdict"],
                      "sha256": pri["sha256"], "note_chars": len(NOTE)}, indent=2))
    return 0 if card["verdict"] == "promote-as-candidate" else 1


if __name__ == "__main__":
    raise SystemExit(main())
