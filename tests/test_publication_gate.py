"""Publication safety regression tests; synthetic cases are not geological experiments."""
import json
from pathlib import Path
import shutil

import pytest
from build_site import build
from check_site import check
from preflight import verify_template

ROOT = Path(__file__).resolve().parents[1]


def fixture_root(tmp_path):
    for directory in ['evidence', 'registry']:
        shutil.copytree(ROOT / directory, tmp_path / directory)
    (tmp_path / 'docs').mkdir()
    return tmp_path


def test_shared_bytes_are_unmodified():
    assert verify_template() == []


def test_builder_is_byte_deterministic_and_links_work():
    build()
    before = {str(p): p.read_bytes() for p in (ROOT / 'docs').rglob('*') if p.is_file()}
    build()
    after = {str(p): p.read_bytes() for p in (ROOT / 'docs').rglob('*') if p.is_file()}
    assert before == after
    assert check() == []


@pytest.mark.parametrize('key,value', [('verdict', 'promote'), ('safe_to_submit', True),
                                      ('safe_to_download', True)])
def test_builder_refuses_unsupported_promotion(tmp_path, key, value):
    root = fixture_root(tmp_path)
    path = root / 'evidence/run_card.json'
    card = json.loads(path.read_text())
    card[key] = value
    path.write_text(json.dumps(card))
    with pytest.raises(ValueError):
        build(root)
    assert not list((root / 'docs').glob('*.html'))


def test_builder_refuses_unapproved_binary(tmp_path):
    root = fixture_root(tmp_path)
    (root / 'docs/unapproved.tif').write_bytes(b'synthetic-test')
    with pytest.raises(ValueError, match='Quarantine'):
        build(root)


def test_checker_detects_reintroduced_download(tmp_path):
    root = fixture_root(tmp_path)
    build(root)
    shutil.copy(ROOT / 'index.html', root / 'index.html')
    (root / 'docs/unapproved.zip').write_bytes(b'synthetic-test')
    assert any('Unapproved binary' in e for e in check(root))
