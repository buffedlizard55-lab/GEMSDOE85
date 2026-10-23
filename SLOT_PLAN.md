# SLOT_PLAN — 3 scored submissions per rolling week, ONE entity · deadline 2026-12-03 (provisional)

Parent for every built file: **R0 = `h33-h33-2-b2`** (`e5eb6e7e`, 37,654 dots, live **0.2778 CLAIM** —
no receipt in `ledger/`). `TOP_PUBLIC`: **____** (human fills from leaderboard with date; no other
target is valid). Slots left this rolling week / total: **__ / __** (human fills from account page).
Twelve gated candidates sit in `releases/`: six `PRUNE` rungs (`fb308615`, `2880b0e9`, `7ebfc408`,
`3908de12`, `acce3907`, `f94be3ad`), three `RELIEF` tercile-exchange files (`669f0637`, `21af1eee`,
`7a0329ee`; `d_cat > 3 px`, 37,654 fixed), and three `SNAP` position-bound controls (`ac3fc128`,
`6913d029`, `de094d8e`; inside ±0.01 band, ranked below `PRUNE` + `RELIEF`).

## Next 3 slots, in order

| # | upload `releases/<id>.tif` (fallback: `-zeros.tif`) | change vs R0 | what the receipt changes | prediction (MODEL) |
|---|---|---|---|---|
| 1 | `h33-2-b2-prune3-20261023-fb308615.tif` | `PRUNE`: drop 2,171 dots at `2 < d_cat ≤ 3 px` → 35,483 (5.77 %) | Establishes the live `d_cat > 3 px` baseline. `Δ ≥ +0.01` ⇒ shadow extends to 300 m; `Δ ≤ −0.01` ⇒ near-catalogue splays carry net truth | **+0.007** (+0.001…+0.012) |
| 2 | `h33-2-b2-reliefp2r10-20261023-669f0637.tif` *(or `…-r3p61-…-f94be3ad.tif` if staying pure-PRUNE)* | `RELIEF`: shift +10 % (`3,765` dots) Piedmont `T2` → Range `T3`, `d_cat > 3 px`, n=37,654 fixed (12.77 %) | Compared to Slot 1, isolates range-front bedrock under-compilation vs concealed-basin regime (`+0.0085` on off-catalogue SGMC PROXY) | **+0.008** (+0.001…+0.015) |
| 3 | **Conditional on Receipts 1 & 2** (all pre-built):<br>• `h33-2-b2-reliefbp2r15-20261023-21af1eee.tif` if `Slot2 − Slot1 ≥ +0.01`<br>• `h33-2-b2-reliefr2bp10-20261023-7a0329ee.tif` if `Slot2 − Slot1 ≤ −0.01`<br>• `h33-2-b2-r3p61-20261023-f94be3ad.tif` if `|Slot2 − Slot1| < 0.01` & `Slot1 − R0 ≥ +0.01` | `+15 %` Basin+Pied→Range (`21af1eee`), `+10 %` Range→Basin+Pied (`7a0329ee`), or `PRUNE` `d_cat ≤ 3.61 px` (`f94be3ad`); if neither 1 nor 2 moves ≥ 0.005, **hold Slot 3** | Pushes the winning direction immediately: tests the 15 % range-front knee, flips to concealed-basin magnetic/gravity ridges, or brackets the >300 m shadow (`r2p85` / `prune4` / `SNAP` stay in reserve) | **+0.006** / **−0.002** (+0.006 cond.) / **+0.005** |

Treat any live `|Δ| < 0.01` as **no evidence** (public chunks only; private chunks and Phase-2
expert-expanded labels may differ). Never upload an encoding twin expecting a new score.

## Calendar to provisional deadline (41 days Oct 23 → Dec 3; human confirms URL & timezone)

- **wk 1–2 (Oct 23 – Nov 5):** Spend Slots 1–3 above (`PRUNE` + `RELIEF`), then test `CONCENTRATION`
  (two-sided km-block reallocation per IR-V2-17) or bracket optimal `PRUNE` (`r3p61` / `r2p85` / `prune4`).
  Spend at most one spare slot on `snap-free-lidar2` if needed as a position-sensitivity bound.
- **wk 3–4 (Nov 6 – Nov 19):** Combine the two axes with positive live receipts (`Δ ≥ +0.01`), one
  controlled step per slot from the highest-receipt parent; run one ablation check if budget allows.
- **wk 5–6 (Nov 20 – Dec 3):** Confirm best candidate, lock ONE blind final submission plus one
  `-zeros.tif` fallback, and re-run disk format/hash validators (`scripts/gemsdoe85_{prune,rung,snap,relief}_session.py`).
  Confirm rules/deadline at https://www.drivendata.org/competitions/306/competition-doe-gems/ and
  https://docs.nlr.gov/docs/fy26osti/96647.pdf (human browser only).

## Better axes for later sessions — proposed, NOT built this session

1. **TWO-SIDED CONCENTRATION on 10-px / 10-km blocks.** Concentrating vs de-concentrating 10–15 % of
   dots by geodetic shear (`geod_shearrate`) + basement step (`iso_grav_anom_slope`) at fixed count
   settles the CV direction ambiguity (IR-V2-17). *Confounder:* block density co-varies with relief.
   *Falsifier:* block-shuffled control at matched CV scores within 0.01 of the prior-ranked move.
2. **DIP-CORRECTED UPDIP OFFSET (replaces naive potential-field `SNAP`).** Shift potential-field ridges
   100–300 m updip toward the footwall zero-crossing rather than hanging-wall gradient peaks.
   *Confounder:* unknown dip polarity in symmetric grabens. *Falsifier:* fails to beat parent by ≥ 0.01.
3. **DIRECTIONAL SHADOW PRUNE.** Prune east- vs west-flank `2–4 px` rings separately to test systematic
   datum/projection shift vs symmetric uncertainty. *Confounder:* range-front dip asymmetry. *Falsifier:*
   east and west receipts within ±0.003 of each other.
4. **CROSS-PHYSICS STRIKE AGREEMENT & PERSISTENCE.** Retain basin/piedmont ridges only where `tmi_hg`
   and `iso_grav_anom_hg` strikes agree within 20° over ≥ 1.5 km open traces (vs closed playa/caldera
   rims). *Confounder:* linear basalt dikes and pluvial shorelines. *Falsifier:* live Δ ≤ 0 vs parent.
