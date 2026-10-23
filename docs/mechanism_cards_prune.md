# Mechanism cards — PRUNE session, parent R0 (`h33-h33-2-b2`, 37,654 dots, live 0.2778 CLAIM)

Written for a structural geologist. One card per variant, plus two negative results that changed
what was built. Nothing here is a score; every number is labelled CLAIM / PROXY / MODEL.

---

## Shared setup: why catalogue-adjacent dots are the cheapest mass to give up

The metric is a distance-weighted Tversky index with α = 0.2 (false positives), β = 0.8 (false
negatives), triangular kernel R = 300 m = 3 px. Written as sums,

    DTI = T / (T + 0.2 (S − M) + 0.8 (G − T)),   T = Σ_truth max credit, S = Σ p, M = Σ p·max_g k

so a unit dot that lands on truth buys ≈ 1 of T; a unit dot that lands nowhere buys 0.2 of
penalty and 0.8 of missed-truth cost against it. The organiser's answer on the forum is the hinge:
published USGS/INGENIOUS pixels are masked pixel-exactly, "new fault" means a fault pixel those
sources do not carry, and new-fault truth may still lie within 300 m of known traces
(https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516,
https://community.drivendata.org/t/where-do-you-draw-the-line/11536).

Consequence: a dot *on* a known fault is the worst dot on the board. Under new-fault truth it can
never be a true positive (that pixel is masked out of the truth set), it sits far from any
*new*-fault pixel whenever the nearest new fault is >300 m away, and it still pays α = 0.2 of unit
mass. Its only value is the residual case the organiser allows: a genuinely new trace within 300 m
of the known one, which the kernel then partly credits.

The parent's own lineage is a two-point measurement of exactly this effect, both on the live
leaderboard (CLAIM, no receipt in this repository):

| step | dots | live | Δ |
|---|---|---|---|
| d2.8 packed ridge (`e56ea318`) | 44,090 | 0.2600 | — |
| − dots with d_cat ≤ 1 px (`8acb75e1`) | 40,199 | 0.2708 | **+0.0108** for −3,891 dots |
| − dots with d_cat ≤ 2 px = **R0** (`e5eb6e7e`) | 37,654 | 0.2778 | **+0.0070** for −2,545 dots |

Both steps are the same edit, in the same direction, with diminishing returns. The session's
decision rule is therefore: continue the rung, and find where it stops paying.

Why the shadow is wider than the map: GeoDAWN Area 2 was flown at 400 m line spacing, 150–200 m
above terrain (https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7), and published
USGS traces are offset from LiDAR-visible scarps by 100–400 m (1–4 px at 100 m) in this region —
the same offset class the GEMSDOE28 notes record. A dot at d_cat = 3–4 px can therefore still be
sitting in the *cartographic* shadow of a known fault rather than on an independent new one.

---

## Card 1 — `h33-2-b2-prune3-20261023-fb308615` (rung 3, 35,483 dots, −5.77 %)

- **Hypothesis.** The residual 2 < d_cat ≤ 3 px ring is still dominated by known-fault shadow,
  so removing it raises live DTI.
- **Mechanism.** 2,171 dots, each paying α = 0.2 of unit mass with a low probability of any
  new-fault truth inside 3 px; removing them cuts (S − M) by ≈434 mass units and removes at most
  the credit they gave to a *new* trace within 300 m — which is the small, deliberately admitted
  case. The ridge geometry they were covering stays covered: the 2.8 px packing rung leaves no
  backbone gap, only a wider flank.
- **Non-fault process that could mimic it.** A pure "delete mass" effect: any 5.8 % thinning would
  raise DTI if the parent were over-mass. This is *not* separable from PRUNE by this experiment
  alone; the MASS analysis below is why the dose ladder, not a random deletion, is the test.
- **Predicted live change.** **+0.007** (range +0.001 … +0.012) — MODEL, from the SGMC-minus-
  catalogue-3 px proxy (−0.0017 PROXY) plus the measured proxy→live bias of +0.0083 on the two
  known rungs. Any |Δ| < 0.01 live is *no evidence* (public chunks only).
- **Falsifier.** A live score ≤ 0.2778. Then the rung is exhausted at 2 px and cartographic shadow
  is not the controlling term; the ladder stops and the next slot goes to a non-PRUNE axis.

## Card 2 — `h33-2-b2-prune4-20261023-2880b0e9` (rung 4, 33,829 dots, −10.16 %)

- **Hypothesis.** The shadow is 100–400 m wide (1–4 px), so the gain continues at least one rung
  further, then decays.
- **Mechanism.** Same as card 1 over a wider annulus: 3,825 dots removed, 1,654 of them newly
  removed relative to rung 3 (the 3–4 px annulus). This is the dose that bisects the shadow-width
  claim rather than assuming it.
- **Mimic.** As card 1, plus the risk that at 4 px we start deleting dots that were the *only*
  coverage of a genuinely new, sub-parallel strand within 400 m of a known trace — geologically
  common in step-over zones.
- **Predicted live change.** **+0.003** (range −0.004 … +0.010) — MODEL from PROXY −0.0055 +
  bias. Strictly a decay test: if rung 4 ≈ rung 3, the shadow ends near 3 px; if rung 4 < rung 3
  but > R0, the optimum is bracketed.
- **Falsifier.** Δ ≤ 0 live, or a score *below* prune3. Then the optimum sits at rung 3 and the
  session's best file is prune3.

## Card 3 — `h33-2-b2-prune5-20261023-7ebfc408` (rung 5, 32,017 dots, −14.97 %)

- **Hypothesis.** Spent only if cards 1–2 both pay: the shadow reaches 5 px (500 m), i.e. beyond
  the documented USGS-vs-LiDAR offset class.
- **Mechanism.** 5,637 dots removed (15 %), 1,812 of them in the 4–5 px annulus. At this width the
  edit stops being "remove the offset shadow" and becomes "desertify a 500 m collar around the
  whole published inventory" — which necessarily includes real, unmapped, sub-parallel strands.
- **Mimic.** Exactly the same edit done by someone who simply wants fewer dots: at 15 % the mass
  term alone is large, so a positive result here could be a MASS effect.
- **Predicted live change.** **−0.003** (range −0.012 … +0.006) — MODEL from PROXY −0.0108 +
  bias; i.e. we predict it is the *first* rung that overshoots.
- **Falsifier.** A live gain ≥ +0.005. Then the shadow is wider than documented, and the next
  session should sweep rungs 5–8 before anything else.

---

## Negative result 1 — the MASS arm as specified is not supported (do not spend a slot)

The session brief's first choice of axis was MASS (drop/add the lowest/highest-ranked 10 %). Two
independent checks say the parent is already near the mass optimum, and that a label-free ranking
cannot identify the dots worth dropping:

1. **Ranking is anti-correlated with value.** The exact label-free ranking available from the
   parent's own geometry is the unique kernel credit U_i (the credit a dot supplies and no other
   kept dot supplies; `src/gems85/r0_lineage.py`). It is *lowest* for dots packed along ridges
   (U ≈ 4.35 at the 2.83 px rung) and highest for isolated dots (U ≈ 9.38). The lowest-U 10 % are
   therefore the on-line dots — precisely the ones that carry the truth coverage. Dropping them
   by U is the worst available deletion rule.
2. **The proxy says mass-down hurts, monotonically** (SGMC truth, PROXY): −0.0048 at −10 %,
   −0.0112 at −20 %, −0.0196 at −30 %. The recorded packing priority (raster-order acceptance) is
   useless as a rank — Spearman with U is −0.003, and it is spatially biased toward the ends of
   components.

MASS stays on the `SLOT_PLAN.md` proposal list only with a *different* mechanism (exchange, not
deletion); it is not built this session.

## Negative result 2 — "refill to hold the count" is impossible at this rung (measured, not argued)

The brief's PRUNE definition asks to refill to the parent's count. Measured capacity of the parent's
own residual ridge, restricted to d_cat > rung and to the same 2.8 px packing rung
(`evidence/session_prune_receipt.json → refill_capacity`):

| rung | dots removed | off-catalogue ridge candidates | accepted at 2.8 px |
|---|---|---|---|
| 3 | 2,171 | 611 | **475** |
| 4 | 3,825 | 577 | **437** |
| 5 | 5,637 | 469 | **350** |

The parent already saturates its own emission at r = 2.8 px: 77,041 of the 121,131 skeleton pixels
were rejected by the packer as too close to an accepted dot, so there is nowhere off-catalogue to
put the mass back without either tightening the rung (a SPACING change) or inventing detections
(a new hypothesis, and the ledger says additions have repeatedly failed live: T-v2's 1,259 dots
earned +2.65 px of credit, live −0.0028). Holding the count would therefore have required a second
change, contaminating the axis. All three variants are pure removals, 5.8–15.0 % of R0.
