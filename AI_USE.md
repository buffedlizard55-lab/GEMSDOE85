# AI-use disclosure

Three v2 sessions are recorded. The first (2026-10-22/23, `arena/cf29702c`) stopped BLOCKED; the
second (2026-10-23, `arena/e081f5da`) cleared the rebuild blocker and built the PRUNE variants; the
third (2026-10-23, `arena/a9cc6c47`) built the SNAP variants, and its entry starts at
"What the AI agent did (SNAP session)".

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

## What the AI agent did (SNAP session, branch `arena/a9cc6c47-gemsdoe85`, 2026-10-23)

- Verified all 11 SHA-256 pins it used (7 parent-lineage pins, plus the lidar scarp, GeoDAWN
  extension, SGMC and 419 MB feature-stack manifests) and rebuilt R0 pixel-identically
  (121,131 → 44,090 → 40,199 → 37,654 dots; parent files `baeae321…` / `c55bafc4…`).
- Wrote `src/gems85/snap85.py` (the two response fields, the deterministic snap rule with its
  catalogue/separation/footprint constraints, the label-free support-coverage diagnostic) and
  `tests/test_snap85.py` (10 synthetic contract tests).
- Wrote `scripts/gemsdoe85_snap_session.py`: pin verification, parent rebuild, three SNAP variants,
  both GeoTIFF encodings, re-read validation against the brief's gates, per-fold catalogue proxy with
  CI, SGMC control, leakage canary, receipt JSON, and idempotent ledger append.
- Wrote `docs/mechanism_cards_snap.md` (hypothesis / mechanism / confounder / predicted sign /
  falsifier per variant), rewrote `SLOT_PLAN.md`, added the SNAP contingency to `docs/SUBMIT.md`,
  inserted the README CURRENT STATE block, and added IR-V2-13 … IR-V2-16.
- Chose the AXIS (SNAP) **after asking the human and receiving no answer** (the question was skipped);
  the choice, its rejected alternatives and the re-scope condition are recorded in IR-V2-13. Chose the
  three values (on-ridge lidar, on-ridge TMI, free-window lidar) to separate "which physics" from
  "may a dot leave the mapped trace".
- Fetched only GitHub-hosted, SHA-256-pinned files through the repository's own restore path. No
  leaderboard, competition page, forum, Dropbox or credentials were accessed; nothing was submitted.

### What remains the human's decision (SNAP session)

- Whether SNAP was the intended axis at all (IR-V2-13); if not, these three files are simply unspent.
- Whether to spend any slot on them — `SLOT_PLAN.md` ranks them **below** the PRUNE ladder because
  their predicted effect is inside the ±0.01 no-evidence band.
- `TOP_PUBLIC` with date, the rolling-week slot count, and a submission-page receipt for every score.
