# IRREGULARITIES — only items that change a decision

Session `arena/fe618e6b-gemsdoe85`, 2026-10-23. Earlier repo-level irregularities stay in
`registry/irregularities.json`; nothing here duplicates them.

## IR-85-101 — the parent's ranking does not exist in any published artifact (blocks MASS)

**Finding.** Every raster in the lineage is binarised: `h19-5` (121,131 px), `d2-8` (44,090),
`solo-d28` (40,199) and R0 (37,654) each contain exactly **two distinct values** (0 and 1) — verified
today on the pinned bytes. The continuous score field, the persistence measure and the selection order
that produced the three prune rungs were never published, and no script in this repo reconstructs
them.

**Decision it changes.** (a) This session's refill had to be defined *without* a ranking (see
`docs/MECHANISM_CARDS.md` card 2). (b) A future `MASS` session **cannot** "drop the lowest-ranked 10 % /
add the next-ranked 10 % by the parent's own ranking" from what exists: it must either rebuild a
continuous ranking from a pinned script (none located) or declare a new ranking, which makes it a
different mechanism, not a MASS test. Do not spend a MASS slot until a ranking is published or rebuilt.

## IR-85-102 — "refill to hold the count" is not satisfiable from the parent's own support

**Finding.** At the parent's own 2.828-px Poisson separation, only **474** of the 2,171 needed
replacement dots fit on the H19-5 ridge outside 3 px (`evidence/prune_variants.json`,
`refill_pool_shortfall`). The field is saturated at 37,654 dots: any larger refill from that pool is
redundant mass inside an existing dot's 3-px kernel, i.e. pure denominator.

**Decision it changes.** The `x3-refill` variant the brief prescribes as "delete then refill to hold
the count" was **not built as written**; it is built as `x3-pushout` (each deleted dot re-placed just
outside 3 px), which holds the count without inventing new dots. If a future axis needs a genuine
refill, it needs a *different* physical signal, not more of this one.

## IR-85-103 — the catalogue hide-and-recover PROXY is degenerate for every exclusion-compliant file

**Finding.** With a 3-px buffer on the withheld components, every dot that respects the ≥3 px
catalogue exclusion is at distance ≥ 3.0 px from every withheld positive, and `k(3.0) = 0`. Both
`x3` variants therefore score a **structural 0.0000** PROXY (tp_w = 0 exactly), not a low score. Only
`x2-readd` (dots at 1.4–2.0 px) registers: 0.0282, CI `[0.0278, 0.0283]`, n = 11,321 withheld
positives.

**Decision it changes.** The PROXY cannot rank any exclusion-compliant file against another, so it
must not be quoted as evidence for or against this axis (nor against `H85-GAPVENT`, whose 0.14232 is
measured on a *model-recovered* surface, not a dot field). It stays REPORT ONLY.

## IR-85-104 — every score this axis rests on is CLAIM, and the chain has a single point of failure

**Finding.** `registry/scored_artifacts.json` states that all 17 scores are owner-reported and no
DrivenData receipt is reproduced anywhere in the repo. The prune ladder's two rungs (0.2600 → 0.2708
→ 0.2778) and the whole `T ≈ 5,470` calibration are therefore CLAIM-level. The brief's §2 requires a
receipt in `ledger/` before 0.2778 is called anything but CLAIM.

**Decision it changes.** `prune-x2-readd` exists so the chain can be *checked* with one slot if the
human chooses; `ledger/submissions.csv` keeps `receipt_score` / `receipt_date` empty for the human to
fill **from the submission-page receipt**. No file in this repo is described as having a score.

## IR-85-105 — the trajectory docs overstate one number (39,000-px error)

**Finding.** `docs/research/why-02778-and-how-to-beat-04413.md` presents the lineage as
121,131 → 60,069 → 44,090 → 40,199 → 37,654, folding the `d1.5` thinning (60,069, a *separate*
branch scored 0.2477) into the branch that actually leads to R0. The branch that leads to R0 is
121,131 → 44,090 → 40,199 → 37,654, and the two prune rungs removed 3,891 and 2,545 dots — the
per-dot costs agree to 7 % (2.57e-6 vs 2.75e-6), which is what makes the third rung predictable.

**Decision it changes.** Predictions in `SLOT_PLAN.md` use the corrected lineage and the corrected
per-dot identity. The site text is untouched (no site redesign this session); a future docs pass
should fix it before the number is quoted to anyone outside the group.

## IR-85-106 — `(parent, axis, value) = (h33-2-b2, PRUNE, x3)` was already merged on `main` (do not double-spend)

**Finding.** While this branch was being built from `e990711`, `main` advanced to `ea2e72e`
(PR #38, 281 files). That PR already contains the same axis on the same parent, including
`releases/h33-2-b2-prune3-20261023-fb308615.tif` — "drop 2,171 dots at `2 < d_cat ≤ 3 px` →
35,483 (5.77 %)". That is **the same edit as this session's `x3-nofill`** (same deleted set, same
count, same percentage), plus `prune4`, `prune5`, `r3p61`, a `prune3fill20` refill, three RELIEF
files and three SNAP files, with its own `SLOT_PLAN.md`, `ledger/submissions.csv` and a
`scripts/build_prune_variants.py` **of the same filename as this branch's**.

**Why the duplicate happened.** This branch's tree had **no `ledger/` directory at all** and no
`SLOT_PLAN.md`; the instruction "check the ledger first" could not be satisfied from the checkout
that was available, and the merged session landed after this branch point.

**Decision it changes.**
1. **Do not spend two slots on both `prune3` files.** They are the same physical edit; upload at most
   one (main's `fb308615` already has a PLAN entry, so prefer it unless the human prefers this
   branch's container/validation receipts).
2. This branch's **PR #41 must stay open, not merged**: it conflicts with `main` on `SLOT_PLAN.md`,
   `ledger/submissions.csv`, `scripts/build_prune_variants.py` and `docs/MECHANISM_CARDS.md`
   (main keeps its cards at `evidence/v2-prune-mechanism-cards.md`), and merging it would fork the
   ledger that the other session's plan depends on. The human chooses which ledger/plan survives.
3. What remains genuinely **new** here and is worth porting by hand:
   - the **count-held push-out** variant (`x3-pushout`, 37,645 dots) — displaces the ring rather than
     deleting it, so it separates *proximity* from *mass*; main's `prune3fill20` refills from a
     different pool and does not do this;
   - **IR-85-103**: the catalogue PROXY is structurally **0.0000** for *every* exclusion-compliant dot
     file (`k(3.0) = 0`), which means main's `+0.0085` "off-catalogue SGMC PROXY" claim and any other
     dot-file proxy comparison need the same caveat;
   - the **rung-to-rung identity check** (7 % scatter in per-dot cost, `T ≈ 5,470`) and the
     **`x2-readd` negative control** that can validate the whole CLAIM chain with one slot;
   - **IR-85-101** (rankings are unrecoverable — blocks a `MASS` session) and **IR-85-102**
     (refill-to-count is unsatisfiable from the parent's own support).
