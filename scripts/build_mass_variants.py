#!/usr/bin/env python3
"""Build this session's MASS variants of R0 and receipt every gate.

AXIS = MASS (chosen by the agent; every other axis already exists in ledger/submissions.csv).
Parent R0 = h33-h33-2-b2, 37,654 dots, rebuilt pixel-exactly (`evidence/r0_rebuild.json`).

    mass-m10e   remove 3,765 dots (10.0 %) -- smallest connected structure first
    mass-m10u   remove 3,765 dots (10.0 %) -- uniform at random, seed 20261023
    mass-p10    add    3,765 dots (10.0 %) -- largest structure first, sep relaxed 2.8 -> 2.2 px

Usage:
    python scripts/build_mass_variants.py            # build, gate, write releases/ + ledger/ + evidence/
    python scripts/build_mass_variants.py --check    # verify in memory, write nothing
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

import numpy as np  # noqa: E402

from gems85 import lineage as L  # noqa: E402
from gems85 import mass as M  # noqa: E402

RELEASES = ROOT / "releases"
LEDGER = ROOT / "ledger" / "submissions.csv"
EVIDENCE = ROOT / "evidence"
STAMP = "20261023"

#: Predictions are set from evidence/mass_holdout_proxy.json (filled in below by --check runs) and
#: revised, if needed, before the files are written.  Never a score: MODEL only.
#: Set from evidence/mass_holdout_proxy.json.  The proxy is the same fold-clean instrument as the
#: PRUNE session, plus a MASS calibration anchor (d1.5 60,069 dots 0.2477 -> d2.8 44,090 dots
#: 0.2600, both CLAIM, both catalogue-free so both symmetric under a hide-and-recover fold).
#: Proxy deltas are multiplied by that anchor's scale (3.07 proxy units per live unit) to reach a
#: live-ish number; the result is a MODEL built on a PROXY and is never called a score.
PREDICTED = {
    "mass-m10e": dict(central=-0.008, low=-0.013, high=-0.003,
                      basis="PROXY -0.00278 (0/5 folds) scaled x3.07; deleting structural speckle "
                            "still deletes crediting dots"),
    "mass-m10u": dict(central=-0.014, low=-0.020, high=-0.008,
                      basis="PROXY -0.00471 (0/5 folds) scaled x3.07; uniform deletion is worse "
                            "than the ranked deletion at the same mass, so the ranking has signal"),
    "mass-p10": dict(central=0.005, low=-0.004, high=0.013,
                     basis="PROXY +0.00158 (5/5 folds) scaled x3.07; the only positive direction, "
                           "but below the 0.01 evidence bar"),
}

LEDGER_COLUMNS = ["id", "site", "name", "score", "evidence_label", "encoding", "n_dots", "sha8",
                  "parent", "axis", "value", "pct_changed", "sha256", "status",
                  "predicted_change", "receipt", "receipt_score", "date"]


def build(name: str, r0: np.ndarray, field: np.ndarray, dist: np.ndarray) -> tuple[np.ndarray, dict]:
    if name == "mass-m10e":
        rank = M.rank_by_extent(r0, field)
        dots, chosen = M.drop_by_rank(r0, rank, M.DELTA)
        return dots, dict(selection="smallest bridged structural extent first",
                          mean_extent_px=float(M.bridged_extent(field).ravel()[chosen].mean()))
    if name == "mass-m10u":
        dots, chosen = M.drop_uniform(r0, M.DELTA)
        return dots, dict(selection="uniform random", seed=M.SEED,
                          mean_extent_px=float(M.bridged_extent(field).ravel()[chosen].mean()))
    if name == "mass-p10":
        dots, fact = M.add_by_extent(r0, field, dist, M.DELTA, min_cat_px=3.0)
        return dots, dict(selection="largest bridged structural extent first", **fact)
    raise KeyError(name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    fp, cat = L.load_template()
    dist = L.catalogue_distance(cat)
    d28 = L.read_dots(L.fetch_pinned("d28"))
    r0 = L.read_dots(L.fetch_pinned("r0"))
    field = L.read_dots(L.fetch_pinned("h19_5"))
    if not np.array_equal(L.prune(d28, dist, 2.0) & fp, r0):
        raise SystemExit("STOP: R0 did not rebuild pixel-exactly")

    rows, receipts = [], {}
    for name in PREDICTED:
        dots, fact = build(name, r0, field, dist)
        diff = L.diff_stats(r0, dots)
        pct = diff["pct_of_parent_dots_changed"]
        if not (1.0 <= pct <= 50.0):
            raise SystemExit(f"{name}: {pct}% changed outside the 1-50% window")
        if np.any(dots & cat):
            raise SystemExit(f"{name}: mass on the catalogue")
        if np.any(dots & ~fp):
            raise SystemExit(f"{name}: mass outside the footprint")
        # Brief §4.4 ("keep >= 3 px from the catalogue") is enforced on mass this variant ADDS.
        # R0 itself carries 2,171 dots at 2 < d <= 3 px; deleting those is PRUNE's experiment
        # (already built and predicted -0.002), and doing it here would silently turn all three
        # MASS arms into PRUNE variants.  Inherited dots are therefore kept and counted, and the
        # deviation is recorded as IR-V2-10 rather than hidden.
        added = dots & ~r0
        inherited_near = int(((dist > 2.0) & (dist <= 3.0) & dots).sum())
        new_inside_3px = int((dist[added] < 3.0).sum()) if added.any() else 0
        if new_inside_3px:
            raise SystemExit(f"{name}: {new_inside_3px} NEW dots inside 300 m of the catalogue")

        pred = PREDICTED[name]
        if args.check:
            print(f"[check] {name}: n={int(dots.sum())} changed={pct}% pred={pred['central']:+.3f}")
            continue

        stem = f"h33-2-b2-{name}-{STAMP}"
        tmp_nan = RELEASES / f".{stem}-nan.partial.tif"
        tmp_zeros = RELEASES / f".{stem}-zeros.partial.tif"
        L.write_nan(tmp_nan, dots, fp)
        L.write_zeros(tmp_zeros, dots)
        sha_nan, sha_zeros = L.sha256_file(tmp_nan), L.sha256_file(tmp_zeros)
        fin_nan = RELEASES / f"{stem}-{sha_nan[:8]}.tif"
        fin_zeros = RELEASES / f"{fin_nan.stem}-zeros.tif"
        tmp_nan.replace(fin_nan)
        tmp_zeros.replace(fin_zeros)

        # min_catalogue_px=0: the distance rule is enforced above on NEW mass only (IR-V2-10).
        rep_nan = L.gates(fin_nan, fp, cat, mode="nan", dist=dist, min_catalogue_px=0.0)
        rep_zeros = L.gates(fin_zeros, fp, cat, mode="zeros", dist=dist, min_catalogue_px=0.0)
        on_disk_ok = (np.array_equal(L.read_dots(fin_nan), dots)
                      and np.array_equal(L.read_dots(fin_zeros), dots))
        if not (rep_nan["ok"] and rep_zeros["ok"] and on_disk_ok):
            raise SystemExit(f"{name}: gate failure {rep_nan['problems']} {rep_zeros['problems']}")

        rec = dict(id=fin_nan.stem, parent="h33-h33-2-b2", axis="MASS",
                   value=name.replace("mass-", ""), n_dots=int(dots.sum()), diff=diff,
                   pct_of_parent_dots_changed=pct, detail=fact,
                   files=dict(nan=str(fin_nan.relative_to(ROOT)),
                              zeros=str(fin_zeros.relative_to(ROOT)),
                              sha256_nan=sha_nan, sha256_zeros=sha_zeros),
                   gates=dict(nan=rep_nan, zeros=rep_zeros, pixels_equal_intended=on_disk_ok),
                   predicted_change_vs_r0=pred["central"], predicted_range=[pred["low"], pred["high"]],
                   prediction_basis=pred["basis"])
        receipts[name] = rec
        rows.append(dict(id=rec["id"], site="GEMSDOE85", name=fin_nan.name, score="",
                         evidence_label="MODEL (prediction; no score)",
                         encoding="nan-outside primary; zeros twin", n_dots=rec["n_dots"],
                         sha8=sha_nan[:8], parent="h33-h33-2-b2", axis="MASS", value=rec["value"],
                         pct_changed=pct, sha256=sha_nan, status="BUILT",
                         predicted_change=(f"{pred['central']:+.3f} "
                                           f"({pred['low']:+.3f} to {pred['high']:+.3f}) MODEL"),
                         receipt="N",
                         receipt_score="", date=""))
        print(f"[BUILT] {rec['id']}  n={rec['n_dots']}  changed={pct}%  pred={pred['central']:+.3f}")

    if args.check:
        return 0

    old = list(csv.DictReader(io.StringIO(LEDGER.read_text())))
    # Idempotent rebuild: this script owns the rows it emits.  Re-running replaces them rather
    # than aborting on its own hashes, so a corrected prediction can actually reach the ledger.
    mine = {r["id"] for r in rows}
    replaced = [r for r in old if r["id"] in mine]
    old = [r for r in old if r["id"] not in mine]
    if replaced:
        print(f"replacing {len(replaced)} existing row(s) owned by this script")
    seen = {r["sha256"] for r in old}
    for r in rows:
        if r["sha256"] in seen:
            raise SystemExit(f"duplicate sha256 already in ledger: {r['sha256']}")
        seen.add(r["sha256"])
    with LEDGER.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LEDGER_COLUMNS)
        w.writeheader()
        for r in old + rows:
            w.writerow({k: r.get(k, "") for k in LEDGER_COLUMNS})

    L.write_json(EVIDENCE / "mass_session.json", dict(
        schema_version=1, axis="MASS", chosen_by="agent (no other axis remained unbuilt)",
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        parent=dict(id="h33-h33-2-b2", n_dots=int(r0.sum()), sha256=L.PINNED["r0"]["sha256"],
                    rebuild="pixel-identical (evidence/r0_rebuild.json)"),
        delta_dots=M.DELTA, seed=M.SEED, variants=receipts,
        ranking=dict(rule="bridged (r=1) connected-component size of the H19-5 field",
                     why="parent stores no scores; its literal rank is raster scan order (IR-V2-08)",
                     r0_median_extent_px=97, r0_pct_on_structures_under_30px=28.3),
        refusals=dict(uniqueness="not applied; brief §6 forbids overlap/rank thresholds")))
    print(f"ledger -> {LEDGER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
