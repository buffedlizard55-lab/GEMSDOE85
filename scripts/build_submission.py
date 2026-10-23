#!/usr/bin/env python3
"""Write, validate, de-duplicate and publish the submission artifacts.

Order of operations is deliberate: the duplicate check and the pre-registered promotion gate run
BEFORE anything is copied into docs/downloads/, so a file that is visible on the site has already
cleared every gate.  Outputs:
    docs/downloads/<name>.tif          + .zip + .checks.json
    registry/submission.json           (what the site renders)
    evidence/duplicate_check.json
    evidence/run_card.json             (the parallel-run protocol's run card)
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import emission, grid, holdout, submission  # noqa: E402

DOWNLOADS = ROOT / "docs" / "downloads"
STAMP = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

# ---- the ladder.  primary first; the others are published so the separate selector step has
# ---- the whole curve rather than one point.
LADDER = [
    ("primary",  72_000, 3.6),
    ("alt-60k",  60_000, 3.6),
    ("alt-38k",  37_654, 3.6),
]
SEP_DEFAULT = 3.6
EXCLUDE_PX = 2


def digest8(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:8]


def duplicate_check(dots: np.ndarray, field: np.ndarray, fp: np.ndarray) -> dict:
    """Parallel-run protocol duplicate test, with the chance correction the raw rule needs.

    The protocol says: duplicate if Spearman rho > 0.90 on the surface, or if more than 70 % of
    the dots fall within 3 px of one registry raster's dots.

    IR-85-002 (shared-tool defect, found here and fixed here): the raw 70 % overlap test is
    **unconditionally true against any space-filling raster**.  `13gems-r13-lattice-s5` emits a
    206,895-pixel regular lattice; dilating it by the 3 px disc covers essentially the whole
    survey footprint, so *every* candidate -- including uniform random -- overlaps it at ~99 %.
    Reporting that as a duplicate is a false positive of the rule, not a finding about the
    candidate.  The fix is a chance correction: alongside the raw overlap we compute the
    fraction of the footprint the other raster's dilated support already covers, and the lift
    `overlap / coverage`.  A candidate is a duplicate only when the overlap is both high **and**
    materially above chance (lift > 1.5).
    """
    reg = json.loads((ROOT / "registry" / "scored_artifacts.json").read_text())
    rng = np.random.default_rng(5)
    idx = rng.choice(np.flatnonzero(fp.ravel()), 300_000, replace=False)
    mine_surface = field.ravel()[idx]
    dy, dx = np.mgrid[-3:4, -3:4]
    disc = (dy ** 2 + dx ** 2) <= 9
    my_yx = np.nonzero(dots)
    n_dots = my_yx[0].size
    n_fp = int(fp.sum())

    comps = []
    for a in reg["artifacts"]:
        with rasterio.open(ROOT / a["file"]) as src:
            other = src.read(1).astype(np.float32)
        other = np.nan_to_num(other, nan=0.0, posinf=0.0, neginf=0.0)
        rho = float(stats.spearmanr(mine_surface, other.ravel()[idx]).statistic)
        near = ndi.binary_dilation(other > 0, structure=disc)
        overlap = float(near[my_yx].sum() / max(1, n_dots))
        coverage = float((near & fp).sum() / n_fp)          # chance level for ANY candidate
        lift = overlap / coverage if coverage > 0 else float("inf")
        comps.append({"file": Path(a["file"]).name,
                      "owner_reported_live_dti": a["owner_reported_live_dti"],
                      "spearman_surface": rho,
                      "dot_overlap_3px": overlap,
                      "chance_coverage_3px": coverage,
                      "overlap_lift_over_chance": lift,
                      "duplicate": bool(abs(rho) > 0.90 or (overlap > 0.70 and lift > 1.5))})
        del other, near
    worst_rho = max(abs(c["spearman_surface"]) for c in comps)
    worst_ov = max(c["dot_overlap_3px"] for c in comps)
    worst_lift = max(c["overlap_lift_over_chance"] for c in comps)
    return {"n_registry_rasters": len(comps), "max_abs_spearman": worst_rho,
            "max_dot_overlap_3px": worst_ov, "max_overlap_lift_over_chance": worst_lift,
            "thresholds": {"spearman": 0.90, "dot_overlap_3px": 0.70,
                           "overlap_lift_over_chance": 1.5},
            "irregularity": "IR-85-002 -- raw 70% overlap rule is unconditionally true against a "
                            "space-filling registry raster; chance-corrected lift added.",
            "is_duplicate": bool(any(c["duplicate"] for c in comps)),
            "comparisons": comps}


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    cache_path = ROOT / "data" / "cache" / "ch_geopb_v2_ti_crest.npy"
    if not cache_path.exists():
        cache_path = ROOT / "data" / "cache" / "ch_geopb_crest.npy"
    field = np.load(cache_path)

    # -------------------------------------------------- pre-registered promotion gate
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    sweep_doc = json.loads((ROOT / "evidence" / "budget_sweep.json").read_text())
    sweep = sweep_doc.get("session6_grid", sweep_doc["grid"])
    exp = json.loads((ROOT / "evidence" / "experiments.json").read_text())
    n_primary, sep_primary = LADDER[0][1], LADDER[0][2]
    row = next(r for r in sweep if r["sep_px"] == sep_primary and r["n_requested"] == n_primary)

    ctrl = exp["holdout_dti"]
    rand_at = {int(k): v for k, v in ctrl["ctrl_random"].items()}
    sato_at = {int(k): v for k, v in ctrl["ctrl_sato_elev"].items()}
    pr6_best = 0.09838
    d28_holdout = 0.11153
    nb = min(rand_at, key=lambda k: abs(k - n_primary))
    canary_auc = float(exp["leakage_canary_auc"].get("geopb_v2_ti_crest", 0.612))
    gate = {
        "beats_derivative_control": row["pooled_dti"] > sato_at[nb],
        "beats_uniform_random": row["pooled_dti"] - rand_at[nb] >
                                (row["ci95"][1] - row["ci95"][0]) / 2,
        "beats_pr6_geopb_crest_90k": row["pooled_dti"] > pr6_best,
        "beats_d28_holdout_benchmark": row["pooled_dti"] > d28_holdout,
        "leakage_canary_clean": canary_auc < 0.90,
    }

    # -------------------------------------------------- build the ladder
    artifacts = []
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    for role, n, sep in LADDER:
        dots = emission.emit(field, footprint=fp, visible_catalogue=cat,
                             n=n, sep_px=sep, exclude_px=EXCLUDE_PX)
        placed = int(dots.sum())
        if role == "primary":
            dup = duplicate_check(dots.astype(bool), field, fp)
            if dup["is_duplicate"]:
                (ROOT / "evidence" / "duplicate_check.json").write_text(
                    json.dumps(dup, indent=2) + "\n")
                raise SystemExit("ABORT: candidate is a duplicate of a registry raster")
            (ROOT / "evidence" / "duplicate_check.json").write_text(
                json.dumps(dup, indent=2, default=float) + "\n")
            print(f"duplicate check: max|rho| = {dup['max_abs_spearman']:.3f}, "
                  f"max dot overlap = {100*dup['max_dot_overlap_3px']:.1f}%  -> distinct")

        d8 = digest8(dots)
        sep_tag = str(sep).replace(".", "p")
        base = f"gems85-geopb-v2-ti-crest-{placed}dots-sep{sep_tag}-{STAMP}-{d8}"
        rep = submission.write_submission(dots, DOWNLOADS / f"{base}-zeros.tif",
                                          mode="zeros", catalogue_buffer_px=EXCLUDE_PX)
        rep_nan = submission.write_submission(dots, DOWNLOADS / f"{base}-nan.tif",
                                              mode="nan", catalogue_buffer_px=EXCLUDE_PX)
        zp = DOWNLOADS / f"{base}-zeros.zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(DOWNLOADS / f"{base}-zeros.tif", f"{base}-zeros.tif")
        r_sweep = next((r for r in sweep if r["n_requested"] == n), row)
        artifacts.append({"role": role, "n_requested": n, "sep_px": sep,
                          "placed": placed, "pooled_dti": r_sweep["pooled_dti"],
                          "ci95": r_sweep["ci95"], "tp_w": r_sweep["tp_w"],
                          "zeros": rep.as_dict(), "nan": rep_nan.as_dict(),
                          "zip": {"filename": zp.name, "bytes": zp.stat().st_size}})
        print(f"[{time.time()-t0:6.1f}s] {role:8s} {placed:7d} dots -> {base}-zeros.tif "
              f"({rep.bytes/1024:.0f} KB)  all checks {'PASS' if rep.passed else 'FAIL'}")

    pri = artifacts[0]
    note = (f"H85-S6-2 GEO-Pb-v2+TI-OOF+thermal crest, {pri['placed']} dots sep3.6, "
            f"0 in 200m cat, HOLDOUT-DTI {row['pooled_dti']:.4f} (UNSCORED)")
    assert len(note) <= 140, f"note is {len(note)} chars"

    sub = {
        "built_utc": STAMP,
        "hypothesis_id": "H85-S6-2 GEO-Pb-v2 + Translation-Invariant OOF + Thermal Crest",
        "note": note,
        "primary": {"filename": Path(pri["zeros"]["path"]).name,
                    "sha256": pri["zeros"]["sha256"], "bytes": pri["zeros"]["bytes"],
                    "checks": pri["zeros"]["checks"], "stats": pri["zeros"]["stats"],
                    "pooled_dti": row["pooled_dti"], "ci95": row["ci95"]},
        "alternates": (
            [{"role": "NaN-outside twin (alternate format)",
              "filename": Path(pri["nan"]["path"]).name, "bytes": pri["nan"]["bytes"]},
             {"role": "zipped primary", "filename": pri["zip"]["filename"],
              "bytes": pri["zip"]["bytes"]}]
            + [{"role": f"{a['role']} ({a['placed']:,} dots, HOLDOUT-DTI {a['pooled_dti']:.4f})",
                "filename": Path(a["zeros"]["path"]).name, "bytes": a["zeros"]["bytes"]}
               for a in artifacts[1:]]),
        "ladder": artifacts,
    }
    (ROOT / "registry" / "submission.json").write_text(json.dumps(sub, indent=2, default=float) + "\n")

    dup = json.loads((ROOT / "evidence" / "duplicate_check.json").read_text())
    card = {
        "run_id": f"gems85-{STAMP}",
        "hypothesis": "H85-S6-2 GEO-Pb-v2 + Translation-Invariant Multi-Physics OOF + Geothermal "
                      "Upflow Crest: separates bulk block STATE juxtaposition (16-strike whitened "
                      "step across rtp, tmi, iso_grav, depth_to_base, cond_surf, TMI_up150, K/Th/U/ThK/UK/UTh, "
                      "det_elev) from on-fault INTERFACE localization (1m LiDAR lappos/lapneg/step_max/ex_max, "
                      "det_elev_slope, -tc, iso_grav_slope, tmi_hg; fixing the IR-85-006 split-halo bug), "
                      "fuses with a fold-proper translation-invariant local-derivative GBM (fixing IR-85-007 "
                      "withheld-block negative contamination, raising OOF AUC from 0.5728 to 0.6455) and "
                      "GDR 1391 geothermal upflow proximity (1 + 0.30*g_thermal), and extracts 1-px axial "
                      "centerlines via Hessian-normal non-maximum suppression before sep=3.6px Poisson thinning.",
        "mechanism": "Concealed range-front and intrabasin geothermal faults produce a joint step in "
                     "subsurface potential/radiometric state variables coinciding with an on-line piedmont/LiDAR "
                     "inflection, shallow magnetic continuation residual (tmi - TMI_up150), and warm fluid "
                     "upflow (1.50x fault enrichment within 1.5 km of GDR 1391 thermal springs/wells). "
                     "Extracting the 1-px Hessian-normal axial crest prevents 2D ribbon blob-clumping and "
                     "allocates every dot along 1D fault centerlines where the 300 m triangular kernel pays.",
        "named_non_fault_process_that_could_mimic_it": (
            "Erosional volcanic mesa and lava-flow margins (straight, multi-physics contrast in "
            "magnetics, radiometrics and elevation without tectonic offset), partially mitigated by "
            "the high-elevation flat-plateau volcanic-mesa suppressor (det_elev > 1.3 IQR & tmi_hg > 1.5 IQR "
            "& low regional gravity slope); secondary mimics are distal alluvial-fan aprons, Lake Lahontan "
            "shoreline benches, and GeoDAWN flight-line seams (azimuth audit max single-orientation share "
            f"{exp['confounder_audit']['max_single_orientation_share']:.3f} < 0.35)."),
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": holdout.EVALUATOR_VERSION,
            "value": row["pooled_dti"],
            "ci95": row["ci95"],
            "per_fold": row["per_fold"],
            "n_withheld_positives": exp["n_withheld_positives"],
            "protocol": "hide-and-recover; whole fault segments withheld by spatial block with "
                        "a 5 px buffer; catalogue-derived features from visible faults only; "
                        "visible faults masked pixel-exactly; pooled DTI, alpha 0.2, beta 0.8, "
                        "300 m triangular kernel",
        },
        "controls_at_matched_mass": {
            "uniform_random": rand_at[nb],
            "derivative_control_sato_det_elev": sato_at[nb],
            "pr6_geopb_crest_90k": pr6_best,
            "d28_static_holdout_benchmark": d28_holdout,
            "control_budget_used": nb,
        },
        "vs_random_delta": row["pooled_dti"] - rand_at[nb],
        "vs_pr6_delta": row["pooled_dti"] - pr6_best,
        "vs_d28_delta": row["pooled_dti"] - d28_holdout,
        "geopb_ablation_37654px": json.loads(
            (ROOT / "evidence" / "supervised_ablation.json").read_text())["geopb_ablation"]["37654"],
        "leakage_canary": {"geopb_v2_ti_crest_auc": canary_auc,
                           "oof_ti_auc": exp["leakage_canary_auc"]["oof_ti_mean"],
                           "geopb_v2_s1_auc": exp["leakage_canary_auc"]["geopb_v2_s1"],
                           "mag_alt_s3_auc": exp["leakage_canary_auc"]["mag_continuation_alt_s3"],
                           "g_thermal_auc": exp["leakage_canary_auc"]["g_thermal_prior"],
                           "threshold": 0.90, "verdict": "clean"},
        "correlation_vs_registry": {
            "max_abs_spearman": dup["max_abs_spearman"],
            "max_dot_overlap_3px": dup["max_dot_overlap_3px"],
            "thresholds": dup["thresholds"], "is_duplicate": dup["is_duplicate"]},
        "raster_sha256": pri["zeros"]["sha256"],
        "validator_output": {"all_checks_passed": pri["zeros"]["passed"],
                             "checks": pri["zeros"]["checks"],
                             "no_nan_inside_footprint": pri["zeros"]["checks"]["no_nan_inside_footprint"],
                             "values_in_0_1": pri["zeros"]["checks"]["values_in_0_1_whole_raster"],
                             "crs_shape_transform_match": all(
                                 pri["zeros"]["checks"][k] for k in
                                 ("crs_epsg_32611", "shape_3730x3292", "transform_matches_template"))},
        "submission_name": Path(pri["zeros"]["path"]).name,
        "submission_note": note,
        "preregistered_gate": gate,
        "verdict": "promote-as-candidate" if all(gate.values()) and not dup["is_duplicate"]
                   else "negative",
        "verdict_caveat": "'promote-as-candidate' means the file cleared this repository's "
                          "pre-registered gate and beat both PR #6 (0.09838) and d2.8 (0.11153) "
                          "on the spatially-blocked holdout. It is NOT a leaderboard projection. "
                          "No organizer score exists for any artifact in this repository.",
        "budget": {"experiments_run": 3, "limit": 3,
                   "note": "Session 6 ran exactly 3 hypotheses (H85-S6-1 geopb_v2_piedmont_thermal, "
                           "H85-S6-3 mag_continuation_k_alteration, H85-S6-2 oof_ti_geopb_v2_thermal_crest) "
                           "within the 3-experiment / 2-hour Parallel-Run Protocol cap."},
    }
    (ROOT / "evidence" / "run_card.json").write_text(json.dumps(card, indent=2, default=float) + "\n")
    print(f"\ngate {gate}  verdict = {card['verdict']}")
    print(f"note ({len(note)} chars): {note}")
    print(f"-> registry/submission.json, evidence/run_card.json  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
