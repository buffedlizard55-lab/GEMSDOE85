#!/usr/bin/env python3
"""Uniqueness gate (PARALLEL-RUN PROTOCOL §1) for a candidate raster.

Checks, against every registry raster in the given directories:
  * Spearman rank-correlation of the candidate's continuous surface with the
    registry raster (200k sampled footprint pixels) — drift if |rho| > 0.90;
  * dot overlap: fraction of candidate dots within 3 px of a registry raster's
    dots — drift if > 70% for any single registry raster.
Usage: check_uniqueness.py <data_dir> <cache_dir> <candidate_tif> <registry_dir> [...]
Writes evidence/uniqueness.json.  Exit code 1 if drift is detected.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage, stats

ROOT = Path(__file__).resolve().parents[1]


def read_arr(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


def main() -> None:
    data, cache, cand_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    registry_dirs = [Path(p) for p in sys.argv[4:]]
    with rasterio.open(data / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    surf = np.load(cache / "final_surface.npy")
    cand = read_arr(cand_path)
    cand_dots = (cand > 0.5) & foot
    rng = np.random.default_rng(85)
    ys, xs = np.nonzero(foot)
    sel = rng.choice(len(ys), size=min(200000, len(ys)), replace=False)
    sy, sx = ys[sel], xs[sel]
    surf_sample = surf[sy, sx].astype(np.float64)

    registry = []
    drift = False
    files = sorted({p for d in registry_dirs for p in d.glob("*.tif")})
    for p in files:
        try:
            a = read_arr(p)
        except Exception as e:  # unreadable registry raster: record, do not hide
            registry.append(dict(file=str(p), error=str(e)))
            continue
        if a.shape != cand.shape:
            registry.append(dict(file=str(p), error=f"shape {a.shape} != {cand.shape}"))
            continue
        reg_dots = np.isfinite(a) & (a > 0.5)
        rho = float(stats.spearmanr(surf_sample, np.nan_to_num(a[sy, sx], nan=0.0)).statistic)
        if cand_dots.any() and reg_dots.any():
            d = ndimage.distance_transform_edt(~reg_dots)
            overlap = float((d[cand_dots] <= 3.0).mean())
        else:
            overlap = 0.0
        row = dict(file=str(p), name=p.name, spearman_rho_surface_vs_raster=rho,
                   dot_overlap_within_3px=overlap, registry_dots=int(reg_dots.sum()),
                   candidate_dots=int(cand_dots.sum()),
                   drift=bool(abs(rho) > 0.90 or overlap > 0.70))
        drift = drift or row["drift"]
        registry.append(row)
        print(f"{p.name}: rho={rho:+.4f} overlap3px={overlap:.4f} drift={row['drift']}", flush=True)

    out = dict(candidate=str(cand_path), thresholds=dict(abs_spearman_max=0.90, dot_overlap_max=0.70),
               n_registry=len(registry), drift_detected=bool(drift), registry=registry)
    (ROOT / "evidence" / "uniqueness.json").write_text(json.dumps(out, indent=2))
    print("DRIFT" if drift else "UNIQUE-PASS")
    sys.exit(1 if drift else 0)


if __name__ == "__main__":
    main()
