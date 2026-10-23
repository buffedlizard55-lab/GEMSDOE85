#!/usr/bin/env python3
"""EXPERIMENT 3 (of 3): credit-bar-gated emission on the GEO-Pb crest field.

Hypothesis (declared before measuring):
  DTI = T / ( alpha*(T + F) + beta*K ): every emitted pixel pays alpha FP mass unless it
  captures truth-weight.  The current rule emits exactly n top-field dots regardless of
  marginal credit, so ~94 % of emitted mass is uncredited (measured in evidence/).  The
  repo's emitter.py implements the metric's exact marginal-gain theorem: accept a dot only
  while its realised credit exceeds the bar alpha*DTI/(1-alpha*DTI) (two-round form with
  rho option).  Gated emission should raise holdout DTI at matched-or-lower mass by dropping
  dots whose field-based expected credit cannot pay their alpha tax.

  This is the *packing* lever, not a new field -- the algebra (docs/research/metric-algebra.md
  §4) says packing is exhausted for the h19-5 field; this tests whether it is also exhausted
  for GEO-Pb.  Negative result expected, published either way.

Instrument: holdout.make_folds + score_folds (pooled DTI, alpha 0.2, beta 0.8, 300 m kernel,
4 spatially-blocked folds, 60,988 withheld positives).  Surface per fold: emitter.greedy on
the crest field masked to allowed pixels (footprint minus visible-fault 2 px halo), hard cap
60,000 dots.  Matched-mass control: plain top-60k emission (already measured: 0.08971) plus a
plain run at whatever mass the gate settles on if it differs materially.

HOLDOUT-DTI only.  No catalogue input in the surface; visible faults masked per fold.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import emission, geopb, grid, holdout  # noqa: E402
from gems85 import emitter as EM  # noqa: E402

CACHE = ROOT / "data" / "cache"
OUT = ROOT / "evidence"
BUDGET = 60_000
EXCLUDE_PX = 2


def allowed_for(fold_visible: np.ndarray, fp: np.ndarray) -> np.ndarray:
    halo = ndi.binary_dilation(fold_visible, np.ones((3, 3), bool), iterations=EXCLUDE_PX)
    return fp & ~halo


def run_gated(field, folds, prior_dti: float) -> dict:
    fp = grid.footprint()

    def surf(fold, f=field):
        masked = np.where(allowed_for(fold.visible, fp), f, 0.0)
        mask, log = EM.emit(masked, budget=BUDGET, prior_dti=prior_dti)
        return mask.astype(np.float64)

    r = holdout.score_folds(surf, folds, domain=fp)
    # total dots actually emitted (union over folds is per-fold; report mean count)
    return {"pooled_dti": r.pooled_dti, "ci95": list(r.ci95),
            "per_fold": [f.dti for f in r.folds],
            "mean_emitted": float(np.mean([f.pred_pixels for f in r.folds])),
            "n_withheld_positives": r.n_withheld_positives}


def run_plain(field, folds, n: int) -> dict:
    return holdout.score_folds(
        lambda fold, f=field, n=n: emission.emit(f, footprint=grid.footprint(),
                                                 visible_catalogue=fold.visible, n=n,
                                                 sep_px=4.0, exclude_px=EXCLUDE_PX),
        folds, domain=grid.footprint())


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    n_withheld = sum(f.n_withheld for f in folds)
    print(f"withheld positives: {n_withheld} across {[f.n_withheld for f in folds]}")

    crest_path = CACHE / "ch_geopb_crest.npy"
    crest = np.load(crest_path)
    print(f"crest support (fp, >0): {int(((crest > 0) & fp).sum()):,}")

    plain60 = run_plain(crest, folds, 60_000)
    d60 = plain60.pooled_dti
    dts = f"{d60:.5f}"
    print("  PLAIN crest n=60,000  pooled DTI = " + dts +
          " CI [" + f"{plain60.ci95[0]:.5f}" + "," + f"{plain60.ci95[1]:.5f}" + "]")

    results = []
    for prior_dti in (0.06, 0.09, 0.12):
        res = run_gated(crest, folds, prior_dti)
        results.append({"prior_dti": prior_dti, **res})
        ne = res["mean_emitted"]; d = res["pooled_dti"]
        pes = f"{ne:,.0f}"; dts = f"{d:.5f}"
        print("  GATED prior=" + str(prior_dti) + " emitted~" + pes +
              "  pooled DTI = " + dts +
          " CI [" + f"{res['ci95'][0]:.5f}" + "," + f"{res['ci95'][1]:.5f}" + "] "
          "vs plain60 " + dts + " delta " + f"{d - d60:+.5f}")

    # matched-mass plain control at the gate's settled mass if materially different from 60k
    best = max(results, key=lambda r: r["pooled_dti"])
    nbest = int(round(best["mean_emitted"]))
    extra = None
    if abs(nbest - 60_000) > 0.10 * 60_000:
        extra = run_plain(crest, folds, nbest)
        dxtra = extra.pooled_dti
        print("  MATCHED plain crest n=" + f"{nbest:,}" + "  pooled DTI = " +
              f"{dxtra:.5f}" + " vs gated " + f"{best['pooled_dti']:.5f}" +
              " delta " + f"{best['pooled_dti'] - dxtra:+.5f}")

    summary = {
        "experiment": 3, "hypothesis_id": "H85-3 credit-bar-gated emission (emitter.py)",
        "hypothesis": "emit a dot only while its field-based marginal kernel credit exceeds "
                      "alpha*DTI/(1-alpha*DTI) (emitter.py lazy greedy), hard cap 60,000; "
                      "drop uncredited mass to raise credit per dot.",
        "mechanism": "exact marginal-gain theorem of metric.py; the alpha false-positive tax "
                     "is only paid on dots whose expected kernel proximity pays for it.",
        "named_non_fault_mimic": "same as H85-1: alluvial-fan margins / Lahontan shorelines, "
                                 "acquisition seams, volcanic mesa/flow margins (unchanged field).",
        "layers": "same geopb_crest field as H85-1 (10-band whitened step statistic, "
                  "2-of-3 domains); no new layers.",
        "difference_from_repo": "existing pipeline emits exactly n top dots; this experiment "
                                "gates emission on the metric's own marginal bar. Packing lever "
                                "only -- no new field, no new data.",
        "leakage_canary": "not rerun: emission mask uses per-fold visible faults only; field "
                          "unchanged from H85-1 (canary AUC 0.5036).",
        "plain60": {"pooled_dti": plain60.pooled_dti, "ci95": plain60.ci95,
                    "per_fold": [f.dti for f in plain60.folds]},
        "results": results,
        "matched_plain_control": None if extra is None else {
            "n": nbest, "pooled_dti": extra.pooled_dti,
            "ci95": extra.ci95, "per_fold": [f.dti for f in extra.folds]},
        "n_withheld_positives": n_withheld,
        "evaluator_version": holdout.EVALUATOR_VERSION,
        "runtime_s": time.time() - t0,
    }
    path = OUT / "experiment_3_emitter.json"
    path.write_text(json.dumps(summary, indent=2, default=float) + "\n")
    print(f"\n-> {path}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
