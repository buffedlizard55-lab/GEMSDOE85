#!/usr/bin/env python3
"""Reproduce local measurements; never turn the sample or a prior into a submission."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
sys.path.insert(0, str(ROOT / 'scripts'))
from gems57.grid import load_grid
from gems57.uniqueness import saturation_certificate
from gems57.gates import format_report
from restore_data import sha256


def main():
    manifest = json.loads((ROOT / 'registry/data_manifest.json').read_text())
    records = []
    for entry in manifest['files']:
        path = ROOT / 'data/raw' / entry['dest']
        if sha256(path) != entry['sha256'] or path.stat().st_size != entry['bytes']:
            raise ValueError(f"Input integrity failed: {entry['id']}")
        with rasterio.open(path) as src:
            records.append(dict(id=entry['id'], sha256=entry['sha256'], bytes=path.stat().st_size,
                shape=list(src.shape), count=src.count, crs=str(src.crs),
                transform=list(src.transform)[:6], bands=list(src.descriptions)))
    g = load_grid(ROOT / 'data/raw')
    with rasterio.open(ROOT / 'data/raw/training_features.tif') as src:
        if (src.shape, src.crs, src.transform) != (g.shape, g.crs, g.transform):
            raise ValueError('Feature grid mismatch')
        missing = []
        for band in range(1, src.count + 1):
            a = src.read(band, masked=True)
            bad = np.ma.getmaskarray(a) | ~np.isfinite(a.data)
            missing.append(dict(band=band, missing_in_footprint=int((bad & g.footprint).sum())))
    receipt = dict(evidence_class='INPUT-MEASUREMENT', organizer_authenticated=False,
        files=records, footprint_pixels=int(g.footprint.sum()), catalogue_pixels=int(g.catalogue.sum()),
        labels_identical_to_catalogue=sha256(ROOT / 'data/raw/labels.tif') == sha256(ROOT / 'data/raw/existing_faults.tif'),
        feature_missing=missing, sample_used_as_prediction=False)
    (ROOT / 'evidence/input_audit.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    witness = ROOT / 'data/raw/learning/registry-saturation-witness.tif'
    if witness.exists():
        certificate = saturation_certificate(witness, g.footprint, g.catalogue,
            expected_grid=(g.shape, g.crs, g.transform))
        certificate['witness_file'] = str(witness.relative_to(ROOT))
        certificate['source'] = 'https://github.com/buffedlizard55-lab/17GEMSDOE/blob/6fc71d19d49dca4960d5434bd81b6dd06fcc030a/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif'
        certificate['protocol_changed'] = False
        (ROOT / 'evidence/saturation_certificate.json').write_text(json.dumps(certificate, indent=2, allow_nan=False) + '\n')
    prior = ROOT / 'data/raw/learning/h33-b2.tif'
    if prior.exists():
        entries = json.loads((ROOT / 'registry/learning_manifest.json').read_text())['files']
        pin = next(e for e in entries if e['id'] == prior.name)
        if sha256(prior) != pin['sha256']:
            raise ValueError('H33 educational artifact hash mismatch')
        with rasterio.open(prior) as src:
            a = src.read(1)
        from scipy.ndimage import distance_transform_edt
        distance = distance_transform_edt(~g.catalogue)
        audit = dict(evidence_class='ARTIFACT-MEASUREMENT',
            provenance='Owner artifact; education only. No organizer submission-page receipt supplied.',
            sha256=sha256(prior), positive_pixels=int((a > 0).sum()),
            binary_values_only=bool(np.isin(a, [0, 1]).all()),
            on_catalogue=int(((a > 0) & g.catalogue).sum()),
            within_2px_of_catalogue=int(((a > 0) & (distance <= 2)).sum()),
            template_report=format_report(prior, ROOT / 'data/raw/sample_submission.tif', footprint=g.footprint))
        audit['template_report']['path'] = str(prior.relative_to(ROOT))
        (ROOT / 'evidence/h33_learning_audit.json').write_text(json.dumps(audit, indent=2, allow_nan=False) + '\n')
    print('Inputs and available educational artifacts audited; no candidate raster created.')


if __name__ == '__main__':
    main()
