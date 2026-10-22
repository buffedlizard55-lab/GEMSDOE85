#!/usr/bin/env python3
"""Offline site checks for the CURRENT contract (candidate-download site).

Rewritten in session arena/22847afd (IR-85-012).  The previous version enforced
the original blocked-state contract ("no TIFF downloads anywhere, verdict must
be negative") -- the exact inverse of the merged GEO-Pb/CTXFUS site, the same
stale contract already quarantined for tests in IR-85-004.  It therefore failed
on every legitimate page in this repository.  This version keeps the parts of
the original intent that still protect the user -- internal links must resolve,
published evidence must not drift silently -- and adds the checks that matter
for a download site:

  * every internal link in root index.html + docs/**/*.html resolves;
  * docs/evidence/run_card.json is byte-identical to evidence/run_card.json,
    and docs/downloads/run_card.json carries the same raster sha256;
  * the primary download advertised in registry/submission.json exists under
    docs/downloads/, its sha256 matches, and all recorded checks passed;
  * the visible banner agrees with the run card: a "promote" verdict requires
    the OK-TO-SUBMIT banner and a passing validator, anything else requires a
    visible DO NOT SUBMIT.
"""
from html.parser import HTMLParser
import hashlib
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


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


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

    # published run card must not drift from the evidence copy
    pub_card = root / 'docs/evidence/run_card.json'
    ev_card = root / 'evidence/run_card.json'
    if pub_card.exists() and pub_card.read_bytes() != ev_card.read_bytes():
        errors.append('docs/evidence/run_card.json differs from evidence/run_card.json')
    card = json.loads(ev_card.read_text())
    dl_card_path = root / 'docs/downloads/run_card.json'
    if dl_card_path.exists():
        dl_card = json.loads(dl_card_path.read_text())
        if dl_card.get('raster_sha256') != card.get('raster_sha256'):
            errors.append('docs/downloads/run_card.json sha256 != evidence run card')

    # primary download: exists, hash matches the registry, checks all passed
    sub = json.loads((root / 'registry/submission.json').read_text())
    pri = sub['primary']
    tif = root / 'docs/downloads' / pri['filename']
    if not tif.exists():
        errors.append(f"primary download missing: {pri['filename']}")
    elif _sha256(tif) != pri['sha256']:
        errors.append('primary download sha256 != registry/submission.json')
    if not all(pri['checks'].values()):
        errors.append('registry/submission.json primary has a failing check')
    if card.get('raster_sha256') != pri['sha256']:
        errors.append('run card raster_sha256 != primary download')

    # visible banner must agree with the verdict -- the user must never have to guess
    index_text = (root / 'docs/index.html').read_text()
    verdict = str(card.get('verdict', ''))
    if verdict.startswith('promote'):
        if 'OK TO DOWNLOAD AND SUBMIT' not in index_text:
            errors.append('verdict=promote but no OK-TO-SUBMIT banner on docs/index.html')
    elif 'DO NOT SUBMIT' not in index_text:
        errors.append(f'verdict={verdict!r} but no DO NOT SUBMIT banner on docs/index.html')
    return errors


if __name__ == '__main__':
    errors = check()
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Site OK: links resolve, run card mirrored, primary download hash- and '
          'check-verified, banner agrees with verdict.')
