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

| order | file | change | what it buys |
|---|---|---|---|
| 1 | `releases/snap-free-lidar2-20261023-ac3fc128.tif` | 56.9 % moved, support coverage −18.9 % | largest effect: if position within ±200 m matters, it shows here. ≥ +0.01 ⇒ the ridge is misplaced vs the scarp; ≤ −0.01 ⇒ off-ridge is harmful, next take #2 |
| 2 | `releases/snap-ridge-lidar2-20261023-6913d029.tif` | 22.3 % moved, coverage −1.4 % | along-trace refinement only; informative after #1 |
| 3 | `releases/snap-ridge-tmi2-20261023-de094d8e.tif` | 30.3 % moved, coverage −2.3 % | the only test of the 400 m *aeromagnetic* positional story; a loss demotes magnetic-gradient axes |

## Weeks to the deadline (41 calendar days from Oct 23 to Dec 3; default plan)

- **Default plan (brief §7):** wk 1–2 `MASS`, `CONCENTRATION`, `SNAP`, `PRUNE`, `RELIEF`; wk 3–4 combine the two best axes; wk 5–6 confirm, choose the final file and a fallback, re-validate the format of both.
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

## Proposed better axes for later sessions (do NOT build this session)

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

---

> **Update 2026-10-23, session `arena/c4de5673`:** the human has now assigned an
> axis (CONCENTRATION), so the slot order below is superseded for this week by the
> three CONCENTRATION rungs at the end of this file. The PRUNE / SNAP rungs above remain
> **built, gated and available as the backup ladder** — the human may reorder them.

## CONCENTRATION slots (session `arena/c4de5673`, 2026-10-23 — the axis the **human assigned**)

| # | file to upload | what it tests | what the result changes |
|---|---|---|---|
| 1 | `releases/gems85-h33-h33-2-b2-conc10-20261023-f89e4659-zeros.tif` | 10 % of R0's dots moved from the lowest-prior 0.8 km blocks into the highest-prior ones (CV 0.551 → 0.767) | If live ≥ **0.2778 + 0.01**, the block prior is a *positive* predictor of hidden new-fault truth: promote `conc15`, build a 30 % arm, and make concentration the headline axis. If live is within ±0.01, the dose is too small to read and the axis is uninformative. If live ≤ **0.2778 − 0.02**, the "clustering costs score" reading is confirmed and the family stops paying slots for distribution edits. |
| 2 | `releases/gems85-h33-h33-2-b2-conc15-20261023-45bfb93b-zeros.tif` | same axis, 15 % dose (CV → 0.786) | Together with slot 1 this gives the *slope* of live score against dose. A monotone decline confirms the dose–response reading; a rise at 15 % after a fall at 10 % says the effect is non-monotone and the 10 % arm was noise. |
| 3 | `releases/gems85-h33-h33-2-b2-conc20-20261023-a93e0b41-zeros.tif` | same axis, 20 % dose (CV → 0.782) | Confirms or breaks the monotone reading at the brief's upper dose. This is also the archive-quality arm: it is the variant whose spatial signature most resembles the H19-5 field (CV 0.787, 0.1922 CLAIM), so a large loss here is the cleanest possible refutation of "concentrate the mass". |

**Blind choice.** The three files are a dose series of one axis, deliberately: the slope is
the measurement. If only one slot survives, submit **conc10** — it is the smallest
departure from the incumbent, so the downside is bounded and the information per unit of
risk is highest.

**Not submitted, and why.** The three NaN-outside twins (`.tif` without `-zeros`) are the
spec-literal encodings (published spec: null outside the footprint) but the repo's shared
validator rejects NaN pixels and the *incumbent itself* is a zeros-outside file, so the
zeros twins are the proven-submittable encoding. See `docs/SUBMIT.md`.

## Weeks to the deadline (2026-12-03) — CONCENTRATION session's view

* **wk 1 (this week) — submit the three CONCENTRATION arms** above, one per slot, and
  paste the three receipts into `ledger/submissions.csv` (`receipt_score`, `receipt_date`).
* **wk 2 — the pivot.** Whatever the slope says, wk 2 moves to the term that the metric
  algebra says is worth ~+0.048 DTI per 1,000 units of truth credit `T`: **SNAP**
  (move each dot ≤ 2 px onto the strongest TMI / gravity-gradient / scarp response in its
  window, same count, same exclusions). The 57-channel stack and the shared edge channels
  already exist in this repo (`src/gems85/features.py`: `tmi_edge`, `rtp_edge`, `grav_edge`,
  `tophat2`, `ridge_s1..s3`); it needs the 419 MB competition feature stack restored
  (`scripts/restore_data.py --groups core`, 5 pinned parts).
* **wk 3 — PRUNE arms, if and only if SNAP is not yet read.** Exclusion radius 3 px
  (the metric's own 300 m kernel radius) with the count held at 37,654; the family record
  says the 2 px prune was worth +0.0070 live, and R0 still carries 2,171 dots in the
  2–3 px flank annulus. The refill pool is thin (74 legal cells at ≥ 3 px), so a PRUNE=3
  arm must refill from the 1–2 px shell and the arm is a *net* edit, not a pure delete.
* **wk 4 — combine the two axes that actually moved the score**, re-validate both files'
  format, and pick the final candidate plus a fallback.
* **wk 5 — re-validate** the chosen file and the fallback from disk (format gate, zero
  catalogue mass, sha256 not already in the ledger), write the final note, and stop.
* **wk 6 (to 2026-12-03) — buffer** for the Phase 2 brief (rules require reproducible code,
  one final file, and generative-AI disclosure) and for the `TRACKB` deliverable
  (strike-consistent traces ≥ 1 km as GeoJSON + raster, one evidence paragraph per trace)
  if the human opens it. TRACKB is *not* a weekly-slot candidate until the human says so.

## Axes proposed for later sessions (not built this session)

1. **SNAP** — hypothesis: the parent's dot positions inherit the ~300 m positional
   uncertainty of 400 m-spaced GeoDAWN lineaments, so a ≤ 2 px nudge to the strongest
   local edge/scarp response raises per-dot truth credit. Confounder: the strongest edge
   may be a lithologic contact or a dike, not a fault. Falsifier: live change within
   ±0.01 at matched count ⇒ the parent's positions were already at the local optimum.
2. **PRUNE=3** — hypothesis: the 300 m kernel radius means dots at 2–3 px from a mapped
   fault pay the full α=0.2 false-positive tax while capturing no new-fault credit.
   Confounder: new-fault truth *can* lie within 300 m of known traces (organiser forum
   11536), so the annulus is not provably empty. Falsifier: live score rises after
   pruning ⇒ the annulus carries real credit and the 2 px prune was over-fitted.
3. **T-RETRACE** (new, proposed here) — hypothesis: R0's 37,654 dots are a maximal 300 m
   cover of a 121,131-cell field, so the field's *unreached* cells are the cheapest
   unexplored truth; emit the ~74 legal ≥ 3 px cells as a small add-on and see whether
   marginal credit beats the 0.059 bar. Confounder: only 74 cells exist, so the arm has
   almost no statistical power; its value is as a bound on the "coverage is exhausted"
   claim. Falsifier: live change within ±0.01 ⇒ coverage is saturated and any future gain
   must come from a *better detector*, not from a different thinning of this field.

### Also proposed by the parallel RELIEF session (`arena/3dd0b94c`, 2026-10-23) — not built

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

---

## Session 2026-10-23 (branch `arena/991f7136-gemsdoe85`) — AXIS chosen here: **SPACING**

The human has delegated axis choice. Axis availability was checked against this ledger first:
PRUNE ×6, SNAP ×3, CONCENTRATION ×3, RELIEF ×3, MASS ×3 (this branch) are already built.
**SPACING had no row**, so it is the only listed axis that adds new information this week.

**The axis is a negative result, and that is its value.** The packing-ceiling hypothesis —
"R0 is packed at 2.828 px, so a truth pixel between two dots can only earn 0.53; halving the
along-trace spacing is nearly free profit" — is **false under the competition metric**, and the
reason is arithmetic: a dot's marginal T is largest where it is the *sole* cover of a pixel
(credit ≈ 1.0), and a gap filler by construction lands where two dots already give 0.53. Measured,
not assumed: T falls 76,726 → 74,686 → 72,302 as gap dots are added at constant count.

| order | file | change | prediction (MODEL) | what the result changes |
|---|---|---|---|---|
| A | *(not a slot — already decided)* | — | — | Do not build further gap-filling or TRACKB-scale interpolation on the "spacing ceiling" story; it is refuted on the metric's own terms. |
| B | `spacing-fill10-20261023-93975107` | 3,765 isolates → 3,765 higher-marginal-credit sites at ≥2.0 px, count fixed | **+0.005** | The only SPACING file with a positive prediction. If a slot is otherwise idle, this is the cheap count-neutral alternative to MASS. |
| C | `spacing-infill10-20261023-f3b2aa49` | 3,765 isolates → 3,765 trace-gap midpoints | **−0.008** | Run **only** as the twin of B: the *contrast* (0.013) is the measurable quantity, and it decides whether arrangement matters at all. |

Neither SPACING file should displace a PRUNE-ladder slot: the ladder's rungs predict +0.005 to
+0.007 with an already-measured live anchor (≤1 px +0.0108, ≤2 px +0.0070, owner-reported), while
these predict inside the ±0.01 no-evidence band. **Recommended slot order this week is unchanged
from the PRUNE section above**, with `spacing-fill10` as the substitute if a slot would otherwise
go unused or if the ladder has been falsified.

Also on file from this branch: **MASS ×3** (`mass-m20` −0.081…+0.007 bracket, `mass-m10`,
`mass-p10` +0.020 circular), built earlier today under the human's then-explicit assignment. The
`main` register (IR-V2-08) already measured mass-down as harmful on its SGMC proxy, which is why
the MASS brackets, not their point estimates, are what the human should read.

### Axes for week 2+ (proposed here, not built)

1. **CATFLANK** — mass only in the 3–6 px ring around the catalogue (free credit on the
   new-fault side, per the algebra's 0.056 bar). *Confounder:* the mapped fault's damage zone sits
   in the same ring. *Falsifier:* doubling the ring changes nothing.
2. **PURITY** — rank by local field coherence at the 400 m survey limit instead of raw credit.
   *Confounder:* coherence is also what a broad fold axis looks like. *Falsifier:* PURITY and MASS
   deltas identical.
3. **DOSE** — a 5-point count ladder at fixed spacing. Blocked today: the 2.828 px packing is
   saturated above 37.7 k (only 605 free sites), so a ladder requires re-packing first.
