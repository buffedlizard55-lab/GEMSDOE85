"""Canonical competition grid + raster IO.

Grid facts are read from the restored competition rasters at import time, never hard-coded
as beliefs: `assert_grid()` fails loudly if a raster does not match the template.

Verified source of the grid spec:
  https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/  ("Submission format")
    - EPSG:32611 (UTM 11N), 100 m resolution, same bounds as the training data,
      single band, float32, values in [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# The grid as published by the organisers and as present in every restored raster.
HEIGHT = 3730
WIDTH = 3292
EPSG = 32611
PIXEL_M = 100.0
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
R_METERS = 300.0
R_PIXELS = R_METERS / PIXEL_M  # 3.0
ALPHA = 0.2
BETA = 0.8

TRAINING_FEATURES = DATA / "training_features.tif"
LABELS = DATA / "labels.tif"
EXISTING_FAULTS = DATA / "existing_faults.tif"
SAMPLE_SUBMISSION = DATA / "sample_submission.tif"

# Band index (1-based) -> short name, read from the GeoTIFF band descriptions of
# training_features.tif (printed verbatim by scripts/inspect_data.py).
BANDS = {
    1: "mag_anom", 2: "rtp", 3: "tmi_hg", 4: "geod_2ndinv", 5: "iso_grav_anom_slope",
    6: "tc", 7: "geod_shearrate", 8: "geod_dilaterate", 9: "tmi_vg", 10: "deq_n100a15",
    11: "iso_grav_anom_vg", 12: "det_elev", 13: "iso_grav_anom", 14: "tmi",
    15: "depth_to_base_surf", 16: "ieq_n100a15", 17: "cond_surf",
    18: "iso_grav_anom_hg", 19: "det_elev_slope",
}
NAME_TO_BAND = {v: k for k, v in BANDS.items()}

# float32 sentinel used as nodata inside training_features.tif
SENTINEL = np.float32(-3.4028234663852886e38)


@dataclass(frozen=True)
class Grid:
    height: int = HEIGHT
    width: int = WIDTH
    epsg: int = EPSG
    transform: Affine = TRANSFORM

    @property
    def shape(self) -> tuple[int, int]:
        return (self.height, self.width)


GRID = Grid()


def assert_grid(src: rasterio.DatasetReader, what: str = "raster") -> None:
    """Raise unless `src` is on the exact competition grid."""
    if (src.height, src.width) != (HEIGHT, WIDTH):
        raise ValueError(f"{what}: shape {(src.height, src.width)} != {(HEIGHT, WIDTH)}")
    if src.crs is None or src.crs.to_epsg() != EPSG:
        raise ValueError(f"{what}: CRS {src.crs} != EPSG:{EPSG}")
    if tuple(src.transform)[:6] != tuple(TRANSFORM)[:6]:
        raise ValueError(f"{what}: transform {tuple(src.transform)[:6]} != {tuple(TRANSFORM)[:6]}")


def read_band(path: Path | str, band: int = 1, *, check: bool = True) -> np.ndarray:
    with rasterio.open(path) as src:
        if check:
            assert_grid(src, str(path))
        return src.read(band)


def read_feature(name_or_index: str | int) -> np.ndarray:
    """Read one band of training_features.tif as float32 with the sentinel replaced by NaN."""
    idx = NAME_TO_BAND[name_or_index] if isinstance(name_or_index, str) else int(name_or_index)
    arr = read_band(TRAINING_FEATURES, idx).astype(np.float32)
    arr[arr <= SENTINEL / 2] = np.nan      # sentinel is -3.4e38; nothing real is near it
    arr[~np.isfinite(arr)] = np.nan
    return arr


def footprint() -> np.ndarray:
    """Boolean mask of the scored survey footprint.

    Definition: pixels where sample_submission.tif is finite. The sample submission is the
    organiser-supplied template, so its finite support *is* the region a submission must cover.
    """
    arr = read_band(SAMPLE_SUBMISSION, 1).astype(np.float32)
    return np.isfinite(arr)


def catalogue() -> np.ndarray:
    """Boolean mask of the given (USGS Quaternary + INGENIOUS) fault catalogue pixels."""
    arr = read_band(LABELS, 1)
    return arr == 1
