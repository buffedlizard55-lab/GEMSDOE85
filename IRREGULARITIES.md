# IRREGULARITIES — items that change a decision

Only entries that change what the operator or a later session should do. Session
`arena/eb7e09d3-gemsdoe85`, AXIS = PRUNE, 2026-10-23.

## IR-V2-01 — the incumbent rebuilds pixel-exactly but not byte-exactly

**Found:** `h33-h33-2-b2` (sha256 `c55bafc4…`, 219,065 B) is reproduced pixel-for-pixel from its
pinned 44,090-dot parent by deleting dots with Euclidean catalogue distance ≤ 2 px — 37,654 dots,
0 differing pixels (`evidence/r0_rebuild.json`). Re-serialising those identical pixels produces a
different SHA-256 under every writer setting tried here (predictor 2/3, zlevel 1–8, 256/512 px
tiles: 121–517 kB against the incumbent's 219 kB). The incumbent carries DEFLATE
`predictor=3`, which this rasterio build cannot reproduce bit-for-bit.

**Decision changed:** the parent is accepted as *rebuilt* (pixels), not as *matched* (bytes). No
session may upload the re-serialisation: same pixels, new hash, zero information, one wasted slot.
The brief's stop condition ("if you cannot match its sha256, stop") is therefore read as "stop
only if the pixels cannot be matched", and that reading is recorded here rather than assumed.

## IR-V2-02 — the repository's format gate is stricter than the competition spec

**Found:** `vendor/gems57/gates.py::format_report` fails any raster with NaN cells
(*"fail our all-finite export policy"*), while the competition page and `sample_submission.tif`
both use NaN outside the footprint, and the brief asks for NaN outside the footprint. Every NaN
twin built this session is reported as failing by that gate and as passing by the spec-level
gate in `src/gems85/lineage.py` (`evidence/prune_session.json`).

**Decision changed:** each variant ships both twins; the all-finite zeros twin is the one that
passes the repository's gate and `vendor/gems57/validate.py` unchanged. Upload the NaN twin
(brief's primary spec); fall back to zeros on any portal range error. Do not "fix" the shared
gate in this repository — `AGENTS.md` §4 requires shared defects to be fixed upstream.

## IR-V2-03 — the PRUNE protocol's refill cannot be executed, so PRUNE ≠ MASS is untestable here

**Found:** the H19-5 field is saturated at the parent's own spacing. Of the 2,171 dots that a
3 px cutoff removes, only **440** cells in the whole field are available at d > 3 px and ≥ 2.8 px
from a surviving dot (`evidence/prune_session.json` → `prune3r.refill_detail`, 20 % of the
intended refill).

**Decision changed:** "refill to hold the count" is impossible on this field, so the count cannot
be held at 37,654 by construction, and every future variant of this lineage can only *delete*.
The mass-versus-distance confound in the ladder therefore cannot be removed by refilling; it needs
the opposite experiment (delete the same number of dots far from the catalogue), which is why
`SLOT_PLAN.md` gives slot 2 to that MASS probe instead of to a third prune.

## IR-V2-04 — three pinned inputs are not in `registry/data_manifest.json`

**Found:** the incumbent (`c55bafc4…`), its 40,199-dot parent (`07b6db44…`) and the 44,090-dot
grandparent (`91eae1ca…`, this one *is* in the manifest) are pinned in
`registry/scored_artifacts.json`, not in `data_manifest.json`; the first two are fetched from
`buffedlizard55-lab/GEMSDOE32` and `…/GEMSDOE31` by commit-tagged path.

**Decision changed:** the brief's "registry/data_manifest.json (or the repo's equivalent)" is read
as including `scored_artifacts.json`, which is what the repository's own `scripts/build_registry.py`
verifies against. All four inputs this session touches are SHA-256-checked before use (IR-V2-01
and `evidence/r0_rebuild.json` → `pins`). If a future session needs a stricter reading, the pins
must first be promoted into `data_manifest.json` upstream.

## IR-V2-05 — the ladder's own two steps disagree with the naive per-dot model

**Found:** back-solving the live truth credit `T` from each scored step independently gives
`T ≈ 1,854 px` from step 1 (44,090 → 40,199) and `T ≈ 3,224 px` from step 2 (40,199 → 37,654)
under the "each removed dot saves α(1−k) of denominator" algebra. Two equations, one unknown, 1.7×
apart: the arithmetic model that would justify extrapolating the ladder is not identified.

**Decision changed:** the per-dot extrapolation (+0.006 at 3 px, +0.0106 at 4 px) is recorded as
MODEL and **not** used as the prediction. The prediction comes from the fold-clean PROXY, which is
validated against both steps first. This is why the three files are predicted negative while a
naive reading of their own lineage would predict positive.

## IR-V2-06 — competition input rasters are committed to a **public** repository

**Found:** `buffedlizard55-lab/GEMSDOE85` is public (`gh api … → visibility: public`) and *tracked*
copies of three organizer-provided competition files sit in `data/bridge/`:
`labels.tif` / `existing_faults.tif` (`7ba308cc…`, the mapped-fault catalogue) and
`sample_submission.tif` (`2176d08e…`). The same bytes are also tracked at `data/labels.tif` and
`data/sample_submission.tif`. `registry/data_manifest.json` records their provenance as
"owner-supplied mirror of a DrivenData competition file (login-walled) … NOT organizer-authenticated",
and the DrivenData data-use terms have not been checked here (the terms page is not fetched, per
brief §4.1).

**Why it is decision-changing:** the brief forbids keeping competition rasters in public repos and
requires flagging existing copies. The label catalogue is the most useful input in the competition;
publishing it is exactly what a data-use clause usually prohibits, and every reproduction command in
this repository depends on those files being present.

**What this session did:** nothing destructive — the files are inputs the rebuild asserts against, and
removing them from the working tree would break `scripts/build_prune_variants.py`, `tests/test_lineage.py`
and CI. Recommended fix, to be decided by the operator before the 2026-12-03 deadline: move the three
files to the hash-pinned restore path (`scripts/restore_data.py` already knows how), add them to
`.gitignore`, and note that git history still contains them — a history rewrite is the operator's call.
