#!/usr/bin/env python3
"""Score every registry artifact on the hide-and-recover holdout and correlate with live.

This answers the only question that licenses any later claim: *does this repository's
holdout rank the real leaderboard?*  If it does not, no holdout gain may be called a
projected score.  Output: evidence/instrument_calibration.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import grid, holdout  # noqa: E402

OUT = ROOT / "evidence" / "instrument_calibration.json"


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    for f in folds:
        print(f"  {f.name}: withheld {f.n_withheld:6d}  visible {f.n_visible:6d}")

    reg = json.loads((ROOT / "registry" / "scored_artifacts.json").read_text())
    rows = []
    for a in reg["artifacts"]:
        p = ROOT / a["file"]
        with rasterio.open(p) as src:
            grid.assert_grid(src, p.name)
            arr = src.read(1).astype(np.float64)
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        arr = np.clip(arr, 0.0, 1.0)
        res = holdout.score_static(arr, folds, domain=fp)
        on_cat = int(((arr > 0) & cat).sum())
        rows.append({
            "file": p.name,
            "label": a["label"],
            "owner_reported_live_dti": a["owner_reported_live_dti"],
            "holdout_pooled_dti": res.pooled_dti,
            "holdout_ci95": list(res.ci95),
            "n_emitting_px": int((arr > 0).sum()),
            "pred_mass": float(arr.sum()),
            "on_catalogue_px": on_cat,
            "per_fold": {f.name: f.dti for f in res.folds},
        })
        print(f"[{time.time()-t0:6.1f}s] live {a['owner_reported_live_dti']:.4f}  "
              f"holdout {res.pooled_dti:.5f}  n={rows[-1]['n_emitting_px']:7d}  "
              f"oncat={on_cat:6d}  {p.name[:58]}")

    live = np.array([r["owner_reported_live_dti"] for r in rows])
    hold = np.array([r["holdout_pooled_dti"] for r in rows])
    rho, p_rho = stats.spearmanr(live, hold)
    pear, p_pear = stats.pearsonr(live, hold)
    # a competing "instrument": does the raw emitted-pixel count explain live score?
    n_px = np.array([r["n_emitting_px"] for r in rows], dtype=float)
    rho_n, p_n = stats.spearmanr(live, n_px)
    oncat = np.array([r["on_catalogue_px"] for r in rows], dtype=float)
    rho_c, p_c = stats.spearmanr(live, oncat)

    summary = {
        "evaluator_version": holdout.EVALUATOR_VERSION,
        "n_artifacts": len(rows),
        "folds": [{"name": f.name, "n_withheld": f.n_withheld, "n_visible": f.n_visible}
                  for f in folds],
        "spearman_holdout_vs_live": {"rho": float(rho), "p": float(p_rho)},
        "pearson_holdout_vs_live": {"r": float(pear), "p": float(p_pear)},
        "spearman_npx_vs_live": {"rho": float(rho_n), "p": float(p_n)},
        "spearman_oncat_vs_live": {"rho": float(rho_c), "p": float(p_c)},
        "artifacts": rows,
        "runtime_s": time.time() - t0,
    }
    OUT.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nSpearman(holdout, live)      rho = {rho:+.4f}  p = {p_rho:.4f}   n = {len(rows)}")
    print(f"Pearson (holdout, live)      r   = {pear:+.4f}  p = {p_pear:.4f}")
    print(f"Spearman(n_emitting_px,live) rho = {rho_n:+.4f}  p = {p_n:.4f}")
    print(f"Spearman(on_catalogue,live)  rho = {rho_c:+.4f}  p = {p_c:.4f}")
    print(f"-> {OUT.relative_to(ROOT)}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
