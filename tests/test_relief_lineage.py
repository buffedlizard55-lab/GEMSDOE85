"""Tests for AXIS = RELIEF tercile-mass exchange, byte-identical R0 rebuild, and shipped gates."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems85 import r0_lineage as RL  # noqa: E402
from gems85 import relief_lineage as REL  # noqa: E402
from gems85.thinning85 import dot_thin  # noqa: E402

HAVE_FULL_DATA = all(p.is_file() for p in RL.PATHS.values()) and all(
    p.is_file() for p in REL.EXTRA_PATHS.values()
)


def _synthetic_relief_fields(H: int = 90, W: int = 90) -> REL.ReliefFields:
    foot = np.ones((H, W), dtype=bool)
    foot[:3, :] = False
    yy, xx = np.mgrid[:H, :W]
    raw = 0.7 * (yy / H) + 0.3 * (xx / W)
    rank = REL._deterministic_pct_rank(raw, foot)
    n_foot = int(foot.sum())
    n1, n2 = n_foot // 3, (2 * n_foot) // 3
    order = np.lexsort((np.arange(n_foot), raw[foot]))
    codes = np.empty(n_foot, dtype=np.int8)
    codes[order[:n1]] = 0
    codes[order[n1:n2]] = 1
    codes[order[n2:]] = 2
    grid_t = np.full((H, W), -1, dtype=np.int8)
    grid_t[foot] = codes
    terciles = {
        "basin": grid_t == 0,
        "piedmont": grid_t == 1,
        "range": grid_t == 2,
    }
    rng = np.random.default_rng(42)
    score = rng.uniform(0.0, 1.0, (H, W))
    cand_pool = foot.copy()
    return REL.ReliefFields(
        foot=foot,
        relief_index=rank,
        terciles=terciles,
        tercile_summary={},
        dot_rank_score=score,
        cand_pool=cand_pool,
        cand_score_range=score + 0.1,
        cand_score_basin=score + 0.2,
        ancestor_union=(yy % 4 == 0) & foot,
    )


def test_deterministic_pct_rank_and_equal_terciles():
    rf = _synthetic_relief_fields(90, 90)
    counts = [int(rf.terciles[k].sum()) for k in REL.TERCILE_NAMES]
    assert sum(counts) == int(rf.foot.sum())
    assert max(counts) - min(counts) <= 1
    assert not (rf.terciles["basin"] & rf.terciles["piedmont"]).any()
    assert not (rf.terciles["piedmont"] & rf.terciles["range"]).any()


def test_shift_relief_terciles_preserves_count_collar_spacing_and_determinism():
    rf = _synthetic_relief_fields(96, 96)
    cat = np.zeros((96, 96), dtype=bool)
    cat[45, 20:75] = True
    dist_cat = ndimage.distance_transform_edt(~cat)

    seed_mask = np.zeros((96, 96), dtype=bool)
    seed_mask[8::4, 6::4] = True
    seed_mask &= rf.foot & (dist_cat > 2.0)
    base = dot_thin(seed_mask, 2.8)
    assert int((base & (dist_cat <= 3.0)).sum()) > 0  # ensures collar clearing is exercised

    delta = {"basin": -12, "piedmont": -8, "range": +20}
    m1, det1 = REL.shift_relief_terciles(base, dist_cat, rf, delta)
    m2, det2 = REL.shift_relief_terciles(base, dist_cat, rf, delta)
    assert np.array_equal(m1, m2)
    assert det1 == det2
    assert int(m1.sum()) == int(base.sum())
    assert int((m1 & (dist_cat <= 3.0)).sum()) == 0
    for k in REL.TERCILE_NAMES:
        assert det1["after_tercile_dots"][k] == det1["before_tercile_dots"][k] + delta[k]

    # Newly added dots must respect >= 2.8 px Euclidean spacing against all kept dots
    added_yx = np.argwhere(m1 & ~base)
    all_yx = np.argwhere(m1)
    for y, x in added_yx:
        d = np.hypot(all_yx[:, 0] - y, all_yx[:, 1] - x)
        d = d[d > 0]
        assert d.min() >= 2.8 - 1e-9


def test_shift_relief_rejects_non_zero_sum():
    rf = _synthetic_relief_fields(40, 40)
    base = np.zeros((40, 40), dtype=bool)
    base[10, 10] = True
    dist = np.full((40, 40), 10.0)
    with pytest.raises(ValueError, match="preserve count"):
        REL.shift_relief_terciles(base, dist, rf, {"basin": -1, "piedmont": 0, "range": 0})


def test_shipped_ledger_and_relief_releases_pass_all_gates():
    """Runs unconditionally in CI using tracked sample_submission.tif + labels.tif."""
    ledger = ROOT / "ledger" / "submissions.csv"
    receipt_path = ROOT / "evidence" / "session_relief_receipt.json"
    docs_mirror = ROOT / "docs" / "evidence" / "session_relief_receipt.json"
    assert ledger.is_file() and receipt_path.is_file() and docs_mirror.is_file()
    assert receipt_path.read_bytes() == docs_mirror.read_bytes()

    rows = list(csv.DictReader(ledger.open()))
    # Dedupe check across entire ledger on sha256 and on (parent, axis, value)
    shas = [r["sha256"] for r in rows]
    assert len(shas) == len(set(shas)), "Duplicate sha256 in ledger/submissions.csv"
    pairs = [(r["parent"], r["axis"], r["value"]) for r in rows]
    assert len(pairs) == len(set(pairs)), "Duplicate (parent, axis, value) in ledger/submissions.csv"

    relief_rows = [r for r in rows if r["axis"] == "RELIEF"]
    assert len(relief_rows) == 3

    with rasterio.open(ROOT / "data" / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
        exp_crs = str(s.crs)
        exp_transform = tuple(s.transform)[:6]
    with rasterio.open(ROOT / "data" / "labels.tif") as lds:
        cat = lds.read(1) == 1
    dist_cat = ndimage.distance_transform_edt(~cat)

    rec = json.loads(receipt_path.read_text())
    assert rec["parent_rebuild"]["byte_identical_geotiff_rebuild"] is True
    assert rec["report_only_proxies"]["leakage_canary"]["verdict"] == "CLEAN"
    assert rec["report_only_proxies"]["leakage_canary"]["best_single_feature_auc"] < 0.90

    for row in relief_rows:
        assert row["parent"] == "h33-h33-2-b2"
        assert row["status"] == "BUILT" and row["receipt"] == "N"
        assert int(row["n_dots"]) == 37654
        pct = float(row["pct_changed"])
        assert 1.0 <= pct <= 50.0
        assert row["sha8"] == row["sha256"][:8]

        tif_nan = ROOT / "releases" / f"{row['id']}.tif"
        tif_zeros = ROOT / "releases" / f"{row['id']}-zeros.tif"
        assert tif_nan.is_file() and tif_zeros.is_file()
        assert RL.sha256_file(tif_nan) == row["sha256"]

        key = row["id"].rsplit("-", 2)[0]
        entry = rec["variants"][key]
        assert len(entry["submission_note"]) <= 140
        assert entry["all_gates_passed"] is True

        with rasterio.open(tif_nan) as ds_n:
            a_n = ds_n.read(1)
            assert ds_n.count == 1 and ds_n.dtypes[0] == "float32"
            assert str(ds_n.crs) == exp_crs
            assert tuple(ds_n.transform)[:6] == exp_transform
            assert np.isnan(ds_n.nodata)
        assert np.isfinite(a_n[foot]).all()
        assert np.isnan(a_n[~foot]).all()
        pos = a_n > 0.5
        assert int(pos.sum()) == 37654
        assert int((pos & cat).sum()) == 0
        assert float(dist_cat[pos].min()) > 3.0

        with rasterio.open(tif_zeros) as ds_z:
            a_z = ds_z.read(1)
            assert ds_z.nodata is None
        assert np.isfinite(a_z).all()
        assert np.array_equal(np.nan_to_num(a_n, nan=0.0), a_z)


@pytest.mark.skipif(not HAVE_FULL_DATA, reason="restored data_manifest rasters absent")
def test_r0_byte_identical_geotiff_rebuild_and_manifest_hashes():
    mrep = REL.verify_manifest_hashes()
    assert mrep["data_manifest.json"]["count"] == 23
    assert mrep["learning_manifest.json"]["count"] == 2
    L, rrep = REL.rebuild_and_verify_r0_bytes()
    assert L.counts()["r0"] == 37654
    assert rrep["rebuilt_r0_nan_sha256"] == RL.PINS["r0_nan"]
    assert rrep["rebuilt_r0_zeros_sha256"] == RL.PINS["r0_zeros"]
