"""Gates for the AXIS=MASS release, runnable without the competition rasters.

Two kinds of assertion:

* on-disk release integrity -- every row in ``ledger/submissions.csv`` must point at a file
  whose sha256 equals the ledger's, whose name encodes that same sha8, and whose sibling
  ``-nan`` twin exists.  This is what catches a renamed or hand-edited deliverable.
* the mechanism arithmetic -- the marginal-gain bar from the problem statement, evaluated
  on hand-computable cases, and the drop-order tie-break rule that makes the MASS variants
  reproducible.
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


def test_every_built_release_exists_and_hashes_as_the_ledger_says():
    built = [r for r in rows() if r["status"].startswith("BUILT")]
    assert built, "no BUILT rows in the ledger"
    for r in built:
        zeros = ROOT / r["file_zeros"]
        nan = ROOT / r["file_nan"]
        assert zeros.is_file(), zeros
        assert nan.is_file(), nan
        assert sha256_file(zeros) == r["sha256"], f"sha256 drift: {zeros.name}"


def test_release_filename_encodes_its_own_sha8_and_variant():
    # Only rows this repo wrote.  The lineages from other repos carry a historical
    # "content digest8" in the name that is not the container sha256 (e.g. h33-2-b2).
    for r in rows():
        if not r["file_zeros"] or not r["status"].startswith("BUILT"):
            continue
        name = Path(r["file_zeros"]).name
        m = re.search(r"-([0-9a-f]{8})-zeros\.tif$", name)
        assert m, f"filename does not carry a sha8: {name}"
        assert r["sha256"].startswith(m.group(1)), f"{name}: sha8 does not match the file hash"
        assert r["axis"] in name.upper(), f"{name}: axis not in the filename"
        assert len(r["id"]) <= 140


def test_variants_change_between_one_and_fifty_percent_of_the_parent():
    for r in rows():
        if not r["status"].startswith("BUILT"):
            continue
        pct = float(r["pct_changed"])
        assert 1.0 <= pct <= 50.0, r["id"]


def test_no_two_built_rows_share_a_hash():
    hashes = [r["sha256"] for r in rows() if r["sha256"]]
    assert len(hashes) == len(set(hashes)), "duplicate raster hash in the ledger"


def test_mass_variants_have_the_declared_dot_counts():
    for r in rows():
        if r["axis"] != "MASS":
            continue
        expected = {"-10%": 33887, "+10%": 41415, "-20%": 30124}[r["value"]]
        assert int(r["n_dots"]) == expected


# ---------------------------------------------------------------- mechanism arithmetic

def improves_on_removal(dt: float, k: float, dti0: float = 0.2778, alpha: float = 0.2) -> bool:
    """Removing one dot helps iff its unique truth credit is below alpha*DTI*(dt+1-k).

    From DTI = T/(alpha*(T + n - M) + beta*|G|): dropping a dot with unique truth credit
    ``dt`` and self-credit ``k`` leaves the same numerator minus ``dt`` and the denominator
    minus ``alpha*(dt + 1 - k)``.
    """
    return dt * 1.0 < dti0 * alpha * (dt + 1.0 - k)


def test_removal_bar_matches_the_hand_computed_cases():
    # a dot sitting exactly on truth (k = dt = 1) is never worth removing at DTI 0.28
    assert not improves_on_removal(dt=1.0, k=1.0)
    # a dot that earns no credit at all (k = dt = 0) always pays to remove: it is pure
    # alpha charge.  This is the mechanism the -MASS variants bet on.
    assert improves_on_removal(dt=0.0, k=0.0)
    # the crossing point, solved by hand: dt < 0.2*DTI*(dt + 1 - k), k = dt
    #   -> dt < 0.2*DTI -> dt < 0.05556 at DTI 0.2778
    assert improves_on_removal(dt=0.05, k=0.05)
    assert not improves_on_removal(dt=0.06, k=0.06)


def test_drop_order_is_weakest_credit_first_with_a_declared_tie_break():
    credit = np.array([2.0, 1.0, 2.0, 2.0])
    dcat = np.array([10.0, 99.0, 99.0, 10.0])
    y = np.array([1, 0, 0, 0])
    x = np.array([5, 9, 3, 1])
    order = np.lexsort((x, y, -dcat, credit))
    assert list(order) == [1, 2, 3, 0], "tie-break changed: -MASS would not be reproducible"
