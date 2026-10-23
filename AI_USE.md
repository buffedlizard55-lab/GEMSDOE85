# AI_USE — disclosure record (competition rule: generative-AI disclosure)

## What an AI agent wrote in this session (2026-10-23)

- `scripts/build_prune_variants.py` — the whole builder (parent verification, push-out refill,
  emission, on-disk validation, PROXY/canary/SGMC instruments, ledger writer).
- `SLOT_PLAN.md`, `docs/MECHANISM_CARDS.md`, `docs/SUBMIT.md`, `IRREGULARITIES.md`, this file, and the
  `README.md` CURRENT STATE block.
- The three rasters in `releases/` were produced by that script from SHA-256-pinned inputs; every
  number in the docs is copied from `evidence/prune_variants.json` or from recomputation in that run.

## What the human decided (not the agent)

- **The AXIS** (`PRUNE`) for this session — the brief left it blank and the agent asked; the human
  selected PRUNE.
- Whether to spend a slot, which file to upload, and the final blind submission.
- `TOP_PUBLIC` and the slot count, which only the human can read from the leaderboard, and every
  receipt score in `ledger/submissions.csv`.
- All competition data access: the agent worked only from files already pinned in this repo
  (`registry/data_manifest.json`, `registry/learning_manifest.json`, `registry/scored_artifacts.json`)
  and fetched their pinned bytes from the mirrors recorded there. No competition page was fetched, no
  leaderboard was scraped, nothing was submitted.

## Rules the agent worked under

No automated access to drivendata.org or dropbox.com; no credentials read, stored or printed; no
login or submission code; no label probing (no region-isolated or patterned files); reproducible
inputs by sha256; fixed seeds (`seed=20` for the holdout draw, `20261023` for the bootstrap); git SHA
recorded in `evidence/prune_variants.json`.
