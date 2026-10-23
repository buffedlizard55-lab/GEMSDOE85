#!/usr/bin/env python3
"""Build all 58 catalogue-free channels and run single-feature leakage canaries (<0.90 AUC)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems85 import gapvent, grid, holdout


def main() -> int:
    t0 = time.time()
    fp = grid.footprint()
    names, handles = gapvent.build_all(fp)
    t_build = time.time() - t0
    print(f"Built/loaded {len(names)} channels in {t_build:.1f}s", flush=True)

    cat = grid.catalogue()
    folds = holdout.make_folds(cat, n_folds=4, block_px=200, buffer_px=5)
    canaries: dict[str, float] = {}
    for name, h in zip(names, handles):
        arr = np.asarray(h, dtype=np.float32)
        auc = holdout.feature_auc(arr, folds, fp)
        canaries[name] = float(auc)
        flag = "LEAK!" if (auc > 0.90 or auc < 0.10) else "ok"
        print(f"  canary {name:26s}: AUC = {auc:.4f}  [{flag}]", flush=True)

    max_ch = max(canaries, key=lambda k: canaries[k])
    max_auc = canaries[max_ch]
    out = {
        "evaluator_version": holdout.EVALUATOR_VERSION,
        "n_withheld_positives": int(sum(f.n_withheld for f in folds)),
        "n_channels": len(canaries),
        "build_seconds": round(t_build, 2),
        "threshold_auc": 0.90,
        "max_auc_channel": max_ch,
        "max_auc": max_auc,
        "all_passed": bool(max_auc < 0.90),
        "canaries": canaries,
    }
    out_path = ROOT / "evidence" / "session_7ded4c0a_canaries.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nMax canary AUC: {max_ch} = {max_auc:.4f} (all < 0.90: {out['all_passed']})")
    assert out["all_passed"], f"Canary leakage detected on {max_ch}: {max_auc}"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
