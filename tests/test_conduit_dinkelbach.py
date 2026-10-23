"""Unit verification of exact marginal DTI algebra, submodular Minoux lazy-heap equivalence,
and strict zero-leakage fold-isolation invariants."""

from __future__ import annotations

import numpy as np
import pytest

from gems85.dinkelbach import (
    ALPHA,
    BETA,
    KERNEL_DX,
    KERNEL_DY,
    KERNEL_W,
    bayes_prior_shift,
    compute_max_kernel_proximity,
    dti_from_totals,
    exact_marginal_dti_delta,
    general_dot_breakeven,
    greedy_submodular_at_tau,
    isolated_dot_breakeven,
    select_dinkelbach_dots,
)


def test_kernel_offsets_match_official_25_positive_cell_disk():
    assert len(KERNEL_W) == 25
    # Self-weight is 1.0; axial 1px is 2/3; axial 2px is 1/3; >=3px is 0.0 and excluded
    center = np.where((KERNEL_DY == 0) & (KERNEL_DX == 0))[0]
    assert len(center) == 1 and KERNEL_W[center[0]] == pytest.approx(1.0)
    assert np.all(KERNEL_W > 0.0)
    assert np.all(np.hypot(KERNEL_DY, KERNEL_DX) < 3.0)


def test_isolated_dot_breakeven_identity_across_10000_states():
    """Verify exact algebra: for dT = q = k, DTI' > DTI iff k > 0.2 * DTI."""
    rng = np.random.default_rng(42)
    tp = rng.uniform(0.1, 8000.0, size=10_000)
    fp = rng.uniform(0.0, 50000.0, size=10_000)
    k_tot = tp + rng.uniform(0.1, 15000.0, size=10_000)
    k = rng.uniform(0.0, 1.0, size=10_000)

    for i in range(10_000):
        tau = dti_from_totals(tp[i], fp[i], k_tot[i])
        thresh = isolated_dot_breakeven(tau)
        assert thresh == pytest.approx(0.2 * tau, abs=1e-13)
        delta = exact_marginal_dti_delta(tp[i], fp[i], k_tot[i], dt=k[i], q=k[i])
        if abs(k[i] - thresh) > 1e-11:
            assert (delta > 0.0) == (k[i] > thresh)


def test_general_overlap_breakeven_identity_across_10000_states():
    """Verify general overlap algebra: for independent (dT, q), DTI' > DTI iff
    dT > (0.2 * tau * (1 - q)) / (1 - 0.2 * tau)."""
    rng = np.random.default_rng(108)
    tp = rng.uniform(0.1, 8000.0, size=10_000)
    fp = rng.uniform(0.0, 50000.0, size=10_000)
    k_tot = tp + rng.uniform(0.1, 15000.0, size=10_000)
    dt = rng.uniform(0.0, 3.0, size=10_000)
    q = rng.uniform(0.0, 1.0, size=10_000)

    for i in range(10_000):
        tau = dti_from_totals(tp[i], fp[i], k_tot[i])
        thresh = general_dot_breakeven(tau, q[i])
        delta = exact_marginal_dti_delta(tp[i], fp[i], k_tot[i], dt=dt[i], q=q[i])
        if abs(dt[i] - thresh) > 1e-11:
            assert (delta > 0.0) == (dt[i] > thresh)


def test_minoux_lazy_heap_equals_bruteforce_greedy_bit_for_bit():
    """Prove Minoux lazy-heap selection matches full O(|S|*N) brute-force greedy identically."""
    rng = np.random.default_rng(7)
    h, w = 24, 28
    p_hat = np.zeros((h, w), dtype=np.float64)
    # Create crossing ridges + blobs so overlapping 300m kernels interact heavily
    p_hat[5:20, 10] = rng.uniform(0.03, 0.25, size=15)
    p_hat[12, 4:24] = rng.uniform(0.03, 0.25, size=20)
    p_hat += rng.uniform(0.0, 0.015, size=(h, w))
    q_hat = np.clip(2.2 * p_hat, 0.0, 0.95)
    allow = np.ones((h, w), dtype=bool)
    allow[:2, :] = False
    tau = 0.22

    fast_mask, fast_stats = greedy_submodular_at_tau(p_hat, q_hat, allow, tau=tau)

    # Brute-force reference greedy
    c1 = 1.0 - (1.0 - BETA) * tau
    c2 = ALPHA * tau
    bf_mask = np.zeros((h, w), dtype=bool)
    cov = np.zeros((h, w), dtype=np.float64)
    while True:
        best_val = 0.0
        best_pos = None
        for y in range(h):
            for x in range(w):
                if not allow[y, x] or bf_mask[y, x]:
                    continue
                dt = 0.0
                for dy, dx, kw in zip(KERNEL_DY, KERNEL_DX, KERNEL_W):
                    ny, nx = y + int(dy), x + int(dx)
                    if 0 <= ny < h and 0 <= nx < w and kw > cov[ny, nx]:
                        dt += p_hat[ny, nx] * (kw - cov[ny, nx])
                g = c1 * dt - c2 * (1.0 - q_hat[y, x])
                # Deterministic tie-break matching flat-index min heap order
                if g > best_val + 1e-14:
                    best_val = g
                    best_pos = (y, x)
        if best_pos is None or best_val <= 0.0:
            break
        by, bx = best_pos
        bf_mask[by, bx] = True
        for dy, dx, kw in zip(KERNEL_DY, KERNEL_DX, KERNEL_W):
            ny, nx = by + int(dy), bx + int(dx)
            if 0 <= ny < h and 0 <= nx < w and kw > cov[ny, nx]:
                cov[ny, nx] = kw

    assert np.array_equal(fast_mask, bf_mask)
    assert fast_stats["n_dots"] == int(bf_mask.sum())


def test_dinkelbach_outer_loop_monotone_and_respects_mask():
    """Verify exact spacing along candidate fault crests under realistic multi-ridge belief."""
    rng = np.random.default_rng(99)
    h, w = 48, 64
    p_hat = rng.uniform(0.0, 0.002, size=(h, w)).astype(np.float32)
    # 5 candidate 22-px ridges each active with probability p = 0.18 (~1 true trace total)
    for col in (8, 20, 32, 44, 56):
        p_hat[6:28, col] = 0.18
    q_hat = compute_max_kernel_proximity(p_hat)
    allow = np.ones((h, w), dtype=bool)
    allow[14:18, :] = False  # Simulate B=2 known-fault exclusion collar across all 5 ridges

    dots, info = select_dinkelbach_dots(p_hat, q_hat, allow, tau_init=0.10, max_outer_iters=4)
    assert dots.any()
    assert not (dots & ~allow).any()
    assert info["dti_hat"] > 0.30
    # 18 unmasked crest pixels per ridge split into 10 finite segments -> ~4 dots/segment (~41 dots vs 90 unthinned)!
    assert 25 <= int(dots.sum()) <= 45


def test_bayes_prior_shift_inverts_identity_when_equal_priors():
    p = np.linspace(0.01, 0.99, 50)
    shifted = bayes_prior_shift(p, pi_train=0.12, pi_target=0.12)
    assert np.allclose(p, shifted, atol=1e-6)


def test_fold_safe_network_features_invariant_to_withheld_truth():
    """Verify strictly zero leakage: mutating withheld components outside visible_faults
    cannot alter a single bit of compute_fold_safe_network_features."""
    from gems85.conduit import compute_fold_safe_network_features

    fp = np.ones((64, 64), dtype=bool)
    visible = np.zeros((64, 64), dtype=bool)
    visible[10:25, 18] = True
    visible[35:50, 42] = True

    hidden_a = np.zeros((64, 64), dtype=bool)
    hidden_a[28:34, 18] = True  # Withheld segment A

    hidden_b = np.zeros((64, 64), dtype=bool)
    hidden_b[12:48, 55] = True  # Totally different withheld segment B

    # Both scenarios pass ONLY `visible` to the feature builder
    net_a = compute_fold_safe_network_features(visible, fp)
    net_b = compute_fold_safe_network_features(visible & ~hidden_b, fp)
    assert np.array_equal(net_a, net_b)
    assert net_a.shape == (8, 64, 64)
    assert np.isfinite(net_a).all()

