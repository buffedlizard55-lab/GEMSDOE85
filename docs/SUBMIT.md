# SUBMIT — file, name, note, format receipt

One entity, three scored submissions per rolling week plus one final. **The human submits from
their own account; no agent does, and nothing here logs in or scrapes.**

Slots this week: **3 of 3 left, 0 used** (human, 2026-10-23).
Parent: `h33-h33-2-b2`, live 0.2778 — **CLAIM, no receipt in this repository.**
TOP_PUBLIC: **not supplied by the human** — do not fill it in from memory or from the README's
cited 0.4413.

## Order of upload (see SLOT_PLAN.md)

### Slot 1 — control: the mandatory ≥ 3 px exclusion, nothing else
* **File:** `releases/h33-h33-2-b2-prune3-20261023-175fefcf-zeros.tif`
* **sha256:** `175fefcf0d4b0990c9723948e154356c41bae465c8ad815ed8c2166dc10d6ba5`
* **Size:** 150,352 bytes · 37,654 unit dots · 4.28 % of dots moved · mean 0.076 px
* **Submission name (≤140):** `GEMSDOE85 prune3 | control: 3px catalogue exclusion only, no snap`
* **Note (≤140):** `parent h33-h33-2-b2 (0.2778 CLAIM); 1611 dots moved off the 2.24-2.83px catalogue ring to >=3px; predicts +0.000..+0.005`

### Slot 2 — the assigned SNAP axis, least destructive setting
* **File:** `releases/h33-h33-2-b2-snapd2t20-20261023-f9c328a5-zeros.tif`
* **sha256:** `f9c328a5ba6fb954ae295939ea1e0487a6f40742fa01df88115085034372adbf`
* **Size:** 150,586 bytes · 37,654 unit dots · 7.32 % of dots moved · mean 0.136 px · Jaccard vs parent 0.864
* **Submission name (≤140):** `GEMSDOE85 SNAP t0.20 | 37654 dots snapped 2px to TMI+gravity-HG crest where gain>=0.20 rank`
* **Note (≤140):** `parent h33-h33-2-b2; 7.3% of dots to PF contact crest (tau .20, d<=2px, mean 0.14px); predicts +0.000..+0.008`

### Slot 3 — reserved (see SLOT_PLAN.md's decision rule)
`releases/h33-h33-2-b2-snapd2t00-20261023-2df068e1-zeros.tif`
(sha256 `2df068e11c35a9407a94e80052dd48253cf883a154c5f60495203b57f5562278`) — **only** if slot 2
comes back at Δ ≥ +0.010. Otherwise do not spend a slot on it: it moves 98.53 % of dots and its
Jaccard overlap with the parent is 0.0074, i.e. it is a different map, not a refinement.

## Format receipt (all four files, re-read from disk after writing)

| check | value |
|---|---|
| CRS | EPSG:32611 |
| shape / transform | 3730 × 3292, affine (100, 0, 243350, 0, −100, 4508550) — identical to `sample_submission.tif` |
| dtype / bands | float32 / 1 |
| values in [0, 1] inside footprint | yes, min 0.0, max 1.0, 37,654 pixels equal to 1, all else 0 |
| NaN/Inf inside footprint | none |
| outside footprint | 0.0 in the `-zeros` twins (repo policy); NaN + `nodata=nan` in the `-nan` twins (competition spec) |
| mass on mapped catalogue | 0 pixels |
| min distance to catalogue | ≥ 3.0 px (parent: 2.236 px) |
| sha256 already in ledger | no — all four are new |
| validator | `vendor/gems57/gates.format_report` + `gems57.validate.validate`: **PASS** for all four `-zeros` twins |

**Which twin to upload.** The `-zeros` twin passes both the competition format rules and this
repository's stricter all-finite export policy, and it is what the parent lineage shipped. The
`-nan` twins match the competition spec (NaN outside the footprint, `nodata=nan`) and pass every
substantive check — correct grid, in-footprint range, zero catalogue mass — but fail the repo's
all-finite policy on the 7,111,787 outside-footprint NaN cells. **Upload the `-zeros` twin.** The
`-nan` twin is published only because the session brief asks for a spec-form twin.

**What a PASS here is not.** Format validity is not geological skill, not uniqueness clearance,
not slot approval, and not organizer acceptance. A live change under 0.01 on the public chunks is
no evidence.
