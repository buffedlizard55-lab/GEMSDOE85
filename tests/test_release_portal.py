"""Regression tests for blocked release presentation and malformed evidence."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


portal = _load("blocked_portal", ROOT / "scripts/build_site.py")
checker = _load("blocked_site_checker", ROOT / "scripts/check_site.py")
preflight = _load("blocked_preflight", ROOT / "scripts/preflight.py")


def _safe_fixture(root: Path) -> None:
    card = preflight.review(ROOT)
    submission = preflight.blocked_submission_registry(card)
    for relative, payload in (("evidence/run_card.json", card), ("registry/submission.json", submission)):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2) + "\n")
    for relative in ("index.html", "registry/lane.json", "registry/cache_manifest.json",
                     "evidence/saturation_certificate.json"):
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    blocked = "<!doctype html><html><body><h1>DO NOT DOWNLOAD OR SUBMIT</h1><p>No new competition submission GeoTIFF is available.</p></body></html>"
    for relative in ("docs/index.html", "docs/executive-summary.html"):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blocked)
    for relative in ("evidence/run_card.json", "registry/submission.json",
                     "registry/lane.json", "registry/cache_manifest.json"):
        source = root / relative
        target = root / "docs" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


@pytest.mark.parametrize("payload", ["not json", "[]", "{}", '{"verdict":"promote","safe_to_download":true,"safe_to_submit":true}'])
def test_malformed_or_forged_current_card_fails_site_check(tmp_path, payload):
    _safe_fixture(tmp_path)
    (tmp_path / "evidence/run_card.json").write_text(payload)
    errors = checker.check(tmp_path)
    assert any("run card" in error.lower() or "evidence/run_card.json" in error for error in errors)


def test_missing_current_card_fails_site_check(tmp_path):
    _safe_fixture(tmp_path)
    (tmp_path / "evidence/run_card.json").unlink()
    (tmp_path / "docs/evidence/run_card.json").unlink()
    assert any("Missing or invalid evidence/run_card.json" in error for error in checker.check(tmp_path))


def test_untrusted_blocker_text_is_html_escaped():
    card = preflight.review(ROOT)
    card["blockers"] = ["<script>alert(1)</script>"]
    text = portal._blocker_list(card)
    assert "<script>" not in text
    assert "&lt;script&gt;" in text


def test_legacy_pages_are_rebuilt_as_blocked_and_deterministically(tmp_path):
    legacy = tmp_path / "docs/duplex-lane"
    legacy.mkdir(parents=True)
    (legacy / "index.html").write_text("OK TO DOWNLOAD AND SUBMIT")
    assert portal.build(tmp_path) == 0
    text = (legacy / "index.html").read_text()
    assert "HISTORICAL RESEARCH ONLY — DO NOT DOWNLOAD OR SUBMIT" in text
    assert "OK TO DOWNLOAD AND SUBMIT" not in text
    assert 'href="../index.html"' in text
    first = (tmp_path / "docs/index.html").read_bytes()
    portal.build(tmp_path)
    assert (tmp_path / "docs/index.html").read_bytes() == first
