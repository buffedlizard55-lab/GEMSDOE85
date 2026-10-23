#!/usr/bin/env python3
"""Duplicate check against the 17-raster fleet registry + historical submission helper.

Restores `duplicate_check()` (IR-85-020: previously clobbered by a 10-line stub while
still imported by `scripts/build_submission_session.py`). Reports BOTH raw 3-px forward
dot overlaps AND chance-coverage / comparable-budget metrics without hiding dense-prior
saturation (`IR-85-002`, `IR-85-07`).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi, stats

ROOT = Path(__file__).resolve().parents[1]


def duplicate_check(dots: np.ndarray, surface: np.ndarray, fp: np.ndarray,
                    *, comparable_max_dots: int = 65_000, seed: int = 20261022) -> dict:
    """Compare candidate `dots` (bool) and pre-placement `surface` against registry rasters."""
    reg_meta = json.loads((ROOT / "registry" / "scored_artifacts.json").read_text())
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(fp)
    sel = rng.choice(ys.size, min(250_000, ys.size), replace=False)
    sy, sx = ys[sel], xs[sel]
    s_vec = np.nan_to_num(surface[sy, sx].astype(np.float64), nan=0.0)

    yy, xx = np.mgrid[-3:4, -3:4]
    disc3 = (yy * yy + xx * xx) <= 9
    cand = dots.astype(bool) & fp
    n_cand = max(1, int(cand.sum()))

    comparisons = []
    for item in reg_meta["artifacts"]:
        p = ROOT / item["file"]
        if not p.exists():
            continue
        with rasterio.open(p) as ds:
            arr = ds.read(1).astype(np.float32)
        arr_clean = np.nan_to_num(arr, nan=0.0)
        rho = float(stats.spearmanr(s_vec, arr_clean[sy, sx].astype(np.float64)).statistic)
        if not np.isfinite(rho):
            rho = 0.0
        reg_pos = np.isfinite(arr) & (arr > 0) & fp
        n_reg = int(reg_pos.sum())
        halo = ndi.binary_dilation(reg_pos, structure=disc3)
        ov = float((cand & halo).sum() / n_cand)
        cov = float((halo & fp).sum() / fp.sum())
        lift = float(ov / cov) if cov > 0 else 0.0
        is_comparable = n_reg <= comparable_max_dots
        # Comparable sparse/dotted submissions enforce strict raw overlap > 0.70;
        # space-filling dense/lattice priors (>65k px) are flagged only if Spearman > 0.90
        # OR (comparable and ov > 0.70), while raw overlap is always disclosed verbatim.
        dup = bool(abs(rho) > 0.90 or (is_comparable and ov > 0.70))
        comparisons.append({
            "file": p.name,
            "owner_reported_live_dti": item["owner_reported_live_dti"],
            "registry_positive_pixels": n_reg,
            "comparable_sparse_budget": is_comparable,
            "spearman_surface": rho,
            "dot_overlap_3px": ov,
            "chance_coverage_3px": cov,
            "overlap_lift_over_chance": lift,
            "duplicate": dup,
        })

    max_rho = max((abs(c["spearman_surface"]) for c in comparisons), default=0.0)
    max_ov_raw = max((c["dot_overlap_3px"] for c in comparisons), default=0.0)
    max_ov_comp = max((c["dot_overlap_3px"] for c in comparisons if c["comparable_sparse_budget"]), default=0.0)
    max_lift = max((c["overlap_lift_over_chance"] for c in comparisons), default=0.0)

    return {
        "n_registry_rasters": len(comparisons),
        "max_abs_spearman": max_rho,
        "max_dot_overlap_3px": max_ov_raw,
        "max_comparable_dot_overlap_3px": max_ov_comp,
        "max_overlap_lift_over_chance": max_lift,
        "thresholds": {
            "spearman": 0.90,
            "comparable_dot_overlap_3px": 0.70,
            "comparable_max_dots": comparable_max_dots,
        },
        "irregularity": (
            "IR-85-002 / IR-85-07 -- space-filling priors (e.g. 206,895-dot r13-lattice-s5 and "
            "5.17M-px continuous rasters) cover 99-100% of the footprint within 3 px by construction. "
            "Both raw all-raster overlap and comparable-budget (<=65k) raw overlap are reported."
        ),
        "is_duplicate": any(c["duplicate"] for c in comparisons),
        "comparisons": comparisons,
    }


def main() -> int:
    print("Use scripts/build_gapvent_submission.py to build, duplicate-check, and 17-check validate the primary submission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
