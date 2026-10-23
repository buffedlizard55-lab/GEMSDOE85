#!/usr/bin/env python3
"""Report-only PROXY evaluation for the v2 PRUNE axis. NEVER a gate.

Two instruments, both labelled PROXY (brief sections 3/6/8): the catalogue
hide-and-recover holdout correlated -0.87..+0.54 with live scores across
sessions, so nothing here promotes or vetoes a variant.

1. Fold-equivalent hide-and-recover (``gems85-holdout-v1.0.0``): the PRUNE
   *rule* is applied per fold using only the fold-visible catalogue
   (base = d2.8 dots; radii 1/2/3 px, >=3 px, and 3 px + refill), then
   scored against withheld catalogue segments. Static R0/variant rasters
   are also scored to document the known instrument defect for files
   pruned against the full catalogue (they cannot earn credit near
   withheld segments by construction).
   Known bias, shared by all radii: the static d2.8 base already avoids
   full-catalogue pixels (including withheld ones); only *differences
   between radii* are interpretable, and only as a PROXY.

2. SGMC control: exact DTI of the static masks against off-catalogue
   (>3 px) SGMC fault pixels inside the footprint (pinned derived SGMC
   raster). A sanity control in the spirit of GEMSDOE32's live-mirror;
   SGMC mapping scale/registration differ from the hidden expert labels.

No feature is trained, so the single-feature leakage canary is not
applicable. Inputs are the same pinned rasters as the builder, plus the
pinned SGMC raster (registry/data_manifest.json:
ext_derived_sgmc_faults_100m_u8). Fail closed on any hash mismatch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from build_prune_variants import PINS, greedy_refill, read_dots  # noqa: E402
from gems85.holdout import make_folds, score_folds, score_static  # noqa: E402
from gems85.metric import dti as dti_fn  # noqa: E402
from validate_v2_release import sha256_file  # noqa: E402

SGMC = (ROOT / "data/external/derived_sgmc_faults_100m_u8.tif",
        "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", type=Path, default=ROOT / "evidence/v2-prune-proxy.json")
    ap.add_argument("--builds", type=Path, default=ROOT / "evidence/v2-prune-builds.json")
    args = ap.parse_args()

    paths = {}
    for key, (rel, pin) in PINS.items():
        p = ROOT / rel
        if not p.is_file() or sha256_file(p) != pin:
            raise SystemExit(f"pinned input missing/mismatched: {rel}")
        paths[key] = p
    sgmc_path, sgmc_pin = SGMC
    if not sgmc_path.is_file() or sha256_file(sgmc_path) != sgmc_pin:
        raise SystemExit("pinned SGMC raster missing/mismatched; restore it first")

    with rasterio.open(paths["sample"]) as ds:
        footprint = np.isfinite(ds.read(1))
    catalogue = read_dots(paths["catalogue"]) & footprint
    d28 = read_dots(paths["d28"]) & footprint
    d15 = read_dots(paths["d15"])
    s5 = read_dots(paths["h19_5"])
    s4 = read_dots(paths["h19_4"])
    tier = np.where(d15, 0, np.where(s4, 1, 2)).astype(np.int16)

    folds = make_folds(catalogue)  # gems85-holdout-v1.0.0 defaults (seed fixed)
    fold_cache = {}

    def rule(radius: float, ge: bool = False, refill: bool = False):
        def fn(fold):
            key = (fold.name, radius, ge, refill)
            if key not in fold_cache:
                dv = distance_transform_edt(~fold.visible)
                keep = (dv >= radius) if ge else (dv > radius)
                pred = d28 & keep
                if refill:
                    target = int((d28 & (dv > 2)).sum())  # fold R0-equivalent count
                    need = target - int(pred.sum())
                    if need > 0:
                        dk = distance_transform_edt(~pred)
                        pool = s5 & footprint & (dv > 3) & ~pred & (dk > 2.0)
                        cand = np.flatnonzero(pool)
                        order = cand[np.lexsort((cand % pool.shape[1], cand // pool.shape[1],
                                                  -dk.ravel()[cand], tier.ravel()[cand]))]
                        pred = pred | greedy_refill(pool, pred, order, need, 2.0)
                fold_cache[key] = pred.astype(np.float64)
            return fold_cache[key]
        return fn

    rules = {
        "fold_eq_prune_gt1px_h27_rule": rule(1),
        "fold_eq_prune_gt2px_R0_rule": rule(2),
        "fold_eq_prune_gt3px": rule(3),
        "fold_eq_prune_ge3px": rule(3, ge=True),
        "fold_eq_prune_gt3px_refill": rule(3, refill=True),
    }
    holdout = {}
    for name, fn in rules.items():
        res = score_folds(fn, folds, domain=footprint)
        holdout[name] = res.as_dict()
        print(f"PROXY {name}: pooled={res.pooled_dti:.5f} ci95={res.ci95} "
              f"n_withheld={res.n_withheld_positives}")

    builds = json.loads(args.builds.read_text())
    static_masks = {"R0_parent_static": read_dots(paths["r0"])}
    for value, v in builds["variants"].items():
        static_masks[f"{value}_static"] = read_dots(ROOT / v["files"]["nan"]["path"])
    static_holdout = {}
    for name, mask in static_masks.items():
        res = score_static(mask.astype(np.float64), folds, domain=footprint)
        static_holdout[name] = res.as_dict()
        print(f"PROXY {name}: pooled={res.pooled_dti:.5f} (static; instrument defect expected)")

    with rasterio.open(sgmc_path) as ds:
        sgmc = ds.read(1) > 0
    dist_cat = distance_transform_edt(~catalogue)
    truth = sgmc & footprint & (dist_cat > 3)
    sgmc_control = {"truth_pixels_off_catalogue_gt3px": int(truth.sum()), "dti": {}}
    for name, mask in static_masks.items():
        r = dti_fn(mask.astype(np.float64), truth, domain=footprint)
        sgmc_control["dti"][name] = r.as_dict()
        print(f"SGMC-control {name}: DTI={r.dti:.5f} (truth n={int(truth.sum())})")

    out = {
        "evidence_label": "PROXY",
        "note": ("Report only, never a gate. Hide-and-recover correlated -0.87..+0.54 "
                 "with live scores (brief section 3). Static pruned files are "
                 "penalized by construction; fold-equivalent rules are the "
                 "interpretable comparison."),
        "evaluator": "gems85-holdout-v1.0.0 (src/gems85/holdout.py), folds=4, seed=20261022",
        "fold_equivalent_rules": holdout,
        "static_rasters_for_contrast": static_holdout,
        "sgmc_control": sgmc_control,
        "leakage_canary": ("NOT APPLICABLE: no feature/model trained this session; "
                           "variants are deterministic edits of pinned dot masks"),
    }
    args.evidence.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(f"wrote {args.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
