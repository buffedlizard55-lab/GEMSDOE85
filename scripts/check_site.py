#!/usr/bin/env python3
"""Offline internal-link, evidence-integrity and submission-readiness checks."""
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
    files = [f for f in [root / 'index.html', *sorted((root / 'docs').rglob('*.html'))] if f.exists()]
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

    sub_path = root / 'registry' / 'submission.json'
    if sub_path.exists():
        sub = json.loads(sub_path.read_text())
        prim = sub.get('primary', {})
        fn = prim.get('filename', '')
        tif_path = root / 'docs' / 'downloads' / fn
        if not fn or not tif_path.exists():
            errors.append(f'Missing advertised primary download TIFF: {tif_path}')
        if not (0 < len(sub.get('note', '')) <= 140):
            errors.append(f'Submission note exceeds 140 chars: {len(sub.get("note", ""))}')
        for name in ['index.html', 'executive-summary.html']:
            html = (root / 'docs' / name).read_text()
            if 'OK TO DOWNLOAD' not in html and 'DO NOT DOWNLOAD' not in html:
                errors.append(f'Missing visible download status banner in docs/{name}')
            if fn and fn not in html:
                errors.append(f'Primary filename {fn} not shown in docs/{name}')
    else:
        for name in ['index.html', 'executive-summary.html']:
            html = (root / 'docs' / name).read_text()
            if 'No verified submission TIFF is available' not in html and 'Current decision: do not submit' not in html:
                errors.append(f'Missing visible blocked status in {name}')
    return errors


if __name__ == '__main__':
    errors = check()
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Site OK: internal links, fragments, and submission status verified.')
