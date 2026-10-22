#!/usr/bin/env python3
"""Build the session arena/22847afd candidate GeoTIFF(s) from the winning RULE.

The rule is re-executed on the FULL catalogue (the holdout folds were only the
instrument).  Which rule is determined by evidence, passed as --field:
  e2b        : 30-channel contextual HGB trained on the full catalogue
  fusion5050 : rank-average( E2b-full , GEO-Pb crest )

Outputs (docs/downloads/): primary zeros TIF + nan twin + zip per ladder rung,
each re-validated from its written bytes (src/gems85/submission.py, 17 checks).
Duplicate check vs the 17 registry rasters runs BEFORE copying anything
(scripts/build_submission.py::duplicate_check, incl. IR-85-002 chance lift).
Writes registry/submission_session.json + evidence/duplicate_check_session.json
(evidence/run_card_session_22847afd.json is written by scripts/make_session_run_card.py).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems85 import emission, featurestack, grid, submission  # noqa: E402
from build_submission import duplicate_check  # noqa: E402
from run_e2b import train_predict  # noqa: E402
from run_session_experiments import build_context_channels, rank01  # noqa: E402

DOWNLOADS = ROOT / "docs" / "downloads"
STAMP = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
EXCLUDE_PX = 2
# Every rung is a configuration actually measured for the fusion rule in
# evidence/session_22847afd_e2b.json: 37,654@sep4 = 0.08082, 60,000@sep2.8 = 0.09222,
# 37,654@sep2.8 = 0.07411 (HOLDOUT-DTI, gems85-holdout-v1.0.0).
LADDER = [("primary", 37_654, 4.0), ("alt-60k", 60_000, 2.8), ("alt-28sep", 37_654, 2.8)]


def digest8(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:8]


def build_field(kind: str, fp, cat) -> np.ndarray:
    cache_f = ROOT / "work" / f"final_field_{kind}.npy"
    if cache_f.exists():
        return np.load(cache_f)
    chan_names = featurestack.build(fp) + build_context_channels(fp)
    handles = featurestack.open_stack(chan_names)
    rng = np.random.default_rng(20261022)
    print(f"training full-catalogue HGB ({len(chan_names)} ch) ...", flush=True)
    hgb = train_predict(handles, fp, cat, grid.WIDTH, rng)
    if kind == "e2b":
        field = hgb
    elif kind == "fusion5050":
        crest = np.load(featurestack.CACHE / "ch_geopb_crest.npy")
        field = (0.5 * rank01(hgb, fp) + 0.5 * rank01(crest, fp)).astype(np.float32)
    else:
        raise ValueError(kind)
    np.save(cache_f, field)
    return field


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--field", required=True, choices=["e2b", "fusion5050"])
    ap.add_argument("--label", required=True, help="short slug, e.g. ctxhgb30")
    args = ap.parse_args()

    fp = grid.footprint()
    cat = grid.catalogue()
    field = build_field(args.field, fp, cat)

    artifacts = []
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    for role, n, sep in LADDER:
        dots = emission.emit(field, footprint=fp, visible_catalogue=cat,
                             n=n, sep_px=sep, exclude_px=EXCLUDE_PX)
        placed = int(dots.sum())
        if role == "primary":
            dup = duplicate_check(dots.astype(bool), field, fp)
            (ROOT / "evidence" / "duplicate_check_session.json").write_text(
                json.dumps(dup, indent=2, default=float) + "\n")
            print(f"duplicate check: max|rho|={dup['max_abs_spearman']:.3f} "
                  f"maxOverlap={100*dup['max_dot_overlap_3px']:.1f}% "
                  f"maxLift={dup['max_overlap_lift_over_chance']:.2f} "
                  f"is_duplicate={dup['is_duplicate']}", flush=True)
            if dup["is_duplicate"]:
                raise SystemExit("ABORT: candidate is a duplicate of a registry raster")
        d8 = digest8(dots)
        base = f"gems85-s85-{args.label}-{placed}dots-sep{sep:g}-{STAMP}-{d8}"
        rep = submission.write_submission(dots, DOWNLOADS / f"{base}-zeros.tif",
                                          mode="zeros", catalogue_buffer_px=EXCLUDE_PX)
        rep_nan = submission.write_submission(dots, DOWNLOADS / f"{base}-nan.tif",
                                              mode="nan", catalogue_buffer_px=EXCLUDE_PX)
        zp = DOWNLOADS / f"{base}-zeros.zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(DOWNLOADS / f"{base}-zeros.tif", f"{base}-zeros.tif")
        artifacts.append({"role": role, "n_requested": n, "sep_px": sep,
                          "placed": placed,
                          "zeros": rep.as_dict(), "nan": rep_nan.as_dict(),
                          "zip": {"filename": zp.name, "bytes": zp.stat().st_size}})
        print(f"{role}: {placed} dots -> {base}-zeros.tif  sha256={rep.sha256[:16]} "
              f"passed={rep.passed}", flush=True)

    pri = artifacts[0]
    out = {
        "built_utc": STAMP, "field_kind": args.field, "label": args.label,
        "primary": {"filename": Path(pri["zeros"]["path"]).name,
                    "sha256": pri["zeros"]["sha256"], "bytes": pri["zeros"]["bytes"],
                    "checks": pri["zeros"]["checks"], "stats": pri["zeros"]["stats"]},
        "alternates": [
            {"role": "NaN-outside twin (alternate format)",
             "filename": Path(pri["nan"]["path"]).name, "bytes": pri["nan"]["bytes"]},
            {"role": "zipped primary", "filename": pri["zip"]["filename"],
             "bytes": pri["zip"]["bytes"]},
        ] + [{"role": f"{a['role']} ({a['placed']:,} dots, sep {a['sep_px']:g}px)",
              "filename": Path(a["zeros"]["path"]).name, "bytes": a["zeros"]["bytes"]}
             for a in artifacts[1:]],
        "ladder": artifacts,
    }
    (ROOT / "registry" / "submission_session.json").write_text(
        json.dumps(out, indent=2, default=float) + "\n")
    print("-> registry/submission_session.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
