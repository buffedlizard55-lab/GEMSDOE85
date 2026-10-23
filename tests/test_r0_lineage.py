"""Tests for the R0 lineage rebuild, the label-free ranking, and the PRUNE variants.

All rasters used here are SHA-256-pinned by `src/gems85/r0_lineage.PINS`; tests that need them
skip cleanly when the restored inputs are absent (they are gitignored, see `scripts/restore_data.py`).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import r0_lineage as RL  # noqa: E402
from gems85.metric import dti  # noqa: E402
from gems85.thinning85 import disc_offsets, dot_thin  # noqa: E402

HAVE_DATA = all(p.is_file() for p in RL.PATHS.values())


# ------------------------------------------------------------------ thinning contract
def test_disc_offsets_are_strictly_inside_radius():
    for md in (1.5, 2.8, 3.0):
        offs = disc_offsets(md)
        assert all(dy * dy + dx * dx < md * md for dy, dx in offs)
        assert (0, 0) in offs


def test_dot_thin_is_subset_deterministic_and_respects_spacing():
    rng = np.random.default_rng(7)
    m = np.zeros((60, 60), bool)
    m[10:50, 12] = True
    m[10:50:2, 30] = True
    m[rng.integers(0, 60, 40), rng.integers(0, 60, 40)] = True
    a, rank = dot_thin(m, 2.8, order=True)
    b = dot_thin(m, 2.8)
    assert np.array_equal(a, b)
    assert not (a & ~m).any()
    kept = np.argwhere(a)
    for i in range(0, len(kept), 7):           # sampled O(n^2) spacing check
        d = np.hypot(*(kept - kept[i]).T)
        d[i] = np.inf
        assert d.min() >= 2.8 - 1e-9
    assert (rank[a] >= 0).all() and (rank[~a] == -1).all()
    assert sorted(rank[a].tolist()) == list(range(int(a.sum())))


def test_dot_thin_short_circuit():
    m = np.zeros((10, 10), bool); m[3, 4] = True
    assert np.array_equal(dot_thin(m, 1.0), m)


# ------------------------------------------------------------------ ranking
def test_unique_credit_matches_bruteforce():
    rng = np.random.default_rng(3)
    dots = np.zeros((40, 40), bool)
    dots[rng.integers(2, 38, 18), rng.integers(2, 38, 18)] = True
    U = RL.unique_credit(dots)
    pts = list(zip(*np.nonzero(dots)))
    H, W = dots.shape
    for i, (y, x) in enumerate(pts):
        tot = 0.0
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                Y, X = y + dy, x + dx
                if not (0 <= Y < H and 0 <= X < W):
                    continue
                k = max(0.0, 1.0 - np.hypot(dy, dx) / 3.0)
                if k <= 0:
                    continue
                other = max([max(0.0, 1.0 - np.hypot(Y - y2, X - x2) / 3.0)
                             for j, (y2, x2) in enumerate(pts) if j != i] + [0.0])
                tot += max(0.0, k - other)
        assert abs(tot - U[i]) < 1e-5


def test_unique_credit_isolated_dot_equals_kernel_area():
    dots = np.zeros((15, 15), bool); dots[7, 7] = True
    U = RL.unique_credit(dots)
    assert U[0] == pytest.approx(sum(k for _, _, k in RL.KERNEL), abs=1e-6)


def test_select_lowest_is_deterministic_and_monotone():
    rng = np.random.default_rng(11)
    dots = np.zeros((40, 40), bool)
    dots[rng.integers(0, 40, 30), rng.integers(0, 40, 30)] = True
    U = RL.unique_credit(dots)
    a = RL.select_lowest(U, dots, 0.10)
    b = RL.select_lowest(U, dots, 0.10)
    c = RL.select_lowest(U, dots, 0.30)
    assert np.array_equal(a, b)
    assert c.sum() < a.sum() < dots.sum()
    assert not (a & ~dots).any() and not (c & ~a).any()


# ------------------------------------------------------------------ rebuild + deliverables
@pytest.mark.skipif(not HAVE_DATA, reason="pinned rasters not restored")
def test_pins_verify():
    pins = RL.verify_pins()
    assert set(pins) == set(RL.PINS)


@pytest.mark.skipif(not HAVE_DATA, reason="pinned rasters not restored")
def test_r0_rebuild_is_pixel_identical_to_pinned_parent():
    L = RL.rebuild(verify_against_pinned_files=True)
    assert L.counts() == {"skeleton": 121131, "d28": 44090, "solo": 40199, "r0": 37654}
    assert RL.sha256_file(RL.PATHS["r0_zeros"]) == RL.PINS["r0_zeros"]
    assert RL.sha256_file(RL.PATHS["r0_nan"]) == RL.PINS["r0_nan"]
    # R0 carries no mass on the catalogue and stays outside 2 px of it
    assert int((L.r0 & (L.dist_cat <= 2.0)).sum()) == 0


@pytest.mark.skipif(not HAVE_DATA, reason="pinned rasters not restored")
def test_prune_variant_semantics_on_parent():
    L = RL.rebuild(verify_against_pinned_files=False)
    p3 = L.r0 & (L.dist_cat > 3.0)
    p5 = L.r0 & (L.dist_cat > 5.0)
    assert int(p3.sum()) == 35483 and int(p5.sum()) == 32017
    assert not (p3 & ~L.r0).any()          # only removals on the PRUNE axis
    assert int((p3 & (L.dist_cat <= 3.0)).sum()) == 0
    assert (L.dist_cat[p3] > 3.0).all()
    # a wider rung is a strict subset of a narrower one
    assert not (p5 & ~p3).any()


@pytest.mark.skipif(not HAVE_DATA, reason="pinned rasters not restored")
def test_shipped_releases_pass_their_own_gates_and_match_the_ledger():
    """Every BUILT row in the ledger must be a real, gated, hash-matching file.

    Axis-aware. PRUNE rows (three integral rungs from the prune session, three fractional rungs from
    the rung session) prove zero catalogue mass and their own declared distance threshold. SNAP rows
    keep count and mass fixed and may never move a dot closer to the catalogue (the parent itself
    carries 2,171 dots at 2.24-3.00 px -- IR-V2-03 -- which SNAP is not allowed to touch).
    """
    ledger = ROOT / "ledger" / "submissions.csv"
    receipts = [ROOT / "evidence" / "session_prune_receipt.json",
                ROOT / "evidence" / "session_rung_receipt.json",
                ROOT / "evidence" / "session_snap_receipt.json",
                ROOT / "evidence" / "session_relief_receipt.json"]
    if not ledger.is_file():
        pytest.skip("session outputs not built")
    rows = list(csv.DictReader(ledger.open()))
    assert len(rows) >= 3
    assert all(r["parent"] == "h33-h33-2-b2" for r in rows)
    assert all(r["axis"] in {"PRUNE", "SNAP", "RELIEF"} for r in rows)
    assert all(r["status"] == "BUILT" and r["receipt"] == "N" for r in rows)
    assert len({r["sha256"] for r in rows}) == len(rows), "duplicate sha256 in the ledger"
    variants = {}
    for path in receipts:
        if path.is_file():
            variants.update(json.loads(path.read_text())["variants"])
    dist_cat = RL.catalogue_distance()
    parent_min = float(dist_cat[RL.rebuild(verify_against_pinned_files=False).r0].min())
    for row in rows:
        axis = row["axis"]
        stem = row["id"].rsplit("-", 2)[0]
        entry = variants.get(stem) or variants[stem.rsplit("-", 1)[-1]]
        tif = ROOT / "releases" / f'{row["id"]}.tif'
        assert tif.is_file(), tif
        assert RL.sha256_file(tif) == row["sha256"]
        assert entry["all_gates_passed"], entry["nan"]["checks"]
        assert entry["nan"]["sha256"] == row["sha256"]
        assert int(row["n_dots"]) == entry["nan"]["positive_pixels"]
        assert float(row["pct_changed"]) > 0.0
        assert row["sha8"] == row["sha256"][:8]
        checks = entry["nan"]["checks"]
        assert checks["zero_mass_on_catalogue"]
        if axis == "PRUNE":
            # the 3 px rule is waived for PRUNE; each rung proves its own declared threshold instead
            assert checks.get("min_distance_to_catalogue_px_gt_3") or \
                checks["all_dots_beyond_declared_rung"]
        elif axis == "RELIEF":
            assert checks["min_distance_to_catalogue_px_gt_3"]
            assert checks["fixed_count_matches_parent"]
        else:
            # SNAP keeps count and mass and may never move a dot closer to the catalogue
            assert entry["nan"]["within_2px_catalogue_px"] == 0
            assert entry["nan"]["min_distance_to_catalogue_px"] >= parent_min - 1e-9
            assert entry["nan"]["positive_pixels"] == entry["snap"]["pair"]["parent_dots"]
        # the zeros twin must be all-finite and pixel-identical
        import rasterio
        with rasterio.open(ROOT / "releases" / f'{row["id"]}-zeros.tif') as z:
            a = z.read(1)
        assert np.isfinite(a).all()
        with rasterio.open(tif) as n:
            b = n.read(1)
        assert np.array_equal(np.nan_to_num(b), a)


def test_dti_penalises_mass_far_from_truth():
    truth = np.zeros((40, 40), bool); truth[20, 5:35] = True
    near = np.zeros((40, 40)); near[20, 5:35] = 1.0
    far = near.copy(); far[35, 5:35] = 1.0            # same mass, 15 px away
    assert dti(far, truth).dti < dti(near, truth).dti
