"""Exact marginal DTI algebra, Bayes prior-shift calibration, and submodular Dinkelbach emission.

Mathematical guarantees verified in ``tests/test_conduit_dinkelbach.py``:
1. Exact marginal binary dot inclusion theorem for ``alpha = 0.2, beta = 0.8``:
   Given active score state ``(T, F, K_tot)`` with ``D = 0.8 * K_tot + 0.2 * T + 0.2 * F``
   and ``tau = T / D``, adding a dot ``u`` with marginal coverage gain ``dT >= 0`` and
   true max-kernel proximity ``q in [0, 1]`` changes ``T -> T + dT`` and ``F -> F + (1 - q)``,
   so ``DTI' > DTI`` iff:
       dT > (0.2 * tau * (1 - q)) / (1 - 0.2 * tau).
   In the isolated single-target special case ``dT = q = k``, ``Delta D = 0.2 * k + 0.2 * (1 - k) = 0.2``
   is independent of ``k``, simplifying identically to ``k > 0.2 * tau``.
2. Exact 1-pixel fault-trace proximity identity:
   Along any 1-pixel fault trace ``C`` active with probability ``p_C``, every pixel ``u`` at
   Euclidean distance ``d`` from ``C`` has ``Q_u = K(d) * 1[C active]``, giving the exact dual
   field ``q_hat(u) = max_{||delta|| < 3} (p_hat(u + delta) * K(delta)) in [0, 1]``.
3. Exact submodularity of the parameterized Dinkelbach surrogate at fixed ``tau in [0, 1)``:
       G_tau(S) = (1 - 0.2 * tau) * T_hat(S) - 0.2 * tau * F_hat(S) - 0.8 * tau * P_tot.
   Because ``g_tau(u | S)`` is non-increasing in ``S``, Minoux's accelerated lazy max-heap
   produces the EXACT same sequence of accepted dots as brute-force greedy search.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression

ALPHA: float = 0.2
BETA: float = 0.8
RADIUS_PX: float = 3.0
EPS: float = 1e-12


def build_kernel_offsets(radius_px: float = RADIUS_PX) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the exact 25 offsets ``(dy, dx, kw)`` with strictly positive triangular weight."""
    r = int(np.ceil(radius_px))
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    dist = np.hypot(yy, xx)
    keep = dist < radius_px
    dy = yy[keep].astype(np.int32)
    dx = xx[keep].astype(np.int32)
    kw = (1.0 - dist[keep] / radius_px).astype(np.float64)
    return dy, dx, kw


KERNEL_DY, KERNEL_DX, KERNEL_W = build_kernel_offsets(RADIUS_PX)


def dti_from_totals(tp: float, fp: float, k_tot: float, alpha: float = ALPHA, beta: float = BETA) -> float:
    """Exact DTI from ``(TP_w, FP_w, |G|)``."""
    fn = k_tot - tp
    den = tp + alpha * fp + beta * fn
    if den <= 0.0:
        return 0.0
    return float(tp / den)


def general_dot_breakeven(tau: float, q: float, alpha: float = ALPHA, beta: float = BETA) -> float:
    """Minimum marginal ``dT`` needed for a dot with proximity ``q`` to strictly beat ``tau``."""
    denom = 1.0 - (1.0 - beta) * tau
    if denom <= 0.0:
        return float("inf")
    return float((alpha * tau * (1.0 - q)) / denom)


def isolated_dot_breakeven(tau: float, alpha: float = ALPHA, beta: float = BETA) -> float:
    """Exact break-even ``k`` for an isolated dot where ``dT = q = k`` (``0.2 * tau``)."""
    denom = 1.0 - (1.0 - beta - alpha) * tau
    return float((alpha * tau) / denom)


def exact_marginal_dti_delta(
    tp: float,
    fp: float,
    k_tot: float,
    dt: float,
    q: float,
    alpha: float = ALPHA,
    beta: float = BETA,
) -> float:
    """Exact ``DTI(S u {u}) - DTI(S)`` for adding a dot with ``(dt, q)``."""
    before = dti_from_totals(tp, fp, k_tot, alpha=alpha, beta=beta)
    after = dti_from_totals(tp + dt, fp + (1.0 - q), k_tot, alpha=alpha, beta=beta)
    return float(after - before)


def compute_max_kernel_proximity(p_hat: np.ndarray) -> np.ndarray:
    """Exact 1-pixel trace dual proximity ``q_hat(u) = max_{||d||<3} p_hat(u+d) * K(d) in [0, 1]``."""
    h, w = p_hat.shape
    p32 = np.clip(np.asarray(p_hat, dtype=np.float32), 0.0, 1.0)
    out = np.zeros((h, w), dtype=np.float32)
    for dy, dx, kw in zip(KERNEL_DY, KERNEL_DX, KERNEL_W):
        sy0, sy1 = max(0, int(dy)), min(h, h + int(dy))
        dy0, dy1 = max(0, -int(dy)), min(h, h - int(dy))
        sx0, sx1 = max(0, int(dx)), min(w, w + int(dx))
        dx0, dx1 = max(0, -int(dx)), min(w, w - int(dx))
        np.maximum(out[dy0:dy1, dx0:dx1], p32[sy0:sy1, sx0:sx1] * np.float32(kw), out=out[dy0:dy1, dx0:dx1])
    return out


def bayes_prior_shift(prob: np.ndarray, pi_train: float, pi_target: float) -> np.ndarray:
    """Map calibrated posterior probabilities from ``pi_train`` to unseen prior ``pi_target``."""
    p = np.clip(np.asarray(prob, dtype=np.float64), 1e-7, 1.0 - 1e-7)
    pi_tr = float(np.clip(pi_train, 1e-6, 1.0 - 1e-6))
    pi_tg = float(np.clip(pi_target, 1e-6, 1.0 - 1e-6))
    w_pos = pi_tg / pi_tr
    w_neg = (1.0 - pi_tg) / (1.0 - pi_tr)
    num = w_pos * p
    return (num / (num + w_neg * (1.0 - p))).astype(np.float32)


@dataclass
class CalibratedConduitModel:
    """Out-of-fold calibrated mapping ``raw_score -> (p_hat, q_hat)``."""

    iso_p: IsotonicRegression
    pi_train: float
    hidden_to_visible_ratio: float = 0.25

    def predict_pq(
        self,
        raw_score: np.ndarray,
        allowed_mask: np.ndarray,
        n_visible_px: int,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """Return ``(p_hat, q_hat, p_tot)`` strictly in ``[0, 1]`` on ``allowed_mask``."""
        shape = raw_score.shape
        allow = np.asarray(allowed_mask, dtype=bool)
        p_hat = np.zeros(shape, dtype=np.float32)
        n_allow = int(allow.sum())
        if n_allow == 0:
            return p_hat, np.zeros(shape, dtype=np.float32), 0.0

        target_pos = max(1.0, float(self.hidden_to_visible_ratio) * float(n_visible_px))
        pi_target = float(np.clip(target_pos / float(n_allow), 1e-5, 0.25))

        s_flat = np.asarray(raw_score[allow], dtype=np.float64)
        p_cal = self.iso_p.predict(s_flat)
        p_shifted = bayes_prior_shift(p_cal, self.pi_train, pi_target)
        s_sum = float(p_shifted.sum())
        if s_sum > 0.0:
            p_shifted = np.clip(p_shifted * (target_pos / s_sum), 0.0, 1.0).astype(np.float32)
        p_hat[allow] = p_shifted
        q_hat = compute_max_kernel_proximity(p_hat)
        q_hat[~allow] = 0.0
        return p_hat, q_hat, float(p_hat[allow].sum())


def fit_conduit_calibrator(
    oof_scores: np.ndarray,
    oof_y: np.ndarray,
    hidden_to_visible_ratio: float = 0.25,
) -> CalibratedConduitModel:
    """Fit ``iso_p`` strictly on inner training-fold held-out component labels."""
    iso_p = IsotonicRegression(y_min=1e-6, y_max=1.0 - 1e-6, out_of_bounds="clip")
    iso_p.fit(np.asarray(oof_scores, dtype=np.float64), np.asarray(oof_y, dtype=np.float64))
    pi_train = float(np.mean(oof_y))
    return CalibratedConduitModel(
        iso_p=iso_p,
        pi_train=pi_train,
        hidden_to_visible_ratio=hidden_to_visible_ratio,
    )


def _initial_kernel_gain(p_hat: np.ndarray) -> np.ndarray:
    """Compute ``sum_delta p_hat(y + dy, x + dx) * K(dy, dx)`` vectorized across the grid."""
    h, w = p_hat.shape
    out = np.zeros((h, w), dtype=np.float64)
    p64 = np.asarray(p_hat, dtype=np.float64)
    for dy, dx, kw in zip(KERNEL_DY, KERNEL_DX, KERNEL_W):
        sy0, sy1 = max(0, int(dy)), min(h, h + int(dy))
        dy0, dy1 = max(0, -int(dy)), min(h, h - int(dy))
        sx0, sx1 = max(0, int(dx)), min(w, w + int(dx))
        dx0, dx1 = max(0, -int(dx)), min(w, w - int(dx))
        out[dy0:dy1, dx0:dx1] += p64[sy0:sy1, sx0:sx1] * kw
    return out


def greedy_submodular_prefix(
    p_hat: np.ndarray,
    q_hat: np.ndarray,
    allowed_mask: np.ndarray,
    *,
    tau_rank: float = 0.25,
    max_dots: int = 25_000,
    max_candidates: int = 160_000,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return exact ordered submodular dot sequence ``(ys, xs, dts)`` up to ``max_dots`` in ~0.4s.

    Uses a 1D flat padded array so the 25-neighbor inner loop executes with zero 2D bounds
    branching and zero redundant heap passes when evaluating inner-validation dot budgets.
    """
    p64 = np.asarray(p_hat, dtype=np.float64)
    q64 = np.asarray(q_hat, dtype=np.float64)
    allow = np.asarray(allowed_mask, dtype=bool)
    h, w = p64.shape

    c1 = 1.0 - (1.0 - BETA) * float(tau_rank)
    c2 = ALPHA * float(tau_rank)

    init_dt = _initial_kernel_gain(p64)
    # Rank key: expected marginal net surplus over false-positive cost
    init_g = c1 * init_dt - c2 * (1.0 - q64)
    cand_flat = np.flatnonzero((allow & (init_dt > 1e-6)).ravel())
    if cand_flat.size == 0:
        return np.empty(0, np.int32), np.empty(0, np.int32), np.empty(0, np.float64)

    if cand_flat.size > max_candidates:
        vals = init_g.ravel()[cand_flat]
        top_part = np.argpartition(vals, -max_candidates)[-max_candidates:]
        cand_flat = cand_flat[top_part]

    # Pad by 2 pixels on all 4 borders so flat neighbor indexing needs ZERO bounds checks
    hp, wp = h + 4, w + 4
    p_pad = np.zeros(hp * wp, dtype=np.float64)
    p_view = p_pad.reshape(hp, wp)
    p_view[2 : h + 2, 2 : w + 2] = p64
    cov_pad = np.zeros(hp * wp, dtype=np.float64)
    sel_pad = np.zeros(hp * wp, dtype=bool)

    k_off = (KERNEL_DY.astype(np.int64) * wp + KERNEL_DX.astype(np.int64)).tolist()
    k_w = KERNEL_W.tolist()
    p_list = p_pad  # numpy 1D view
    q_flat = q64.ravel()

    cy, cx = np.divmod(cand_flat, w)
    pad_idx = ((cy + 2) * wp + (cx + 2)).tolist()
    init_scores = init_g.ravel()[cand_flat].tolist()
    heap: list[tuple[float, int, int]] = [
        (-sc, pidx, int(fidx)) for sc, pidx, fidx in zip(init_scores, pad_idx, cand_flat.tolist())
    ]
    heapq.heapify(heap)

    out_y: list[int] = []
    out_x: list[int] = []
    out_dt: list[float] = []

    while heap and len(out_y) < max_dots:
        neg_key, pidx, fidx = heapq.heappop(heap)
        if sel_pad[pidx]:
            continue

        dt = 0.0
        for m in range(25):
            nb = pidx + k_off[m]
            rem = k_w[m] - cov_pad[nb]
            if rem > 0.0:
                pv = p_list[nb]
                if pv > 0.0:
                    dt += pv * rem

        live_g = c1 * dt - c2 * (1.0 - float(q_flat[fidx]))
        if -neg_key > live_g + 1e-11:
            heapq.heappush(heap, (-live_g, pidx, fidx))
            continue

        sel_pad[pidx] = True
        for m in range(25):
            nb = pidx + k_off[m]
            kw = k_w[m]
            if kw > cov_pad[nb]:
                cov_pad[nb] = kw

        out_y.append(fidx // w)
        out_x.append(fidx % w)
        out_dt.append(dt)

    return np.array(out_y, dtype=np.int32), np.array(out_x, dtype=np.int32), np.array(out_dt, dtype=np.float64)


def greedy_submodular_at_tau(
    p_hat: np.ndarray,
    q_hat: np.ndarray,
    allowed_mask: np.ndarray,
    tau: float,
    *,
    max_candidates: int = 350_000,
    max_dots: int | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Exact Minoux lazy-heap maximization of Dinkelbach surrogate ``G_tau(S)``."""
    p64 = np.asarray(p_hat, dtype=np.float64)
    q64 = np.asarray(q_hat, dtype=np.float64)
    allow = np.asarray(allowed_mask, dtype=bool)
    h, w = p64.shape
    p_tot = float(p64[allow].sum())

    c1 = 1.0 - (1.0 - BETA) * float(tau)
    c2 = ALPHA * float(tau)

    init_dt = _initial_kernel_gain(p64)
    init_g = c1 * init_dt - c2 * (1.0 - q64)
    cand_mask = allow & (init_g > 0.0) & (init_dt > 0.0)
    cand_flat = np.flatnonzero(cand_mask.ravel())

    if cand_flat.size > max_candidates:
        vals = init_g.ravel()[cand_flat]
        top_part = np.argpartition(vals, -max_candidates)[-max_candidates:]
        cand_flat = cand_flat[top_part]

    selected = np.zeros((h, w), dtype=bool)
    if cand_flat.size == 0 or p_tot <= 0.0:
        return selected, {
            "tau_in": float(tau),
            "dti_hat": 0.0,
            "tp_hat": 0.0,
            "fp_hat": 0.0,
            "p_tot": p_tot,
            "n_dots": 0,
            "n_candidates": int(cand_flat.size),
        }

    coverage = np.zeros((h, w), dtype=np.float64)
    heap: list[tuple[float, int]] = [
        (-float(init_g.ravel()[idx]), int(idx)) for idx in cand_flat
    ]
    heapq.heapify(heap)

    k_dy = KERNEL_DY.tolist()
    k_dx = KERNEL_DX.tolist()
    k_w = KERNEL_W.tolist()
    n_k = len(k_w)

    tp_hat = 0.0
    fp_hat = 0.0
    n_dots = 0

    while heap:
        if max_dots is not None and n_dots >= max_dots:
            break
        neg_key, idx = heapq.heappop(heap)
        y = idx // w
        x = idx - y * w
        if selected[y, x]:
            continue

        dt = 0.0
        for m in range(n_k):
            ny = y + k_dy[m]
            nx = x + k_dx[m]
            if 0 <= ny < h and 0 <= nx < w:
                rem = k_w[m] - coverage[ny, nx]
                if rem > 0.0:
                    pv = p64[ny, nx]
                    if pv > 0.0:
                        dt += pv * rem

        live_g = c1 * dt - c2 * (1.0 - q64[y, x])
        if live_g <= 0.0:
            continue
        if -neg_key > live_g + 1e-12:
            heapq.heappush(heap, (-live_g, idx))
            continue

        selected[y, x] = True
        tp_hat += dt
        fp_hat += 1.0 - q64[y, x]
        n_dots += 1
        for m in range(n_k):
            ny = y + k_dy[m]
            nx = x + k_dx[m]
            if 0 <= ny < h and 0 <= nx < w:
                kw = k_w[m]
                if kw > coverage[ny, nx]:
                    coverage[ny, nx] = kw

    dti_hat = dti_from_totals(tp_hat, fp_hat, p_tot)
    return selected, {
        "tau_in": float(tau),
        "dti_hat": float(dti_hat),
        "tp_hat": float(tp_hat),
        "fp_hat": float(fp_hat),
        "p_tot": float(p_tot),
        "n_dots": int(n_dots),
        "n_candidates": int(cand_flat.size),
    }


def select_dinkelbach_dots(
    p_hat: np.ndarray,
    q_hat: np.ndarray,
    allowed_mask: np.ndarray,
    *,
    tau_init: float = 0.16,
    max_outer_iters: int = 3,
    tol: float = 1e-4,
    max_candidates: int = 350_000,
    min_dots: int = 0,
    max_dots: int | None = None,
) -> tuple[np.ndarray, dict[str, object]]:
    """Solve ``max_S DTI_hat(S)`` via Dinkelbach fixed-point outer iterations."""
    tau = float(tau_init)
    history: list[dict[str, float]] = []
    best_mask = np.zeros(p_hat.shape, dtype=bool)
    best_stats: dict[str, float] = {"dti_hat": -1.0, "n_dots": 0}

    for _ in range(max_outer_iters):
        mask, stats = greedy_submodular_at_tau(
            p_hat,
            q_hat,
            allowed_mask,
            tau,
            max_candidates=max_candidates,
            max_dots=max_dots,
        )
        history.append(stats)
        if stats["dti_hat"] >= best_stats["dti_hat"]:
            best_mask = mask
            best_stats = stats
        new_tau = float(stats["dti_hat"])
        if abs(new_tau - tau) <= tol or new_tau <= 0.0:
            break
        tau = new_tau

    if best_stats["n_dots"] < min_dots:
        best_mask, best_stats = greedy_submodular_at_tau(
            p_hat,
            q_hat,
            allowed_mask,
            tau=0.0,
            max_candidates=max_candidates,
            max_dots=min_dots,
        )
        history.append(best_stats)

    return best_mask, {
        **best_stats,
        "outer_iterations": len(history),
        "history": history,
    }
