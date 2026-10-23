# SLOT_PLAN — 3 scored submissions per rolling week, ONE entity, deadline 2026-12-03 (provisional)

Parent for every slot below: **R0 = `h33-h33-2-b2`** (`e5eb6e7e`; 37,654 dots; live **0.2778 CLAIM** —
owner-reported, no receipt in `ledger/`). `TOP_PUBLIC` is **unfilled**: the human must read it off the
leaderboard with a date; no other target number is valid. Slots left this rolling week: **unknown**
(from the account page; 3/week is a ceiling, not a target).

## Next 3 slots, in order

| # | upload (fallback: the `-zeros` twin) | change vs R0 | what the result would change | prediction (MODEL) |
|---|---|---|---|---|
| 1 | `releases/h33-2-b2-prune3-20261023-fb308615.tif` | drop 2,171 dots at 2 < d_cat ≤ 3 px → 35,483 (−5.77 %) | Δ ≥ +0.005 ⇒ the catalogue-shadow rung is alive; rungs 4/5 become the plan. Δ ≤ 0 ⇒ ladder exhausted at 2 px and the slot budget moves to the axes in §3 | **+0.007** (+0.001…+0.012) |
| 2 | `releases/h33-2-b2-prune4-20261023-2880b0e9.tif` | drop 3,825 dots at 2 < d_cat ≤ 4 px → 33,829 (−10.16 %) | brackets the optimum: prune4 ≥ prune3 ⇒ push rung 5; prune4 < prune3 but > R0 ⇒ the optimum is bracketed and the final file is the better of the two | **+0.003** (−0.004…+0.010) |
| 3 | `releases/h33-2-b2-prune5-20261023-7ebfc408.tif` | drop 5,637 dots at 2 < d_cat ≤ 5 px → 32,017 (−14.97 %) | spend only if 1 and 2 both scored ≥ 0.2778. A gain ⇒ the shadow exceeds the documented 100–400 m offset class; a loss ⇒ close the ladder | **−0.003** (−0.012…+0.006) |

**SNAP (new this session) is a hedge, not a slot.** The three SNAP files are gated and sit in
`releases/`, but this session's own measurements predict a null result for all three
(−0.0004…+0.0001 MODEL): every edge field is a weak fault localiser (AUC 0.51–0.56 on the mapped
catalogue) and R0's dots already sit above the footprint mean on all of them. Use
`releases/h33-2-b2-snapgrav2-20261023-1b033f40.tif` (2,603 dots moved, 6.9 %) **only** in a week where
a slot would otherwise expire unused, because a null SNAP receipt is what closes the position axis
(§3.1). Do not upload `snaptop2` as a first SNAP test: it moves 52.5 % of the dots and confounds
position with a near-redraw.

Live changes under 0.01 are **no evidence** (public chunks only; the private chunks and the Phase-2
expert-expanded labels may differ). Every live result needs a submission-page RECEIPT;
`ledger/submissions.csv` stays `status=BUILT` until then. Never schedule an exact repeat for another
score (the encoding twins scored identically).

## Calendar (deadline provisional, human must confirm)

- **wk 1 (Oct 23–29):** slots 1–3 above, rolling week permitting. Keep one slot in reserve.
- **wk 2 (Oct 30–Nov 5):** combine the winning rung with the single best non-PRUNE axis, one change at
  a time, only if the predicted Δ ≥ +0.005; otherwise do not spend a slot.
- **wk 3 (Nov 6–12):** the spare encoding twin only if a slot expires unused (a fallback test, not an
  experiment).
- **wk 4–5 (Nov 13–26):** confirm the winner on fresh proxies, choose the final file plus one fallback,
  re-validate both formats.
- **wk 6 (to Dec 3):** freeze. One blind final submission; no geometry changes after the last receipt.
- **41 calendar days** from Oct 23 to Dec 3, not six full weeks; the deadline and timezone are not
  independently confirmed — the human checks
  https://www.drivendata.org/competitions/306/competition-doe-gems/ and the quota in
  https://docs.nlr.gov/docs/fy26osti/96647.pdf (neither fetched this session).

## What this session closed, and the axes it implies (proposed, NOT built)

1. **Position (SNAP) — closed pending one receipt.** Six edge fields were measured before building
   anything: mapped-fault AUC 0.51–0.56, and every arm's fault-credit delta is ≈ 0 or negative. The
   three files exist to falsify the "we are 1–2 px off" hypothesis, not to win points.
2. **Add-mass axes are capacity-blocked, not geology-blocked.** After the parent's 2.8 px packing rung,
   only **283** free parent-ridge cells remain in the high-relief tercile and **794** overall, versus the
   3,766+ dots a 10 % count-holding RELIEF / CONCENTRATION / MASS-add arm must place. Do not schedule
   them without first relaxing the packing rung (which is a different axis and a known risk).
3. **RELIEF prior is real but unexploitable by adding mass.** Mapped-fault density (SGMC minus
   catalogue, > 3 px) is 5.8× higher in the high detrended-elevation tercile than in the low one, while
   R0's dot density is only 1.8× higher — dots per mapped-fault pixel 1.11 / 1.02 / 0.36. The
   *removal* version of this (drop the basin tercile) is the only untested mass edit with a live prior;
   it is a PRUNE-family edit and should be pre-registered as such.
4. **Cross-physics strike agreement** (earlier sessions' proposal) remains the best *selection* test:
   matched count and ranking strata, magnetic vs gravity boundary alignment. Falsifier: ≥ 0.01 receipt
   loss despite increased agreement.

## What this session did *not* do, on purpose

No submission, no leaderboard or forum access, no credentials, no site redesign, no change to
`vendor/gems57`, no MASS/CONCENTRATION/RELIEF build (blocked by §2), no TRACKB traces (Phase 2, expert
time required).
