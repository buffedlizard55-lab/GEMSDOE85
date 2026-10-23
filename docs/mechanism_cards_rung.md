# Mechanism cards — session 3 · AXIS = PRUNE (fractional cup-distance rungs)

Parent for every variant: **R0 = `h33-h33-2-b2`** (`e5eb6e7e`, 37,654 unit-mass dots, live
**0.2778 = CLAIM**, owner-reported, no receipt in this repository). Every card is written for a
structural geologist who has to decide whether to spend one of three weekly slots on it.

Shared reading of the metric (exact, `src/gems85/metric.py`):

    DTI = T / (0.2·T + 0.2·(S − M) + 0.8·|G|)

with `T` the kernel credit actually delivered, `S` the emitted mass (37,654 at unit density),
`M` the mass that lands within the 300 m kernel of truth, `|G|` the new-fault truth. A dot that sits
on masked catalogue pixels, or in the 300 m ring around them, can still pay `T`, but the pixels it
covers there are **not truth** — the organisers mask the known USGS/INGENIOUS faults pixel-exactly —
so most of its credit is collected on a surface that can never be counted. That is the shadow this
axis removes.

---

## Card 1 — `r2p25`: drop the √5 ring (d_cat ≤ 2.25 px, 941 dots, −2.50 %)

* **Hypothesis.** The first ring of dots that R0 still carries — the eight cells at
  `(±1,±2)/(±2,±1)`, i.e. 224–250 m from a mapped trace — is the part of the 2–3 px rung that the
  previous session's `prune3` value bundled with two farther rings. Removing only this ring tests
  whether the shadow gain is a *near-field* effect (map-vs-imagery offset of one to two pixels) or a
  *far-field* one.
* **Mechanism.** Mapped trace geometry is digitised at reconnaissance scale and is offset from the
  geomorphic trace by up to 2–4 px in places; the GeoDAWN Area 2 survey flew 400 m line spacing with
  150–200 m clearance, so a lineament's *position* is uncertain by about the kernel radius
  (https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7). A dot inside the 3 px
  kernel of a mapped trace can therefore be either (a) the same fault, whose pixels are masked and
  therefore unscorable, or (b) a genuinely new, unmapped splay. This card removes only the tightest
  version of (a).
* **Non-fault process that could mimic it.** Any *parallel* geomorphic feature that follows a mapped
  fault at a constant small offset — a fault-line scarp degraded to a younger surface, a shutter
  ridge, or a vegetation lineament on the down-thrown block — sits in exactly this ring and is not a
  fault. Removing these dots cannot hurt; keeping them cannot help.
* **Predicted sign and size.** Positive, small: **+0.003 (−0.003 … +0.009) MODEL**. A null result
  here while `prune3` gains would place the shadow's centre of mass in the 2.8–3.6 px rings.
* **Falsifier.** Receipt ≤ 0.2778 while `prune3` also scores ≤ 0.2778 kills the shadow mechanism
  outright; a receipt ≤ 0.2778 *with* `prune3` above it means the near ring is load-bearing (new
  faults sit preferentially within 250 m of known traces, exactly as the organisers warned).

## Card 2 — `r2p85`: drop √5 + 2√2 rings (d_cat ≤ 2.85 px, 1,611 dots, −4.28 %)

* **Hypothesis.** The 2.83 px ring (`(±2,±2)`, 283 m) is the **inner edge of the kernel**, where a
  dot's own 3 px disc still overlaps the masked trace by ~6 %. If the shadow is a kernel-geometry
  effect rather than a mapping-offset effect, the gain should already be ~74 % of the `prune3` gain
  at 74 % of its dot count.
* **Mechanism.** DTI's triangular kernel makes credit fall linearly with distance; a dot at 2.83 px
  from a mapped trace contributes almost nothing that is *not* already masked, while still paying
  0.2 of unit mass in the false-positive term everywhere it is not near truth.
* **Non-fault process that could mimic it.** A real, unmapped **sub-parallel splay within 300 m of
  the master fault** — the commonest structure in the Basin and Range — lives in this ring, and the
  organisers have said in terms that new-fault truth *can* lie within 300 m of known traces
  (https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516).
  This is the strongest counter-mechanism on the axis and the reason the dose must be measured, not
  assumed.
* **Predicted sign and size.** Positive, **+0.005 (−0.002 … +0.012) MODEL**; the interval's lower
  half covers the splay counter-mechanism.
* **Falsifier.** `r2p85` scoring below `r2p25` while both are above R0 reverses the monotone dose
  reading and says the 2.83 px ring is where real unmapped splays live.

## Card 3 — `r3p61`: drop rings up to 3.61 px (3,361 dots, −8.93 %) — brackets `prune3`

* **Hypothesis.** `prune3` (2,171 dots, d_cat > 3) sits between this variant and `r2p85`. If the
  optimum is *past* 3 px, `r3p61` ≥ `prune3` and the ladder should be extended; if it is *at* 3 px,
  `r3p61` < `prune3` and the previous session's single-peaked model is confirmed by an independent
  bracket.
* **Mechanism.** Same shadow; this card adds the 3.0, 3.16 and 3.61 px rings (531 + 659 dots at
  3.16/3.61 px, still inside or at the kernel edge), and is therefore also the cheapest test of
  whether the effect saturates at the kernel radius or extends to the 400 m (4 px) rung that
  `prune4` already encodes.
* **Non-fault process that could mimic it.** At 3.6 px a dot is outside the kernel of the mapped
  trace altogether, so the only way it loses value is by occupying the 300 m ring *between* two
  mapped traces — i.e. an unmapped connecting fault, which is a real and common structure. This card
  has the most to lose if that population is real.
* **Predicted sign and size.** **+0.005 (−0.004 … +0.014) MODEL** — deliberately wide and centred
  below `prune3`'s published +0.007.
* **Falsifier.** A receipt **above** `prune3` by ≥ 0.005 (i.e. a *larger* prune scoring better) is
  the single most informative outcome available this week: it says the shadow extends past the kernel
  radius and the next session should sweep 4–8 px with the same fine spacing.

---

## Why the other axes were not built this session (measured, not argued)

| axis | measurement against R0's own geometry | verdict |
|---|---|---|
| SNAP | R0 is a **saturated** 2.8 px Poisson-disk packing of a 1-px skeleton: at a separation floor of 2.8, 2.4 or 2.2 px, **0 of 37,654 dots** have a free destination cell within 2 px. Relaxing to 2.0 px makes radius-2 snapping possible (18,065 dots, 48 %) but costs 1.2 % of the parent's unique kernel credit and lowers the SGMC proxy from 0.0954 to 0.0926. | infeasible at fixed packing; inadmissible as a one-axis edit |
| CONCENTRATION | Free skeleton cells exist (794 in the whole footprint, 26 in the top-prior 1-km tercile at d_cat > 3 px, 205 at d_cat > 2 px). Block-density CV of R0 is **1.874** (1-km blocks, fully covered blocks only) and density is uncorrelated with the km-scale prior (Spearman −0.023). | no destination capacity → would become an off-ridge *addition*, a different axis already falsified live |
| RELIEF | same capacity limit as CONCENTRATION; the tercile shift is a relocation by definition | infeasible |
| MASS (up) | refill capacity at the parent's rung was measured last session at 475 dots vs 2,171 removed | infeasible |
| SPACING | would have to re-thin the skeleton, i.e. change the count — that is the previous session's dose ladder, not a new axis | deferred |

All numbers: `evidence/session_rung_receipt.json` → `axis_feasibility`, `snap_probe`,
`block_density_cv_parent`.
