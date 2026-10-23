#!/usr/bin/env python3
"""MODEL: what a <=2 px re-placement can do to R0's captured credit.

Projection only. Never a score. The parent's live 0.2778 is a CLAIM with no receipt.

Everything follows from the parent's own published back-solve (README section 1):

    n        = 37,654 dots
    T        = 5,470   captured credit
    M        = 2,188   credited mass  (M = n - F, F = 35,466 = "uncredited mass")
    K        = 14,400  hidden truth pixels
    DTI      = T / (alpha*(T + F) + beta*K) = 0.2776   (published 0.2778; rounding)

Two consequences, and they are the whole argument:

1. **The dots that earn anything sit on truth.**  Credited mass M = 2,188 is spread over
   n - F = 2,188 dots, so the mean self-credit of a credited dot is k = M/(n-F) = 1.00,
   i.e. distance to the nearest hidden truth pixel is ~0 px.  94.2 % of dots (F = 35,466)
   earn exactly nothing and are free to move.

2. **For a dot already on a 1-px trace, a re-placement cannot gain self-credit** (k is
   already maximal at 1) and generally loses it: a move of length m at angle phi to the
   local strike leaves a perpendicular offset m*|sin phi|, so

       k_after = max(0, 1 - m*|sin phi| / 3).

   Along-strike moves (phi ~ 0) are free; every other direction is a loss.  A random
   direction gives E|sin phi| = 2/pi = 0.637.

So the expected change is **non-positive by construction** unless the snap is
directionally informed (moves dots along strike, or lands uncredited dots exactly on a
trace).  The two available local measurements of that skill are the leakage canary in
evidence/session_snap.json (single-band AUC 0.499-0.557 against withheld catalogue
positives -- indistinguishable from an uninformative field) and the SGMC control (agreement
with independently mapped faults *falls* monotonically as more dots are snapped).

The script reports, per variant, the best case (all moves along strike), the random case,
and the probability that an uncredited dot lands on truth by chance.

Usage:  python scripts/snap_mechanism_model.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ALPHA, BETA, R = 0.2, 0.8, 3.0
N_DOTS, T_PARENT, M_CREDITED, K_TRUTH, F_UNCREDITED = 37654, 5470.0, 2188.0, 14400.0, 35466.0
LIVE_PARENT = 0.2778


def dti(t: float) -> float:
    """DTI from captured credit t, holding the free-mass term F and |G| fixed.

    Conservative reading: a re-placed dot that keeps a non-zero self-credit keeps its
    own contribution to ``n - M`` unchanged, so only the numerator moves.
    """
    return t / (ALPHA * (t + F_UNCREDITED) + BETA * K_TRUTH)


def main() -> int:
    ev = json.loads((ROOT / "evidence/session_snap.json").read_text())
    base = dti(T_PARENT)
    f_credited = M_CREDITED / N_DOTS
    out = dict(
        schema_version=1, kind="MODEL",
        note="projection, never a score. Parent 0.2778 is CLAIM (no receipt); T, M, F, K are "
             "the repo's own back-solve of that claim, so every number here inherits it.",
        inputs=dict(n_dots=N_DOTS, T=T_PARENT, M_credited=M_CREDITED,
                    F_uncredited=F_UNCREDITED, K_truth=K_TRUTH,
                    credited_dot_share=round(f_credited, 4),
                    mean_self_credit_of_credited_dot=round(M_CREDITED / (N_DOTS - F_UNCREDITED), 4),
                    alpha=ALPHA, beta=BETA, kernel_px=R,
                    model_baseline_dti=round(base, 5), claimed_live=LIVE_PARENT),
        chance_uncredited_dot_lands_on_truth=round(
            (N_DOTS - F_UNCREDITED) / 5167373.0, 8),
        variants={})

    for v in ev["variants"]:
        st = v["stats"]
        m = st["mean_displacement_px"]
        moved = st["n_moved"]
        moved_credited = moved * f_credited
        # per moved credited dot: loss is (m/3)*E|sin phi|, capped at its own k (>= 1.0 available)
        esin_random = 2.0 / np.pi
        loss_random = min(1.0, (m / R) * esin_random)
        loss_best = 0.0                       # every move happens along strike: free
        out["variants"][v["value"]] = dict(
            mean_displacement_px=m, n_moved=moved,
            pct_of_all_dots_moved=st["pct_moved"],
            n_credited_dots_moved=round(moved_credited, 1),
            loss_per_moved_credited_dot_random=round(loss_random, 4),
            delta_T_best_case=0.0,
            delta_T_random_case=round(-loss_random * moved_credited, 1),
            dti_best_case=round(dti(T_PARENT) - base, 5),
            dti_random_case=round(dti(T_PARENT - loss_random * moved_credited) - base, 5),
            predicted=dict(low=v["predicted"]["low"], high=v["predicted"]["high"],
                           text=v["predicted"]["text"]))

    out["reading"] = (
        "A snap of this parent is a bet that the edge field knows the local strike better "
        "than the parent's own field, because the parent's credited dots already sit on "
        "truth and cannot gain self-credit. The measured evidence for that skill is absent: "
        "canary AUC 0.499 (iso_grav_anom_hg) and 0.525 (tmi_hg) against withheld catalogue "
        "positives, and SGMC agreement falling with every increase in the moved fraction. "
        "Best case (all moves along strike) is exactly zero for all three variants.")
    (ROOT / "evidence/snap_mechanism_model.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1)[:2600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
