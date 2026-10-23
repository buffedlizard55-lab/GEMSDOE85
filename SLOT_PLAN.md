# SLOT_PLAN — GEMSDOE85, session 2026-10-23 (AXIS = MASS)

One entity, 3 scored submissions per rolling week, one final file, deadline **2026-12-03**
(confirm on the competition page — not re-checked here; DrivenData is not fetched from this
sandbox). Slots left this week: **3 / 3** (human-supplied 2026-10-23).
Target: **TOP_PUBLIC = 0.3195** — UNVERIFIED, supplied by the human from an earlier repo
prompt, not a receipt. Parent: **R0 = h33-h33-2-b2, CLAIM 0.2778**.

## What this session established (and what it costs you to ignore)

1. **No local instrument can rank this lineage.** Scoring R0 against the catalogue's own
   positive pixels (the only truth in this repo) gives **0.0067** against a claimed 0.2778;
   the same test misses every ancestor by 0.05–0.27 (D1.5 0.172 vs 0.248, d2.8 0.049 vs 0.271,
   d28_offcat 0.162 vs 0.260). The live truth is therefore *new* faults with the catalogue
   masked, exactly as the forum says — so every prediction below is a bracket from the metric
   algebra plus the ledger's confounded slope, never a proxy score.
2. **The ledger's apparent "less mass is better" (+0.0028 per 1,000 dots removed, twice,
   independently) is a PRUNE effect, not a MASS effect.** Both steps that produced it removed
   dots *by distance to the catalogue*, where credit is structurally zero and the α charge is
   pure loss. The MASS variants remove dots by *field credit*, which does not carry that
   free lunch. Anyone extrapolating the slope onto MASS will over-predict by a factor of 2–3.
3. **R0 is already at its own packing limit** (2.828 px; 605 free sites remain), so +MASS is
   only achievable at a finer spacing — a second parameter that `mass-p10` moves deliberately
   and discloses.

## The next three slots, in order

| # | file | why this one, and what the result buys |
|---|---|---|
| 1 | `h33-2-b2-mass-m20-20261023-a6075d2f` (30,124 dots) | Largest single test of the only mechanism in this family that has ever produced a positive live delta (denominator shedding). Bracket [−0.081, +0.0074]. **If ≥ 0.288** (+0.01): the field fringe is worthless → go to −30 %/−40 % and stop touching the +MASS direction. **If ≤ 0.268**: fringe dots carry real faults → R0's count is at or below optimum, and the axis is closed. Anywhere in between: no evidence, and slot 2 should skip MASS. |
| 2 | `h33-2-b2-mass-p10-20261023-82aa483f` (41,415 dots) | The only file that can falsify "saturation". Predicted −0.0037 to +0.020; **≤ 0.268 retires +MASS permanently**, ≥ 0.288 says the field's coverage, not its count, was binding. Pair it with slot 1: together they bracket the optimum to a ±10 % window. |
| 3 | `h33-2-b2-mass-m10-20261023-a296bbd1` (33,887 dots) | Use **only** if slot 1's result was inside ±0.01 (then m10 is the cheapest dose–response point, nested inside m20, and tells you whether the effect is monotone near 37.7 k). If slot 1 was decisive, **do not spend slot 3 on MASS** — spend it on CONCENTRATION at fixed count, which is the one axis with a reported empirical optimum (block-density CV 0.51–0.59) that this lineage has never tested at constant mass. |

Fallbacks are already built: each variant ships a `-nan` twin with identical content, so a
rejected upload costs a minute, not a slot.

## After this week

- **Week 2:** if MASS moved ≥0.01, combine it with the winning mass in one file (MASS ×
  CONCENTRATION); if it did not, drop MASS from the plan and spend the three slots on
  CONCENTRATION (2 values) + PRUNE ≤3 px with refill (1 value).
- **Weeks 3–4:** SNAP (2 px displacement toward the TMI/gravity-gradient maxima, same count)
  and RELIEF (basin/piedmont/range-front mass shift) — both already specified, neither built.
- **Weeks 5–6:** re-validate the format of the two best files, pick the final file and its
  fallback, and confirm the deadline on the competition page.

## Axes I would propose instead (not built this session, per the brief)

1. **CATFLANK** — mass *at 3–6 px from the catalogue* only. Mechanism: the algebra says a dot
   pays iff its credit `k > 0.2·DTI` (0.056 → 2.83 px), so the 1.5–3 px ring is the only place
   where catalogue-adjacent credit is *free* on the new-fault side. Confounder: the same ring
   is where a mapped fault's damage zone sits, and the mask may extend. Falsifier: no change
   when the ring is doubled.
2. **DOSE** — a 5-point count ladder (25 k → 45 k) on one field, one slot per point over two
   weeks. Mechanism: this session shows the family's response curve has never been measured at
   constant field. Confounder: spacing must be held fixed, which the 2.828 px saturation
   forbids above 37.7 k without re-packing. Falsifier: a flat curve.
3. **PURITY** — replace field-credit ranking with a *precision* ranking (local field coherence
   at 400 m, the survey's own resolution limit). Mechanism: the brief's resolution fact says
   lineament positions are uncertain by about the kernel radius, so sub-kernel structure is
   noise. Falsifier: PURITY and MASS deltas identical.

## What the human must supply before any slot is spent

`TOP_PUBLIC` with a date and a leaderboard citation; slots-left confirmation on the day of
submission; and the receipt (score + date) pasted into `ledger/submissions.csv` after each
upload. `receipt_score` / `receipt_date` are deliberately empty in this repo.
