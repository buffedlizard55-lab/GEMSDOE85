# SLOT_PLAN — one entity, 3 scored submissions/week, deadline 2026-12-03

**Parent for every file: R0 = `h33-h33-2-b2`** — 37,654 unit dots, rebuilt pixel-exactly from its
recipe (IR-86-001). Live **0.2778 = CLAIM**: no receipt exists anywhere in this repository.
**TOP_PUBLIC: unfilled by the human.** **Slots: 3 of 3 this week, 0 used** (human, 2026-10-23).

The ledger now holds **22 gated candidates** on this one parent, all `n = 37,654` where the axis
allows it: 6 PRUNE rungs, 3 RELIEF, 3 CONCENTRATION, 3 SNAP (`main`, merged) + 4 SNAP and 3 SPACING
(this branch). No `(parent, axis, value)` pair is repeated.

## Next 3 slots, in order

| # | file | what it tests | if it lands | if it does not |
|---|---|---|---|---|
| 1 | `releases/h33-2-b2-prune3-20261023-fb308615.tif` (drop 2,171 dots at 2 < d_cat ≤ 3 px → 35,483) | **The collar baseline.** Every non-PRUNE axis in this repo applies the same ≥ 3 px collar, so this receipt prices the collar once and fixes the baseline for all of them. | Δ ≥ +0.01 ⇒ the 2.24–2.83 px ring was costing real mass and PRUNE is the axis to push (`prune4`, `r3p61`). | Δ ≤ −0.01 ⇒ near-catalogue splays carry net truth and the ≥ 3 px rule must be revisited (organizer thread 11516 says new truth *can* lie within 300 m of known traces). |
| 2 | `releases/h33-h33-2-b2-conc10-20261023-f89e4659.tif` (10 % of dots moved between 0.8 km blocks by prior) | The one axis whose *prior* is independent of the parent's own field, and the only axis with a dose ladder (10/15/20) already built. | Δ ≥ +0.01 ⇒ spend slot 3 on `conc15`/`conc20` to find the knee. | \|Δ\| < 0.01 ⇒ concentration is not the active variable; slot 3 goes to RELIEF `reliefp2r10`. |
| 3 | conditional (all pre-built):<br>• `h33-h33-2-b2-reliefp2r10-…-669f0637.tif` if slot 2 was flat<br>• `gems85-h33-h33-2-b2-conc15-…-45bfb93b.tif` if slot 2 was positive<br>• `h33-h33-2-b2-space10-20261023-b4a3bd25-zeros.tif` if slots 1–2 both show the collar is *free* (Δ ≥ 0 on slot 1) | Third axis, chosen by what the first two receipts excluded. | | |

Treat any live |Δ| < 0.01 as **no evidence** (public chunks only). Never spend a slot on an encoding
twin: NaN-outside and zeros-outside of the same pixels score identically.

## What this session's SPACING files can and cannot tell you

Pre-registered: `space10` +0.000…+0.010, `space20` −0.005…+0.010, `space10s` +0.000…+0.012.

The measurement that matters is in `evidence/session_spacing.json`, and it is **not** favourable to a
large spacing intervention: matched-count refill is only possible by re-packing **tighter**. Mean
nearest-neighbour distance falls 10.03 → 9.49 px (`space10`), 8.97 (`space20`), 9.23 (`space10s`);
the share of dots with a neighbour inside 3 px rises 5.1 % → 7.5 / 11.8 / 9.2 %; block CV rises
0.635 → 0.657 / 0.679 / 0.669 (the best files reportedly sit at 0.51–0.59, i.e. *lower*). Capacity at
the parent's own 2.8 px rung is **201 cells** against 3,765 refills needed — the ridge is already
close to capacity at the metric's 3 px kernel scale, which is the same conclusion a merged sibling
reached independently (IR-V2-09). So these three files are a **capacity probe**, not a bet: they say
whether buying coverage is worth densifying, and they should not pre-empt a PRUNE or CONCENTRATION
slot unless both of those come back flat.

## Weeks to deadline (6 weeks)

* **wk 1–2** — slots 1–3 above. One axis per slot; record receipts in `ledger/submissions.csv`.
* **wk 3–4** — combine the two axes with Δ ≥ +0.01, one controlled step per slot from the
  highest-receipt parent. Never combine two nulls.
* **wk 5** — confirm the leader; check dot count against the private-chunk behaviour (the record
  says 37–44 k, and mass is confounded with field — do not infer a mass effect from file names).
* **wk 6** — lock ONE blind final file plus a `-zeros` fallback; re-run
  `scripts/validate_submission.py` on both; do not touch the winner afterwards.

## Axes I would assign next (mechanism · confounder · falsifier)

1. **Two-sided CONCENTRATION with a de-concentration arm.** R0's 10 km CV is 0.635, *above* the
   0.51–0.59 band, so the direction of the CV hypothesis is still ambiguous: build the opposite arm
   at matched count. *Confounder:* CV tracks the footprint silhouette; only blocks ≥ 50 % footprint
   coverage are scored. *Falsifier:* the two arms straddle the parent within ±0.01 — then density is
   not the variable and the band is an artefact of file selection.
2. **Directional shadow PRUNE (east vs west flank).** Tests a systematic 100–300 m datum/lineament
   offset against symmetric positional uncertainty. *Confounder:* range-front dip asymmetry.
   *Falsifier:* the two flanks score within ±0.003 of each other.
3. **TRACKB (Phase 2).** Strike-consistent ≥ 1 km traces from R0's highest-credit dots as GeoJSON +
   raster, one evidence paragraph each. It cannot win a weekly slot, but Phase 2 rescores against
   labels experts expand *after reviewing submitted faults*, so a legible trace inventory is the
   only artefact that can influence that step. *Confounder:* an expert-recognised trace that is not
   a fault. *Falsifier:* no organizer engagement with the traces.
