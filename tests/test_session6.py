"""Unit and contract tests for Session-6 (`src/gems85/next_gen.py`) advances and defect fixes."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from gems85 import emission, metric, next_gen, submission

ROOT = Path(__file__).resolve().parents[1]


def test_expected_kernel_credit_peaks_on_fault_line():
    """expected_kernel_credit(p) must reach its strict maximum on the centerline of a fault ribbon."""
    h, w = 48, 48
    fp = np.ones((h, w), dtype=bool)
    p = np.zeros((h, w), dtype=np.float32)
    p[22:26, 6:42] = 0.8
    p[23:25, 6:42] = 1.0  # centerline around y=23..24
    c = next_gen.expected_kernel_credit(p, fp)
    assert c.shape == (h, w)
    assert c.dtype == np.float32
    # Centerline must have strictly higher expected credit than shoulders at y=20 or y=27
    assert float(c[23, 24]) > float(c[20, 24])
    assert float(c[23, 24]) > float(c[27, 24])


def test_crest_1step_collapses_ribbon_onto_centerline():
    """IR-85-007 fix: crest_1step collapses a 2D probability ribbon onto its 1-px axial crest."""
    h, w = 64, 64
    fp = np.ones((h, w), dtype=bool)
    yy, xx = np.mgrid[0:h, 0:w]
    # Smooth horizontal fault ribbon centered at y = 32 with Gaussian half-width 4 px
    ribbon = np.exp(-0.5 * ((yy - 32.0) / 4.0) ** 2).astype(np.float32)
    thinned = next_gen.crest_1step(ribbon, fp, sigma=1.0, keep_floor=0.04)

    # Emit 14 dots with sep=3.6 px: all dots must lie on the centerline y=32, not in a 2D blob
    dots = emission.emit(thinned, footprint=fp, visible_catalogue=np.zeros_like(fp), n=14, sep_px=3.6, exclude_px=0) > 0
    ys, _ = np.nonzero(dots)
    assert ys.size == 14
    assert np.all(np.abs(ys - 32) <= 1), f"dots wandered off centerline: {ys}"


def test_shipped_session6_submission_beats_pr6_and_d28_on_holdout():
    """Verify the promoted Session-6 run card and submission artifacts on disk."""
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    sub = json.loads((ROOT / "registry" / "submission.json").read_text())

    assert card["verdict"] == "promote-as-candidate"
    assert card["holdout_dti"]["label"] == "HOLDOUT-DTI"
    assert card["holdout_dti"]["value"] > 0.11153, "must beat d2.8 static holdout benchmark"
    assert card["holdout_dti"]["value"] > 0.09838, "must beat PR #6 90k GEO-Pb v1"
    assert card["holdout_dti"]["ci95"][0] > 0.10654, "lower 95% CI must exceed PR #6 upper 95% CI"
    assert card["budget"]["experiments_run"] <= 3
    assert len(card["submission_note"]) <= 140
    assert not card["correlation_vs_registry"]["is_duplicate"]

    for item in sub["ladder"]:
        z_path = ROOT / "docs" / "downloads" / Path(item["zeros"]["path"]).name
        n_path = ROOT / "docs" / "downloads" / Path(item["nan"]["path"]).name
        assert z_path.exists(), z_path
        assert n_path.exists(), n_path
        rep = submission.validate(z_path)
        assert rep.passed, rep.checks
