# SUBMIT — session 3, 2026-10-23 (supersedes the previous session's SUBMIT page)

Upload **one file per slot** from your own registered account. Nothing in this repository logs in,
scrapes or submits. All three files below are built from the SHA-256-verified parent R0
(`h33-h33-2-b2`, `e5eb6e7e`), pass every gate, and are **unscored** — every number is MODEL until you
paste a receipt.

`TOP_PUBLIC` and the remaining rolling-week slot count are read by the human off the leaderboard and
the account page, then written into `README.md` (CURRENT STATE block). If fewer than three slots are
left, take them in the order below.

## Slot 1 — the anchor rung

- **File:** `releases/h33-2-b2-prune3-20261023-fb308615.tif`
  (fallback if the portal rejects NaN outside the footprint: `…-fb308615-zeros.tif`, identical pixels)
- **sha256:** `fb308615161ad8f62b063d90972a4c36e7c66e7c58beb3316c81497cfe65261e` · 35,483 dots
- **Note (115/140):** `R0 h33-2-b2 PRUNE rung3: drop 2<d_cat<=3px flank dots, 37654->35483 (5.77%), no refill; pred +0.007 MODEL; UNSCORED`
- **Format receipt:** `evidence/session_prune_receipt.json → variants["h33-2-b2-prune3"]` — EPSG:32611 ·
  3730×3292 · 1 band · float32 · transform `100,0,243350,0,-100,4508550` · `nodata=nan` · values ⊆ {0,1}
  inside the footprint · 0 NaN/Inf inside · NaN everywhere outside · 0 positive px on the catalogue ·
  min distance to catalogue 3.16 px · re-read from disk after writing · **14/14 PASS** (zeros 15/15).

## Slot 2 — the decision slot (brackets slot 1 from above)

- **File:** `releases/h33-2-b2-r3p61-20261023-f94be3ad.tif` (fallback `…-f94be3ad-zeros.tif`)
- **sha256:** `f94be3ada76a4c5a5f1f1273e9514e8a2ee04d0e84eec0a506c5d8e0d0cece8a` · 34,293 dots (−8.93 %)
- **Note (122/140):** `R0 h33-2-b2 PRUNE fractional rung 3.61px: drop rings <=3.61px 37654->34293 (8.93%), no refill; pred +0.005 MODEL; UNSCORED`
- **What it decides:** above slot 1 ⇒ the catalogue shadow extends past the 300 m kernel and the next
  session sweeps 4–8 px; below slot 1 by ≥ 0.005 ⇒ the optimum is bracketed at 3 px and the final file
  is chosen from the files already built.
- **Format receipt:** `evidence/session_rung_receipt.json → variants["r3p61"]` — same grid/CRS/encoding
  as slot 1, 0 positive px on the catalogue, min distance to catalogue 4.00 px, **12/12 PASS**
  (zeros 14/14).

## Slot 3 — the low-risk file (fewer dots removed)

- **File:** `releases/h33-2-b2-r2p85-20261023-acce3907.tif` (fallback `…-acce3907-zeros.tif`)
- **sha256:** `acce390710c0d1fcf066947712c52cec45f8c0dcc2fb53bb1b254fbff959fcd7` · 36,043 dots (−4.28 %)
- **Note (126/140):** `R0 h33-2-b2 PRUNE fractional rung 2.85px: drop sqrt5+2sqrt2 rings 37654->36043 (4.28%), no refill; pred +0.005 MODEL; UNSCORED`
- **Format receipt:** `evidence/session_rung_receipt.json → variants["r2p85"]` — min distance to
  catalogue 3.00 px, **12/12 PASS** (zeros 14/14).

A fourth built file, `releases/h33-2-b2-r2p25-20261023-3908de12.tif` (941 dots removed, min distance
2.83 px, +0.003 MODEL), is the cheapest possible probe of the shadow. Spend a slot on it only if one
is otherwise unused.

## After each score

1. Paste the score and the date into `ledger/submissions.csv` (`receipt_score`, `date`, `receipt=Y`)
   and change the row's `evidence_label` to `RECEIPT`.
2. Update `README.md` CURRENT STATE (best receipt).
3. Do **not** submit the same geometry twice in different encodings to farm feedback — the encoding
   twins score identically (8 slots have already been spent that way in this lineage).

## Gate summary for all files (re-check after download)

`sha256sum <file>` must equal the hash above. The `sha8` inside each filename is the first 8 hex of
that same hash, so a truncated download is visible immediately. All files: 1 band, float32,
EPSG:32611, 3730×3292, values in {0,1}, NaN exactly outside the sample footprint, zero mass on the
catalogue, and no dot inside the declared prune rung.
