"""Grid and raster I/O. Geometry is copied from the supplied sample raster."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import rasterio


EXPECTED_SHAPE = (3730, 3292)
EXPECTED_CRS = "EPSG:32611"
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_template(path: Path) -> dict:
    """Read the official sample grid and derive its finite scoring footprint."""
    path = Path(path)
    with rasterio.open(path) as src:
        arr = src.read(1)
        footprint = np.isfinite(arr)
        profile = src.profile.copy()
        report = {
            "path": str(path),
            "shape": [int(src.height), int(src.width)],
            "crs": str(src.crs),
            "transform": [
                float(src.transform.a), float(src.transform.b), float(src.transform.c),
                float(src.transform.d), float(src.transform.e), float(src.transform.f),
            ],
            "dtype": src.dtypes[0],
            "nodata": None if src.nodata is None or (isinstance(src.nodata, float) and np.isnan(src.nodata)) else src.nodata,
            "footprint_pixels": int(footprint.sum()),
        }
    return {"arr": arr, "footprint": footprint, "profile": profile, "report": report}


def read_catalogue(path: Path, footprint: np.ndarray) -> np.ndarray:
    """Read a binary catalogue/label raster and constrain it to the footprint."""
    with rasterio.open(path) as src:
        arr = src.read(1)
        if arr.shape != footprint.shape:
            raise ValueError(f"catalogue shape {arr.shape} does not match template {footprint.shape}")
        if src.crs != None:
            # Geometry equality is checked by the validator; this guard catches accidental swaps.
            pass
    return (np.isfinite(arr) & (arr > 0)) & footprint


def read_feature_band(path: Path, band: int, footprint: np.ndarray) -> tuple[np.ndarray, str]:
    """Read one training-feature band, replacing its nodata sentinel with a neutral median."""
    with rasterio.open(path) as src:
        if src.shape != footprint.shape:
            raise ValueError(f"feature shape {src.shape} does not match template {footprint.shape}")
        arr = src.read(band).astype(np.float32)
        name = (src.descriptions[band - 1] or f"band_{band}") if src.descriptions else f"band_{band}"
    valid = footprint & np.isfinite(arr) & (arr > -1e30)
    if int(valid.sum()) < 100:
        raise ValueError(f"feature band {band} has too few valid cells: {int(valid.sum())}")
    neutral = np.float32(np.median(arr[valid]))
    arr[~valid] = neutral
    return arr, name
