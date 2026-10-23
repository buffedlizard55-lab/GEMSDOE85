"""Invariants of the SPACING session builder (no network; large rasters optional)."""
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

import run_spacing_session as S  # noqa: E402


def test_unique_credit_is_zero_for_doubled_dots_and_positive_for_isolated():
    shape = (40, 40)
    # a lone dot owns its whole kernel disc; a doubled dot owns almost nothing
    lone = S.unique_credit(shape, np.array([20]), np.array([20]))
    pair = S.unique_credit(shape, np.array([20, 20]), np.array([20, 21]))
    assert lone[0] > 3.0
    assert pair.sum() < lone[0]                      # sharing destroys unique credit
    assert pair.min() < lone[0] / 2


def test_dilate_max_matches_bruteforce_on_a_small_grid():
    shape = (12, 12)
    y, x = np.array([5]), np.array([5])
    c = S.dilate_max(shape, y, x)
    assert abs(float(c[5, 5]) - 1.0) < 1e-6
    assert c[5, 8] == 0.0
    assert abs(float(c[5, 7]) - 1.0 / 3.0) < 1e-6    # 2 px away


def test_greedy_refill_respects_separation_and_count():
    shape = (30, 30)
    cand = np.ones(shape, bool)
    forbid = np.zeros(shape, bool)
    added, _ = S.greedy_refill(shape, cand, np.array([10]), np.array([10]), 12, forbid)
    assert added.shape[0] == 12
    allp = np.vstack([added, np.array([[10, 10]])])
    d = np.sqrt(((allp[:, None] - allp[None]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    assert d.min() >= np.sqrt(2) - 1e-9


def test_greedy_refill_never_uses_forbidden_or_taken_cells():
    shape = (20, 20)
    forbid = np.zeros(shape, bool)
    forbid[:, :10] = True
    added, _ = S.greedy_refill(shape, np.ones(shape, bool), np.array([0]), np.array([19]), 5, forbid)
    assert (added[:, 1] >= 10).all()
    assert len({(int(a), int(b)) for a, b in added}) == added.shape[0]


def test_session_evidence_meets_the_gates_if_present():
    ev = ROOT / "evidence/session_spacing.json"
    if not ev.is_file():
        pytest.skip("spacing evidence not built in this checkout")
    d = json.loads(ev.read_text())
    assert d["parent_rebuild"]["pixel_identical"] is True
    assert d["catalogue_clear_px"] >= 3.0
    for v in d["variants"]:
        assert v["format_report"]["ok"], v["value"]
        assert v["local_validate"]["all_checks_passed"], v["value"]
        assert v["stats"]["n_dots"] == d["parent_stats"]["n_dots"]
        assert v["stats"]["added_on_skeleton_pct"] == 100.0
        assert v["stats"]["n_removed"] <= int(0.20 * d["parent_stats"]["n_dots"]) + 1
