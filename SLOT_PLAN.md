# SLOT_PLAN — one page, GEMSDOE85, session `arena/fe618e6b-gemsdoe85` (2026-10-23)

**AXIS (human-assigned this session): `PRUNE`.** Parent **R0 = `h33-h33-2-b2`** (`c55bafc4…`,
37,654 dots, 0.2778 **CLAIM** — no receipt exists anywhere in this repo).

**What the axis already proved on the live scorer** (both rungs re-derived from pinned bytes today,
not from prose):

| rung | edit | dots | live | Δ |
|---|---|---|---:|---:|
| 1 | − 3,891 dots at `d_cat ≤ 1 px` | 44,090 → 40,199 | 0.2600 → 0.2708 | **+0.0108** |
| 2 | − 2,545 dots at `1 < d_cat ≤ 2 px` | 40,199 → 37,654 | 0.2708 → 0.2778 | **+0.0070** |

Both are pure denominator edits (`T` cannot move: those dots sit on/beside *masked* truth), and both
obey `ΔDTI = DTI·αn/(D − αn)` with the **same** invariant `T ≈ 5,470`, predicting the third rung to
≈7 %: `+0.0062` for the 2,171 dots still at `2 < d_cat ≤ 3 px`. That is the whole bet.

## Next 3 slots, in order

| # | file (upload the `-zeros` twin) | change | prediction (MODEL) | what the result would change |
|---|---|---|---|---|
| 1 | `releases/h33-b2-prune-x3-nofill-20261023-89498c48-zeros.tif` | delete the 2,171 ring dots → 35,483 | **+0.0062 → 0.2840** `[0.2820, 0.2860]` | ≥0.2840: the prune ladder is a live lever — next session spends `x4` (1,654 dots at `3 < d_cat ≤ 4 px`) instead of a new signal lane. 0.2780–0.2830: weaker but positive, combine with a second axis. ≤0.2778: **falsified** — catalogue-proximal mass is not monotone, stop pruning, and re-check the ledger's CLAIMs. |
| 2 | `…-prune-x3-pushout-20261023-ab917ea0-zeros.tif` | ring deleted, each ring dot re-placed just outside 3 px (count held, 37,645) | **≈0.2778** `[0.274, 0.283]` | Isolates *sign* from *mass*: `≈0.2840` ⇒ the ring dots were negative wherever they sit (the "new faults lie within 300 m" prior is refuted for this file); `≈0.2708` ⇒ they carried real credit and slot 1's gain came from mass, not purity. Only worth a slot if slot 1 lands inside `[0.2780, 0.2830]`. |
| 3 | `…-prune-x2-readd-20261023-dfe20999-zeros.tif` | re-admit the 2,545 dots (`1 < d_cat ≤ 2 px`) → 40,199 | **−0.0070 → 0.2708** `[0.268, 0.273]` | Calibration only, and only if slots 1–2 are ambiguous: it reproduces a support that already has a CLAIM of 0.2708. It is **not** a candidate. Its value is detecting a regime change (different chunk split / scorer) that would invalidate every number above. If you'd rather not spend a slot on a control, skip it. |

Upload **one file per slot**; both encodings of each variant exist (`…-zeros.tif` and the
NaN-outside twin). Send the note from `docs/SUBMIT.md`.

## Weeks to the deadline (2026-12-03; confirm on the competition page)

- **wk1 (this week):** slot 1 `x3-nofill`; slot 2 `x3-pushout` **iff** slot 1 ∈ [0.2780, 0.2830].
- **wk2:** `PRUNE x4` (`3 < d_cat ≤ 4 px`, 1,654 dots, predicted +0.004 if the ladder holds; the
  300 m kernel makes this an out-of-range extrapolation and the natural place for the ladder to die)
  + `SPACING` at matched count, since the ladder is spent once `T` is fixed.
- **wk3–4:** combine the two best axes (candidates on record: `CONCENTRATION` block rebalance and
  `SNAP ≤ 2 px`), one change at a time off slot 1's winner.
- **wk5–6:** confirm; pick the final file **and** a fallback, re-validate both against
  `sample_submission.tif`, and record which one is blind-chosen.

## Axes proposed for later sessions (mechanism / confounder / falsifier) — do not build now

1. **`BLOCKDENSITY` (km-scale reallocation).** *Mechanism:* hidden truth is clustered along
   basin-range-front systems, so expected credit per dot rises where dot density is high but not
   saturated. *Confounder:* density correlates with how well the parent's ridge detector already
   fits, so it can just re-express H19-5. *Falsifier:* reallocating 15 % of dots between 5 km blocks
   at fixed count changes nothing (±0.002).
2. **`STRIKE-CONTINUITY`.** *Mechanism:* the metric is a max-kernel dilation, so a *chain* of dots
   every ≤2 px along a real trace pays 1.0 per truth cell where scattered dots pay ~0.5; credit per
   dot should rise 30–50 % on line-like truth. *Confounder:* chains also align with mapped catalogue
   traces and get masked. *Falsifier:* chaining R0's own dots to a ≤2 px along-strike lattice at
   fixed count fails to beat R0 by more than 0.002.
3. **`FAR-FIELD ONLY`.** *Mechanism:* the strongest evidence in this lineage is that
   catalogue-adjacent mass is negative; the corollary is that the *uncovered* interior basins
   (`d_cat > 10 px`) are where `T` is missing (≈62 % of hidden truth weight is uncaptured).
   *Confounder:* those basins are also where the ridge detector is blind, so a naive shift just
   trades one kind of mass for another. *Falsifier:* moving 20 % of dots to `d_cat > 10 px` at fixed
   count does not raise the live score above R0.

## Ledger discipline

`ledger/submissions.csv` now carries the lineage (`CLAIM`) plus this session's three `BUILT` rows
with sha256, % changed and prediction. Fill `receipt_score` / `receipt_date` **from the submission
page receipt**, not from memory; a score without a receipt stays `CLAIM` and every model above
depends on it. Duplicate check is exact-hash plus repeated `(parent, axis, value)` only.
