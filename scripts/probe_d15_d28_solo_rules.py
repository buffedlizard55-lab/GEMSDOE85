#!/usr/bin/env python3
"""Probe how the d1.5 / d2.8 cuts and the h27 'solo' step are defined.

Read-only.  Prints candidate rule matches for:
  d15 = h19_5 minus (catalogue within 1.5 px)?
  d28 = h19_5 minus (catalogue within 2.8 px)?
  h27 = isolated pixels of d28 (no 4- or 8-neighbour)?
"""
from __future__ import annotations

import numpy as np
import rasterio
from scipy import ndimage

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "data" / "registry_rasters"
SCORED = ROOT / "data" / "scored"


def read(p):
    with rasterio.open(p) as ds:
        return ds.read(1)


h19 = (read(REG / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") > 0)
d15 = (read(SCORED / "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif") > 0)
d28 = (read(SCORED / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") > 0)
pois = (read(REG / "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif") > 0)
h27 = (read(REG / "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif") > 0)
h33 = (read(REG / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif") > 0)
lab = read(ROOT / "data" / "labels.tif")
cat = lab == 1

print("d28 == poisson300 set:", np.array_equal(d28, pois))
print("counts h19,d15,d28,h27,h33:", h19.sum(), d15.sum(), d28.sum(), h27.sum(), h33.sum())

dist = {
    "euclid": ndimage.distance_transform_edt(~cat),
    "city": ndimage.distance_transform_cdt(~cat, metric="cityblock"),
    "chess": ndimage.distance_transform_cdt(~cat, metric="chessboard"),
}

for name, d in dist.items():
    for thr in (1.5, 2.8):
        cand = h19 & (d > thr)
        for tgt, tname in ((d15, "d15"), (d28, "d28")):
            if np.array_equal(cand, tgt):
                print(f"MATCH {name} thr={thr} -> {tname} (n={cand.sum()})")

# also: threshold applied to the whole raster (not restricted to h19)
for name, d in dist.items():
    for thr in (1.5, 2.8):
        cand = d > thr
        for tgt, tname in ((d15, "d15"), (d28, "d28")):
            if np.array_equal(cand, tgt):
                print(f"MATCH-ALL {name} thr={thr} -> {tname} (n={cand.sum()})")

# h27 'solo' rule applied to d28
for src, sname in ((d28, "d28"), (d15, "d15"), (h19, "h19")):
    for conn_name, st in (("4", np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])),
                          ("8", np.ones((3, 3)))):
        for mode in ("min", "max"):
            nb = ndimage.convolve(src.astype(np.uint8), st, mode="constant", cval=0)
            cand = src & ((nb == 1) if mode == "min" else (nb <= 1))
            if np.array_equal(cand, h27):
                print(f"MATCH-SOLO src={sname} conn={conn_name} rule={mode} n={cand.sum()}")
            elif (cand & h27).sum() / max(1, h27.sum()) > 0.9:
                print(f"  near-solo src={sname} conn={conn_name} rule={mode} "
                      f"n={cand.sum()} overlap={(cand & h27).sum()}/{h27.sum()}")

# how many dots does h27 drop from d28, and where do they sit?
drop = d28 & ~h27
print("d28->h27 dropped:", drop.sum())
print("  dropped within 2px(city) of catalogue:", int((drop & (dist['city'] <= 2)).sum()))
print("  dropped within 2px(euclid) of catalogue:", int((drop & (dist['euclid'] <= 2)).sum()))
# h27 vs d28: does h27 = d28 minus anything distance related?
for name, d in dist.items():
    for thr in (1.0, 1.5, 2.0, 2.5, 2.8, 3.0):
        cand = d28 & (d > thr)
        if np.array_equal(cand, h27):
            print(f"MATCH h27 = d28 minus d_cat<={thr} ({name})")

# neighbours: is every h27 dot isolated inside d28?
nb8 = ndimage.convolve(d28.astype(np.uint8), np.ones((3, 3)), mode="constant", cval=0)
print("h27 dots with a d28 8-neighbour:", int((h27 & (nb8 > 1)).sum()))
nb4 = ndimage.convolve(d28.astype(np.uint8), np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]), mode="constant", cval=0)
print("h27 dots with a d28 4-neighbour:", int((h27 & (nb4 > 1)).sum()))
