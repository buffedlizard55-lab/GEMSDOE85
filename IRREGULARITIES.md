# IRREGULARITIES — decisions that change what to do

**2026-10-23 — Parent halo mismatch (IR-61e-001)**
R0 `h33-h33-2-b2` (c55bafc4) claims exc2 (none within 2 px Euclidean, 0 dots ≤2.0 vs distance map) and indeed has 0 within Chebyshev 1 and 0 within Euclidean 2. It has 1,611 within Chebyshev 2 and 3,843 within Chebyshev 3. Brief hard constraint requires “zero mass on catalogue and keep ≥3 px unless AXIS=PRUNE”. Therefore any non-PRUNE variant must be exc3. Our CONC variants enforce exc3 (halo 3 px Chebyshev) — change vs R0 is 10.2% halo cleanup + 10-20% CONC move = 18.8-27.6% total. This is intentional compliance, not a bug. Decision impact: live comparison of CONC vs R0 confounds concentration with halo tightening; expect +0.009 holdout exc2→exc3 effect from prior session (0.133→0.142) to bias upward. Falsifier: if CONC live underperforms R0, cannot tell if due to bad prior or halo over-exclusion — need PRUNE control next week to separate.

**2026-10-23 — Parent ranking not stored (IR-61e-002)**
Brief requires MASS variants “by parent’s own ranking (rebuild from recorded recipe if not stored)”. No ranking file exists for h33 lineage; only binary dot rasters (h19-5 121k, d2.8 44k, h27-4 40k, h33 37k) are in registry. Rebuilding ranking from binary nested inclusion is underdetermined (within-tier order unknown). Therefore this session chose CONCENTRATION (no ranking needed) first, deferring MASS until recipe is recovered or GAPVENT proxy justified. Decision impact: MASS hypothesis (tail dropping) not tested this session; P(win) impact deferred to wk3.

**2026-10-23 — Holdout vs live divergence (IR-61e-003)**
Parent R0 holdout (gems85-holdout-v1.0.0, 60,988 withheld, 4 folds) scores 0.00479 [MODEL, not live]; CONC variants score 0.00000 on same instrument (tp_w 0). Prior session 7ded4c0a measured holdout-live ρ = −0.222 (n=17, p=0.39) and dots-live ρ = −0.926. Holdout cannot fairly score static rasters that already hard-excluded catalogue (IR-85-001). We report holdout as PROXY only (never a gate) and do not gate promotion on it, per brief §6. Decision: submit CONC10 first; holdout 0 is not evidence against live potential, but a live negative with concentration will falsify prior.

No other brief-vs-rules conflict detected this session; if found it will be logged here.
