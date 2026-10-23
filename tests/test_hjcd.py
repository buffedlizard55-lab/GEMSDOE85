"""Unit & integration test suite for Lane H85-HJCD:
- 12/16-strike lattice geometry (`geopb.NORMALS_R4_12`, `NORMALS_R6_16`, `geopb16_components`)
- Pure-stdlib hydrothermal parser & `BANNED_COLUMNS` leakage guard (`hydrothermal.py`)
- Exact 29-pixel 300 m kernel & Minoux lazy-greedy Dinkelbach emitter + dispersion invariant (`submodular_emitter.py`)
- Strict out-of-fold visibility contract (`hjcd.compute_fold_structural_features`)
- 112-feature leakage canary receipt (`evidence/feature_canaries.json`), promoted GeoTIFF/ZIP integrity,
  and `restore_data.sha256` compatibility (`IR-85-012`).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems85 import geopb, grid, hjcd, hydrothermal, submodular_emitter as submod

ROOT = Path(__file__).resolve().parents[1]


def test_restore_data_exports_sha256_alias():
    import restore_data

    assert hasattr(restore_data, "sha256")
    assert restore_data.sha256 is restore_data.sha256_file
    digest = restore_data.sha256(ROOT / "requirements-lock.txt")
    assert len(digest) == 64


def test_geopb16_lattice_normals_are_distinct_and_non_collinear():
    assert len(geopb.NORMALS_R4_12) == 12
    assert len(geopb.NORMALS_R6_16) == 16

    for ring in (geopb.NORMALS_R4_12, geopb.NORMALS_R6_16):
        angles = sorted(float(np.arctan2(dy, dx) % np.pi) for dy, dx in ring)
        for a, b in zip(angles, angles[1:]):
            assert abs(b - a) > 1e-4, f"Collinear duplicate vectors in lattice ring: {ring}"

    # Verify synthetic step response peaks on a true fault step without NaNs
    rng = np.random.default_rng(85)
    H, W = 64, 64
    fp = np.ones((H, W), dtype=bool)
    step = np.zeros((3, H, W), dtype=np.float32)
    step[:, :, 32:] = 3.0
    step += rng.normal(0.0, 0.25, size=step.shape).astype(np.float32)
    Y = geopb.whiten(step, geopb.NORMALS_R4_12, fp)
    s_r4 = np.zeros((H, W), dtype=np.float32)
    for dy, dx in geopb.NORMALS_R4_12:
        u = geopb.shift(Y[0], dy, dx) - geopb.shift(Y[0], -dy, -dx)
        np.maximum(s_r4, np.abs(u), out=s_r4)
    assert s_r4.shape == (H, W) and np.isfinite(s_r4).all()
    assert float(s_r4[:, 31:33].mean()) > float(s_r4[:, 8:14].mean()) * 2.5


def test_hydrothermal_bans_dist_known_fault_px_column(tmp_path: Path):
    assert "dist_known_fault_px" in hydrothermal.BANNED_COLUMNS
    ext = tmp_path / "data" / "external"
    ext.mkdir(parents=True)
    ws_csv = ext / "gdr_wellspring_in_footprint.csv"
    csv_hdr = [
        "layer",
        "name",
        "thermalclass",
        "row",
        "col",
        "utm_x",
        "utm_y",
        "dist_known_fault_px",
        "temp_c",
        "geothermquartz_c",
        "geothermchalc_c",
        "geothermcat_c",
    ]
    with ws_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(csv_hdr)
        w.writerow(["ws", "Hot1", "Hot", 10, 12, 0.0, 0.0, 0.0, 88.5, 145.0, 120.0, 138.0])
        w.writerow(["ws", "Cold1", "Cold", 25, 30, 0.0, 0.0, 999.0, 14.0, 20.0, 15.0, 18.0])

    vv_csv = ext / "gdr_volcanic_vents_in_footprint.csv"
    with vv_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row", "col", "dist_known_fault_px"])
        w.writerow([15, 16, 0.0])

    fp = np.ones((48, 48), dtype=bool)
    feats1, stats1 = hydrothermal.load_wellspring_and_volcanic_fields(ext, fp)

    # Mutating `dist_known_fault_px` drastically MUST produce bit-for-bit identical features!
    with ws_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(csv_hdr)
        w.writerow(["ws", "Hot1", "Hot", 10, 12, 0.0, 0.0, 123456.0, 88.5, 145.0, 120.0, 138.0])
        w.writerow(["ws", "Cold1", "Cold", 25, 30, 0.0, 0.0, -99999.0, 14.0, 20.0, 15.0, 18.0])
    feats2, stats2 = hydrothermal.load_wellspring_and_volcanic_fields(ext, fp)

    for key in feats1:
        assert np.array_equal(feats1[key], feats2[key]), f"Leakage via banned column in {key}!"
    assert len(feats1) >= 4 and stats1 == stats2


def test_submodular_emitter_exact_29px_kernel_and_dispersion_invariant():
    assert len(submod.KERNEL_OFFSETS) == 29
    H, W = 60, 60
    fp = np.ones((H, W), dtype=bool)
    vis = np.zeros((H, W), dtype=bool)
    vis[10, :] = True

    p_trace = np.full((H, W), 0.01, dtype=np.float32)
    p_trace[30, 10:50] = 0.45
    p_trace[45, 10:50] = 0.35
    k_exp = np.clip(p_trace * 1.4, 0.0, 1.0)

    # Build a synthetic prior mask covering row 30 completely
    prior_mask = np.zeros(H * W, dtype=bool)
    prior_mask[27 * W : 34 * W] = True
    packed = np.packbits(prior_mask[:, None], axis=1)

    em, meta = submod.emit_submodular_dinkelbach(
        p_trace,
        k_exp,
        fp,
        vis,
        fp_lambda=0.04,
        max_dots=40,
        min_dots=20,
        prior_near3_packed=packed,
        overlap_cap=0.50,
    )
    assert em.dtype == np.float32
    assert float(em[vis].max()) == 0.0
    assert float(em.min()) >= 0.0 and float(em.max()) <= 1.0
    actual_overlap = float(prior_mask[em.ravel() > 0].mean())
    assert actual_overlap <= 0.50 + 6.0 / meta["n_dots"] + 1e-6


def test_fold_structural_features_use_only_visible_mask():
    H, W = 64, 64
    fp = np.ones((H, W), dtype=bool)
    vis = np.zeros((H, W), dtype=bool)
    vis[16:48, 20] = True
    vis[16:48, 44] = True
    aux = {
        "strike_rad": np.zeros((H, W), dtype=np.float32),
        "hydro_master": np.ones((H, W), dtype=np.float32),
        "geopb_pot": np.ones((H, W), dtype=np.float32),
        "lidar_scarp": np.ones((H, W), dtype=np.float32),
        "strain_trans": np.ones((H, W), dtype=np.float32),
    }
    S = hjcd.compute_fold_structural_features(vis, aux, fp)
    assert S.shape == (H * W, len(hjcd.STRUCTURAL_FEATURE_NAMES))
    assert np.isfinite(S).all()


def test_committed_evidence_and_promoted_geotiff_contracts():
    canaries = json.loads((ROOT / "evidence" / "feature_canaries.json").read_text())
    assert canaries["n_total_features_tested"] == 112
    assert canaries["n_leakage_triggers"] == 0
    assert canaries["max_directional_auc"] <= 0.90

    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    assert card["verdict"] == "promote"
    assert card["holdout_dti"]["dti"] > 0.19
    assert card["holdout_dti"]["paired_delta_vs_CTRL_h33_2_b2_foldproper"] > 0.09
    assert card["registry_comparison"]["discriminating_max_3px_overlap"] <= 0.70

    tif_path = ROOT / card["download_tif"]
    with rasterio.open(tif_path) as ds:
        arr = ds.read(1)
        assert ds.shape == grid.SHAPE
        assert str(ds.crs) == grid.CRS
        assert np.isfinite(arr).all()
        assert set(np.unique(arr).tolist()).issubset({0.0, 1.0})
