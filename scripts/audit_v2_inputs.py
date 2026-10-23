#!/usr/bin/env python3
"""Offline byte inventory, not a candidate approval or an R0 rebuild.

Run: python scripts/audit_v2_inputs.py > evidence/v2-input-audit.json
Missing files are reported, never downloaded or approximated. Geometry is read
only after both the parent and catalogue pass their recorded byte pins.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inspect_entry(root, entry, directories):
    dest = Path(entry['dest'])
    if dest.is_absolute() or '..' in dest.parts:
        raise ValueError('Manifest destination escapes input root')
    copies = []
    for directory in directories:
        path = root / directory / dest
        if not path.is_file():
            continue
        digest = sha256(path)
        size = path.stat().st_size
        copies.append(dict(path=str(path.relative_to(root)), sha256=digest,
                           bytes=size, matches_pin=(digest == entry['sha256']
                                                    and size == entry['bytes'])))
    status = ('MISSING' if not copies else
              'VERIFIED' if all(c['matches_pin'] for c in copies) else 'MISMATCH')
    return dict(id=entry['id'], expected_sha256=entry['sha256'], status=status, copies=copies)


def audit(root=ROOT):
    manifests = {}
    for name, directories in [
        ('data_manifest', ['data', 'data/raw', 'data/bridge']),
        ('learning_manifest', ['data/learning', 'data/raw', 'data/registry_rasters']),
    ]:
        entries = json.loads((root / 'registry' / f'{name}.json').read_text())['files']
        rows = [inspect_entry(root, e, directories) for e in entries]
        manifests[name] = dict(files=rows, counts={
            s: sum(r['status'] == s for r in rows)
            for s in ['VERIFIED', 'MISSING', 'MISMATCH']})
    parent = next(r for r in manifests['learning_manifest']['files'] if r['id'] == 'h33-b2.tif')
    cat = next(r for r in manifests['data_manifest']['files'] if r['id'] == 'existing_faults')
    geometry = None
    if parent['status'] == cat['status'] == 'VERIFIED':
        import numpy as np
        import rasterio
        from scipy.ndimage import distance_transform_edt
        with rasterio.open(root / parent['copies'][0]['path']) as ds:
            a = ds.read(1)
            grid = (ds.shape, ds.crs, ds.transform)
        with rasterio.open(root / cat['copies'][0]['path']) as ds:
            if grid != (ds.shape, ds.crs, ds.transform):
                raise ValueError('Parent/catalogue grids differ')
            catalogue = ds.read(1) == 1
        distance = distance_transform_edt(~catalogue)
        dots = a > 0
        geometry = dict(n_dots=int(dots.sum()), mass=float(a.sum()),
                        values=np.unique(a).tolist(), catalogue_mass=float(a[catalogue].sum()),
                        min_catalogue_distance_px=float(distance[dots].min()),
                        dots_distance_lt3=int((dots & (distance < 3)).sum()),
                        dots_distance_le3=int((dots & (distance <= 3)).sum()))
    parent_rebuilt = False
    variants_built = 0
    try:
        import sys
        if str(root / 'src') not in sys.path:
            sys.path.insert(0, str(root / 'src'))
        from gems85 import r0_lineage as RL
        if all(p.is_file() for p in RL.PATHS.values()):
            RL.verify_pins()
            L = RL.rebuild(verify_against_pinned_files=True)
            parent_rebuilt = (L.counts() == {'skeleton': 121131, 'd28': 44090, 'solo': 40199, 'r0': 37654})
        ledger = root / 'ledger' / 'submissions.csv'
        if ledger.is_file():
            import csv
            variants_built = sum(1 for r in csv.DictReader(ledger.open()) if r.get('status') == 'BUILT')
    except Exception:
        pass
    return dict(schema_version=1, purpose='Input inventory and R0 lineage verification',
                git_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                manifests=manifests, restored_parent_geometry=geometry,
                parent_rebuilt=parent_rebuilt, variants_built=variants_built)


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2, allow_nan=False))
