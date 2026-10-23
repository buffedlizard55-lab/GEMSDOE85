# AI-use disclosure

Two v2 sessions are recorded. The first (2026-10-22/23, `arena/cf29702c`) stopped BLOCKED; the
second (2026-10-23, `arena/e081f5da`) cleared the rebuild blocker and built the PRUNE variants.

## 2026-10-23 — arena/cf29702c-gemsdoe85 (kept verbatim)
- Human supplied the v2 brief, R0 identity, evidence policy, allowed axes, quota and no-submission constraints. Human did **not** assign AXIS, provide TOP_PUBLIC, receipts or remaining quota.
- AI inspected local manifests/history and limited GitHub metadata/source paths, restored the already-pinned R0 artifact into ignored storage, verified byte pins, and measured its dot count/catalogue distance. This was not a recipe rebuild or a new prediction.
- AI wrote `scripts/audit_v2_inputs.py`, byte-verification and metric-algebra regression tests, `evidence/v2-input-audit.json`, the session run card, the header-only ledger, CURRENT STATE block, slot proposal, submission stop note, this disclosure and irregularities. No model training, raster generation, feature-ranking choice or submission was performed.
- AI stopped because the recipe-rebuild gate and human assignment/history prerequisites were not cleared. Human retains axis selection, publication-permission review, quota/receipt records, final-file choice and all submissions.
- This disclosure covers this session only; it does not certify completeness of earlier AI-use records. No credentials or account sessions were obtained. No forbidden hosts were contacted.

## 2026-10-23 — arena/e081f5da-gemsdoe85 (this session)
The competition rules require disclosure of generative-AI use, and the brief requires a record of what
the AI wrote versus what the human decided. This file is the factual record for this session; it is not
a legal statement.

## What the AI agent did (this session, branch `arena/e081f5da-gemsdoe85`)

- Wrote `src/gems85/thinning85.py` (re-implementation of the deterministic Poisson-disk dot thinning,
  extended to record the packing order, verified byte-identical to the pinned d2.8 raster).
- Wrote `src/gems85/r0_lineage.py` (SHA-256 pin table, R0 rebuild from pinned inputs, label-free
  per-dot unique-credit ranking, deterministic removal rule).
- Wrote `scripts/gemsdoe85_prune_session.py` (the whole build: pin verification, parent rebuild,
  three PRUNE variants, GeoTIFF writing in both encodings, re-read validation, report-only proxies,
  ledger and receipt emission).
- Wrote `tests/test_r0_lineage.py` (11 tests: thinning contract, unique-credit vs brute force,
  determinism, parent reproduction, variant semantics, shipped-file gates).
- Wrote `docs/mechanism_cards_prune.md`, `SLOT_PLAN.md`, `docs/SUBMIT.md`, `IRREGULARITIES.md`,
  this file, and the CURRENT STATE block at the top of `README.md`.
- Selected the AXIS (PRUNE) and the three rung values, after rejecting MASS with the two measurements
  recorded in `IRREGULARITIES.md` IR-V2-08.
- Fetched only GitHub-hosted, SHA-256-pinned inputs (`scripts/restore_data.py`); read no competition
  web page, no leaderboard, no credentials; submitted nothing.

## What the human decided / must decide

- That the session runs on this branch with this agent, and the overall objective (maximise P(win)).
- The registered account, the three weekly slots, and which file goes in each slot
  (`docs/SUBMIT.md` proposes the order; the human may reorder).
- `TOP_PUBLIC` (with date) and the number of slots left — both still unfilled.
- Whether the redistribution terms of the pinned competition rasters permit this repository to keep
  them (IR-V2-10).
- All live scores. Every score in this repository is a CLAIM until the human pastes a
  submission-page receipt into `ledger/submissions.csv`.

## Standing human-only constraints honoured

No contact with dropbox.com; no automated access to drivendata.org (including the leaderboard and the
terms page); no credentials read, requested or stored; no code that logs in, scrapes or submits; one
entity, no slot multiplication. Analysis is deterministic and reproducible from pins: rerunning
`python scripts/gemsdoe85_prune_session.py` on the same pinned inputs and the same git commit
regenerates byte-identical GeoTIFFs (the sha8 in each filename is checkable).

## Provenance of the substantive ideas

The parent lineage (H19-5 ridge → 2.8 px packing → catalogue-flank prunes), the 100–400 m USGS-vs-LiDAR
offset argument, and the live scores 0.2600 / 0.2708 / 0.2778 come from the owner's earlier sessions
(GEMSDOE19/24/25/28/31/32) and the brief. This session's own contributions are the exact rebuild
verification, the unique-credit ranking and its rejection as a MASS tool, the measured refill-capacity
result, and the SGMC-proxy bias calibration (+0.0083) used to state the predictions.

---

## Session 2026-10-23 (branch `arena/fb7ddb5a-gemsdoe85`) — SNAP axis

**What the AI wrote (and the human should review):** `src/gems85/snap_axis.py` (offset set, nodata-aware
edge field, kernel-credit accounting, the constrained snapping loop), `scripts/gemsdoe85_snap_session.py`
(pins → rebuild → three arms → gates → proxies → ledger → receipt), `scripts/restore_axis_inputs.py`
(the six pinned inputs this session reads), `tests/test_snap_axis.py` (9 contract tests), the three SNAP
rows in `ledger/submissions.csv`, the CURRENT STATE block in `README.md`, the SNAP section of
`docs/SUBMIT.md`, the rewritten `SLOT_PLAN.md`, and IR-V2-13…16. The mechanism cards, the choice of
SNAP, the three edge fields and the predictions are AI-authored models, not measurements of the live
metric.

**What the AI decided without the human:** the axis (the human skipped the question; IR-V2-14), the
`min_sep = 2.0 px` packing floor, `margin = 0.05`, the "never move closer to the catalogue" rule, and
the reading that the SGMC-minus-catalogue proxy is the least mass-confounded local instrument.

**What only the human can do:** read `TOP_PUBLIC` and the remaining slots off the account page; decide
whether a spare slot is worth spending on a predicted-null SNAP receipt; upload, and paste the
submission-page receipts back into `ledger/submissions.csv`. No file here is endorsed for upload by the
AI, and none was submitted.
