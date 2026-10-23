"""Project-level release invariants; these are not geological skill tests."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_submission_registry_is_fail_closed():
    submission = json.loads((ROOT / "registry/submission.json").read_text())
    assert submission["status"] == "blocked"
    assert submission["primary"] is None
    assert submission["safe_to_download"] is False
    assert submission["safe_to_submit"] is False
    assert submission["submission_slots_used"] == 0
    assert len(submission["note"]) <= 140


def test_run_card_is_preflight_not_candidate_result():
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["experiment_status"] == "NOT RUN"
    assert card["budget"]["experiments_run"] == 0
    assert card["budget"]["experiment_limit"] == 3
    assert card["budget"]["hours_used"] == 0
    assert card["budget"]["hours_limit"] == 2
    assert card["budget"]["submission_slots_used"] == 0
    assert card["raster_sha256"] is None
    assert card["safe_to_download"] is False
    assert card["safe_to_submit"] is False
    assert card["holdout_dti"]["status"].startswith("NOT RUN")


def test_pages_tree_has_no_tiff_or_zip():
    docs = ROOT / "docs"
    assert not [p for suffix in ("*.tif", "*.tiff", "*.zip") for p in docs.rglob(suffix)]


def test_main_status_pages_are_explicit():
    for relative in ("docs/index.html", "docs/executive-summary.html"):
        text = (ROOT / relative).read_text()
        assert "DO NOT DOWNLOAD OR SUBMIT" in text
        assert "No new competition submission GeoTIFF" in text
