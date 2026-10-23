#!/usr/bin/env python3
"""Check a TIFF with the shared validators. Format PASS never means submit-ready."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from gems57.gates import format_report, sha256
from gems57.grid import load_grid, SHA256_SAMPLE_SUBMISSION, SHA256_EXISTING_FAULTS
from gems57.validate import validate


def _reference_dir() -> Path:
    """The pinned grid lives in data/bridge (gems57.grid.DATA_DIR); data/raw is the legacy
    restore target. Resolve either, fail loudly if neither is present."""
    for candidate in (ROOT / 'data/bridge', ROOT / 'data/raw'):
        if (candidate / 'sample_submission.tif').is_file() and (candidate / 'existing_faults.tif').is_file():
            return candidate
    raise ValueError('no pinned reference grid found in data/bridge or data/raw')


def check(path):
    ref = _reference_dir()
    sample = ref / 'sample_submission.tif'
    cat = ref / 'existing_faults.tif'
    if sha256(sample) != SHA256_SAMPLE_SUBMISSION or sha256(cat) != SHA256_EXISTING_FAULTS:
        raise ValueError('Reference grid/catalogue integrity mismatch')
    grid = load_grid(ref)
    template = format_report(path, sample, footprint=grid.footprint)
    local = validate(path, grid.footprint)
    return dict(format_ok=bool(template['ok'] and local['all_checks_passed']), template=template,
        local=local, safe_to_submit=False, organizer_accepted=False,
        reason='Format-only diagnostic. Does not establish geological performance, uniqueness, slot approval, or organizer acceptance.')


def json_safe_metadata(value):
    """Represent invalid numeric metadata explicitly; never alter raster pixels."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: json_safe_metadata(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe_metadata(item) for item in value]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tif', type=Path)
    args = parser.parse_args()
    try:
        report = check(args.tif)
    except (OSError, ValueError) as exc:
        report = dict(format_ok=False, safe_to_submit=False, error=str(exc))
    print(json.dumps(json_safe_metadata(report), indent=2, allow_nan=False))
    return 0 if report['format_ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
