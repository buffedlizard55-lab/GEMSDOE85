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


def test_session6_history_is_preserved_but_not_release_authority():
    """Byte/receipt diagnostics cannot authorize an overlap-violating candidate."""
    import hashlib
    card = json.loads((ROOT / "evidence/run_card_session6_historical.json").read_text())
    sub = json.loads((ROOT / "registry/submission_session6_historical.json").read_text())
    current = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert card["holdout_dti"]["label"] == "HOLDOUT-DTI"
    assert len(card["holdout_dti"]["ci95"]) == 2
    assert card["correlation_vs_registry"]["max_dot_overlap_3px"] > 0.70
    assert current["safe_to_submit"] is False
    assert current["verdict"] == "negative"
    assert sub["release_status"].startswith("historical-only")
    path = ROOT / "docs/downloads" / sub["primary"]["filename"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == card["raster_sha256"]
    # This is a synthetic/byte contract, not a new HOLDOUT-DTI experiment.
    rows = {row["file"]: row for row in current["historical_artifacts"]}
    assert rows[path.relative_to(ROOT).as_posix()]["format_ok"]
    assert not rows[path.relative_to(ROOT).as_posix()]["safe_to_submit"]
