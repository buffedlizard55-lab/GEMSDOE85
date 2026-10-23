#!/usr/bin/env python3
"""Restore pinned public GitHub mirrors. Integrity is NOT organizer authentication."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


sha256_file = sha256


def restore(entry, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    relative = Path(entry['dest'])
    if relative.is_absolute() or '..' in relative.parts or relative.name != str(relative):
        raise ValueError('Manifest destination must be a single local filename')
    dest = directory / relative
    if dest.is_file() and sha256(dest) == entry['sha256']:
        return dict(id=entry['id'], path=str(dest.relative_to(ROOT)), sha256=entry['sha256'], bytes=dest.stat().st_size, status='cached')
    # Staging is on the same filesystem. A failed fetch never publishes corrupt data.
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        assembled = Path(tmp) / 'assembled'
        with assembled.open('wb') as output:
            for part in entry.get('parts', [entry.get('path')]):
                if not part:
                    raise ValueError('manifest entry lacks a path')
                fragment = Path(tmp) / 'fragment'
                with fragment.open('wb') as stream:
                    subprocess.run(['gh', 'api', f"repos/{entry['repo']}/contents/{part}?ref={entry['ref']}",
                                    '-H', 'Accept: application/vnd.github.raw'], stdout=stream, check=True, timeout=300)
                with fragment.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1 << 20), b''):
                        output.write(chunk)
                fragment.unlink()
        if assembled.stat().st_size != entry['bytes'] or sha256(assembled) != entry['sha256']:
            raise ValueError(f"Size/hash mismatch for {entry['id']}; not restored")
        assembled.replace(dest)
    return dict(id=entry['id'], path=str(dest.relative_to(ROOT)), sha256=entry['sha256'], bytes=dest.stat().st_size, status='restored')


def main():
    manifest = json.loads((ROOT / 'registry/data_manifest.json').read_text())
    results = []
    for entry in manifest['files']:
        results.append(restore(entry, ROOT / 'data/raw'))
        print(entry['id'], results[-1]['status'], flush=True)
    (ROOT / 'evidence/data_restore.json').write_text(json.dumps(dict(
        provenance='Owner mirrors; hash-pinned, not organizer-authenticated', files=results), indent=2) + '\n')


if __name__ == '__main__':
    main()
