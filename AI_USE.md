# AI-use disclosure

Four v2 sessions plus a "session 3" are recorded. (1) 2026-10-22/23, `arena/cf29702c` — stopped BLOCKED. (2) 2026-10-23,
`arena/e081f5da` — cleared the rebuild blocker and built the PRUNE variants. (3) 2026-10-23,
`arena/30dcc7f0` — re-verification turn, no raster built. (4) 2026-10-23, `arena/a9cc6c47` — built the
SNAP variants; its entry starts at "What the AI agent did (SNAP session)".

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

## Concurrent sessions merged to `main` during this PR (preserved verbatim)

## 2026-10-23 — arena/30dcc7f0-gemsdoe85 (verification turn)

- AI read the local manifest, ledger, slot plan, and existing R0 recipe; restored only the hash-pinned
  H19-5, d2.8/solo, R0, labels, and sample-template inputs from their GitHub mirrors into ignored
  `data/` storage. No competition-site or leaderboard page was accessed.
- AI installed the locked Python dependencies, verified the relevant manifest and lineage hashes,
  rebuilt R0 (37,654 dots) and matched both pinned R0 SHA-256 values exactly, re-read/validated all
  three existing PRUNE release pairs, and ran the targeted metric/lineage tests (31 passed).
- AI did not build another raster: the PRUNE axis was selected by the earlier AI session, not assigned
  by the human in this brief, and all three corresponding axis/value experiments already exist in the
  ledger. AI added the README CURRENT STATE block and recorded this decision in IRREGULARITIES.md.
- Human has not supplied an AXIS, dated TOP_PUBLIC, slot availability, or receipt in this turn. No
  competition submission was made; no slot use is claimed.

## What the AI agent did (SNAP session, branch `arena/a9cc6c47-gemsdoe85`, 2026-10-23)

- Verified all 11 SHA-256 pins it used (7 parent-lineage pins plus the lidar scarp, GeoDAWN extension,
  SGMC and 419 MB feature-stack manifests) and rebuilt R0 pixel-identically
  (121,131 → 44,090 → 40,199 → 37,654 dots; parent files `baeae321…` / `c55bafc4…`).
- Wrote `src/gems85/snap85.py` (the two response fields, the deterministic snap rule with its
  catalogue/separation/footprint constraints, the label-free support-coverage diagnostic) and
  `tests/test_snap85.py` (10 synthetic contract tests).
- Wrote `scripts/gemsdoe85_snap_session.py`: pin verification, parent rebuild, three SNAP variants,
  both GeoTIFF encodings, re-read validation against the brief's gates, per-fold catalogue proxy with
  CI, SGMC control, leakage canary, receipt JSON, and idempotent ledger append.
- Wrote `docs/mechanism_cards_snap.md` (hypothesis / mechanism / confounder / predicted sign /
  falsifier per variant), rewrote `SLOT_PLAN.md`, added the SNAP contingency to `docs/SUBMIT.md`,
  consolidated the README CURRENT STATE block, and added IR-V2-14 … IR-V2-17.
- Chose the AXIS (SNAP) **after asking the human and receiving no answer** (the question was skipped);
  the choice, its rejected alternatives and the re-scope condition are recorded in IR-V2-14. Chose the
  three values (on-ridge lidar, on-ridge TMI, free-window lidar) to separate "which physics" from
  "may a dot leave the mapped trace".
- Fetched only GitHub-hosted, SHA-256-pinned files through the repository's own restore path. No
  leaderboard, competition page, forum, Dropbox or credentials were accessed; nothing was submitted.

### What remains the human's decision (SNAP session)

- Whether SNAP was the intended axis at all (IR-V2-14); if not, these three files are simply unspent.
- Whether to spend any slot on them — `SLOT_PLAN.md` ranks them **below** the PRUNE ladder because
  their predicted effect is inside the ±0.01 no-evidence band (IR-V2-16).
- `TOP_PUBLIC` with date, the rolling-week slot count, and a submission-page receipt for every score.

## 2026-10-23 — arena/28da814f-gemsdoe85 (this session)

- AI restored all 23 `registry/data_manifest.json` + 2 `registry/learning_manifest.json` + 7 R0 lineage
  inputs from commit-pinned GitHub mirrors into gitignored storage and verified all SHA-256 digests
  (`evidence/v2-input-audit.json`: 23/23 and 2/2 VERIFIED).
- AI verified `IR-V2-19` (`requirements-lock.txt` `rasterio==1.4.4` deflate stream parity) and added a
  GeoTIFF re-encoding SHA-256 check to `scripts/gemsdoe85_prune_session.py` and `tests/test_r0_lineage.py`
  proving that rebuilding and writing `L.r0` from scratch reproduces both pinned R0 digests
  (`baeae3219bba6a19bc8cfe79224e28555c50184b7c1ca65c2a822f54807c77dd` and
  `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`) and re-validated all 9 shipped
  release pairs across `PRUNE`, `PRUNE-rungs`, and `SNAP`.
- Human retains `AXIS` assignment/confirmation, `TOP_PUBLIC` (with date), weekly/total slot count, score
  receipts, deadline/timezone confirmation, and all portal submissions. No forbidden hosts were contacted.

## 2026-10-23 — arena/85dc0b4a-gemsdoe85 (AXIS=PRUNE applied; merged with parallel ladder/SNAP sessions)
- Human supplied the v2 brief and decided in-session: AXIS=PRUNE; content-exact rebuild acceptable (later superseded upstream by byte-identical rebuild under rasterio 1.4.4); parent exclusions stand; 3 slots free this week; no R0 variant previously submitted. TOP_PUBLIC/receipts/deadline still not supplied.
- AI restored pinned rasters from GitHub mirrors only (SHA-256 verified; no drivendata.org/dropbox), verified the recorded R0 recipe content-exactly, built prune3/r2p85/prune3fill20, found on merge that the first two duplicate tracked upstream builds byte-for-byte (deduped; no duplicate ledger rows), kept the novel count-held refill (`12a3b132…`) with upstream-schema receipt, computed report-only proxies, seeded `ledger/lineage_claims.csv`, and reconciled README/SLOT_PLAN/SUBMIT/IRREGULARITIES as addenda to the upstream canonical text.
- AI wrote `scripts/build_prune_variants.py`, `scripts/validate_v2_release.py`, `scripts/proxy_prune_holdout.py`, `tests/test_v2_prune.py`, `evidence/v2-prune-*`, `evidence/session_prune_refill_receipt.json`, and one receipts-list line in `tests/test_r0_lineage.py`. No slot used, nothing submitted, no credentials accessed.
