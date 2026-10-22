#!/usr/bin/env python3
"""Read-only release audit. No experiment, export, slot selection or policy exemptions."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def audit(root=ROOT):
    pin = json.loads((root / 'registry/template_pin.json').read_text())
    intact = all((root / 'vendor/gems57' / name).is_file() and
                 sha(root / 'vendor/gems57' / name) == digest
                 for name, digest in pin['files'].items())
    lane = json.loads((root / 'registry/lane.json').read_text())
    core_manifest = json.loads((root / 'registry/data_manifest.json').read_text())
    for identity in ['sample_submission', 'existing_faults']:
        entry = next(x for x in core_manifest['files'] if x['id'] == identity)
        path = root / 'data' / entry['dest']
        if path.stat().st_size != entry['bytes'] or sha(path) != entry['sha256']:
            raise ValueError('Reference integrity mismatch: ' + identity)
    witness = root / 'data/raw/learning/registry-saturation-witness.tif'
    manifest = json.loads((root / 'registry/learning_manifest.json').read_text())
    expected = next(x for x in manifest['files'] if x['id'] == witness.name)
    saturation = None
    # Verify shared bytes BEFORE importing/executing them.
    if intact and witness.is_file() and sha(witness) == expected['sha256']:
        from gems57.uniqueness import saturation_certificate
        with rasterio.open(root / 'data/sample_submission.tif') as ref:
            footprint = np.isfinite(ref.read(1))
            grid = ref.shape, ref.crs, ref.transform
        with rasterio.open(root / 'data/existing_faults.tif') as cat:
            if (cat.shape, cat.crs, cat.transform) != grid:
                raise ValueError('Catalogue grid mismatch')
            catalogue = cat.read(1) == 1
        saturation = saturation_certificate(witness, footprint, catalogue, expected_grid=grid)
        saturation['witness_file'] = str(witness.relative_to(root))
    rows = []
    with rasterio.open(root / 'data/sample_submission.tif') as ref:
        reference_grid = ref.shape, ref.crs, ref.transform
        footprint = np.isfinite(ref.read(1))
    for path in sorted((root / 'submissions').rglob('*.tif')):
        row = dict(file=str(path.relative_to(root)), sha256=sha(path))
        try:
            with rasterio.open(path) as src:
                a = src.read(1)
                match = (src.shape, src.crs, src.transform) == reference_grid
                row['checks'] = dict(single_band=src.count == 1, dtype_float32=src.dtypes[0] == 'float32',
                    crs_shape_transform_match=match,
                    all_finite_whole_grid=bool(np.isfinite(a).all()),
                    values_in_0_1_whole_grid=bool((np.isfinite(a) & (a >= 0) & (a <= 1)).all()),
                    no_nan_inside_footprint=bool(np.isfinite(a[footprint]).all()) if match else False,
                    values_in_0_1_inside_footprint=bool(((a[footprint] >= 0) & (a[footprint] <= 1)).all()) if match else False)
                row['format_ok_conservative'] = all(row['checks'].values())
                row['positive_pixels'] = int((np.isfinite(a) & (a > 0)).sum())
        except (OSError, ValueError, IndexError) as exc:
            row.update(error=str(exc), format_ok_conservative=False)
        # Historical bytes cannot be promoted by passing a format check.
        row['safe_to_submit'] = False
        rows.append(row)
    return dict(schema_version=1, hypothesis=None, mechanism=None, non_fault_mimic=None,
        experiment_status='NOT RUN — duplicate-stop preflight; no lane assigned',
        holdout=dict(label='HOLDOUT-DTI', evaluator_version=None, dti=None, ci95=None,
                     withheld_positive_pixels=None, status='not run this session'),
        registry=dict(uniqueness_cleared=False, correlation=None, overlap=None,
                      saturation_certificate=saturation, phase_surface='stopped before placement',
                      phase_final_dots='no new dots'),
        raster_sha256=None, validator=dict(status='no new raster; historical format diagnostics only'),
        historical_artifacts=rows, template_unmodified=intact, lane=lane,
        blockers=[('Literal any-raster overlap gate: saturated prior blocks every nonempty allowed candidate.'
                   if saturation and saturation['universal_overlap_blocker'] else 'Saturation witness unavailable or unverified; uniqueness remains blocked.'),
                  'No explicit assigned single-method paragraph.',
                  'Pinned transformed cache unavailable; no comparable current-best shared holdout receipt.',
                  'No authenticated organizer score receipts or account-specific remaining quota.'],
        submission=dict(name=None, note='Blocked: literal duplicate gate and missing lane/cache. Historical TIFFs quarantined; no slot used.'),
        safe_to_download=False, safe_to_submit=False, verdict='negative', promoted=False,
        experiments_run=0, submission_slots_used=0,
        reason='Negative protocol preflight, not a geological negative. No new unique TIFF was generated.')


def main():
    card = audit()
    (ROOT / 'evidence/run_card.json').write_text(json.dumps(card, indent=2, allow_nan=False) + '\n')
    print(json.dumps(card, indent=2, allow_nan=False))
    return 2  # A blocked release must never appear successful to automation.


if __name__ == '__main__':
    raise SystemExit(main())
