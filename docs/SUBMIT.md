# SUBMIT — how to upload (copy-paste)

**Do not submit without a human copying from here; no auto-submit code exists.**

## File to upload
`releases/h33-h33-2-b2-CONC10-20261023-7414b0c3.tif` **primary (NaN outside, per spec)**
- Fallback (if form rejects NaN outside): `releases/h33-h33-2-b2-CONC10-20261023-7414b0c3-zeros.tif` — human uploads **only one** per slot. Both score identically.

## Submission name (as entered on form)
`h33-h33-2-b2-CONC10-20261023-7414b0c3`

## Submission note (≤140 chars, copy exactly)
`h33-2-b2 CONC10 5km TMIhg prior, 10%+10%halo 37654 dots sep2.8 exc3 CV1.07 PRED+0.004 live` (108/140)

Alt notes:
- CONC15: `h33-2-b2 CONC15 5km TMIhg, 15%+10%halo 37654 dots sep2.8 exc3 CV1.13 PRED+0.005` (102)
- CONC20: `h33-2-b2 CONC20 5km TMIhg, 20%+10%halo 37654 dots sep2.8 exc3 CV1.14 PRED+0.003` (102)

## Format receipt (paste with submission)
- NaN primary: `sha256 7414b0c319af99e607c14fc5920d7635ba8da50336cba129b9962ff40fc78081` bytes 320473, EPSG:32611, 3730×3292, float32, 1 band, values [0,1], 0 NaN inside, NaN outside, 0 on catalogue, 0 within 3 px, re-read from disk PASS.
- Zeros twin: `sha256 f33caef9e6fb2fecb8f0758b3f629c6da4f17d8d1646850478e1732947a63a1a` bytes 276418, all finite, zeros outside, same checks PASS (exc3).
- All 3 variants share: CRS EPSG:32611, transform 100,0,243350,0,-100,4508550, resolution 100 m, bounds of sample_submission.tif, one band.

## After upload
Copy the receipt: score, date, slot usage → `ledger/submissions.csv` columns receipt_score, receipt_date, receipt Y/N. Fill TOP_PUBLIC in README with leaderboard high + date. Do not overwrite predicted_change.

## Mechanism cards (for slot rationale)

**CONC hypothesis (structural geologist):** Concealed Basin-and-Range normal faults under Quaternary alluvium produce weak but spatially coherent magnetic susceptibility contrasts; the total-field horizontal gradient (TMI_hg) is sensitive to basement offset but each pixel is weak (single-band AUC ~0.57). Aggregating to 5-km blocks averages out acquisition noise while preserving range-front vs basin signal.

**Mechanism:** By moving 10-20% of dots from lowest-quartile TMI_hg 5-km blocks (deep basins, low susceptibility contrast) to highest-quartile blocks (range fronts, intrabasinal horsts), credit per dot should rise because high-gradient blocks have higher hidden-fault density. Halo 300 m (3 px) removes flank false positives that cost α=0.2 per wasted dot (incumbent’s +0.007 live from 2-px pruning; prior E2 shows +0.009 holdout 2→3 px).

**Non-fault mimic:** Distal alluvial-fan toes, Lake Lahontan 1335-m shorelines, and erosional volcanic mesa margins also generate linear TMI_hg edges; they will be sampled as false positives. Declared irreducible — mitigated only by 300-m halo, not by gradient alone.

**Predicted live:** CONC10 +0.004, CONC15 +0.005, CONC20 +0.003 (diminishing; 20% may over-cluster FP). All MODEL, not score.

**Falsifier:** If CONC10 live ≤ −0.01 vs R0, prior is wrong (blind faults favor low-gradient basins) or halo over-exclusion removed true near-catalogue faults (organizer says new truth can be within 300 m of known traces). Next axis PRUNE (exc1 vs exc3) separates halo vs concentration effects.

