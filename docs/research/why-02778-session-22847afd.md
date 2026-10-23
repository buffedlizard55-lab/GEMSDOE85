# Why h33-h33-2-b2 scored 0.2778 — PhD-level answer, verified line by line this session

Artifact: `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, sha256
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`
(restored 2026-10-22 from the GEMSDOE32 mirror and hash-verified against
`registry/scored_artifacts.json`). Score 0.2778 is **OWNER-REPORT** (operator ledger;
no DrivenData receipt is reproduced in this repo — IR-85-04). Leaderboard high 0.4413 is
a **PUBLIC-LEADERBOARD-OBSERVATION** with no file/hash crosswalk.

## The mechanism, each step measured from bytes this session

1. **One field, five budgets.** `h33 (37,654 dots) ⊂ h27-4 (40,199) ⊂ d2.8 (44,090) ⊂
   h19-5 support (121,131 px)` — verified pixel-exactly: 100.0 % of h33 dots lie on
   h19-5 support pixels. The live cascade 0.1922 → 0.2477 → 0.2600 → 0.2708 → 0.2778 is
   the *emission budget* of one multi-physics corroborated-ridge field being tuned, not
   five geological discoveries. Field quality sets the ceiling; thinning cashes it in.
2. **The metric is a budget.** Official DTI (DrivenData #306 problem page): triangular
   300 m kernel, α=0.2, β=0.8, equivalently `DTI = T / (0.2·(T+F) + 0.8·K)`. A second dot
   within the kernel of an already-covered truth pixel earns ≈0 new `T` but pays the
   full 0.2 mass tax. Poisson thinning at ≈2.8 px removes exactly that waste. A dot is
   worth adding iff its realised credit exceeds `0.2·DTI/(1−0.2·DTI)` = **0.0588 at
   0.2778** (0.0969 at the leader's 0.4413).
3. **The B2 halo prune is free money.** The live truth is faults *absent* from the USGS
   catalogue (official "Competition structure"). Dots ≤2 px from a mapped fault sit
   almost entirely on already-known structures: measured live effect +0.0070 for
   deleting 2,545 such dots. h33 has 0 dots ≤2 px from the catalogue (median distance
   to catalogue 19.6 px, measured this session).
4. **Binary amplitude is provably optimal** (ratio of affines ⇒ endpoint optimum), and
   the **all-finite zeros encoding** cannot trip the portal's `[0,1]` check.

Two-point algebra on the controlled pair (0.2708 at 40,199 → 0.2778 at 37,654, same
field, only catalogue-proximal dots deleted) implies captured credit `T ≈ 5,470` and
hidden-truth mass `K ≈ 14,400 px` (~144 km of trace), i.e. ≈0.145 credit per dot, ~5× a
uniform-random dot, with ~94 % of dots earning nothing. h33 is not a good *map*; it is
a well-priced *bet* on a strong field. (Derivation and assumptions:
`docs/research/metric-algebra.md` §5; `K` depends on the stated `M ≈ T/2.5` assumption
and is labelled a model, not a measurement.)

## Can a new submission beat 0.2778? What it would take

- **Not by re-thinning h19-5.** The cascade's marginal gain has flattened (+0.007 for
  the last 2,545 deletions); a power-law fit to the family's own `T(n)` puts the
  re-emission ceiling ≈0.280. And re-emitting that field is prohibited here anyway:
  >70 % of dots would fall within 3 px of h33's (parallel-run protocol §1).
- **Only by credit-per-dot.** At 37,654 dots, beating 0.2778 needs mean realised credit
  >0.145/dot; matching 0.4413 needs ≈1.64× that, or the same credit-per-dot sustained
  to ~100 k dots. Both are statements about the *field's top-ranked pixels*, not about
  packing.
- **Where new credit can plausibly come from.** The hidden set was mapped by experts
  using the same GeoDAWN/LiDAR data participants have. Fault classes a scarp-first
  catalogue under-maps but experts can still trace: (a) along-strike continuations and
  relay links under cover (network incompleteness — this session's RELAY lane);
  (b) concealed juxtapositions with small per-band but large joint-vector steps
  (GEO-Pb lane); (c) line-context patterns a per-pixel classifier cannot see
  (contextual supervised lane). Fleet live evidence that independent geometry carries
  credit: tip/stepover analog 0.2632 and orthogonal-gated 0.2376 (OWNER-REPORT), the
  latter sharing only 42 % of h33's 3-px neighbourhood (measured this session).
- **What cannot be done honestly:** proving a live beat locally. The catalogue holdout
  cannot reward a fault no one has mapped, and it *structurally penalises* catalogue-
  proximal geometry (whole blocks are withheld). It is a screen for skill over chance
  and controls — the gate this session pre-registered — not a live predictor. Any
  claim stronger than that would be a hallucination.
