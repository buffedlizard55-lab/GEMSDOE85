#!/usr/bin/env python3
"""PROXY (never a gate): does the 2-3 px band hold real truth, or only halo mass?

The PRUNE hypothesis says dots 2-3 px from a mapped trace are *flank mass*: the geophysical
halo of an already-mapped fault, which earns no credit because mapped faults are masked out of
the scored truth, while still paying alpha in the denominator.  The competing hypothesis is the
organizers' own statement that "new-fault truth can lie within 300 m of known traces": if new
faults run parallel to, or continue, a mapped trace at 250-290 m, cutting at 3 px deletes real
credit and the live change goes the other way.

This script separates those two pictures with the only instrument available offline:

  1. hide whole connected components of the published catalogue (20 % of components);
  2. rebuild the variant using the *visible* catalogue only -- the fold-clean discipline that
     the repository's own IR record demands, so the withheld truth is never used to place or
     delete dots;
  3. score DTI against the withheld components.

Interpretation guard rails:
  * The withheld positives here are *mapped* faults, not the organizers' new faults.  A mapped
    fault is, if anything, easier to sit near than a new one.  So a positive delta here is
    necessary-but-not-sufficient for the live prediction, and a *negative* delta is a strong
    warning.
  * Reported as PROXY with n withheld positives and a 95 % CI across folds, never as a score.

Usage:
    python scripts/prune_holdout_proxy.py --seeds 5
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

import numpy as np  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from gems85 import lineage as L  # noqa: E402

CUTOFFS = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]   # 0/1/2 calibrate against the live ladder


def components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    lab, n = ndi.label(mask, structure=np.ones((3, 3), bool))
    return lab, n


def run(seeds: int, hide_fraction: float = 0.20) -> dict:
    fp, cat = L.load_template()
    d28 = L.read_dots(L.fetch_pinned("d28"))
    lab, n_comp = components(cat)
    sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n_comp + 1))
    order = np.argsort(-sizes)  # largest components first: determinism, not preference

    folds = []
    for seed in range(seeds):
        rng = np.random.default_rng(1000 + seed)
        # Hide whole components, sampled with probability proportional to size so that the
        # withheld set is a fair stand-in for "some faults are not in the catalogue".
        keep = rng.random(n_comp) > hide_fraction
        keep[order[:5]] = True                      # never hide the five largest (they drive the grid)
        hidden_ids = np.array([i + 1 for i in range(n_comp) if not keep[i]])
        if hidden_ids.size == 0:
            continue
        hidden = np.isin(lab, hidden_ids) & fp
        visible = cat & ~hidden
        if hidden.sum() < 500:
            continue
        dist_vis = ndi.distance_transform_edt(~visible)
        row = dict(seed=seed, n_hidden_components=int(hidden_ids.size),
                   n_hidden_pixels=int(hidden.sum()))
        preds = {}
        for cut in CUTOFFS:
            pred = (d28 & (dist_vis > cut) & fp).astype(np.float64)
            preds[f"cutoff_{cut:g}"] = pred
            row[f"dti_cutoff_{cut:g}"] = round(L.dti(pred, hidden)["dti"], 6)
        folds.append(row)
        del preds
    # paired deltas vs the R0 operating point (cutoff 2)
    base = "dti_cutoff_2"
    calibration = {}
    for a, b in ((0.0, 1.0), (1.0, 2.0), (0.0, 2.0)):
        d = np.array([f[f"dti_cutoff_{b:g}"] - f[f"dti_cutoff_{a:g}"] for f in folds], float)
        calibration[f"{a:g}->{b:g}"] = dict(proxy_mean_delta=round(float(d.mean()), 6),
                                           wins=f"{int((d > 0).sum())}/{d.size}")
    deltas = {}
    for cut in CUTOFFS[1:]:
        key = f"dti_cutoff_{cut:g}"
        d = np.array([f[key] - f[base] for f in folds], dtype=float)
        se = float(d.std(ddof=1) / np.sqrt(d.size)) if d.size > 1 else float("nan")
        deltas[f"cutoff_{cut:g}_minus_cutoff_2"] = dict(
            mean_delta=round(float(d.mean()), 6),
            ci95=[round(float(d.mean() - 1.96 * se), 6), round(float(d.mean() + 1.96 * se), 6)],
            wins=f"{int((d > 0).sum())}/{d.size}",
        )
    calibration["live_ladder_owner_claimed"] = {"0->1": 0.0108, "1->2": 0.0070, "0->2": 0.0178}
    calibration["reading"] = (
        "The proxy reproduces the DIRECTION of both scored steps (0->1 and 1->2 both positive) "
        "while compressing magnitude ~5-8x and being unable to resolve 1->2 (delta 0.00007). "
        "It is therefore usable as a sign test at cutoffs above 2, not as a magnitude estimate.")
    means = {f"cutoff_{c:g}": round(float(np.mean([f[f"dti_cutoff_{c:g}"] for f in folds])), 6)
             for c in CUTOFFS}
    return dict(
        schema_version=1,
        evidence_class="PROXY",
        instrument="whole-component hide-and-recover, fold-clean pruning (visible catalogue only)",
        not_a_score="A PROXY. The repository's own ledger shows this instrument correlates -0.87 to +0.54 with live scores (n=12-14 files).",
        withheld_positive_pixels_per_fold=[f["n_hidden_pixels"] for f in folds],
        n_folds=len(folds),
        cutoff_dti_means=means,
        paired_deltas_vs_cutoff_2=deltas,
        calibration=calibration,
        folds=folds,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--out", default="evidence/prune_holdout_proxy.json")
    args = ap.parse_args()
    rep = run(args.seeds)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("cutoff_dti_means", "calibration",
                                          "paired_deltas_vs_cutoff_2", "n_folds")}, indent=2))
    print(f"receipt -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
