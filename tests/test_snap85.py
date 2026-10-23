"""Unit tests for the SNAP axis (`src/gems85/snap85.py`).

These are synthetic: no competition raster is read, so they run anywhere and pin the *rule*, not the
result.  They are the contract the build script relies on:

    count and mass fixed; |move| <= cap; never closer to the catalogue; >= min_sep between dots;
    strictly better response only; deterministic; no move when the response is flat.
"""

from __future__ import annotations

import numpy as np
import pytest

from gems85.snap85 import disc_offsets, parent_disc_count, snap_dots, support_coverage


def _scene(h=40, w=60, n=12, seed=3):
    rng = np.random.default_rng(seed)
    dots = np.zeros((h, w), bool)
    flat = rng.choice(h * w, size=n, replace=False)
    dots.ravel()[flat] = True
    # enforce a >= 2.8 px packing like the parent (drop anything too close)
    keep = np.zeros_like(dots)
    for y, x in np.argwhere(dots)[np.argsort(np.argwhere(dots)[:, 0] * w + np.argwhere(dots)[:, 1])]:
        yy, xx = np.nonzero(keep)
        if yy.size and np.min(np.hypot(yy - y, xx - x)) < 2.8:
            continue
        keep[y, x] = True
    resp = np.zeros((h, w), np.float32)
    resp[5:30, 5:50] = 0.25
    resp[20:24, 10:40] = 0.80          # a bright band
    foot = np.ones((h, w), bool)
    dist_cat = np.full((h, w), 50.0, np.float32)
    dist_cat[:, :3] = 0.0              # a catalogue strip on the left edge
    return keep, resp, dist_cat, foot


def test_offsets_respect_cap():
    assert sorted(disc_offsets(1.0, inclusive=True)) == sorted([(-1, 0), (1, 0), (0, -1), (0, 1)])
    assert disc_offsets(1.0) == []                       # nothing strictly inside 1 px
    for dy, dx in disc_offsets(2.0, inclusive=True):
        assert 0 < dy * dy + dx * dx <= 4.0


def test_parent_disc_count_counts_centre_only_for_isolated_dot():
    dots = np.zeros((9, 9), bool)
    dots[4, 4] = True
    cnt = parent_disc_count(dots, 2.0)
    assert cnt[4, 4] == 1.0
    assert cnt[4, 6] == 0.0                              # exactly 2 px away: outside the strict disc
    assert cnt[4, 5] == 1.0


def test_snap_keeps_count_and_mass_and_cap():
    dots, resp, dcat, foot = _scene()
    out, info = snap_dots(dots, resp, dcat, foot, cap_px=2.0)
    assert int(out.sum()) == int(dots.sum())             # count and mass fixed
    moved = dots & ~out
    assert info["n_moved"] == int(moved.sum())
    assert info["max_displacement_px"] <= 2.0 + 1e-9
    # every final dot is either an unchanged parent dot or a destination inside the cap
    assert not (out & ~dots & ~foot).any()


def test_snap_never_gets_closer_to_catalogue():
    dots, resp, dcat, foot = _scene()
    out, _ = snap_dots(dots, resp, dcat, foot, cap_px=2.0, min_cat_dist=3.0)
    assert dcat[out].min() >= 3.0
    # per-dot: a destination may not be closer to the catalogue than its own parent was
    ys, xs = np.nonzero(dots)
    for y, x in zip(ys, xs):
        if dots[y, x] and not out[y, x]:
            # find where it went: the nearest final dot within the cap
            yy, xx = np.nonzero(out)
            d = np.hypot(yy - y, xx - x)
            j = np.argmin(d)
            assert d[j] <= 2.0 + 1e-9
            assert dcat[yy[j], xx[j]] >= dcat[y, x] - 1e-9


def test_snap_enforces_min_separation():
    dots, resp, dcat, foot = _scene()
    out, _ = snap_dots(dots, resp, dcat, foot, cap_px=2.0, min_sep=2.0)
    cnt = parent_disc_count(out, 2.0)
    assert cnt[out].max() == 1.0                         # no other dot strictly within 2 px


def test_flat_response_moves_nothing():
    dots, _, dcat, foot = _scene()
    resp = np.zeros_like(dcat)
    out, info = snap_dots(dots, resp, dcat, foot, cap_px=2.0)
    assert info["n_moved"] == 0
    assert np.array_equal(out, dots)


def test_deterministic():
    dots, resp, dcat, foot = _scene()
    a, ia = snap_dots(dots, resp, dcat, foot, cap_px=2.0)
    b, ib = snap_dots(dots, resp, dcat, foot, cap_px=2.0)
    assert np.array_equal(a, b) and ia == ib


def test_dest_mask_confines_moves():
    dots, resp, dcat, foot = _scene()
    allowed = np.zeros_like(dots)
    allowed[18:26, 8:42] = True
    out, info = snap_dots(dots, resp, dcat, foot, cap_px=2.0, dest_mask=allowed)
    assert info["confined"] is True
    # confinement binds destinations only; a dot that does not move stays at its parent position
    assert not (out & ~dots & ~allowed).any()


def test_strictly_better_only():
    dots, resp, dcat, foot = _scene()
    base = resp.copy()
    out, _ = snap_dots(dots, base, dcat, foot, cap_px=2.0)
    # a dot that did not move must not have had a strictly better eligible neighbour
    for y, x in np.argwhere(dots & out):
        best = resp[y, x]
        for dy, dx in disc_offsets(2.0, inclusive=True):
            yy, xx = y + dy, x + dx
            if 0 <= yy < resp.shape[0] and 0 <= xx < resp.shape[1]:
                if foot[yy, xx] and dcat[yy, xx] >= max(3.0, dcat[y, x]):
                    assert resp[yy, xx] <= best + 1e-9


def test_support_coverage_bounds():
    dots, resp, dcat, foot = _scene()
    c_same = support_coverage(dots, dots)
    assert 0.99 < c_same <= 1.0
    c_far = support_coverage(np.zeros_like(dots), dots)
    assert c_far == 0.0
