"""Tests for the PRUNE session: metric algebra, the R0 rebuild, and the emitted files.

Tests that need the pinned parent rasters skip when those rasters are absent, because CI runs
without network access and without ``work/ref``.  Everything that can run on the tracked bridge
files alone (the template, the catalogue, the DTI algebra, the gates) always runs.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from gems85 import lineage as L  # noqa: E402
from gems85 import metric as repo_metric  # noqa: E402

LEDGER = ROOT / "ledger" / "submissions.csv"
RELEASES = ROOT / "releases"


# --------------------------------------------------------------------------------- algebra
@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_dti_matches_the_repository_metric(seed: int) -> None:
    """The brief's algebra must be the same function the repository already ships."""
    rng = np.random.default_rng(seed)
    pred = (rng.random((48, 48)) > 0.94).astype(np.float64)
    truth = rng.random((48, 48)) > 0.96
    mine = L.dti(pred, truth)
    theirs = repo_metric.dti_exact(pred, truth)
    assert mine["dti"] == pytest.approx(theirs["dti"], abs=1e-12)
    assert mine["T"] == pytest.approx(theirs["tp_w"], abs=1e-9)


def test_kernel_offsets_are_the_triangular_disc() -> None:
    """R = 3 px: a dot exactly on truth gives k = 1, and the disc has 29 cells including itself."""
    assert (0, 0, 1.0) in [(dy, dx, k) for dy, dx, k in L.OFFSETS]
    assert all(np.hypot(dy, dx) <= 3.0 for dy, dx, _ in L.OFFSETS)
    assert all(0.0 <= k <= 1.0 for _, _, k in L.OFFSETS)


def test_marginal_gain_is_positive_on_truth_and_zero_far_away() -> None:
    truth = np.zeros((40, 40), bool)
    truth[20, 20] = True
    pred = np.zeros((40, 40))
    assert L.marginal_gain(pred, truth, 20, 20) > 0
    assert L.marginal_gain(pred, truth, 0, 0) == 0.0


def test_adding_mass_inside_the_kernel_beats_adding_it_outside() -> None:
    truth = np.zeros((40, 40), bool)
    truth[20, 20] = True
    pred = np.zeros((40, 40))
    inside = L.marginal_gain(pred, truth, 21, 20)     # 1 px away, k = 2/3
    outside = L.marginal_gain(pred, truth, 25, 20)    # 5 px away, k = 0
    assert inside > outside


# ------------------------------------------------------------------------------ the rebuild
def _have_pins() -> bool:
    return all(Path(L.PINNED[k]["dest"]).is_file() for k in ("r0", "d28"))


@pytest.mark.skipif(not _have_pins(), reason="pinned parent rasters not fetched in this checkout")
def test_r0_rebuilds_pixel_exactly_from_its_parent() -> None:
    fp, cat = L.load_template()
    dist = L.catalogue_distance(cat)
    d28 = L.read_dots(Path(L.PINNED["d28"]["dest"]))
    r0 = L.read_dots(Path(L.PINNED["r0"]["dest"]))
    assert np.array_equal(L.prune(d28, dist, 2.0) & fp, r0)


@pytest.mark.skipif(not _have_pins(), reason="pinned parent rasters not fetched in this checkout")
def test_pruning_is_monotone_in_the_cutoff() -> None:
    fp, cat = L.load_template()
    dist = L.catalogue_distance(cat)
    d28 = L.read_dots(Path(L.PINNED["d28"]["dest"]))
    counts = [int(L.prune(d28, dist, c).sum()) for c in (0.0, 1.0, 2.0, 3.0, 4.0)]
    assert counts == sorted(counts, reverse=True)
    assert len(set(counts)) == len(counts)


@pytest.mark.skipif(not _have_pins(), reason="pinned parent rasters not fetched in this checkout")
def test_euclidean_and_chebyshev_cutoffs_are_not_interchangeable() -> None:
    """A cutoff of 3 px must mean 300 m, not three king-moves: the two rules differ here."""
    fp, cat = L.load_template()
    dist = L.catalogue_distance(cat)
    d28 = L.read_dots(Path(L.PINNED["d28"]["dest"]))
    cheb2 = np.zeros_like(cat, bool)
    cheb2[2:-2, 2:-2] = cat[:-4, :-4] | cat[1:-3, :-4] | cat[2:-2, :-4] | cat[3:-1, :-4] | cat[4:, :-4]
    assert int((L.prune(d28, dist, 2.0)).sum()) != int((d28 & ~cheb2).sum())


# ----------------------------------------------------------------------------------- gates
def test_gate_rejects_a_dot_on_the_catalogue(tmp_path: Path) -> None:
    fp, cat = L.load_template()
    dots = np.zeros(fp.shape, bool)
    y, x = np.argwhere(cat)[0]
    dots[y, x] = True
    path = tmp_path / "bad.tif"
    L.write_nan(path, dots, fp)
    rep = L.gates(path, fp, cat, mode="nan")
    assert not rep["ok"]
    assert any("on catalogue" in p for p in rep["problems"])


def test_gate_accepts_a_clean_pair(tmp_path: Path) -> None:
    fp, cat = L.load_template()
    dots = np.zeros(fp.shape, bool)
    dots[1000, 1000] = True
    nan_path, zeros_path = tmp_path / "clean.tif", tmp_path / "clean-zeros.tif"
    L.write_nan(nan_path, dots, fp)
    L.write_zeros(zeros_path, dots)
    assert L.gates(nan_path, fp, cat, mode="nan")["ok"]
    assert L.gates(zeros_path, fp, cat, mode="zeros")["ok"]


def test_gate_rejects_nan_inside_the_footprint(tmp_path: Path) -> None:
    import rasterio
    fp, cat = L.load_template()
    path = tmp_path / "holes.tif"
    L.write_nan(path, np.zeros(fp.shape, bool), fp)
    with rasterio.open(path) as src:
        arr = src.read(1)
        prof = src.profile
    y, x = np.argwhere(fp)[0]
    arr[y, x] = np.nan
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(arr, 1)
    rep = L.gates(path, fp, cat, mode="nan")
    assert not rep["ok"] and any("inside the footprint" in p for p in rep["problems"])


# ------------------------------------------------------------------------------- the output
@pytest.mark.skipif(not LEDGER.is_file(), reason="no ledger on this branch")
def test_every_ledger_row_has_two_validated_files() -> None:
    rows = list(csv.DictReader(LEDGER.open()))
    assert rows, "ledger exists but is empty"
    fp, cat = L.load_template()
    dist = L.catalogue_distance(cat)
    for r in rows:
        nan = RELEASES / f"{r['id']}.tif"
        zeros = RELEASES / f"{r['id']}-zeros.tif"
        assert nan.is_file() and zeros.is_file(), r["id"]
        assert L.sha256_file(nan) == r["sha256"]
        nan_rep = L.gates(nan, fp, cat, mode="nan", dist=dist, min_catalogue_px=0.0)
        zeros_rep = L.gates(zeros, fp, cat, mode="zeros", dist=dist, min_catalogue_px=0.0)
        for rep, expected in ((nan_rep, r["n_dots"]), (zeros_rep, r["n_dots"])):
            assert rep["ok"], rep["problems"]
            assert int(L.read_dots(nan if rep is nan_rep else zeros).sum()) == int(expected)
        assert nan_rep["dots_on_catalogue"] == 0
        pct = float(r["pct_changed"])
        if r["axis"] != "SNAP":          # the brief exempts SNAP from the 1-50 % window
            assert 1.0 <= pct <= 50.0


@pytest.mark.skipif(not LEDGER.is_file(), reason="no ledger on this branch")
def test_ledger_has_no_duplicate_hash_or_axis_value_pair() -> None:
    rows = list(csv.DictReader(LEDGER.open()))
    hashes = [r["sha256"] for r in rows]
    assert len(hashes) == len(set(hashes))
    pairs = [(r["parent"], r["axis"], r["value"]) for r in rows]
    assert len(pairs) == len(set(pairs))


# ---------------------------------------------------------------------------------- MASS axis
def _mass_inputs():
    need = ("r0", "h19_5")
    return all(Path(L.PINNED[k]["dest"]).is_file() for k in need)


@pytest.mark.skipif(not _have_pins(), reason="pinned rasters not fetched in this checkout")
def test_mass_arms_move_exactly_ten_percent() -> None:
    from gems85 import mass as M
    r0 = L.read_dots(Path(L.PINNED["r0"]["dest"]))
    field = L.read_dots(Path(L.PINNED["h19_5"]["dest"]))
    rank = M.rank_by_extent(r0, field)
    drop_e = M.drop_by_rank(r0, rank, M.DELTA)[0]
    drop_u = M.drop_uniform(r0, M.DELTA)[0]
    for arm in (drop_e, drop_u):
        assert int(r0.sum()) - int(arm.sum()) == M.DELTA
        assert not (arm & ~r0).any(), "a deletion arm added mass"
    added = M.add_by_extent(r0, field, np.zeros_like(r0, float) + 99.0, M.DELTA)[0]
    assert int(added.sum()) - int(r0.sum()) == M.DELTA


@pytest.mark.skipif(not _mass_inputs(), reason="pinned rasters not fetched in this checkout")
def test_the_two_deletion_arms_are_not_the_same_set() -> None:
    """If the ranking were degenerate (e.g. raster order) the arms would coincide."""
    from gems85 import mass as M
    r0 = L.read_dots(Path(L.PINNED["r0"]["dest"]))
    field = L.read_dots(Path(L.PINNED["h19_5"]["dest"]))
    rank = M.rank_by_extent(r0, field)
    e = M.drop_by_rank(r0, rank, M.DELTA)[0]
    u = M.drop_uniform(r0, M.DELTA)[0]
    overlap = int((r0 & ~e & ~u).sum())     # dots dropped by BOTH arms
    assert overlap < 0.25 * M.DELTA, overlap


def test_structural_ranking_is_catalogue_free() -> None:
    """The rank must depend only on the field's geometry, never on the fault catalogue."""
    from gems85 import mass as M
    field = np.zeros((30, 30), bool)
    field[5:25, 5] = True       # one long structure
    field[8, 20] = True         # one speck
    field[9, 24] = True         # another speck
    r0 = field.copy()
    rank = M.rank_by_extent(r0, field)
    # rank 0 is the FIRST dot to be dropped, i.e. the smallest structure
    assert rank[8, 20] < rank[5, 5], "speckle must rank below (be dropped before) a long structure"


def test_mechanism_cards_exist_and_are_complete() -> None:
    cards = ROOT / "evidence" / "mechanism_cards.json"
    if not cards.is_file():
        pytest.skip("no mechanism cards on this branch")
    data = json.loads(cards.read_text())
    required = {"hypothesis", "mechanism", "mimic", "predicted_change", "falsifier"}
    assert len(data["cards"]) == 3
    for card in data["cards"]:
        assert required <= set(card), card.get("id")
        assert len(card["falsifier"]) > 40


def test_mass_mechanism_cards_exist_and_are_complete() -> None:
    cards = ROOT / "evidence" / "mechanism_cards_mass.json"
    if not cards.is_file():
        pytest.skip("no MASS cards on this branch")
    data = json.loads(cards.read_text())
    required = {"hypothesis", "mechanism", "mimic", "predicted_change", "falsifier", "id"}
    assert len(data["cards"]) == 3
    for card in data["cards"]:
        assert required <= set(card), card.get("id")
        assert len(card["falsifier"]) > 40
        pred = card["predicted_change"]
        assert -0.05 < pred["central"] < 0.05, "a MASS prediction that large needs a receipt"
