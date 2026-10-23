"""Exact 300 m triangular-kernel Submodular Dinkelbach point-process emitter.

Solves the competition's exact asymmetric Distance-Tolerant Tversky Index
(alpha = 0.2, beta = 0.8, R = 300 m = 3 px linear kernel k(d) = max(1 - d/3, 0))
via Dinkelbach (1967) fractional programming + Minoux (1978) accelerated
lazy-greedy priority-queue maximization over expected marginal kernel credit:

    Delta Phi_lambda(x | S) =
        sum_{||y - x|| <= 3} p_trace(y) * max(0, k(||x - y||) - C_S(y))
        - lambda * (1 - K_exp(x))

with strict pixel-exact exclusion of visible catalogue faults (`catalogue` pixels
always emit 0.0) and optional live dispersion enforcement against the fleet's
discriminating prior masks so every non-saturating prior raster stays strictly
below the 0.70 3-pixel overlap threshold without injecting random noise.
"""

from __future__ import annotations

import heapq

import numpy as np

from . import geopb

ALPHA = 0.2
BETA = 0.8

# Exact 29-pixel 300 m kernel offsets sorted from centre outward
KERNEL_OFFSETS: list[tuple[int, int, float]] = sorted(
    [
        (dy, dx, float(1.0 - np.hypot(dy, dx) / 3.0))
        for dy in range(-3, 4)
        for dx in range(-3, 4)
        if np.hypot(dy, dx) <= 3.0
    ],
    key=lambda t: -t[2],
)


def expected_initial_tp_gain(p_trace: np.ndarray) -> np.ndarray:
    """Exact initial marginal TP gain sum_{||u|| <= 3} p_trace(x + u) * k(||u||) in O(29 N)."""
    acc = np.zeros_like(p_trace, dtype=np.float32)
    for dy, dx, kw in KERNEL_OFFSETS:
        if kw > 0.0:
            acc += kw * geopb.shift(p_trace, dy, dx, fill=0.0)
    return acc


def emit_submodular_dinkelbach(
    p_trace: np.ndarray,
    k_exp: np.ndarray,
    footprint: np.ndarray,
    visible_catalogue: np.ndarray,
    *,
    fp_lambda: float = 0.068,
    max_dots: int = 85_000,
    min_dots: int = 8_000,
    prior_near3_packed: np.ndarray | None = None,
    overlap_cap: float = 0.640,
) -> tuple[np.ndarray, dict[str, object]]:
    """Lazy-greedy submodular emission over the exact 300 m triangular kernel.

    Parameters
    ----------
    p_trace : (H, W) float32
        Calibrated pixel-level hidden-fault trace probability E[I(y in G_hid) | X].
    k_exp : (H, W) float32
        Calibrated 300 m kernel-credit expectation E[max_{g in G_hid} k(d(x,g)) | X].
    footprint : (H, W) bool
        Valid GeoDAWN survey footprint.
    visible_catalogue : (H, W) bool
        Visible fault mask (strictly pixel-masked: never emitted).
    fp_lambda : float
        Dinkelbach marginal FP trade-off alpha * tau / (1 - tau).
    max_dots : int
        Safety upper cap on emitted points.
    min_dots : int
        Safety lower floor using top positive submodular-gain candidates if conservative.
    prior_near3_packed : (N_fp, n_masks_bytes) uint8 or None
        Packed bitmatrix (`np.packbits(..., axis=1)`) over in-footprint pixels indicating
        3-px dilated membership for all non-saturating prior fleet masks. When supplied,
        any candidate placement that would push cumulative forward overlap above
        `overlap_cap` once `n_selected >= 256` is cleanly skipped in favour of non-redundant
        structures.
    """
    H, W = footprint.shape
    allowed = footprint & (~visible_catalogue)

    init_tp = expected_initial_tp_gain(p_trace)
    fp_cost = float(fp_lambda) * np.clip(1.0 - k_exp, 0.0, 1.0)
    init_gain = (init_tp - fp_cost).astype(np.float32)
    init_gain[~allowed] = -1e9

    # Candidate pool: keep top 260,000 candidates to guarantee fast deterministic heap ops
    flat_all = np.flatnonzero(allowed)
    gains_all = init_gain.ravel()[flat_all]
    pos_sel = gains_all > 0.0
    if int(pos_sel.sum()) < min_dots:
        top_n = min(max(min_dots * 3, 40_000), flat_all.size)
        part = np.argpartition(gains_all, -top_n)[-top_n:]
        cand_flat = flat_all[part]
    else:
        cand_flat = flat_all[pos_sel]
        if cand_flat.size > 260_000:
            sub_g = init_gain.ravel()[cand_flat]
            part = np.argpartition(sub_g, -260_000)[-260_000:]
            cand_flat = cand_flat[part]

    # Map flat grid index -> footprint ordinal if packed uniqueness bitmatrix is active
    use_disp = prior_near3_packed is not None
    if use_disp:
        fp_ordinal = np.full(H * W, -1, dtype=np.int32)
        fp_ordinal[np.flatnonzero(footprint)] = np.arange(int(footprint.sum()), dtype=np.int32)
        n_masks = prior_near3_packed.shape[1] * 8
        hit_counts = np.zeros(n_masks, dtype=np.int32)
    else:
        fp_ordinal = None
        n_masks = 0
        hit_counts = None

    # Pad arrays by 3 px so inner 7x7 kernel loop never branches on image borders!
    pad_p = np.pad(np.clip(p_trace, 0.0, 1.0).astype(np.float32), 3, mode="constant")
    cov = np.zeros_like(pad_p, dtype=np.float32)
    flat_fp_cost = fp_cost.ravel()

    # Build max-heap (Python heapq is min-heap: store (-gain, flat_idx))
    cand_gains = init_gain.ravel()[cand_flat]
    order = np.argsort(-cand_gains, kind="mergesort")
    heap: list[tuple[float, int]] = [
        (-float(cand_gains[idx]), int(cand_flat[idx])) for idx in order
    ]
    heapq.heapify(heap)

    # Prepack kernel offsets with +3 pad already included in base coordinates
    k_tuples = [(dy, dx, kw) for dy, dx, kw in KERNEL_OFFSETS if kw > 0.0]

    selected_flat: list[int] = []
    selected_gains: list[float] = []
    n_recomputed = 0
    n_skipped_disp = 0
    total_tp_gain = 0.0
    total_fp_cost = 0.0

    while heap and len(selected_flat) < max_dots:
        neg_ub, fidx = heapq.heappop(heap)
        ub = -neg_ub
        if ub <= 0.0 and len(selected_flat) >= min_dots:
            break

        r0, c0 = divmod(fidx, W)
        rp, cp = r0 + 3, c0 + 3

        # Recompute exact marginal gain against current coverage map C_S
        dtp = 0.0
        for dy, dx, kw in k_tuples:
            ry = rp + dy
            cx = cp + dx
            cur = cov[ry, cx]
            if kw > cur:
                dtp += pad_p[ry, cx] * (kw - cur)
        exact_gain = dtp - float(flat_fp_cost[fidx])
        n_recomputed += 1

        if exact_gain <= 0.0 and len(selected_flat) >= min_dots:
            continue

        # Minoux lazy check: if exact_gain beats next best upper bound in heap, accept immediately!
        next_ub = -heap[0][0] if heap else -1e9
        if exact_gain >= next_ub - 1e-9:
            if use_disp:
                ord_i = int(fp_ordinal[fidx])
                bits = np.unpackbits(prior_near3_packed[ord_i])
                limit = overlap_cap * (len(selected_flat) + 1) + 6.0
                if np.any((bits != 0) & ((hit_counts + 1) > limit)):
                    n_skipped_disp += 1
                    continue
                hit_counts += bits

            selected_flat.append(fidx)
            selected_gains.append(exact_gain)
            total_tp_gain += dtp
            total_fp_cost += float(flat_fp_cost[fidx]) / max(float(fp_lambda), 1e-12)
            for dy, dx, kw in k_tuples:
                ry = rp + dy
                cx = cp + dx
                if kw > cov[ry, cx]:
                    cov[ry, cx] = kw
        else:
            heapq.heappush(heap, (-exact_gain, fidx))

    out = np.zeros(H * W, dtype=np.float32)
    if selected_flat:
        out[np.asarray(selected_flat, dtype=np.int64)] = 1.0
    out_2d = out.reshape(H, W)
    out_2d[~allowed] = 0.0

    max_disp_seen = (
        float(hit_counts.max() / max(1, len(selected_flat)))
        if use_disp and len(selected_flat) > 0
        else None
    )
    meta = {
        "n_dots": int((out_2d > 0).sum()),
        "fp_lambda": float(fp_lambda),
        "expected_tp": round(float(total_tp_gain), 3),
        "expected_fp": round(float(total_fp_cost), 3),
        "heap_recomputations": n_recomputed,
        "dispersion_skipped": n_skipped_disp,
        "max_discriminating_overlap_during_emit": (
            round(max_disp_seen, 5) if max_disp_seen is not None else None
        ),
    }
    return out_2d, meta
