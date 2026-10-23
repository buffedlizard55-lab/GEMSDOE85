"""Unit tests: metric vs brute force, emitter support confinement, writer/validator round-trip."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems85 import emitter, metric  # noqa: E402
from gems85 import evaluate_holdout as EH  # noqa: E402


def test_metric_binary_matches_bruteforce():
    rng = np.random.default_rng(0)
    truth = np.zeros((40, 40), bool); truth[10:20, 12] = True; truth[30, 30] = True
    pred = np.zeros((40, 40), bool); pred[11:18, 13] = True; pred[5, 5] = True
    a = metric.dti_binary(pred, truth)
    b = metric.dti_bruteforce(pred.astype(float), truth)
    assert abs(a["dti"] - b["dti"]) < 1e-9


def test_credit_bar_algebra():
    # adding a dot with credit k improves DTI iff k > alpha * DTI
    assert abs(metric.marginal_inclusion_threshold(0.2778) - 0.2 * 0.2778) < 1e-12


def test_emitter_support_confined_and_budget():
    field = np.zeros((60, 60), np.float32)
    field[10:50:3, 10:50:3] = 1.0
    mask, log = emitter.emit(field, budget=50, prior_dti=0.0)
    assert mask.sum() <= 50
    assert (mask & (field <= 0)).sum() == 0  # support confinement


def test_holdout_pooled_is_between_cell_extremes():
    rng = np.random.default_rng(1)
    foot = np.ones((120, 120), bool)
    labels = np.zeros((120, 120), bool); labels[10:110:7, 60] = True; labels[20, 10:110:9] = True
    ho = EH.make_holdout(labels, foot)
    mask = labels.copy()
    r = EH.score_mask_pooled(mask, ho)
    cell_dtis = [c["dti"] for c in r["per_cell"].values()]
    assert min(cell_dtis) - 1e-9 <= r["pooled_dti"] <= max(cell_dtis) + 1e-9
    assert r["n_withheld_positives"] > 0
    assert r["ci95"][0] <= r["pooled_dti"] <= r["ci95"][1]


def test_writer_validator_roundtrip(tmp_path):
    import rasterio
    from gems85 import submission_writer as SW
    H, W = SW.EXPECTED_H, SW.EXPECTED_W
    # small synthetic sample is not the real grid; instead test validate() logic
    # on the real sample if present, else skip the grid-size assertions.
    sample = Path(__file__).resolve().parents[1] / "data" / "sample_submission.tif"
    if not sample.exists():
        return
    labels = np.zeros((H, W), bool)
    # IR-85-005 (defect in this test, not in the writer): the original block [100:200, 100:200]
    # lies entirely OUTSIDE the survey footprint -- 0 of its 10,000 cells are valid in
    # sample_submission.tif -- so the writer correctly zeroed every pixel and the test then
    # asserted 0 == 1156. Moved to an interior block (9,991/10,000 in-footprint) so the
    # round-trip actually exercises the writer.
    mask = np.zeros((H, W), bool); mask[1800:1900:3, 1600:1700:3] = True
    with rasterio.open(sample) as _s:                      # keep only in-footprint cells, so
        mask &= np.isfinite(_s.read(1))                    # positive_px == mask.sum() is exact
    audit = SW.write_pair(mask, labels, sample, tmp_path, "test-zeros.tif")
    assert audit["zeros"]["all_checks_passed"]
    assert audit["zeros"]["positive_px"] == int(mask.sum())
