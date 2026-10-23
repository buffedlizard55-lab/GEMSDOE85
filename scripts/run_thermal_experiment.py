#!/usr/bin/env python3
"""EXPERIMENT 1 (of 3): H_TM — thermal-spring proximity x GEO-Pb crest conjunction.

Hypothesis (declared before measuring):
  Geothermal upflow rises along permeable fault conduits, so verified hot/warm
  springs are a direct, isotropic, short-range prior on blind fault location;
  GEO-Pb is an oriented, zero-thermal-information prior (measured AUC at hot/warm
  sites = 0.5034, p = 0.213 — statistically orthogonal). Re-rank GEO-Pb's fixed
  emission budget toward thermal evidence:

      fused(x) = crest(x) * (1 + lambda * exp(-d_thermal(x) / tau))

  d_thermal = distance to nearest hot/warm spring (px), springs from the DOE GDR
  1391 well/spring chemistry compilation (GDR row/col pixel coords — no catalogue
  column is used; dist_known_fault_px is label-derived and is NOT used).
  tau in {5, 10, 20} px (~0.5/1/2 km; the measured fault-spring lift is 1.50x at
  1 km), lambda in {0.5, 1.0, 2.0}. This is pure re-ranking under a mass
  constraint: no pixel is added that GEO-Pb did not already propose, so uncredited
  mass cannot grow — only the budget is redistributed (metric-algebra.md §4).

Why it targets catalogue-missing faults:
  619 of 1,839 hot/warm sites sit >3 km from any mapped fault (knowledge §2,
  Finding 2) — direct physical evidence of deep circulation with no mapped
  structure. The USGS/INGENIOUS catalogue is scarp-dominated; blind conduits
  under Holocene alluvium have no scarp but still host springs.

Named non-fault mimic:
  Spring lines along valley floors/playa margins and irrigation-well alignments
  along roads (linear anthropogenic or depositional water sources). Mitigated by
  requiring the GEO-Pb juxtaposition factor (a spring alone scores nothing).

Differs from everything in the repo:
  No existing channel or emission rule touches GDR thermal point data; the only
  thermal reference in the fleet (h19-4 'thermal-pop') used a thermal population
  raster as a corroboration weight on an already-catalogue-anchored ridge field
  and scored 0.1894 live — never tested on a hide-and-recover holdout here.

Instrument: holdout.make_folds + score_folds (pooled DTI, alpha 0.2, beta 0.8,
300 m triangular kernel, 4 spatially-blocked folds, 60,988 withheld positives).
Every number below is HOLDOUT-DTI; nothing is an organizer score.
"""

from __future__ import annotations

import csv
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
SPRINGS = ROOT / "data" / "external" / "gdr_wellspring_in_footprint.csv"


# ------------------------------------------------------------------ thermal field


def thermal_proximity(fp: np.ndarray, tau_px: float) -> np.ndarray:
    """exp(-distance-to-nearest-hot/warm-spring / tau), 0 outside footprint."""
    rows, cols, wts = [], [], []
    with SPRINGS.open(newline="") as fh:
        for rec in csv.DictReader(fh):
            tc = (rec.get("thermalclass") or "").strip()
            if tc not in ("Hot", "Warm"):
                continue
            r = rec.get("row")
            c = rec.get("col")
            if r in (None, "") or c in (None, ""):
                continue
            temp = rec.get("temp_c") or ""
            try:
                t = float(temp)
            except ValueError:
                t = 80.0 if tc == "Hot" else 50.0
            wts.append(max(1.0, min(t, 120.0)) / 100.0)  # temperature weight
            rows.append(int(float(r)))
            cols.append(int(float(c)))
    rows = np.array(rows, dtype=int)
    cols = np.array(cols, dtype=int)
    keep = (rows >= 0) & (rows < fp.shape[0]) & (cols >= 0) & (cols < fp.shape[1])
    rows, cols, wts = rows[keep], cols[keep], np.array(wts, dtype=float)[keep]
    print(f"  hot/warm spring sites used: {rows.size}")

    d = np.full(fp.shape, np.inf, dtype=np.float32)
    d[rows, cols] = 0.0
    from scipy import ndimage as ndi

    d = ndi.distance_transform_edt(~np.isfinite(d))  # distance to nearest zero = spring
    # weight: nearer spring -> stronger; nearest-distance kernel combines sites
    field = np.exp(-d / tau_px).astype(np.float32)
    field[~fp] = 0.0
    return field


# ------------------------------------------------------------------ scoring


def run(field_name: str, field: np.ndarray, folds, n: int, sep_px: float,
        exclude_px: int) -> dict:
    """Score one field at one mass on the holdout; return pooled DTI + parts."""
    fp = grid.footprint()

    def surf(fold, f=field, n=n):
        return emission.emit(f, footprint=fp, visible_catalogue=fold.visible,
                             n=n, sep_px=sep_px, exclude_px=exclude_px)

    r = holdout.score_folds(surf, folds, domain=fp)
    return {"pooled_dti": r.pooled_dti, "ci95": list(r.ci95),
            "n_withheld_positives": r.n_withheld_positives,
            "per_fold": [f.dti for f in r.folds],
            "tp_w": r.tp_w, "fp_w": r.fp_w, "fn_w": r.fn_w,
            "pred_pixels": r.folds[-1].pred_pixels}


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    n_withheld = sum(f.n_withheld for f in folds)
    print(f"withheld positives: {n_withheld} across {[f.n_withheld for f in folds]}")

    # ---- GEO-Pb crest surface (catalogue-free; cached)
    CACHE.mkdir(parents=True, exist_ok=True)
    crest_path = CACHE / "ch_geopb_crest.npy"
    if not crest_path.exists():
        print("computing GEO-Pb crest surface ...")
        base, axis = geopb.geopb_surface(sigma=1.5, normals=tuple(geopb.NORMALS_R3),
                                         persistence_px=15.0, footprint=fp,
                                         return_parts=True)
        crest = geopb.crest(base, axis, tuple(geopb.NORMALS_R3))
        np.save(crest_path, crest.astype(np.float32))
        del base, axis
    crest = np.load(crest_path)
    print(f"crest loaded: max {crest[fp].max():.4f}")

    # ---- leakage canary: thermal field alone vs withheld positives (per tau)
    canary = {}
    for tau in (5.0, 10.0, 20.0):
        th = thermal_proximity(fp, tau)
        np.save(CACHE / f"ch_thermal_tau{int(tau)}.npy", th)
        auc = holdout.feature_auc(th, folds, fp)
        canary[f"thermal_tau{int(tau)}"] = auc
        print(f"  LEAKAGE CANARY thermal tau={int(tau)}px AUC = {auc:.4f} "
              f"({'CLEAN <0.90' if auc < 0.90 else 'SUSPECT'})")

    # ---- baseline: crest alone at matched masses (re-measured in this run)
    baseline = {}
    for n in (37_654, 60_000, 90_000):
        baseline[n] = run("geopb_crest", crest, folds, n, sep_px=4.0, exclude_px=2)
        b = baseline[n]
        n_s = f"{n:,}"; bdt = f"{b['pooled_dti']:.5f}"
        clo = f"{b['ci95'][0]:.5f}"; chi = f"{b['ci95'][1]:.5f}"
        print("  BASELINE crest n=" + n_s + "  pooled DTI = " + bdt +
              " CI [" + clo + "," + chi + "]")

    # ---- fusion grid search at n=60,000
    results = []
    for lam in (0.5, 1.0, 2.0):
        for tau in (5.0, 10.0, 20.0):
            th = np.load(CACHE / f"ch_thermal_tau{int(tau)}.npy")
            fused = (crest * (1.0 + lam * th)).astype(np.float32)
            fused[~fp] = 0.0
            np.save(CACHE / f"ch_geopb_thermal_l{lam}_t{int(tau)}.npy", fused)
            res = run(f"geopb_thermal_l{lam}_t{int(tau)}", fused, folds, 60_000,
                      sep_px=4.0, exclude_px=2)
            delta = res["pooled_dti"] - baseline[60_000]["pooled_dti"]
            results.append({"lambda": lam, "tau_px": int(tau), **res,
                            "delta_vs_crest_at_60k": delta})
            dti = res["pooled_dti"]; lo = res["ci95"][0]; hi = res["ci95"][1]
            dtis = f"{dti:.5f}"; clos = f"{lo:.5f}"; chis = f"{hi:.5f}"
            deltas = f"{delta:+.5f}"
            print("  FUSED l=" + str(lam) + " tau=" + str(int(tau)) + "px n=60k  DTI = " +
                  dtis + " CI [" + clos + "," + chis + "]  delta vs crest = " + deltas)

    best = max(results, key=lambda r: r["pooled_dti"])
    lam = best["lambda"]; tau = best["tau_px"]; bdt = best["pooled_dti"]
    bdts = f"{bdt:.5f}"
    print("  BEST fusion: lambda=" + str(lam) + " tau=" + str(tau) + "px  DTI " + bdts)

    # ---- re-measure winner at all masses + crest at all masses
    winner_path = CACHE / f"ch_geopb_thermal_l{best['lambda']}_t{best['tau_px']}.npy"
    winner = np.load(winner_path)
    detail = {"crest": {}, "winner": {}}
    for n in (37_654, 60_000, 90_000):
        detail["crest"][str(n)] = run("geopb_crest", crest, folds, n, 4.0, 2)
        detail["winner"][str(n)] = run(f"winner l{best['lambda']} t{best['tau_px']}",
                                       winner, folds, n, 4.0, 2)
        c = detail["crest"][str(n)]["pooled_dti"]
        w = detail["winner"][str(n)]["pooled_dti"]
        print(f"  n={n:,}  crest={c:.5f}  winner={w:.5f}  delta={w-c:+.5f}")

    summary = {
        "experiment": 1, "hypothesis_id": "H_TM thermal-spring x GEO-Pb conjunction",
        "hypothesis": "score(x) = geopb_crest(x) * (1 + lambda * exp(-d_thermal(x)/tau)); "
                      "re-rank GEO-Pb's fixed dot budget toward verified hot/warm springs (GDR 1391).",
        "mechanism": "hot/warm springs mark deep circulation along permeable fault conduits; "
                     "619/1839 sites are >3 km from any mapped fault; GEO-Pb is blind to them (AUC 0.5034).",
        "named_non_fault_mimic": "valley-floor/playa-margin spring lines and road-aligned irrigation wells; "
                                 "mitigated by requiring the GEO-Pb juxtaposition factor.",
        "layers": "training_features: geopb_crest (10-band whitened step statistic, 2-of-3 domains); "
                  "GDR 1391 gdr_wellspring_in_footprint.csv (row/col, thermalclass, temp_c) -> d_thermal.",
        "difference_from_repo": "no channel or rule in this repo or the fleet uses GDR thermal point data; "
                                "pure re-ranking under a mass constraint, no added uncredited mass.",
        "leakage_canary": canary,
        "baseline_crest": baseline,
        "fusion_grid": results,
        "winner": {"lambda": best["lambda"], "tau_px": best["tau_px"]},
        "detail_at_matched_mass": detail,
        "n_withheld_positives": n_withheld,
        "evaluator_version": holdout.EVALUATOR_VERSION,
        "runtime_s": time.time() - t0,
    }
    path = OUT / "experiment_1_thermal.json"
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
