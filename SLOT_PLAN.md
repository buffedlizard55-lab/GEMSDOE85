# SLOT_PLAN — provisional, human authorization required

**State (2026-10-23):** Parent R0 is `h33-h33-2-b2` (37,654 dots; `0.2778` is a CLAIM, not a receipt). The current brief leaves AXIS blank and reserves assignment to the human. The earlier AI-selected PRUNE axis is not treated as a human assignment. No new variant was built this turn; the three PRUNE candidates below already exist in the ledger and must not be rebuilt. `TOP_PUBLIC` (with date), incumbent receipt, weekly slots remaining, and deadline/timezone confirmation are still missing. `TOP_PUBLIC` must come from the human's leaderboard observation; no other target number is valid.

## Next three candidate slots (only if human confirms AXIS = PRUNE and quota permits)

| Order | Candidate / change from R0 | Predicted live Δ (MODEL) | What the result would change |
|---|---|---:|---|
| 1 | `releases/h33-2-b2-prune3-20261023-fb308615.tif`; remove R0 dots with 2 < d_cat ≤ 3 px; 37,654 → 35,483 (5.766%). | +0.007 (range +0.001…+0.012) | A receipt gain ≥0.01 supports a residual catalogue-shadow effect; otherwise treat as no evidence and switch axis. |
| 2 | `releases/h33-2-b2-prune4-20261023-2880b0e9.tif`; remove dots with 2 < d_cat ≤ 4 px; 37,654 → 33,829 (10.158%). | +0.003 (−0.004…+0.010) | Compare to slot 1 to bracket the shadow width; a change under 0.01 is no evidence. |
| 3 | `releases/h33-2-b2-prune5-20261023-7ebfc408.tif`; remove dots with 2 < d_cat ≤ 5 px; 37,654 → 32,017 (14.971%). | −0.003 (−0.012…+0.006) | Spend only if human/account constraints allow and slots 1–2 both receipt at least the R0 CLAIM value; a gain ≥0.01 would justify a wider shadow test. |

Each has a `-zeros.tif` encoding twin; upload only one encoding per slot. No exact hash or `(parent, axis, value)` repeat. PRUNE's requested count-preserving refill was measured infeasible on the parent's residual ridge at the same 2.8 px spacing (see `evidence/session_prune_receipt.json` and IR-V2-09); the existing candidates are removal-only. This limitation must be accepted before choosing PRUNE.

## Calendar and decision gates

- **Week 1 (Oct 23–29):** only the first candidate after human confirms axis, TOP_PUBLIC, account quota, and incumbent receipt. One entity; maximum three scored submissions in a rolling week.
- **Week 2 (Oct 30–Nov 5):** continue the PRUNE dose ladder only if receipts justify it; otherwise assign a distinct axis/value and pre-register its falsifier.
- **Weeks 3–4 (Nov 6–19):** test the best supported axis once, then a matched control if a slot is available; do not spend on exact repeats.
- **Weeks 5–6 (Nov 20–Dec 3):** confirm the best supported candidate, choose final + fallback blind, and revalidate both formats. Deadline and timezone are provisional; human must confirm on the competition page.

## Better axes for later human assignment (not built)

1. **PRUNE-EXCHANGE:** move removed flank mass along the same ridge to off-catalogue gaps, count fixed. Mechanism: distinguish position from mass. Confounder: tighter spacing changes overlap. Falsifier: matched-count random relocation performs as well or better.
2. **Cross-physics strike agreement:** favor lineaments independently aligned in magnetic and gravity gradients at matched count. Mechanism: structural boundaries may share strike. Confounder: lithologic contacts can align across both fields. Falsifier: no ≥0.01 receipt gain over a matched single-physics control.
3. **Persistence vs closed edges:** favor kilometre-scale open, strike-consistent boundaries over closed rims. Mechanism: through-going faults persist across scales. Confounder: shorelines/lava margins also persist. Falsifier: no receipt gain and no better blind geological review.

All predictions are MODEL; hide-and-recover and SGMC are PROXY only, never gates. No live score is inferred from local proxies.
