"""Line-by-line verification of src/gems85/metric.py against the official definitions.

No number in this file is invented: the published worked example and the three sums are
transcribed from
  https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
(section "Performance metric" -> "Mathematical representation" / "Scoring example").
"""

from __future__ import annotations

import numpy as np
import pytest

from gems85.metric import ALPHA, BETA, R_PIXELS, OFFSETS, dti, kernel_dilate


# ---------------------------------------------------------------- kernel


def test_kernel_support_is_the_29_pixel_disc():
    # offsets with dy^2+dx^2 <= 9
    assert len(OFFSETS) == 29
    assert all(np.hypot(dy, dx) <= 3.0 + 1e-12 for dy, dx, _ in OFFSETS)
    # triangular kernel values k(d) = 1 - d/3
    for dy, dx, k in OFFSETS:
        assert k == pytest.approx(max(0.0, 1.0 - np.hypot(dy, dx) / 3.0))
    # k(0) = 1, k(3) = 0
    assert dict(((dy, dx), k) for dy, dx, k in OFFSETS)[(0, 0)] == 1.0
    assert dict(((dy, dx), k) for dy, dx, k in OFFSETS)[(0, 3)] == 0.0


def test_R_is_three_pixels_at_100m():
    assert R_PIXELS == 300.0 / 100.0


# ---------------------------------------------------------------- published example


def test_published_worked_example_combination():
    """TP_w=3.00, FP_w=1.89, FN_w=2.00 -> 0.60 with alpha=0.2, beta=0.8 (official)."""
    tp_w, fp_w, fn_w = 3.00, 1.89, 2.00
    value = tp_w / (tp_w + ALPHA * fp_w + BETA * fn_w)
    assert round(value, 2) == 0.60


def test_published_alpha_beta():
    assert (ALPHA, BETA) == (0.2, 0.8)


# ---------------------------------------------------------------- brute force


def _brute(p: np.ndarray, g: np.ndarray, R: float = 3.0):
    """Literal O(N^2) transcription of the three published sums."""
    h, w = p.shape
    gs = [(y, x) for y in range(h) for x in range(w) if g[y, x]]
    xs = [(y, x) for y in range(h) for x in range(w) if p[y, x] > 0]

    def k(d):
        return max(0.0, 1.0 - d / R)

    tp = 0.0
    fn = 0.0
    for (gy, gx) in gs:
        best = 0.0
        for (py, px) in xs:
            d = np.hypot(py - gy, px - gx)
            if d <= R:
                best = max(best, p[py, px] * k(d))
        tp += best
        fn += 1.0 - best
    fp = 0.0
    for (py, px) in xs:
        best = 0.0
        for (gy, gx) in gs:
            best = max(best, k(np.hypot(py - gy, px - gx)))
        fp += p[py, px] * (1.0 - best)
    return tp, fp, fn


def test_bruteforce_equivalence_random():
    rng = np.random.default_rng(0)
    for trial in range(8):
        h = w = 24
        p = np.where(rng.random((h, w)) < 0.05, rng.random((h, w)), 0.0)
        g = rng.random((h, w)) < 0.03
        r = dti(p, g)
        tp, fp, fn = _brute(p, g)
        assert r.tp_w == pytest.approx(tp, abs=1e-9), trial
        assert r.fp_w == pytest.approx(fp, abs=1e-9), trial
        assert r.fn_w == pytest.approx(fn, abs=1e-9), trial
        assert r.dti == pytest.approx(tp / (tp + ALPHA * fp + BETA * fn), abs=1e-12)


def test_bruteforce_equivalence_vertical_line_like_the_example():
    """Geometry of the organisers' figure: a single vertical truth line + scattered preds."""
    h, w = 12, 12
    g = np.zeros((h, w), bool)
    g[3:8, 6] = True
    p = np.zeros((h, w))
    p[3, 6] = 1.0      # exact hit
    p[5, 7] = 0.8      # 1 px off
    p[9, 2] = 0.5      # far away -> nearly pure FP
    r = dti(p, g)
    tp, fp, fn = _brute(p, g)
    assert (r.tp_w, r.fp_w, r.fn_w) == pytest.approx((tp, fp, fn), abs=1e-9)


# ---------------------------------------------------------------- identities used in design


def test_fn_identity_equals_K_minus_TP():
    rng = np.random.default_rng(3)
    p = np.where(rng.random((40, 40)) < 0.1, rng.random((40, 40)), 0.0)
    g = rng.random((40, 40)) < 0.05
    r = dti(p, g)
    assert r.fn_w == pytest.approx(r.n_truth - r.tp_w, abs=1e-9)


def test_fp_identity_equals_S_minus_M():
    rng = np.random.default_rng(4)
    p = np.where(rng.random((40, 40)) < 0.1, rng.random((40, 40)), 0.0)
    g = rng.random((40, 40)) < 0.05
    r = dti(p, g)
    kg = kernel_dilate(g.astype(float))
    S = p.sum()
    M = (p * kg).sum()
    assert r.fp_w == pytest.approx(S - M, abs=1e-9)


def test_scaling_monotonicity():
    """DTI(lam*p) is strictly increasing in lam -- the reason submissions use p=1 dots."""
    rng = np.random.default_rng(5)
    p = np.where(rng.random((60, 60)) < 0.08, 1.0, 0.0)
    g = rng.random((60, 60)) < 0.03
    vals = [dti(lam * p, g).dti for lam in (0.25, 0.5, 0.75, 1.0)]
    assert all(b > a for a, b in zip(vals, vals[1:]))


def test_nan_in_prediction_is_zero_mass():
    g = np.zeros((10, 10), bool); g[5, 5] = True
    p = np.full((10, 10), np.nan); p[5, 5] = 1.0
    r = dti(p, g)
    assert r.tp_w == pytest.approx(1.0)
    assert r.fp_w == pytest.approx(0.0)
    assert r.dti == pytest.approx(1.0)


def test_domain_restriction():
    g = np.zeros((10, 10), bool); g[2, 2] = True; g[8, 8] = True
    p = np.zeros((10, 10)); p[2, 2] = 1.0
    dom = np.zeros((10, 10), bool); dom[:5, :5] = True
    r = dti(p, g, domain=dom)
    assert r.n_truth == 1 and r.tp_w == pytest.approx(1.0) and r.dti == pytest.approx(1.0)
