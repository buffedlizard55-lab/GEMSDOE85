"""Integration and contract tests for the GEMSDOE85 submission and site."""
from pathlib import Path
import json
import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]

import importlib.util

def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

build_site = _load_module("build_site_main", ROOT / "scripts/build_site.py")
build = build_site.build

check_site = _load_module("check_site_main", ROOT / "scripts/check_site.py")
check = check_site.check


def test_site_generation_and_validation():
    """Verify site generation and comprehensive check_site validation."""
    assert build() == 0
    errors = check(ROOT)
    assert errors == [], f"check_site reported errors: {errors}"


def test_submission_deliverable_and_format_contracts():
    """Verify the primary submission GeoTIFF passes all format and metric contracts."""
    sub = json.loads((ROOT / "registry/submission.json").read_text())
    pri = sub["primary"]
    fn = pri["filename"]
    tif_path = ROOT / "docs/downloads" / fn
    assert tif_path.exists(), f"Primary submission file missing: {tif_path}"

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1, "Must be single-band"
        assert ds.dtypes[0] == "float32", "Must be float32"
        assert (ds.height, ds.width) == (3730, 3292), "Dimensions must be 3730x3292"
        assert ds.crs is not None and ds.crs.to_epsg() == 32611, "CRS must be EPSG:32611"
        assert ds.nodata is None, "No nodata tag permitted in all-finite zeros mode"
        a = ds.read(1)
        assert np.isfinite(a).all(), "All values must be finite (no NaN, no Inf)"
        assert a.min() >= 0.0 and a.max() <= 1.0, "Values must be strictly in [0, 1]"
        assert (a > 0).sum() == 90000, f"Expected 90,000 emitted dots, got {(a > 0).sum()}"

    # Catalogue distance guarantee (zero within 2px of catalogue)
    labels_path = ROOT / "data/labels.tif"
    if labels_path.exists():
        with rasterio.open(labels_path) as s:
            cat = s.read(1) >= 1
        from scipy import ndimage as ndi
        halo = ndi.binary_dilation(cat, np.ones((3, 3), bool), iterations=2)
        assert not ((a > 0) & halo).any(), "Zero mass permitted within 2px of mapped catalogue"


def test_run_card_and_note_contracts():
    """Verify run card fields, note length limit, and verdict."""
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert card["verdict"] == "promote-as-candidate"
    assert card["raster_sha256"] == "ba33ea18936e6324037457e1ff5070d8e879b7b29a25b4ae2c0003bc509a567f"
    ho = card["holdout_dti"]
    assert ho["label"] == "HOLDOUT-DTI"
    assert ho["evaluator_version"] == "gems85-holdout-v1.0.0"
    assert ho["value"] > 0.09
    assert len(ho["ci95"]) == 2
    assert ho["ci95"][0] < ho["value"] < ho["ci95"][1]
    assert ho["n_withheld_positives"] == 60988

    sub = json.loads((ROOT / "registry/submission.json").read_text())
    assert len(sub["note"]) <= 140, f"Note exceeds 140 chars: {len(sub['note'])}"


def test_source_register_does_not_claim_organizer_score_receipt():
    """Verify source classifications distinguish local holdouts from official receipts."""
    j = json.loads((ROOT / "registry/sources.json").read_text())
    assert next(x for x in j["sources"] if x["id"] == "organizer-submissions")["status"] == "redirected to login"
    assert next(x for x in j["sources"] if x["id"] == "h33-owner-page")["class"] == "owner research, not official score receipt"
