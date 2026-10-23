# AI_USE.md — generative-AI disclosure (required by the competition rules)

Required by https://docs.nlr.gov/docs/fy26osti/96647.pdf (reproducible code + generative-AI
disclosure). Scope: session 2026-10-23, branch `arena/991f7136-gemsdoe85`, AXIS = MASS.

## What the AI agent wrote

- `scripts/build_mass_axis.py` — parent reproduction, the substituted ranking, the three
  variant builds (deterministic greedy max-coverage for the +10 % file), validation, and the
  bracket predictor.
- `scripts/write_mass_ledger.py` — ledger rows generated from `evidence/mass_axis.json`,
  with every sha256 re-read from disk and refused if it disagrees.
- `tests/test_mass_axis.py` — release-integrity and mechanism-arithmetic tests.
- `releases/MECHANISM_CARDS.md`, `SLOT_PLAN.md`, `IRREGULARITIES.md`, `docs/SUBMIT.md`, this
  file, and the CURRENT STATE block of `README.md`.
- The three rasters in `releases/` (a mechanical consequence of the script, not a judgement).

## What the human decided

- **AXIS = MASS** (the brief left it blank; `registry/lane.json` is still `unassigned`).
- **TOP_PUBLIC = 0.3195**, supplied from an earlier repo prompt; carried as UNVERIFIED.
- **Slots left this week = 3.**
- Whether any file is uploaded, which one, and from the human's own registered account. The
  agent never submits, never logs in, never scrapes the leaderboard, and never contacts
  Dropbox.

## Frame

The AI used the parent CLAIM 0.2778 and the ledger's owner-reported numbers as given, labelled
them CLAIM, and did not invent any score. Numbers produced here are either measured from
pinned inputs (sha256-verified) or labelled MODEL. No proxy is presented as a score.
