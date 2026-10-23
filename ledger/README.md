# ledger/

`submissions.csv` is the score ledger. It is **generated**, not hand-edited:

```bash
python scripts/build_ledger.py     # reads registry/scored_artifacts.json + evidence/session_snap.json
```

Columns: `id, parent, axis, value, n_dots, pct_changed, sha256, status, predicted_change,
receipt_score, receipt_date, evidence_class, source`.

## Provenance, stated plainly

* There is **no `raw_paste.txt`** in this repository and **no submission-page receipt anywhere
  in it**. `registry/scored_artifacts.json` says so itself: "No DrivenData receipt is reproduced
  in this repository."
* Every historical score is therefore `SCORED-CLAIM` with `evidence_class = CLAIM
  (owner-reported; no receipt in repo)`. The human confirmed on 2026-10-23 that no receipts are
  available. Nothing in this ledger is a RECEIPT.
* The climb recorded by the owner: 0.1922 (h19-5 continuous field, 121,131 px) → 0.2477
  (thinned to dots d1.5, 60,069 px) → 0.2600 (d28 poisson 300 m off-catalogue) → 0.2708
  (solo d28) → **0.2778 (h33-2-b2, parent R0)**.
* `predicted_change` is what was pre-registered before the run, not an estimate revised after it.
  The mechanism model's own range is in `evidence/snap_mechanism_model.json` and is discussed in
  `SLOT_PLAN.md`.
* The human fills `receipt_score` and `receipt_date` from the submission page. Until then a
  BUILT row has **no score of any kind**.
