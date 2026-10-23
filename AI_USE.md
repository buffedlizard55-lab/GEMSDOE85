# AI_USE — disclosure required by the challenge rules (reproducible code; generative-AI disclosure)

Session `arena/59608071-gemsdoe85`, 2026-10-23. One entity, no submission was made by an agent.

## What the AI wrote

* `scripts/run_snap_variants.py` — parent rebuild, edge field, greedy snap, file writing, gates.
* `scripts/snap_mechanism_model.py` — the credit-loss projection.
* `scripts/build_ledger.py` — ledger assembly from pinned artefacts.
* `tests/test_snap_session.py` — invariants for the snap/eligibility code.
* This session's prose: `SLOT_PLAN.md`, `IRREGULARITIES.md`, `docs/SUBMIT.md`, the mechanism
  cards below, and the README `CURRENT STATE` block.

## What the human decided

* **The AXIS (SNAP)**, chosen from the four options offered, on 2026-10-23.
* **No TOP_PUBLIC target** is supplied, so no leaderboard number was invented or fetched
  (fetching drivendata.org is barred by its terms of use and by the brief).
* **Slot accounting:** 3 of 3 left this week, 0 used.
* **Score evidence:** no submission receipts exist; everything is CLAIM.

## One design change after pre-registration, and why

The first design was a **displacement ladder** (d = 1 px → d = 2 px → d = 2 px + DEM scarp
channel) with an unconditional move to the local argmax. Before any score of any kind was
computed, the geometry showed that an unconditional snap moves **98.2 %** of R0's dots: it does
not refine the parent, it replaces its localisation wholesale. That cannot be a controlled
single change. The ladder was therefore re-cut as a **gain-threshold ladder** at the brief's
maximum displacement (τ = 0.20 → 0.10 → 0.00), where τ = 0.00 is the brief's literal definition
and the two other settings move 7.3 % and 19.2 % of dots.

No score, proxy value, canary, or SGMC number was computed before this change. Both the original
predictions and the final ones are in the git history of the script.

## Mechanism cards (for a structural geologist)

### `snapd2t20` — SNAP, d ≤ 2 px, gain threshold 0.20 (7.32 % of dots move, mean 0.136 px)
* **Hypothesis.** Where the parent field and the potential-field contact field disagree
  strongly, the parent's dot is misplaced; moving it to the contact crest recovers credit.
* **Mechanism.** Faults are contacts. The horizontal gradient of a potential field peaks over a
  contact; R0's dots come from a different operator (scarp/ridge lineage, H19→H27→H33). Two
  independent locators agreeing at one pixel is evidence neither carries alone.
* **Mimic.** High horizontal gradient also occurs at the margins of magnetic bodies (basalt
  flows, intrusions), at the edge of alluvial fill against bedrock, and at survey-block seams —
  none of which is a fault.
* **Predicted sign/size.** Pre-registered +0.000…+0.008; the credit-loss model
  (`evidence/snap_mechanism_model.json`) gives −0.003 (random direction) to 0.000 (all moves
  along strike).
* **Falsifier.** Live Δ < 0.01 = no evidence. A live *loss* while `prune3` is flat would say the
  moved dots are the ones that were earning credit.

### `snapd2t10` — gain threshold 0.10 (19.17 % moved, mean 0.365 px)
Identical hypothesis and mimic; four times the intervention. Pre-registered +0.000…+0.012,
model −0.008…0.000. Falsifier as above; it exists to show the dose-response of the *same* change,
which is the only way to tell a mechanism from noise at this effect size.

### `snapd2t00` — gain threshold 0.00, i.e. every dot to the local argmax (98.53 % moved, mean 1.764 px)
* **Hypothesis.** The parent's per-dot localisation is worse than the edge field's, everywhere.
* **Mechanism.** None beyond the previous card, applied without a disagreement test — this is the
  brief's literal definition, and its value is as the **upper bound on what a pure snap can do**.
* **Mimic.** As above; at this intervention size the raster's Jaccard overlap with the parent
  falls to **0.0074**, i.e. it is a different map that happens to keep the same dot count.
* **Predicted sign/size.** Pre-registered −0.015…+0.015; model −0.039…0.000.
* **Falsifier.** If this scores ≈ 0.2778, the parent's localisation carries no information at
  all — a result that would redirect the whole project away from field quality and towards
  emission count.

### `prune3` — control, no snapping, ≥ 3 px catalogue exclusion only (4.28 % moved, mean 0.076 px)
* **Hypothesis.** The 2.236/2.828 px ring is waste, because those pixels are masked live.
* **Mechanism.** Known-fault pixels are removed from scoring; dots there neither earn nor cost,
  but they consume mass that could sit elsewhere. (Counter-mechanism: new faults concentrate
  near known ones, so the ring is also where new truth is likeliest.)
* **Mimic.** None; this is a null change by construction.
* **Predicted sign/size.** +0.000…+0.005, on the strength of the parent's own 2 px prune (+0.007)
  and the thinner remaining ring.
* **Falsifier.** A loss means the ring was earning credit — i.e. new-fault truth does lie within
  300 m of known traces, exactly as the organizer said, and the ≥ 3 px rule is a mistake.
