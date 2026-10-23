"""Fail-closed repository and site regression tests; not geological experiments."""
from pathlib import Path
import hashlib
import json
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]

import importlib.util


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


build_site = _load_module("build_site_main", ROOT / "scripts/build_site.py")
check_site = _load_module("check_site_main", ROOT / "scripts/check_site.py")
preflight = _load_module("preflight_main", ROOT / "scripts/preflight.py")


def _minimal_safe_fixture(root: Path) -> None:
    """Build the smallest valid blocked-state tree accepted by the site checker."""
    card = preflight.review(ROOT)
    sub = preflight.blocked_submission_registry(card)
    for relative, payload in (("evidence/run_card.json", card), ("registry/submission.json", sub)):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2) + "\n")
    for relative in ("index.html", "registry/lane.json", "registry/cache_manifest.json",
                     "evidence/saturation_certificate.json"):
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    docs = root / "docs"
    (docs / "evidence").mkdir(parents=True, exist_ok=True)
    (docs / "registry").mkdir(parents=True, exist_ok=True)
    blocked = '''<!doctype html><html><body>
    <h1>DO NOT DOWNLOAD OR SUBMIT</h1>
    <p>No new competition submission GeoTIFF is available.</p>
    </body></html>'''
    (docs / "index.html").write_text(blocked)
    (docs / "executive-summary.html").write_text(blocked)
    for relative in ("evidence/run_card.json", "registry/submission.json",
                     "registry/lane.json", "registry/cache_manifest.json"):
        source = root / relative
        target = docs / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def test_site_generation_and_validation():
    """The generated site must be internally consistent and remain blocked."""
    assert build_site.build(ROOT) == 0
    assert check_site.check(ROOT) == []
    index = (ROOT / "docs/index.html").read_text()
    executive = (ROOT / "docs/executive-summary.html").read_text()
    assert "DO NOT DOWNLOAD OR SUBMIT" in index
    assert "DO NOT DOWNLOAD OR SUBMIT" in executive
    assert "No new competition submission GeoTIFF" in index
    assert "No file link is provided" in executive
    assert not [p for suffix in ("*.tif", "*.tiff", "*.zip") for p in (ROOT / "docs").rglob(suffix)]


def test_current_run_card_and_registry_are_negative():
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    sub = json.loads((ROOT / "registry/submission.json").read_text())
    assert card["verdict"] == "negative"
    assert "proposal rank 1" in card["hypothesis"].lower()
    assert "proposal only, not tested" in card["mechanism"].lower()
    assert "lateral sedimentary facies change" in card["named_non_fault_process_that_could_mimic_it"]
    assert card["safe_to_download"] is False
    assert card["safe_to_submit"] is False
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert card["holdout_dti"]["label"] == "HOLDOUT-DTI"
    assert card["holdout_dti"]["evaluator_version"] == "gems57-pooled-hide-v2"
    assert card["holdout_dti"]["value"] is None
    assert card["holdout_dti"]["ci95"] is None
    assert card["holdout_dti"]["n_withheld_positives"] is None
    assert card["correlation_overlap_vs_registry"]["max_abs_spearman_surface"] is None
    assert card["correlation_overlap_vs_registry"]["max_dot_overlap_within_3px"] is None
    saturation = card["correlation_overlap_vs_registry"]["saturation_certificate"]
    assert saturation["witness_file"] == "data/raw/learning/registry-saturation-witness.tif"
    assert saturation["manifest_restore_path"] == "data/learning/registry-saturation-witness.tif"
    assert saturation["witness_path_mismatch"] is True
    assert saturation["local_revalidation"] is False
    assert card["validator_output"]["status"].startswith("NOT RUN")
    assert card["budget"]["experiments_run"] == 0
    assert card["budget"]["experiment_limit"] == 3
    assert card["budget"]["hours_used"] == 0
    assert card["budget"]["hours_limit"] == 2
    assert card["budget"]["submission_slots_used"] == 0
    assert len(card["submission_note"]) <= 140
    assert sub["status"] == "blocked"
    assert sub["primary"] is None
    assert sub["safe_to_download"] is False
    assert sub["safe_to_submit"] is False


def test_quarantine_manifest_accounts_for_all_removed_public_artifacts():
    manifest = json.loads((ROOT / "submissions/quarantine/manifest.json").read_text())
    assert len(manifest["files"]) == 42
    for record in manifest["files"]:
        path = ROOT / record["quarantine_copy"]
        assert path.is_file(), record["quarantine_copy"]
        assert path.stat().st_size == record["bytes"], record["quarantine_copy"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], record["quarantine_copy"]
        assert "not cleared" in record["release_status"]


def test_preflight_is_not_a_geological_experiment(capsys):
    card = preflight.review(ROOT)
    assert preflight.experiment_gate(ROOT) == 2
    assert "no experiment ran" in capsys.readouterr().out.lower()
    assert card["verdict"] == "negative"
    assert card["experiment_status"] == "NOT RUN"
    assert card["budget"]["experiments_run"] == 0
    assert card["budget"]["experiment_limit"] == 3
    assert card["budget"]["hours_used"] == 0
    assert card["budget"]["hours_limit"] == 2
    assert card["budget"]["submission_slots_used"] == 0
    assert card["safe_to_download"] is False
    assert card["safe_to_submit"] is False
    assert card["gates"]["lane_assigned"] is False
    assert card["gates"]["cached_feature_stack_available"] is False
    assert card["gates"]["literal_saturation_blocker"] is True
    assert card["correlation_overlap_vs_registry"]["unique"] is False


def test_checker_rejects_a_historical_tiff_link_and_file(tmp_path):
    _minimal_safe_fixture(tmp_path)
    assert check_site.check(tmp_path) == []
    page = tmp_path / "docs/index.html"
    page.write_text(page.read_text().replace("</body>", '<a href="prior.tif">prior</a></body>'))
    errors = check_site.check(tmp_path)
    assert any("download link is forbidden" in error for error in errors)

    # Direct prior-file URLs in machine-readable evidence are blocked too.
    page.write_text(page.read_text().replace('<a href="prior.tif">prior</a>', ""))
    direct = tmp_path / "docs/registry/external_sources.json"
    direct.write_text('{"url": "https://example.org/archive/prior.tif"}')
    errors = check_site.check(tmp_path)
    assert any("direct raster/archive URL is forbidden" in error for error in errors)
    direct.unlink()

    # A public Pages binary is blocked even if no page links to it.
    (tmp_path / "docs/downloads").mkdir()
    (tmp_path / "docs/downloads/prior.tif").write_bytes(b"not a real raster; checker fixture only")
    errors = check_site.check(tmp_path)
    assert any("Pages tree contains a raster/archive file" in error for error in errors)


def test_source_register_keeps_score_evidence_boundary():
    sources = json.loads((ROOT / "registry/sources.json").read_text())
    h33 = next(row for row in sources["sources"] if row["id"] == "h33-owner-page")
    assert h33["class"] == "owner research, not official score receipt"
    assert "no organizer score" in h33["limits"].lower()
