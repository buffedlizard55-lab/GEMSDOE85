# SUBMIT — what to upload, and the receipt for each file

One file per slot. The human uploads from their own registered account; nothing here submits,
logs in, or touches the leaderboard. A slot is a scored submission; the twin you do **not**
upload is the fallback.

## 1. `h33-2-b2-prune3-20261023-c493fdeb`  ← PRUNE 3.0 px, 35,483 dots, no refill

| Field | Value |
|---|---|
| Upload | `releases/h33-2-b2-prune3-20261023-c493fdeb.tif` (NaN outside the footprint, 210 KB) |
| Fallback twin | `releases/h33-2-b2-prune3-20261023-c493fdeb-zeros.tif` (all-finite, 0 outside, 140 KB) |
| Name (≤140) | `GEMSDOE85 PRUNE3 h33-2-b2 cutoff 300m 35483 dots 0 on-cat UNSCORED` |
| Note (≤140) | `parent h33-2-b2 37654 dots; delete dots within 300 m of mapped traces (PRUNE 3px, no refill); predicted -0.002; ledger row prune3` |
| Format | CRS EPSG:32611, 3730×3292, float32, 1 band, transform (100,0,243350,0,-100,4508550), values ∈ {0,1} inside the footprint, NaN (twin: 0) outside, **0** dots on the catalogue |
| SHA-256 | `c493fdeb4505deb888b9f09c2dc5b2dfe7a16bf58873186d418025d113db0e78` (NaN file) |
| Twin SHA-256 | `8341c546…` |
| Gates | `evidence/prune_session.json` → `variants.prune3.gates` (re-read from disk after writing) |

## 2. `h33-2-b2-prune3r-20261023-b633c5e9` — PRUNE 3.0 px + refill (control, 35,923 dots)

| Field | Value |
|---|---|
| Upload | `releases/h33-2-b2-prune3r-20261023-b633c5e9.tif` |
| Fallback twin | `releases/h33-2-b2-prune3r-20261023-b633c5e9-zeros.tif` |
| Name | `GEMSDOE85 PRUNE3R h33-2-b2 cutoff 300m refill 35923 dots UNSCORED` |
| Note | `parent h33-2-b2; PRUNE 3px + max refill (field saturated: 440 of 2171 fit); predicted -0.003; mass-control for prune3` |
| SHA-256 | `b633c5e9af03dc7dd763f6c3db04a4e7c133df7254a23b9720f4311276644809` |

## 3. `h33-2-b2-prune4-20261023-37fe5e5e` — PRUNE 4.0 px (control, 33,829 dots)

| Field | Value |
|---|---|
| Upload | `releases/h33-2-b2-prune4-20261023-37fe5e5e.tif` |
| Fallback twin | `releases/h33-2-b2-prune4-20261023-37fe5e5e-zeros.tif` |
| Name | `GEMSDOE85 PRUNE4 h33-2-b2 cutoff 400m 33829 dots UNSCORED` |
| Note | `parent h33-2-b2; delete dots within 400 m of mapped traces (past kernel R=300 m); predicted -0.006; extrapolation probe` |
| SHA-256 | `37fe5e5e39c01a22bd7a902858ef8920e6d03410ca1459149b3def6a29f1b6e9` |

## Which one, and what to do with the receipt

`SLOT_PLAN.md` says slot 1 is file 1 (it is the only one whose result moves a decision). Files 2
and 3 are controls: skip them unless file 1 scores ≥ 0.2840.

After the submission page returns a score, copy the score **and its date** into
`ledger/submissions.csv` on the matching row (`receipt_score`, `receipt_date`) and change
`status` from `BUILT` to `RECEIPT`. Until that happens the row is a prediction, not a result.

**Never** upload `evidence/r0_rebuild.json`'s re-serialised raster: it has R0's pixels but a new
hash, so it would spend a slot to learn nothing (IR-V2-01).

## Format note the operator should know

The competition page permits NaN outside the footprint and the sample submission uses it; the
repository's own `vendor/gems57/gates.py` enforces a **stricter all-finite** policy and therefore
reports the NaN twin as failing ("fail our all-finite export policy"). That is a repository policy,
not a portal rule (IR-V2-02). The all-finite twin passes both. If a portal range error ever
appears on the NaN twin, switch to the zeros twin — they carry identical predictions.
