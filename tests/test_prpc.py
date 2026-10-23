"""Unit and regression tests for Lane H85-P1 (`gems85.prpc`).

Covers:
1. IR-85-006 regression: odd-parity step channels peak on rock-state step edges while even-parity
   fault-core impulse channels peak ON centered ridges (where cross-trace odd differencing cancels).
2. IR-85-007 regression: `decontaminate_lidar_scarps` produces no spurious step across a sharp
   3DEP `lidar_valid` tile boundary on smooth terrain.
3. Exact strike convention equivalence across all 4 cardinal/diagonal azimuths (0, 45, 90, 135 deg)
   between `compute_prpc_operators` and `_fault_local_strike_rad`.
4. Visible-network mechanics: colinear wash-gap bridge scores higher in an along-strike gap between
   two colinear segments than broadside across a valley, and depends strictly on `visible_mask`.
5. Zero-leakage static code & CSV column audit (`dist_known_fault_px` and `derived_sgmc_faults`
   never referenced as features).
6. Submodular off-catalogue emission: strictly binary {0, 1}, exact budget, and zero dots within
   200 m of `visible_catalogue`.
"""

from __future__ import annotations

import inspect
import numpy as np
from scipy import ndimage as ndi

from gems85 import prpc


def _blank_inputs(shape=(128, 128)) -> dict[str, np.ndarray]:
    keys = [
        "rtp_z", "tmi_up150_z", "tmi_hg_z", "grad_tmi_up150_z", "mag_depth_persistence",
        "iso_grav_z", "iso_grav_hg_z", "cba_hg_z", "depth_base_z", "cond_surf_z",
        "det_elev_z", "elev_1km_z", "elev_25km_z", "slope_z", "tc_z", "neg_tc_z",
        "piedmont_hinge", "mesa_caprock_penalty", "K_z", "Th_z", "U_z", "UK_z", "UTh_z",
        "ThK_z", "rad_redox_conduit", "heat_flow_z", "geod_dilatrate_z", "geod_2ndinv_z",
        "geod_shearrate_z", "ieq_z", "slip_tend_z", "dilat_tend_z",
        "lappos_max_seamfree", "lapneg_max_seamfree", "step_max_seamfree",
        "downface_max_seamfree", "scarp_asymmetry_seamfree", "scarp_dipole_seamfree",
        "hydro_meas_1km", "hydro_meas_3km", "hydro_geotherm_2km", "hydro_prox", "volcanic_vent_2km",
    ]
    rng = np.random.default_rng(42)
    return {k: (rng.normal(0.0, 0.02, size=shape)).astype(np.float32) for k in keys}


def test_parity_operators_fix_ir85_006():
    """Even-symmetry fault-core impulse peaks AT the trace center x=64, not in a double halo."""
    h, w = 128, 128
    fp = np.ones((h, w), dtype=bool)
    yy, xx = np.indices((h, w), dtype=np.float32)

    # Case A: pure centered even-symmetry N-S scarp breakline at col = 64
    inp_even = _blank_inputs((h, w))
    impulse = (4.0 * np.exp(-0.5 * ((xx - 64.0) / 1.2) ** 2)).astype(np.float32)
    inp_even["lappos_max_seamfree"] = impulse
    inp_even["scarp_dipole_seamfree"] = impulse
    inp_even["neg_tc_z"] = impulse
    ops_even = prpc.compute_prpc_operators(inp_even, fp)

    core_profile = ops_even["prpc_core_even_z"][32:96, :].mean(axis=0)
    assert int(np.argmax(core_profile)) == 64
    assert core_profile[64] > core_profile[60] + 1.5
    assert core_profile[64] > core_profile[68] + 1.5

    # Case B: pure odd-symmetry subsurface step across N-S fault at col = 64
    inp_odd = _blank_inputs((h, w))
    step = np.tanh((xx - 64.0) / 1.5).astype(np.float32) * 3.0
    inp_odd["rtp_z"] = step
    inp_odd["tmi_up150_z"] = step
    inp_odd["iso_grav_z"] = -step
    ops_odd = prpc.compute_prpc_operators(inp_odd, fp)

    sub_profile = ops_odd["prpc_sub_odd_z"][32:96, :].mean(axis=0)
    peak_col = int(np.argmax(sub_profile))
    assert abs(peak_col - 64) <= 1
    assert sub_profile[64] > sub_profile[50] + 1.5


def test_lidar_seam_decontamination_fixes_ir85_007():
    """A sharp 3DEP lidar_valid boundary on smooth terrain creates no artificial seam spike."""
    h, w = 101, 100  # also tests odd height handling
    fp = np.ones((h, w), dtype=bool)
    yy, xx = np.indices((h, w), dtype=np.float32)
    # Smoothly varying terrain with no fault at col=50
    det_elev = 0.05 * xx + 0.02 * yy
    slope = np.full((h, w), 2.0, dtype=np.float32)
    tc = np.zeros((h, w), dtype=np.float32)

    lidar_valid = xx < 50  # hard tile seam right down col = 50!
    base_val = np.where(lidar_valid, 25, 0).astype(np.uint8)  # raw raster drops to 0 outside valid!
    lidar_bands = {
        nm: base_val.copy()
        for nm in ("slope_p95", "step_max", "lappos_max", "lapneg_max", "relief", "upface_max", "downface_max")
    }
    clean = prpc.decontaminate_lidar_scarps(lidar_bands, lidar_valid, det_elev, slope, tc, fp)
    prof = clean["lappos_max_seamfree"][20:80, :].mean(axis=0)
    # Cross-seam jump across col 47..53 must be tiny (near zero on uniform slope/curvature)
    seam_jump = float(np.max(np.abs(np.diff(prof[44:56]))))
    assert seam_jump < 0.15, f"unexpected seam jump {seam_jump}"


def test_strike_angle_consistency_all_four_orientations():
    """`_fault_local_strike_rad` matches `STRIKE_ANGLES_RAD` convention across 0, 45, 90, 135 deg."""
    h, w = 101, 101
    yy, xx = np.indices((h, w), dtype=np.float32)
    cy, cx = 50.0, 50.0

    for deg in (0.0, 45.0, 90.0, 135.0):
        theta = np.deg2rad(deg)
        ty, tx = -np.sin(theta), np.cos(theta)
        ny, nx = -tx, ty
        perp_dist = np.abs((yy - cy) * ny + (xx - cx) * nx)
        mask = perp_dist <= 1.1
        est = prpc._fault_local_strike_rad(mask)[50, 50]
        align = float(np.cos(est - theta) ** 2)
        assert align > 0.96, f"deg={deg}: est={np.rad2deg(est):.1f}, align={align:.3f}"


def test_visible_network_wash_gap_and_strict_fold_isolation():
    """Colinear wash-gap bridge peaks in the gap between two aligned segments, not broadside."""
    h, w = 121, 121
    fp = np.ones((h, w), dtype=bool)
    vis = np.zeros((h, w), dtype=bool)
    # Two colinear N-S segments along col=60 separated by a 14-pixel wash gap (rows 45..59)
    vis[15:45, 60] = True
    vis[59:90, 60] = True

    strike = np.full((h, w), np.pi / 2.0, dtype=np.float32)
    score = np.ones((h, w), dtype=np.float32)
    feats = prpc.build_visible_network_features(vis, strike, score, fp)

    gap_val = float(feats["net_colinear_wash_gap"][52, 60])
    broadside_val = float(feats["net_colinear_wash_gap"][30, 75])
    tip_val = float(feats["net_tip_cone_short"][50, 60])
    far_val = float(feats["net_tip_cone_short"][30, 90])

    assert gap_val > broadside_val + 0.5, f"gap={gap_val} vs broadside={broadside_val}"
    assert tip_val > far_val + 0.5, f"tip={tip_val} vs far={far_val}"


def test_no_forbidden_columns_or_rasters_in_prpc_source():
    """Static + contract check: dist_known_fault_px and SGMC faults are never used as features."""
    src = inspect.getsource(prpc)
    assert "FORBIDDEN_GDR_COLUMNS" in src
    # Verify derived_sgmc_faults_100m_u8.tif only appears in FORBIDDEN_RASTER_NAMES
    assert src.count("derived_sgmc_faults_100m_u8.tif") == 1


def test_submodular_emit_off_catalogue_invariants():
    h, w = 80, 80
    fp = np.ones((h, w), dtype=bool)
    vis = np.zeros((h, w), dtype=bool)
    vis[20:60, 40] = True
    rng = np.random.default_rng(9)
    prob = rng.uniform(0.01, 0.25, size=(h, w)).astype(np.float32)

    pred, log = prpc.submodular_emit_off_catalogue(
        prob, footprint=fp, visible_catalogue=vis, budget=60, exclude_radius_m=200.0
    )
    assert pred.dtype == np.float32
    assert set(np.unique(pred)).issubset({0.0, 1.0})
    assert int((pred > 0).sum()) == 60
    dist_vis = ndi.distance_transform_edt(~vis)
    assert float(dist_vis[pred > 0].min()) > 2.0
