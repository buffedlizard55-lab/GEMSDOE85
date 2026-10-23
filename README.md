# GEMSDOE85 — DOE GEMS fault research and fail-closed release gate

**Current status (2026-10-23): BLOCKED — DO NOT DOWNLOAD OR SUBMIT ANY HISTORICAL TIFF.**

This repository currently has **no new candidate GeoTIFF** cleared for competition use. The
previous public Pages content incorrectly presented historical files as ready. Those links have
been removed, and files retained for audit/education are quarantined under `submissions/quarantine/`,
and the site now fails closed. A format-valid raster is not, by itself, unique, scientifically
validated, or authorized for a weekly submission slot.

| Gate | Current finding |
|---|---|
| **Method lane** | `registry/lane.json` is `unassigned`; the prompt's “single method paragraph” is not present. No lane may be selected by inference. |
| **Feature data/cache** | The pinned transformed feature-stack manifest is empty/unavailable; the raw `training_features.tif` is not present in this checkout. Owner-mirror hashes do not establish organizer authentication. |
| **Uniqueness** | The binding `REGISTRY-MEASUREMENT` certificate in `evidence/saturation_certificate.json` records full coverage of the allowed domain by one prior under the literal positive-support definition. Its witness is not locally revalidated in this checkout. The protocol's >70% overlap stop is not waived. |
| **Holdout** | No candidate or comparable current-best paired holdout was evaluated in this preflight. `HOLDOUT-DTI`: not run; no withheld-positive count or 95% CI exists for a current candidate. |
| **Submission** | No new raster, name, receipt, or slot selection. The current verdict is `negative` (blocked preflight, not a geological negative). |
| **Site** | `docs/index.html` states the decision at the top; `docs/executive-summary.html` explains the future upload process without offering a file. |

The demand to produce a unique TIF conflicts with the binding literal duplicate-stop certificate and the missing lane/cache prerequisites. Generating a placeholder, moving predictions into known-fault pixels, or changing the overlap definition would not be a scientifically honest solution. Therefore this session **does not create or promote a TIFF**. A separate selector step, within the organizer's actual weekly cap, remains required even after a valid candidate exists.

```bash
python -m pip install -r requirements-lock.txt
python -m pytest -q                         # offline tests
python scripts/preflight.py                 # expected exit 2 while blocked; writes the negative run card
python scripts/build_site.py
python scripts/check_site.py                # must pass with no public TIF/ZIP links or files
```

> **Standing brief:** read this README in full at the start of each project session. Historical
> result tables and candidate write-ups later in this file describe prior sessions only; they do
> not override the current block above. Scores supplied in the chat or sibling-project pages are
> not `ORGANIZER-CONFIRMED` without a submission-page receipt. For current blockers, see
> [`research/review.md`](research/review.md), [`evidence/run_card.json`](evidence/run_card.json),
> and [`registry/irregularities.json`](registry/irregularities.json).

---
## The standing brief

> **Transcription note.** The operator's brief arrived as a chat message, not a file. What follows
> is a faithful, complete transcription of its requirements, grouped by topic; wording is the
> operator's where it was preserved verbatim. It is the standing starting point — **re-read this
> section at the start of every session before doing anything else.** Nothing below has been
> softened or dropped. Where a requirement was met, the link says where; where it was not, the
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

### Complete prompt verbatim text

<details>
<summary>Click to view the full prompt verbatim as requested</summary>

```
Review the repo. 

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.  A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413		

0.3195	is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.  

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Our Core Values: Maximize P(Win) / Own the Outcome

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:
"Predicted values must be in range [0, 1]"
Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.
Work on the next steps from the previous sessions first.
Pass 1: Implement the task completely and verify the result.
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.
Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.
Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.
```
</details>

---


## Historical project record (superseded)

The pre-reconciliation README is preserved verbatim at
[`research/archive/README-pre-2026-10-23-reconciliation.md`](research/archive/README-pre-2026-10-23-reconciliation.md).
It contains previous-session candidate, lane, score, experiment, and publishing claims. These
records are retained for audit, but they are **not revalidated current results**, do not override
`AGENTS.md`, and do not authorize a current download or weekly slot. The governing current review
is [`research/review.md`](research/review.md); the single machine-readable decision record is
[`evidence/run_card.json`](evidence/run_card.json).
