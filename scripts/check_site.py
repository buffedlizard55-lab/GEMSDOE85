#!/usr/bin/env python3
"""Check links, published evidence, current audit identity and blocked UI contracts.

A successful site check means the blocked status is truthful, NOT slot approval.
"""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BANNER = 'BLOCKED — DO NOT SUBMIT'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.blocked = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.blocked |= attrs.get('data-release-status') == 'blocked'
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        for name in ['href', 'src']:
            if attrs.get(name):
                self.links.append(attrs[name])


def check(root=ROOT, *, fresh_audit=True):
    root = Path(root).resolve()
    errors = []
    for file in [root / 'index.html', *sorted((root / 'docs').rglob('*.html'))]:
        text = file.read_text()
        parser = Links()
        parser.feed(text)
        if not parser.blocked or BANNER not in text:
            errors.append(f'{file}: missing current BLOCKED status')
        primary = file.parent == root / 'docs' and file.name in (
            'index.html', 'executive-summary.html', 'method.html', 'data.html')
        if primary and ('OK TO DOWNLOAD AND SUBMIT' in text or 'ready to upload' in text.lower()):
            errors.append(f'{file}: unauthorized promotion text')
        for url in parser.links:
            part = urlsplit(url)
            if part.scheme or part.netloc:
                continue
            dest = (file.parent / unquote(part.path)).resolve() if part.path else file
            if not dest.is_relative_to(root):
                errors.append(f'{file}: link escapes project: {url}')
            elif not dest.exists():
                errors.append(f'{file}: broken link: {url}')
            elif part.fragment and dest.suffix == '.html':
                target = Links()
                target.feed(dest.read_text())
                if unquote(part.fragment) not in target.ids:
                    errors.append(f'{file}: missing fragment: {url}')
            if primary and part.path.lower().endswith(('.tif', '.zip')):
                errors.append(f'{file}: blocked primary page offers a submission binary')
    for group in ('evidence', 'registry'):
        for source in (root / group).glob('*.json'):
            public = root / 'docs' / group / source.name
            if not public.is_file() or source.read_bytes() != public.read_bytes():
                errors.append(f'Missing/stale published {group}: {source.name}')
    card = json.loads((root / 'evidence/run_card.json').read_text())
    if card.get('safe_to_submit') is not False or card.get('verdict') != 'negative':
        errors.append('Current blocked review must not promote a historical raster')
    if card.get('raster_sha256') is not None or card.get('experiments_run') != 0:
        errors.append('Preflight must not fabricate a new raster or experiment')
    if len(card.get('submission_note', '')) > 140:
        errors.append('Submission note exceeds 140 characters')
    public_card = root / 'docs/downloads/run_card.json'
    if not public_card.exists() or public_card.read_bytes() != (root / 'evidence/run_card.json').read_bytes():
        errors.append('Download run card differs from current decision')
    if fresh_audit:
        from release_audit import audit
        if audit(root) != card:
            errors.append('Current run card does not match a fresh byte-level release audit')
    return errors


if __name__ == '__main__':
    errors = check()
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Site OK: links, evidence identity and BLOCKED release status verified; no submission authorized.')
