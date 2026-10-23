"""RELAY: fault-network completion geometry from a *visible* catalogue mask.

Session lane `arena/22847afd` (pre-registered in
research/session-22847afd-hypotheses.md).  The idea is topological, not
photometric: a mapped fault network is geometrically incomplete where segments
terminate abruptly or face each other across small gaps.  This module turns that
incompleteness into a scalar field using ONLY the catalogue mask it is given
(in the holdout that mask is `fold.visible`, so nothing about withheld segments
can leak in):

  1. label 8-connected segments, drop specks (< 8 px);
  2. find each segment's two terminal tips (1-neighbour endpoints when the
     rasterised trace is a clean 1-px line, PCA-projection extremes otherwise);
  3. estimate tip strike by PCA of the terminal 15 px, oriented *outward*;
  4. cast decaying **extension rays** up to `ext_len` px beyond every tip;
  5. add **relay bridges** between tips of *different* segments that face each
     other across 10..`bridge_len` px with small strike misfit.

The result is a geometry-only prior.  It is meant to *gate* a geophysical line
field (extensions into geologically blank ground should not emit), which is how
the experiments use it.  Named mimic: genuine displacement-death tips, where an
extension ray overshoots into intact rock.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree


def _segment_tips(mask: np.ndarray, min_len: int = 8, terminal_px: float = 15.0):
    """Return tips as arrays (y, x, uy, ux, seg_id, seg_len); u points outward."""
    lab, n = ndi.label(mask, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        z = np.empty(0)
        return z, z, z, z, np.empty(0, dtype=int), np.empty(0, dtype=int)

    # neighbour count within the mask (for clean-line endpoints)
    cnt = ndi.convolve(mask.astype(np.int32), np.ones((3, 3), dtype=np.int32),
                       mode="constant") - 1
    ys_all, xs_all = np.nonzero(mask)
    lab_at = lab[ys_all, xs_all]
    order = np.argsort(lab_at, kind="stable")
    ys_s, xs_s, lab_s = ys_all[order], xs_all[order], lab_at[order]
    starts = np.searchsorted(lab_s, np.arange(1, n + 2))

    TY, TX, UY, UX, SID, SLEN = [], [], [], [], [], []
    for sid in range(1, n + 1):
        a, b = starts[sid - 1], starts[sid]
        if b - a < min_len:
            continue
        ys = ys_s[a:b].astype(np.float64)
        xs = xs_s[a:b].astype(np.float64)
        c = np.stack([ys, xs], axis=1)
        ctr = c.mean(axis=0)
        # PCA strike of the whole segment
        cov = np.cov((c - ctr).T)
        if not np.isfinite(cov).all():
            continue
        w, v = np.linalg.eigh(cov)
        pc1 = v[:, -1]                                   # (y, x) strike direction
        proj = (c - ctr) @ pc1

        # candidate tips: clean endpoints if exactly 2, else projection extremes
        ends = (cnt[ys_s[a:b].astype(int), xs_s[a:b].astype(int)] == 1)
        if ends.sum() == 2:
            tip_idx = np.nonzero(ends)[0]
        else:
            tip_idx = np.array([int(np.argmin(proj)), int(np.argmax(proj))])

        for ti in tip_idx:
            tip = c[ti]
            # terminal subset: pixels within terminal_px (projected) of the tip
            dproj = np.abs(proj - proj[ti])
            term = c[dproj <= terminal_px]
            if term.shape[0] < 3:
                term = c[np.argsort(dproj)[: min(5, c.shape[0])]]
            tctr = term.mean(axis=0)
            tcov = np.cov((term - tctr).T) if term.shape[0] > 2 else cov
            tw, tv = np.linalg.eigh(tcov)
            u = tv[:, -1].astype(np.float64)
            outward = tip - tctr
            if np.dot(u, outward) < 0:
                u = -u
            nrm = np.hypot(u[0], u[1])
            if nrm == 0:
                continue
            u /= nrm
            TY.append(tip[0]); TX.append(tip[1])
            UY.append(u[0]); UX.append(u[1])
            SID.append(sid); SLEN.append(int(b - a))
    return (np.array(TY), np.array(TX), np.array(UY), np.array(UX),
            np.array(SID, dtype=int), np.array(SLEN, dtype=int))


def relay_field(mask: np.ndarray, footprint: np.ndarray, *,
                ext_len: float = 60.0, ext_decay: float = 30.0,
                bridge_len: float = 80.0, bridge_min: float = 10.0,
                bridge_weight: float = 1.5, min_len: int = 8,
                smooth_sigma: float = 1.0) -> np.ndarray:
    """Geometry-only network-completion field (float32, 0 outside footprint).

    `mask` must be the catalogue the caller is allowed to see (fold-visible in
    the holdout, the full catalogue only for the final submission build).
    """
    H, W = mask.shape
    field = np.zeros((H, W), dtype=np.float32)
    ty, tx, uy, ux, sid, slen = _segment_tips(mask.astype(bool), min_len=min_len)
    if ty.size == 0:
        return field
    len_w = np.minimum(1.0, slen / 30.0)               # longer segments carry further

    # ---- extension rays --------------------------------------------------
    ts = np.arange(3.0, ext_len + 1.0, 1.0)
    decay = np.exp(-ts / ext_decay).astype(np.float32)
    for t, wgt in zip(ts, decay):
        yy = np.rint(ty + t * uy).astype(int)
        xx = np.rint(tx + t * ux).astype(int)
        ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
        np.add.at(field, (yy[ok], xx[ok]), (wgt * len_w[ok]).astype(np.float32))

    # ---- relay bridges between facing tips of different segments ---------
    pts = np.stack([ty, tx], axis=1)
    tree = cKDTree(pts)
    pairs = tree.query_pairs(r=bridge_len, output_type="ndarray")
    if pairs.size:
        i, j = pairs[:, 0], pairs[:, 1]
        diff = pts[j] - pts[i]                          # i -> j
        dist = np.hypot(diff[:, 0], diff[:, 1])
        keep = (sid[i] != sid[j]) & (dist >= bridge_min)
        if keep.any():
            i, j, diff, dist = i[keep], j[keep], diff[keep], dist[keep]
            dhat = diff / dist[:, None]
            ui = np.stack([uy[i], ux[i]], axis=1)
            uj = np.stack([uy[j], ux[j]], axis=1)
            face_i = (ui * dhat).sum(axis=1)            # i points toward j
            face_j = -(uj * dhat).sum(axis=1)           # j points toward i
            okp = (face_i > 0.7) & (face_j > 0.7)
            for a, b, d in zip(i[okp], j[okp], dist[okp]):
                steps = max(2, int(round(float(d))))
                tt = np.linspace(0.0, 1.0, steps + 1)[1:-1]
                yy = np.rint(ty[a] + tt * (ty[b] - ty[a])).astype(int)
                xx = np.rint(tx[a] + tt * (tx[b] - tx[a])).astype(int)
                wgt = bridge_weight * min(len_w[a], len_w[b]) * float(np.exp(-d / 60.0))
                np.add.at(field, (yy, xx), np.float32(wgt))

    if smooth_sigma > 0:
        field = ndi.gaussian_filter(field, smooth_sigma, mode="constant")
    field[mask.astype(bool)] = 0.0                      # geometry is about the gaps
    field[~footprint] = 0.0
    return field.astype(np.float32)


def tip_table(mask: np.ndarray, min_len: int = 8) -> dict:
    """Diagnostics: how many segments/tips the field is built from."""
    lab, n = ndi.label(mask.astype(bool), structure=np.ones((3, 3), dtype=int))
    ty, *_ = _segment_tips(mask.astype(bool), min_len=min_len)
    return {"n_segments_total": int(n), "n_tips_used": int(ty.size)}
