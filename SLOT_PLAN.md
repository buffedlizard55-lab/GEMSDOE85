# SLOT_PLAN — 3 scored submissions per rolling week, ONE entity, deadline 2026-12-03 (provisional)

Parent for every built file: **R0 = `h33-h33-2-b2`** (`e5eb6e7e`, 37,654 dots, live **0.2778 CLAIM** —
no receipt in `ledger/`). `TOP_PUBLIC`: **____** (human fills from leaderboard with date; no other
target is valid). Slots left this rolling week / total: **__ / __** (human fills from account page).
Six gated candidates now sit in `releases/`: three `PRUNE` rungs (`fb308615`, `2880b0e9`, `7ebfc408`)
and three `RELIEF` tercile-exchange variants (`669f0637`, `21af1eee`, `7a0329ee`). Pairing one
`PRUNE` probe with one orthogonal `RELIEF` probe in Slots 1–2 de-confounds the `d_cat > 3 px` collar
and picks Slot 3 on live evidence rather than spending three blind slots on a single axis.

## Next 3 slots, in order

| # | upload `releases/<id>.tif` (fallback: `-zeros.tif`) | change vs R0 | what the receipt changes | prediction (MODEL) |
|---|---|---|---|---|
| 1 | `h33-2-b2-prune3-20261023-fb308615.tif` | `PRUNE`: drop 2,171 dots at `2 < d_cat ≤ 3 px` → 35,483 (5.77 %) | Establishes the live `d_cat > 3 px` baseline. `Δ ≥ +0.01` ⇒ shadow extends to 300 m; `Δ ≤ −0.01` ⇒ near-catalogue splays carry net truth | **+0.007** (+0.001…+0.012) |
| 2 | `h33-2-b2-reliefp2r10-20261023-669f0637.tif` | `RELIEF`: shift +10 % (`3,765` dots) Piedmont `T2` → Range `T3`, `d_cat > 3 px`, n=37,654 fixed (12.77 %) | Compared to Slot 1, isolates range-front bedrock under-compilation vs concealed-basin regime (`+0.0085` on off-catalogue SGMC PROXY) | **+0.008** (+0.001…+0.015) |
| 3 | **Conditional on Receipts 1 & 2** (all pre-built):<br>• `h33-2-b2-reliefbp2r15-20261023-21af1eee.tif` if `Slot2 − Slot1 ≥ +0.01`<br>• `h33-2-b2-reliefr2bp10-20261023-7a0329ee.tif` if `Slot2 − Slot1 ≤ −0.01`<br>• `h33-2-b2-prune4-20261023-2880b0e9.tif` if `|Slot2 − Slot1| < 0.01` and `Slot1 − R0 ≥ +0.01` | `+15 %` Basin+Pied→Range (`21af1eee`), `+10 %` Range→Basin+Pied (`7a0329ee`), or `PRUNE` `d_cat ≤ 4 px` (`2880b0e9`); if neither 1 nor 2 moves ≥ 0.005, **hold Slot 3** | Pushes the winning direction immediately without waiting a week: tests the 15 % range-front knee, flips to concealed-basin magnetic/gravity ridges, or brackets the 400 m shadow | **+0.006** / **−0.002** (+0.006 cond.) / **+0.003** |

Treat any live `|Δ| < 0.01` as **no evidence** (public chunks only; private chunks and Phase-2
expert-expanded labels may differ). Never upload an encoding twin expecting a new score.

## Calendar to provisional deadline (41 days Oct 23 → Dec 3; human confirms URL & timezone)

- **wk 1–2 (Oct 23 – Nov 5):** Spend Slots 1–3 above (`PRUNE` + `RELIEF`), then test `CONCENTRATION`
  (km-block prior reallocation) and, only if human-supplied 1 m LiDAR rasters clear data terms,
  strike-normal `SNAP` (`MASS` and 100 m potential-field `SNAP` rejected on measured controls).
- **wk 3–4 (Nov 6 – Nov 19):** Combine the two axes with positive live receipts (`Δ ≥ +0.01`), one
  controlled step per slot from the highest-receipt parent; run one ablation check if budget allows.
- **wk 5–6 (Nov 20 – Dec 3):** Confirm best candidate, lock ONE blind final submission plus one
  `-zeros.tif` fallback, and re-run disk format/hash validators on both (`scripts/gemsdoe85_relief_session.py`
  and `scripts/gemsdoe85_prune_session.py`). Confirm deadline/rules at
  https://www.drivendata.org/competitions/306/competition-doe-gems/ and
  https://docs.nlr.gov/docs/fy26osti/96647.pdf (human browser only).

## Better axes for later sessions — proposed, NOT built this session

1. **CONCENTRATION at 10–15 km blocks (`CV ≈ 0.52–0.64`).** Reallocate 10–15 % of dots from lowest
   to highest fault-interaction blocks (geodetic shear `geod_shearrate` + basement-step `iso_grav_anom_slope`),
   count fixed. *Confounder:* block scale correlates with range spacing (relief). *Falsifier:* block-shuffled
   control at matched block-density CV scores within 0.01 of the prior-ranked move.
2. **DIP-CORRECTED EDGE-TO-SCARP OFFSET (replaces naive `SNAP`).** Shift potential-field-only ridges
   100–300 m updip (toward zero-crossing of `tmi_vg` / `iso_grav_anom_vg` on the footwall side) rather
   than onto hanging-wall gradient peaks. *Confounder:* unknown fault dip polarity in symmetric grabens.
   *Falsifier:* fails to beat unshifted parent by ≥ 0.01 live or loses on off-catalogue SGMC faults.
3. **ALONG-STRIKE PERSISTENCE FILTER (replaces `MASS`).** Exchange dots on isolated `< 600 m` closed
   rims (playa/caldera margins) for dots on open `≥ 1.5 km` strike-consistent segments at fixed count.
   *Confounder:* linear pluvial shorelines also persist > 1.5 km. *Falsifier:* receipt loss or `< 0.01`
   delta relative to matched-count parent.
4. **CROSS-PHYSICS STRIKE AZIMUTH AGREEMENT.** Retain basin/piedmont ridges only where magnetic
   (`tmi_hg`) and gravity (`iso_grav_anom_hg`) horizontal-gradient azimuths agree within 20° (juxtaposed
   basement blocks vs superficial fan channels). *Confounder:* shallow basalt dikes align both fields
   without Quaternary slip. *Falsifier:* live Δ ≤ 0 despite higher cross-field azimuth coherence.
