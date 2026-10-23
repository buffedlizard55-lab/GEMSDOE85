# Submission instructions — PRUNE variants of R0 (v2, 2026-10-23)

Three BUILT variants await human slot decisions (order in `SLOT_PLAN.md`).
Nothing has been submitted. The human submits from their own registered
account; upload **only one encoding per slot** (NaN primary below; zeros
twin is a fallback and scores identically — never spend a slot on a twin).
Parent R0 `h33-h33-2-b2` 0.2778 is **CLAIM** (no receipt in `ledger/`).
Predicted changes are **MODEL**. Release rasters are git-ignored (public
repo; competition-data terms unchecked) — regenerate them locally exactly:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-lock.txt
# restore pinned inputs (GitHub mirrors; every sha256 verified by the builder)
mkdir -p data/learning data/scored data/external
gh api "repos/buffedlizard55-lab/GEMSDOE32/contents/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif?ref=780a5a534269c79adfe6d1d7d5aadead161332aa" -H "Accept: application/vnd.github.raw" > data/learning/h33-b2.tif
gh api "repos/buffedlizard55-lab/GEMSDOE31/contents/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif" -H "Accept: application/vnd.github.raw" > data/scored/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif
gh api "repos/buffedlizard55-lab/GEMSDOE24/contents/inputs/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif?ref=07345ea0604953d7efb858d9cfbc21e20c7aca0b" -H "Accept: application/vnd.github.raw" > data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif
gh api "repos/buffedlizard55-lab/GEMSDOE24/contents/docs/downloads/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif?ref=07345ea0604953d7efb858d9cfbc21e20c7aca0b" -H "Accept: application/vnd.github.raw" > data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif
gh api "repos/buffedlizard55-lab/GEMSDOE24/contents/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif?ref=07345ea0604953d7efb858d9cfbc21e20c7aca0b" -H "Accept: application/vnd.github.raw" > data/scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif
gh api "repos/buffedlizard55-lab/GEMSDOE24/contents/inputs/gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif?ref=07345ea0604953d7efb858d9cfbc21e20c7aca0b" -H "Accept: application/vnd.github.raw" > data/scored/gems19-h19-4.tif
.venv/bin/python scripts/build_prune_variants.py   # writes releases/*.tif + evidence JSON; fails closed on any pin mismatch
sha256sum releases/*.tif   # must match the table below before uploading anything
```

| Slot order | File (upload this one) | SHA-256 | Dots | Form note (≤140 chars) |
|---|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-pruneD3pure-20261023-f8b4c584.tif` | `24952cdabe1c7e639775cd83d01dcb28458e147177e892faabc52d983d99ccfe` | 35,483 | `R0 h33-h33-2-b2 PRUNE d>3px pure: -2171 flank dots, 35483 total. Predicted +0.006 (MODEL). Parent 0.2778 CLAIM.` (111) |
| 2 | `releases/h33-h33-2-b2-pruneD3refill-20261023-8148117b.tif` | `554441e68f0f0e53b1e3edd6f7496cb4b1aab47bdf9e8ab7c77308bec594f20b` | 37,654 | `R0 h33-h33-2-b2 PRUNE d>3px +refill 2171 H19-5 support dots, 37654 total. Predicted +0.002 (MODEL).` (99) |
| 3 (conditional) | `releases/h33-h33-2-b2-pruneD3ge-20261023-a225c607.tif` | `f045acca8b5022a1bd303b40575574fb2b1e555b023c165d945d11a3d6fe9a62` | 36,043 | `R0 h33-h33-2-b2 PRUNE d>=3px pure: -1611 dots, keep 300m ring, 36043 total. Predicted +0.004 (MODEL).` (101) |

Zeros fallbacks (same masks; do not also submit): `…-f8b4c584-zeros.tif`
`02c65c537cdc…`, `…-8148117b-zeros.tif` `ee106fccd7e3…`,
`…-a225c607-zeros.tif` `014376bd1f96…` (full hashes in
`evidence/v2-prune-builds.json`).

**Format receipt** (all six files, re-read from disk,
`scripts/validate_v2_release.py`): PASS — EPSG:32611, 3730×3292, sample
transform, float32, one band, values in [0,1], no NaN inside footprint,
NaN (or zeros) outside per encoding, zero catalogue mass, min catalogue
distance ≥3 px. Determinism verified: independent rebuild reproduced all
six SHA-256s. Build env: rasterio 1.4.3 / GDAL 3.9.3 / numpy 2.2.6
(`requirements-lock.txt`); no RNG. Byte hashes depend on the encoder
versions — if a local rebuild's hashes differ, compare the mask content
digests (`f8b4c584`, `a225c607`, `8148117b`) and stop if those differ.

After each submission, fill `receipt_score` + `date` for that row in
`ledger/submissions.csv` from the submission-page receipt (that upgrades
CLAIM→RECEIPT), and record dated TOP_PUBLIC + remaining slots in
`README.md` CURRENT STATE. Competition page (human browser only):
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
