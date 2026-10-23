# SLOT_PLAN — 3 scored submissions per rolling week, ONE entity, deadline 2026-12-03 (provisional)

**State (2026-10-23, `arena/28da814f-gemsdoe85`):** Parent R0 is `h33-h33-2-b2` (`e5eb6e7e`, 37,654 dots; live `0.2778` is a **CLAIM**, not a receipt; recipe-rebuilt and byte-verified against `baeae321…` / `c55bafc4…`). The brief leaves `AXIS` blank for human assignment (`IR-V2-13`). The three `PRUNE` candidates below were built and gated in `arena/e081f5da` (`ledger/submissions.csv`, `status = BUILT`, `receipt = N`); each `(parent, axis, value)` is built once across all sessions, so they are re-verified from disk and not duplicated. `TOP_PUBLIC` (with date), incumbent receipt, rolling-week slots remaining, and deadline/timezone confirmation must be supplied by the human; no other target number is valid.

## Next 3 slots in order (if human confirms `AXIS = PRUNE` and quota permits)

| # | Upload file (fallback: `-zeros.tif` twin) | Change vs R0 | Predicted live Δ (MODEL) | What the result would change |
|---|---|---|---:|---|
| 1 | `releases/h33-2-b2-prune3-20261023-fb308615.tif` | drop 2,171 dots at `2 < d_cat ≤ 3 px` → 35,483 (−5.766%) | **+0.007** (+0.001…+0.012) | Receipt Δ ≥ +0.01 confirms the catalogue-shadow mechanism beyond 200 m and advances slot 2; Δ ≤ 0 falsifies further pruning and switches wk 2 to a human-assigned non-PRUNE axis |
| 2 | `releases/h33-2-b2-prune4-20261023-2880b0e9.tif` | drop 3,825 dots at `2 < d_cat ≤ 4 px` → 33,829 (−10.158%) | **+0.003** (−0.004…+0.010) | Brackets optimal shadow width: prune4 ≥ prune3 ⇒ shadow ≥ 400 m (unlocks slot 3); prune4 < prune3 but > R0 ⇒ optimum bracketed at 300 m (`prune3`) |
| 3 | `releases/h33-2-b2-prune5-20261023-7ebfc408.tif` | drop 5,637 dots at `2 < d_cat ≤ 5 px` → 32,017 (−14.971%) | **−0.003** (−0.012…+0.006) | Spend **only** if slots 1 and 2 both receipt ≥ 0.2778. Δ ≥ +0.01 extends the collar sweep; Δ ≤ 0 closes `PRUNE` and moves to the next assigned axis |

Live changes under `0.01` are **no evidence** (public chunks only; private chunks and Phase-2 expert-expanded labels may differ). Upload at most one encoding per slot (`-zeros.tif` twins score identically). Count-holding refill on `H19-5` at 2.8 px was measured infeasible (`475` capacity vs `2,171` removed; `IR-V2-09`).

## Weeks to the deadline (41 calendar days from Oct 23 to Dec 3; default plan)

- **Default plan (brief §7):** **wk 1–2:** `MASS`, `CONCENTRATION`, `SNAP`, `PRUNE`, `RELIEF` (one human-assigned axis at a time; resolve `IR-V2-03` `<3 px` R0 flank conflict before any non-PRUNE edit); **wk 3–4:** combine the two best receipt-backed axes one change at a time; **wk 5–6 (to Dec 3):** confirm, choose the ONE blind final file and one encoding fallback, and re-validate the format of both with `scripts/gemsdoe85_prune_session.py`.
- Quota per https://docs.nlr.gov/docs/fy26osti/96647.pdf (3 scored/rolling week, 1 final); confirm deadline/timezone on https://www.drivendata.org/competitions/306/competition-doe-gems/ .

## Proposed better axes for later sessions (do NOT build this session)

1. **PRUNE-EXCHANGE (replaces MASS deletion):** relocate removed `2 < d_cat ≤ 3 px` flank dots along-strike onto corroborated off-catalogue ridge segments (`d_cat > 5 px`) at fixed 37,654 dot count. **Mechanism:** isolates spatial collar removal from total mass change $S$. **Confounder:** tighter along-strike spacing alters kernel overlap $M$. **Falsifier:** fails to beat removal-only `prune3` or a matched-count random-relocation control by ≥ 0.01 RECEIPT.
2. **RELIEF basin-ward shift (`det_elev` / `det_elev_slope` terciles):** shift 10–15% of mass from exposed range-front (`T3`) into concealed piedmont/basin (`T1/T2`) segments at fixed count (R0 has 20.4% dots in `det_elev` `T1` vs 30.4% of catalogue faults). **Mechanism:** unmapped Quaternary faults are preferentially concealed under low-relief alluvial fill. **Confounder:** GeoDAWN flight-height / basin-sediment attenuation and LiDAR coverage edges. **Falsifier:** receipt loss ≥ 0.01 or sign reversal inside the LiDAR-covered subset.
3. **Cross-physics strike agreement (magnetic + gravity gradients):** reallocate 10–15% of dots toward ridges where `tmi_hg` and `iso_grav_anom_hg` share local strike within 15° at matched count. **Mechanism:** basement-cutting fault conduits juxtapose both density and susceptibility, whereas surficial lava margins/shorelines rarely align in gravity. **Confounder:** pluton/lithologic contacts can align in both fields. **Falsifier:** no ≥ 0.01 RECEIPT gain over R0.
