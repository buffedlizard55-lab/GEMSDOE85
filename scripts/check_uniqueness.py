#!/usr/bin/env python3
"""CLI for the unchanged literal shared gate, surface FIRST, dots only on PASS.

The retired positional CLI used >0.5 support and partial directory scans. That
cannot clear the requested any-registry-raster gate. No alternate policy here.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from preflight import verify_template


def check(surface, dots, index, sample, footprint):
    from gems57.gates import lane_uniqueness_report
    reports = {}
    for phase, array in [('surface', surface), ('dots', dots)]:
        if phase == 'dots' and array is None:
            return dict(unique=False, stop_required=False, pending_final_dots=True, phases=reports,
                        reason='Surface passed; final dots not supplied or cleared. No release authorized')
        # A lazy dot loader lets the surface check STOP before any final-dot read.
        if callable(array):
            array = array()
        reports[phase] = lane_uniqueness_report(array, footprint, sample=sample,
                                               phase=phase, registry_index=index)
        if not reports[phase]['ok']:
            return dict(unique=False, stop_required=True, phases=reports,
                        reason=f'{phase} gate did not clear; stopped without policy exemption')
    return dict(unique=True, stop_required=False, phases=reports,
                reason='Both literal shared checks passed; this alone does not authorize a slot')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--surface', type=Path, required=True, help='Continuous surface .npy, never a prior renamed as new')
    parser.add_argument('--dots', type=Path, help='Final-dot TIFF; omit for the pre-placement surface-only check')
    parser.add_argument('--registry-index', type=Path, required=True, help='Full shared public inventory JSON, not a directory subset')
    parser.add_argument('--sample', type=Path, default=ROOT / 'data/sample_submission.tif')
    args = parser.parse_args()
    changed = verify_template(ROOT)
    if changed:
        raise RuntimeError('Shared template changed; not executed: ' + ', '.join(changed))
    import numpy as np
    import rasterio
    with rasterio.open(args.sample) as src:
        footprint = np.isfinite(src.read(1))
        grid = src.shape, src.crs, src.transform
    def read_dots():
        with rasterio.open(args.dots) as src:
            if src.count != 1 or (src.shape, src.crs, src.transform) != grid:
                raise ValueError('Dots must be a single band on the exact sample grid')
            return src.read(1)
    result = check(np.load(args.surface, allow_pickle=False), read_dots if args.dots else None,
                   json.loads(args.registry_index.read_text()), args.sample, footprint)
    (ROOT / 'evidence/uniqueness_current.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['unique'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
