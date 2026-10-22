#!/usr/bin/env python3
"""Offline internal-link, evidence-integrity and unsafe-download checks."""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        for name in ['href', 'src']:
            if attrs.get(name):
                self.links.append(attrs[name])


def check(root=ROOT):
    errors = []
    files = [root / 'index.html', *sorted((root / 'docs').rglob('*.html'))]
    for file in files:
        parser = Links()
        parser.feed(file.read_text())
        for url in parser.links:
            part = urlsplit(url)
            if part.scheme or part.netloc:
                continue
            dest = (file.parent / unquote(part.path)).resolve() if part.path else file
            if not dest.is_relative_to(root.resolve()):
                errors.append(f'{file}: link escapes project: {url}')
            elif not dest.exists():
                errors.append(f'{file}: broken link: {url}')
            elif part.fragment and dest.suffix == '.html':
                target = Links()
                target.feed(dest.read_text())
                if unquote(part.fragment) not in target.ids:
                    errors.append(f'{file}: missing fragment: {url}')
            if part.path.lower().endswith(('.tif', '.tiff', '.zip')):
                errors.append(f'{file}: unexpected candidate download in blocked-review site: {url}')
    for source in (root / 'docs/evidence').glob('*.json'):
        original = root / 'evidence' / source.name
        if source.read_bytes() != original.read_bytes():
            errors.append(f'Stale/altered published evidence: {source}')
    for source in (root / 'docs/registry').glob('*.json'):
        original = root / 'registry' / source.name
        if source.read_bytes() != original.read_bytes():
            errors.append(f'Stale/altered published registry: {source}')
    for file in (root / 'docs').rglob('*'):
        if file.suffix.lower() in {'.tif', '.tiff', '.zip'}:
            errors.append(f'Unapproved binary artifact under public docs: {file}')
    card = json.loads((root / 'docs/evidence/run_card.json').read_text())
    if card['safe_to_submit'] is not False or card['safe_to_download'] is not False or card['verdict'] != 'negative':
        errors.append('This site supports only an explicit blocked/negative verdict')
    if 'Current decision: do not submit' not in (root / 'index.html').read_text():
        errors.append('Root redirect must visibly retain blocked decision')
    for name in ['index.html', 'executive-summary.html']:
        if 'No verified submission TIFF is available' not in (root / 'docs' / name).read_text() and 'Current decision: do not submit' not in (root / 'docs' / name).read_text():
            errors.append(f'Missing visible blocked status in {name}')
    return errors


if __name__ == '__main__':
    errors = check()
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Site OK: internal links, copied evidence, blocked status and no TIFF/ZIP downloads.')
