#!/usr/bin/env python3
"""PROXY (never a gate): what does the fold-clean instrument say about the MASS trio?

Same instrument as the PRUNE session, with one addition that this axis specifically needs: a
**mass** calibration anchor.  The PRUNE session could only calibrate against catalogue-distance
steps.  Here the lineage supplies a pure thinning step with a live score:

    d1.5  60,069 dots  live 0.2477 (CLAIM)   ->  d2.8  44,090 dots  live 0.2600 (CLAIM)
                                                (+0.0123 for removing 15,979 dots)

Both files are SHA-256 pinned; both are scored rungs of the same lineage.  The proxy is run on
all of them in the same folds, so the scaling between proxy units and live units is measured on a
mass change rather than borrowed from a distance change.

Fold-clean discipline: R0's *parent* is given, but anything a variant does with the catalogue is
rebuilt per fold against the VISIBLE catalogue only (matters for the `p10` arm, whose d > 2 px
constraint would otherwise see the withheld traces).

Usage:
    python scripts/mass_holdout_proxy.py --seeds 5
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
from gems85 import mass as M  # noqa: E402

D15 = ROOT / "work" / "ref" / "d15-nan.tif"
D15_SHA = "68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310"
LIVE = {"d15": 0.2477, "d28": 0.2600, "p1": 0.2708, "r0": 0.2778}   # all CLAIM


def run(seeds: int, hide_fraction: float = 0.20) -> dict:
    fp, cat = L.load_template()
    r0 = L.read_dots(L.fetch_pinned("r0"))
    d28 = L.read_dots(L.fetch_pinned("d28"))
    p1 = L.read_dots(L.fetch_pinned("prune1"))
    field = L.read_dots(L.fetch_pinned("h19_5"))
    d15 = L.read_dots(D15) if D15.is_file() else None
    if d15 is not None and L.sha256_file(D15) != D15_SHA:
        raise SystemExit("d1.5 anchor does not match its pin")

    lab, n_comp = ndi.label(cat, structure=np.ones((3, 3), bool))
    sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n_comp + 1))
    order = np.argsort(-sizes)
    rank = M.rank_by_extent(r0, field)

    folds = []
    for seed in range(seeds):
        rng = np.random.default_rng(1000 + seed)
        keep = rng.random(n_comp) > hide_fraction
        keep[order[:5]] = True                      # never hide the five largest components
        hidden_ids = np.array([i + 1 for i in range(n_comp) if not keep[i]])
        if hidden_ids.size == 0:
            continue
        hidden = np.isin(lab, hidden_ids) & fp
        if hidden.sum() < 500:
            continue
        visible = cat & ~hidden
        dist_vis = ndi.distance_transform_edt(~visible)

        # FOLD-CLEAN LADDER.  The shipped d28/p1/r0 were pruned against the FULL catalogue, so in
        # a fold that hides components they have already removed mass near the *withheld* truth.
        # Comparing them as-is measures that artefact, not the variants (first run: proxy said
        # -0.068 for a step that scores +0.0108 live).  Every arm is therefore rebuilt here from
        # the same catalogue-free source (d2.8) against the VISIBLE catalogue only.
        base = d28 & fp
        p1f = base & (dist_vis > 1.0)
        r0f = base & (dist_vis > 2.0)
        n_f = int(r0f.sum())
        n_delta = int(round(0.10 * n_f))
        rank_f = M.rank_by_extent(r0f, field)

        preds = {"r0f": r0f, "d28": base, "p1f": p1f}
        if d15 is not None:
            preds["d15"] = d15                      # catalogue-free, so already symmetric
        preds["mass-m10e"] = M.drop_by_rank(r0f, rank_f, n_delta)[0]
        preds["mass-m10u"] = M.drop_uniform(r0f, n_delta)[0]
        preds["mass-p10"] = M.add_by_extent(r0f, field, dist_vis, n_delta)[0]

        row = dict(seed=seed, n_hidden_components=int(hidden_ids.size),
                   n_hidden_pixels=int(hidden.sum()), n_fold_clean_r0=n_f)
        for k, v in preds.items():
            row[k] = round(L.dti(v.astype(np.float64), hidden)["dti"], 6)
        folds.append(row)

    keys = ["d15", "d28", "p1f", "r0f", "mass-m10e", "mass-m10u", "mass-p10"]
    means = {k: round(float(np.mean([f[k] for f in folds])), 6) for k in keys if all(k in f for f in folds)}

    def delta(a: str, b: str) -> dict:
        d = np.array([f[b] - f[a] for f in folds], float)
        se = float(d.std(ddof=1) / np.sqrt(d.size)) if d.size > 1 else float("nan")
        return dict(proxy_mean_delta=round(float(d.mean()), 6),
                    ci95=[round(float(d.mean() - 1.96 * se), 6), round(float(d.mean() + 1.96 * se), 6)],
                    wins=f"{int((d > 0).sum())}/{d.size}")

    anchors = dict(
        mass_d15_to_d28=dict(proxy=delta("d15", "d28"), live=LIVE["d28"] - LIVE["d15"],
                             note="pure thinning by 15,979 dots; the MASS calibration anchor"),
        prune_d28_to_p1=dict(proxy=delta("d28", "p1f"), live=LIVE["p1"] - LIVE["d28"],
                             note="catalogue prune, fold-clean rebuild of the p1 rung"),
        prune_p1_to_r0=dict(proxy=delta("p1f", "r0f"), live=LIVE["r0"] - LIVE["p1"],
                            note="catalogue prune, fold-clean rebuild of the R0 rung"),
        prune_d28_to_r0=dict(proxy=delta("d28", "r0f"), live=LIVE["r0"] - LIVE["d28"],
                             note="both scored prune steps combined"),
    )
    scale = None
    pa = anchors["mass_d15_to_d28"]["proxy"]["proxy_mean_delta"]
    if pa:
        scale = round((LIVE["d28"] - LIVE["d15"]) / pa, 3)
    variants = {k: delta("r0f", k) for k in ("mass-m10e", "mass-m10u", "mass-p10") if k in means}
    for k, v in variants.items():
        v["live_scaled_by_mass_anchor"] = (round(v["proxy_mean_delta"] * scale, 4)
                                           if scale is not None else None)
    return dict(
        schema_version=1, evidence_class="PROXY",
        instrument="whole-component hide-and-recover, fold-clean rebuilds, 5 folds, 20 % components",
        not_a_score="A PROXY. Ledger correlation with live is -0.87 to +0.54 (n=12-14 files).",
        n_folds=len(folds), means=means, anchors=anchors,
        stock_r0_dots=37654, fold_clean_r0_dots=[f["n_fold_clean_r0"] for f in folds],
        mass_anchor_scale=scale,
        variants_vs_r0=variants,
        reading=("The mass anchor measures how many proxy units one live unit is worth on a pure "
                 "mass change; it is used only to put the three deltas on a live-ish scale, and the "
                 "result stays a MODEL until a receipt exists."),
        folds=folds,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--out", default="evidence/mass_holdout_proxy.json")
    args = ap.parse_args()
    rep = run(args.seeds)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("means", "anchors", "mass_anchor_scale",
                                          "variants_vs_r0")}, indent=2))
    print(f"receipt -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
