# AI USE — GEMSDOE85, session `arena/c4de5673-gemsdoe85` (2026-10-23)

Disclosed for the competition's generative-AI disclosure requirement
(rules: <https://docs.nlr.gov/docs/fy26osti/96647.pdf>).

## What the AI wrote (all of it)

Everything in this session was written by the AI agent (Arena.ai Agent Mode) under the
operator's brief:

* `scripts/session_setup.sh` — venv + pinned-restore bootstrap.
* `scripts/inspect_r0_lineage.py`, `scripts/probe_d15_d28_solo_rules.py` — read-only
  lineage forensics (how `d1.5`, `d2.8`, `h27-4-solo-d28` and `h33-2-b2` relate).
* `scripts/axis_concentration_stats.py` — calibration of the block-density CV statistic
  against the family's own scored files.
* `scripts/build_concentration_variants.py` — builds the three CONCENTRATION variants,
  rebuilds and verifies the parent, runs the format gates, writes
  `evidence/axis_concentration_build.json`.
* `scripts/build_ledger.py` — writes `ledger/submissions.csv` and `ledger/history.csv`.
* `evidence/holdout_proxy/*.json` — report-only holdout-proxy receipts produced by the
  shared evaluator (`vendor/gems57/evaluate_holdout.py`).
* `releases/*` — the six raster files (3 variants × NaN-outside and zeros-outside).
* `docs/MECHANISM_CARDS.md`, `SLOT_PLAN.md`, `IRREGULARITIES.md`, `docs/SUBMIT.md`,
  `AI_USE.md`, and the CURRENT STATE block in `README.md`.

The AI also wrote the code and prose in the repository's existing modules that this session
touched; it did **not** modify `vendor/gems57` (no private evaluator or writer fork).

## What the human decided (and the AI did not)

* **The AXIS for this session: CONCENTRATION.** The brief assigns the axis to the human;
  the AI asked and did not choose. (The AI did rank the axes by predicted effect before
  asking, as input to the decision — SNAP, CONCENTRATION, PRUNE, MASS, RELIEF, SPACING.)
* **`TOP_PUBLIC` and "slots left this week": left UNKNOWN** at the human's explicit
  instruction. The AI did not read the DrivenData leaderboard (the terms ban automated
  access) and did not guess.
* **The upload encoding: zeros-outside twin.** The human is the one who submits; the AI
  wrote both encodings and documented which one the shared validator accepts and which
  encoding the incumbent uses. The human may override.
* **Nothing was submitted.** The AI never contacted `dropbox.com`, never fetched a
  `drivendata.org` page, never read, requested, stored or printed credentials, and never
  wrote code that logs in, scrapes a leaderboard or submits.
* **The interpretation of constraint 4** (≥ 3 px from the catalogue) for non-PRUNE axes is
  documented in `IRREGULARITIES.md` (IR-85-A4) and is offered for the human's confirmation.
* **The final selection** of which file to submit, and of the final Phase 2 file, is the
  human's; the AI proposes the order in `SLOT_PLAN.md`.
