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

## 2026-10-23 — session 3, branch `arena/cbdb023a-gemsdoe85`

### What the AI agent wrote / ran

- Restored every pinned input and verified SHA-256 before use (`scripts/restore_data.py`), including a
  one-line fix so manifest paths with subdirectories can be restored at all (IR-V3-01). Rebuilt R0 from
  its pinned ancestors and asserted pixel identity (37,654 dots).
- Ran the axis feasibility measurements — SNAP destination availability at four separation floors, the
  SNAP probe (18,065 dots / 48 % moved at a 2.0 px floor, −1.2 % unique credit), and the 1-km block
  prior / destination capacity (26 cells) — **before** choosing an axis (IR-V3-02).
- Wrote `scripts/gemsdoe85_rung_session.py` (new), the three fractional PRUNE rungs, all gate checks,
  `evidence/session_rung_receipt.json`, the ledger rows, `docs/mechanism_cards_rung.md`, `SLOT_PLAN.md`,
  `docs/SUBMIT.md`, the README CURRENT STATE block and the IR-V3 items.
- Wrote the mechanism cards and the predictions. No model was trained; no new geophysical hypothesis
  was introduced; no dot was added anywhere.
- Submitted nothing, scored nothing, contacted no leaderboard, read no credentials, contacted no
  forbidden host, and did not access drivendata.org or dropbox.com.

### What the human decided / must decide

- **AXIS for this session was not supplied**; the AI asked and the question was skipped, so the AI chose
  PRUNE from measurement (IR-V3-02). The human can overrule this before the next build.
- Which three files go in which slots, the date-stamped `TOP_PUBLIC`, the remaining quota, and all
  submission-page receipts (still absent; 0.2778 remains a CLAIM).
- Whether the pinned competition rasters may stay in this repository at all (IR-V2-10, still open).

### Provenance of the ideas

The prune ladder, the 100–400 m USGS-vs-imagery offset argument and the live numbers 0.2600 / 0.2708 /
0.2778 come from the owner's earlier sessions and the brief. This session's own contributions are the
fractional-rung decomposition of the 2–3 px ring, and the measurement that SNAP, CONCENTRATION and
RELIEF cannot be built on this parent at its 2.8 px packing rung.
