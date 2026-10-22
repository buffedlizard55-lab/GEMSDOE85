"""Catalogue-free channel stack, cached one channel per .npy so RAM never holds all of it.

Every channel here is a function of the geophysics only.  None of them sees the fault
catalogue, which is what makes the leakage canary meaningful: a channel that cannot see the
answer cannot leak it.  The novel channels are `geopb_*` (see geopb.py); the rest are the
standard derivative descriptors, present so that the supervised comparison is honest about how
much GEO-Pb adds on top of what the family already had.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from . import baselines, geopb, grid

CACHE = grid.ROOT / "data" / "cache"


def _ext(fname: str, band: int, fp: np.ndarray) -> np.ndarray:
    with rasterio.open(grid.DATA / "external" / fname) as ds:
        grid.assert_grid(ds, fname)
        a = ds.read(band).astype(np.float32)
    a[a == 0] = np.nan
    med = float(np.nanmedian(a[fp])) if np.isfinite(a[fp]).any() else 0.0
    return np.nan_to_num(a, nan=med)


def _feat(name: str, fp: np.ndarray) -> np.ndarray:
    a = grid.read_feature(name)
    med = float(np.nanmedian(a[fp]))
    return np.nan_to_num(a, nan=med).astype(np.float32)


def _grad(a: np.ndarray, sigma: float) -> np.ndarray:
    gy = ndi.gaussian_filter(a, sigma, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(a, sigma, order=(0, 1), mode="nearest")
    return np.hypot(gy, gx).astype(np.float32)


def _local_range(a: np.ndarray, size: int) -> np.ndarray:
    return (ndi.maximum_filter(a, size) - ndi.minimum_filter(a, size)).astype(np.float32)


def channel_builders(fp: np.ndarray) -> dict:
    """name -> zero-arg callable returning a float32 full-grid array."""
    def pf(name, sigma=None):
        return lambda: (_feat(name, fp) if sigma is None else _grad(_feat(name, fp), sigma))

    return {
        # --- the novel lane -------------------------------------------------
        "geopb_r3_L15": lambda: geopb.geopb_surface(sigma=1.5, normals=tuple(geopb.NORMALS_R3),
                                                    persistence_px=15.0, footprint=fp),
        "geopb_r6_L25": lambda: geopb.geopb_surface(sigma=2.5, normals=tuple(geopb.NORMALS_R6),
                                                    persistence_px=25.0, footprint=fp),
        "geopb_crest": lambda: _crest(fp),
        # --- derivative descriptors the family already had -------------------
        "sato_det_elev": lambda: baselines.sato_ridge("det_elev", footprint=fp),
        "grad_rtp_s2": pf("rtp", 2.0),
        "grad_rtp_s5": pf("rtp", 5.0),
        "grad_grav_s2": pf("iso_grav_anom", 2.0),
        "grad_cond_s2": pf("cond_surf", 2.0),
        "grad_depth_s2": pf("depth_to_base_surf", 2.0),
        "tilt_tc": pf("tc"),
        "tmi_hg": pf("tmi_hg"),
        "tmi_vg": pf("tmi_vg"),
        "det_elev_slope": pf("det_elev_slope"),
        "relief5": lambda: _local_range(_feat("det_elev", fp), 5),
        "depth_to_base": pf("depth_to_base_surf"),
        "cond_surf": pf("cond_surf"),
        # --- external, hash-pinned -------------------------------------------
        "lidar_ex_max": lambda: _ext("lidar_scarp_features_u8.tif", 1, fp),
        "lidar_step_max": lambda: _ext("lidar_scarp_features_u8.tif", 3, fp),
        "lidar_downface": lambda: _ext("lidar_scarp_features_u8.tif", 6, fp),
        "lidar_coh100": lambda: _ext("lidar_scarp_features_u8.tif", 10, fp),
        "rad_K": lambda: _ext("geodawn_rad_u8.tif", 1, fp),
        "rad_Th": lambda: _ext("geodawn_rad_u8.tif", 2, fp),
        "rad_TC": lambda: _ext("geodawn_rad_u8.tif", 4, fp),
        "rad_ThK": lambda: _ext("geodawn_extensions_u8.tif", 1, fp),
    }


def _crest(fp):
    base, axis = geopb.geopb_surface(sigma=1.5, normals=tuple(geopb.NORMALS_R3),
                                     persistence_px=15.0, footprint=fp, return_parts=True)
    return geopb.crest(base, axis, tuple(geopb.NORMALS_R3))


def build(fp: np.ndarray, names: list[str] | None = None) -> list[str]:
    """Compute and cache every channel; returns the ordered channel list."""
    CACHE.mkdir(parents=True, exist_ok=True)
    builders = channel_builders(fp)
    names = names or list(builders)
    for n in names:
        p = CACHE / f"ch_{n}.npy"
        if p.exists():
            continue
        a = np.asarray(builders[n](), dtype=np.float32)
        a[~fp] = 0.0
        np.save(p, a)
        del a
    return names


def open_stack(names: list[str]):
    """Memory-mapped channel handles -- RAM holds only the slices actually read."""
    return [np.load(CACHE / f"ch_{n}.npy", mmap_mode="r") for n in names]


def gather(handles, flat_idx: np.ndarray, width: int) -> np.ndarray:
    """X[(n_pixels, n_channels)] for arbitrary flat pixel indices, read chunk-wise."""
    ys, xs = np.divmod(flat_idx, width)
    X = np.empty((flat_idx.size, len(handles)), dtype=np.float32)
    for c, h in enumerate(handles):
        X[:, c] = h[ys, xs]
    return X
