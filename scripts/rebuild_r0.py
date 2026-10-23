#!/usr/bin/env python3
"""Verify every pin this session uses, rebuild the incumbent R0, and receipt the result.

Exit status is 1 if the rebuild is not pixel-identical to the pinned incumbent, because the
brief forbids proceeding on an approximate parent.  Byte identity is checked too and reported
separately: it is not achievable in this environment (IR-V2-01).

Usage:
    python scripts/rebuild_r0.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

import numpy as np  # noqa: E402

from gems85 import lineage as L  # noqa: E402


def main() -> int:
    pins = {}
    for key in ("r0", "prune1", "d28", "h19_5"):
        path = L.fetch_pinned(key)
        pins[key] = dict(path=str(path.relative_to(ROOT)), sha256=L.sha256_file(path),
                         bytes=path.stat().st_size, declares=L.PINNED[key]["pin"],
                         pin=L.PINNED[key]["sha256"],
                         ok=L.sha256_file(path) == L.PINNED[key]["sha256"])
    fp, cat = L.load_template()
    dist = L.catalogue_distance(cat)

    d28 = L.read_dots(L.PINNED["d28"]["dest"])
    p1 = L.read_dots(L.PINNED["prune1"]["dest"])
    inc = L.read_dots(L.PINNED["r0"]["dest"])

    ladder = {
        "d28_dots": int(d28.sum()),
        "prune1_dots": int(p1.sum()),
        "incumbent_dots": int(inc.sum()),
        "prune1_equals_d28_minus_cutoff1": bool(np.array_equal(L.prune(d28, dist, 1.0), p1)),
        "r0_equals_d28_minus_cutoff2": bool(np.array_equal(L.prune(d28, dist, 2.0), inc)),
        "r0_equals_prune1_minus_cutoff2": bool(np.array_equal(L.prune(p1, dist, 2.0), inc)),
        "cutoff3_dots": int(L.prune(d28, dist, 3.0).sum()),
        "min_distance_of_incumbent_dots_px": round(float(dist[inc].min()), 4),
        "incumbent_dots_within_3px": int((dist[inc] < 3.0).sum()),
    }

    # byte-level serialisation check: same pixels out, different bytes is expected (IR-V2-01)
    probe = ROOT / "work" / "rebuild" / "r0-reserialised-zeros.tif"
    probe.parent.mkdir(parents=True, exist_ok=True)
    L.write_zeros(probe, inc)
    sha = L.sha256_file(probe)
    byte_identity = sha == L.PINNED["r0"]["sha256"]

    report = dict(
        schema_version=1,
        generated_by="scripts/rebuild_r0.py",
        pins=pins,
        ladder=ladder,
        rebuild=dict(parent="d28 (44,090 dots)", rule="remove dots with Euclidean distance to catalogue <= 2.0 px",
                     n_dots=int(L.prune(d28, dist, 2.0).sum()),
                     pixel_identical_to_pinned_incumbent=ladder["r0_equals_d28_minus_cutoff2"],
                     n_differing_pixels=int((L.prune(d28, dist, 2.0) ^ inc).sum())),
        serialisation=dict(reserialised_sha256=sha, pinned_sha256=L.PINNED["r0"]["sha256"],
                           byte_identical=byte_identity,
                           note="Pixel-identical re-serialisation; bytes differ because the incumbent was written with DEFLATE predictor=3 by an unavailable compression stack (IR-V2-01). Never upload the re-serialisation: same pixels, new hash, no new information."),
        conclusion=("STOP: parent could not be rebuilt" if not ladder["r0_equals_d28_minus_cutoff2"]
                    else "PASS: incumbent rebuilt pixel-exactly from its pinned parent"),
    )
    out = ROOT / "evidence" / "r0_rebuild.json"
    L.write_json(out, report)
    print(json.dumps({k: report[k] for k in ("ladder", "rebuild", "conclusion")}, indent=2))
    print(f"receipt -> {out.relative_to(ROOT)}")
    return 0 if ladder["r0_equals_d28_minus_cutoff2"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
