"""Fail-closed site and current authorization contracts (no raster libs needed)."""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


site = load("build_site_review", ROOT / "scripts/build_site.py")
checker = load("check_site_review", ROOT / "scripts/check_site.py")


def test_current_gate_is_fail_closed():
    blockers = site.submission_blockers(ROOT)
    assert blockers
    assert any("lane" in item.lower() for item in blockers)
    assert any("stack" in item.lower() for item in blockers)
    assert any("saturation" in item.lower() for item in blockers)


def test_site_build_and_checker():
    assert site.build() == 0
    assert checker.check(ROOT) == []
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html"):
        text = (ROOT / rel).read_text()
        assert "BLOCKED — DO NOT DOWNLOAD OR SUBMIT" in text
        assert "ALL 17 CHECKS PASS — OK TO DOWNLOAD AND SUBMIT" not in text


def test_no_active_internal_prediction_downloads():
    for p in (ROOT / "docs").rglob("*.html"):
        assert checker.LinksFor(p).artifact_links() == [], p


def test_current_card_is_negative_not_a_geological_result():
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["safe_to_download"] is False
    assert card["safe_to_submit"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 0
    assert "not a geological negative" in card["note"].lower()


def test_standing_prompt_is_preserved():
    readme = (ROOT / "README.md").read_text()
    assert "## The standing brief" in readme
    assert "MUST GENERATE A UNIQUE TIF SUBMISSION" in readme
    assert "5. RUN CARD" in readme
