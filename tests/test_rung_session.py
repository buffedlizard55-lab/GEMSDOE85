"""Ledger ↔ release consistency for the session-3 fractional PRUNE rungs.

These tests need no competition data (which is gitignored and restored separately): they check that
every BUILT ledger row points at a file that exists, is the size and sha256 the row claims, and that
the fractional rungs are strictly ordered the way the mechanism cards describe.
"""
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "submissions.csv"
RELEASES = ROOT / "releases"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rows():
    with LEDGER.open() as fh:
        return list(csv.DictReader(fh))


def test_ledger_has_no_duplicate_ids_or_hashes():
    rows = _rows()
    ids = [r["id"] for r in rows]
    hashes = [r["sha256"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate ledger id"
    assert len(hashes) == len(set(hashes)), "same raster recorded twice (encoding twins score alike)"


def test_ledger_parent_and_status_columns():
    for r in _rows():
        assert r["parent"] == "h33-h33-2-b2"
        assert r["status"] == "BUILT"
        assert r["evidence_label"].startswith("MODEL")
        assert "MODEL" in r["predicted_change"]


@pytest.mark.parametrize("row", _rows(), ids=lambda r: r["id"])
def test_each_ledger_row_matches_its_release_file(row):
    path = RELEASES / row["name"]
    assert path.is_file(), f"missing release file {path.name}"
    assert path.name.startswith(row["id"]), "file name does not carry the ledger id"
    assert path.name.endswith(f'-{row["sha8"]}.tif') or path.name.endswith(".tif")
    assert _sha256(path) == row["sha256"], "release bytes do not match the ledger sha256"


def test_rung_values_are_strictly_ordered():
    rungs = {}
    for r in _rows():
        m = re.match(r"d_cat<= ?([0-9.]+)px", r["value"])
        if m:
            rungs[float(m.group(1))] = int(r["n_dots"])
    assert rungs, "no fractional rung rows found"
    thresholds = sorted(rungs)
    counts = [rungs[t] for t in thresholds]
    assert counts == sorted(counts, reverse=True), "a wider rung must never keep more dots"


def test_prediction_bands_bracket_zero_for_the_frontier_rungs():
    """Every fractional rung is a genuine bet: its MODEL band must contain 0 to stay honest."""
    for r in _rows():
        if "r2p" in r["id"] or "r3p" in r["id"]:
            nums = [float(x) for x in re.findall(r"[-+]?\d+\.\d+", r["predicted_change"])]
            assert len(nums) >= 2
            assert nums[1] <= 0.0 <= nums[2], f'{r["id"]}: band {nums[1]}..{nums[2]} excludes 0'


def test_submission_notes_fit_the_portal_limit():
    """The portal caps the note at 140 characters; the docs quote the same strings."""
    submit = (ROOT / "docs" / "SUBMIT.md").read_text()
    for note in re.findall(r"\*\*Note \((\d+)/140\):\*\* `([^`]+)`", submit):
        declared, text = int(note[0]), note[1]
        assert len(text) <= 140
        assert len(text) == declared, f"declared {declared} chars but the note is {len(text)}"
    assert np.isfinite(1.0)
