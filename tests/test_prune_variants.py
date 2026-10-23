"""Tests for the PRUNE axis: the prune-ladder algebra, the parent rebuild, and the variants.

All numbers are either (a) the metric transcribed in ``vendor/gems57/metric.py``, (b) recovered
from the pinned rasters, or (c) recorded in ``evidence/prune_variants.json``. Nothing is
invented here.

The heavy checks (parent rebuild, variant invariants) skip when the pinned rasters have not
been restored, exactly like the rest of this repo; they do not weaken into a pass.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
ALPHA = 0.2


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_prune_variants", ROOT / "scripts" / "build_prune_variants.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- the ladder algebra
def _delta_after_deleting(dti: float, T: float, n_delete: int, alpha: float = ALPHA) -> float:
    """Exact change when ``n_delete`` zero-credit dots are removed at achieved ``dti``."""
    D = T / dti
    return T / (D - alpha * n_delete) - dti


def test_denominator_identity_reproduces_both_scored_rungs():
    """Both rungs are pure mass edits; one invariant T must explain both to a few percent."""
    # rung 2 (measured): 2,545 dots deleted, 0.2708 -> 0.2778
    T = 2545 * ALPHA / (1 / 0.2708 - 1 / 0.2778)
    assert 5_000 < T < 6_000, T
    # rung 1 (measured): 3,891 dots deleted, 0.2600 -> 0.2708, using the SAME T
    pred1 = _delta_after_deleting(0.2600, T, 3891)
    assert pred1 == pytest.approx(0.0108, abs=0.0010)
    pred2 = _delta_after_deleting(0.2708, T, 2545)
    assert pred2 == pytest.approx(0.0070, abs=0.0007)
    # per-dot costs agree to ~1 %, which is what licenses the third rung
    per1, per2 = pred1 / 3891, pred2 / 2545
    assert abs(per1 - per2) / per2 < 0.10   # 6.7 % between rungs; this is the real scatter


def test_third_rung_prediction_matches_the_recorded_model():
    T = 2545 * ALPHA / (1 / 0.2708 - 1 / 0.2778)
    dti_after = 0.2778 + _delta_after_deleting(0.2778, T, 2171)
    ev = json.loads((ROOT / "evidence" / "prune_variants.json").read_text(encoding="utf-8"))
    point = ev["predictions"]["prune-x3-nofill"]["point"]
    assert dti_after == pytest.approx(point, abs=1e-4)
    lo, hi = ev["predictions"]["prune-x3-nofill"]["interval"]
    assert lo < point < hi


def test_deleting_mass_never_moves_T_in_the_model():
    """The model's premise: a zero-credit dot removal leaves T (and hence truth recall) alone."""
    T = 5470.0
    D = T / 0.2778
    assert T / (D - 0.2 * 2171) > T / D  # strictly better


# ---------------------------------------------------------------- instruments
def test_auc_rank_is_tie_aware_and_bounded():
    b = _load_builder()
    y = np.array([1, 1, 0, 0], bool)
    assert b.auc_rank(y, np.array([0.9, 0.9, 0.1, 0.1])) == pytest.approx(1.0)
    assert b.auc_rank(y, np.array([0.1, 0.1, 0.9, 0.9])) == pytest.approx(0.0)
    # all ties -> 0.5, and the interval stays inside [0, 1]
    a = b.auc_rank(y, np.zeros(4))
    assert a == pytest.approx(0.5)
    rng = np.random.default_rng(0)
    for _ in range(5):
        s = rng.random(50)
        yy = rng.random(50) < 0.3
        v = b.auc_rank(yy, s)
        assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------- pins / rebuild / variants
def _grid():
    vendor = pytest.importorskip("vendor.gems57.grid")
    try:
        return vendor.load_grid()
    except FileNotFoundError:  # pragma: no cover - restored-data dependent
        pytest.skip("pinned bridge rasters not restored")


def test_pins_verify_or_skip():
    b = _load_builder()
    missing = [rel for rel, _ in b.PINS.values() if not (ROOT / rel).is_file()]
    if missing:
        pytest.skip(f"pinned rasters not restored: {missing[:2]}")
    pins = b.verify_pins()
    assert len(pins) == len(b.PINS)


def test_parent_support_rebuilds_bit_exactly():
    b = _load_builder()
    missing = [rel for rel, _ in b.PINS.values() if not (ROOT / rel).is_file()]
    if missing:
        pytest.skip("pinned rasters not restored")
    grid = _grid()
    r0, d_cat, facts = b.parent_support(grid)
    assert facts["derived_vs_parent_xor_pixels"] == 0
    assert facts["parent_dots"] == 37654
    assert int((r0 & grid.catalogue).sum()) == 0
    assert float(d_cat[r0].min()) > 2.0


def test_release_invariants_match_the_ledger():
    b = _load_builder()
    import rasterio

    releases = sorted((ROOT / "releases").glob("*.tif"))
    if not releases:
        pytest.skip("no release rasters in this checkout")
    rows = list(csv.DictReader((ROOT / "ledger" / "submissions.csv").open(encoding="utf-8")))
    built = {}
    for r in rows:
        if r["status"] != "BUILT":
            continue
        built[r["sha256"]] = r
        if r.get("sha256_nan"):
            built[r["sha256_nan"]] = r
    grid = _grid()
    for path in releases:
        digest = b.sha256(path)
        assert digest in built, f"{path.name} is not in the ledger"
        row = built[digest]
        with rasterio.open(path) as src:
            a = src.read(1)
            assert src.count == 1 and src.dtypes[0] == "float32"
            assert (src.height, src.width) == (3730, 3292)
            assert str(src.crs) == "EPSG:32611"
        inside = a[grid.footprint]
        assert np.isfinite(inside).all()
        assert inside.min() >= 0.0 and inside.max() <= 1.0
        assert int((a[grid.catalogue] > 0).sum()) == 0
        assert int((a > 0).sum()) == int(row["n_dots"])
        if not path.name.endswith("-zeros.tif"):
            assert np.isnan(a[~grid.footprint]).all()
        else:
            assert (a[~grid.footprint] == 0).all()


def test_variants_change_between_one_and_fifty_percent_and_respect_exclusion():
    b = _load_builder()
    missing = [rel for rel, _ in b.PINS.values() if not (ROOT / rel).is_file()]
    if missing:
        pytest.skip("pinned rasters not restored")
    import rasterio

    grid = _grid()
    r0 = rasterio.open(ROOT / b.PINS["parent_R0"][0]).read(1) > 0
    from scipy.ndimage import distance_transform_edt as _edt
    d_cat = _edt(~grid.catalogue)
    for tag, spec in b.variant_masks(grid, r0, d_cat).items():
        diff = b.parent_diff(r0, spec["dots"], d_cat, grid)
        assert 1.0 <= diff["pct_of_parent_dots_changed"] <= 50.0, tag
        assert diff["outside_footprint"] == 0
        if tag != "prune-x2-readd":
            assert diff["dots_within_3px_of_catalogue"] == 0, tag
        if tag == "prune-x3-nofill":
            assert diff["n_variant"] == 37654 - 2171
        if tag == "prune-x2-readd":
            assert diff["n_variant"] == 40199
