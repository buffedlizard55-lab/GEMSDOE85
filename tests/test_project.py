"""Release contracts: format-valid history must never imply protocol clearance."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
import importlib.util


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def generated():
    builder = load('build_site')
    assert builder.build() == 0
    return json.loads((ROOT / 'evidence/run_card.json').read_text())


def test_site_generation_and_validation(generated):
    assert load('check_site').check(ROOT) == []


def test_all_historical_files_revalidated_not_promoted(generated):
    rows = generated['historical_artifacts']
    expected = set((ROOT / 'submissions').rglob('*.tif')) | set((ROOT / 'docs/downloads').rglob('*.tif'))
    assert {row['file'] for row in rows} == {p.relative_to(ROOT).as_posix() for p in expected}
    assert rows and any(r['format_ok'] for r in rows)
    for row in rows:
        assert row['safe_to_submit'] is False
        path = ROOT / row['file']
        assert row['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
        if row['format_ok']:
            assert all(row['checks'].values())
            assert row['validator_output']['ok']
    assert any(not row['format_ok'] for row in rows if '-nan.tif' in row['file'])


def test_run_card_and_note_contracts(generated):
    card = generated
    assert card['verdict'] == 'negative'
    assert card['safe_to_submit'] is False
    assert card['raster_sha256'] is None
    assert card['submission_name'] is None
    assert len(card['submission_note']) <= 140
    assert card['holdout']['evidence_class'] == 'HOLDOUT-DTI'
    for key in ('dti', 'ci95', 'withheld_positive_pixels'):
        assert card['holdout'][key] is None
    assert card['experiments_run'] == card['submission_slots_used'] == 0
    assert card['gates']['template_unmodified']
    assert not card['gates']['cached_stack_available']


def test_source_register_does_not_claim_organizer_score_receipt():
    j = json.loads((ROOT / 'registry/sources.json').read_text())
    assert next(x for x in j['sources'] if x['id'] == 'organizer-submissions')['status'] == 'redirected to login'
    assert next(x for x in j['sources'] if x['id'] == 'h33-owner-page')['class'] == 'owner research, not official score receipt'
