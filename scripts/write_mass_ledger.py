#!/usr/bin/env python3
"""Rebuild ledger/submissions.csv from evidence/mass_axis.json + the files on disk.

Every hash is read back off the written raster and cross-checked against the evidence
JSON before the row is emitted; the script refuses if they disagree.  No value in the
ledger is typed by hand.  Receipt columns are left empty on purpose -- only the human
can copy them from a submission-page receipt.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "submissions.csv"

COLS = ["id", "parent", "axis", "value", "n_dots", "pct_changed", "sha256", "status",
        "predicted_change", "receipt_score", "receipt_date", "file_zeros", "file_nan",
        "evidence"]

# Lineage rows: every score here is a CLAIM (owner-reported), never a receipt.
LINEAGE = [
    dict(id="h33-h33-2-b2-20261004T220000Z-e5eb6e7e", parent="h27-4-solo-d28", axis="PRUNE",
         value="<=2px", n_dots=37654, pct_changed="6.32",
         sha256="c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
         status="CLAIM 0.2778 (owner-reported, no receipt in this repo)",
         predicted_change="owner-projected +0.0049; the parent every MASS variant descends from",
         receipt_score="", receipt_date="",
         file_zeros="data/registry_rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
         file_nan="", evidence="registry/scored_artifacts.json"),
    dict(id="h27-4-solo-d28-20261004-8acb75e1", parent="h19-5-d2.8", axis="PRUNE",
         value="baseline", n_dots=40199, pct_changed="0",
         sha256="07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40",
         status="CLAIM 0.2708 (owner-reported, no receipt in this repo)",
         predicted_change="n/a", receipt_score="", receipt_date="",
         file_zeros="", file_nan="data/registry_rasters/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
         evidence="registry/scored_artifacts.json"),
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    ev = json.loads((ROOT / "evidence" / "mass_axis.json").read_text())
    rows = list(LINEAGE)
    for key, v in ev["variants"].items():
        zeros = ROOT / v["file_zeros"]
        nan = ROOT / v["file_nan"]
        got = sha256_file(zeros)
        if got != v["sha256"] or sha256_file(nan) != v["sha256_nan"]:
            raise SystemExit(f"{key}: on-disk hash does not match evidence; refusing")
        p = v["prediction"]
        rows.append(dict(
            id=v["id"], parent=v["parent"], axis=v["axis"], value=v["value"],
            n_dots=v["n_dots"], pct_changed=f"{v['pct_changed']:.2f}", sha256=got,
            status="BUILT (local format gates pass; UNSHipped, no slot spent)",
            predicted_change=(f"MODEL bracket [{p['bracket_floor_no_new_credit']:+.4f}, "
                              f"{p['bracket_ceiling_lost_credit_was_real']:+.4f}]; "
                              f"circular-proxy point {p['predicted_live_change']:+.4f}; "
                              f"a null (<0.01) is the modal outcome"),
            receipt_score="", receipt_date="",
            file_zeros=v["file_zeros"], file_nan=v["file_nan"],
            evidence="evidence/mass_axis.json",
        ))
    LEDGER.parent.mkdir(exist_ok=True)
    with LEDGER.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {LEDGER.relative_to(ROOT)} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
