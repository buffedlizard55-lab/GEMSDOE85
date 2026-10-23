#!/usr/bin/env python3
"""Offline internal-link, evidence-integrity, and submission deliverable checks."""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
import zipfile
import numpy as np
import rasterio

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

    # Validate submission metadata and files
    sub_path = root / 'registry/submission.json'
    if not sub_path.exists():
        errors.append('Missing registry/submission.json')
        return errors
    sub = json.loads(sub_path.read_text())
    pri = sub.get('primary', {})
    fn = pri.get('filename')
    if not fn:
        errors.append('registry/submission.json missing primary filename')
        return errors
    tif_path = root / 'docs/downloads' / fn
    if not tif_path.exists():
        errors.append(f'Primary submission file missing from docs/downloads: {fn}')
        return errors

    # Check zip twin
    zip_fn = fn.replace('-zeros.tif', '-zeros.zip')
    zip_path = root / 'docs/downloads' / zip_fn
    if zip_path.exists():
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            if len(names) != 1 or names[0] != fn:
                errors.append(f'Zip {zip_path} should contain exactly {fn}, found: {names}')

    # Re-verify the GeoTIFF on disk
    try:
        with rasterio.open(tif_path) as ds:
            if ds.count != 1:
                errors.append(f'{fn}: expected single band, got {ds.count}')
            if ds.dtypes[0] != 'float32':
                errors.append(f'{fn}: expected float32, got {ds.dtypes[0]}')
            if (ds.height, ds.width) != (3730, 3292):
                errors.append(f'{fn}: expected (3730, 3292), got {(ds.height, ds.width)}')
            if ds.crs is None or ds.crs.to_epsg() != 32611:
                errors.append(f'{fn}: expected EPSG:32611, got {ds.crs}')
            if ds.nodata is not None:
                errors.append(f'{fn}: expected no nodata tag, got {ds.nodata}')
            arr = ds.read(1)
            if not np.isfinite(arr).all():
                errors.append(f'{fn}: expected all finite in zeros mode, found non-finite')
            if arr.min() < 0.0 or arr.max() > 1.0:
                errors.append(f'{fn}: values out of range [0, 1]: min={arr.min()}, max={arr.max()}')
            if (arr > 0).sum() == 0:
                errors.append(f'{fn}: expected positive predictions, found 0')
    except Exception as exc:
        errors.append(f'Failed to validate GeoTIFF {tif_path}: {exc}')

    # Note validation (<= 140 chars)
    note = sub.get('note', '')
    if len(note) > 140:
        errors.append(f'Submission note exceeds 140 characters: {len(note)}')

    # Check visible status on site
    for name in ['index.html', 'executive-summary.html']:
        page_text = (root / 'docs' / name).read_text()
        if fn not in page_text:
            errors.append(f'Missing primary download filename in docs/{name}')
        if 'FORMAT PASS ONLY — SUBMISSION BLOCKED' not in page_text:
            errors.append(f'Missing blocked-format-only banner in docs/{name}')
        if 'nan.tif' in page_text.lower():
            errors.append(f'Unsafe NaN-outside TIFF link exposed in docs/{name}')
        if 'NOT CLEARED FOR SUBMISSION' not in page_text and name == 'index.html':
            errors.append('Landing page does not clearly state candidate is not cleared for submission')

    return errors


if __name__ == '__main__':
    errors = check()
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Site OK: internal links, evidence integrity, candidate GeoTIFF format PASS, and explicit BLOCKED submission status.')
