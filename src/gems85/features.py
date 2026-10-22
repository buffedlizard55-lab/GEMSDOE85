"""The single H85 method lane: scale-space persistence of detrended-slope edges."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from .grid import read_feature_band, read_template

METHOD_ID = "H85-scale-space-detrended-slope-persistence"
BAND = 19
SIGMAS = (0.5, 1.0, 2.0, 3.0)


def _robust_unit(values: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, dict]:
    finite = footprint & np.isfinite(values)
    p01, p99 = np.percentile(values[finite], [1.0, 99.0])
    scale = float(p99 - p01)
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("feature has no usable 1st-to-99th percentile spread")
    unit = np.clip((values - p01) / scale, 0.0, 1.0).astype(np.float32)
    return unit, {"p01": float(p01), "p99": float(p99)}


def build_scale_space(feature_path: Path, template_path: Path, sigmas: tuple[float, ...] = SIGMAS) -> dict:
    """Build a label-free, multi-scale edge surface from band 19.

    The band is the supplied ``det_elev_slope`` layer.  Gaussian gradient
    magnitude is calculated at four physical scales (50, 100, 200, 300 m at
    the 100 m grid), each is robustly clipped, and the cellwise maximum is the
    persistence envelope.  No label or catalogue pixels enter this transform.
    """
    template = read_template(Path(template_path))
    footprint = template["footprint"]
    raw, description = read_feature_band(Path(feature_path), BAND, footprint)
    raw_unit, raw_stats = _robust_unit(raw, footprint)
    scale_fields: dict[str, np.ndarray] = {}
    scale_stats: dict[str, dict] = {}
    for sigma in sigmas:
        edge = ndi.gaussian_gradient_magnitude(raw_unit, sigma=float(sigma), mode="nearest").astype(np.float32)
        edge_unit, stats = _robust_unit(edge, footprint)
        edge_unit[~footprint] = 0.0
        key = f"sigma_{sigma:g}_px"
        scale_fields[key] = edge_unit
        scale_stats[key] = stats
    surface = np.maximum.reduce(list(scale_fields.values())).astype(np.float32)
    surface[~footprint] = 0.0
    return {
        "surface": surface,
        "features": scale_fields,
        "footprint": footprint,
        "band": BAND,
        "description": description,
        "sigmas": [float(s) for s in sigmas],
        "raw_normalization": raw_stats,
        "scale_normalization": scale_stats,
        "method_id": METHOD_ID,
    }
