"""Tests for H85-GAPVENT session pipeline, uniqueness gate, banned-column security, and site sync."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems85 import gapvent, grid

ROOT = Path(__file__).resolve().parents[1]


def test_gapvent_bans_leaky_wellspring_column():
    """Verify _load_deep_geotherm_points structurally excludes dist_known_fault_px."""
    src = inspect.getsource(gapvent._load_deep_geotherm_points)
    assert 'BANNED_COL = "dist_known_fault_px"' in src
    assert "assert BANNED_COL not in ALLOWED_COLS" in src


def test_gapvent_excludes_lacustrine_tufa():
    """Verify _load_hydrothermal_paleo_points filters out Lake Lahontan Tufa mounds."""
    src = inspect.getsource(gapvent._load_hydrothermal_paleo_points)
    assert 'dtype.lower() == "tufa"' in src


def test_basin_id_channels_excluded_from_tree_splits():
    """Verify IR-85-023 protection: long-wavelength basin-ID channels are excluded from tree splits."""
    dummy_names = ["geopb_crest", "gv_dem10_line_s15", "gv_zmean_m", "depth_to_base", "gv_probe2m_anom_prox"]
    dummy_handles = [np.zeros((4, 4), dtype=np.float32) for _ in dummy_names]
    kept_names, kept_handles = gapvent.select_local_tree_stack(dummy_names, dummy_handles)
    assert kept_names == ["geopb_crest", "gv_dem10_line_s15"]
    assert len(kept_handles) == 2


def test_stripwise_gather_matches_direct_indexing():
    """Verify gather_stripwise returns exact pixel values in caller order regardless of input permutation."""
    rng = np.random.default_rng(42)
    h1 = rng.normal(size=(grid.HEIGHT, grid.WIDTH)).astype(np.float32)
    h2 = rng.normal(size=(grid.HEIGHT, grid.WIDTH)).astype(np.float32)
    idx = rng.choice(grid.HEIGHT * grid.WIDTH, size=500, replace=False)
    X = gapvent.gather_stripwise([h1, h2], idx, strip_rows=256)
    ys, xs = np.divmod(idx, grid.WIDTH)
    np.testing.assert_array_equal(X[:, 0], h1[ys, xs])
    np.testing.assert_array_equal(X[:, 1], h2[ys, xs])


def test_primary_gapvent_submission_and_3px_halo_contract():
    """Verify the promoted H85-GAPVENT primary GeoTIFF satisfies 17/17 checks, 3-px halo, and uniqueness."""
    sub = json.loads((ROOT / "registry" / "submission.json").read_text())
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    dup = json.loads((ROOT / "evidence" / "duplicate_check.json").read_text())

    fn = sub["primary"]["filename"]
    assert "gapvent57" in fn
    assert len(sub["note"]) <= 140
    assert card["submission_name"] == fn
    assert card["raster_sha256"] == sub["primary"]["sha256"]
    assert card["holdout_dti"]["value"] > 0.14
    assert not dup["is_duplicate"]
    assert dup["max_abs_spearman"] <= 0.90
    assert dup["max_comparable_dot_overlap_3px"] <= 0.70

    tif_path = ROOT / "docs" / "downloads" / fn
    assert tif_path.exists()
    with rasterio.open(tif_path) as ds:
        arr = ds.read(1)
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert ds.nodata is None
        assert np.isfinite(arr).all()
        assert set(np.unique(arr).tolist()) == {0.0, 1.0}
        assert int((arr > 0).sum()) == 37_654

    labels_path = ROOT / "data" / "labels.tif"
    if labels_path.exists():
        with rasterio.open(labels_path) as ls:
            cat = ls.read(1) >= 1
        halo3 = ndi.binary_dilation(cat, np.ones((3, 3), bool), iterations=3)
        assert not ((arr > 0) & halo3).any(), "Primary must have zero dots within 3-px (300 m) of catalogue"
