> **SUPERSEDED FOR SLOT CHOICE (2026-10-23).** A parallel session (`arena/28da814f`) landed its own
> `SLOT_PLAN.md` on `main` while this branch was open, and it already ranks `prune3`/`prune4` as slot
> candidates at +0.007/+0.003. The ranking below is not merged over it. What survives from this file is
> the *evidence*: the fold-clean instrument in `evidence/prune_holdout_proxy.json` contradicts those
> positive predictions. Adjudicate the two readings (IR-V2-07) before spending a slot.

# SLOT_PLAN — next 3 slots, in order

Entity quota: 3 scored submissions per rolling week + one final file. Deadline **2026-12-03**
(~6 weeks from 2026-10-23). Standing incumbent: **R0 `h33-h33-2-b2`, 37,654 dots, 0.2778
CLAIM** (no receipt in `ledger/` yet). Nothing in this session is predicted to beat it.

| # | Slot | File (built) | Predicted live | What the result changes |
|---|---|---|---|---|
| 1 | this week | `h33-2-b2-prune3-20261023-c493fdeb` (35,483 dots) | −0.002, range −0.010…+0.004 | **Closes or reopens PRUNE.** ≥0.2840 → the 2–3 px annulus is halo and the ladder continues; ≤0.2700 → the annulus carries real new-fault truth and every future prune must stop at 2 px. |
| 2 | this week or next | MASS probe: R0 minus 2,171 dots drawn from **d > 10 px** (same count removed as slot 1, opposite location) | +0.004 if mass dominates, −0.004 if distance does | The decisive mass-vs-distance test the ladder has never run. Together with slot 1 it separates the two effects that every rung of the ladder confounds. If it wins, every later variant should be a mass sweep at fixed field. |
| 3 | next week | CONCENTRATION at 2 km blocks, prior = catalogue density, move 15 % of dots, target block-density CV 0.51–0.59 | +0.002…+0.008 | Tests whether the score responds to *where* mass is at all. |

Then: wk 3–4 combine the two axes that moved; wk 5 confirm on the winner and build the fallback
twin; wk 6 freeze the final file, re-validate both twins, upload once blind.

**Do not** spend a slot on `prune3r` or `prune4` unless slot 1 lands above 0.2840. They are
controls, and their predictions are the same sign as slot 1 with worse magnitude.

## Why this is not the brief's default plan

The default (wk1–2 MASS, CONCENTRATION, SNAP, PRUNE, RELIEF) assumes PRUNE was unexplored. It
was: cutoffs 1 and 2 are already the two most recent scored rungs (+0.0108, +0.0070). This
session measured the third rung before spending it, and the fold-clean instrument — the only
offline instrument that reproduces both of those steps — says the ladder turns over at exactly
3 px (0/5 folds). Spending all three slots on PRUNE values 3 and 4 would therefore buy two
near-certain nulls.

## Two proposals for later axes (not built this session)

1. **MASS at fixed field, swept downward.** The field is saturated: only 440 cells remain
   available at d > 3 px at the parent's 2.8 px spacing (measured, `evidence/prune_session.json`
   → `refill_detail`). So *every* future variant can only delete. A clean sweep (R0, −5 %, −10 %,
   −15 % at random-from-far-field) answers "is this a mass effect?" in one week. Mechanism:
   DTI's denominator is affine in mass while T saturates. Confounder: mass and catalogue
   proximity are correlated along the whole H19-5 field. Falsifier: a flat score across a 15 %
   mass range.
2. **STRIKE-COHERENCE filter (SPACING × TRACKB, Phase-2 shaped).** Rank R0's dots by how well
   they lie on a ≥1 km strike-consistent trace, keep the same count, and drop the rest. The
   metric's kernel pays for length, and Phase 2 rescoring by geologists rewards traces that a
   human can draw. Mechanism: fault traces are 1-D; isolated dots buy at most one kernel cell.
   Confounder: drainage lineaments are also strike-coherent. Falsifier: a geology-blind shuffle
   that preserves strike coherence but destroys position scores the same.

## Rules this plan is bound by

3 slots/week, one final file, no leaderboard scraping, human uploads from their own account.
A live change under 0.01 is no evidence. The hide-and-recover number is a PROXY (the ledger
shows it correlates −0.87 to +0.54 with live scores over n = 12–14 files), never a gate.
