"""Byte verification fails closed; no network or competition data needed."""
import hashlib
import pytest
from scripts.audit_v2_inputs import inspect_entry


def entry():
    return dict(id='fixture', dest='fixture.bin', bytes=3,
                sha256=hashlib.sha256(b'abc').hexdigest())


def test_missing_is_not_verified(tmp_path):
    assert inspect_entry(tmp_path, entry(), ['data'])['status'] == 'MISSING'


def test_checks_all_local_copies(tmp_path):
    for directory, content in [('data', b'abc'), ('bridge', b'abd')]:
        (tmp_path / directory).mkdir()
        (tmp_path / directory / 'fixture.bin').write_bytes(content)
    assert inspect_entry(tmp_path, entry(), ['data'])['status'] == 'VERIFIED'
    assert inspect_entry(tmp_path, entry(), ['data', 'bridge'])['status'] == 'MISMATCH'
    wrong_size = dict(entry(), bytes=4)
    assert inspect_entry(tmp_path, wrong_size, ['data'])['status'] == 'MISMATCH'


def test_rejects_escaping_destinations(tmp_path):
    for dest in ['../fixture.bin', '/fixture.bin']:
        with pytest.raises(ValueError):
            inspect_entry(tmp_path, dict(entry(), dest=dest), ['data'])
