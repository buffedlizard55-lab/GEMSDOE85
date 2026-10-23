# Decision-changing irregularities — v2, 2026-10-23

Two v2 sessions on this branch history: `arena/cf29702c` (2026-10-22/23) stopped BLOCKED; this one
(`arena/e081f5da`, 2026-10-23) cleared the rebuild blocker and built the PRUNE variants. Items
IR-V2-01 … IR-V2-06 are the earlier session's, kept verbatim; the status line under each says what
this session did about it. New items are IR-V2-07 … IR-V2-12. Only items that change a decision.

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

## IR-V2-13 — the parent's *file* SHA-256 cannot be reproduced by re-emitting it
R0 is rebuilt from four pinned inputs and every intermediate is compared **pixel-for-pixel** with its
pinned raster (skeleton 121,131 → d2.8 44,090 → solo 40,199 → R0 37,654: all identical). A byte-identical
*re-emit* was attempted with `deflate` z1–z9 × predictor none/2/3 and matches nothing: GTiff bytes depend
on the writer's libdeflate/GDAL build, not on the array. Decision: proceed, treating the decoded array
as the identity of the parent and recording both pinned file hashes
(`baeae321…` nan / `c55bafc4…` zeros) in `evidence/session_snap_receipt.json → parent_rebuild`. Nothing
in this session claims a byte-identical regeneration of the parent.

## IR-V2-14 — no axis was assigned, so the agent selected one and recorded the evidence
The human was asked which §5 axis to build and the question was skipped. Decision: **SNAP**, chosen on
measurements taken before any file was built (all recorded in the receipt's `diagnostics`):
SNAP is the only §5 axis that changes neither mass nor geometry source, and the alternatives are
blocked — add-mass arms have **794** free parent-ridge cells against the ≥ 3,766 dots a 10 % shift
needs, and MASS-down lowers the fault proxy monotonically. The human can override this at any time; no
slot is spent by building a file. IR-V2-02 (no assigned axis) is therefore *superseded for this session
only*, not closed.

## IR-V2-15 — `scripts/restore_data.py` cannot restore 19 of its own manifest entries
`restore()` rejects any `dest` containing `/` unless the entry carries `_subdirs`, which is set only for
the geothermal and learning manifests; every `external/…` and `scored/…` entry of
`registry/data_manifest.json` therefore fails with `dest must be a single local filename`. Decision:
do **not** edit the shared restorer mid-session; `scripts/restore_axis_inputs.py` restores exactly the
six files this session reads, each cross-checked against `data_manifest.json` / `scored_artifacts.json`
/ `r0_lineage.PINS` and verified by SHA-256 (9/9, `evidence/axis_inputs_receipt.json`). The shared bug
is left for its owner with this note.

## IR-V2-16 — SNAP cannot satisfy the `>= 3 px` catalogue rule without becoming two axes
R0 carries 2,171 dots at 2 < d_cat ≤ 3 px (min 2.236 px), as already logged in IR-V2-03. SNAP keeps the
parent's `> 2 px` exclusion, forbids any move that ends closer to the catalogue, and does not re-prune
the inherited flank dots, because that re-prune *is* PRUNE rung 3. Consequence: the three SNAP files
fail hard constraint §4 numerically (2.236 px) in exactly the way R0 does, and are disclosed as such in
`docs/SUBMIT.md` and in the receipt. Only the PRUNE files meet the rule. If the human requires strict
compliance for every non-PRUNE upload, SNAP cannot be uploaded until a PRUNE base becomes the parent.
