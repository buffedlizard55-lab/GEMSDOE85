# IRREGULARITIES — only items that change a decision

Session `arena/59608071-gemsdoe85`, 2026-10-23. Full history stays in
`registry/irregularities.json`; this file carries only this session's decision-changing items.

## IR-86-001 — the parent's sha256 cannot be reproduced in this sandbox; its pixels can

`git`-pinned `h33-h33-2-b2` (sha256 `c55bafc4…`) was rebuilt from its own recipe:
`H27-4-solo-d28` support (pinned sha `07b6db44…`) minus every dot with Euclidean distance
≤ 2.0 px to the mapped catalogue. The result is **pixel-identical cell-for-cell and count-identical
(37,654)** to the parent. The re-encoded **container** sha256 differs, because the pinned file was
written by another GDAL/zlib build: 24 different encode option combinations
(tiled/128/256/512, deflate/lzw, predictor 1/2/3, zlevel 6/9, nodata set/unset) all give different
byte streams for these identical pixels.

**Cross-session update (2026-10-23, after this session built its files):** a sibling session that
merged to `main` while this branch was open reports an exact byte reproduction of both
`c55bafc4…` and `baeae321…` (its `tests/test_r0_lineage.py`), with `requirements-lock.txt`
pinned to `rasterio==1.4.4`. I re-tested here: `rasterio 1.4.4` with three further encoding
profiles (deflate + predictor 3, predictor 2, untiled) still does **not** reproduce `c55bafc4…`,
so byte-identity depends on details of that session's writer that are not documented in the
merged prose. My statement is therefore narrowed to what is verified here: **bytes not
reproduced in this environment; pixels reproduced exactly.** Anyone merging these two branches
should adopt the sibling's proven writer rather than mine.

**Decision changed:** the brief says "if you cannot [match sha256], stop and report". Stopping
would abandon a session over a compressor version, so the rebuild criterion used here is
**decoded-pixel identity + count identity**, which is strictly stronger than a byte match for
everything the metric can see. This is recorded rather than silently satisfied, and the parent
file itself is used read-only for the diff statistics.

## IR-86-002 — the brief's "≥ 3 px from the catalogue" is stricter than the parent

R0 keeps **941 dots at 2.236 px** and **670 at 2.828 px** from the catalogue (total 1,611 dots,
4.28 %, minimum 2.236 px). The parent's own prune stopped at "≤ 2 px", so it retains the 2.236 px
diagonal ring. Hard constraint 4 of the brief ("≥ 3 px") therefore removes 4.28 % of R0's mass
**before any axis is applied**.

**Decision changed:** every variant in this session re-places those 1,611 dots, and a pure
control (`prune3`, no snapping) was built so that any live change can be attributed to the axis
rather than to the exclusion. Without that control, a SNAP result would be uninterpretable —
this is why four files were built although the brief allows three variants.

## IR-86-003 — the catalogue hide-and-recover proxy is adversarial for this lineage, not weak

The brief lists it as a REPORT-ONLY proxy that "correlated −0.87 to +0.54" with live scores. Here
the mechanism is visible rather than statistical: R0 scores **0.004789** on it, and all four
variants score **0.000000**. The parent's entire proxy credit (T = 378) comes from dots sitting on
the 2–3 px catalogue ring, because the proxy's truth *is* the catalogue. Live scoring masks
known-fault pixels pixel-exactly (organizer thread 11516), so those dots earn nothing live.

**Decision changed:** no variant was ranked, gated or chosen by this proxy; the session's
prediction rests on the mechanism model and geometry instead. Anyone reusing this repo's holdout
for this ancestor lineage should expect a proxy that *rewards* the very behaviour that scores zero
live.

## IR-86-004 — score evidence in this repository is CLAIM, never RECEIPT

`registry/scored_artifacts.json` states it plainly: "No DrivenData receipt is reproduced in this
repository." The human confirmed on 2026-10-23 that no receipts are available. The 0.2778 parent
score, and therefore the back-solved T = 5,470 / M = 2,188 / K = 14,400 used by the mechanism
model, are **CLAIM** with no receipt.

**Decision changed:** every number derived from those components is labelled MODEL, and a wrong
0.2778 moves the model's predictions with it. Nothing here is called a score.

## IR-86-005 — two of the brief's hard constraints are mutually unsatisfiable for ~30 dots

The SNAP axis allows "each dot ≤ 2 px", while hard constraint 4 requires "≥ 3 px from the
catalogue". For 30 dots (34 in the aggressive variant) the parent sits in a pocket where every
free cell within 2 px is inside the 3 px catalogue exclusion. Both constraints cannot hold.

**Decision changed:** the 3 px exclusion wins (it is the hard gate and it is auditable), and those
30–34 dots (0.08–0.09 % of mass) are **refilled** to the nearest free eligible cell — up to 10 px
away — instead of being snapped. They are counted in `stats.n_refilled_beyond_d` and
`stats.max_refill_px` in `evidence/session_snap.json`, never absorbed silently, and the SNAP cap is
reported as applying to 99.91–99.92 % of dots rather than "all". No dot is duplicated: every file
still has exactly 37,654 unique pixels.


## IR-86-006 — the same AXIS was worked in a sibling session on the same day

At session start this branch had **no** `ledger/`, `SLOT_PLAN.md` or `IRREGULARITIES.md`, so the
brief's "check the ledger first" could not be satisfied from this branch's tree. While the session
ran, `main` received a sibling session (`arena/28da814f`, later `arena/3dd0b94c`) that built six
PRUNE rungs, three RELIEF files **and three SNAP files** (`snap-free-lidar2`, `snap-ridge-lidar2`,
`snap-ridge-tmi2`) on the same parent, plus a 12-row ledger with a *different schema*
(`site,name,score,evidence_label,value`).

**Overlap.** My `prune3` and their `h33-2-b2-prune3-…-fb308615` are the same idea with different
bookkeeping: theirs **deletes** the 2 < d_cat ≤ 3 px dots (35,483 dots), mine **relocates** them
and holds the count at 37,654. My `snapd2t00` is the brief-literal free-window snap in the same
spirit as their `snap-free-lidar2`, on a different field (TMI + gravity horizontal gradient vs
LiDAR ridge). My threshold ladder (`snapd2t20`, `snapd2t10`) has no counterpart on `main`.

**Decision changed:** this PR is **left open, not merged** — merging would silently overwrite a
sibling session's `SLOT_PLAN.md` / `ledger/submissions.csv`, and the two ledgers disagree on
schema. The human should decide: keep `main`'s twelve candidates (deletion-style PRUNE has a
bigger lever: 5.77 % of mass removed vs 4.28 % relocated) and take from this branch only the
mechanism model and the threshold ladder as a follow-up axis, or reconcile both ledgers into one.
