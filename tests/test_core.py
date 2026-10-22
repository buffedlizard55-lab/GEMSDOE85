from __future__ import annotations

import numpy as np

from gems85.emission import emit_peaks
from gems85.holdout import withhold_segments
from gems85.metric import dti_from_components


def test_metric_equation():
    expected = 3.0 / (3.0 + 0.2 * 1.89 + 0.8 * 2.0)
    assert abs(dti_from_components(3.0, 1.89, 2.0) - expected) < 1e-12


def test_emission_is_deterministic_and_spaced():
    surface = np.zeros((30, 30), dtype=np.float32)
    surface[5, 5] = 1.0
    surface[5, 12] = 0.9
    surface[20, 20] = 0.8
    eligible = np.ones_like(surface, dtype=bool)
    a = emit_peaks(surface, eligible, budget=10, min_distance_px=2.8)
    b = emit_peaks(surface, eligible, budget=10, min_distance_px=2.8)
    assert np.array_equal(a, b)
    assert a[5, 5] and a[5, 12] and a[20, 20]


def test_holdout_hides_whole_components_and_buffer():
    catalogue = np.zeros((20, 20), dtype=bool)
    catalogue[2:5, 2] = True
    catalogue[14:18, 15] = True
    footprint = np.ones_like(catalogue, dtype=bool)
    split = withhold_segments(catalogue, footprint, hold_frac=0.3, buffer_px=2, seed=1)
    assert split["hidden"].sum() in (3, 4, 7)
    assert not np.any(split["visible"] & split["hidden_buffer"])
    assert split["n_components"] == 2
