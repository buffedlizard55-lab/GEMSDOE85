"""MASS: change only the amount of mass, then ask whether the *ranking* of that mass matters.

Context this session inherits
------------------------------
The lineage's climb (0.1922 -> 0.2778) is confounded: every rung changed mass *and* position at
the same time, and the ledger explicitly warns "mass is confounded with field". The previous
session closed PRUNE at 2 px (0/5 folds at 3 px) leaving the confound unresolved. This module
attacks it directly. Three variants, all from R0, all MASS:

    mass-m10e   remove exactly 10 % of dots, chosen by a rebuilt structural ranking (smallest
                first).  This is the brief's "drop the lowest-ranked 10 %".
    mass-m10u   remove exactly 10 % of dots, chosen uniformly at random (seed 20261023).
                The control: identical mass change, no ranking.
    mass-p10    ADD 10 % of dots to the parent's field, largest structural extent first.

The m10e / m10u pair is the experiment: same mass removed, different ranking. If they differ, the
*ranking* matters and a better ranking is worth more than a mass sweep. If they agree, mass is what
matters and the final file should be chosen on the mass axis alone.

Why the ranking had to be rebuilt, and why it is structural
-----------------------------------------------------------
R0 stores no scores: ``h33-2-b2`` is a 0/1 raster, and the field it sits on (``H19-5``) is binary
too (all 121,131 support pixels equal 1.0). The parent's *literal* ranking is therefore the
emission order of ``poisson_thin`` — descending field value, ties broken by raster order — which on
a constant field degenerates to **row-major scan order**. Dropping "the lowest-ranked 10 %" with
that ranking would delete the bottom of the image: a region-isolated, patterned file, which the
brief forbids and which would measure geography rather than mass. IR-V2-08 records this.

The rebuilt ranking is instead catalogue-free and geological: the size of the connected structure a
dot belongs to, after bridging the field's 1-px gaps (a single-pixel gap is a rasterisation artefact,
not a geological break). The field has 26,645 raw fragments but only 10,767 bridged components
(r = 1), so bridged extent separates "on a coherent lineament" from "isolated speckle". Measured on
R0: median extent 97 px, p90 865 px, 28.3 % of dots on structures < 30 px. Crucially this is **not**
a repackaged PRUNE: the smallest-10 % selection has mean catalogue distance 30.3 px against 29.0 px
for all of R0, i.e. it is very slightly *further* from the known traces, and it overlaps a uniform
random 10 % on only 442 of 3,765 dots (chance ~376).

Nothing here selects a slot or a submission.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import lineage as L

#: Exactly 10 % of R0's 37,654 dots.  Both 10 % arms move this many, so the pair differs only in
#: which dots move.
DELTA = 3765
SEED = 20261023
#: The parent packs at 2.8 px.  Adding mass at 2.8 px is impossible -- only 794 cells in the whole
#: field are free at that separation -- so the add arm relaxes to 2.2 px and says so (IR-V2-09).
ADD_SEP_PX = 2.2


def bridged_extent(field: np.ndarray, bridge: int = 1) -> np.ndarray:
    """Size of the connected structure each support cell belongs to, after bridging `bridge` px."""
    f = np.asarray(field, bool)
    g = f if bridge == 0 else ndi.binary_dilation(
        f, ndi.iterate_structure(ndi.generate_binary_structure(2, 1), bridge))
    lab, n = ndi.label(g, structure=np.ones((3, 3), int))
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    return sizes[lab]


def rank_by_extent(r0: np.ndarray, field: np.ndarray) -> np.ndarray:
    """Deterministic rank of every R0 dot, 0 = smallest structure (the first to be dropped)."""
    ext = bridged_extent(field).ravel()
    idx = np.flatnonzero(r0)
    # ascending extent, ties by raster index (stable) -- reproducible with no seed
    order = np.argsort(ext[idx], kind="stable")
    rank = np.empty(idx.size, np.int64)
    rank[order] = np.arange(idx.size)
    out = np.full(r0.size, -1, np.int64)
    out[idx] = rank
    return out.reshape(r0.shape)


def drop_by_rank(r0: np.ndarray, rank: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    flat = rank.ravel()
    idx = np.flatnonzero(flat >= 0)
    chosen = idx[np.argsort(flat[idx], kind="stable")[:n]]
    keep = r0.copy()
    keep.ravel()[chosen] = False
    return keep, chosen


def drop_uniform(r0: np.ndarray, n: int, seed: int = SEED) -> tuple[np.ndarray, np.ndarray]:
    idx = np.flatnonzero(r0)
    rng = np.random.default_rng(seed)
    chosen = np.sort(rng.choice(idx, size=n, replace=False))
    keep = r0.copy()
    keep.ravel()[chosen] = False
    return keep, chosen


def add_by_extent(r0: np.ndarray, field: np.ndarray, dist: np.ndarray, n: int, *,
                  sep_px: float = ADD_SEP_PX, min_cat_px: float = 2.0) -> tuple[np.ndarray, dict]:
    """Add `n` dots to the field, largest structure first, at a relaxed minimum separation."""
    from .emission import poisson_thin

    ext = bridged_extent(field).astype(np.float32)
    # Pixels already inside the parent's own minimum separation are not candidates at all; putting
    # them in `allowed` lets the greedy spend its budget there and then get discarded.
    h, w = r0.shape
    off = int(np.ceil(sep_px))
    yy, xx = np.mgrid[-off:off + 1, -off:off + 1]
    inside = (yy * yy + xx * xx) <= sep_px ** 2
    near_parent = np.zeros_like(r0)
    y0, x0 = np.nonzero(r0)
    for dy, dx in zip(yy[inside], xx[inside]):
        near_parent[np.clip(y0 + dy, 0, h - 1), np.clip(x0 + dx, 0, w - 1)] = True
    allowed = field & (dist > min_cat_px) & ~near_parent
    added = poisson_thin(ext, n=n, sep_px=sep_px, allowed=allowed)
    return r0 | added, dict(n_requested=n, n_added=int(added.sum()), sep_px=sep_px,
                            n_free_cells_at_add_sep=int(allowed.sum()),
                            n_free_cells_at_parent_sep=794)
