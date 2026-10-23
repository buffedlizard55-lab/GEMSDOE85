# Mechanism cards — PRUNE axis, parent R0 = `h33-h33-2-b2` (2026-10-23)

One card per variant, written for a structural geologist. The metric is a 300 m triangular kernel
(`k = max(1 − d/300 m, 0)`, 3 px) with α = 0.2 for wasted mass and β = 0.8 for missed truth
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). Organiser facts used
here (forum thread 11516, checked by the human 2026-10-22): known USGS/INGENIOUS fault pixels are
masked **pixel-exactly** and are score-neutral; the pixels *beside* them are scored against
**new-fault truth only**; and new-fault truth **can** lie within 300 m of known traces. Those three
sentences are the entire physical premise of this axis, in both directions.

---

## 1. `prune-x3-nofill` — delete the 2,171 dots at `2 < d_cat ≤ 3 px` (35,483 dots)

**Hypothesis.** The dot budget is a fixed 37,654-dot hypothesis set; dots that sit 200–300 m from a
mapped trace are, in this file, *pure false-positive mass* — their expected new-fault credit is below
the marginal bar `α·DTI ≈ 0.056`, so deleting them raises DTI by `DTI·αn/(D − αn) = +0.0062`.

**Mechanism.** A dot's cost is `α·(1 − max_g k)` against *scored* truth. Mapped catalogue pixels are
masked, so a dot parked on the flank of a known fault collects credit from nothing but an unmapped
fault inside 300 m. Fault-scarp colluvial wedges and potential-field upward continuation put the
ridge detector's maximum on that flank; the kernel is what turns a *detector* artefact into a
*scored* false positive. Removing the flank therefore removes cost without touching `T`.

**Non-fault process that could mimic it.** (i) Range-front shorelines, spring/travertine mounds and
playa margins parallel mapped faults at exactly this offset — deleting them is genuine FP removal and
would *inflate* the apparent benefit of the edit. (ii) A real second strand of the same system
(step-over relay ramp, 200–300 m across) is a genuinely new fault *pixel* under the organiser's
definition and would be deleted too, *deflating* it. The two biases act in opposite directions and
are indistinguishable from one live number — which is why rung 2's +0.0070 is treated as a *net*
measurement, not a purity proof.

**Predicted live change.** **+0.0062** (0.2778 → 0.2840), interval `[0.2820, 0.2860]`, `MODEL`
(the interval is the ±0.0005 rung-to-rung scatter in the per-dot cost, plus
the CLAIM-level uncertainty in 0.2778 itself, which no receipt in this repo can reduce).

**Falsifier.** Live ≤ 0.2778 (i.e. Δ ≤ 0 with 2,171 dots of pure mass removed) falsifies the model
that produced both earlier rungs: it would mean the ring's dots were *earning* more than their
0.2 tax, so the "new faults lie within 300 m of known traces" prior dominates at 3 px and the ladder
must stop. A live change between −0.01 and +0.01 is treated as **no evidence**, per the brief.

---

## 2. `prune-x3-pushout` — same deletion, each ring dot re-placed just outside 3 px (37,645 dots)

**Hypothesis.** The gain in card 1 is *proximity*, not *mass*: if the same hypotheses are moved
~1.4 px outward (median), they stop being catalogue-flank false positives and the file keeps its
budget. If instead the gain is mass, this file returns to ≈0.2778.

**Mechanism.** Same denominator arithmetic, opposite lever: `n` held, `T` held (the dot is on the
same local ridge, displaced < 2 px), so only the credit term can move. The displacement is radial —
away from the nearest catalogue pixel — because that is the direction in which the masked-truth
collar lies; it is *not* an edge snap (no new signal is used).

**Non-fault process that could mimic it.** A pushed-out dot can land in the same wedge/shoreline
belt it came from (mean displacement 3.2 px is dominated by a few 8–14 px fan fallbacks), in which
case it only re-labels the artefact. It can also land on the *other* flank of a narrow ridge, which
is real geology but displaced from the parent's hypothesis — this variant therefore cannot separate
"hypothesis was right, position was wrong" from "hypothesis was wrong".

**Predicted live change.** **≈0.000** vs R0 (0.274 → 0.283), `MODEL`. Deliberately a bracket, not a
candidate: 2,171 moved dots × 0.2 = 434 denominator units is the same tax whether they sit at 2.4 px
or 3.4 px.

**Falsifier.** ≈0.2840 ⇒ the ring is negative *wherever* it sits (proximity is not the mechanism; the
ring dots are simply wrong hypotheses) → slot 1 wins and the axis is spent. ≈0.2708 ⇒ the relocated
dots kept credit that their originals had, so the ring was *earning* and the prune is a coincidence of
mass. Also fails closed on count: 9 of 2,171 replacements found no free cell and were dropped
(37,645 vs 37,654 — 0.02 % mass confound, recorded rather than hidden).

---

## 3. `prune-x2-readd` — re-admit the 2,545 dots at `1 < d_cat ≤ 2 px` (40,199 dots)

**Hypothesis.** This is the **negative control**, not a candidate: it reproduces the support that
already carries a CLAIM of 0.2708, so a live score of 0.2708 ± 0.002 confirms that the scorer, the
chunk split and the ledger are still the ones the two rungs were measured on. Any other value
invalidates the calibration of cards 1–2.

**Mechanism.** Identical to card 1 with the sign reversed: put back exactly the 2,545 flank dots that
rung 2 deleted, encoded with zeros outside the footprint instead of NaN (the ledger records that NaN
and zeros twins score identically).

**Non-fault process that could mimic it.** If the public chunk set changed between October 4 and now,
this file's score moves for reasons that have nothing to do with dots; that is precisely the signal
the control is designed to expose.

**Predicted live change.** **−0.0070** (0.2778 → 0.2708), `[0.268, 0.273]`, `MODEL`.

**Falsifier.** Paying a slot for a known answer is only justified if the answer is *checked*: a score
outside `[0.268, 0.273]` means the ledger's CLAIM chain is not reproducible today, and every
prediction in `SLOT_PLAN.md` must be rescaled before the next slot is spent.
