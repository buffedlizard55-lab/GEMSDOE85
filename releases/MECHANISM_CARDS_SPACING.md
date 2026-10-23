# SPACING — same count, same mass, different arrangement (session 2026-10-23)

Parent **R0** = `h33-h33-2-b2`, 37,654 dots, **CLAIM 0.2778**. All three files keep the count at
**37,654** and keep unit mass per dot: only *where* the dots are changes. Every file passes the
17 local format checks, is re-read from disk, and has a `-nan` twin.

| id | change | count | positions changed |
|---|---|---|---|
| `spacing-infill10-20261023-f3b2aa49` | −3,765 lowest-credit dots, +3,765 trace-gap midpoints | 37,654 | 20.00 % |
| `spacing-infill20-20261023-7e1be53d` | same rule, double dose | 37,654 | 40.00 % |
| `spacing-fill10-20261023-93975107` | **ablation**: same −3,765, +3,765 at ≥2.0 px separation by marginal field credit, *not* in gaps | 37,654 | 20.00 % |

## The idea this axis was built to test

R0 is packed at ≥ 2.828 px. Along any trace the best credit a truth pixel can get therefore
alternates 1.0, 0.53, 0.0, 0.53 …: a truth pixel midway between two good dots earns
`k(1.41) = 0.53` however good those dots are. If that is the binding constraint, halving the
along-trace spacing should be almost free profit, because a dot that lands on real truth costs
`α(1−k) ≈ 0` in the denominator.

**Card: `spacing-infill10` / `spacing-infill20`.**
*Mechanism.* Remove the dots that carry the least unique credit (the 3,765 removed have field
credit ≤ 1.000, i.e. each is the sole cover of its own pixel) and spend the freed positions on
2.83–3.0 px dot pairs whose midpoint sits on the ancestor field — the exact sites where a
continuous trace would have a dot. Insertions have mean field credit **4.01** (4-fold
better-attested than what they replace) and sit a mean **1.31 px** from a parent dot.
*The non-fault process that could mimic it.* A midpoint between two field-mode artefacts is
still a midpoint; gap-filling sharpens whatever the pair already was. Aeromagnetic lineaments
at 400 m spacing put their positional uncertainty (≈ the kernel radius) exactly at this scale,
so "interpolating between two lineament picks" can refine a *noise* ridge just as well as a
fault.
*Predicted sign and size.* **Negative, from the metric's own bookkeeping, not from a proxy
opinion.** Coverage of the ancestor field *falls* 0.6334 → 0.6166 (infill10) and → 0.5969
(infill20): T drops 76,726 → 74,686 → 72,302 across the two files while the count is constant.
The reason is structural — a dot pays maximally where it is the *only* cover of a pixel
(credit ≈ 1.0), and a gap-filler by construction lands where two dots already give 0.53, so its
marginal T is ≈ 0.47 against an α cost it cannot avoid. MODEL: **−0.008** (infill10),
**−0.017** (infill20), both inside the no-evidence band.
*Falsifier.* A live **≥ 0.288** (+0.01) on infill20 kills the "isolates are worth their α
charge" reading and says the truth is line-like enough that trace continuity beats unique
coverage — which would make TRACKB the best Phase-2 investment. Anything ≥ R0 + 0.01 on
infill10 does the same at lower dose.

**Card: `spacing-fill10` (the ablation, and the only file here with a positive prediction).**
*Mechanism.* Identical removals, identical freed mass, identical pool; the only difference is
the placement rule — highest marginal field credit at ≥ 2.0 px separation instead of
midpoints. Insertions average 2.84 credit at 2.75 px displacement, 21 % within 2 px of a
parent dot. Coverage rises to 0.6444.
*Predicted sign and size.* **+0.005** (MODEL). The point of the file is not its own score: run
against `infill10` it is a controlled contrast of **0.013**, and that contrast — not either
file's score — is what separates "geometry matters" (infill wins) from "only marginal coverage
matters" (fill wins).
*Falsifier.* If `fill10` and `infill10` land within 0.005 of each other, arrangement at this
scale is irrelevant and the axis is exhausted; do not spend a third slot on spacing.

## What this session settled regardless of any slot

The packing-ceiling hypothesis is **false under the competition metric**, and the reason is
arithmetic rather than empirical: at fixed count, a dot's marginal T is largest where it is the
sole cover of a pixel, and a gap-filling dot is by construction never that. This is measured
here, not assumed (T falls by 2,040 and 4,424 for +3,765 and +7,530 gap dots).
