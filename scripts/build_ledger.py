#!/usr/bin/env python3
"""Build ledger/submissions.csv from pinned artefacts + this session's evidence.

There is no ``ledger/raw_paste.txt`` in this repository and no submission-page receipt
anywhere in it, so every historical score is written as **CLAIM** (owner-reported).  Nothing
here invents a receipt.  Columns are the brief's, plus ``evidence_class`` and ``source``.

Usage:  python scripts/build_ledger.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "submissions.csv"
FIELDS = ["id", "parent", "axis", "value", "n_dots", "pct_changed", "sha256", "status",
          "predicted_change", "receipt_score", "receipt_date", "evidence_class", "source"]


def sha8(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:8]


def n_positive(p: Path) -> int | None:
    try:
        with rasterio.open(p) as src:
            return int((src.read(1) > 0).sum())
    except Exception:  # noqa: BLE001
        return None


def find_restored(sha: str) -> Path | None:
    """Locate a restored artefact by full sha256 (manifest destinations move between groups)."""
    if not sha:
        return None
    for base in ("data/scored", "data/registry_rasters", "docs/downloads"):
        d = ROOT / base
        if not d.is_dir():
            continue
        for p in d.glob("*.tif"):
            if hashlib.sha256(p.read_bytes()).hexdigest() == sha:
                return p
    return None


def main() -> int:
    rows: list[dict] = []
    hist = json.loads((ROOT / "registry/scored_artifacts.json").read_text())

    # The climb, oldest first, as recorded by the owner (all CLAIM, no receipt in repo).
    climb = [
        ("gems19-h19-5", "h19-5 continuous field", 0.1922),
        ("gems24-h25-1-d1-5", "h19-5 thinned to dots d1.5", 0.2477),
        ("gems30-d28-poisson", "d28 poisson 300 m off-catalogue", 0.2600),
        ("gems31-h27-4", "solo d28", 0.2708),
        ("gemsdoe32-h33-h33-2-b2", "prune <=2 px of catalogue (PARENT R0)", 0.2778),
    ]
    for aid, label, score in climb:
        art = next((a for a in hist["artifacts"]
                    if a["owner_reported_live_dti"] == score and aid.split("-")[0] in a["file"]), None)
        path = find_restored(art["sha256"]) if art else None
        rows.append(dict(
            id=aid, parent="", axis="n/a", value="ancestor", n_dots=n_positive(path) if path else "",
            pct_changed="", sha256=art["sha256"] if art else "", status="SCORED-CLAIM",
            predicted_change="", receipt_score=score, receipt_date="",
            evidence_class="CLAIM (owner-reported; no receipt in repo)",
            source=f"registry/scored_artifacts.json :: {label}"))

    session = json.loads((ROOT / "evidence/session_snap.json").read_text())
    for v in session["variants"]:
        st, p = v["stats"], v["predicted"]
        rows.append(dict(
            id=v["id"], parent="h33-h33-2-b2", axis="SNAP",
            value=f"d2 tau={v['tau']}" + (" (CONTROL: exclusion only)" if v["tau"] is None else ""),
            n_dots=st["n_dots"], pct_changed=st["pct_moved"],
            sha256=v["zeros"]["sha256"], status="BUILT",
            predicted_change=f"{p['low']:+.3f} .. {p['high']:+.3f}",
            receipt_score="", receipt_date="", evidence_class="MODEL (prediction; no live score)",
            source="evidence/session_snap.json + " + v["zeros"]["path"]))

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {LEDGER.relative_to(ROOT)} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
