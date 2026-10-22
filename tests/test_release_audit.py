"""Release decisions must not be inferred from historical format diagnostics."""
from pathlib import Path
import json
import shutil
import pytest
import build_site
from preflight import verify_template

ROOT = Path(__file__).resolve().parents[1]


def test_shared_bytes_still_match_pins():
    assert verify_template() == []


def test_remeasured_literal_stop_overrides_historical_format_pass():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    sat = card['registry']['saturation_certificate']
    assert sat['universal_overlap_blocker'] is True
    assert sat['uncovered_allowed_pixels'] == 0
    assert card['template_unmodified']
    assert any(row['format_ok_conservative'] for row in card['historical_artifacts'])
    assert all(row['safe_to_submit'] is False for row in card['historical_artifacts'])
    assert not card['safe_to_submit']
    assert card['experiments_run'] == card['submission_slots_used'] == 0


def test_publisher_refuses_unapproved_positive_card(tmp_path):
    (tmp_path / 'evidence').mkdir()
    (tmp_path / 'evidence/run_card.json').write_text(json.dumps(dict(verdict='promote',safe_to_submit=True)))
    with pytest.raises(ValueError, match='No authorized promotion'):
        build_site.build(tmp_path)
    assert not (tmp_path / 'docs/index.html').exists()


def test_publisher_refuses_public_binary_even_for_negative_card(tmp_path):
    (tmp_path / 'evidence').mkdir()
    shutil.copy(ROOT / 'evidence/run_card.json', tmp_path / 'evidence/run_card.json')
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs/unapproved.tif').write_bytes(b'unapproved')
    with pytest.raises(ValueError, match='Unapproved public binary'):
        build_site.build(tmp_path)


def test_site_generation_is_deterministic():
    build_site.build()
    before = {p: p.read_bytes() for p in (ROOT / 'docs').rglob('*.html')}
    build_site.build()
    assert all(p.read_bytes() == content for p, content in before.items())
