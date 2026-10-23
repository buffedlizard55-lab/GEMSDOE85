#!/usr/bin/env python3
"""EXPERIMENT 2 (of 3): GEO-Pb orientation resolution -- 16 strikes, persistence retired.

Hypothesis (declared before measuring):
  GEO-Pb's step statistic is sampled at 8 candidate strikes (normal azimuth spacing ~22.5 deg).
  A fault whose strike falls between two sampled normals is observed off-angle: the two
  half-windows straddle the boundary only partially, so the offset difference is attenuated.
  Doubling to 16 strikes (~11 deg spacing) reduces that attenuation and raises the crest
  field's credit per emitted dot.  The persistence term (1.5 km line mean) is retired --
  evidence/experiments.json measured L = 1/15/25 px statistically indistinguishable
  (0.0683 / 0.0666 / 0.0679) -- so the parameter budget is spent on orientation, not straightness.

Why it targets catalogue-missing faults: unchanged from H85-1 -- juxtaposition of basement
susceptibility, cover thickness and surface geochemistry across concealed faults; the
statistic never differentiates, so it works where no single band has a large gradient.

Named non-fault mimics: unchanged -- alluvial-fan margins / Lahontan shorelines (lobate,
killed by straightness-only structure; here straightness comes purely from the orientation
consensus across 16 strikes), acquisition seams (single-domain, killed by the two-of-three
median vote), volcanic mesa/flow margins (the irreducible confounder).

Differs from Exp 1 and from the shipped lane: same detector, 16 strikes instead of 8 and no
persistence multiplier.  No new data.

Instrument: holdout.make_folds + score_folds (pooled DTI, alpha 0.2, beta 0.8, 300 m kernel,
4 spatially-blocked folds, 60,988 withheld positives).  HOLDOUT-DTI only.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import emission, geopb, grid, holdout  # noqa: E402

CACHE = ROOT / "data" / "cache"
OUT = ROOT / "evidence"


def crest_surface(normals, persistence_px: float, fp: np.ndarray) -> np.ndarray:
    base, axis = geopb.geopb_surface(sigma=1.5, normals=tuple(normals),
                                     persistence_px=persistence_px, footprint=fp,
                                     return_parts=True)
    out = geopb.crest(base, axis, tuple(normals)).astype(np.float32)
    del base, axis
    return out


def run(field_name: str, field: np.ndarray, folds, n: int, sep_px: float,
        exclude_px: int) -> dict:
    fp = grid.footprint()

    def surf(fold, f=field, n=n):
        return emission.emit(f, footprint=fp, visible_catalogue=fold.visible,
                             n=n, sep_px=sep_px, exclude_px=exclude_px)

    r = holdout.score_folds(surf, folds, domain=fp)
    return {"pooled_dti": r.pooled_dti, "ci95": list(r.ci95),
            "n_withheld_positives": r.n_withheld_positives,
            "per_fold": [f.dti for f in r.folds],
            "tp_w": r.tp_w, "fp_w": r.fp_w, "fn_w": r.fn_w}


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    n_withheld = sum(f.n_withheld for f in folds)
    print(f"withheld positives: {n_withheld} across {[f.n_withheld for f in folds]}")

    CACHE.mkdir(parents=True, exist_ok=True)
    crest8_path = CACHE / "ch_geopb_crest.npy"
    if not crest8_path.exists():
        crest8 = crest_surface(geopb.NORMALS_R3, 15.0, fp)
        np.save(crest8_path, crest8)
    crest8 = np.load(crest8_path)

    crest16_path = CACHE / "ch_geopb_crest_16.npy"
    if not crest16_path.exists():
        print("computing GEO-Pb crest 16-strike surface ...")
        crest16 = crest_surface(geopb.NORMALS_R16, 1.0, fp)  # persistence retired (L=1)
        np.save(crest16_path, crest16)
    crest16 = np.load(crest16_path)

    print(f"crest8  max {crest8[fp].max():.4f}")
    print(f"crest16 max {crest16[fp].max():.4f}")

    results = {"crest8": {}, "crest16": {}}
    for name, field in (("crest8", crest8), ("crest16", crest16)):
        for n in (37_654, 60_000, 90_000):
            res = run(name, field, folds, n, sep_px=4.0, exclude_px=2)
            results[name][str(n)] = res
            dti = res["pooled_dti"]; lo = res["ci95"][0]; hi = res["ci95"][1]
            ns = f"{n:,}"; dts = f"{dti:.5f}"; cls_ = f"{lo:.5f}"; chs = f"{hi:.5f}"
            print("  " + name + " n=" + ns + "  pooled DTI = " + dts +
                  " CI [" + cls_ + "," + chs + "]")

    print("\n  delta (crest16 - crest8):")
    for n in (37_654, 60_000, 90_000):
        d8 = results["crest8"][str(n)]["pooled_dti"]
        d16 = results["crest16"][str(n)]["pooled_dti"]
        ns = f"{n:,}"
        print("    n=" + ns + ": " + f"{d16 - d8:+.5f}")

    summary = {
        "experiment": 2, "hypothesis_id": "H85-2 GEO-Pb 16 strikes, persistence retired",
        "hypothesis": "double GEO-Pb strike resolution 8 -> 16 (normal azimuth spacing ~22.5 -> "
                      "~11 deg) and retire the 1.5 km persistence term (null result), to raise "
                      "credit per emitted dot on strikes sampled off-angle.",
        "mechanism": "off-angle strike sampling attenuates the two-sample step statistic; 16 "
                     "strikes reduce the worst-case angular error; persistence removed because "
                     "L = 1/15/25 px were statistically indistinguishable on holdout.",
        "named_non_fault_mimic": "distal alluvial-fan margins and Lake Lahontan shorelines "
                                 "(straightness from orientation consensus); aeromagnetic/"
                                 "radiometric acquisition seams (two-of-three median vote); "
                                 "erosional volcanic mesa/flow margins (irreducible confounder).",
        "layers": "same 10-band whitened step stack as H85-1: rtp, iso_grav_anom, cond_surf, "
                  "depth_to_base_surf (potential field); GeoDAWN K/Th/TC (radiometric); "
                  "det_elev, det_elev_slope, LiDAR step_max (topographic).",
        "difference_from_repo": "H85-1 uses 8 strikes + persistence 15 px; this experiment uses "
                                "16 strikes + persistence 1 px (retired). No new data.",
        "leakage_canary": "not rerun: surface is unchanged in construction (covariance-whitened "
                          "offset differences, no catalogue input); H85-1 canary AUC = 0.5036.",
        "results": results,
        "n_withheld_positives": n_withheld,
        "evaluator_version": holdout.EVALUATOR_VERSION,
        "runtime_s": time.time() - t0,
    }
    path = OUT / "experiment_2_orientation.json"
    path.write_text(json.dumps(summary, indent=2, default=float) + "\n")
    print(f"\n-> {path}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    from preflight import experiment_gate
    blocked = experiment_gate(ROOT)
    if blocked:
        raise SystemExit(blocked)
    raise SystemExit(main())
