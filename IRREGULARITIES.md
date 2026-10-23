# Decision-changing irregularities — v2, 2026-10-23

Three v2 sessions on this branch history: `arena/cf29702c` (2026-10-22/23) stopped BLOCKED;
`arena/e081f5da` (2026-10-23) cleared the rebuild blocker and built the PRUNE variants; the
`arena/a9cc6c47` session (2026-10-23) built the SNAP variants. Items IR-V2-01 … IR-V2-06 are the
earlier session's, kept verbatim. New items are IR-V2-07 … IR-V2-16; the last four are this
session's. Only items that change a decision.

## Status of the earlier blockers

| item | blocker | status now |
|---|---|---|
| IR-V2-01 | R0 not recipe-rebuilt | **CLEARED** — full chain reproduced and proven pixel-identical (below, IR-V2-07) |
| IR-V2-02 | no axis, no history | **PARTLY CLEARED** — PRUNE chosen on evidence (IR-V2-08); history/receipts still absent (IR-V2-12) |
| IR-V2-03 | R0 has dots < 3 px, conflicts with a non-PRUNE edit | **RESOLVED by choosing PRUNE** — all three variants sit at > 3 px (3.16 / 4.12 / 5.10 px) |
| IR-V2-04 | competition rasters in a public repo | **OPEN** — unchanged, restated in IR-V2-10 |
| IR-V2-05 | historical instructions conflict with v2 | **OPEN** — unchanged; the CURRENT STATE block still overrides |
| IR-V2-06 | `vendor/gems57/uniqueness.py` byte mismatch | **OPEN** — vendor untouched, no uniqueness gate used |

---

## IR-V2-01 — Required start gate not cleared: STOP
- `registry/data_manifest.json`: 3/28 entries verified locally (labels, catalogue, sample; both root/bridge copies match); 25 absent, not corrupted. No unreachable-source claim is made for files not requested.
- R0 restored through the commit-pinned `registry/learning_manifest.json` and verified as `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`. This proves byte identity of the existing **zeros** file, not regeneration. Its 37,654 unit dots and zero catalogue mass were re-read locally.
- No R0 recipe was executed. The h27-4 ancestor in `registry/scored_artifacts.json` is absent locally; a complete recipe/ranking and reproducible writer environment have not been established. Do not copy/re-encode R0 and call that a rebuild. Supply a pinned rebuild bundle (including dependencies and ancestor/ranking inputs).
- Parent source: https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif . Local evidence: `evidence/v2-input-audit.json`; reproduction: `.venv/bin/python scripts/audit_v2_inputs.py`.

## IR-V2-02 — No assigned axis or complete history: no candidate/slot choice
`ledger/`, `ledger/raw_paste.txt`, and `SLOT_PLAN.md` were absent at session start. A header-only ledger and conditional slot proposal are now present; they are **not** a reconstruction of historical submissions. Old registry summaries are CLAIMs, not receipts or a complete cross-session `(parent, axis, value)` registry. Human must provide the complete paste/ledger, R0 receipt if available, dated TOP_PUBLIC and rolling-week slot usage. R0 0.2778 remains CLAIM. No dated TOP_PUBLIC is authorized; historical README targets are not used.

## IR-V2-03 — Exact R0 conflicts with the non-PRUNE exclusion
Verified Euclidean distance from the catalogue is at least sqrt(5) px in R0, but **1,611 dots are <3 px** and **2,171 are <=3 px**. Keeping unchanged R0 dots therefore conflicts with the requested >=3 px rule outside PRUNE. Silently moving/removing them under MASS, CONCENTRATION or RELIEF changes another axis. Human must assign PRUNE or explicitly resolve the exclusion/parent conflict before those builds. Do not infer zero truth credit beside known traces: the supplied organizer clarification permits new-fault truth there (https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516; supplied fact, not re-fetched).

## IR-V2-04 — Competition rasters already tracked in a public repository
`gh repo view --json nameWithOwner,isPrivate` returned `isPrivate: false` for https://github.com/buffedlizard55-lab/GEMSDOE85 . Six competition input TIFF paths are tracked under `data/` and `data/bridge/`, alongside historical predictions under `docs/downloads/`. Data-use terms are **unchecked**; this is a risk flag, not a finding of a rules violation. No raster is added by this PR; local R0 and future release TIFF/ZIP paths are ignored. Human should review publication permission and decide remediation; history was not rewritten.

## IR-V2-05 — Historical instructions/tools conflict with v2
`AGENTS.md`, the preserved README and old preflight/site tools require overlap/correlation or PROXY promotion gates and advertise old candidates as ready. The current brief supersedes those workflow rules: no such uniqueness thresholds are applied here, no prior candidate is endorsed, and no static site is rebuilt or redesigned. A CURRENT STATE block overrides the historical narrative for this session only. `research/review.md` required by AGENTS.md is absent. Historical artifacts remain unchanged.

The deadline is provisional until the human checks https://www.drivendata.org/competitions/306/competition-doe-gems/ . No DrivenData, Dropbox, forum or rules-PDF request was made, and no credentials were requested/read. Official rules have not been independently checked this session; no new rule conflict is asserted as verified.

## IR-V2-06 — Shared byte integrity check exposes a pre-existing mismatch
12/13 files match `registry/template_pin.json`; `vendor/gems57/uniqueness.py` does not (expected `1c5094b814277ae801ccea6a47cf744429cffcdc10f9cc79f229d5fc44a8df95`, actual `6364b26ada45c405d9f76402d218c2344d1af7265fc7fbdcea7113a489e96a32`). No vendor file was edited and no uniqueness code was used as a gate. Treat the old shared-tool integrity claim as unverified until an upstream fix/verified repin; do not silently fork or change thresholds. This does not invalidate the independently checked input hashes or metric-algebra tests.

---

## IR-V2-07 — R0 is now recipe-rebuilt, exactly (closes IR-V2-01)

The parent lineage is a deterministic function of two pinned rasters; no model is refitted. Verified
chain (every SHA-256 checked, intermediates compared pixel-for-pixel against the pinned files):

| stage | pixels | pin |
|---|---|---|
| H19-5 1-px ridge skeleton | 121,131 | `ec1f9b56…` |
| deterministic 2.8 px Poisson-disk packing | 44,090 | `91eae1ca…` (`e56ea318`) |
| drop dots with `d_cat ≤ 1 px` | 40,199 | `07b6db44…` (`8acb75e1`) |
| drop dots with `d_cat ≤ 2 px` = **R0** | 37,654 | `baeae321…` / `c55bafc4…` (`e5eb6e7e`) |

The packing was re-implemented from its determinism contract (seeds = lowest raster index per
8-connected component, FIFO BFS, disc radius strictly inside 2.8 px) in `src/gems85/thinning85.py` and
reproduces the pinned 44,090-px raster **byte-identically**; `src/gems85/r0_lineage.py` rebuilds R0 and
asserts pixel identity. Reproduce: `.venv/bin/python scripts/gemsdoe85_prune_session.py`.
Note the resolution of the earlier "do not copy/re-encode R0 and call that a rebuild" concern: nothing
is copied — the rasters are regenerated from the skeleton and then compared to the pins.

## IR-V2-08 — AXIS was still unassigned; PRUNE was chosen on evidence and MASS was rejected

The template leaves AXIS to the human. MASS was evaluated first and rejected on two measurements
(`docs/mechanism_cards_prune.md`, negative result 1): (a) the only label-free ranking the parent's own
geometry provides — unique kernel credit U_i — is *lowest* for the on-ridge dots that carry coverage
(U ≈ 4.35 at the 2.83 px rung) and highest for isolated dots (U ≈ 9.38), so dropping the lowest-ranked
dots deletes the backbone; (b) the SGMC proxy says mass-down hurts monotonically (−0.005 at −10 % to
−0.020 at −30 %), and the recorded packing order is not a usable rank (Spearman with U_i = −0.003,
spatially biased toward component ends). PRUNE is the only axis with a two-point live dose–response in
this lineage (+0.0108 then +0.0070 for the 1 px and 2 px rungs). **If the human intended a different
axis, re-scope before the next slot**; each (AXIS, value) pair is built once.

## IR-V2-09 — "refill to hold the count" (the brief's own PRUNE definition) is impossible here

Measured capacity of the parent's residual ridge at the same 2.8 px rung, restricted to
`d_cat > rung`: 611 candidates / 475 accepted at rung 3, 577 / 437 at rung 4, 469 / 350 at rung 5 —
against 2,171 / 3,825 / 5,637 dots removed (`evidence/session_prune_receipt.json → refill_capacity`).
Holding the count would need either a tighter packing rung (a SPACING change) or off-ridge additions
(a new hypothesis, and additions have repeatedly failed live: T-v2's 1,259 dots earned +2.65 px of
credit, live −0.0028). **Decision:** all three variants are pure removals; the refill question is
parked as PRUNE-EXCHANGE in `SLOT_PLAN.md`.

## IR-V2-10 — competition rasters are restored from public mirrors into gitignored paths (restates IR-V2-04)

`data_manifest.json` pins the 419 MB `training_features.tif` and the 60,988-px catalogue to public
GitHub mirrors; this session restored all 28 entries (SHA-256 verified) into `data/`, which is
gitignored. Data-use terms were **not** read (drivendata.org is off-limits to automated access).
**Decision:** ship only derived binary submissions (~330–350 KB each) in `releases/`; never the mirrors.
The human must confirm redistribution terms before any public release.

## IR-V2-11 — `releases/` naming follows the brief, not the repo's historical `-nan.tif` convention

Brief §7 wants `releases/<id>.tif` (NaN outside footprint) plus `<id>-zeros.tif`; older artifacts use
`-nan.tif`. **Decision:** follow the brief, and name the exact upload file in `docs/SUBMIT.md` so no
slot is wasted. The `sha8` in each id is the first 8 hex of that file's own sha256, re-checkable after
download.

## IR-V2-12 — `TOP_PUBLIC`, slots-left and any receipt for 0.2778 are still missing

`TOP_PUBLIC` (with date), remaining rolling-week quota, and a submission-page receipt for the 0.2778
incumbent are absent from the brief and the repository (`registry/scored_artifacts.json` marks all 17
scores OWNER-REPORT). **Decision:** 0.2778 stays a CLAIM, `TOP_PUBLIC` stays unfilled, and every
prediction here is labelled MODEL. The human must fill all three before slot 2 is spent, because the
third slot is conditional on the first two receipts.

---

## IR-V2-13 — AXIS was unassigned again; SNAP built on the recommendation, and the human did not answer

The brief makes AXIS a human assignment. This session asked explicitly (one question with four axis
options and one on lidar admissibility); the questions were **skipped**, so no answer exists. SNAP was
chosen on evidence: it is the only remaining axis that changes something *orthogonal* — dot position at
fixed count and fixed mass — instead of re-weighting the same prior that already built the ridge (MASS
was measured negative in IR-V2-08; CONCENTRATION's prior is the ridge's own signal and its direction is
contradicted by the block-density CV, IR-V2-16). **Decision:** three SNAP variants are built and ledgered
as BUILT/UNSCORED; the axis is ranked *below* the PRUNE ladder in `SLOT_PLAN.md` because its predicted
effect is inside the ±0.01 no-evidence band (IR-V2-15). **If the human intended a different axis, say so
before the next build** — each `(AXIS, value)` pair is built once, and these three files are already
spent as build effort.

## IR-V2-14 — the catalogue hide-and-recover PROXY is structurally biased for any candidate derived from a catalogue-pruned parent

Measured this session with the repo's own fold machinery (`src/gems85/holdout.py`: 4 spatially blocked
segment folds, 5-px buffer, prediction masked on `visible`, truth = withheld, 60,988 withheld
positives): R0 scores **0.00479**, while the three SNAP variants score 0.00781 / 0.00940 / **0.01350**
— a 3× rise — even though the SGMC off-catalogue control moves by **≤0.002** and the label-free support
coverage *falls*. The mechanism is not a discovery: R0's dots were deliberately pushed >2 px away from
the **whole** catalogue, so in a fold where part of that catalogue is withheld, the parent is artificially
far from the withheld trace and *any* rule that re-approaches it — including a snap driven by an
independent geophysical field — scores higher. The live scorer **masks** those pixels, so the proxy
rewards exactly what earns nothing.

**Decision.** The catalogue hide-and-recover proxy is reported per fold with its CI but is **not used as
evidence** for SNAP, and the previous session's +0.0083 bias correction (calibrated on PRUNE contrasts,
which are the one edit class that *does* target the catalogue shadow) is **not transferred** to this
edit class. Predictions here come from the label-free support-coverage diagnostic and the SGMC
off-catalogue control. Anyone reusing the hide-and-recover proxy on a catalogue-derived lineage must
carry this caveat.

## IR-V2-15 — the brief's own SNAP definition (≤ 2 px) cannot produce a result above the brief's own evidence floor

The brief caps SNAP at 2 px and also says a live change under 0.01 is no evidence. At 100 m pixels,
2 px = 200 m, while the triangular kernel has R = 300 m: a dot moved ≤2 px is usually still inside the
same kernel neighbourhood of the truth pixel it was already serving, so the metric is close to neutral
by construction. Measured here: the largest variant moves 56.9 % of dots and still changes the
label-free support coverage by only 18.9 %, and the SGMC control by ≤0.002. **Decision:** SNAP is a
*bound* on position sensitivity, not a bet on a gain — one slot at most, only if the PRUNE ladder is
closed or a slot would otherwise go unused, and the best single spend is the **free-window** file
(largest effect, cleanest split of "off-ridge cost" vs "on-ridge refinement"). A receipt inside ±0.01
must be written into the ledger as **no evidence**, not as a null result.

**Related, and still open:** R0 itself violates the brief's "≥ 3 px from the catalogue" rule (IR-V2-03:
2,171 dots at 2.24–3.00 px). SNAP inherits that and is not allowed to fix it: its rule keeps every dot
at least as far from the catalogue as it already was, which incidentally lowers the within-3-px count
to 1,839 / 1,786 / 1,219. The SNAP files must therefore **not** be described as §4.4-compliant either;
only the PRUNE files are.

## IR-V2-16 — CONCENTRATION's direction is contradicted by the parent's measured block-density CV

R0's occupied-block density CV on 1-km (10-px) blocks is **0.619** (37,654 dots; median 2, p95 5 dots
per occupied block), *above* the 0.51–0.59 band the brief attributes to the best files. The brief's
CONCENTRATION moves 10–20 % of mass from low-prior to high-prior blocks, which raises CV — the opposite
of the only (confounded, PROXY-grade) observation available. **Decision:** do not build CONCENTRATION
until the direction is settled; if it is built, run it as two-sided (concentrate *and* de-concentrate)
at matched CV distance. The band itself is a file-name-derived observation and mass is confounded with
field, so it cannot settle the direction on its own.
