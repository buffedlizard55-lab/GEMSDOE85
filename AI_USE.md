# AI_USE — what the AI wrote, what the human decided

Required by the competition rules on generative-AI disclosure (see
https://docs.nlr.gov/docs/fy26osti/96647.pdf). This file is scoped to the PRUNE session on branch
`arena/eb7e09d3-gemsdoe85`; earlier sessions' disclosures are unchanged.

## The human decided

| Decision | Value | When |
|---|---|---|
| AXIS for this session | **PRUNE** (chosen by the operator from the five options offered) | 2026-10-23 |
| TOP_PUBLIC and slots left | left **blank** — the operator fills them from their own account; nothing is scraped | 2026-10-23 |
| Which file to submit, and when | **open** — `SLOT_PLAN.md` recommends slot 1 = `h33-2-b2-prune3-…` | not yet |
| The standing incumbent | `h33-h33-2-b2` (0.2778, CLAIM) | inherited |

## The AI wrote

* `src/gems85/lineage.py` — pins, the R0 rebuild, the PRUNE edit, the DTI algebra used for the
  target, the on-disk gates, and the GeoTIFF writers.
* `scripts/rebuild_r0.py` — hash-verifies four pins and proves R0 is pixel-identical to the
  incumbent (`evidence/r0_rebuild.json`).
* `scripts/build_prune_variants.py` — builds the three variants, enforces the 1–50 % change window,
  re-reads every file from disk, writes `releases/`, `ledger/submissions.csv` and
  `evidence/prune_session.json`.
* `scripts/prune_holdout_proxy.py` — the fold-clean hide-and-recover instrument, its calibration
  against the two scored ladder steps, and the turnover result
  (`evidence/prune_holdout_proxy.json`).
* `tests/test_lineage.py` — 16 tests: algebra against the repository's own metric, the rebuild,
  monotonicity, Euclidean-vs-Chebyshev, gate accept/reject, ledger/file consistency.
* `evidence/mechanism_cards.json`, `SLOT_PLAN.md`, `docs/SUBMIT.md`, `IRREGULARITIES.md`, this
  file, and the CURRENT STATE block in `README.md`.

## What the AI did **not** do

No submission, no login, no scraping, no leaderboard access, no drivendata.org fetch, no
dropbox.com contact. No credentials were read, requested or stored. No label probing: every
variant is a distance-threshold edit of the incumbent's own dots, and the only holdout used is
built from the *published* catalogue with whole components withheld and the fold-clean rule that
variants may only see visible ones. The AI did not choose the axis, the slot, or the final file.

## Claims the AI could not verify

R0's 0.2778 and the ladder's 0.2600 / 0.2708 are **owner-reported**; no submission-page receipt
exists in `ledger/`. Every number this session produced that depends on them is labelled MODEL or
PROXY accordingly, and none of them is called a score.
