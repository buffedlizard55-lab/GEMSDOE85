#!/usr/bin/env python3
"""Calibrate the block-density CV statistic used by the CONCENTRATION axis.

The agent brief reports that "the best files reportedly sit at 0.51-0.59" block-density CV,
without stating the block size or the population the CV is taken over.  This script finds
(block size, population) pairs that reproduce that band for the family's own best files and
separates them from the files that scored badly, so the axis can be built against a statistic
that is actually anchored to the family's record.

Read-only.  Usage:  python scripts/axis_concentration_stats.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "data" / "registry_rasters"
SCORED = ROOT / "data" / "scored"

FILES = {
    # label: (path, owner-reported live DTI, family)
    "h33-2-b2 (R0)": (REG / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", 0.2778, "best"),
    "h27-4-solo-d28": (REG / "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif", 0.2708, "best"),
    "d2.8 (44,090)": (REG / "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif", 0.2600, "best"),
    "d1.5 (60,069)": (SCORED / "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477, "best"),
    "h19-5 field": (SCORED / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif", 0.1922, "field"),
    "topo-gap-closure": (SCORED / "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449, "mid"),
    "Hedge-v2": (SCORED / "8GEMSDOE_Hedge-v2_submission.tif", 0.1563, "bad"),
    "r13 lattice s5": (SCORED / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", 0.0904, "bad"),
    "H25 ctx-ridge": (SCORED / "gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif", 0.1280, "bad"),
}


def read_mask(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return (a > 0) & np.isfinite(a)


def main() -> int:
    with rasterio.open(ROOT / "data" / "sample_submission.tif") as ds:
        sample = ds.read(1)
    footprint = np.isfinite(sample)
    h, w = footprint.shape

    out = {"footprint_px": int(footprint.sum()), "grid": [h, w], "block_sizes_km": [1, 2, 3, 5], "rows": {}}

    masks = {k: read_mask(p) for k, (p, _, _) in FILES.items()}

    for bs_km in (1, 2, 3, 5):
        b = int(bs_km * 1000 / 100)  # px per block side
        nb_y, nb_x = h // b, w // b
        # block id per pixel (pixels beyond a whole block are dropped from the last block)
        yy = np.minimum(np.arange(h) // b, nb_y - 1)
        xx = np.minimum(np.arange(w) // b, nb_x - 1)
        bid = (yy[:, None] * nb_x + xx[None, :])
        nb = nb_y * nb_x
        area_px = np.zeros(nb, dtype=np.int64)
        np.add.at(area_px, bid.ravel(), footprint.ravel().astype(np.int64))
        occupied = area_px > 0  # blocks that contain any footprint pixel

        for label, (path, score, family) in FILES.items():
            m = masks[label]
            cnt = np.zeros(nb, dtype=np.int64)
            np.add.at(cnt, bid.ravel(), m.ravel().astype(np.int64))
            occ = cnt > 0
            # population A: occupied blocks only (density = dots per occupied block)
            cv_occ = float(cnt[occ].std(ddof=0) / cnt[occ].mean()) if occ.any() else float("nan")
            # population B: all footprint blocks (empty blocks count as 0)
            dens = cnt[occupied] / area_px[occupied]
            cv_all = float(dens.std(ddof=0) / dens.mean()) if dens.size else float("nan")
            # population C: all footprint blocks, raw dot counts (not density)
            cv_raw = float(cnt[occupied].std(ddof=0) / cnt[occupied].mean()) if occupied.any() else float("nan")
            out["rows"].setdefault(label, {})[f"{bs_km}km"] = {
                "owner_reported_dti": score,
                "family": family,
                "dots": int(m.sum()),
                "cv_occupied_blocks": cv_occ,
                "cv_all_footprint_blocks_density": cv_all,
                "cv_all_footprint_blocks_counts": cv_raw,
                "n_occupied_blocks": int(occ.sum()),
                "n_footprint_blocks": int(occupied.sum()),
            }

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
