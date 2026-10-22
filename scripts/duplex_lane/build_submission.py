#!/usr/bin/env python3
"""Build the final GEMSDOE85 submission from the winning experiment's method.

Retrains the fold-proper detector on ALL visible catalogue faults (the only
catalogue use; features contain no catalogue-derived channel), predicts the
full grid, emits with the template lazy-greedy max-coverage emitter at the
holdout-chosen budget, confines emission to footprint & EDT(catalogue) > 2 px,
writes the all-finite zeros primary + NaN twin, validates both from disk, and
checks uniqueness against every registry raster found in the registry dirs.

Usage: build_submission.py <data_dir> <cache_dir> <method> [budget]
  method in {E1_supervised_hgb, E2_orientation_consensus, E3_strain_gated}
The method/budget must be the holdout winner — see evidence/holdout_experiments.json.
This script refuses to label the artifact PROMOTE unless the caller passes the
holdout evidence and it beats the best control (checked by scripts/make_run_card.py).
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from gems85 import emitter, fields, submission_writer as SW  # noqa: E402
from gems85.features import CHANNELS  # noqa: E402

SEED = 85


def read_bool(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> None:
    data = Path(sys.argv[1]); cache = Path(sys.argv[2])
    method = sys.argv[3]
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else 37654
    support_n = 150000
    t0 = time.time()
    stack = np.lib.format.open_memmap(cache / "feature_stack.npy", mode="r")
    with rasterio.open(data / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    labels = read_bool(data / "labels.tif") & foot

    ext = []
    for rel, nb in [("external/lidar_scarp_features_u8.tif", 12),
                    ("external/geodawn_rad_u8.tif", 4),
                    ("external/geodawn_extensions_u8.tif", 4)]:
        with rasterio.open(data / rel) as s:
            for i in range(1, nb + 1):
                ext.append(s.read(i))
    ext_arr = np.stack(ext, axis=-1)

    def sample_X(ys, xs):
        return np.concatenate([np.asarray(stack[ys, xs, :], dtype=np.float32),
                               ext_arr[ys, xs, :].astype(np.float32) / 255.0], axis=1)

    if method == "E1_supervised_hgb":
        rng = np.random.default_rng(SEED)
        pos_ys, pos_xs = np.nonzero(labels & foot)
        dist_labels = ndimage.distance_transform_edt(~labels)
        neg_pool = np.argwhere(foot & ~labels & (dist_labels > 1))
        neg_idx = rng.choice(len(neg_pool), size=min(3 * len(pos_ys), len(neg_pool)), replace=False)
        ys = np.concatenate([pos_ys, neg_pool[neg_idx, 0]])
        xs = np.concatenate([pos_xs, neg_pool[neg_idx, 1]])
        y = np.concatenate([np.ones(len(pos_ys), np.int8), np.zeros(len(neg_idx), np.int8)])
        clf = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08,
                                             max_leaf_nodes=63, min_samples_leaf=40,
                                             l2_regularization=1.0, random_state=SEED)
        clf.fit(sample_X(ys, xs), y)
        print(f"trained full model pos={len(pos_ys)} ({time.time()-t0:.0f}s)", flush=True)
        surf = np.zeros(labels.shape, np.float32)
        for r0 in range(0, labels.shape[0], 128):
            r1 = min(r0 + 128, labels.shape[0])
            by, bx = np.nonzero(foot[r0:r1])
            if len(by):
                surf[by + r0, bx] = clf.predict_proba(sample_X(by + r0, bx))[:, 1].astype(np.float32)
    elif method == "E2_orientation_consensus":
        surf = np.load(cache / "surf_h85b.npy")
    elif method == "E3_strain_gated":
        surf = np.load(cache / "surf_h85c.npy")
    else:
        raise SystemExit(f"unknown method {method}")
    np.save(cache / "final_surface.npy", surf)
    print(f"surface ready ({time.time()-t0:.0f}s)", flush=True)

    d_cat = ndimage.distance_transform_edt(~labels)
    allowed = foot & (d_cat > 2.0)
    sup = fields.top_n_support(surf, allowed, support_n)
    f2 = np.where(sup, surf, 0.0).astype(np.float32)
    mask, log = emitter.emit(f2, budget=budget, prior_dti=0.0)
    mask &= allowed
    print(f"emitted={int(mask.sum())} stopped={log.stopped_by} ({time.time()-t0:.0f}s)", flush=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    import hashlib
    digest8 = hashlib.sha256(np.packbits(mask)).hexdigest()[:8]
    slug = {"E1_supervised_hgb": "h85a-foldproper-hgb-maxcov",
            "E2_orientation_consensus": "h85b-orient-consensus-maxcov",
            "E3_strain_gated": "h85c-straingate-maxcov"}[method]
    zeros_name = f"gems85-{slug}-{budget}-{ts}-{digest8}-zeros.tif"
    out_dir = ROOT / "submissions"
    audit = SW.write_pair(mask, labels, data / "sample_submission.tif", out_dir, zeros_name)
    receipt = dict(method=method, budget=budget, support_n=support_n,
                   emitted=int(mask.sum()), zeros_name=zeros_name,
                   surface_sha256=hashlib.sha256(surf.tobytes()).hexdigest(),
                   audit=audit, seconds=time.time() - t0)
    (ROOT / "evidence" / "final_build.json").write_text(json.dumps(receipt, indent=2, default=str))
    print(json.dumps(receipt, indent=2, default=str))


if __name__ == "__main__":
    main()
