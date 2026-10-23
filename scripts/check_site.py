#!/usr/bin/env python3
"""Offline internal-link, evidence-integrity, and submission deliverable checks."""
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

    # Evidence and registry consistency checks
    for source in (root / 'docs/evidence').glob('*.json'):
        original = root / 'evidence' / source.name
        if original.exists() and source.read_bytes() != original.read_bytes():
            errors.append(f'Stale/altered published evidence: {source}')
    for source in (root / 'docs/registry').glob('*.json'):
        original = root / 'registry' / source.name
        if original.exists() and source.read_bytes() != original.read_bytes():
            errors.append(f'Stale/altered published registry: {source}')

    # A format receipt cannot authorize a blocked historical submission.
    card = json.loads((root / 'evidence/run_card.json').read_text())
    if card.get('safe_to_submit') is not False or card.get('verdict') != 'negative':
        errors.append('No implemented selector can authorize promotion; expected blocked run card.')
    for file in files:
        text = file.read_text()
        parser = Links(); parser.feed(text)
        if 'BLOCKED — DO NOT SUBMIT' not in text:
            errors.append(f'Missing blocked status: {file}')
        if 'OK TO DOWNLOAD AND SUBMIT' in text or 'ready to upload' in text.lower():
            errors.append(f'Contradictory release claim: {file}')
        for url in parser.links:
            if urlsplit(url).path.lower().endswith(('.tif', '.tiff', '.zip')):
                errors.append(f'Blocked page links prediction bytes: {file}: {url}')
    return errors


if __name__ == '__main__':
    errors = check()
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Site OK: blocked status, links and evidence consistency verified; no submission authorized.')
