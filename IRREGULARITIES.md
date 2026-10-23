# Decision-changing irregularities — v2 session, 2026-10-23

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
