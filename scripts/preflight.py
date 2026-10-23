#!/usr/bin/env python3
"""Fail-closed session preflight. This review does not implement a model/selector.

Exit 2 means blocked, NOT a failed test. No TIFF is produced by preflight.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
try:
    from restore_data import sha256_file as sha256
except ImportError:
    from restore_data import sha256


def verify_template(root=ROOT):
    pin = json.loads((root / 'registry/template_pin.json').read_text())
    return [name for name, expected in pin['files'].items()
            if not (root / 'vendor/gems57' / name).is_file()
            or sha256(root / 'vendor/gems57' / name) != expected]


def review(root=ROOT):
    blockers = []
    modified = verify_template(root)
    if modified:
        blockers.append('Shared template is missing/modified: ' + ', '.join(modified))
    lane = json.loads((root / 'registry/lane.json').read_text())
    if lane['status'] != 'assigned' or not lane['method_paragraph']:
        blockers.append('No explicit single-method lane assignment supplied.')
    integrity = []
    manifest = json.loads((root / 'registry/data_manifest.json').read_text())
    required = {'training_features', 'labels', 'existing_faults', 'sample_submission'}
    core_entries = [entry for entry in manifest['files'] if entry.get('group', 'core') == 'core']
    manifest_ok = {entry['id'] for entry in core_entries} == required and len(core_entries) == len(required)
    if not manifest_ok:
        blockers.append('Core data manifest must contain exactly the four required input identities.')
    for entry in core_entries:
        path = root / 'data' / entry['dest']
        integrity.append(dict(id=entry['id'], ok=path.is_file() and path.stat().st_size == entry['bytes'] and sha256(path) == entry['sha256']))
    core_ok = manifest_ok and all(row['ok'] for row in integrity)
    if not core_ok:
        blockers.append('One or more core data mirrors are missing or fail their hash/size pins.')
    # A transformed cache is distinct from the raw GeoTIFF. Do not rebuild it.
    cache = json.loads((root / 'registry/cache_manifest.json').read_text())
    cache_rows = cache.get('cache_files', [])
    cache_ok = bool(cache_rows) and all(
        (root / row['path']).is_file() and sha256(root / row['path']) == row['sha256'] for row in cache_rows)
    if not cache_ok:
        blockers.append('The template cached feature-stack bytes and hash manifest are unavailable locally.')
    witness = root / 'data/learning/registry-saturation-witness.tif'
    saturation = None
    grid_ok = all(any(row['id'] == name and row['ok'] for row in integrity)
                  for name in ['sample_submission', 'existing_faults'])
    if grid_ok and witness.is_file() and not modified:
        # Do not execute changed shared code before/after an integrity failure.
        from gems57.grid import load_grid
        from gems57.uniqueness import saturation_certificate
        witness_entry = next(e for e in json.loads((root / 'registry/learning_manifest.json').read_text())['files']
                             if e['id'] == witness.name)
        if sha256(witness) != witness_entry['sha256']:
            blockers.append('Registry witness hash mismatch; certificate invalid.')
        else:
            grid = load_grid(root / 'data')
            saturation = saturation_certificate(witness, grid.footprint, grid.catalogue,
                expected_grid=(grid.shape, grid.crs, grid.transform))
            saturation['witness_file'] = str(witness.relative_to(root))
            if saturation['universal_overlap_blocker']:
                blockers.append('Literal registry overlap rule blocks every nonempty candidate: a prior is positive throughout the allowed domain.')
    if saturation is None:
        blockers.append('Registry saturation witness has not been locally verified.')
    blockers.extend([
        'Full registry raster bytes have not been compared at either the pre-placement surface or final-dot stage.',
        'Historical lane results exist but no current candidate has passed the strict protocol and a paired current-best improvement gate.',
        'Historical model scripts and quarantined rasters exist; no current lane candidate or automatic slot selector is approved.',
        'Account-specific weekly remaining quota and submission-page receipts are unavailable; no slot selection authorized.'
    ])
    return dict(schema_version=1, reviewed_utc=datetime.now(timezone.utc).isoformat(),
        hypothesis=None, mechanism=None, non_fault_mimic=None,
        experiment_status='NOT RUN: prerequisites and literal uniqueness gate blocked',
        holdout=dict(evidence_class='HOLDOUT-DTI', evaluator_version='gems57-pooled-hide-v2',
            dti=None, ci95=None, withheld_positive_pixels=None, status='not run'),
        registry=dict(correlation=None, overlap=None, phase_surface='not run', phase_final_dots='not run',
            uniqueness_cleared=False, saturation_certificate=saturation),
        raster_sha256=None,
        validator=dict(status='not run: no candidate', no_nan_inside_footprint=None,
            values_in_0_1=None, crs_match=None, shape_match=None, transform_match=None),
        submission=dict(name=None, note='No candidate: missing lane/cache and literal registry saturation. No weekly slot used.'),
        gates=dict(core_manifest_valid=manifest_ok, core_mirror_integrity=integrity, core_inputs_available=core_ok,
            template_unmodified=not modified, cached_stack_available=cache_ok),
        blockers=blockers, verdict='negative', safe_to_download=False, safe_to_submit=False,
        promoted=False, selector_implemented=False, submission_slots_used=0, experiments_run=0,
        note='Negative preflight deliverable; not a geological negative result or a competition submission.')


def main():
    card = review()
    (ROOT / 'evidence/run_card.json').write_text(json.dumps(card, indent=2, allow_nan=False) + '\n')
    print(json.dumps(card, indent=2, allow_nan=False))
    return 2 if card['blockers'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
