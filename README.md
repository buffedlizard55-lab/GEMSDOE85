# GEMSDOE85 — auditable fault-discovery submission gate

## Executive status — 2026-10-22 safety review

**BLOCKED — DO NOT SUBMIT. No unique-cleared submission TIFF is available.**
The previous “OK to submit” headline was incorrect under the literal parallel-run protocol.
Historical rasters are preserved under `submissions/quarantine/`, not offered as approved downloads.
The historical GEO-Pb card reports dot overlap **0.991433** (REGISTRY-MEASUREMENT, not DTI),
above the required **0.70** limit. A chance-corrected exemption cannot override that gate.
No new geological experiment or competition upload was performed in this review.

- [Current executive summary](docs/executive-summary.html) explains the automated gates and future upload steps.
- [Current run card](evidence/run_card.json) is a **negative preflight**, not a geological negative result.
- [Safety review](research/safety-review-2026-10-22.md) records contradictions, fixes, limitations and next steps.
- [Historical README](research/archive/README-before-safety-review.md) preserves earlier claims without endorsing them.
- [Research shortlist](research/hypotheses.md): four proposed hypotheses; none is a lane assignment.
- The literal overlap-saturation obstruction, missing assigned lane and absent pinned transformed cache block generation.
- The owner-reported H33 result is not an ORGANIZER-CONFIRMED score: no submission-page receipt is present.
  Sparse pruning is a plausible metric mechanism, not proof of a score's cause or a forecast of improvement.
- Maximize P(Win): do not spend slots on unsupported claims. Own the Outcome: fail closed and preserve contrary evidence.

### Reproduce this review

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/python scripts/preflight.py   # exit 2 = blocked, not a model failure
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/check_site.py
.venv/bin/python -m pytest
```

Read this README and `AGENTS.md` at each session start. The standing brief below is an inherited
requirements summary, **not a verbatim full prompt transcript**. The archived README's claim of a
complete transcription was not supportable; the original chat remains the authority.

---

## The standing brief

> **Transcription note.** The operator's brief arrived as a chat message, not a file. What follows
> is an inherited requirements summary, grouped by topic; wording is the
> operator's where it was preserved verbatim. It is the standing starting point — **re-read this
> section at the start of every session before doing anything else.** It must not be treated as a byte-for-byte copy of the original prompt. Where a requirement was met, the link says where; where it was not, the
> *Limitations* section says so.

### Objective

Work on the **DOE GEMS Prize Challenge**, DrivenData competition #306
(<https://www.drivendata.org/competitions/306/competition-doe-gems/>). Build, in the empty repo
`GEMSDOE85`, a complete, auditable, self-driving system that produces a **unique,
downloadable, submission-ready single-band GeoTIFF**.

Answer with PhD-level rigor: **why** did the artifact
`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` score **0.2778**, and can we beat it? The target
is to beat the stated leaderboard high (the brief gives 0.3195, and separately 0.4413 as the
GEMSDOE leaderboard high).

### Hard requirements

1. **Generate a UNIQUE TIF submission.** It must not duplicate any artifact on the prior
   GEMSDOE sites. Prior submissions may be studied **for learning/education only**.
2. **It must be obvious on the site whether the generated TIF is OK to download and submit.**
   The one-click download goes in the **executive summary at the very top** of the site.
3. **Validation must be automated in-project — no human inspector** — and must **gate**
   submission. Many prior sites said "inspection only / human inspector"; that is not acceptable.
4. **Fix the prior failure.** A previous submission form upload was rejected with
   **"Predicted values must be in range [0, 1]"**. Values must be in [0, 1], no NaN inside the
   footprint, CRS / shape / geotransform matching the submission format.
5. Provide a **unique submission name** and a **≤ 140-character note** string, so submissions can
   be told apart.
6. Create an **executive-summary subpage** explaining **exactly how to submit**.
7. **Put the full prompt into the repo README** as the standing starting point.
8. **Before implementing**, generate **3–5 new geological hypotheses**. Each must name the
   specific layers, the physical signature/transform, **why it catches a fault _missing_ from the
   USGS/INGENIOUS catalogue** rather than one already in it, and how it differs from what is in
   the repo. Rank by expected DTI gain vs implementation cost. **Validate the top candidate on
   the spatially-blocked holdout before spending a weekly submission slot.**
9. Do **deep original research on geothermal-vent discovery**, stored as reusable knowledge from
   **official verified sources**.
10. Build a **clean, simple GitHub Pages site** with all information and official source links.
11. Run a **three-pass workflow**: implement + verify → review and fix bugs and edge cases →
    re-check against the original request. Do not stop after the first pass.
12. **Finish by creating a pull request and merging it to main**, then list remaining work,
    suggestions and limitations.
13. **State my limitations and what access is needed.**

### How the work must be done

- Work **line by line, verifying from official verified trusted sources**; provide links for
  manual review. **Flag irregularities. No hallucinations.**
- **No manual input from the user** — work autonomously, end to end.
- Use only **free, publicly available, official/verified** external data. If a candidate needs new
  external data, **name the specific free official source and confirm obtainability first.**
- Keep **Arena's Core Values — "Maximize P(Win)" and "Own the Outcome"** — central to building,
  developing, researching, suggesting upgrades and implementing.
- Be **contrarian but scientifically grounded**; find data others overlook. The heart of the
  project is the **scientific discovery of geothermal vents**.
- **Work on next steps from previous sessions first.**
- **Do not spend a weekly submission slot on an idea that has not beaten the current holdout
  best.**

### Parallel-run protocol (this session is one lane of several)

- **Stay in one method lane.** If rank-correlation with any registry raster > 0.90, or > 70 % of
  dots fall within 3 px of one registry raster's dots, **log as duplicate and stop.** Check on the
  surface before placement **and** on the final dots.
- **Reuse the template's cached feature stack, `evaluate_holdout.py`, `submission_writer.py`.
  Fix shared tools in the template, never fork privately.**
- **Holdout = hide-and-recover**: withhold whole fault segments with a buffer; derive
  catalogue-based features **only from visible faults**; mask visible faults **pixel-exactly**;
  score pooled DTI (α 0.2, β 0.8, 300 m triangular kernel).
- **Label every number** as `HOLDOUT-DTI` (evaluator version, number of withheld positives, 95 %
  CI) or `ORGANIZER-CONFIRMED`. **A projection is never written as a score.**
- **Leakage canary**: test each feature alone on the holdout; **AUC > 0.90 means leakage** until
  proven otherwise.
- End with **one JSON run card**: hypothesis; mechanism; named non-fault mimic process; holdout
  DTI + CI; correlation/overlap vs registry; raster sha256; validator output; submission name +
  ≤ 140-char note; verdict promote/negative. **Negative results are deliverables.**
- **Budget: stop after 3 experiments or 2 hours.** Do not pick submissions — promotion to a real
  slot is a separate selector step.

---
