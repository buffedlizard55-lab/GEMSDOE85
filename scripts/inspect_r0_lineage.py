#!/usr/bin/env python3
"""Inspect the R0 lineage (h19-5 -> d1.5 -> d2.8 -> h27-4-solo-d28 -> h33-2-b2).

Read-only diagnostics: pixel-set relationships, catalogue-distance conventions, and
the rank structure of the parent field.  No submission is produced here.

Usage:  python scripts/inspect_r0_lineage.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "data" / "registry_rasters"
SCORED = ROOT / "data" / "scored"


def read(path: Path):
    with rasterio.open(path) as ds:
        return ds.read(1), ds


def main() -> int:
    files = {
        "h19_5": REG / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
        "d15": SCORED / "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "d28": SCORED / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "poisson300": REG / "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
        "h27": REG / "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        "h33": REG / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    }
    out = {}
    arrs = {}
    for k, p in files.items():
        a, ds = read(p)
        arrs[k] = a
        pos = (a > 0) & np.isfinite(a)
        out[k] = {
            "path": str(p.relative_to(ROOT)),
            "n_positive": int(pos.sum()),
            "unique_positive_values": int(np.unique(a[pos]).size),
            "min_pos": float(np.nanmin(a[pos])) if pos.any() else None,
            "max_pos": float(np.nanmax(a[pos])) if pos.any() else None,
            "nan_count": int(np.isnan(a).sum()),
        }

    sets = {k: (v > 0) & np.isfinite(v) for k, v in arrs.items()}

    lab, _ = read(ROOT / "data" / "labels.tif")
    catalogue = lab == 1
    out["catalogue_px"] = int(catalogue.sum())

    # distance conventions from the catalogue, in pixels
    d_euc = ndimage.distance_transform_edt(~catalogue)
    d_cheb = ndimage.distance_transform_cdt(~catalogue, metric="chessboard")
    d_city = ndimage.distance_transform_cdt(~catalogue, metric="cityblock")

    # 1) is h33 exactly h27 minus dots within 2 px of the catalogue?
    for name, d in (("euclidean", d_euc), ("chessboard", d_cheb), ("cityblock", d_city)):
        for thr in (1.0, 1.5, 2.0, 2.8, 3.0):
            keep = sets["h27"] & ~(d <= thr)
            same = np.array_equal(keep, sets["h33"])
            if same:
                out["h33_rule"] = {"metric": name, "threshold_px": thr}
            out.setdefault("h27_minus_catalogue_probe", []).append(
                {"metric": name, "thr": thr, "n_kept": int(keep.sum()), "equals_h33": bool(same)}
            )

    # 2) set relations
    rel = {}
    for a in sets:
        for b in sets:
            if a < b:
                inter = int((sets[a] & sets[b]).sum())
                rel[f"{a}&{b}"] = inter
    out["intersections"] = rel
    for a in sets:
        out.setdefault("subset_checks", {})[a] = {
            b: bool(np.all(sets[a] <= sets[b])) for b in sets if a != b
        }

    # 3) rank structure: is the h19-5 field the ranking key?
    f = arrs["h19_5"]
    finite = np.isfinite(f)
    vals = f[finite]
    out["h19_5_field"] = {
        "n_finite": int(finite.sum()),
        "n_positive": int((f > 0).sum()),
        "min": float(vals.min()), "max": float(vals.max()),
        "n_unique_positive": int(np.unique(f[f > 0]).size),
    }
    for k in ("d15", "d28", "poisson300", "h27", "h33"):
        v = f[sets[k] & finite]
        out.setdefault("field_value_stats", {})[k] = {
            "min": float(v.min()), "max": float(v.max()),
            "mean": float(v.mean()),
        }
    # is d15 / d28 a threshold cut of the field?
    for k, target_n in (("d15", None), ("d28", None), ("h27", None)):
        v = np.sort(f[finite])[::-1]
        n = int(sets[k].sum())
        out.setdefault("field_threshold_probe", {})[k] = {
            "n": n,
            "field_value_at_rank_cut": float(v[n - 1]),
            "field_value_at_rank_cut_plus1": float(v[n]),
            "min_field_in_set": float(f[sets[k]].min()),
        }
    # do d15/d28 equal a strict field threshold?
    for k in ("d15", "d28", "poisson300", "h27", "h33"):
        thr = float(f[sets[k]].min())
        above = finite & (f >= thr)
        out.setdefault("field_threshold_exact", {})[k] = {
            "thr": thr,
            "n_above": int(above.sum()),
            "n_set": int(sets[k].sum()),
            "set_equals_above": bool(np.array_equal(above, sets[k])),
        }

    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
