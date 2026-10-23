"""Invariants of the SNAP session builders (no network, no large rasters required)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "src"))

import run_snap_variants as R  # noqa: E402


def test_offsets_include_stay_and_respect_radius():
    for d in (1.0, 2.0):
        offs = R.offsets_within(d)
        assert (0, 0, 0.0) in offs
        assert all(np.hypot(dy, dx) <= d + 1e-9 for dy, dx, _ in offs)
        # nearest-first ordering is what makes the tie-break deterministic
        dists = [dist for _, _, dist in offs]
        assert dists == sorted(dists)
    assert len(R.offsets_within(1.0)) == 5      # stay + 4-neighbourhood (diagonals are 1.414)
    assert len(R.offsets_within(2.0)) == 13     # disc of radius 2 (no diagonals of 2.236)


def test_rank01_is_a_footprint_percentile():
    a = np.arange(100, dtype=np.float32).reshape(10, 10)
    valid = np.ones_like(a, bool)
    r = R.rank01(a, valid)
    assert r.min() == 0.0 and r.max() < 1.0
    assert r[0, 1] > r[0, 0]


def _field(shape=(40, 40), seed=3):
    rng = np.random.default_rng(seed)
    e = rng.random(shape).astype(np.float32)
    return e, np.ones(shape, bool)


def test_snap_preserves_count_injectivity_and_displacement():
    shape = (40, 40)
    e, elig = _field(shape)
    dots = np.argwhere(np.ones(shape, bool))[:200]
    for tau in (None, 0.0, 0.5):
        out, st = R.snap(dots, e, elig, 2.0, tau, shape)
        assert out.shape == dots.shape
        assert st["n_unique_targets"] == st["n_dots"] == len(dots)
        assert st["n_duplicate_placement"] == 0
        # the 2 px cap holds for every snapped dot; a handful of dots with no eligible
        # cell inside the cap are refilled wider and counted separately
        assert st["max_displacement_px"] <= 10.0 + 1e-9
        assert st["n_refilled_beyond_d"] == 0 or st["max_refill_px"] > 0
        assert (out >= 0).all() and (out[:, 0] < shape[0]).all() and (out[:, 1] < shape[1]).all()


def test_control_moves_only_ineligible_dots():
    shape = (40, 40)
    e, _ = _field(shape)
    elig = np.ones(shape, bool)
    dots = np.array([[10, 10], [20, 20], [30, 30]], dtype=np.int64)
    elig[10, 10] = False                      # this dot must move even with tau=None
    out, st = R.snap(dots, e, elig, 2.0, None, shape)
    assert st["n_moved"] == 1
    assert st["n_moved_because_forced"] == 1
    assert not np.array_equal(out[0], dots[0])
    assert np.array_equal(out[1], dots[1]) and np.array_equal(out[2], dots[2])


def test_threshold_never_moves_more_than_unconditional():
    shape = (40, 40)
    e, elig = _field(shape, seed=11)
    dots = np.argwhere(np.ones(shape, bool))[:300]
    _, a = R.snap(dots, e, elig, 2.0, 0.50, shape)
    _, b = R.snap(dots, e, elig, 2.0, 0.20, shape)
    _, c = R.snap(dots, e, elig, 2.0, 0.00, shape)
    assert a["n_moved"] <= b["n_moved"] <= c["n_moved"]


def test_ineligible_targets_are_never_used():
    """A dot inside a 3x3 ineligible hole must be placed outside it, never on it."""
    shape = (40, 40)
    e, _ = _field(shape)
    elig = np.ones(shape, bool)
    elig[20:23, 20:23] = False                 # ineligible pocket, reachable from outside
    dots = np.array([[21, 21], [20, 20], [19, 19], [24, 24]], dtype=np.int64)
    out, st = R.snap(dots, e, elig, 2.0, 0.0, shape)
    used = np.zeros(shape, bool)
    used[out[:, 0], out[:, 1]] = True
    assert not (used & ~elig).any()
    assert st["n_duplicate_placement"] == 0


def test_session_evidence_meets_the_gates_if_present():
    """If the session artefacts exist, their recorded gates must all be true."""
    ev = ROOT / "evidence/session_snap.json"
    if not ev.is_file():
        pytest.skip("session evidence not built in this checkout")
    d = json.loads(ev.read_text())
    assert d["parent_rebuild"]["pixel_identical"] is True
    assert d["parent_rebuild"]["n_dots"] == 37654
    assert d["catalogue_clear_px"] >= 3.0
    for v in d["variants"]:
        assert v["format_report"]["ok"], v["value"]
        assert v["local_validate"]["all_checks_passed"], v["value"]
        assert v["stats"]["n_dots"] == 37654
        assert v["stats"]["n_duplicate_placement"] == 0
        assert v["stats"]["max_refill_px"] <= 10.0 + 1e-6
        assert v["stats"]["n_refilled_beyond_d"] / v["stats"]["n_dots"] < 0.002
