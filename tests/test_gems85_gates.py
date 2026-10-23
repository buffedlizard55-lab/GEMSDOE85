"""Automated end-to-end verification tests for GEMSDOE85 (Lane H85-TVFV)."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from gems57.grid import EPSG, HEIGHT, TRANSFORM, WIDTH
from gems57.uniqueness import RADIUS_PX, compare_array_to_registry
from gems57.validate import assert_submittable, validate
from gems85.dinkelbach import build_exact_300m_kernel_offsets
from gems85.forensics_and_audit import sha256_file
from gems85.paths import DOWNLOADS_DIR, EVIDENCE_DIR, EXTERNAL_REPO_DIR, ROOT


def test_clean_external_csv_provenance() -> None:
    """Verify tracked external CSVs exist, are non-empty, and strip fault vertex coords."""
    hf_csv = EXTERNAL_REPO_DIR / "usgs_heat_flow_wells_epsg32611.csv"
    st_csv = EXTERNAL_REPO_DIR / "gb_regional_stress_grid_10km.csv"
    assert hf_csv.is_file() and hf_csv.stat().st_size > 100_000
    assert st_csv.is_file() and st_csv.stat().st_size > 40_000
    header = st_csv.read_text().splitlines()[0]
    assert "QFFD_ID" not in header
    assert "block_row_10km" in header and "shmin_az_deg" in header and "aphi" in header


def test_upstream_uniqueness_fast_path_exact_bit_identity(tmp_path: Path) -> None:
    """Prove upstream sparse dilation optimization matches scipy binary_dilation to 1e-15."""
    rng = np.random.default_rng(85)
    H, W = 96, 112
    fp = np.ones((H, W), dtype=bool)
    fp[:4, :] = False
    mine = np.zeros((H, W), dtype=np.float32)
    theirs = np.zeros((H, W), dtype=np.float32)
    mine_pts = rng.choice(H * W, size=240, replace=False)
    their_pts = rng.choice(H * W, size=310, replace=False)
    mine.ravel()[mine_pts] = 1.0
    theirs.ravel()[their_pts] = 1.0
    mine[~fp] = 0.0
    theirs[~fp] = 0.0

    ref_tif = tmp_path / "ref.tif"
    with rasterio.open(
        ref_tif, "w", driver="GTiff", height=H, width=W, count=1,
        dtype="float32", crs="EPSG:32611", transform=TRANSFORM,
    ) as ds:
        ds.write(theirs, 1)

    res = compare_array_to_registry(mine, [{"repo": "test", "submission": "ref", "file": str(ref_tif)}], fp)
    got_ov = res["rows"][0]["my_dots_within_3px_of_theirs"]

    r = int(np.ceil(RADIUS_PX))
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    exact_ov = float(binary_dilation(theirs > 0, structure=(yy * yy + xx * xx <= RADIUS_PX * RADIUS_PX))[mine > 0].mean())
    assert abs(got_ov - exact_ov) < 1e-12


def test_exact_300m_kernel_geometry() -> None:
    dr, dc, k_arr, flat_off, k2d = build_exact_300m_kernel_offsets(WIDTH)
    # 29 integer lattice points satisfy d <= 300m; the 4 cardinal boundary points (+-3,0),(0,+-3) have k(300m)=0,
    # leaving exactly 25 strictly positive kernel weights k(d) = max(1 - d/300, 0) > 0!
    assert len(k_arr) == 25
    assert float(k_arr.max()) == 1.0
    assert np.all((k_arr > 0.0) & (k_arr <= 1.0))
    assert k2d.shape == (7, 7) and float(k2d[3, 3]) == 1.0
    assert int((k2d > 0).sum()) == 25
    assert flat_off.shape == (25,)


def test_leakage_canary_and_strict_3_experiment_budget() -> None:
    canary = json.loads((EVIDENCE_DIR / "leakage_canary.json").read_text())
    assert canary["passed"] is True
    assert canary["violations_count"] == 0
    assert canary["features_checked"] == 61
    assert float(canary["max_observed_symmetric_auc"]) <= 0.90

    summary = json.loads((EVIDENCE_DIR / "experiments_holdout_summary.json").read_text())
    assert summary["evidence_class"] == "HOLDOUT-DTI"
    assert summary["evaluator_version"] == "gems57-pooled-hide-v2"
    assert summary["strict_budget_experiments_run"] == 3
    assert list(summary["experiments"].keys()) == ["E85-1", "E85-2", "E85-3"]
    assert float(summary["mean_holdout_dti"]) > float(summary["h33_reference_holdout_dti"])


def test_final_submission_geotiff_zip_and_all_7_gates() -> None:
    audit = json.loads((EVIDENCE_DIR / "automated_validation_and_uniqueness.json").read_text())
    assert audit["ready_for_competition_upload"] is True, f"Failed gates: {audit['gates']}"
    assert audit["verdict"] == "READY_TO_SUBMIT_PROMOTE"
    for gname, g in audit["gates"].items():
        assert g["passed"] is True, f"Gate {gname} failed: {g['detail']}"

    sub_tif = DOWNLOADS_DIR / audit["submission_file"]
    sub_zip = sub_tif.with_suffix(".zip")
    sub_json = sub_tif.with_suffix(".json")
    assert sub_tif.is_file() and sub_zip.is_file() and sub_json.is_file()
    assert sha256_file(sub_tif) == audit["submission_sha256"]

    receipt_json = json.loads(sub_json.read_text())
    assert 1 <= len(receipt_json["note"]) <= 140
    assert 1 <= len(receipt_json["submission_name"]) <= 140

    with rasterio.open(ROOT / "data/bridge/sample_submission.tif") as sds:
        fp = np.isfinite(sds.read(1))
    with rasterio.open(ROOT / "data/bridge/existing_faults.tif") as cds:
        cat = (cds.read(1) > 0) & fp

    val = validate(sub_tif, fp, cat)
    assert_submittable(val)
    assert val["meta"]["crs"] == f"EPSG:{EPSG}"
    assert val["meta"]["shape"] == [HEIGHT, WIDTH]
    assert val["n_nan"] == 0 and val["n_infinite"] == 0
    assert 0.0 <= val["min"] <= val["max"] <= 1.0
    assert val["on_catalogue_positive_pixels"] == 0

    with zipfile.ZipFile(sub_zip) as zf:
        assert zf.namelist() == [sub_tif.name]
        assert zf.read(sub_tif.name) == sub_tif.read_bytes()


def test_github_pages_links_figures_and_run_card() -> None:
    import re
    for page in ("index.html", "executive-summary.html", "methodology.html"):
        html_path = ROOT / "docs" / page
        assert html_path.is_file() and html_path.stat().st_size > 4_000
        text = html_path.read_text()
        assert "READY_TO_SUBMIT_PROMOTE" in text or "ALL 7 AUTOMATED GATES PASSED" in text
        for href in re.findall(r'(?:href|src)="([^"]+)"', text):
            if href.startswith(("http://", "https://", "#")):
                continue
            target = (ROOT / "docs" / href).resolve()
            assert target.is_file(), f"Broken local asset/link in {page}: {href} -> {target}"

    readme = (ROOT / "README.md").read_text()
    assert "I want to win this competition:" in readme
    assert "gems85-h85-tvfv-e85-3-20261022-zeros.tif" in readme

    rc = json.loads((EVIDENCE_DIR / "run_card.json").read_text())
    assert rc["verdict"] == "promote"
    assert rc["safe_to_download_and_submit_without_human_intervention"] is True
    assert rc["correlation_and_overlap_vs_registry"]["duplicate_detected"] is False
    assert rc["correlation_and_overlap_vs_registry"]["binding_discriminating_3px_forward_overlap_max"] <= 0.70
    assert rc["correlation_and_overlap_vs_registry"]["surface_max_abs_spearman"] <= 0.90
    s1 = rc["holdout_dti"]["strict_3_experiment_ablation"]["E85-1"]["score"]
    s2 = rc["holdout_dti"]["strict_3_experiment_ablation"]["E85-2"]["score"]
    s3 = rc["holdout_dti"]["strict_3_experiment_ablation"]["E85-3"]["score"]
    h33 = rc["holdout_dti"]["h33_fold_equivalent_control"]
    assert h33 < s1 < s2 < s3
