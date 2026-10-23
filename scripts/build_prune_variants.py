#!/usr/bin/env python3
"""Build this session's PRUNE variants of R0 and receipt every gate.

AXIS = PRUNE (operator-assigned).  Three variants, each differing from R0 **only** by which
dots survive a Euclidean distance-to-catalogue threshold (plus, for one variant, the PRUNE
protocol's own refill):

    h33-2-b2-prune3    keep d > 3.0 px, no refill             (~35.5 k dots)
    h33-2-b2-prune3r   keep d > 3.0 px, refill to R0's count  (37,654 dots)
    h33-2-b2-prune4    keep d > 4.0 px, no refill             (~33.8 k dots)

Every pixel is on the same H19-5 field as R0.  Nothing is re-ranked, re-fitted, or moved.

Usage:
    python scripts/build_prune_variants.py            # build everything, write releases/ + ledger
    python scripts/build_prune_variants.py --check    # re-verify from disk only, no writes
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

import numpy as np  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from gems85 import lineage as L  # noqa: E402

RELEASES = ROOT / "releases"
LEDGER = ROOT / "ledger"
EVIDENCE = ROOT / "evidence"
STAMP = "20261023"

#: Predictions are set from the fold-clean PROXY (evidence/prune_holdout_proxy.json), which was
#: first validated against the two scored rungs: it reproduces their direction (0->1 +0.00207,
#: 0->2 +0.00214, 5/5 folds) while compressing magnitude ~5-8x.  It then turns over at 3 px.
#: The naive per-dot extrapolation below is kept only to show what it would have predicted and
#: why it is not used.  See the mechanism cards.
PREDICTED = {
    "prune3": dict(central=-0.002, low=-0.010, high=0.004,
                   basis="PROXY sign test, 0/5 folds at cutoff 3 (-0.0017 proxy units); magnitude uncalibrated"),
    "prune3r": dict(central=-0.003, low=-0.011, high=0.003,
                    basis="PROXY sign test at cutoff 3 plus 440 refill dots taken from the least valuable remaining cells"),
    "prune4": dict(central=-0.006, low=-0.013, high=0.001,
                   basis="PROXY sign test, 0/5 folds at cutoff 4 (-0.0060 proxy units)"),
}

#: Rate measured on the two *scored* rungs of this lineage: the 44,090-dot file (owner-claimed
#: 0.2600) and the 40,199-dot file (0.2708) differ by 3,891 dots exactly, and the 40,199-dot
#: file and R0 differ by 2,545 dots exactly (both verified pixel-identical in
#: evidence/r0_rebuild.json).  Gain per removed dot: 0.0108/3891 = 2.78e-6 and
#: 0.0070/2545 = 2.75e-6.  See mechanism card for why this is a MODEL, not a law.
RATE_PER_DOT = 2.765e-6

NOTES = {
    "prune3": "PRUNE closed at 2px: fold-clean proxy 0/5 folds at 3px. Slot 1 candidate (information).",
    "prune3r": "mass-control; refill saturated (440 of 2171). Do not spend a slot unless prune3 > 0.2840.",
    "prune4": "extrapolation probe past kernel R=300m; 0/5 folds in proxy. Control only.",
}

VARIANTS = {
    "prune3": dict(cutoff=3.0, refill=0, value="3.0-no-refill",
                   hypothesis="flank mass 2-3 px from a mapped trace pays alpha with no credit"),
    "prune3r": dict(cutoff=3.0, refill="match", value="3.0-refill-to-37654",
                    hypothesis="is the ladder's gain about distance or about count?"),
    "prune4": dict(cutoff=4.0, refill=0, value="4.0-no-refill",
                   hypothesis="does the ladder stop at the metric's own support radius R=3 px?"),
}


def log(msg: str) -> None:
    print(msg, flush=True)


def build_variant(name: str, spec: dict, d28: np.ndarray, dist: np.ndarray,
                  fp: np.ndarray, r0: np.ndarray) -> tuple[np.ndarray, dict]:
    """Return the dot mask plus the recipe facts that produced it."""
    kept = L.prune(d28, dist, spec["cutoff"]) & fp
    removed = int(r0.sum() - (r0 & kept).sum())
    added_mask = np.zeros_like(kept)
    refill_detail = None
    if spec["refill"] == "match":
        n_add = int(r0.sum() - kept.sum())
        if n_add > 0:
            # Refill rule: put the new dots where they newly credit the most *uncovered* H19-5
            # support, at d > cutoff, with the parent's own 2.8 px minimum separation.
            field = L.read_dots(L.PINNED["h19_5"]["dest"]).astype(bool)
            covered = ndi.binary_dilation(kept, ndi.generate_binary_structure(2, 1), iterations=3)
            uncovered = field & ~covered
            disc = np.zeros((7, 7), np.float64)
            y, x = np.mgrid[-3:4, -3:4]
            disc[(y * y + x * x) <= 9] = 1.0
            score = ndi.convolve(uncovered.astype(np.float64), disc, mode="constant") * field
            allowed = field & (dist > spec["cutoff"]) & ~covered
            from gems85.emission import poisson_thin
            added_mask = poisson_thin(score.astype(np.float32), n=n_add, sep_px=2.8, allowed=allowed)
            refill_detail = dict(n_requested=n_add, n_added=int(added_mask.sum()),
                                 rule="max newly-credited uncovered support, sep 2.8 px, d > cutoff")
        kept = kept | added_mask
    return kept, dict(n_removed_from_parent=removed, refill_detail=refill_detail,
                      n_added_beyond_parent=int((added_mask & ~r0).sum()))


def serialise(name: str, dots: np.ndarray, fp: np.ndarray) -> dict:
    """Write the NaN-outside primary and the all-finite zeros fallback, then name by hash."""
    RELEASES.mkdir(parents=True, exist_ok=True)
    stem = f"h33-2-b2-{name}-{STAMP}"
    tmp_nan = RELEASES / f".{stem}-nan.partial.tif"
    tmp_zeros = RELEASES / f".{stem}-zeros.partial.tif"
    L.write_nan(tmp_nan, dots, fp)
    L.write_zeros(tmp_zeros, dots)
    sha_nan, sha_zeros = L.sha256_file(tmp_nan), L.sha256_file(tmp_zeros)
    # One id per variant: <parent>-<axis><value>-<yyyymmdd>-<sha8 of the primary (NaN) file>.
    fin_nan = RELEASES / f"{stem}-{sha_nan[:8]}.tif"
    fin_zeros = RELEASES / f"{fin_nan.stem}-zeros.tif"
    tmp_nan.replace(fin_nan)
    tmp_zeros.replace(fin_zeros)
    return dict(nan_path=fin_nan, zeros_path=fin_zeros,
                sha256=sha_nan, sha256_zeros=sha_zeros,
                bytes=fin_nan.stat().st_size, bytes_zeros=fin_zeros.stat().st_size)


def verify_from_disk(path: Path, fp: np.ndarray, cat: np.ndarray, dist: np.ndarray,
                     dots: np.ndarray, mode: str) -> dict:
    """Re-read the file from disk and prove it still carries the intended pixel set."""
    rep = L.gates(path, fp, cat, mode=mode, dist=dist)
    from gems85 import lineage as L2
    on_disk = L2.read_dots(path)
    rep["pixels_equal_intended"] = bool(np.array_equal(on_disk, dots))
    rep["n_dots_on_disk"] = int(on_disk.sum())
    if not rep["pixels_equal_intended"]:
        rep["problems"].append("on-disk pixels differ from the intended dot set")
        rep["ok"] = False
    return rep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify existing releases, write nothing")
    args = ap.parse_args()

    fp, cat = L.load_template()
    dist = L.catalogue_distance(cat)
    d28 = L.read_dots(L.fetch_pinned("d28"))
    r0 = L.read_dots(L.fetch_pinned("r0"))
    rebuilt = L.prune(d28, dist, 2.0) & fp
    if not np.array_equal(rebuilt, r0):
        raise SystemExit("STOP: R0 could not be rebuilt pixel-exactly; not building children")

    rows, receipts, built = [], {}, {}
    for name, spec in VARIANTS.items():
        dots, fact = build_variant(name, spec, d28, dist, fp, r0)
        diff = L.diff_stats(r0, dots)
        pct = diff["pct_of_parent_dots_changed"]
        if pct is not None and not (1.0 <= pct <= 50.0):
            raise SystemExit(f"{name}: {pct}% of parent dots changed is outside the 1-50% window")
        if np.any(dots & cat):
            raise SystemExit(f"{name}: mass on the catalogue")
        if np.any(dots & ~fp):
            raise SystemExit(f"{name}: mass outside the footprint")
        naive = round(RATE_PER_DOT * (diff["n_removed"] - diff["n_added"]), 4)
        pred = PREDICTED[name]
        built[name] = dots
        if args.check:
            continue
        files = serialise(name, dots, fp)
        nan_report = verify_from_disk(files["nan_path"], fp, cat, dist, dots, "nan")
        zeros_report = verify_from_disk(files["zeros_path"], fp, cat, dist, dots, "zeros")
        if not (nan_report["ok"] and zeros_report["ok"]):
            raise SystemExit(f"{name}: gate failure {nan_report['problems']} {zeros_report['problems']}")
        dmin = float(dist[dots].min())
        rec = dict(
            id=files["nan_path"].stem,
            parent="h33-h33-2-b2 (GEMSDOE32, 37,654 dots)",
            axis="PRUNE", value=spec["value"], cutoff_px=spec["cutoff"], refill=spec["refill"],
            hypothesis=spec["hypothesis"],
            n_dots=int(dots.sum()), pct_of_parent_dots_changed=pct, diff=diff,
            min_distance_to_catalogue_px=round(dmin, 4),
            **fact,
            files=dict(nan=str(files["nan_path"].relative_to(ROOT)),
                       zeros=str(files["zeros_path"].relative_to(ROOT)),
                       sha256_nan=files["sha256"], sha256_zeros=files["sha256_zeros"],
                       bytes_nan=files["bytes"], bytes_zeros=files["bytes_zeros"]),
            gates=dict(nan=nan_report, zeros=zeros_report),
            predicted_change_vs_r0=pred["central"],
            predicted_range=[pred["low"], pred["high"]],
            prediction_basis=pred["basis"],
            naive_per_dot_model_change=naive,
            naive_model_note=("MODEL (not used): 2.765e-6 per removed dot extrapolated from the two "
                              "scored rungs. The fold-clean PROXY, which reproduces those two steps, "
                              "turns over at 3 px and contradicts this extrapolation."),
        )
        receipts[name] = rec
        rows.append(dict(
            id=rec["id"], parent=rec["parent"], axis="PRUNE", value=spec["value"],
            n_dots=rec["n_dots"], pct_changed=pct,
            sha256=files["sha256"], status="BUILT",
            predicted_change=pred["central"],
            receipt_score="", receipt_date="", notes=NOTES[name]),
        )
        log(f"[BUILT] {rec['id']}  n={rec['n_dots']}  changed={pct}%  min_d={dmin:.3f}px  "
            f"pred={pred['central']:+.4f} [{pred['low']:+.3f},{pred['high']:+.3f}]  "
            f"naive={naive:+.4f}  sha={files['sha256'][:8]}")

    if args.check:
        log("--check: verified buildability and gates in memory; nothing written")
        return 0

    LEDGER.mkdir(parents=True, exist_ok=True)
    ledger_path = LEDGER / "submissions.csv"
    fieldnames = ["id", "parent", "axis", "value", "n_dots", "pct_changed", "sha256",
                  "status", "predicted_change", "receipt_score", "receipt_date", "notes"]
    existing = []
    if ledger_path.is_file():
        with ledger_path.open(newline="") as fh:
            existing = [r for r in csv.DictReader(fh) if r["status"] != "BUILT" or r["receipt_score"]]
    seen = {r["sha256"] for r in existing}
    for r in rows:
        if r["sha256"] in seen:
            raise SystemExit(f"duplicate sha256 in ledger: {r['sha256']}")
    with ledger_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in existing + rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    session = dict(
        schema_version=1, axis="PRUNE", assigned_by="operator", generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        parent=dict(id="h33-h33-2-b2", n_dots=int(r0.sum()),
                    sha256=L.PINNED["r0"]["sha256"],
                    rebuild="pixel-identical from d2.8 at Euclidean cutoff 2 (evidence/r0_rebuild.json)"),
        rate_per_removed_dot=RATE_PER_DOT,
        variants=receipts,
        refusals=dict(
            uniqueness_gate="not applied: the brief forbids rank-correlation and dot-overlap thresholds (§6)",
            holdout_proxy="reported separately in evidence/prune_holdout_proxy.json; never a gate",
        ),
    )
    L.write_json(EVIDENCE / "prune_session.json", session)
    log(f"ledger  -> {ledger_path.relative_to(ROOT)}")
    log(f"receipt -> {(EVIDENCE / 'prune_session.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
