"""Release regressions: format-only promotion must never be reintroduced."""
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release_portal', ROOT / 'scripts/build_site.py')
portal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portal)


@pytest.mark.parametrize('payload', [None, 'not json', '[]', '{}', '{"safe_to_submit": true, "verdict": "promote"}'])
def test_missing_malformed_or_claimed_promotion_fails_closed(tmp_path, payload):
    (tmp_path / 'evidence').mkdir()
    (tmp_path / 'registry').mkdir()
    if payload is not None:
        (tmp_path / 'evidence/run_card.json').write_text(payload)
    assert portal.release_blockers(tmp_path)


def test_legacy_urls_rebuilt_without_download_claims(tmp_path):
    (tmp_path / 'docs/duplex-lane').mkdir(parents=True)
    (tmp_path / 'docs/duplex-lane/index.html').write_text('OK TO DOWNLOAD AND SUBMIT')
    (tmp_path / 'registry').mkdir()
    (tmp_path / 'evidence').mkdir()
    assert portal.build(tmp_path) == 0
    text = (tmp_path / 'docs/duplex-lane/index.html').read_text()
    assert 'BLOCKED — DO NOT SUBMIT' in text
    assert 'OK TO DOWNLOAD AND SUBMIT' not in text
    assert 'href="../index.html"' in text
    first = (tmp_path / 'docs/index.html').read_bytes()
    portal.build(tmp_path)
    assert (tmp_path / 'docs/index.html').read_bytes() == first


def test_untrusted_blocker_text_is_escaped(tmp_path):
    (tmp_path / 'registry').mkdir()
    (tmp_path / 'evidence').mkdir()
    (tmp_path / 'evidence/run_card.json').write_text(json.dumps({'blockers': ['<script>alert(1)</script>']}))
    portal.build(tmp_path)
    text = (tmp_path / 'docs/index.html').read_text()
    assert '<script>' not in text
    assert '&lt;script&gt;' in text
