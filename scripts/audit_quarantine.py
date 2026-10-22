#!/usr/bin/env python3
"""Inspect historical zero-filled rasters using pinned shared tools, not private validators.

Diagnostics only: never writes predictions, promotes, or uses a submission slot.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from gems57.grid import load_grid
from gems57.validate import validate
from gems57.uniqueness import dot_overlap
from preflight import verify_template
from restore_data import sha256_file


def audit(root=ROOT):
    import numpy as np
    import rasterio
    if verify_template(root):
        raise ValueError('Shared byte integrity failed')
    grid = load_grid(root / 'data')
    witness = root / 'data/learning/registry-saturation-witness.tif'
    entry = next(x for x in json.loads((root / 'registry/learning_manifest.json').read_text())['files']
                 if x['id'] == witness.name)
    if sha256_file(witness) != entry['sha256']:
        raise ValueError('Witness integrity failed')
    with rasterio.open(witness) as ds:
        prior = ds.read(1)
        if (ds.shape, ds.crs, ds.transform) != (grid.shape, grid.crs, grid.transform):
            raise ValueError('Witness grid mismatch')
    prior_dots = np.isfinite(prior) & (prior > 0) & grid.footprint
    rows = []
    for path in sorted((root / 'submissions').rglob('*-zeros.tif')):
        result = validate(path, grid.footprint, grid.catalogue)
        with rasterio.open(path) as ds:
            dots = ds.read(1) > 0
        # Literal forward overlap, without coverage/chance correction.
        overlap = dot_overlap(dots, prior_dots, radius_px=3)
        rows.append(dict(path=path.relative_to(root).as_posix(), sha256=sha256_file(path),
                         format=result, literal_overlap_vs_witness=overlap,
                         uniqueness_cleared=False, safe_to_submit=False))
    return dict(evidence_class='FORMAT/REGISTRY-MEASUREMENT, not HOLDOUT-DTI',
                witness_sha256=entry['sha256'], artifacts=rows,
                verdict='negative', experiments_run=0, submission_slots_used=0)


if __name__ == '__main__':
    receipt = audit()
    (ROOT / 'evidence/quarantine_audit.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(f"Audited {len(receipt['artifacts'])} historical zero-filled TIFFs; no promotion.")
