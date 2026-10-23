# Mechanism cards — PRUNE axis on R0 (h33-h33-2-b2), 2026-10-23

Audience: structural geologist. Evidence labels per brief §8. Live deltas in the
lineage (0.2600 → 0.2708 → 0.2778) are **CLAIM** (owner-reported; no receipt in
`ledger/`). Predicted changes are **MODEL**. Hide-and-recover/SGMC numbers are
**PROXY**, report-only. A live change <0.01 is no evidence (brief §5).

Shared background. R0's dots are a 2.8 px-spaced thinning of the H19-5
multi-line (magnetic/gravity/topographic ridge) detector support, then pruned
twice by catalogue distance (≤1 px, then ≤2 px; both steps pure removals).
GeoDAWN Area 2 was flown at 400 m line spacing, 150–200 m above terrain
(https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7), so a
buried range-front fault produces a potential-field gradient zone several
hundred metres wide, and its mapped trace can sit anywhere inside it.
Metric: DTI, triangular kernel R=300 m (3 px), α=0.2/β=0.8
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
Catalogue pixels are masked pixel-exactly; new-fault truth *can* lie within
300 m of known traces, and "new" includes new geometry of existing systems
(https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516,
https://community.drivendata.org/t/where-do-you-draw-the-line/11536; organizer
statements as supplied in the brief, not re-fetched this session).

## V1 `pruneD3pure` — remove every dot with d_cat ≤ 3 px (35,483 dots; −2,171; 5.77%)

- **Hypothesis.** R0 dots 200–300 m from a mapped trace mostly re-detect that
  same fault (second edge of its gradient zone, damage-zone fracture fabric
  parallel to the master strand) and cannot earn credit against masked
  catalogue truth; deleting them raises DTI, as the ≤1 px and ≤2 px removals
  did (CLAIM +0.0108, +0.0070 respectively).
- **Mechanism.** A dot pays iff its kernel credit from *new* truth beats the
  α-charge (bar ≈0.2·DTI ≈ 0.056 credit at 0.28 for isolated truth). Inside
  one kernel radius of a known trace, the detector's response is dominated by
  the known structure's own flank, so P(new truth within 300 m of the dot,
  closer to it than to any other dot) is low; the two previous rings behaved
  exactly this way (near-constant CLAIM gain ≈ 2.76e-6 per dot removed).
- **Non-fault mimic / counter-mechanism.** Genuine parallel synthetics,
  antithetics, relay/step-over strands and unmapped splays of known systems
  *do* live 200–300 m off mapped traces (organizer confirms such truth is
  scored). If the ring dots sit on those, pruning removes earners. Also, the
  mapped trace's own positional error (~kernel radius) means some "flank"
  dots may be *on* the true fault while the catalogue line is offset.
- **Predicted live change.** **+0.006 (MODEL)**, plausible range −0.006…+0.014
  (linear per-dot extrapolation of the two CLAIM steps; ring is one step
  farther from the trace, so diminishing returns are expected). In
  expectation this is below the 0.01 evidence threshold.
- **Falsifier.** Receipt Δ ≤ −0.01 vs R0: the 2–3 px ring earns its keep
  (parallel new geometry dominates) and the flank mechanism stops at 2 px.
  Δ ≥ +0.01 supports continuing to test larger radii / adopting ≥3 px as the
  standing exclusion. |Δ| < 0.01: no evidence either way.

## V2 `pruneD3ge` — remove d_cat < 3 px only, keep the exactly-300 m ring (36,043; −1,611; 4.28%)

- **Hypothesis.** Same flank mechanism, but dots at *exactly* d=3 px have zero
  kernel coupling to the mapped trace itself, so they are the most likely
  ring members to be independent parallel strands rather than re-detections.
- **Mechanism / mimic.** Identical to V1, restricted to the √5/√8 ring
  (941 + 670 dots). The 560 dots at exactly 300 m can only earn from truth on
  their far side; keeping them hedges the step-over/splay counter-mechanism.
- **Predicted live change.** **+0.0045 (MODEL)**, range −0.004…+0.011.
- **Falsifier.** If V1 (slot 1) loses ≥0.01 but V2 does not, the exactly-300 m
  ring carries the earning new geometry. If both lose, the flank mechanism
  ends at 2 px. V2 is the conditional third slot, not a standalone bet.

## V3 `pruneD3refill` — V1 + 2,171 refills, count held at 37,654 (11.53% turnover)

- **Hypothesis.** The prune gain is positional, not a mass effect: returning
  the removed mass as H19-5-support dots at d_cat > 3 px retains V1's gain
  (or adds to it) at equal dot count.
- **Mechanism.** Refill pool = H19-5 support pixels the 2.8 px thinning
  suppressed; all 2,171 accepted refills are positions the finer d1.5
  thinning of the same support actually selected (tier 0), >2.0 px from every
  dot, d_cat > 3 px (min realized mutual spacing 2.24 px vs parent 2.83 px).
- **Non-fault mimic / declared confounders.** (1) Refill at parent spacing is
  impossible — only 611 pool pixels exist >2.8 px from kept dots — so refills
  sit in the first suppressed halo of kept dots, largely on the *same*
  lineaments; their kernel coverage overlaps kept dots' and they may add
  little new-truth credit while still paying α. (2) Refill order is a lineage
  proxy (d1.5 selection), not the parent's continuous ranking — no continuous
  H19-5 field is pinned anywhere (on-disk H19-5/H19-4 are binary). V3
  therefore tests "prune + closer-spaced same-field mass", not pure position.
- **Predicted live change.** **+0.002 vs R0 (MODEL)**, range −0.008…+0.010;
  relative to V1, refill is expected to cost a little (suppressed-halo dots
  are by construction the thinning's second choices).
- **Falsifier.** Receipt V3 ≥ V1 + 0.01: mass was limiting and same-field
  densification pays — reopens MASS/SPACING at finer spacing. V3 ≤ V1 − 0.01:
  suppressed-halo mass is dead weight; spacing is load-bearing.

## Why there is no ≤1 px arm

Brief §5 lists ≤1 / ≤2 (R0) / ≤3 px. The ≤1 arm already exists as pinned,
hash-verified `h27-4-solo-d28` (CLAIM 0.2708) — it *is* R0's parent before the
≤2 px step, re-verified here (`H27 == D28 & d>1`, `R0 == H27 & d>2`, array-
exact). Rebuilding it for a slot would be an exact repeat. It is in the ledger
as the measured ≤1 point of the dose-response.

## Report-only PROXY (never a gate)

Fold-equivalent hide-and-recover (`gems85-holdout-v1.0.0`, 60,988 withheld
positives): rule radii >1 / >2 / >3 / ≥3 / >3+refill pooled DTI
0.1146 / 0.1168 / 0.1187 / 0.1182 / 0.1191, 95% CIs ≈ ±0.009 and mutually
overlapping — direction consistent with pruning, magnitude indistinguishable
from noise, and the instrument mechanically rewards keeping mass off the
visible catalogue. SGMC off-catalogue control (62,122 truth px): R0 0.0954,
V1 0.0937, V2 0.0942, V3 0.0962 — equally noise-level, opposite sign for the
pure arms. Neither instrument promotes or vetoes anything (brief §3: holdout
correlated −0.87…+0.54 live). Full numbers: `evidence/v2-prune-proxy.json`.
