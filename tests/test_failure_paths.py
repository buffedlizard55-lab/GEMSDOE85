import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import pytest
import restore_data
from preflight import review
from validate_submission import json_safe_metadata

ROOT = Path(__file__).resolve().parents[1]


def test_diagnostic_nan_metadata_serializes_without_changing_pixels():
    value = {'meta': {'nodata': float('nan')}, 'range_ok': False}
    safe = json_safe_metadata(value)
    assert safe['meta']['nodata'] == 'nan'
    assert safe['range_ok'] is False
    json.dumps(safe, allow_nan=False)
    assert value['meta']['nodata'] != value['meta']['nodata']


def test_empty_data_manifest_cannot_pass(tmp_path):
    shutil.copytree(ROOT / 'registry', tmp_path / 'registry')
    shutil.copytree(ROOT / 'vendor', tmp_path / 'vendor')
    (tmp_path / 'registry/data_manifest.json').write_text('{"files": []}')
    card = review(tmp_path)
    assert not card['gates']['core_manifest_valid']
    assert not card['gates']['core_inputs_available']
    assert card['verdict'] == 'negative'


def entry(payload):
    return dict(id='synthetic', repo='unused-in-network-mock', ref='unused-in-network-mock',
                path='sample.tif', dest='sample.tif', bytes=len(payload),
                sha256=hashlib.sha256(payload).hexdigest())


def test_failed_hash_never_replaces_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(restore_data, 'ROOT', tmp_path)
    directory = tmp_path / 'data'; directory.mkdir()
    dest = directory / 'sample.tif'; dest.write_bytes(b'existing')
    def fake_run(command, stdout, **kwargs):
        stdout.write(b'corrupt')
    monkeypatch.setattr(restore_data.subprocess, 'run', fake_run)
    with pytest.raises(ValueError, match='Size/hash mismatch'):
        restore_data.restore(entry(b'expected'), directory)
    assert dest.read_bytes() == b'existing'
    assert list(directory.iterdir()) == [dest]


def test_split_download_hash_and_atomic_replace(tmp_path, monkeypatch):
    monkeypatch.setattr(restore_data, 'ROOT', tmp_path)
    chunks = iter([b'first', b'second'])
    def fake_run(command, stdout, **kwargs):
        stdout.write(next(chunks))
    monkeypatch.setattr(restore_data.subprocess, 'run', fake_run)
    e = entry(b'firstsecond'); e.pop('path'); e['parts'] = ['first.part', 'second.part']
    directory = tmp_path / 'data'
    result = restore_data.restore(e, directory)
    assert result['status'] == 'restored'
    assert (directory / 'sample.tif').read_bytes() == b'firstsecond'
    assert len(list(directory.iterdir())) == 1
    assert restore_data.restore(e, directory)['status'] == 'present'


@pytest.mark.parametrize('path', ['../outside', '/tmp/outside', 'subdir/file.tif'])
def test_manifest_cannot_escape_target(tmp_path, path):
    e = entry(b'a'); e['dest'] = path
    with pytest.raises(ValueError, match='single local filename'):
        restore_data.restore(e, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_registry_old_submissions_under_data_remain_priors():
    from refresh_inventory import raster_role
    assert raster_role('data/scored/old-prediction.tif') == 'possible-prior-prediction'
    assert raster_role('docs/downloads/old-prediction.tif') == 'possible-prior-prediction'
    assert raster_role('data/bridge/sample_submission.tif') == 'input-or-derived-data'
