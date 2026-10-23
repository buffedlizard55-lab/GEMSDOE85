"""Synthetic format fixtures only: these are NOT geological experiments."""
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from release_audit import audit
from preflight import verify_template

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def raster(path, array, *, transform=None, crs='EPSG:32611', count=1):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, 'w', driver='GTiff', height=array.shape[0], width=array.shape[1], count=count,
                       dtype=array.dtype, transform=transform or from_origin(0, 1000, 100, 100), crs=crs) as dst:
        for band in range(1, count + 1):
            dst.write(array, band)


@pytest.fixture
def fixture_repo(tmp_path):
    shutil.copytree(ROOT / 'vendor', tmp_path / 'vendor')
    shutil.copytree(ROOT / 'registry', tmp_path / 'registry')
    manifest = {'files': []}
    for identity in ('sample_submission', 'existing_faults', 'labels', 'training_features'):
        path = tmp_path / 'data' / (identity + '.tif')
        raster(path, np.zeros((8, 9), np.float32))
        manifest['files'].append(dict(id=identity, dest=path.name, bytes=path.stat().st_size,
                                     sha256=hashlib.sha256(path.read_bytes()).hexdigest(), group='core'))
    write_json(tmp_path / 'registry/data_manifest.json', manifest)
    return tmp_path


def test_format_pass_never_promotes_and_missing_witness_blocks(fixture_repo):
    p = fixture_repo / 'docs/downloads/history.tif'
    a = np.zeros((8, 9), np.float32); a[4, 4] = 1
    raster(p, a)
    card = audit(fixture_repo)
    assert card['historical_artifacts'][0]['format_ok']
    assert card['historical_artifacts'][0]['safe_to_submit'] is False
    assert card['safe_to_submit'] is False
    assert card['registry']['saturation_certificate'] is None
    assert any('witness' in b for b in card['blockers'])


@pytest.mark.parametrize('kind', ['range', 'nan', 'crs', 'shape', 'transform', 'dtype', 'bands'])
def test_actual_byte_checks_not_manifest_claims(fixture_repo, kind):
    a = np.zeros((8, 9), np.float32)
    kwargs = {}
    if kind == 'range': a[4, 4] = -9999
    if kind == 'nan': a[4, 4] = np.nan
    if kind == 'crs': kwargs['crs'] = 'EPSG:4326'
    if kind == 'shape': a = a[:-1]
    if kind == 'transform': kwargs['transform'] = from_origin(1, 1000, 100, 100)
    if kind == 'dtype': a = a.astype('float64')
    if kind == 'bands': kwargs['count'] = 2
    raster(fixture_repo / 'docs/downloads/history.tif', a, **kwargs)
    card = audit(fixture_repo)
    assert not card['historical_artifacts'][0]['format_ok']
    assert not card['safe_to_submit']


def test_corrupt_reference_does_not_execute_shared_validator(fixture_repo):
    raster(fixture_repo / 'docs/downloads/history.tif', np.zeros((8, 9), np.float32))
    (fixture_repo / 'data/sample_submission.tif').write_bytes(b'corrupt')
    card = audit(fixture_repo)
    assert not card['historical_artifacts'][0]['format_ok']
    assert 'integrity unavailable' in card['historical_artifacts'][0]['error']


def test_changed_template_is_not_executed(fixture_repo):
    path = fixture_repo / 'vendor/gems57/gates.py'
    path.write_text('raise AssertionError("must not execute")')
    raster(fixture_repo / 'docs/downloads/history.tif', np.zeros((8, 9), np.float32))
    assert verify_template(fixture_repo)
    card = audit(fixture_repo)
    assert not card['gates']['template_unmodified']
    assert not card['historical_artifacts'][0]['format_ok']


def test_missing_inputs_remain_blocked_no_exception(fixture_repo):
    shutil.rmtree(fixture_repo / 'data')
    card = audit(fixture_repo)
    assert not card['safe_to_submit']
    assert not card['gates']['core_inputs_available']


def test_surface_failure_never_checks_final_dots(monkeypatch):
    from check_uniqueness import check
    from gems57 import gates
    calls = []
    def blocked(array, footprint, **kwargs):
        calls.append(kwargs['phase'])
        return {'ok': False, 'unique': False, 'stop_required': True}
    monkeypatch.setattr(gates, 'lane_uniqueness_report', blocked)
    result = check(np.ones((2, 2)), np.ones((2, 2)), {}, Path('not-read'), np.ones((2, 2), bool))
    assert result['stop_required'] and not result['unique']
    assert calls == ['surface']
    assert 'dots' not in result['phases']


def test_uniqueness_uses_shared_gate_without_policy_kwargs(monkeypatch):
    from check_uniqueness import check
    from gems57 import gates
    calls = []
    def good(array, footprint, **kwargs):
        calls.append(kwargs)
        return {'ok': True, 'unique': True, 'stop_required': False}
    monkeypatch.setattr(gates, 'lane_uniqueness_report', good)
    result = check(np.ones((2, 2)), np.ones((2, 2)), {'source': 'fixture'}, Path('not-read'), np.ones((2, 2), bool))
    assert result['unique']
    assert [c['phase'] for c in calls] == ['surface', 'dots']
    assert all(set(c) == {'phase', 'sample', 'registry_index'} for c in calls)


@pytest.mark.parametrize('mutation,expected', [
    ('banner', 'missing current BLOCKED'),
    ('approval', 'unauthorized promotion'),
    ('download', 'offers a submission binary'),
    ('escape', 'link escapes project'),
])
def test_site_checker_rejects_unsafe_entrypoint(monkeypatch, mutation, expected):
    # Read interception only: never rewrite actual scientific evidence or TIFFs.
    from check_site import check
    target = ROOT / 'docs/index.html'
    original = Path.read_text
    def altered(path, *args, **kwargs):
        text = original(path, *args, **kwargs)
        if path == target:
            if mutation == 'banner': text = text.replace('BLOCKED — DO NOT SUBMIT', 'Historical status')
            if mutation == 'approval': text += '<p>OK TO DOWNLOAD AND SUBMIT</p>'
            if mutation == 'download': text += '<a href="downloads/old.tif">Download submission</a>'
            if mutation == 'escape': text += '<a href="../../../../outside">Bad link</a>'
        return text
    monkeypatch.setattr(Path, 'read_text', altered)
    assert any(expected in error for error in check(ROOT, fresh_audit=False))


def test_surface_only_cannot_clear_final_release(monkeypatch):
    from check_uniqueness import check
    from gems57 import gates
    monkeypatch.setattr(gates, 'lane_uniqueness_report', lambda *a, **k: {'ok': True})
    result = check(np.ones((2, 2)), None, {}, Path('not-read'), np.ones((2, 2), bool))
    assert result['pending_final_dots']
    assert not result['unique']
    assert list(result['phases']) == ['surface']


def test_surface_stop_does_not_load_dots(monkeypatch):
    from check_uniqueness import check
    from gems57 import gates
    monkeypatch.setattr(gates, 'lane_uniqueness_report', lambda *a, **k: {'ok': False})
    def must_not_read():
        raise AssertionError('Blocked surface must stop before final-dot load')
    assert check(np.ones((2, 2)), must_not_read, {}, Path('not-read'), np.ones((2, 2), bool))['stop_required']


def test_retired_exporter_exits_blocked_without_importing_old_model():
    import subprocess
    import sys
    before = sorted((ROOT / 'docs/downloads').glob('*.tif'))
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_submission_session.py'),
                             '--field', 'fusion5050', '--label', 'must-not-generate'],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert 'BLOCKED — DO NOT SUBMIT' in result.stdout
    assert result.stderr == ''
    assert sorted((ROOT / 'docs/downloads').glob('*.tif')) == before
