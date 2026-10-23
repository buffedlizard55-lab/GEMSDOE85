from pathlib import Path
import json
import shutil
import pytest
from check_site import check
from preflight import review

ROOT = Path(__file__).resolve().parents[1]


def test_site_links_and_submission_status_work():
    assert check() == []
    sub_path = ROOT / 'registry/submission.json'
    assert sub_path.exists()
    sub = json.loads(sub_path.read_text())
    assert len(sub['note']) <= 140
    assert (ROOT / 'docs/downloads' / sub['primary']['filename']).exists()


def test_preflight_missing_data_is_negative_not_success(tmp_path):
    shutil.copytree(ROOT / 'registry', tmp_path / 'registry')
    shutil.copytree(ROOT / 'vendor', tmp_path / 'vendor')
    card = review(tmp_path)
    assert card['verdict'] == 'negative'
    assert card['safe_to_submit'] is False
    assert card['safe_to_download'] is False
    assert card['experiments_run'] == 0
    assert card['submission_slots_used'] == 0
    assert not all(row['ok'] for row in card['gates']['core_mirror_integrity'])
    assert card['gates']['template_unmodified']
    assert not card['gates']['cached_stack_available']
    assert not list(tmp_path.rglob('*.tif'))


def test_preflight_detects_shared_code_drift(tmp_path):
    shutil.copytree(ROOT / 'registry', tmp_path / 'registry')
    shutil.copytree(ROOT / 'vendor', tmp_path / 'vendor')
    p = tmp_path / 'vendor/gems57/metric.py'
    p.write_text(p.read_text() + '\n# synthetic tampering test\n')
    card = review(tmp_path)
    assert not card['gates']['template_unmodified']
    assert any('metric.py' in blocker for blocker in card['blockers'])


def test_source_register_does_not_claim_organizer_score_receipt():
    j = json.loads((ROOT / 'registry/sources.json').read_text())
    assert next(x for x in j['sources'] if x['id'] == 'organizer-submissions')['status'] == 'redirected to login'
    assert next(x for x in j['sources'] if x['id'] == 'h33-owner-page')['class'] == 'owner research, not official score receipt'
