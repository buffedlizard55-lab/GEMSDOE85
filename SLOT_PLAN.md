# SLOT_PLAN — GEMS Prize 2026-10-23

**Deadline 2026-12-03** (confirm on competition page). **Entity quota 3 scored/week, 1 final blind.**

## Current state
- **Parent R0** `h33-h33-2-b2` (c55bafc4, 37,654 dots, sep≈2.8, exc2) CLAIM 0.2778 (no receipt yet in ledger)
- **This session (arena/61e6332f)** built **AXIS=CONCENTRATION** 10/15/20% moved 5-km blocks prior=`tmi_hg`, all exc3 compliant, CV 0.96→1.07-1.14.
- Slots used this rolling week: 0/3 (these 3 files are BUILT, not yet submitted). Human must submit ≤3.

## Next 3 slots (in order) — wk1-2 of plan

| Slot | Axis/Value | What it changes vs R0 | Expected live delta | What result teaches |
|------|------------|----------------------|---------------------|---------------------|
| **1** | **CONC10** `h33-h33-2-b2-CONC10-20261023-7414b0c3.tif` (18.8% changed, CV 0.962→1.073) | Move 10% mass (3,765 dots) from bottom-quartile 5-km TMI-hg blocks to top-quartile, plus enforce 300 m catalogue halo (3,843 dots). Count fixed 37,654, sep 2.8, exc3. | **+0.004** if high-gradient blocks host 1.3× hidden-fault density; −0.002 if prior is noise. | Tests “concentration helps” at minimal displacement; if it scores ≥+0.01 live, prior is real and we should push to 15-20%. If ≤−0.01, prior is anti-correlated (basin-floor blind faults dominate) — abandon CONC. |
| **2** | **CONC15** `h33-h33-2-b2-CONC15-20261023-ec24d9e3.tif` (23.1% changed, CV 1.134) | Same mechanism, 15% move (5,648 dots). Stronger concentration, same halo fix. | **+0.005** (peak) | Tests dose-response: if CONC10 positive and CONC15 more positive, optimum is beyond 10%; if CONC15 < CONC10, optimum is ~10% and over-concentration clusters FP. Picks best CONC dose before combining. |
| **3** | **CONC20** `h33-h33-2-b2-CONC20-20261023-dd3988a9.tif` (27.6% changed, CV 1.138) | 20% move (7,531 dots), expanded low pool to 50% of blocks for source. | **+0.003** (diminishing) | Stress test: if 20% still positive, concentration effect saturates slowly — we can safely push to 25-30% next week. If negative, hard ceiling at ~15% — next axis shifts to PRUNE/RELIEF instead. |

**Why CONC first?** Default plan wk1-2 is MASS, CONCENTRATION, SNAP, PRUNE, RELIEF. MASS needs parent ranking (not stored; rebuilding risks leakage) and is confounded with field; SNAP needs TMI/gravity gradient bands we have but displacement audit required. CONC is cleanest controlled edit: same count, same exclusion (exc3), only spatial allocation changes, CV before/after reported, mimic named, falsifier explicit.

## Weeks to deadline

- **Wk2 (2026-10-27)** PRUNE variants: `h33-2-b2` → exc1 / exc2 / exc3 with refill to 37,654. Tests halo 200 m vs 300 m (organizer says new truth can be within 300 m of known faults). If exc3 (our CONC baseline) already beats exc2 live, confirms flank-tax hypothesis; if exc1 wins, new faults are near known faults and we should relax halo.
- **Wk3 (2026-11-03)** MASS (−10%, +10%) using parent’s own ranking rebuilt from h19-5→d28 lineage (if recipe recovered) or GAPVENT proxy. Isolates budget vs field confounding. If −10% (drop tail) beats R0, parent was over-budget; if +10% beats, under-budget.
- **Wk4 (2026-11-10)** SNAP: move each dot ≤2 px to max TMI_hg / iso_grav_hg edge in window (provided bands). Same count, same exc3, report mean displacement. Tests whether sub-pixel scarp alignment raises credit/dot.
- **Wk5-6 (2026-11-17)** Combine two best axes (e.g., CONC15 + PRUNE3 or CONC + SNAP) at matched count. Confirm, choose final file + fallback (second-best), re-validate format of both (17 checks, re-read from disk, sha256 not in ledger).
- **Final (by 2026-12-03)** Submit ONE final blind-chosen file. Slots left this week: **3/3**, total remaining: **~12–15** regular + 1 final.

**Gates:** format check vs sample_submission.tif (CRS/shape/transform/dtype/band/values, no NaN inside, NaN outside), zero catalogue mass, sha not in ledger, parent-diff recorded, re-read after write. PROXY hide-and-recover, canary AUC>0.90, SGMC control are REPORT ONLY.

**If this brief conflicts with official rules/page, they win — log in IRREGULARITIES.md.**
