# Session bf7be90f review (2026-10-22) — 3 passes, verdict: negative / BLOCKED

## Why did h33-h33-2-b2 score 0.2778? [OWNER-REPORT score; mechanism MEASURED in fleet]
1. Strong parent field (h19-5 multi-physics corroborated ridges: 0.1922 continuous).
2. Binary {0,1} emission (DTI strictly increasing in constant amplitude).
3. Poisson thinning ~2.8px: under the 300m triangular kernel (alpha 0.2, beta 0.8, official DrivenData #306 metric) adjacent dots duplicate coverage; spacing multiplies credit/dot. d2.8=0.2600, r1-solo=0.2708.
4. Catalogue-halo prune B2 (44,090->37,654 dots, >2px from catalogue): removes FP mass on faults the scorer masks. 0.2708->0.2778.
5. All-finite zeros encoding: immune to "Predicted values must be in range [0, 1]".
Algebra: a dot helps iff realised kernel credit k > 0.2*DTI (0.0556 at 0.2778; 0.0883 at 0.4413). Winner captures T~5,470, wastes ~94% of dots; FP tax = 42% of denominator. It is a well-priced bet, not a good map.

## Can we beat it?
Not with this file, on present evidence. GEO-Pb HOLDOUT-DTI 0.09838 [0.09022,0.10654] (gems85-holdout-1, 60,988 withheld) lifts only 1.3-1.4x over uniform random vs the incumbent's ~5x live. Transfer projection ~0.17-0.23 [MODEL]. Emission tuning is exhausted (family marginal 0.032/dot < 0.0556 bar). Only a surface raising credit-per-dot at ~38k dots (1.64x for 0.4413) can win. Ranked untried hypotheses already on file: docs/research/hypotheses.md (5) and research/hypotheses.md (4: paired basin-interface flexure first). None may be implemented until a lane is assigned.

## Pass 1 (verify): re-read written bytes with rasterio 1.4.4 - zeros primary: sha256 ba33ea18...a567f, 3730x3292 EPSG:32611 transform == sample, 0 NaN, min/max 0/1, 90,000 dots, 0 on catalogue. PASS. NaN twin: 7,111,787 NaNs - do not upload.
## Pass 2 (bugs fixed): (a) site said "OK TO DOWNLOAD AND SUBMIT" despite AGENTS.md BLOCKED rule + saturation certificate overlap 1.0 + lane unassigned -> banner/verdict corrected in scripts/build_site.py, README, root index.html; (b) NaN twin offered as download -> removed from builder; (c) duplicate_check.json is_duplicate=false contradicts its own thresholds (raw 0.991>0.7, lift 1.519>1.5) -> IR-85-10.
## Pass 3 (recheck): pytest, site rebuild + link check, validator re-run. Verdict remains negative. No new TIF generated: doing so would select a lane the brief never assigned and manufacture dots to dodge a binding gate (AGENTS.md 2-3,7) - a negative result is the deliverable.
