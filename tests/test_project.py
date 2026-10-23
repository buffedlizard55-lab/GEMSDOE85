"""End-to-end verification of build_site, check_site, byte-level GeoTIFF/ZIP contract, and preflight."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from gems85_site import build, check
from gems57 import gates as g57_gates
from gems57.grid import load_grid
from gems57.validate import assert_submittable, validate
from preflight import review

ROOT = Path(__file__).resolve().parents[1]


def test_site_build_links_and_validated_submission_contract():
    build()
    assert check() == []

    c_ev = (ROOT / "evidence/run_card.json").read_text(encoding="utf-8")
    c_docs = (ROOT / "docs/evidence/run_card.json").read_text(encoding="utf-8")
    c_dl = (ROOT / "docs/downloads/run_card.json").read_text(encoding="utf-8")
    assert c_ev == c_docs == c_dl

    card = json.loads(c_ev)
    assert card["safe_to_download"] is True
    assert card["safe_to_submit"] is True
    assert card["experiments_run"] == 3
    assert card["experiments_run"] <= card["experiments_limit"]

    sub = card["submission"]
    assert 1 <= len(sub["note"]) <= 140
    assert card["holdout"]["evidence_class"] == "HOLDOUT-DTI"
    assert card["holdout"]["evaluator_version"] == "gems57-pooled-hide-v2"
    assert card["holdout"]["withheld_positive_pixels"] == 11321
    assert card["holdout"]["dti"] > card["holdout"]["best_valid_control_dti"]

    assert card["leakage_canary"]["any_leakage_flag"] is False
    assert card["leakage_canary"]["max_symmetric_auc"] <= 0.90
    assert card["uniqueness"]["is_duplicate"] is False
    assert card["uniqueness"]["surface_worst_abs_spearman"] <= 0.90
    assert card["uniqueness"]["dots_worst_nonsaturating_3px_overlap"] <= 0.70

    tif_path = ROOT / sub["download_path"]
    zip_path = ROOT / sub["zip_download_path"]
    assert tif_path.is_file() and zip_path.is_file()
    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == sub["raster_sha256"]

    grid = load_grid(ROOT / "data")
    rep = validate(tif_path, grid.footprint, grid.catalogue)
    assert_submittable(rep)
    assert rep["in_footprint_positive_pixels"] == sub["emitted_dots"]
    assert rep["on_catalogue_positive_pixels"] == 0
    assert rep["n_nan"] == 0 and rep["n_infinite"] == 0
    assert rep["min"] == 0.0 and rep["max"] == 1.0

    t_rep = g57_gates.format_report(tif_path, ROOT / "data/sample_submission.tif", footprint=grid.footprint)
    assert t_rep["ok"] is True

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_path.read_bytes()


def test_preflight_missing_data_is_negative_not_success(tmp_path):
    shutil.copytree(ROOT / "registry", tmp_path / "registry")
    shutil.copytree(ROOT / "vendor", tmp_path / "vendor")
    card = review(tmp_path)
    assert card["verdict"] == "negative"
    assert card["safe_to_submit"] is False
    assert card["safe_to_download"] is False
    assert card["experiments_run"] == 0
    assert card["submission_slots_used"] == 0
    assert not all(row["ok"] for row in card["gates"]["core_mirror_integrity"])
    assert card["gates"]["template_unmodified"]
    assert not card["gates"]["cached_stack_available"]
    assert not list(tmp_path.rglob("*.tif"))


def test_preflight_detects_shared_code_drift(tmp_path):
    shutil.copytree(ROOT / "registry", tmp_path / "registry")
    shutil.copytree(ROOT / "vendor", tmp_path / "vendor")
    p = tmp_path / "vendor/gems57/metric.py"
    p.write_text(p.read_text() + "\n# synthetic tampering test\n")
    card = review(tmp_path)
    assert not card["gates"]["template_unmodified"]
    assert any("metric.py" in blocker for blocker in card["blockers"])


def test_source_register_does_not_claim_organizer_score_receipt():
    j = json.loads((ROOT / "registry/sources.json").read_text())
    assert next(x for x in j["sources"] if x["id"] == "organizer-submissions")["status"] == "redirected to login"
    assert next(x for x in j["sources"] if x["id"] == "h33-owner-page")["class"] == "owner research, not official score receipt"
