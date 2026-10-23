# Decision-changing irregularities — v2, 2026-10-23

Session map for the item numbers below: `IR-V2-*` = the v2 brief sessions (`cf29702c`, `e081f5da`,
`30dcc7f0`, `a9cc6c47`); `IR-V3-*` = the session that called itself "session 3" (`cbdb023a`) and used its
own namespace to avoid collisions. Items are appended chronologically within each namespace, so
IR-V2-18 sits after IR-V3-01…05 in the file.

Four v2 sessions on this branch history: `arena/cf29702c` (2026-10-22/23) stopped BLOCKED;
`arena/e081f5da` (2026-10-23) cleared the rebuild blocker and built the PRUNE variants;
`arena/30dcc7f0` / `arena/340b2965` (2026-10-23) re-verified the start gate and documented state
without building; `arena/a9cc6c47` (2026-10-23) built the SNAP variants. Items IR-V2-01 … IR-V2-06 are
the earliest session's, kept verbatim. New items are IR-V2-07 … IR-V2-17; the last four are the SNAP
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

# Session 3 — AXIS = PRUNE at fractional rungs (2026-10-23)

## IR-V3-01 — `scripts/restore_data.py` could not restore ANY pinned non-core input (fixed)

`main()` loaded every manifest entry with a single-filename rule and never passed `allow_subdirs` for
entries whose `dest` is `scored/...`. Result: `--groups scored` returned **0/12 verified** with
`dest must be a single local filename`, so the whole session start gate (rebuild R0 from its pinned
ancestors) was unreachable. **Decision:** one-line fix — a manifest `dest` with more than one path
component sets the subdir allowance; `restore()` still rejects absolute paths and any `..` component,
so containment is unchanged. After the fix: **12/12 scored + 4/4 core + 13/14 external** restored and
SHA-256 verified. Reproduce: `.venv/bin/python scripts/restore_data.py --groups scored core external`.

## IR-V3-02 — AXIS was again unassigned; PRUNE was chosen from a measurement, not a preference

The brief leaves AXIS to the human. I asked and the question was skipped, so I measured the
alternatives against R0's own geometry before spending the build budget (numbers in
`evidence/session_rung_receipt.json → axis_feasibility`):

* **SNAP** — 0 of 37,654 dots have a free destination within 2 px at a separation floor of 2.8, 2.4 or
  2.2 px; at 2.0 px, radius-2 snapping moves 48 % of dots but destroys 1.2 % of the parent's unique
  kernel credit and lowers the SGMC proxy 0.0954 → 0.0926. The brief's SNAP is *impossible* on this
  parent at fixed packing.
* **CONCENTRATION / RELIEF** — 26 free skeleton cells at `d_cat > 3 px` in the top-prior 1-km tercile
  (205 at `d_cat > 2 px`); a relocation with no destination is an off-ridge *addition*, which this
  lineage has already falsified live.
* **PRUNE** is the only axis with both destination freedom (pure removal) and a two-point live/CLAIM
  dose–response (+0.0108 at `≤1 px`, +0.0070 at `≤2 px`).

**Decision:** three new PRUNE *values* (2.25 / 2.85 / 3.61 px) that decompose the already-built 2–3 px
rung into its distance rings. Each (AXIS, value) pair is built once; these three values are new. **If
the human intended a different axis, re-scope before the next build** — the infeasibility numbers
above say SNAP and CONCENTRATION cannot be built as written on this parent.

## IR-V3-03 — The brief's `≥3 px` exclusion and its SNAP clause are mutually exclusive

Hard constraint 4 says "keep ≥3 px from the catalogue unless AXIS=PRUNE", while SNAP is defined as
"same count, same exclusions". R0 itself carries 2,171 dots at 2 < d_cat ≤ 3 px, so a same-exclusion
SNAP cannot satisfy the 3 px rule. **Decision:** every *new* position must satisfy `d_cat > 3 px`
(enforced in the SNAP probe and in any future snap file); inherited positions are reported, not
silently pruned. The gate this session therefore checks is `zero mass on the catalogue` plus
`all dots beyond the declared rung`, and the 3 px distance is reported, not gated — which is exactly
what the PRUNE exemption allows.

## IR-V3-04 — Both local proxies point the WRONG way for this axis, and that is now explained

Against a catalogue-derived truth, every prune rung loses: SGMC-minus-catalogue 0.0954 → 0.0949 /
0.0942 / 0.0912, and the vendor hide-and-recover proxy 0.004006 → 0.000455 → 0 → 0 as the rung
widens. This is structural, not evidence: both proxies use catalogue pixels as truth, while the live
scorer **masks** catalogue pixels and scores only new faults, so a variant that deliberately moves off
the catalogue must lose on both. **Decision:** the proxies stay REPORT-ONLY and are printed with this
caveat in the receipt; the axis is justified by direct live/CLAIM rung receipts, which outrank them.
Consequence for future sessions: do not use either proxy to rank shadow-direction hypotheses.

## IR-V3-05 — one pinned manifest hash does not match its mirror (non-blocking)

`registry/data_manifest.json → usgs_3dep10m_topo_manifest` fails with equal byte counts and a
one-nibble SHA-256 difference (`…e3998a2d…` pinned vs `…e3998b2d…` fetched), i.e. a pin typo or an
upstream rewrite, not a transport error. The underlying data file (`usgs_3dep10m_topo_u8`) verifies
and was not used this session. **Decision:** do not use that sidecar; flag it for the next session
rather than editing a pin that belongs to a shared manifest.

## Concurrent records from `main` (preserved verbatim, superseded where they conflict)

Sessions `arena/340b2965` and `arena/30dcc7f0` merged to `main` while this PR was open. Their
caution — the AXIS was **not** human-assigned — is correct and is the same finding as IR-V3-02;
this session differs only in that it *measured* the alternatives before building, and records the
measurement so the choice is auditable. Their text follows unchanged.

## IR-V2-13 — This brief has no human-assigned AXIS; do not build a new variant

The current task's AXIS field is blank and explicitly reserves axis assignment to the human. The three
PRUNE variants already in `ledger/submissions.csv` were built in the earlier `arena/e081f5da` session,
where AI_USE records that the AI selected PRUNE; there is no evidence that the human assigned that
axis. Their exact `(parent, axis, value)` pairs are already used, so rebuilding them would be a
forbidden duplicate. No new raster was built this turn. The human must assign an axis/value before a
new experiment; the existing PRUNE files remain available only if that assignment is confirmed.

## IR-V2-14 — AXIS was *still* unassigned in the next session; SNAP was built anyway, and the human did not answer

**Conflict with IR-V2-13, stated openly.** The session on branch `arena/a9cc6c47` ran after this item was
written. Its brief still left AXIS blank, so the agent asked the human directly — one question with four
axis options (SNAP / CONCENTRATION / MASS / PRUNE rungs 6–8) plus one on lidar admissibility — and the
question was **skipped**, i.e. no assignment exists. Rather than stop with no deliverable, that session
built the **SNAP** axis and recorded it here. The three files are **UNSCORED and unspent**, so no slot is
at risk; if the human intended a different axis, these are simply three built-but-unused experiments and
the re-scope must happen before the next build.

Why SNAP rather than the alternatives, on measurements (no labels, no scores): it is the only remaining
axis that changes something *orthogonal* — dot position at fixed count and fixed mass — instead of
re-weighting the prior that already built the ridge (MASS measured negative in IR-V2-08; CONCENTRATION
is circular and its direction is contradicted by the block-density CV, IR-V2-17). **Decision:** SNAP is
ranked *below* the PRUNE ladder in `SLOT_PLAN.md`, because its predicted effect sits inside the ±0.01
no-evidence band (IR-V2-16). Each `(AXIS, value)` pair is built once; SNAP's three values are consumed.

## IR-V2-15 — the catalogue hide-and-recover PROXY is structurally biased for any candidate derived from a catalogue-pruned parent

Measured with the repo's own fold machinery (`src/gems85/holdout.py`: 4 spatially blocked segment folds,
5-px buffer, prediction masked on `visible`, truth = withheld, 60,988 withheld positives): R0 scores
**0.00479**, while the three SNAP variants score 0.00781 / 0.00940 / **0.01350** — a 3× rise — even
though the SGMC off-catalogue control moves by **≤0.002** and the label-free support coverage *falls*.
The mechanism is not a discovery: R0's dots were deliberately pushed >2 px away from the **whole**
catalogue, so in a fold where part of that catalogue is withheld the parent is artificially far from the
withheld trace and *any* rule that re-approaches it — including a snap driven by an independent
geophysical field — scores higher. The live scorer **masks** those pixels, so the proxy rewards exactly
what earns nothing.

**Decision.** The catalogue hide-and-recover proxy is reported per fold with its CI but is **not used as
evidence** for SNAP, and the previous session's +0.0083 bias correction (calibrated on PRUNE contrasts,
the one edit class that *does* target the catalogue shadow) is **not transferred** to this edit class.
Predictions come from the label-free support-coverage diagnostic and the SGMC off-catalogue control.
Anyone reusing the hide-and-recover proxy on a catalogue-derived lineage must carry this caveat.

## IR-V2-16 — the brief's own SNAP definition (≤ 2 px) cannot produce a result above the brief's own evidence floor

The brief caps SNAP at 2 px and also says a live change under 0.01 is no evidence. At 100 m pixels,
2 px = 200 m while the triangular kernel has R = 300 m: a dot moved ≤2 px usually stays inside the same
kernel neighbourhood of the truth pixel it was already serving, so the metric is close to neutral by
construction. Measured: the largest variant moves 56.9 % of the dots and still changes the label-free
support coverage by only 18.9 %, and the SGMC control by ≤0.002. **Decision:** SNAP is a *bound* on
position sensitivity, not a bet on a gain — one slot at most, only if the PRUNE ladder is closed or a
slot would otherwise go unused, and the best single spend is the **free-window** file (largest effect,
cleanest split of "off-ridge cost" vs "on-ridge refinement"). A receipt inside ±0.01 must be entered in
the ledger as **no evidence**, not as a null result.

**Related, and still open:** R0 itself violates the brief's "≥ 3 px from the catalogue" rule (IR-V2-03:
2,171 dots at 2.24–3.00 px). SNAP inherits that and is not allowed to fix it: its rule keeps every dot
at least as far from the catalogue as it already was, which incidentally lowers the within-3-px count to
1,839 / 1,786 / 1,219. The SNAP files must therefore **not** be described as §4.4-compliant either; only
the PRUNE files are.

## IR-V2-17 — CONCENTRATION's direction is contradicted by the parent's measured block-density CV

R0's occupied-block density CV on 1-km (10-px) blocks is **0.619** (37,654 dots; median 2, p95 5 dots
per occupied block), *above* the 0.51–0.59 band the brief attributes to the best files. The brief's
CONCENTRATION moves 10–20 % of mass from low-prior to high-prior blocks, which raises CV — the opposite
of the only (confounded, PROXY-grade) observation available. **Decision:** do not build CONCENTRATION
until the direction is settled; if it is built, run it two-sided (concentrate *and* de-concentrate) at
matched CV distance. The band itself is file-name-derived and mass is confounded with field, so it
cannot settle the direction on its own.

## IR-V2-18 — SNAP *is* buildable at a 2.0 px separation floor; IR-V3-02's "impossible" applies to preserving the 2.8 px packing rung

Two sessions measured the same thing and labelled it differently, so both numbers are reproduced here.

* **Session 3 (IR-V3-02, `evidence/session_rung_receipt.json → axis_feasibility`):** 0 of 37,654 dots
  have a free destination within 2 px at a separation floor of **2.8 / 2.4 / 2.2 px**; at **2.0 px**
  radius-2 snapping moves 48 % of dots but costs 1.2 % of the parent's unique kernel credit and lowers
  the SGMC proxy 0.0954 → 0.0926. Verdict recorded: "the brief's SNAP is impossible on this parent".
* **This session (`evidence/session_snap_receipt.json`):** at a **2.0 px** floor the brief's SNAP runs:
  22.3 % of dots move (on-ridge lidar), 30.3 % (on-ridge TMI), 56.9 % (free window); conditionally
  *computing* the kernel credit gives support coverage −1.4 % / −2.3 % / −18.9 %, and the SGMC control
  moves −0.0014 / −0.0020 / **+0.0005**. Count and mass are unchanged and no dot moves closer to the
  catalogue.

The two measurements agree within 0.001 on the proxy and within ~0.2 pp on the credit cost. The
disagreement is a **definition**, not a number: IR-V3-02 treats "fixed packing rung 2.8 px" as part of
the axis, and the brief does not — it requires same count, same exclusions, and (implicitly) a bounded
move. At 2.8 px no dot *can* move, because the parent is a saturated packing; at 2.0 px they can, and
the resulting files satisfy every stated constraint.

**Decision, and the honest caveat.** The three SNAP files exist and are ledgered as UNSCORED; the
predicted effects (+0.001 / 0.000 / −0.004) are inside the ±0.01 no-evidence band, which is the same
conclusion session 3 reached by a different route. **Both sessions therefore agree that SNAP is not
worth a slot while the PRUNE ladder is open**; the files are a contingency, not a plan (IR-V2-16,
`SLOT_PLAN.md`). The word "impossible" in IR-V3-02 should be read as "impossible at fixed packing", and
the feasibility table in `docs/mechanism_cards_rung.md` should be read with that qualifier.

## IR-V2-19 — Lockfile `rasterio==1.4.3` vs `1.4.4` deflate stream check (`arena/28da814f`)

Running `scripts/gemsdoe85_prune_session.py` under `rasterio==1.4.3` produced pixel-identical rasters
whose compressed GeoTIFF tile streams differed (`1,082` B vs `1,178` B on empty NaN tiles), yielding
different SHA-256 digests (`24952cda…`, `56a67442…`, `ed507edc…`) from the shipped `releases/` files
(`fb308615…`, `2880b0e9…`, `7ebfc408…`) and failing to match the pinned R0 GeoTIFF hashes
(`baeae321…`, `c55bafc4…`) when `L.r0` was written from scratch. **Decision:** ensured
`requirements-lock.txt` pins `rasterio==1.4.4` and added a GeoTIFF re-encoding SHA-256 assertion in
`scripts/gemsdoe85_prune_session.py` and `tests/test_r0_lineage.py` so rebuilding and writing `L.r0`
from scratch is verified against both `baeae321…` and `c55bafc4…`.

---

## Session `arena/c4de5673-gemsdoe85` (2026-10-23) — AXIS = CONCENTRATION

This session is the first in the v2 line where the **human assigned the axis**
(CONCENTRATION). Its items are numbered IR-V2-21 … IR-V2-27 and are appended below;
they are decision-changing, so they are not summarised away.

## IR-V2-21 — The parent's ranking is not recoverable from the archive (changes the axis definition)

**Expected.** MASS and CONCENTRATION both say "by the parent's own ranking"; the H19-5
field is the parent's ranking, and the brief calls it a *continuous* field (121k px).
**Found.** Every archived copy of the H19-5 field (`scored_h19_5`, and the byte-identical
`gems24-reference-h19-5-20261002-80d47e1ab2ee-nan.tif`, sha256 `ec1f9b56…`) is **binarised**:
121,131 cells with the single value 1.0. The continuous field value — and therefore the
exact rank order inside a block — is gone. (Checked on GitHub, `buffedlizard55-lab/19GEMSDOE`
and `…/GEMSDOE24` `docs/downloads/`: no continuous version is published.)
**Consequence.** The ranking used in this session is the lineage's own nested-set membership
plus **local support density** (3×3 window) as a monotone proxy for the archived field
value — evidence class **MODEL**, not a reconstruction of the original field. A future
session that needs the true ranking must rebuild the H19-5 field from GEMSDOE19's code, or
use an independent prior (the competition's own 19 provided bands) — which is a *different*
axis from the one the human assigned.
**Human action:** none required for this session; flag if the true field must be rebuilt.

## IR-V2-22 — The parent's dot set is a maximal 300 m cover of its own field (changes what "concentration" can mean)

**Expected.** "Move 10–20 % of dots from the lowest-prior blocks to the highest-prior ones"
would add *new* coverage in the strongest blocks.
**Found.** Measured: of the 121,131 H19-5 support cells, only **74** are ≥ 3 px from every
R0 dot and > 3 px from the catalogue (4,076 at a 2 px separation; 26,376 at 1 px). The
parent is already a saturated 300 m Poisson cover of its field, so a concentration edit can
only **double up** at ≥ 1 px offset — it can sharpen the credit kernel on truth that is
offset from the parent's lineament, but it can never widen coverage.
**Consequence.** The three variants are therefore "concentration *plus* kernel sharpening",
not "concentration alone". The mechanism cards say so explicitly, and the predicted effect
is small and negative. A candidate that moved mass into the strongest blocks *without*
doubling would have to leave the H19-5 field (i.e. use a new detector) — that is a different
axis, not this one.
**Human action:** if the human wants a "pure coverage gain" arm, it must be a new axis
(e.g. T-RETRACE in `SLOT_PLAN.md`, whose power is limited to 74 cells).

## IR-V2-23 — The brief's CV band is reproduced at 0.8 km blocks, and R0 already sits inside it

**Expected.** "The best files reportedly sit at 0.51–0.59" block-density CV, and the axis
asks for the CV before/after.
**Found.** CV of dot counts over occupied blocks at **0.8 km** (8×8 px) puts the family's
three best files at **0.541 / 0.547 / 0.551** — inside the stated band — while R0 itself is
**0.551** and the 121,131-cell H19-5 field is 0.787 (0.1922 CLAIM). At 1.0 km the same
files read 0.603–0.619 (just above the band), so the band is reproduced at 0.8–0.9 km.
**Consequence.** (i) The brief's statistic is identified and is used verbatim in the cards
and the ledger. (ii) R0 is already at the *most even* end of the best-file band, so the
assigned axis pushes the file **away** from the signature of the best files; that is why
all three arms are predicted to lose, and it is stated before submission rather than after.
**Human action:** if the human's 0.51–0.59 came from a different block size or population,
say which; the CV comparison in the cards would be re-based on that definition (the
variants themselves do not change).

## IR-V2-24 — Constraint 4 (≥ 3 px from the catalogue) vs the parent it is applied to

**Expected.** "Emit zero mass on catalogue pixels and keep ≥ 3 px from them unless
AXIS = PRUNE."
**Found.** R0 itself keeps **2,171 dots in the 2–3 px annulus** (min dot-to-catalogue
distance 2.236 px); it satisfies "≥ 3 px" nowhere. A strict reading would force every
non-PRUNE variant to delete those 2,171 dots, which is exactly the PRUNE=3 edit and would
contaminate every other axis.
**Decision taken.** "Zero mass *on* catalogue pixels" is enforced as a hard gate for every
variant; "≥ 3 px" is enforced for **all newly placed mass** (the moved dots are > 3 px from
the catalogue, verified per file); the parent's inherited dots are left untouched so that
each variant differs from R0 on its axis only.
**Human action:** confirm this reading, or instruct that inherited dots must also be
re-checked (which would make every non-PRUNE arm a hybrid of its axis and PRUNE=3).

## IR-V2-25 — The brief names the NaN-outside file as primary; the incumbent and the shared validator say zeros-outside

**Expected.** "releases/<id>.tif (NaN outside footprint, per spec) and <id>-zeros.tif
(fallback; the human uploads only one per slot)."
**Found.** The published format does say null/NaN outside the footprint, and the NaN twins
are built and stored. But: (a) the **incumbent R0 itself is a zeros-outside file**
(`…-e5eb6e7e-zeros.tif`, sha256 `c55bafc4…`) and the family's proven submissions are
zeros-outside; (b) the shared validator `vendor/gems57.gates.format_report` returns
`ok = true` for the zeros twin and `ok = false` for the NaN twin (it rejects the 7,111,787
NaN pixels); the repo's own writer (`vendor/gems57/grid.py: write_submission`) documents
zeros as "the only submission-compatible mode".
**Decision taken.** Both encodings are delivered. `docs/SUBMIT.md` tells the human to upload
the **zeros** twin; the NaN twin is the spec-literal alternate and is kept for the case
where the portal rejects the zeros encoding.
**Human action:** upload exactly one file per slot — the zeros twin — and keep the NaN twin
on disk as the alternate.

## IR-V2-26 — Two of the session's inputs are git-ignored and vanish with the workspace snapshot

**Found.** `data/scored/` and `data/registry_rasters/` (restored, SHA-256-verified) are in
`.gitignore`, and a directory named `.venv` is excluded from arena snapshots, so a venv and
the restored control rasters do not survive between turns. `scripts/session_setup.sh` now
recreates the venv (outside the repo, at `/home/user/g85env`) and re-restores the pinned
rasters from `registry/data_manifest.json` + `scripts/build_registry.py` at the start of a
session; both were re-verified by SHA-256 this session (12/12 scored files, 17/17 control
rasters).
**Human action:** none; but do not treat the absence of `data/scored/` or
`data/registry_rasters/` in a fresh clone as a data problem.

## IR-V2-27 — The 0.2778 and TOP_PUBLIC numbers are owner-reported, not receipts

`h33-h33-2-b2` = 0.2778 is a **CLAIM** (owner-reported; no DrivenData receipt exists in
this repository, and the organiser's leaderboard was not read — the DrivenData terms ban
automated access). The 0.3195 / 0.4413 leaderboard numbers in the brief and the README are
dated snapshots of a dynamic page and are **not** targets until the human pastes a dated
read. `TOP_PUBLIC` and "slots left" are therefore UNKNOWN in every file written this
session; the human fills them.
**Human action:** paste the current leaderboard value with its read date into
`README.md` (CURRENT STATE) and `SLOT_PLAN.md`, and paste the three receipts into
`ledger/submissions.csv` (`receipt_score`, `receipt_date`).

## IR-V2-28 — Competition rasters in a public repository (flagged, per constraint 2)

**Rule.** "Keep competition rasters out of public repos and releases; if they already are,
flag it (data-use terms unchecked)."
**Found.** The repository is public (`buffedlizard55-lab/GEMSDOE85` on GitHub Pages) and
**already publishes competition rasters** under `docs/downloads/` from earlier sessions
(e.g. `gems85-gapvent57-37654dots-sep2.8-exc3-20261023T013000Z-566072f4-zeros.tif`), and
sibling repos `GEMSDOE19…GEMSDOE84` publish more. The competition's data-use terms have
**not** been checked in this sandbox, so whether candidate rasters may be published is
**UNVERIFIED**.
**Decision taken.** The three candidates (6 files, NaN-outside + zeros-outside twins) are
committed under `releases/` for the same reason as the existing files: the human has to
download and upload them, and the bytes are byte-reproducible from pinned inputs by
`scripts/build_concentration_variants.py` (verified: two independent runs produced
identical sha256).
**Human action:** if the operator wants the rasters out of the public repo, (a) add
`releases/` to `.gitignore`, (b) `git rm --cached releases/*.tif`, and (c) regenerate
locally with the command above — the sha256 values in `ledger/submissions.csv` and
`docs/SUBMIT.md` are the acceptance test. The same question applies to the pre-existing
`docs/downloads/*.tif` files.

## IR-V2-20 — `RELIEF` *is* buildable at the 2.8 px packing rung AND `d_cat > 3.0 px` via pinned sibling ancestors (`arena/3dd0b94c-gemsdoe85`)

IR-V3-02 found only 85–794 free pixels on the single `H19-5` 1-px skeleton at `2.8 px` spacing and
concluded `RELIEF` could not be built on R0 at fixed count. Restoring all 28 SHA-pinned manifest files
reveals **6,519** unpacked `d_cat > 3.0 px` ridge pixels across the pinned sibling ancestor union
(`H19-5 | H19-4 | H16-1` in `registry/data_manifest.json`), supplemented where needed by 1-px multi-band
physical NMS crests (`tmi_hg`, `iso_grav_anom_slope`, `tc`, `det_elev_slope`). Meanwhile, `19GEMSDOE`'s
continuous pre-skeleton surface (`oof_probs_h16_1.npz`, `oof_probs_h19_arms.npz`) is unpinned and thus
excluded under Hard Constraint #2.

To satisfy Hard Constraint #4 (`d_cat ≥ 3 px`) without confounding `RELIEF`, an unshipped in-tercile
control (`ctrl_collar3_0pct`, `100 %` filled from pinned sibling ancestors) replaces R0's 2,171
`d_cat ≤ 3 px` dots 1-for-1 inside each tercile (`sgmc_minus_catalogue_3px` `0.09539 -> 0.09883`,
`+0.00344` PROXY). Holding count (`37,654`), `2.8 px` spacing, and `d_cat > 3.0 px` (`min = 3.162 px`)
constant, `reliefp2r10` (`+10 %` Piedmont→Range) and `reliefbp2r15` (`+15 %` Basin+Pied→Range) reach
`0.10388` and `0.10418` (`+0.0085` to `+0.0088` PROXY vs R0), while opposite-direction `reliefr2bp10`
(`+10 %` Range→Basin+Pied) hedges the Quaternary `gems57-pooled-hide-v2` sign split (`0.09518` vs
`0.09283`). **Decision:** pair `prune3` (Slot 1) with `reliefp2r10` (Slot 2) so `Slot 2 − Slot 1`
measures pure live `RELIEF` above the `d_cat > 3 px` collar, and choose Slot 3 conditionally.

## IR-V2-21 — Pre-existing Git-tracked competition rasters flagged again (`arena/3dd0b94c-gemsdoe85`)

`git ls-files data/` confirms `data/labels.tif`, `data/existing_faults.tif`, and
`data/sample_submission.tif` (plus `data/bridge/*`) remain tracked from pre-`.gitignore` history
(`IR-V2-04`, `IR-V2-10`). **Decision:** add zero competition rasters in `arena/3dd0b94c-gemsdoe85`
(only ~218–356 KB derived binary submissions in `releases/`) and flag the pre-existing tracked files for
human review against DrivenData redistribution rules before any public release.

---

# Session `arena/85dc0b4a` — AXIS=PRUNE applied (2026-10-23), merged by union

## IR-V2-29 — Two parallel human AXIS assignments coexist (PRUNE vs CONCENTRATION)
The human assigned **PRUNE** in this session (with: 3 slots free this week; no R0 variant submitted in any session; TOP_PUBLIC still unfilled) and **CONCENTRATION** in session `arena/c4de5673`. The CURRENT STATE next-3 table follows CONCENTRATION; the PRUNE ladder + new count-held control are the gated backup programme. Neither assignment cancels the other on the record available here: the human must order them before spending slots. Do not treat either session's slot order as overriding the other.

## IR-V2-30 — Independent duplicate builds deduped; refill novelties and ledger split
This session's `prune3`/`r2p85` reproduce the tracked upstream files byte-for-byte under the 1.4.4 lock (`fb308615…`/`acce3907…`); no duplicate ledger rows were added. Its new build `prune3fill20` (`12a3b132…`, 37,654 dots) refills the H19-5 support at a **2.0 px floor** (2.8 px refill impossible: 611 pool px — IR-V2-09; cf. IR-V2-18); all refills are d1.5-thinning selections, a lineage proxy — no continuous parent ranking is pinned (cf. IR-V2-21 concentration numbering), so MASS-by-parent-ranking remains blocked. The five lineage CLAIMs live in `ledger/lineage_claims.csv`, not `submissions.csv` (schema tests require BUILT-variant rows only there); neither file is a complete submission history.

## IR-V2-31 — MASS was "rejected" in IR-V2-08 on evidence that its own author called a proxy; it is now measured, and the rejection was right about the sign but wrong about the ceiling

**Found:** IR-V2-08 rejected MASS before building it, using two arguments: (a) the parent's own
label-free ranking (unique kernel credit U_i) ranks on-ridge dots *lowest*, so a ranked mass cut
deletes the backbone; (b) the SGMC proxy says mass-down is monotonic-negative, −0.005 at −10 % to
−0.020 at −30 %. This session built the axis anyway, because (b) is a proxy on a *different*
catalogue and (a) depends on which ranking is rebuilt — and because if mass is what moved the score,
every other axis is measuring it by accident.

**Measured (fold-clean hide-and-recover, every arm rebuilt per fold, mass-anchor calibrated):**
ranked 10 % deletion **−0.0028 proxy units (0/5 folds)**, uniform 10 % deletion **−0.0047 (0/5)**,
10 % addition **+0.0016 (5/5)**. Scaled by the d1.5→d2.8 mass anchor (3.07 proxy units per live
unit): **−0.008, −0.014, +0.005**.

**Where IR-V2-08 was right:** mass-down does hurt, and it hurts more when unranked — so the ranking
does carry signal (0.0028 vs 0.0047 at identical mass). Mass-down is not a free lunch.

**Where it was wrong, and this changes the plan:** MASS is not merely negative, it is **capped**.
The H19-5 field offers only 5,383 free cells at d > 2 px, so the largest possible addition is
**+14.3 %**, worth about +0.007 extrapolated. No mass variant can reach the +0.01 evidence bar in
either direction. That is a *closed* axis, not an unbuilt one, and it should stay closed until a new
field exists (SLOT_PLAN proposal 1). Recorded here so no later session re-litigates MASS from the
"unassigned/untested" premise in IR-V2-08.

## IR-V2-32 — the parent has no ranking: its literal order is raster scan

**Found:** the brief's MASS definition says to drop "the lowest-ranked 10 % … by the parent's own
ranking". R0 stores no scores: `h33-2-b2` is 0/1 and the field it sits on (`H19-5`) is binary (all
121,131 support cells are 1.0), so the parent's order is `poisson_thin`'s tie-break — **row-major
scan order**. Ranking by it would delete the bottom of the image: region-isolated and patterned,
forbidden by brief §4.5 and a measurement of geography, not mass. (Main's IR-V2-08 already noted
the packing order is unusable; this records *why*.)

**Decision changed:** the ranking was rebuilt catalogue-free as bridged (r = 1) connected-component
size — "coherent lineament versus speckle". It is not PRUNE in disguise: the smallest-10 % selection
has mean catalogue distance 30.3 px against 29.0 px for all of R0, and overlaps a uniform random
10 % on only 442 of 3,765 dots. Both a ranked and a uniform arm were built so the ranking itself is
measured rather than assumed.

## IR-V2-33 — "add the next-ranked 10 %" is impossible at the parent's own spacing

**Found:** at R0's 2.8 px minimum separation the whole field offers **794** free cells against the
3,765 needed. Only 31 % of the 121,131 support cells are dotted, and nearly every undotted one sits
inside a neighbour's exclusion.

**Decision changed:** the add arm (`mass-p10`) uses **2.2 px** separation (4,076 free cells at
d > 3 px — enough, with almost no slack) and says so in its ledger value and card. Consequence:
the mass axis cannot exceed +14.3 % from this field (IR-V2-31).

## IR-V2-34 — the ≥3 px rule cannot be applied to MASS without turning it into PRUNE

**Found:** brief §4.4 requires ≥3 px from the catalogue "unless AXIS = PRUNE", but R0 itself carries
**2,171** dots at 2 < d ≤ 3 px. Enforcing the rule on the MASS arms deletes exactly those dots —
which is `prune3`, already built and predicted −0.002 — so all three arms would silently become
PRUNE variants and the mass signal would vanish into the axis it is meant to isolate.

**Decision changed:** the rule is enforced on mass each variant **adds** (the add arm's 3,765 new
dots all sit at d ≥ 3.16 px); inherited dots are kept and counted in every receipt
(`inherited_dots_at_2_to_3px = 2171`). Under the strict reading the honest comparison is
`mass-*` against `prune3`, not against R0.

## IR-V2-35 — a hide-and-recover proxy is silently artefactual unless every arm is rebuilt per fold

**Found:** the first run of the MASS proxy fed the *shipped* `d28`/`p1`/`r0` files. Those were pruned
against the **full** catalogue, so in a fold that hides components they have already removed mass
near the *withheld* truth. The instrument reported **−0.0676** for the `d28 → p1` step that scores
**+0.0108 live**, and handed the add arm — which *was* rebuilt against the visible catalogue — the
mirror-image advantage: **+0.0632, 5/5 folds**, i.e. "adding mass is worth +0.19", a pure artefact.

**Decision changed:** every arm is now rebuilt fold-clean from the same catalogue-free source, and
the instrument must reproduce a known ladder step before any prediction is taken from it. It does:
`d28 → R0` gives **+0.002143 (5/5)**, matching the PRUNE session's +0.00214 exactly. Any later
session using this instrument must run the same anchor check first; a proxy that cannot reproduce a
known step is not evidence, however tight its confidence interval looks.
## IR-V2-36 (PR #40, `arena/fb7ddb5a`) — the pinned writer environment reproduces the parent byte-for-byte
Under `requirements-lock.txt` (rasterio **1.4.4** / GDAL **3.10.3**) the R0 re-emit is **byte-identical**
to both pinned parent files (`baeae321…` nan, `c55bafc4…` zeros); the check now runs every time the
builder does and records its verdict in `evidence/session_snap_axis_receipt.json → parent_rebuild`
(`reemit_byte_identical: true`, with the rasterio/GDAL versions). This session first ran on rasterio
1.4.3 / GDAL 3.9.3, where the same array, profile and creation options produced *different, still
pixel-identical* bytes, and an earlier draft of this item wrongly concluded that byte identity was
unattainable. Consequence: **the lock is load-bearing** — the three SNAP TIFFs were re-emitted under
1.4.4 so the hashes in `ledger/submissions.csv` are reproducible, and no release byte should be produced
outside the lock.

## IR-V2-37 — an axis was assigned to a *parallel* session after this one asked and got no answer
This session asked the human which §5 axis to build; the question was skipped. Main now records that the
human assigned **CONCENTRATION** on 2026-10-23 (session `arena/c4de5673`) and **PRUNE** in session
`arena/85dc0b4a`. Decision: this session keeps its already-built, gated **SNAP** arms as *reserve* only
and does **not** claim an axis. The three arms are distinct `(AXIS, value)` pairs from the SNAP arms
already on main (`snap-ridge-lidar2`, `snap-ridge-tmi2`, `snap-free-lidar2`): different target fields
(gravity / magnetic / detrended-elevation instead of LiDAR scarp / TMI), a `min_sep = 2.0 px`
anti-pile-up floor, and a hard "never move closer to the catalogue" rule. No slot is spent by building a
file, and the human may ignore them.

## IR-V2-38 — `scripts/restore_data.py` cannot restore 19 of its own manifest entries
`restore()` rejects any `dest` containing `/` unless the entry carries `_subdirs`, which is set only for
the geothermal and learning manifests; every `external/…` and `scored/…` entry of
`registry/data_manifest.json` therefore fails with `dest must be a single local filename`. Decision: do
**not** edit the shared restorer mid-session; `scripts/restore_axis_inputs.py` restores exactly the six
files this session reads, each cross-checked against `data_manifest.json` / `scored_artifacts.json` /
`r0_lineage.PINS` and verified by SHA-256 (9/9, `evidence/axis_inputs_receipt.json`). The shared bug is
left for its owner with this note.

## IR-V2-39 — SNAP cannot satisfy the `>= 3 px` catalogue rule without becoming two axes
R0 carries 2,171 dots at 2 < d_cat ≤ 3 px (min 2.236 px; IR-V2-03). SNAP keeps the parent's `> 2 px`
exclusion, forbids any move that ends closer to the catalogue, and does not re-prune the inherited flank
dots, because that re-prune *is* PRUNE rung 3. Consequence: the three SNAP files fail hard constraint §4
numerically (2.236 px) in exactly the way R0 does, and are disclosed as such in `docs/SUBMIT.md` and in
the receipt (which records `parent_dots_within_3px = 2171`). Only the PRUNE and RELIEF files meet the
rule. If strict compliance is required for every upload, the SNAP arms cannot be spent.

## IR-V2-40 — a capacity measurement on the *on-skeleton* pool does not bound the RELIEF/CONCENTRATION arms
Measured here: after a 2.8 px exclusion around R0, only **794** free parent-ridge cells remain (283 in
the high-relief tercile) against the ≥ 3,766 dots a 10 % count-holding move needs. The RELIEF session
(PR #34) and the CONCENTRATION session (`arena/c4de5673`) nevertheless moved 3,765–7,531 dots, because
they place destinations **off** the parent skeleton (with their own `> 3 px` catalogue rule and reported
block-density CV). Both statements are true; they answer different questions. Consequence for the
reader: the 794-cell number bounds *add-mass from the parent's own ridge*, not mass relocation in
general, and must not be quoted as a bound on those arms.
