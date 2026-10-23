#!/usr/bin/env python3
"""Write ledger/submissions.csv (one row per BUILT variant) and ledger/history.csv.

The historical rows are collapsed on exact sha256 (repeat submissions of the same bytes
score identically) and every score is labelled with its evidence class.  Nothing here is a
DrivenData receipt: the family record is OWNER-REPORT == CLAIM.

Run:  python scripts/build_ledger.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "evidence" / "axis_concentration_build.json"
LEDGER = ROOT / "ledger"

PREDICTED = {
    10: ("-0.010 to -0.030 vs R0 0.2778 (CLAIM); concentration raises block-density CV "
         "0.551->0.767, the family's clustered pattern (h19-5 field CV 0.787, 0.1922 CLAIM)"),
    15: ("-0.015 to -0.040 vs R0 0.2778 (CLAIM); CV 0.551->0.786; holdout-PROXY truth credit "
         "falls with dose (TPw 129.3->117.9, n=22,663 withheld positives)"),
    20: ("-0.020 to -0.050 vs R0 0.2778 (CLAIM); CV 0.551->0.782; holdout-PROXY truth credit "
         "falls with dose (TPw 129.3->112.9, n=22,663 withheld positives)"),
}


def form_note(pct: int) -> str:
    note = (f"parent h33-2-b2 0.2778 CLAIM; {pct}% of dots moved from lowest- to highest-prior "
            f"0.8km blocks; pred live -0.01 to -0.03")
    assert len(note) <= 140, (len(note), note)
    return note


def main() -> int:
    build = json.loads(BUILD.read_text())
    LEDGER.mkdir(exist_ok=True)

    rows = []
    for v in build["variants"]:
        pct = v["value_pct"]
        rows.append({
            "id": v["id"],
            "parent": "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
            "parent_sha256": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
            "axis": "CONCENTRATION",
            "value": f"{pct}pct_of_dots_moved",
            "n_dots": v["n_dots"],
            "pct_dots_changed": round(v["pct_dots_changed"], 2),
            "sha256": v["sha256_nan"],
            "sha256_zeros_twin": v["sha256_zeros"],
            "file": v["files"]["nan_outside_spec"],
            "file_zeros_twin": v["files"]["zeros_outside_fallback"],
            "status": "BUILT",
            "predicted_change": PREDICTED[pct],
            "form_note": form_note(pct),
            "receipt_score": "",
            "receipt_date": "",
            "evidence_class": "MODEL (prediction; no receipt yet)",
        })
    with (LEDGER / "submissions.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # ---- family history (owner-reported == CLAIM unless a receipt exists)
    artifacts = json.loads((ROOT / "registry" / "scored_artifacts.json").read_text())["artifacts"]
    hist = []
    for a in artifacts:
        hist.append({
            "site": "GEMSDOE-family",
            "name": Path(a["file"]).name,
            "score": a["owner_reported_live_dti"],
            "encoding": "zeros-outside" if "zeros" in Path(a["file"]).name else "nan-outside",
            "n_dots": "",
            "sha8": a["sha256"][:8],
            "sha256": a["sha256"],
            "parent": "",
            "receipt": "N",
            "evidence_class": "CLAIM (owner-reported; no DrivenData receipt in this repo)",
            "label": a["label"],
        })
    # the three files this session built
    for v in build["variants"]:
        hist.append({
            "site": "GEMSDOE85 (this session)",
            "name": Path(v["files"]["nan_outside_spec"]).name,
            "score": "",
            "encoding": "nan-outside",
            "n_dots": v["n_dots"],
            "sha8": v["sha256_nan"][:8],
            "sha256": v["sha256_nan"],
            "parent": "h33-2-b2",
            "receipt": "N",
            "evidence_class": "MODEL (built, unscored)",
            "label": f"CONCENTRATION {v['value_pct']}%",
        })
    # collapse exact repeats on sha256
    seen, collapsed = set(), []
    for h in hist:
        if h["sha256"] in seen:
            continue
        seen.add(h["sha256"])
        collapsed.append(h)
    with (LEDGER / "history.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(collapsed[0]))
        w.writeheader()
        w.writerows(collapsed)

    print(f"ledger/submissions.csv: {len(rows)} rows")
    print(f"ledger/history.csv: {len(collapsed)} rows (collapsed on sha256)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
