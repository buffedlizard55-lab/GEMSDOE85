<!-- CROSS-SESSION NOTE (2026-10-23): while this branch was open, `main` received a sibling
session that built six PRUNE rungs, three RELIEF files and three SNAP files on the same parent
(`h33-h33-2-b2`), with its own SLOT_PLAN and a differently-shaped ledger. This plan is therefore
superseded as the repository's single plan; see IRREGULARITIES.md IR-86-006. It remains the
correct plan for the four files in `releases/` built here. -->
# SLOT_PLAN — one entity, 3 scored submissions/week, deadline 2026-12-03

**Parent (R0):** `h33-h33-2-b2` (GEMSDOE32) — 37,654 unit dots, 0 on the catalogue,
min 2.236 px from it. **Best receipt: none.** The 0.2778 is a CLAIM (owner-reported); no
submission-page receipt exists in this repository.
**TOP_PUBLIC: unfilled by the human.** The README cites a leaderboard high of 0.4413
(fetched 2026-10-22); that is a cited number, not this session's target.
**Slots: 3 of 3 left this week, 0 used** (human, 2026-10-23).

## What this session established (evidence, not opinion)

* Rebuilt R0 from its recipe **pixel-exactly**: `H27-4-solo-d28` minus dots ≤ 2.0 px from the
  catalogue = the parent's 37,654 pixels. The container sha256 cannot be reproduced in this
  sandbox (different GDAL/zlib build) — IR-86-001.
* The parent keeps 1,611 dots (4.28 %) at 2.236 px from the catalogue, i.e. the brief's
  "≥ 3 px" rule removes 4.28 % of R0's mass whatever else is done — the mandatory exclusion,
  built as the control `prune3`.
* **The catalogue hide-and-recover proxy is structurally adversarial for this lineage.**
  R0 scores 0.004789 there and every variant scores 0.000000: the parent's entire proxy credit
  (378 of 5,470) comes from dots on the 2–3 px catalogue ring, which live scoring masks out.
  Do not read a proxy drop as a live drop. REPORT ONLY.
* **A ≤ 2 px snap has a non-positive expectation on this parent** (`evidence/snap_mechanism_model.json`).
  The parent's own back-solve gives credited mass M = 2,188 over n − F = 2,188 credited dots,
  i.e. k̄ = 1.00: the dots that earn anything already sit *on* truth. A dot on a 1-px trace
  cannot gain self-credit by moving; it can only lose it (perpendicular component). The only
  local measurements of the skill needed to beat that are the leakage canary (single-band AUC
  0.499–0.557 vs withheld catalogue positives ≈ uninformative) and the SGMC control (agreement
  with independently mapped faults *falls* monotonically: 0.1550 → 0.1515 → 0.1505 → 0.1479 as
  the moved fraction rises).

## The next three slots, in order

| # | File | What it tests | If it lands | If it does not |
|---|------|---------------|-------------|----------------|
| 1 | `releases/h33-h33-2-b2-prune3-20261023-175fefcf-zeros.tif` | **Attribution.** The mandatory ≥3 px exclusion and nothing else. | ≥ 0.2830 → the 2.236 px ring was costing real mass; PRUNE becomes the weekly axis. Positive but < 0.005 → the parent's +0.007 from 2 → 3 px was already harvested; SNAP must be judged against this baseline, not against 0.2778. | < 0.2778 → the ring was earning credit; every future variant must *keep* it and the ≥3 px rule must be re-negotiated with the organiser's masking behaviour. |
| 2 | `releases/h33-h33-2-b2-snapd2t20-20261023-f9c328a5-zeros.tif` | The assigned axis, least destructive setting: 7.32 % of dots move, mean 0.136 px. | Δ ≥ +0.010 → spend slot 3 on `snapd2t00` (98.5 % moved), the only version where the mechanism can express itself at scale. | |Δ| < 0.010 → **no evidence**, and by the brief's own rule SNAP is retired this cycle. Do not spend slot 3 on `snapd2t10`/`snapd2t00`; they are strictly more destructive (7.32 % → 19.17 % → 98.53 % moved). |
| 3 | Reserve — decide after 1 and 2 | Either `snapd2t00` (only if slot 2 is positive) or CONCENTRATION at matched count — note R0's 10 km block-density CV is **0.635**, *above* the 0.51–0.59 band the best files reportedly sit in, so the axis would have to *reduce* CV, not raise it. | | |

Slots 1 and 2 can be spent in the same week only if the human accepts that a SNAP result
below 0.01 is uninformative and slot 2 is a deliberate null test, not a bet.

## Weeks to deadline (6 weeks: 2026-10-23 → 2026-12-03)

* **Wk 1–2** — prune3 + snapd2t20 (above). One axis per session; record receipts.
* **Wk 3–4** — combine the two axes that survived with |Δ| ≥ 0.01; never combine two nulls.
* **Wk 5** — confirm the leader on the private chunks' likely behaviour (dot count, exclusion).
* **Wk 6** — choose one final file plus one fallback, re-validate both formats, do not touch
  the winner after the final submit.

## Axes I would assign next (mechanism · confounder · falsifier)

1. **PRUNE ≥ 3 px with rank refill** (highest prior support; R0's own history is +0.007 for 2→3 px).
   *Confounder:* the gain may be pure mass removal, not localisation — refill to a fixed count
   separates them. *Falsifier:* no live change at fixed count while the count-reduced twin gains.
2. **CONCENTRATION at matched count** (10–20 % of dots from the lowest-prior 10 km blocks to the
   highest). *Mechanism:* the metric pays per truth pixel, and truth concentrates along the
   known systems. *Confounder:* block density also encodes the footprint silhouette; measure CV
   after removing blocks with < 50 % footprint coverage (already implemented here).
   *Falsifier:* CV rises but live DTI falls — then density is not the active variable.
3. **SPACING / along-strike de-densification at matched count.** *Mechanism:* two dots 1 px apart
   credit the same truth pixels, so the second is pure false-positive mass; a Poisson-disk
   thinning at fixed n should raise T/FP. *Confounder:* thinning also removes the redundancy that
   protects against positional error (~300 m). *Falsifier:* nearest-neighbour separation rises
   while live DTI falls — redundancy is insurance here, and it should be *kept*.
