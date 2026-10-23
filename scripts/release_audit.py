#!/usr/bin/env python3
"""Read-only, fail-closed release decision; never trains, exports or selects a slot.

Historical format PASS is diagnostic only. Shared tools stay byte-pinned.
Exit 2 means a blocked release; exit 1 means an audit error.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
sys.path.insert(0, str(ROOT / 'scripts'))
from preflight import review, verify_template
from restore_data import sha256_file as sha


def audit(root=ROOT):
    root = Path(root)
    card = review(root)
    # Stable input-derived report: rebuilding a site must not invent a fresh observation time.
    card.pop('reviewed_utc', None)
    card['schema_version'] = 2
    card['audit_version'] = 'gems85-release-audit-v2'
    rows = []
    inputs = card['gates']['core_mirror_integrity']
    reference_ok = any(r['id'] == 'sample_submission' and r['ok'] for r in inputs)
    intact = not verify_template(root)
    if intact and reference_ok:
        import numpy as np
        import rasterio
        from gems57.gates import format_report
        with rasterio.open(root / 'data/sample_submission.tif') as src:
            footprint = np.isfinite(src.read(1))
    files = sorted(set((root / 'submissions').rglob('*.tif')) |
                   set((root / 'docs/downloads').rglob('*.tif')))
    for path in files:
        row = dict(file=path.relative_to(root).as_posix(), sha256=sha(path),
                   safe_to_submit=False, classification='historical diagnostic; NOT a new submission')
        if intact and reference_ok:
            try:
                report = format_report(path, root / 'data/sample_submission.tif', footprint=footprint)
                report['path'] = row['file']
                with rasterio.open(path) as src, rasterio.open(root / 'data/sample_submission.tif') as ref:
                    a = src.read(1)
                    match = (src.shape, src.crs, src.transform) == (ref.shape, ref.crs, ref.transform)
                    checks = dict(
                        no_nan_inside_footprint=bool(np.isfinite(a[footprint]).all()) if match else False,
                        values_in_0_1=bool((np.isfinite(a) & (a >= 0) & (a <= 1)).all()),
                        crs_shape_transform_match=match)
                row.update(validator_output=report, checks=checks, format_ok=report['ok'])
            except (OSError, ValueError, IndexError) as exc:
                row.update(format_ok=False, error=str(exc))
        else:
            row.update(format_ok=False, error='Reference or shared-code integrity unavailable; not executed')
        rows.append(row)
    card['historical_artifacts'] = rows
    card['reason'] = 'Negative protocol preflight, not a geological negative. No new unique TIFF generated.'
    card['submission_name'] = None
    card['submission_note'] = card['submission']['note']
    card['validator_output'] = card['validator']
    return card


def main():
    card = audit()
    path = ROOT / 'evidence/run_card.json'
    path.write_text(json.dumps(card, indent=2, allow_nan=False) + '\n')
    print(json.dumps(card, indent=2, allow_nan=False))
    return 2 if not card['safe_to_submit'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
