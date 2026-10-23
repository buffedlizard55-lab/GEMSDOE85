# SLOT_PLAN — 3 scored submissions per rolling week, ONE entity · deadline 2026-12-03 (provisional)

Parent for every slot: **R0 = `h33-h33-2-b2`** (`e5eb6e7e`, 37,654 dots, live **0.2778 CLAIM** —
owner-reported, no receipt here). `TOP_PUBLIC` is **unfilled** (the human reads it off the leaderboard
with a date; no other target number is valid). Slots left this rolling week: **unknown** — 3/week is a
ceiling, not a target. Every file below is BUILT and gated; none is scored.
**AXIS was not assigned by the human in any session** (asked each time; skipped). PRUNE was chosen from
the measurements in IR-V3-02 and SNAP from the orthogonality argument in IR-V2-14; confirm or overrule
before spending a slot.

## The ladder now has five measured rungs plus three finer ones

| dots removed | variant | d_cat threshold | file (fallback `-zeros` twin always exists) | prediction (MODEL) |
|---:|---|---|---|---|
| 941 | `r2p25` | ≤ 2.25 px | `releases/h33-2-b2-r2p25-20261023-3908de12.tif` | +0.003 |
| 1,611 | `r2p85` | ≤ 2.85 px | `releases/h33-2-b2-r2p85-20261023-acce3907.tif` | +0.005 |
| 2,171 | `prune3` | ≤ 3.0 px | `releases/h33-2-b2-prune3-20261023-fb308615.tif` | +0.007 |
| 3,361 | `r3p61` | ≤ 3.61 px | `releases/h33-2-b2-r3p61-20261023-f94be3ad.tif` | +0.005 |
| 3,825 | `prune4` | ≤ 4.0 px | `releases/h33-2-b2-prune4-20261023-2880b0e9.tif` | +0.003 |
| 5,637 | `prune5` | ≤ 5.0 px | `releases/h33-2-b2-prune5-20261023-7ebfc408.tif` | −0.003 |

Two live/CLAIM rungs already anchor the curve: `≤1 px` gave **+0.0108** and `≤2 px` gave **+0.0070**
(owner-reported, no receipts in this repository). Everything below is relative to that anchor.

## Next three candidate slots (only if human confirms AXIS = PRUNE and quota permits)

| # | upload | change vs R0 | what the result changes | prediction |
|---|---|---|---|---|
| 1 | `…-prune3-…-fb308615.tif` | −2,171 (−5.77 %) | the anchor rung: ≥ 0.2778 keeps the shadow mechanism alive; ≤ 0.2778 retires the whole axis and hands wk 2 to the geometry lanes | **+0.007** |
| 2 | `…-r3p61-…-f94be3ad.tif` | −3,361 (−8.93 %) | **the decision slot.** Above slot 1 ⇒ the shadow extends past the kernel radius, sweep 4–8 px next; below slot 1 by ≥ 0.005 ⇒ optimum bracketed at 3 px and the final file comes from slots 1–3 | **+0.005** |
| 3 | `…-r2p85-…-acce3907.tif` | −1,611 (−4.28 %) | how little can be pruned and keep the gain — the risk-minimising file for the final submission | **+0.005** |

Do **not** spend slot 3 if slots 1 and 2 are both ≤ 0.2778: keep it for a fresh axis.
Do **not** schedule `prune4` / `prune5` / `r2p25` unless slot 2 lands *above* slot 1 (then `prune4` is
the next rung) or the account shows more than three slots left in the week.
A live change under 0.01 is **no evidence** (public chunks only; private chunks plus the Phase-2
expert-expanded labels may differ). Only a submission-page receipt counts, and only the human can
produce one.

## SNAP contingency — built (session `arena/a9cc6c47`), ranked **below** the ladder

Three SNAP variants at **fixed count and fixed mass** (37,654 dots before and after, ≤2 px moves, no dot
ever moved closer to the catalogue, minimum separation 2.0 px). Rationale: position is the only axis
left that is orthogonal to mass. Note on IR-V3-02's "impossible" verdict: it applies to preserving the
2.8 px packing floor, not to the brief's rule — at a **2.0 px separation floor** the snap is feasible
and 22–57 % of dots move, with the same proxy magnitudes session 3 measured (IR-V2-18).

They are **not** in the next three slots because their predicted effect is inside the ±0.01 no-evidence
band (+0.001 / 0.000 / −0.004): a receipt could not settle anything unless it moves by ≥0.01. Spend **at
most one** SNAP slot in a week, and only if the ladder is closed or a slot would otherwise be idle.

| order | file | change | what it buys |
|---|---|---|---|
| 1 | `releases/snap-free-lidar2-20261023-ac3fc128.tif` | 56.9 % moved, support coverage −18.9 % | largest effect: if position within ±200 m matters, it shows here. ≥ +0.01 ⇒ the ridge is misplaced vs the scarp; ≤ −0.01 ⇒ off-ridge is harmful, next take #2 |
| 2 | `releases/snap-ridge-lidar2-20261023-6913d029.tif` | 22.3 % moved, coverage −1.4 % | along-trace refinement only; informative after #1 |
| 3 | `releases/snap-ridge-tmi2-20261023-de094d8e.tif` | 30.3 % moved, coverage −2.3 % | the only test of the 400 m *aeromagnetic* positional story; a loss demotes magnetic-gradient axes |

## Calendar and decision gates

- **wk 1 (Oct 23–29):** slots 1–3 above.
- **wk 2 (Oct 30–Nov 5):** if the shadow extends past 3 px, sweep 4.5 / 5 / 6 px at fine spacing; if it
  peaks at 3 px, freeze the optimum. A free slot may then go to `snap-free-lidar2` as the position
  bound; otherwise keep it in reserve.
- **wk 3 (Nov 6–12):** one confirmation of the best file through the other encoding only if a slot is
  otherwise unused (a fallback test, not an experiment).
- **wk 4–5 (Nov 13–26):** choose the final file and one fallback; re-validate both formats with
  `scripts/gemsdoe85_rung_session.py`, `scripts/gemsdoe85_prune_session.py`,
  `scripts/gemsdoe85_snap_session.py`.
- **wk 6 (to Dec 3):** freeze. One blind final submission; no geometry changes after the last receipt.
  41 calendar days from Oct 23 to Dec 3, not six full weeks. Quota per
  https://docs.nlr.gov/docs/fy26osti/96647.pdf (not fetched this session).

## Better axes for later human assignment (not built)

1. **SNAP-AFTER-REPACK.** Re-thin the parent's 121k-px skeleton at 2.8 px with the edge response as the
   packing *priority* instead of raster order: same count ballpark, same exclusions, positions now
   edge-aligned. Confounder: it re-seeds the packing, so a matched-count random-priority control must
   lose by ≥ 0.01. Falsifier: no receipt gain despite a ≥3 % rise in mean edge response under the dots.
   (The already-built SNAP files are the cheaper version of this idea and will report first.)
2. **PRUNE-EXCHANGE.** Same count as R0, with the removed shadow mass moved along strike into
   `d_cat > 5 px` segments. Measured capacity at the parent's rung is small (794 free skeleton cells in
   the footprint), so this needs the repack of proposal 1 to be feasible.
3. **Directional shadow.** Split the removed ring by side (east/west of the mapped trace). If the
   USGS-vs-imagery offset is systematic rather than isotropic, one side should carry the whole gain.
   Cheap: two more PRUNE files from the same parent, no new machinery. Falsifier: symmetric receipts
   within ±0.003 of each other.
4. **MASS-UP on scarp response, off-catalogue.** The lidar scarp field scores higher near mapped faults
   than R0's own dots do (catalogue proxy 0.0048 → 0.0135 purely from dots moving toward them), i.e. it
   is a fault-likelihood surface. Whether adding dots at its maxima where `d_cat > 5 px` pays back the
   0.2 FP charge is untested. Confounder: additions failed live before (T-v2, −0.0028). Falsifier:
   matched-count random additions must lose by ≥ 0.01.
5. **RELIEF terciles** and **CONCENTRATION at 1 km blocks**: both need a direction decision first
   (IR-V2-17: R0's block-density CV 0.619 is above the 0.51–0.59 band attributed to the best files,
   which contradicts the brief's concentration direction).
6. **Cross-physics strike agreement** and **persistence vs closed edges** (carried over, unchanged).

## What these sessions did *not* do, on purpose

No CONCENTRATION or RELIEF file, no addition of any dot, no submission, no leaderboard access, no
credentials, no site redesign. SNAP was built but is not scheduled; PRUNE rungs beyond slot 3 stay in
reserve.
