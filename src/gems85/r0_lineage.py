"""Rebuild parent R0 exactly, rank its dots without truth labels, and emit one-axis variants.

Parent R0 = `h33-h33-2-b2` (GEMSDOE32 `e5eb6e7e`, owner-reported live DTI 0.2778 = CLAIM).
This module contains **no path to a submission**: it only writes candidate GeoTIFFs and receipts.

Everything here is a deterministic function of four SHA-256-pinned inputs
(`registry/data_manifest.json` + `registry/scored_artifacts.json`):

    H19-5 ridge skeleton   data/scored/gems19-h19-5-...-e27054cf-nan.tif   ec1f9b56...
    labels / catalogue     data/labels.tif                                 7ba308cc...
    sample_submission.tif  data/sample_submission.tif                      2176d08e...
    parent rasters (checks) data/registry_rasters/... or docs/downloads     07b6db44... / c55bafc4...

Ranking used by the MASS axis
-----------------------------
`unique_credit` U_i is the exact amount of *max-dilated kernel credit* that dot i supplies and no
other kept dot supplies:

    C(x)     = max_j  k(x - d_j),          k(d) = (1 - d/3)_+
    C_-i(x)  = max_{j != i} k(x - d_j)
    U_i      = sum_x [ k(x - d_i) - C_-i(x) ]_+

DTI's true-positive term reads exactly C(x) at truth pixels, so U_i is a *label-free* estimate of
what a dot contributes to TP_w, while every dot costs 0.2 of its unit mass in FP_w wherever it is
not within 3 px of truth.  Dots with U_i ~ 0 are pure FP candidates.  This is the parent's own
geometry, no geophysics, no truth, no seed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

from .thinning85 import dot_thin

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# --- pins --------------------------------------------------------------------------------
PINS = {
    "h19_5": "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
    "d28": "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8",
    "solo_d28": "07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40",
    "r0_zeros": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "r0_nan": "baeae3219bba6a19bc8cfe79224e28555c50184b7c1ca65c2a822f54807c77dd",
    "labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}
PATHS = {
    "h19_5": DATA / "scored" / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
    "d28": DATA / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "solo_d28": DATA / "registry_rasters" / "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
    "r0_nan": DATA / "registry_rasters" / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif",
    "r0_zeros": DATA / "registry_rasters" / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "labels": DATA / "labels.tif",
    "sample_submission": DATA / "sample_submission.tif",
}
MIN_DIST = 2.8          # px, the recorded packing rung of the d2.8 lineage
CAT_PRUNE_PX = 2.0      # px, R0 = dots strictly farther than 2 px from the catalogue


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pins(keys=None) -> dict:
    """Verify SHA-256 of every pinned input this module reads. Raises on mismatch."""
    out = {}
    for k in (keys or PINS):
        p = PATHS[k]
        if not p.is_file():
            raise FileNotFoundError(f"{k}: pinned input missing at {p.relative_to(ROOT)}")
        got = sha256_file(p)
        if got != PINS[k]:
            raise ValueError(f"{k}: sha256 {got} != pinned {PINS[k]}")
        out[k] = dict(path=str(p.relative_to(ROOT)), sha256=got, bytes=p.stat().st_size)
    return out


def _read_mask(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.nan_to_num(a, nan=0.0) > 0.5


def load_catalogue() -> np.ndarray:
    with rasterio.open(PATHS["labels"]) as ds:
        return ds.read(1) == 1


def catalogue_distance() -> np.ndarray:
    """Euclidean distance in pixels from every cell to the nearest catalogue pixel."""
    return ndimage.distance_transform_edt(~load_catalogue())


def footprint() -> np.ndarray:
    with rasterio.open(PATHS["sample_submission"]) as ds:
        return np.isfinite(ds.read(1))


@dataclass(frozen=True)
class Lineage:
    skeleton: np.ndarray
    d28: np.ndarray
    solo: np.ndarray
    r0: np.ndarray
    dist_cat: np.ndarray
    pack_rank: np.ndarray

    def counts(self) -> dict:
        return dict(skeleton=int(self.skeleton.sum()), d28=int(self.d28.sum()),
                    solo=int(self.solo.sum()), r0=int(self.r0.sum()))


def rebuild(verify_against_pinned_files: bool = True) -> Lineage:
    """Rebuild R0 from the pinned skeleton, asserting every intermediate against its pin."""
    skeleton = _read_mask(PATHS["h19_5"])
    d28, pack_rank = dot_thin(skeleton, MIN_DIST, order=True)
    dist = catalogue_distance()
    solo = d28 & (dist > 1.0)
    r0 = solo & (dist > CAT_PRUNE_PX)

    if verify_against_pinned_files:
        for key, arr in (("d28", d28), ("solo_d28", solo), ("r0_nan", r0)):
            ref = _read_mask(PATHS[key])
            if not np.array_equal(arr, ref):
                raise AssertionError(f"rebuilt {key} is not pixel-identical to its pinned raster")
    return Lineage(skeleton=skeleton, d28=d28, solo=solo, r0=r0, dist_cat=dist, pack_rank=pack_rank)


# --- label-free per-dot ranking ----------------------------------------------------------
KERNEL = [(dy, dx, max(0.0, 1.0 - float(np.hypot(dy, dx)) / 3.0)) for dy in range(-3, 4)
          for dx in range(-3, 4) if np.hypot(dy, dx) <= 3.0]


def unique_credit(dots: np.ndarray) -> np.ndarray:
    """U_i for every dot, in the order of `np.nonzero(dots)` (row-major)."""
    dots = np.asarray(dots, bool)
    ys, xs = np.nonzero(dots)
    H, W = dots.shape
    ys_i = ys.astype(np.int64)
    xs_i = xs.astype(np.int64)
    own_id = np.full((H, W), -1, np.int32)
    own_id[ys_i, xs_i] = np.arange(ys_i.size, dtype=np.int32)

    # credit contributed to each cell by each kernel offset, with the owner dot id
    b1 = np.zeros((H, W), np.float32)
    o1 = np.full((H, W), -1, np.int32)
    b2 = np.zeros((H, W), np.float32)
    for dy, dx, k in KERNEL:
        if k <= 0.0:
            continue
        src_y = slice(max(0, -dy), H - max(0, dy))
        dst_y = slice(max(0, dy), H - max(0, -dy))
        src_x = slice(max(0, -dx), W - max(0, dx))
        dst_x = slice(max(0, dx), W - max(0, -dx))
        cand_id = own_id[src_y, src_x]
        cand_v = np.where(cand_id >= 0, np.float32(k), np.float32(0.0))
        cur_b1, cur_o1, cur_b2 = b1[dst_y, dst_x], o1[dst_y, dst_x], b2[dst_y, dst_x]
        take = cand_v > cur_b1
        new_o1 = np.where(take, cand_id, cur_o1)
        new_b2 = np.where(take, cur_b1, np.maximum(cur_b2, cand_v))
        b1[dst_y, dst_x] = np.where(take, cand_v, cur_b1)
        b2[dst_y, dst_x] = new_b2
        o1[dst_y, dst_x] = new_o1

    U = np.zeros(ys_i.size, np.float64)
    for dy, dx, k in KERNEL:
        if k <= 0.0:
            continue
        py, px = ys_i + dy, xs_i + dx
        ok = (py >= 0) & (py < H) & (px >= 0) & (px < W)
        pyc, pxc = py[ok], px[ok]
        idx = np.flatnonzero(ok)
        comp = np.where(o1[pyc, pxc] == idx, b2[pyc, pxc], b1[pyc, pxc])
        U[idx] += np.maximum(0.0, k - comp.astype(np.float64))
    return U


def select_lowest(U: np.ndarray, dots: np.ndarray, fraction: float) -> np.ndarray:
    """Return the kept mask after dropping the `fraction` of dots with the smallest U.

    Deterministic tie-break: row-major position (so the result never depends on sort stability).
    """
    if not 0.0 <= fraction < 1.0:
        raise ValueError("fraction must be in [0, 1)")
    ys, xs = np.nonzero(np.asarray(dots, bool))
    n_drop = int(round(fraction * ys.size))
    order = np.lexsort((xs, ys, U))       # primary U, then y, then x
    drop = np.zeros(ys.size, bool)
    drop[order[:n_drop]] = True
    kept = np.zeros_like(np.asarray(dots, bool))
    kept[ys[~drop], xs[~drop]] = True
    return kept
