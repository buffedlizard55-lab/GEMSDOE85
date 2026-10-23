"""v2 PRUNE builder/validator regressions. Offline; pinned-data tests skip cleanly."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from scripts.build_prune_variants import PINS, content_digest8, greedy_refill
from scripts.validate_v2_release import sha256_file, validate

ROOT = Path(__file__).resolve().parents[1]


def test_content_digest8_is_packbits_tag():
    mask = np.zeros((4, 8), dtype=bool)
    mask[1, 2] = True
    assert content_digest8(mask) == hashlib.sha256(np.packbits(mask)).hexdigest()[:8]


def test_greedy_refill_spacing_count_determinism():
    rng = np.random.default_rng(306)
    kept = np.zeros((60, 60), dtype=bool)
    kept[10, 10] = kept[40, 40] = True
    pool = rng.random((60, 60)) < 0.4
    pool &= distance_transform_edt(~kept) > 2.0
    cand = np.flatnonzero(pool)
    a = greedy_refill(pool, kept, cand, need=50, spacing=2.0)
    b = greedy_refill(pool, kept, cand, need=50, spacing=2.0)
    assert (a == b).all(), "greedy refill must be deterministic"
    assert int(a.sum()) == 50
    assert not (a & kept).any() and (a <= pool).all()
    yx = np.column_stack(np.nonzero(kept | a))
    nn, _ = cKDTree(yx).query(yx, k=2)
    assert float(nn[:, 1].min()) > 2.0


def test_greedy_refill_respects_order_and_cap():
    pool = np.zeros((10, 30), dtype=bool)
    pool[5, :] = True
    kept = np.zeros_like(pool)
    cand = np.flatnonzero(pool)
    out = greedy_refill(pool, kept, cand, need=3, spacing=2.0)
    assert int(out.sum()) == 3
    assert out[5, 0] and out[5, 3] and out[5, 6]  # first-fit in scan order


def _tiny_profile():
    return dict(driver="GTiff", dtype="float32", count=1, height=6, width=5,
                crs="EPSG:32611", transform=Affine(100, 0, 0, 0, -100, 600))


def test_validator_rejects_unpinned_template(tmp_path):
    # The validator must fail closed rather than grade against wrong bytes.
    sample = tmp_path / "sample.tif"
    with rasterio.open(sample, "w", **_tiny_profile(), nodata=np.nan) as ds:
        ds.write(np.zeros((6, 5), dtype=np.float32), 1)
    cat = tmp_path / "cat.tif"
    with rasterio.open(cat, "w", **dict(_tiny_profile(), dtype="int8")) as ds:
        ds.write(np.zeros((6, 5), dtype=np.int8), 1)
    with pytest.raises(ValueError, match="pin"):
        validate(sample, sample, cat, "nan")


@pytest.mark.skipif(
    not all((ROOT / rel).is_file() and sha256_file(ROOT / rel) == pin
            for rel, pin in [PINS[k] for k in ("r0", "h27", "d28", "catalogue")]),
    reason="pinned lineage rasters not restored in this checkout")
def test_rebuild_gate_content_exact():
    from scripts.build_prune_variants import read_dots
    cat = read_dots(ROOT / PINS["catalogue"][0])
    dist = distance_transform_edt(~cat)
    r0 = read_dots(ROOT / PINS["r0"][0])
    h27 = read_dots(ROOT / PINS["h27"][0])
    d28 = read_dots(ROOT / PINS["d28"][0])
    assert int(r0.sum()) == 37_654
    assert bool(((h27 & (dist > 2)) == r0).all())
    assert bool(((d28 & (dist > 1)) == h27).all())
    assert content_digest8(r0) == "e5eb6e7e"


@pytest.mark.skipif(
    not (ROOT / "releases").is_dir() or not list((ROOT / "releases").glob("*.tif")),
    reason="release rasters are local-only (git-ignored); build them first")
def test_built_releases_pass_format_gates():
    import json
    builds = json.loads((ROOT / "evidence/v2-prune-builds.json").read_text())
    sample, cat = ROOT / PINS["sample"][0], ROOT / PINS["catalogue"][0]
    known = {a["sha256"] for a in
             json.loads((ROOT / "registry/scored_artifacts.json").read_text())["artifacts"]}
    for variant in builds["variants"].values():
        for enc, info in variant["files"].items():
            report = validate(ROOT / info["path"], sample, cat, enc)
            assert report["format_ok"], report
            assert report["sha256"] not in known  # never a repeat of a scored file
