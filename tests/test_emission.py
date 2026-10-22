"""Emission + submission-writer invariants.

These are the tests that stand between this repo and a second "Predicted values must be in
range [0, 1]" rejection.  They run without the data cache (synthetic grids) so CI stays cheap,
plus one opt-in test that checks the real shipped artifact when it is present.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from gems85 import emission, submission
from gems85.grid import HEIGHT, WIDTH

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- emission
def _toy(h=120, w=160, seed=0):
    rng = np.random.default_rng(seed)
    field = rng.random((h, w)).astype(np.float32)
    field[40:44, :] += 3.0                       # a strong horizontal "fault"
    fp = np.zeros((h, w), bool)
    fp[5:-5, 5:-5] = True
    cat = np.zeros((h, w), bool)
    cat[80:82, 20:140] = True                    # a mapped fault to exclude
    return field, fp, cat


def test_emit_returns_a_valid_prediction_raster():
    """emit() returns the prediction surface itself: float32, strictly binary, in [0,1]."""
    field, fp, cat = _toy()
    pred = emission.emit(field, footprint=fp, visible_catalogue=cat, n=300, sep_px=2.8)
    assert pred.dtype == np.float32
    assert set(np.unique(pred)) <= {0.0, 1.0}, "emit must stay binary (metric-optimal)"
    assert pred.min() >= 0.0 and pred.max() <= 1.0
    assert np.isfinite(pred).all()


def test_emit_respects_budget_and_footprint():
    field, fp, cat = _toy()
    dots = emission.emit(field, footprint=fp, visible_catalogue=cat, n=300, sep_px=2.8) > 0
    assert dots.sum() <= 300
    assert not (dots & ~fp).any(), "dot placed outside the survey footprint"


def test_emit_excludes_the_catalogue_halo_exactly():
    field, fp, cat = _toy()
    for excl in (0, 1, 2, 3):
        dots = emission.emit(field, footprint=fp, visible_catalogue=cat, n=500,
                             sep_px=2.8, exclude_px=excl) > 0
        from scipy import ndimage as ndi
        halo = cat if excl == 0 else ndi.binary_dilation(
            cat, np.ones((3, 3), bool), iterations=excl)
        assert not (dots & halo).any(), f"dot inside the {excl}px catalogue halo"


def test_emit_enforces_minimum_separation():
    field, fp, cat = _toy()
    for sep in (2.8, 4.0, 5.5):
        dots = emission.emit(field, footprint=fp, visible_catalogue=cat, n=200, sep_px=sep) > 0
        ys, xs = np.nonzero(dots)
        if ys.size < 2:
            continue
        d2 = (ys[:, None] - ys[None, :]) ** 2 + (xs[:, None] - xs[None, :]) ** 2
        np.fill_diagonal(d2, 10 ** 9)
        assert d2.min() >= int(sep ** 2) - 1e-9, f"separation {sep} violated"


def test_emit_prefers_high_field_values():
    """Sanity: the rule must actually be driven by the field, not by position."""
    field, fp, cat = _toy()
    dots = emission.emit(field, footprint=fp, visible_catalogue=cat, n=200, sep_px=2.8) > 0
    ys, _ = np.nonzero(dots)
    on_ridge = ((ys >= 39) & (ys <= 45)).mean()
    assert on_ridge > 0.20, f"only {on_ridge:.1%} of dots near the planted ridge"


def test_emit_is_deterministic():
    field, fp, cat = _toy()
    a = emission.emit(field, footprint=fp, visible_catalogue=cat, n=250, sep_px=2.8)
    b = emission.emit(field, footprint=fp, visible_catalogue=cat, n=250, sep_px=2.8)
    assert np.array_equal(a, b)


def test_emit_handles_nan_and_empty_field():
    field, fp, cat = _toy()
    field[10:20, 10:20] = np.nan
    dots = emission.emit(field, footprint=fp, visible_catalogue=cat, n=100, sep_px=2.8) > 0
    assert np.isfinite(field[dots]).all() or dots.sum() == 0
    zero = emission.emit(np.zeros_like(field), footprint=fp, visible_catalogue=cat,
                         n=50, sep_px=2.8)
    assert zero.sum() <= 50


def test_emit_budget_larger_than_capacity_does_not_hang():
    field, fp, cat = _toy(h=40, w=40)
    dots = emission.emit(field, footprint=fp, visible_catalogue=cat, n=10 ** 6, sep_px=4.0) > 0
    assert 0 < dots.sum() < 10 ** 6


# --------------------------------------------------------------------------- validator
def test_validator_rejects_out_of_range_values(tmp_path):
    """The exact failure mode that got the previous submission rejected."""
    import rasterio
    from gems85.grid import TRANSFORM, EPSG
    bad = tmp_path / "bad.tif"
    arr = np.zeros((HEIGHT, WIDTH), np.float32)
    arr[0, 0] = 1.5                                            # out of [0,1]
    with rasterio.open(bad, "w", driver="GTiff", height=HEIGHT, width=WIDTH, count=1,
                       dtype="float32", crs=f"EPSG:{EPSG}", transform=TRANSFORM) as dst:
        dst.write(arr, 1)
    rep = submission.validate(bad)
    assert not rep.passed
    assert rep.checks["values_in_0_1_whole_raster"] is False


def test_validator_rejects_nan_inside_footprint(tmp_path):
    import rasterio
    from gems85.grid import TRANSFORM, EPSG, footprint
    try:
        fp = footprint()
    except Exception:                                          # pragma: no cover
        pytest.skip("data cache not present")
    bad = tmp_path / "nan.tif"
    arr = np.zeros((HEIGHT, WIDTH), np.float32)
    ys, xs = np.nonzero(fp)
    arr[ys[0], xs[0]] = np.nan
    with rasterio.open(bad, "w", driver="GTiff", height=HEIGHT, width=WIDTH, count=1,
                       dtype="float32", crs=f"EPSG:{EPSG}", transform=TRANSFORM) as dst:
        dst.write(arr, 1)
    rep = submission.validate(bad)
    assert not rep.passed
    assert rep.checks["no_nan_inside_footprint"] is False


def test_write_submission_raises_on_failure(tmp_path, monkeypatch):
    """write_submission must never leave a failing file where a user could download it."""
    dots = np.zeros((HEIGHT, WIDTH), bool)
    out = tmp_path / "x.tif"
    orig = submission.validate

    def fake(path, *a, **k):
        rep = orig(path, *a, **k)
        rep.checks["values_in_0_1_whole_raster"] = False
        return rep

    monkeypatch.setattr(submission, "validate", fake)
    with pytest.raises(Exception):
        submission.write_submission(dots, out, mode="zeros")


# --------------------------------------------------------------------------- shipped artifact
@pytest.mark.skipif(not (ROOT / "registry" / "submission.json").exists(),
                    reason="no submission built yet")
def test_shipped_artifact_passes_every_check():
    sub = json.loads((ROOT / "registry" / "submission.json").read_text())
    path = ROOT / "docs" / "downloads" / sub["primary"]["filename"]
    assert path.exists(), f"site advertises {path.name} but the file is missing"
    rep = submission.validate(path)
    failed = [k for k, v in rep.checks.items() if v is False]
    assert rep.passed, f"shipped artifact fails: {failed}"
    assert submission.sha256_file(path) == sub["primary"]["sha256"], \
        "shipped artifact does not match the sha256 the site publishes"


@pytest.mark.skipif(not (ROOT / "registry" / "submission.json").exists(),
                    reason="no submission built yet")
def test_published_note_is_within_140_chars():
    sub = json.loads((ROOT / "registry" / "submission.json").read_text())
    assert 0 < len(sub["note"]) <= 140


@pytest.mark.skipif(not (ROOT / "evidence" / "run_card.json").exists(),
                    reason="no run card yet")
def test_run_card_has_every_required_protocol_field():
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    for key in ("hypothesis", "mechanism", "named_non_fault_process_that_could_mimic_it",
                "holdout_dti", "correlation_vs_registry", "raster_sha256",
                "validator_output", "submission_name", "submission_note", "verdict"):
        assert key in card and card[key], f"run card missing {key}"
    assert card["holdout_dti"]["label"] == "HOLDOUT-DTI"
    assert "ci95" in card["holdout_dti"] and "n_withheld_positives" in card["holdout_dti"]
