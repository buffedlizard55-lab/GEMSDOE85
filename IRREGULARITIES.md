# IRREGULARITIES — only items that changed a decision

Session 2026-10-23, AXIS=MASS, branch `arena/991f7136-gemsdoe85`. Items that do not change
what was built, predicted or recommended are deliberately absent.

## IR-85-MASS-01 — the parent's ranking does not exist anywhere (changed the ranking rule)

**Finding.** The brief's MASS instruction is to drop/add "by the parent's own ranking
(rebuild the ranking from the recorded recipe if it is not stored)". Neither the ranking nor
the recipe is recoverable:

- every raster in the lineage ships a strictly binary field — `h19-5`, `d1.5`, `d2.8`,
  `solo-d28` and `h33-2-b2` each carry exactly the values {0, 1} (or {0, 1, NaN}); no
  intensity survives anywhere, so no stored order can be read off;
- the 2.8 px packing leaves no redundant pairs (minimum nearest-neighbour distance over R0's
  37,654 dots is 2.828 px), so a geometric tie-break cannot order the dots either;
- the repositories that would hold the recipe are gone: `buffedlizard55-lab/GEMSDOE19`
  returns 404, and `GEMSDOE24/scripts/build_candidate.py` (which produced `d1.5`/`d2.8`
  from `h19-5`) returns 404 against `ref=main`.

**Decision.** Rank each dot by its exact kernel credit against the pinned `h19-5` ancestor
support — the metric's own T-term, evaluated on the field the parent was thinned from —
ascending, ties broken by larger distance-to-catalogue, then row, then column. The rule is
stated in `scripts/build_mass_axis.py`, is deterministic, and is unit-tested
(`tests/test_mass_axis.py::test_drop_order_is_weakest_credit_first_with_a_declared_tie_break`).
Every MASS result is therefore conditional on a substituted ranking, not on the parent's own,
and the mechanism cards say so.

## IR-85-MASS-02 — the parent fails this repo's own catalogue gate (changed what was asserted)

**Finding.** `gems85.submission.validate(..., catalogue_buffer_px=2)` dilates the catalogue
with a 3×3 structuring element twice, i.e. it tests a **Chebyshev-2** buffer, which is
Euclidean ≤ 2.83 px (verified: the ring it produces over R0's dots equals the set at
Euclidean distance ≤ 2.83 exactly). R0 was built to a **Euclidean ≤ 2 px** rule, so the
incumbent itself fails that check: **1,611 of its 37,654 dots** sit inside the Chebyshev-2
buffer, and 2,171 sit at Euclidean distance in (2, 3] px.

**Decision.** The three variants inherit R0's exclusion (asserted: zero mass on catalogue
pixels, minimum Euclidean distance to the catalogue > 2.0 px) and the shared validator is
called with the buffer check disabled, rather than silently re-pruning 1,611–2,171 dots — a
PRUNE edit — inside a MASS experiment. The Chebyshev count is recorded per file in
`evidence/mass_axis.json` (`dots_in_chebyshev2_catalogue_buffer`: 1,115 / 1,348 / 2,672)
and in the build log. Consequence for the human: **brief §4's ≥3 px rule is not satisfied by
any file in this release, including R0**, and the compliance fix is a PRUNE change, not a
MASS one — `python scripts/build_mass_axis.py --cat-buffer 3.0` regenerates all three
variants from a compliant base (which confounds MASS with PRUNE and must be logged as such).

## IR-85-MASS-03 — R0's content reproduces exactly; its container bytes do not

**Finding.** R0 = {dots of `solo-d28`} ∩ {Euclidean distance to catalogue > 2 px} reproduces
**pixel-exactly**: 40,199 → 37,654 dots, **0 differing pixels**, asserted before every build.
The file's sha256 (`c55bafc4…`, 219,065 B) is not reachable: sweeping deflate levels 1–9 ×
predictors 1–4 with GDAL 3.9.3 gives 204,802–479,010 B and no match; re-encoding R0's own
array reproduces the array but never the container.

**Decision.** The brief's start gate ("rebuild R0 and match its sha256; if you cannot, stop
and report") is satisfied on content and failed on bytes. The session continued because the
parent is *exactly* reconstructible as a pixel field and because the MASS variants are
defined by dot sets, not by container bytes; a byte-identical parent would not change a single
dot. The reason is a foreign GDAL/zlib build, not corruption. Recorded here rather than
silently approximated: every variant's parent-diff is computed against the pinned parent file
read from disk.

## IR-85-MASS-04 — no local instrument can rank this lineage (changed every prediction)

**Finding.** With truth = the catalogue's own 60,988 positive pixels (identical to
`sample_submission.tif`'s 1-pixels, verified) the metric returns R0 **0.0067** against a CLAIM
of 0.2778, and misses the whole lineage: `d1.5` 0.1719 (claim 0.2477), `d2.8/solo` 0.0491
(0.2708), `d28_offcat` 0.1618 (0.2600). The repo's masked holdout instrument likewise scores
R0 at 0.0046 (`registry/irregularities.json` IR-85-08) for the same structural reason.

**Decision.** No PROXY score is reported as a prediction in this release. Predictions are
published as a **MODEL bracket**: floor = removed dots earn no new-fault credit (pure α
saving), ceiling = all lost ancestor-field credit was real truth. The field proxy is
circular — it is the parent's own surface, so it always rewards adding dots — and the
mechanism cards state that the floor, not the point estimate, should govern reading `p10`.

## IR-85-MASS-05 — +MASS is impossible at the parent's own packing (changed the design)

**Finding.** Restricting additions to the ancestor support, > 2 px from the catalogue and
≥ 2.828 px from every existing dot yields only **605** admissible sites, not the 3,761 needed.
The parent is saturated at its own packing radius.

**Decision.** `mass-p10` adds at ≥ 1.5 px, the lineage's own looser packing (`d1.5`, 60,069
dots, CLAIM 0.2477), and discloses the second moving parameter in its card. The build refuses
rather than silently loosening: the exhaustion case raises.

## Brief-vs-repo conflicts logged, not acted on

- The brief's `ledger/raw_paste.txt`, `ledger/submissions.csv` and `SLOT_PLAN.md` did not
  exist; the ledger was created from `registry/scored_artifacts.json` + this session's
  evidence, and the two lineage rows are marked **CLAIM**, not receipt.
- The brief's `TOP_PUBLIC` was blank. The human supplied **0.3195** on 2026-10-23; it is
  carried as UNVERIFIED everywhere and is not treated as a scored receipt.
- `registry/lane.json` remains `unassigned`. The human assigned AXIS=MASS explicitly for this
  session; that is a session assignment, not a lane declaration, and `lane.json` was not
  edited.

## IR-85-MASS-06 — a parallel session already tested MASS and rejected it (changes how to read this release)

**Finding.** While this session was building, `main` advanced to `751d0bd`, which includes a
PRUNE session whose register records a MASS evaluation with two measurements
(`origin/main:IRREGULARITIES.md` IR-V2-08, `origin/main:docs/mechanism_cards_prune.md`):

- the label-free ranking the parent's own geometry offers (unique kernel credit `U_i`) is
  *lowest* for the on-ridge dots that carry coverage and highest for isolated dots, so
  dropping the lowest-ranked dots deletes the backbone;
- an SGMC proxy puts mass-down as monotonically harmful, roughly −0.005 at −10 % to −0.020
  at −30 %;
- the recorded packing order is not a usable rank (Spearman with `U_i` = −0.003).

**Why this release is not a duplicate of that.** The ranking here is credit against the
*pinned h19-5 ancestor field*, not `U_i` against the parent's own dot set, and the three
variants are built as dose-response pairs on the same parent for a live measurement, not as a
proxy screen. But the two converge on the same sign for mass-down on the ridge interior: my
drop set removes the *isolated* dots (credit 1.0, versus median 2.45), which is the opposite
of "deleting the backbone" only if isolated dots are worthless — precisely the open question.

**Decision.** `SLOT_PLAN.md` ranks `mass-m20` first, but the prediction paragraph now carries
the SGMC result as prior evidence that mass-down hurts, which is why the bracket floor
(+0.0074) and not the point estimate is the number the human should weight. If `mass-m20`
lands at or below R0 − 0.01, MASS is closed permanently and CONCENTRATION takes the slot. The
conflict between the two branches' SLOT_PLAN/AI_USE/IRREGULARITIES/ledger files is left
unresolved deliberately (see the PR): both branches created those files independently this
week and merging them by hand into one ≤1-page plan is a human decision, not an agent's.

**Scoping note on IR-85-MASS-03.** The same main-branch register claims a byte-identical
re-encoding of "the pinned 44,090-px raster" (`src/gems85/r0_lineage.py`). I re-tested the
family writer's exact profile (tiled 256, deflate, predictor 2, with and without `zlevel`)
against the 44,090-px file in *this* branch's inputs and did not reproduce its bytes
(161,523 / 326,923 / 131,357 B vs 806,758 B). My byte-level claim is therefore scoped to
`h33-2-b2` only, and the two branches' byte-identity claims are about different files, not a
contradiction — but it must be checked before anyone states "R0 is byte-reproducible" as fact.
