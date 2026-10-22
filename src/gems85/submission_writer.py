"""Submission writer + independent validator for GEMSDOE85.

Primary artifact policy (fixes the user-reported portal error
``Predicted values must be in range [0, 1]``):
  * single-band float32 GeoTIFF, EPSG:32611, exact sample-submission grid;
  * ALL-FINITE "zeros" encoding: every one of the 3730x3292 cells is finite and
    in [0, 1]; ``nodata=None`` (no NaN tag, no -3.4e38 sentinel anywhere);
  * binary {0.0, 1.0} values only;
  * zero positive pixels on the catalogue and zero within 2 px of it (checked
    by the writer; the validator re-checks from the written bytes).
A NaN-outside twin (competition-sample encoding) is written for inspection
only and is never the promoted download.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

EXPECTED_W, EXPECTED_H = 3292, 3730
EXPECTED_FOOTPRINT_PX = 5167373  # finite pixels of sample_submission.tif (measured)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_template(sample_path: Path):
    with rasterio.open(sample_path) as s:
        profile = s.profile.copy()
        foot = np.isfinite(s.read(1))
        transform = tuple(s.transform)[:6]
        crs = str(s.crs)
    return profile, foot, transform, crs


def write_pair(mask: np.ndarray, labels: np.ndarray, sample_path: Path,
               out_dir: Path, filename_zeros: str) -> dict:
    """Write zeros (primary) + nan (twin) GeoTIFFs; return audit dicts for both."""
    profile, foot, _, _ = load_template(sample_path)
    clean = (np.asarray(mask, bool) & foot & ~labels).astype(np.float32)
    out_dir.mkdir(parents=True, exist_ok=True)

    base = profile.copy()
    base.update(driver="GTiff", dtype="float32", count=1, compress="deflate",
                predictor=3, zlevel=9, tiled=True, blockxsize=256, blockysize=256)

    zeros_path = out_dir / filename_zeros
    prof = base.copy(); prof.update(nodata=None)
    arr = np.where(foot, clean, np.float32(0.0)).astype(np.float32)
    with rasterio.open(zeros_path, "w", **prof) as dst:
        dst.write(arr, 1)

    nan_name = filename_zeros.replace("-zeros.tif", "-nan.tif")
    nan_path = out_dir / nan_name
    prof = base.copy(); prof.update(nodata=np.nan)
    arr_nan = np.where(foot, clean, np.float32(np.nan)).astype(np.float32)
    with rasterio.open(nan_path, "w", **prof) as dst:
        dst.write(arr_nan, 1)

    return dict(zeros=validate(zeros_path, sample_path, labels),
                nan=validate(nan_path, sample_path, labels))


def validate(tif_path: Path, sample_path: Path, labels: np.ndarray | None = None,
             mode: str = "auto") -> dict:
    """Independent re-read validation of a written submission (no human inspection).

    ``mode='zeros'`` requires the all-finite, nodata=None encoding (the primary);
    ``mode='nan'`` requires NaN outside the footprint (the inspection twin).
    ``mode='auto'`` infers from the filename suffix.
    """
    if mode == "auto":
        mode = "nan" if str(tif_path).endswith("-nan.tif") else "zeros"
    _, foot, exp_transform, exp_crs = load_template(sample_path)
    with rasterio.open(tif_path) as s:
        a = s.read(1)
        count, dtypes = s.count, s.dtypes
        H, W = s.height, s.width
        crs_str, transform = str(s.crs), tuple(s.transform)[:6]
        nodata = s.nodata
    finite_all = bool(np.isfinite(a).all())
    in_foot = a[foot]
    dist_cat = None
    on_cat = within2 = None
    if labels is not None:
        lab = labels & foot
        on_cat = int(((a > 0.5) & lab).sum())
        d = ndimage.distance_transform_edt(~lab)
        within2 = int(((a > 0.5) & (d <= 2.0)).sum())
        dist_cat = float(d[a > 0.5].min()) if (a > 0.5).any() else None
    checks = {
        "single_band": count == 1,
        "dtype_float32": dtypes[0] == "float32",
        "shape_3730x3292": (H == EXPECTED_H and W == EXPECTED_W),
        "crs_matches_sample_epsg32611": crs_str == exp_crs and "32611" in crs_str,
        "transform_matches_sample": transform == exp_transform,
        "footprint_px_matches_sample": int(foot.sum()) == EXPECTED_FOOTPRINT_PX,
        "no_nan_inside_footprint": bool(np.isfinite(in_foot).all()),
        "values_in_0_1_inside_footprint": bool(((in_foot >= 0) & (in_foot <= 1)).all()),
        "binary_values_only": bool(set(np.unique(in_foot).tolist()) <= {0.0, 1.0}),
    }
    if mode == "zeros":
        checks.update({
            "nodata_is_none": nodata is None,
            "all_finite_whole_grid": finite_all,
            "whole_grid_in_0_1": bool(((a >= 0) & (a <= 1)).all()) if finite_all else False,
        })
    else:  # nan twin: outside footprint must be exactly NaN, nodata tag NaN
        checks.update({
            "nodata_is_nan": bool(isinstance(nodata, float) and np.isnan(nodata)),
            "outside_footprint_all_nan": bool(np.isnan(a[~foot]).all()),
        })
    if labels is not None:
        checks["zero_on_catalogue"] = on_cat == 0
        checks["zero_within_2px_of_catalogue"] = within2 == 0
    receipt = dict(mode=mode, file=str(tif_path), filename=Path(tif_path).name,
                   bytes=Path(tif_path).stat().st_size, sha256=sha256_file(Path(tif_path)),
                   crs=crs_str, transform=list(transform), shape=[H, W],
                   dtype=dtypes[0], nodata=(None if nodata is None else str(nodata)),
                   positive_px=int((a > 0.5).sum()),
                   min=float(np.nanmin(a)), max=float(np.nanmax(a)),
                   on_catalogue_px=on_cat, within_2px_catalogue_px=within2,
                   min_dist_to_catalogue_px=dist_cat,
                   checks=checks, all_checks_passed=bool(all(checks.values())))
    return receipt
