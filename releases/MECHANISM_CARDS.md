# MASS — one change per file, three files, one lineage

Parent **R0** = `h33-h33-2-b2` (GEMSDOE32), 37,654 dots, CLAIM 0.2778, sha256 `c55bafc4…`.
R0 is rebuilt here pixel-exactly from its two pinned inputs before every build
(`scripts/build_mass_axis.py --check-parent`: 40,199 → 37,654, **0 differing pixels**).
The container sha256 is **not** reproduced: R0's file was written by a different GDAL/zlib
build, so every deflate level and predictor I can emit lands on a different byte count
(204,802 / 213,248 / 230,434 B vs 219,065 B). The *content* is exact; the *bytes* are not.
`IRREGULARITIES.md` IR-85-MASS-03.

All three variants move **dot count and nothing else**: same grid, same footprint, same
unit mass per dot, same catalogue exclusion, every surviving dot inherits R0's position.
Changed fraction 10.00 %, 10.00 %, 9.99 % of R0's dots (the ±50 % band in the brief is met).

| id | change | n dots | sha256 (zeros) |
|---|---|---|---|
| `h33-2-b2-mass-m20-20261023-02204f67` | drop 20 % lowest-ranked | 30,124 | `02204f67…` |
| `h33-2-b2-mass-m10-20261023-719d2fb9` | drop 10 % lowest-ranked | 33,887 | `719d2fb9…` |
| `h33-2-b2-mass-p10-20261023-6ec5d841` | add 10 % next-ranked | 41,415 | `6ec5d841…` |

---

## Card 1 — `mass-m20` (30,124 dots)

**Hypothesis.** A fifth of R0's dots earn less new-fault credit than they pay in charge, so
deleting them raises DTI.

**Mechanism.** With `DTI = T/(α(T + n − M) + β|G|)`, dropping a dot with unique truth credit
`dt` and self-credit `k` subtracts `dt` from the numerator and only `α·(dt + 1 − k)` from the
denominator. Removal pays iff `dt < α·DTI·(dt + 1 − k)`, i.e. `dt < 0.0556` at DTI 0.2778
(`tests/test_mass_axis.py` pins both sides of that crossing). The 7,530 dots removed here
are the ones with the lowest kernel credit against the pinned h19-5 ancestor field — the
isolated fringe of the field, minimum credit exactly 1.0 (a dot alone in its own cell),
against a median of 2.45 and a max of 6.31.

**The non-fault process that could mimic it.** Fringe dots are exactly where a 400 m-spaced
aeromagnetic/lineament field decays into noise, so "low credit" and "no fault" are not the
same claim: the fringe is also where a *narrow* unmapped fault would produce a weak, isolated
positive. If that is what those dots are, this file destroys value at the same rate.

**Predicted sign and size.** Genuinely two-sided. Floor (removed dots carry no new-fault
truth): **+0.0074**. Ceiling (all lost field credit was real truth, circular field proxy):
**−0.081**. Modal outcome: still inside the brief's ±0.01 no-evidence band. If it lands
above +0.01 the fringe is worthless and the next step is a −30 %/ −40 % dose; if it lands
below −0.01, R0's mass is already below the optimum and the +MASS direction is confirmed.

**Falsifier.** A live score ≤ 0.268 (< R0 − 0.01) kills the redundancy mechanism for fringe
dots and forbids any further thinning of this lineage from the field-credit ranking.

## Card 2 — `mass-m10` (33,887 dots)

**Hypothesis.** Same mechanism at half the dose: the drop set is a strict subset of card 1's,
so the two files are a clean dose–response pair and not two independent bets.

**Prediction.** Floor **+0.0037**, ceiling **−0.040**. Because the two drop sets nest, the
pair measures the *shape* of DTI vs count near 37.7 k, which is what the plan needs; neither
number alone is worth a slot.

**Falsifier.** If `m10` and `m20` disagree in sign (one up, one down) the ranking is not
ordering value monotonically and the axis is exhausted — do not spend a third slot on it.

## Card 3 — `mass-p10` (41,415 dots)

**Hypothesis.** The 0.2778 file is under-dotted: the ancestor field still has uncovered
support (measured coverage of the h19-5 support is 0.633 with R0, 0.676 with this file), so
3,761 more dots can buy real credit cheaply.

**Mechanism.** Inverse of the removal bar: adding a dot pays iff its unique new truth credit
exceeds `α·(1 − k)`. Additions are the exact greedy max-coverage order (lazy greedy, exact
marginal kernel credit against the ancestor field), candidates restricted to the field
support, > 2 px from the catalogue, and ≥ 1.5 px from every accepted dot.

**Why the separation had to change.** At R0's own 2.828 px packing the pool holds only
**605** admissible sites — the parent's packing is essentially saturated at that radius. The
1.5 px radius is the lineage's own looser setting (the `d1.5` file, 60,069 dots, CLAIM
0.2477). This is the one place where a second parameter moves, and it is recorded as such.

**The non-fault process that could mimic it.** New dots go where the field is already dense,
so they mostly deepen existing clusters: they can raise `M` (credit already claimed by
neighbours) without raising `T`. That is the credit-saturation failure mode, and it is why
the predicted sign of the *marginal* dot flips negative well before 41 k.

**Predicted sign and size.** Point estimate (circular field proxy) **+0.020**; floor if the
added dots earn nothing **−0.0037**. The proxy is circular in the favourable direction here —
the field is the parent's own surface, so it rewards adding dots — which is exactly why the
floor, not the point, should govern how this file is read.

**Falsifier.** A live score ≤ R0 − 0.01 confirms saturation and retires +MASS permanently;
anything above R0 + 0.01 means the field, not the count, was the binding constraint.
