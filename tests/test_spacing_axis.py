"""Gates for the SPACING (and inherited MASS) releases, against the merged ledger schema.

The ledger is shared with four other sessions and its column set changes as they land, so
these tests read it positionally by name and skip columns they do not know.  They assert
only what a release must guarantee: the file on disk is the file the ledger describes, the
filename carries the hash it actually has, the axis/value pair is claimed once, and the
changed fraction is inside the brief's 1-50 % band.
"""
from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "submissions.csv"
SESSION_AXES = {"SPACING", "MASS"}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rows() -> list[dict]:
    if not LEDGER.is_file():
        pytest.skip("no ledger")
    with LEDGER.open(newline="") as fh:
        return list(csv.DictReader(fh))


def session_rows() -> list[dict]:
    return [r for r in rows() if r.get("axis") in SESSION_AXES]


def test_this_sessions_rows_are_present_for_both_axes():
    axes = Counter(r["axis"] for r in session_rows())
    assert axes["SPACING"] == 3, axes
    assert axes["MASS"] == 3, axes


def test_every_session_file_hashes_as_the_ledger_says():
    for r in session_rows():
        primary = ROOT / "releases" / r["name"]
        zeros = ROOT / "releases" / f"{r['id']}-zeros.tif"
        assert primary.is_file(), primary
        assert zeros.is_file(), zeros
        assert sha256_file(primary) == r["sha256"], f"sha256 drift: {primary.name}"


def test_filename_carries_its_own_sha8():
    for r in session_rows():
        name = r["name"]
        m = re.search(r"-([0-9a-f]{8})\.tif$", name)
        assert m, name
        assert r["sha256"].startswith(m.group(1)), f"{name}: sha8 != file hash"
        assert r["axis"] in name.upper().replace("H33-2-B2-", ""), name
        assert len(r["id"]) <= 140


def test_changed_fraction_inside_the_brief_band():
    for r in session_rows():
        pct = float(r["pct_changed"])
        assert 1.0 <= pct <= 50.0, (r["id"], pct)


def test_spacing_files_hold_the_parent_count_and_mass():
    for r in session_rows():
        if r["axis"] == "SPACING":
            assert int(r["n_dots"]) == 37654, r["id"]


def test_no_axis_value_pair_is_claimed_twice():
    pairs = Counter((r["axis"], r["value"]) for r in rows() if r.get("axis"))
    dupes = {k: v for k, v in pairs.items() if v > 1}
    assert not dupes, f"rebuild of an existing (axis, value) pair: {dupes}"


def test_no_duplicate_hashes_across_the_whole_ledger():
    hashes = [r["sha256"] for r in rows() if r.get("sha256")]
    assert len(hashes) == len(set(hashes)), "two rows share a raster hash"


# ---------------------------------------------------------------- mechanism, on hand values

def marginal_T(site_credit: float, already_covered: float) -> float:
    """Credit a new dot actually adds where the best existing cover is `already_covered`."""
    return max(0.0, site_credit - already_covered)


def alpha_cost(k_nearest_truth: float, alpha: float = 0.2) -> float:
    return alpha * (1.0 - k_nearest_truth)


def test_a_gap_filler_cannot_beat_a_unique_cover():
    """The finding this session rests on, as arithmetic rather than opinion.

    A gap filler sits between two dots, so the best cover at its site is already k(1.41) = 0.53
    and its marginal T is at most 1 - 0.53 = 0.47, while its nearest-truth credit is 1.0 so it
    pays no alpha.  A dot that is the sole cover of a pixel contributes up to 1.0.
    """
    gap_gain = marginal_T(1.0, 0.53)

    assert gap_gain == pytest.approx(0.47)
    assert gap_gain < 1.0, "a gap filler must never look like a fresh cover"
    assert alpha_cost(1.0) == pytest.approx(0.0)


def test_the_kernel_gives_the_measured_midpoint_credit():
    """k(1.414 px) is the number quoted in the cards; check it against the definition."""
    k = max(0.0, 1.0 - np.hypot(1, 1) / 3.0)
    assert k == pytest.approx(0.5286, abs=1e-3)
