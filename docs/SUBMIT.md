# SUBMIT — v2, 2026-10-23 (PRUNE + RELIEF gated candidates; human submits)

The human uploads **one file per slot** from their own registered DrivenData account. Nothing in
this repository logs in, scrapes the leaderboard, or submits. `TOP_PUBLIC` (with observation date)
and remaining rolling-week / total slots must be filled by the human in `README.md` (`CURRENT STATE`)
and `SLOT_PLAN.md`. After each scored upload, record `receipt_score`, `date`, and `receipt = Y` in
`ledger/submissions.csv`.

---

## Recommended Next 3 Slots (`SLOT_PLAN.md`)

### Slot 1 — `PRUNE` rung 3 (live `d_cat > 3 px` baseline)

- **Primary upload file (NaN outside footprint):** `releases/h33-2-b2-prune3-20261023-fb308615.tif`
  - `sha256`: `fb308615161ad8f62b063d90972a4c36e7c66e7c58beb3316c81497cfe65261e` (`346,839 B`, `35,483` dots)
- **Fallback twin (zeros outside footprint; upload ONLY if portal rejects NaN):**
  `releases/h33-2-b2-prune3-20261023-fb308615-zeros.tif`
  - `sha256`: `7296873be941b40d157d136243dc701a4e40f2c0b7485549fd45c7b59a87a98d` (`210,331 B`, `35,483` dots)
- **Submission name:** `h33-2-b2-prune3-20261023-fb308615`
- **Form note (`115 / 140` chars):**
  `R0 h33-2-b2 PRUNE rung3: drop 2<d_cat<=3px flank dots, 37654->35483 (5.77%), no refill; pred +0.007 MODEL; UNSCORED`
- **Format receipt (`evidence/session_prune_receipt.json`):** `EPSG:32611` · `3730×3292` · 1 band ·
  `float32` · transform `[100, 0, 243350, 0, -100, 4508550]` · values `⊆ {0, 1}` inside footprint ·
  `0` NaN/Inf inside footprint · `NaN` outside · `0` catalogue mass · `min d_cat = 3.162 px` ·
  re-read from disk · **14/14 checks PASS** (`15/15` zeros twin).

### Slot 2 — `RELIEF` Piedmont → Range-front +10 % (orthogonal relief-regime test)

- **Primary upload file (NaN outside footprint):** `releases/h33-2-b2-reliefp2r10-20261023-669f0637.tif`
  - `sha256`: `669f0637b8141e1cf37d89929bf22155771d2e48a7d32b046fb75a6dfae4d050` (`354,759 B`, `37,654` dots)
- **Fallback twin (zeros outside footprint):**
  `releases/h33-2-b2-reliefp2r10-20261023-669f0637-zeros.tif`
  - `sha256`: `e730deb681a25ab19c67a9befaa2c47affd7ca6744a40e50142a332ba35ddbf9` (`219,076 B`, `37,654` dots)
- **Submission name:** `h33-2-b2-reliefp2r10-20261023-669f0637`
- **Form note (`114 / 140` chars):**
  `R0 h33-2-b2; RELIEF piedmont->range +10% (3765 dots, d_cat>3px, n=37654 fixed); pred +0.008 (+0.001..+0.015) MODEL`
- **Format receipt (`evidence/session_relief_receipt.json → variants["h33-2-b2-reliefp2r10"]`):**
  `EPSG:32611` · `3730×3292` · 1 band · `float32` · transform `[100, 0, 243350, 0, -100, 4508550]` ·
  `nodata=nan` · values `⊆ {0, 1}` inside footprint · `0` NaN/Inf inside footprint · `NaN` outside ·
  `37,654` positive px (`12.769 %` parent dots replaced; `3,765` shifted `T2 -> T3`) · `0` catalogue
  mass · `min d_cat = 3.162 px > 3.0 px` · re-read from disk · **16/16 checks PASS** (`17/17` zeros twin).

### Slot 3 — Conditional on Receipts 1 & 2 (upload at most ONE of 3A / 3B / 3C)

- **Option 3A (if `Slot 2 − Slot 1 ≥ +0.01`): `RELIEF` Basin+Piedmont → Range-front +15 %**
  - **File:** `releases/h33-2-b2-reliefbp2r15-20261023-21af1eee.tif` (fallback `...-zeros.tif`, sha256 `e61ad36064dd7e898ed99916444ce194e50c8ae8751ed80e21ea6872bee67be5`)
  - `sha256`: `21af1eee6b8ce7eb92f79f0be586b8a34e551d74a1901ad16deb496b26bdf3d0` (`354,079 B`, `37,654` dots, `17.092 %` changed)
  - **Name:** `h33-2-b2-reliefbp2r15-20261023-21af1eee`
  - **Form note (`120 / 140` chars):**
    `R0 h33-2-b2; RELIEF basin+piedmont->range +15% (5648 dots, d_cat>3px, n=37654 fixed); pred +0.006 (-0.002..+0.014) MODEL`
  - **Format receipt:** `min d_cat = 3.162 px`, `0` catalogue mass, re-read from disk, **16/16 PASS** (`17/17` zeros).

- **Option 3B (if `Slot 2 − Slot 1 ≤ −0.01`): `RELIEF` Range-front → Basin+Piedmont +10 %**
  - **File:** `releases/h33-2-b2-reliefr2bp10-20261023-7a0329ee.tif` (fallback `...-zeros.tif`, sha256 `108dde9c53f8c68850ea80d8ad71add672d41ef2fa8fbd27787ef47744e69c58`)
  - `sha256`: `7a0329ee1d53cf4738d114c0c7f1601e3828099d2bd15c0385fd1382675180c2` (`356,035 B`, `37,654` dots, `13.672 %` changed)
  - **Name:** `h33-2-b2-reliefr2bp10-20261023-7a0329ee`
  - **Form note (`120 / 140` chars):**
    `R0 h33-2-b2; RELIEF range->basin+piedmont +10% (3765 dots, d_cat>3px, n=37654 fixed); pred -0.002 (-0.010..+0.007) MODEL`
  - **Format receipt:** `min d_cat = 3.162 px`, `0` catalogue mass, re-read from disk, **16/16 PASS** (`17/17` zeros).

- **Option 3C (if `|Slot 2 − Slot 1| < 0.01` and `Slot 1 − R0 ≥ +0.01`): `PRUNE` rung 4**
  - **File:** `releases/h33-2-b2-prune4-20261023-2880b0e9.tif` (fallback `...-zeros.tif`; reserve rung 5 `h33-2-b2-prune5-20261023-7ebfc408.tif` also validated in `releases/`)
  - `sha256`: `2880b0e90582d4cfe03165c41201c107071d3a1a88a5717351a6943f29365e7a` (`340,096 B`, `33,829` dots, `10.158 %` changed)
  - **Name:** `h33-2-b2-prune4-20261023-2880b0e9`
  - **Form note (`116 / 140` chars):**
    `R0 h33-2-b2 PRUNE rung4: drop 2<d_cat<=4px flank dots, 37654->33829 (10.16%), no refill; pred +0.003 MODEL; UNSCORED`
  - **Format receipt:** `min d_cat = 4.123 px`, `0` catalogue mass, re-read from disk, **14/14 PASS** (`15/15` zeros).

---

## Report-only diagnostics (`evidence/session_relief_receipt.json` — PROXY, never gates)

- **Catalogue hide-and-recover PROXY (`gems57-pooled-hide-v2`, `n = 11,321` withheld positives, 400 20-km cluster draws):**
  `R0_parent_rule` = `0.09609` `[0.08242, 0.10899]`; `ctrl_collar3_0pct` = `0.09638` `[0.08292, 0.11017]`;
  `reliefp2r10` = `0.09283` `[0.07952, 0.10584]`; `reliefbp2r15` = `0.09295` `[0.07983, 0.10578]`;
  `reliefr2bp10` = `0.09518` `[0.08203, 0.10820]`.
- **SGMC off-catalogue control PROXY (`sgmc_minus_catalogue_3px`, `n = 62,122` positives):**
  `R0_parent` = `0.09539` `[0.08457, 0.10672]`; `ctrl_collar3_0pct` = `0.09883` `[0.08830, 0.10959]`;
  `reliefp2r10` = `0.10388` `[0.09296, 0.11487]`; `reliefbp2r15` = `0.10418` `[0.09339, 0.11595]`;
  `reliefr2bp10` = `0.09434` `[0.08458, 0.10454]`.
- **Leakage canary:** 19 competition bands tested (`60,988` positives vs `200,000` background); max
  single-feature AUC = **`0.5693`** (`geod_2ndinv`) `< 0.90` → **CLEAN**.
