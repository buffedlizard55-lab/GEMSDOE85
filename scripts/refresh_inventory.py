#!/usr/bin/env python3
"""Snapshot owner repositories at immutable commits. Inventory != uniqueness clearance.

Only metadata is fetched. All prediction TIFFs (including old/quarantined files) are
retained conservatively; missing repositories, truncated trees and API failures are
explicit errors. No inference about live Pages contents or organizer acceptance.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
# Names as supplied in the user's URLs; no inferred GEMSDOE1/5/6 aliases.
PREFIXED = {5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 55, 56, 57, 58, 59, 60, 61, 62}
NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
           21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
           41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60,
           61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80,
           81, 82, 83, 84, 85, 86, 87, 88]


def raster_role(path):
    # Conservative possible-prior classification. These labels are NOT clearance.
    core_names = {'existing_faults.tif', 'labels.tif', 'sample_submission.tif',
                  'training_features.tif', 'gems-geodawn-numerical-features.tif', 'example_submission.tif'}
    is_input = Path(path).name in core_names or path.startswith(('data/external/', 'vendor/'))
    return 'input-or-derived-data' if is_input else 'possible-prior-prediction'


def api(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', endpoint], timeout=90, stderr=subprocess.PIPE))


def inspect(number):
    name = 'GEMSDOE' if number == 1 else f'{number}GEMSDOE' if number in PREFIXED else f'GEMSDOE{number}'
    repo = f'buffedlizard55-lab/{name}'
    result = dict(repository=repo, pages_url=f'https://buffedlizard55-lab.github.io/{name}/', rasters=[], cache_files=[])
    try:
        info = api(f'repos/{repo}')
        ref = api(f"repos/{repo}/commits/{info['default_branch']}")['sha']
        tree = api(f'repos/{repo}/git/trees/{ref}?recursive=1')
        result.update(commit=ref, tree_sha=tree['sha'], truncated=tree.get('truncated', False))
        if tree.get('truncated'):
            raise ValueError('Truncated tree; cannot claim inventory completeness')
        for obj in tree['tree']:
            p = obj['path']
            if obj['type'] != 'blob':
                continue
            if p.lower().endswith(('.npy', '.npz')):
                result['cache_files'].append(dict(path=p, bytes=obj.get('size'), blob_sha=obj['sha']))
            if not p.lower().endswith(('.tif', '.tiff')):
                continue
            result['rasters'].append(dict(path=p, bytes=obj.get('size'), git_blob_sha=obj['sha'],
                role=raster_role(p),
                url=f'https://github.com/{repo}/blob/{ref}/{p}'))
        result['status'] = 'metadata-inspected'
    except (subprocess.SubprocessError, ValueError, KeyError) as exc:
        result.update(status='error', error=str(exc))
    return result


def main():
    results = list(ThreadPoolExecutor(8).map(inspect, NUMBERS))
    output = dict(checked_utc=datetime.now(timezone.utc).isoformat(),
        scope='Public default-branch Git trees of the user-listed repositories. Not PR branches or private submissions. TIFF bytes not compared.',
        complete_accessible_scan=False, uniqueness_cleared=False,
        repositories=results, errors=[r['repository'] for r in results if r['status'] == 'error'])
    (ROOT / 'registry/public_inventory.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(dict(repositories=len(results), errors=output['errors'],
        possible_priors=sum(r['role']=='possible-prior-prediction' for row in results for r in row['rasters'])), indent=2))


if __name__ == '__main__':
    main()
