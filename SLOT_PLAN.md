# SLOT_PLAN — 3 scored submissions per rolling week, ONE entity, deadline 2026-12-03 (provisional)

Supersedes the BLOCKED plan of the v2 preflight session (`a6004d6`): R0 is now recipe-rebuilt and
verified (IR-V2-07), the axis conflict IR-V2-03 is resolved by choosing PRUNE, and three variants exist.
Parent for every slot below: **R0 = `h33-h33-2-b2`** (`e5eb6e7e`, 37,654 dots, live **0.2778 CLAIM** —
owner-reported, no receipt here). `TOP_PUBLIC` is **unfilled**: the human must read it off the leaderboard
with a date; no other target number is valid. Remaining slots this rolling week: **unknown** — from the
account page, 3/week is a ceiling, not a target, and the three scores below are one dose–response curve,
not three independent bets.

## Next 3 slots, in order

| # | upload this file (fallback: the `-zeros` twin) | change vs R0 | what the result would change | prediction (MODEL) |
|---|---|---|---|---|
| 1 | `releases/h33-2-b2-prune3-20261023-fb308615.tif` | drop 2,171 dots at 2 < d_cat ≤ 3 px → 35,483 (−5.77 %) | Δ ≥ +0.005 ⇒ the catalogue-shadow rung mechanism is alive and rungs 4/5 become the plan; Δ ≤ 0 ⇒ ladder exhausted at 2 px, week 2 switches axis | **+0.007** (+0.001…+0.012) |
| 2 | `releases/h33-2-b2-prune4-20261023-2880b0e9.tif` | drop 3,825 dots at 2 < d_cat ≤ 4 px → 33,829 (−10.16 %) | brackets the optimum: prune4 ≥ prune3 ⇒ shadow ≥ 400 m, push rung 5; prune4 < prune3 but > R0 ⇒ optimum bracketed in (3,4) px and the final file is the better of the two | **+0.003** (−0.004…+0.010) |
| 3 | `releases/h33-2-b2-prune5-20261023-7ebfc408.tif` | drop 5,637 dots at 2 < d_cat ≤ 5 px → 32,017 (−14.97 %) | spend only if 1 and 2 both scored ≥ 0.2778. A gain means the shadow exceeds the documented 100–400 m offset class and the next session sweeps rungs 5–8; a loss closes the ladder and hands the axis budget to CONCENTRATION/RELIEF | **−0.003** (−0.012…+0.006) |

Live changes under 0.01 are **no evidence** (public chunks only; private chunks plus the Phase-2
expert-expanded labels may differ). All live results require a submission-page RECEIPT; catalogue and
SGMC results are PROXY and never a promotion gate. Never schedule an exact repeat just to obtain
another score (the ledger's encoding twins scored identically).

## Calendar (deadline provisional, human must confirm)

- **wk 1 (Oct 23–29):** slots 1–3 above, rolling week permitting. Keep one slot in reserve if the
  account shows fewer than three left.
- **wk 2 (Oct 30–Nov 5):** combine the winning rung with the single best non-PRUNE axis, one change at
  a time, predicted Δ ≥ +0.005 — otherwise do not spend a slot.
- **wk 3 (Nov 6–12):** replicate the best file's geometry through the other encoding only if a slot is
  otherwise unused (this is a fallback test, not an experiment).
- **wk 4–5 (Nov 13–26):** confirm the winner on fresh proxies, choose the final file and one fallback,
  re-validate both formats with `scripts/gemsdoe85_prune_session.py`.
- **wk 6 (to Dec 3):** freeze. One blind final submission; no geometry changes after the last receipt.
- There are **41 calendar days** from Oct 23 to Dec 3, not six full weeks; deadline and timezone are not
  independently confirmed — human checks https://www.drivendata.org/competitions/306/competition-doe-gems/ .
  Quota per https://docs.nlr.gov/docs/fy26osti/96647.pdf (not fetched this session).

## Better axes for later sessions — proposed, NOT built, NOT assigned

1. **PRUNE-EXCHANGE (replaces MASS).** Same count as R0, but the dots removed from the catalogue shadow
   are moved along strike on the parent's own ridge into segments with d_cat > 5 px, at fixed mass.
   Mechanism: exchange isolates position from mass. Confounder: it re-seeds the packing, so it is not a
   pure prune. Falsifier: a matched-count random-relocation control must score worse by ≥ 0.01.
2. **CONCENTRATION at 1 km blocks.** Move 15 % of mass from the lowest-prior 1-km blocks to the highest
   (prior = GeoDAWN radiometric TC + detrended-elevation slope, both pinned), reporting block-density CV
   before/after. Confounder: the prior is the same layer family that built the ridge. Falsifier:
   prior-shuffled control at matched CV fails to lose ≥ 0.01.
3. **RELIEF terciles.** Shift 10–15 % of mass between basin / piedmont / range-front terciles (`det_elev`),
   count fixed. Confounder: range-front concentration can be a survey-coverage artefact (LiDAR footprint
   edge). Falsifier: sign flips inside the LiDAR-covered subset.
4. **Cross-physics strike agreement** (from the earlier session), matched count/ranking strata:
   independent magnetic/gravity boundary alignment may separate faults from lithologic contacts.
   Falsifier: ≥ 0.01 receipt loss despite increased agreement; smaller changes are inconclusive.
5. **Persistence versus closed edges** (earlier session), matched count/relief: favour kilometre-scale
   open, strike-consistent boundaries over closed rims. Confounder: shorelines and lava margins persist
   too. Falsifier: no ≥ 0.01 receipt gain and no improved blind geological evidence on reviewed traces.
6. **SPACING sweep on the pruned geometry** (rungs 2.6–4.0 px) — lowest priority: partly duplicates the
   PRUNE dose ladder running now.

## What this session did *not* do, on purpose

No MASS variant (its only label-free ranking is anti-correlated with value), no count-holding refill
(measured capacity 475 dots vs 2,171 removed), no SNAP/TRACKB (a second axis would contaminate the dose
ladder), no submission of any kind, no leaderboard access, no site redesign.
