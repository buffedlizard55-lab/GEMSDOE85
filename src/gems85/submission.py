"""Write and *validate* a competition-legal GeoTIFF, with no human in the loop.

Format requirements, quoted from the official submission-format section
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/):

  - same projected CRS as the training data (UTM 11N, EPSG 32611)
  - same resolution as the training data (100 m)
  - same bounds as the training data; data outside the bounds is null or nan
  - a single layer, datatype float32, values between 0 and 1

Plus one requirement that is *not* on that page but IS enforced by the live upload form, and
which cost the operator a rejected upload:

      "Predicted values must be in range [0, 1]"

A NaN fails `0 <= v <= 1` under IEEE-754 comparison, so a raster whose outside-footprint area is
NaN can be rejected by that check even though the written format page permits nan.  This module
therefore defaults to the **all-finite** form: zeros outside the footprint, no nodata tag, every
value a real number in [0, 1].  The NaN-outside twin is still written, clearly marked as the
alternate, so both forms are on the shelf.

`validate()` is the gate.  `write_submission()` refuses to return a path whose validation
failed, so a file that reaches docs/downloads/ has already passed every check.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import rasterio

from . import grid


@dataclass
class ValidationReport:
    path: str
    sha256: str
    bytes: int
    mode: str
    passed: bool
    checks: dict
    stats: dict

    def as_dict(self) -> dict:
        return asdict(self)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_raster(arr: np.ndarray, path: Path | str, *, mode: str = "zeros") -> Path:
    """mode='zeros' -> all-finite (recommended); mode='nan' -> NaN outside the footprint."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fp = grid.footprint()
    a = np.asarray(arr, dtype=np.float32).copy()
    a[~np.isfinite(a)] = 0.0
    np.clip(a, 0.0, 1.0, out=a)
    a[~fp] = np.float32("nan") if mode == "nan" else np.float32(0.0)
    profile = {
        "driver": "GTiff", "height": grid.HEIGHT, "width": grid.WIDTH, "count": 1,
        "dtype": "float32", "crs": rasterio.crs.CRS.from_epsg(grid.EPSG),
        "transform": grid.TRANSFORM, "compress": "deflate", "predictor": 2,
        "zlevel": 9, "tiled": False, "nodata": None,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(a, 1)
    return path


def validate(path: Path | str, *, mode: str = "zeros",
             catalogue_buffer_px: int = 2) -> ValidationReport:
    """Every check the submission must pass.  No human inspection anywhere."""
    path = Path(path)
    fp = grid.footprint()
    cat = grid.catalogue()
    with rasterio.open(path) as src:
        checks = {
            "file_exists": True,
            "single_band": src.count == 1,
            "dtype_float32": src.dtypes[0] == "float32",
            "shape_3730x3292": (src.height, src.width) == (grid.HEIGHT, grid.WIDTH),
            "crs_epsg_32611": src.crs is not None and src.crs.to_epsg() == grid.EPSG,
            "transform_matches_template": tuple(src.transform)[:6] == tuple(grid.TRANSFORM)[:6],
            "resolution_100m": (abs(src.transform.a), abs(src.transform.e)) == (100.0, 100.0),
        }
        a = src.read(1)
        nodata_tag = src.nodata

    inside = a[fp]
    outside = a[~fp]
    finite_in = np.isfinite(inside)
    checks["no_nan_inside_footprint"] = bool(finite_in.all())
    checks["no_inf_inside_footprint"] = bool(np.isfinite(inside[finite_in]).all())
    checks["values_in_0_1_inside_footprint"] = bool(
        finite_in.all() and inside.min() >= 0.0 and inside.max() <= 1.0)
    if mode == "zeros":
        checks["all_finite_whole_raster"] = bool(np.isfinite(a).all())
        checks["values_in_0_1_whole_raster"] = bool(
            np.isfinite(a).all() and a.min() >= 0.0 and a.max() <= 1.0)
        checks["outside_footprint_is_zero"] = bool((outside == 0).all())
        checks["no_nodata_tag"] = nodata_tag is None
    else:
        checks["outside_footprint_is_nan"] = bool(np.isnan(outside).all())
    pos = np.isfinite(a) & (a > 0)
    checks["has_positive_predictions"] = bool(pos.any())
    checks["no_prediction_outside_footprint"] = bool(not (pos & ~fp).any())
    if catalogue_buffer_px is not None:
        from scipy import ndimage as ndi
        halo = ndi.binary_dilation(cat, np.ones((3, 3), bool), iterations=catalogue_buffer_px)
        checks[f"zero_mass_within_{catalogue_buffer_px}px_of_catalogue"] = bool(not (pos & halo).any())

    stats = {
        "emitting_pixels": int(pos.sum()),
        "prediction_mass": float(a[pos].sum()),
        "min_inside": float(np.nanmin(inside)), "max_inside": float(np.nanmax(inside)),
        "unique_values_inside": int(min(10, np.unique(inside[finite_in]).size)),
        "footprint_pixels": int(fp.sum()),
        "on_catalogue_pixels": int((pos & cat).sum()),
        "nodata_tag": None if nodata_tag is None else float(nodata_tag),
    }
    return ValidationReport(str(path), sha256_file(path), path.stat().st_size,
                            mode, all(checks.values()), checks, stats)


def write_submission(arr: np.ndarray, path: Path | str, *, mode: str = "zeros",
                     catalogue_buffer_px: int = 2) -> ValidationReport:
    p = write_raster(arr, path, mode=mode)
    rep = validate(p, mode=mode, catalogue_buffer_px=catalogue_buffer_px)
    if not rep.passed:
        failed = [k for k, v in rep.checks.items() if not v]
        raise RuntimeError(f"submission failed validation: {failed}")
    Path(str(p) + ".checks.json").write_text(json.dumps(rep.as_dict(), indent=2) + "\n")
    return rep
