# Mechanism cards — RELIEF session, parent R0 (`h33-h33-2-b2`, 37,654 dots, live 0.2778 CLAIM)

Written for a structural geologist. One card per variant, plus the unshipped `d_cat > 3 px` collar
decomposition control and the measured 12-run `SNAP` negative result. Every number carries an
explicit evidence label (`CLAIM`, `PROXY`, `MODEL`); no number here is a live `RECEIPT`.

---

## Shared structural setup: why R0's relief allocation is skewed toward piedmont mimics

Parent R0 (`h33-h33-2-b2`, 37,654 unit-mass dots) was derived by 2.8 px Poisson-disk thinning of the
pinned `H19-5` 1-px skeleton (`ec1f9b56…`, 121,131 px). In `H19-5`, topographic openness and local
relief ridges dominate the pre-thinning surface (~83–90 % of fusion weight), whereas subsurface
potential-field gradients carry minor weight. Partitioning the 5,167,373-pixel competition footprint
into exact equal-area Basin / Piedmont / Range-front terciles via the two competition
detrended-elevation bands (`0.70 · pct_rank(det_elev) + 0.30 · pct_rank(det_elev_slope)` from
`data/training_features.tif`, Bands 12 and 19) exposes a strong structural imbalance:

| Equal-area footprint tercile | Footprint px | Median `det_elev` | Median slope | R0 dots (share) | Uncompiled SGMC faults `d_cat > 3 px` (share) |
|---|---:|---:|---:|---:|---:|
| **T1 — Basin** (graben floor / playa) | 1,722,457 (33.3 %) | −219.95 m | 0.665° | 3,870 (**10.3 %**) | 3,947 (6.4 %) |
| **T2 — Piedmont** (coalescing bajadas) | 1,722,458 (33.3 %) | −75.58 m | 3.480° | 19,361 (**51.4 %**) | 15,901 (25.6 %) |
| **T3 — Range-front / horst block** | 1,722,458 (33.3 %) | +210.87 m | 14.716° | 14,423 (**38.3 %**) | 42,274 (**68.0 %**) |

Two competing structural-geology regimes explain where unmapped "new-fault" truth may lie
(organiser clarifications confirm known USGS/INGENIOUS pixels are masked pixel-exactly while label
sources and fault types are undisclosed:
https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516,
https://community.drivendata.org/t/where-do-you-draw-the-line/11536,
https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527):

1. **Under-compiled range-front & intra-range bedrock strands (`T2 -> T3`).** The INGENIOUS
   Quaternary compilation concentrates on alluvial-piedmont scarps (`T2`), leaving 68.0 % of
   geologic-map SGMC fault pixels outside a 300 m catalogue collar in `T3`, while R0 places 51.4 %
   of all dots in `T2` where incised fan-channel margins and pluvial Lake Lahontan/Bonneville
   shorelines generate scarp-like openness ridges without basement offset.
2. **Concealed intra-basin & piedmont relay / accommodation structures (`T3 -> T1 + T2`).** Where
   test labels reflect subsurface geophysical interpretation beneath Quaternary alluvium (e.g.,
   step-overs and accommodation zones of the class catalogued on known systems by Faulds & Hinz,
   used only as a fault-interaction prior), R0's 10.3 % Basin share under-samples concealed basement
   structures imaged by horizontal magnetic/gravity gradients (`tmi_hg`, `iso_grav_anom_slope`) at
   GeoDAWN's 400 m line spacing
   (https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7).

### De-confounding Hard Constraint #4 (`d_cat > 3.0 px`) from pure `RELIEF`

Hard Constraint #4 requires zero catalogue mass and distance ≥ 3 px from the catalogue outside
`AXIS = PRUNE`. R0 contains 2,171 dots at `2 < d_cat ≤ 3 px` (255 in `T1`, 1,128 in `T2`, 788 in
`T3`). To enforce `d_cat > 3.0 px` (`min = √10 = 3.162 px`) without altering baseline tercile shares,
an unshipped control (`ctrl_collar3_0pct`) replaces each tercile's `d_cat ≤ 3 px` dots 1-for-1
*inside that same tercile* from pinned sibling ancestors (`H19-5 | H19-4 | H16-1`, 100 % ancestor
fill). On `sgmc_minus_catalogue_3px` (`62,122` positives), `ctrl_collar3_0pct` moves DTI from
`0.09539` (`R0`) to `0.09883` (`+0.00344` PROXY), and on `gems57-pooled-hide-v2` (`11,321` withheld
positives) from `0.09609` to `0.09638` (`+0.00029` PROXY). Every variant below holds both total
count (`37,654`) and the `d_cat > 3.0 px` rule constant, isolating the inter-tercile `RELIEF` shift.

---

## Card 1 — `h33-2-b2-reliefp2r10-20261023-669f0637` (`T2 -> T3` +10 %, 37,654 dots, 12.77 % changed)

- **Hypothesis.** Half of R0's budget sits on piedmont bajadas (`T2`, 51.4 %), where surface-only
  scarp ridges pay α = 0.2 false-positive cost, whereas uncompiled range-front/bedrock fault strands
  in `T3` are under-covered relative to their regional fault density.
- **Mechanism.** Holds Basin `T1` fixed (`3,870` dots), removes `3,765` Piedmont `T2` dots (`19,361 ->
  15,596`, dropping `d_cat ≤ 3 px` flank dots first and then the R0 dots with the weakest
  subsurface `tmi_hg` + `iso_grav_anom_slope` + `tc` corroboration), and places `+3,765` dots in
  Range-front `T3` (`14,423 -> 18,188`) at `d_cat > 3.0 px` and Euclidean spacing `≥ 2.8 px` (76 %
  from pinned `H19-5 | H19-4 | H16-1` ridges, 24 % from 1-px multi-physics NMS crests).
- **Non-fault process that could mimic it.** Resistant volcanic flow margins, welded-tuff cooling
  scarps, metamorphic-intrusive lithologic contacts, and steep non-tectonic canyon walls in `T3`
  produce colocated topographic slope and magnetic/gravity gradients; survey-boundary contrast along
  high-relief DEM tile seams can also elevate `T3` ridge density.
- **Predicted live change.** **+0.008** (range **+0.001 to +0.015**) **MODEL**. On
  `sgmc_minus_catalogue_3px`, DTI rises from `0.09539` `[0.08457, 0.10672]` (`R0`) to `0.10388`
  `[0.09296, 0.11487]` (**+0.00849 PROXY** over R0; **+0.00505 PROXY** pure `RELIEF` over
  `ctrl_collar3_0pct`), while Quaternary-biased `gems57-pooled-hide-v2` shifts by `−0.00326` PROXY
  (`0.09283` `[0.07952, 0.10584]`). Any live change `|Δ| < 0.01` is treated as no evidence.
- **Falsifier.** A live receipt at least `0.01` *below* Slot 1 (`h33-2-b2-prune3`, which isolates
  the `d_cat > 3 px` collar). That refutes range-front under-sampling on new-fault truth and triggers
  Card 3 (`reliefr2bp10`).

## Card 2 — `h33-2-b2-reliefbp2r15-20261023-21af1eee` (`T1+T2 -> T3` +15 %, 37,654 dots, 17.09 % changed)

- **Hypothesis.** If hidden test faults are predominantly unmapped range-bounding splay, footwall,
  and intra-range bedrock structures, pushing a 15 % mass transfer out of both playa floors (`−5 %`)
  and piedmont aprons (`−10 %`) into `T3` (`+15 %`) captures the remaining uncompiled bedrock trace
  length before spacing saturation sets in.
- **Mechanism.** Shifts `−1,883` dots from Basin `T1` (`3,870 -> 1,987`) and `−3,765` from Piedmont
  `T2` (`19,361 -> 15,596`) into Range-front `T3` (`14,423 -> 20,071`) at `d_cat > 3.0 px` and
  `≥ 2.8 px` spacing (`3,458` from pinned sibling ancestors + `2,978` from 1-px physical NMS crests).
- **Non-fault process that could mimic it.** Same volcanic/intrusive contact and canyon-wall mimics
  as Card 1, amplified because exhausting the `3,458`-dot pinned-ancestor pool in `T3` draws 46 % of
  additions from raw multi-physics NMS crests where pluton roofs and basalt tablelands sit.
- **Predicted live change.** **+0.006** (range **−0.002 to +0.014**) **MODEL**. On
  `sgmc_minus_catalogue_3px`, DTI reaches `0.10418` `[0.09339, 0.11595]` (**+0.00879 PROXY** vs R0),
  gaining only `+0.00030` PROXY over the +10 % dose (`reliefp2r10`) while halving Basin coverage —
  indicating diminishing marginal returns near 15 %. Live `|Δ| < 0.01` is no evidence.
- **Falsifier.** Spend only if Card 1 gains live; falsified if Card 2 fails to beat Card 1 on live
  receipt (proving the 10–15 % range-front capacity knee is already saturated by volcanic/erosional
  mimics).

## Card 3 — `h33-2-b2-reliefr2bp10-20261023-7a0329ee` (`T3 -> T1+T2` +10 %, 37,654 dots, 13.67 % changed)

- **Hypothesis.** Hidden geothermal-relevant test faults are concealed intra-basin step-overs,
  axial accommodation zones, and buried piedmont synthetic/antithetic normal faults beneath
  Quaternary fill where surface scarps are bevelled or buried, whereas intra-range `T3` detections
  over-sample inactive bedrock canyons.
- **Mechanism.** Removes `3,765` lowest-corroborated dots from Range-front `T3` (`14,423 -> 10,658`)
  and adds `+1,883` dots to Basin `T1` (`3,870 -> 5,753`, upweighting subsurface `tmi_hg` +
  `iso_grav_anom_slope` + `tc` horizontal gradients to 0.70 vs 0.30 surface slope) and `+1,882` dots
  to Piedmont `T2` (`19,361 -> 21,243`, 100 % from pinned sibling ancestors), all at `d_cat > 3.0 px`
  and `≥ 2.8 px` spacing.
- **Non-fault process that could mimic it.** Buried paleochannels, Pleistocene pluvial shoreline
  spits/bars, axial playa evaporite-margin conductivity/density steps, and intra-basin basalt sills
  generate linear potential-field and micro-topographic gradients across `T1`–`T2` without brittle
  fault offset.
- **Predicted live change.** **−0.002** (range **−0.010 to +0.007**) **MODEL** unconditionally,
  switching to **+0.006 MODEL conditional on Card 1 losing live**. On Quaternary-biased
  `gems57-pooled-hide-v2`, `reliefr2bp10` (`0.09518` `[0.08203, 0.10820]`) outperforms both `p2r10`
  (`0.09283`) and `bp2r15` (`0.09295`) by `+0.0023` PROXY, while losing `−0.00105` vs R0 (`−0.00449`
  vs `ctrl_collar3_0pct`) on bedrock-dominated `sgmc_minus_catalogue_3px` (`0.09434`
  `[0.08458, 0.10454]`). Live `|Δ| < 0.01` is no evidence.
- **Falsifier.** Spent only if Card 1 loses relative to `prune3`; falsified if live score fails to
  exceed `prune3` by ≥ 0.01, which rejects wholesale relief reallocation in both directions.

---

## Measured negative result — `SNAP` on provided gradient bands rejected before building

Before selecting `RELIEF`, 12 deterministic `SNAP` configurations were tested on R0 (`37,654` dots,
`≤ 1.5 px` and `≤ 2.0 px` Euclidean windows, collision-free greedy displacement onto raw and
high-pass `tmi_hg`, `iso_grav_anom_slope`, `det_elev_slope`, and multi-band fusions at `d_cat ≥ 3 px`
for moved dots). **All 12 configurations degraded both `sgmc` (`−0.0046` to `−0.0084` PROXY) and
`sgmc_minus_catalogue_3px` (`−0.0015` to `−0.0057` PROXY)**, moving 88–95 % of dots by mean
1.09–1.64 px. Two physical causes explain the uniform loss:

1. **Hanging-wall potential-field dip shift.** Over 45–65° dipping Basin-and-Range normal faults,
   `tmi_hg` and `iso_grav_anom_slope` peak 100–400 m downdip of the surface fault trace (compounded
   by 400 m flight-line gridding), pulling dots *off* the surface trace.
2. **Spacing collapse.** Independent `≤ 2 px` local-maximum shifts compress R0's optimal `2.8 px`
   Poisson-disk spacing toward `2.0 px`, increasing 300 m kernel overlap without adding truth reach.

`SNAP` is therefore not built with provided 100 m potential-field bands; only strike-normal snapping
onto human-supplied 1 m LiDAR scarp rasters (`SLOT_PLAN.md`) could evade the hanging-wall dip bias.
