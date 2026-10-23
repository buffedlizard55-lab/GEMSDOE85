"""Contract tests for the SNAP axis (src/gems85/snap_axis.py).

These pin the four invariants the session relies on:
  1. the offset set is exactly the <= max_px neighbourhood, never the dot's own cell;
  2. a snap preserves the dot count and moves each dot at most once;
  3. no dot ends closer to the catalogue, and no dot lands on a catalogue pixel;
  4. the final set keeps the requested minimum separation, and the result is deterministic.
"""

from __future__ import annotations

import numpy as np

from gems85.snap_axis import (consensus, edge_field, kernel_credit, mean_credit,
                              separation_disc, snap, snap_offsets)


def _field(shape, spots, value=0.9):
    f = np.zeros(shape, np.float32)
    for y, x in spots:
        f[y, x] = value
    return f


def test_offsets_are_the_two_pixel_neighbourhood():
    off = snap_offsets(2.0)
    assert (off == 0).all(axis=1).sum() == 0, "the dot's own cell must not be a candidate"
    assert all(np.hypot(dy, dx) <= 2.0 + 1e-9 for dy, dx in off)
    assert len(off) == 12, "a 2 px disc (excluding the centre) has 12 cells"
    assert len({tuple(o) for o in off}) == 12
    assert np.array_equal(snap_offsets(1.0), np.array([[-1, 0], [0, -1], [0, 1], [1, 0]]))


def test_separation_disc_is_strictly_inside():
    oy, ox = separation_disc(2.0)
    assert len(oy) == 9, "centre + 4 axial (1 px) + 4 diagonal (1.41 px), all < 2.0 px"
    assert any((a, b) == (0, 0) for a, b in zip(oy, ox)), "the centre is included so a dot counts itself"
    assert all(np.hypot(a, b) < 2.0 for a, b in zip(oy, ox))


def test_snap_moves_one_dot_and_preserves_count():
    dots = np.zeros((40, 40), bool)
    dots[10, 10] = True
    edge = _field((40, 40), [(12, 10)])
    dist = np.full((40, 40), 50.0)
    foot = np.ones((40, 40), bool)
    out, diag = snap(dots, edge, dist, foot, max_px=2.0, margin=0.05, min_sep=2.0)
    assert diag["n_moved"] == 1 and out.sum() == dots.sum() == 1
    assert out[12, 10] and not out[10, 10]
    assert diag["mean_displacement_px"] == 2.0
    sy, sx, dy, dx = diag["pairs"]
    assert (sy, sx, dy, dx) == (np.array([10]), np.array([10]), np.array([12]), np.array([10]))


def test_snap_never_approaches_the_catalogue():
    dots = np.zeros((40, 40), bool)
    dots[10, 10] = True
    edge = _field((40, 40), [(11, 10)])
    dist = np.full((40, 40), 50.0)
    dist[11, 10] = 2.0                      # destination would be *on* the 2 px floor
    foot = np.ones((40, 40), bool)
    out, diag = snap(dots, edge, dist, foot, cat_floor_px=2.0)
    assert diag["n_moved"] == 0 and out[10, 10], "a move that reaches the catalogue floor is refused"


def test_snap_respects_minimum_separation():
    dots = np.zeros((40, 40), bool)
    dots[10, 10] = True
    dots[10, 11] = True                     # already 1 px apart: a pathological parent
    # the only attractive cell is 1 px from the other dot, so neither may take it
    edge = _field((40, 40), [(10, 12), (10, 9)])
    dist = np.full((40, 40), 50.0)
    foot = np.ones((40, 40), bool)
    out, diag = snap(dots, edge, dist, foot, min_sep=2.0)
    ys, xs = np.nonzero(out)
    d = np.hypot(ys[:, None] - ys[None, :], xs[:, None] - xs[None, :])
    np.fill_diagonal(d, np.inf)
    assert d.min() >= 2.0, "the final set never sits closer than min_sep"
    assert out.sum() == 2
    # with no separation rule at all the same field does move one dot
    out0, diag0 = snap(dots, edge, dist, foot, min_sep=0.0)
    assert diag0["n_moved"] >= 1


def test_diminishing_returns_and_credit():
    truth = np.zeros((20, 20), bool)
    truth[10, 10] = True
    on = np.zeros((20, 20), bool); on[10, 10] = True
    off = np.zeros((20, 20), bool); off[10, 12] = True
    far = np.zeros((20, 20), bool); far[10, 14] = True
    assert kernel_credit(on, truth)[0] == 1.0
    assert abs(kernel_credit(off, truth)[0] - (1 - 2 / 3)) < 1e-9
    assert kernel_credit(far, truth)[0] == 0.0
    assert mean_credit(on, truth) == 1.0
    assert mean_credit(far, truth) == 0.0


def test_edge_field_normalisation_and_nodata():
    # the competition bands are already derivative products (tmi_hg, iso_grav_anom_hg,
    # det_elev_slope), so the edge strength of a band is its absolute value, smoothed.
    band = np.zeros((30, 30))
    band[15, 5:25] = 2.0                    # a gradient high along one line
    band[0, 0] = -3.4028234663852886e38     # competition nodata sentinel
    valid = band != -3.4028234663852886e38
    e = edge_field(band, valid, sigma=1.0, pct=99.0)
    assert e.max() <= 1.0 and e.min() >= 0.0
    assert e[15, 15] > 0.5, "the gradient high is the edge"
    assert e[25, 25] < 0.05, "a quiet cell stays quiet"
    assert e[0, 0] < 0.05, "a nodata cell must not become a spurious maximum"
    assert e[1, 1] < 0.05, "the nodata hole must not bleed a false edge into its neighbours"


def test_consensus_requires_both_fields():
    a = np.ones((5, 5), np.float32)
    b = np.zeros((5, 5), np.float32)
    b[2, 2] = 1.0
    c = consensus(a, b)
    assert c[2, 2] == 1.0 and c[0, 0] == 0.0


def test_snap_is_deterministic():
    rng = np.random.default_rng(7)
    dots = rng.random((60, 60)) > 0.97
    edge = rng.random((60, 60)).astype(np.float32)
    dist = rng.uniform(3, 20, (60, 60))
    foot = np.ones((60, 60), bool)
    a, da = snap(dots, edge, dist, foot)
    b, db = snap(dots, edge, dist, foot)
    assert np.array_equal(a, b)
    assert da["n_moved"] == db["n_moved"]
    assert np.array_equal(da["pairs"][0], db["pairs"][0])
