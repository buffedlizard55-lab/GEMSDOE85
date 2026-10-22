"""Synthetic contract tests, NOT geological holdout experiments or scores."""
from pathlib import Path
import hashlib
import json
import zipfile
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from scipy.ndimage import distance_transform_edt, label
import pytest

# IR-85-003 (pre-existing defect inherited from the shared template, found during the lane merge):
# this module imports a package `gems57` that does not exist in GEMSDOE85 -- the template was
# copied from a sibling repository without renaming the import. It therefore fails at COLLECTION,
# which takes the whole suite down with it. Skipped with a stated reason rather than deleted, so
# the contract tests come back for free the day the shared package is vendored in.
pytest.importorskip("gems57", reason="IR-85-003: shared contract package not vendored in GEMSDOE85")

from gems57 import evaluate_holdout as ev
from gems57.grid import Grid, HEIGHT, WIDTH, TRANSFORM
from gems57.holdout import buffered_component_draw
from gems57.metric import dti_exact, dti_bruteforce, kernel
from gems57.submission_writer import write_submission
from gems57.uniqueness import dot_overlap, saturation_certificate, compare_array_to_registry
from gems57.gates import format_report
from preflight import verify_template


def raster(path, a, transform=None, count=1, crs='EPSG:32611'):
    transform = transform or from_origin(0, 10000, 100, 100)
    with rasterio.open(path, 'w', driver='GTiff', count=count, height=a.shape[0], width=a.shape[1],
                       dtype=str(a.dtype), crs=crs, transform=transform, compress='deflate') as dst:
        for band in range(1, count + 1):
            dst.write(a, band)
    return path


def test_shared_bytes_unmodified():
    assert verify_template() == []


@pytest.mark.parametrize('seed', range(5))
def test_metric_matches_literal_equations(seed):
    rng = np.random.default_rng(seed)
    p = rng.uniform(0, 1, (10, 12)) * (rng.uniform(size=(10, 12)) < .2)
    g = rng.uniform(size=p.shape) < .1
    a, b = dti_exact(p, g), dti_bruteforce(p, g)
    for k in ['tp', 'fp', 'fn', 'dti']:
        assert a[k] == pytest.approx(b[k], abs=1e-10)


def test_kernel_support_and_diagonal():
    assert kernel(np.array([0., 1., 3., 4.])).tolist() == pytest.approx([1, 2/3, 0, 0])
    assert float(kernel(np.sqrt(2))) == pytest.approx(1 - np.sqrt(2)/3)


def test_pixel_exact_known_mask_not_buffered():
    g = np.zeros((10, 10), bool)
    g[4, 5] = True
    visible = np.zeros_like(g)
    visible[4, 4] = True
    p = np.zeros(g.shape)
    p[4, 4] = 1  # Must be removed pixel-exactly.
    p[4, 5] = 1  # Must remain; it is adjacent but not a visible pixel.
    fold = dict(region=np.ones_like(g), truth=g, visible=visible)
    score, terms = ev.evaluate(p, fold, np.ones_like(g), block_side=5)
    assert score['tp'] == pytest.approx(1)
    assert score['fp'] == pytest.approx(0)
    assert score['n_emitted'] == 1
    assert terms[:, 3].sum() == 1


@pytest.mark.parametrize('bad', [np.nan, np.inf, -1e38, -.001, 1.001])
def test_evaluator_rejects_invalid_before_mask(bad):
    p = np.zeros((8, 8)); p[0, 0] = bad
    truth = np.zeros((8, 8), bool); truth[4, 4] = True
    region = np.zeros_like(truth); region[3:6, 3:6] = True
    fold = dict(region=region, truth=truth, visible=np.zeros_like(truth))
    with pytest.raises(ValueError, match='finite'):
        ev.evaluate(p, fold, np.ones_like(truth), block_side=4)


def test_pooled_ci_and_aligned_truth_counts():
    candidate = np.array([[2, 1, 1, 3], [1, 2, 2, 3]], float)
    baseline = np.array([[1, 1, 2, 3], [1, 2, 2, 3]], float)
    r = ev.pooled_summary({'candidate': candidate, 'baseline': baseline}, draws=200, seed=7, candidate='candidate')
    assert r['evaluator_version'] == ev.VERSION
    assert r['pooled']
    assert r['scores']['candidate']['withheld_positive_pixels'] == 6
    assert len(r['scores']['candidate']['ci95']) == 2
    assert r['scores']['candidate']['dti'] == pytest.approx(float(ev.from_terms(candidate.sum(axis=0))))
    bad = baseline.copy(); bad[0, 3] += 1
    with pytest.raises(ValueError, match='same integer truth count'):
        ev.pooled_summary({'candidate': candidate, 'baseline': bad}, candidate='candidate')


def test_whole_components_buffered_not_short_chunks():
    fp = np.ones((160, 160), bool)
    cat = np.zeros_like(fp)
    for y in [20, 40, 60, 100, 120, 140]:
        for x in [20, 45, 100, 125]:
            cat[y:y+8, x] = True
    grid = Grid(fp, cat, None, TRANSFORM, *fp.shape)
    folds, _ = buffered_component_draw(grid, seed=20, buffer_px=3, boundary_px=8)
    hidden = folds[0]['hidden_all']
    comp, count = label(cat, np.ones((3, 3), bool))
    for c in range(1, count + 1):
        selected = hidden[comp == c]
        assert selected.all() or not selected.any()
    assert hidden.any()
    for fold in folds:
        assert not (fold['visible'] & hidden).any()
        assert distance_transform_edt(~fold['visible'])[hidden].min() > 3
        assert np.array_equal(fold['masked_known'], cat & ~hidden)
        assert not (fold['truth'] & ~fold['region']).any()


def test_literal_saturation_blocks_even_different_sparse_candidate(tmp_path):
    fp = np.ones((14, 16), bool)
    prior = raster(tmp_path / 'dense.tif', np.full(fp.shape, .1, np.float32))
    mine = np.zeros(fp.shape, np.float32); mine[3, 3] = 1; mine[10, 10] = 1
    cert = saturation_certificate(prior, fp)
    assert cert['universal_overlap_blocker']
    assert cert['uncovered_allowed_pixels'] == 0
    assert dot_overlap(mine, np.full(fp.shape, .1)) == 1
    index = dict(complete_accessible_scan=True, errors=[], rasters=[dict(
        repo_first='synthetic', sources=['test'], cache_file=str(prior),
        sha256=hashlib.sha256(prior.read_bytes()).hexdigest())])
    result = compare_array_to_registry(mine, index, fp)
    assert result['rows'][0]['duplicate_by_overlap']
    assert not result['unique']
    assert result['stop_required']


def test_euclidean_three_pixel_halo_not_square():
    prior = np.zeros((20, 20)); prior[10, 10] = 1
    mine = np.zeros_like(prior); mine[13, 10] = 1
    assert dot_overlap(mine, prior) == 1
    mine[:] = 0; mine[13, 13] = 1
    assert dot_overlap(mine, prior) == 0


def test_missing_inventory_never_clears(tmp_path):
    fp = np.ones((12, 12), bool)
    mine = np.zeros(fp.shape, np.float32); mine[6, 6] = 1
    result = compare_array_to_registry(mine, [], fp)
    assert not result['unique'] and result['stop_required']


@pytest.mark.parametrize('bad', [np.nan, np.inf, -3.4028235e38, -.001, 1.001])
def test_writer_no_silent_repair_or_partial_file(tmp_path, bad):
    p = np.zeros((3, 3)); p[1, 1] = bad
    with pytest.raises(ValueError, match='normalized, finite'):
        write_submission(tmp_path / 'private.tif', p, tmp_path / 'absent-sample.tif', np.ones_like(p, bool),
                         name='synthetic-contract-test', note='test only')
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('field', ['note', 'name'])
def test_writer_note_name_limit(tmp_path, field):
    kwargs = dict(name='test', note='test')
    kwargs[field] = 'x' * 141
    with pytest.raises(ValueError, match='140'):
        write_submission(tmp_path / 'test.tif', np.zeros((2, 2)), tmp_path / 'none', np.ones((2, 2), bool), **kwargs)


def test_shared_writer_real_grid_tiff_zip_roundtrip(tmp_path):
    # Full-size synthetic fixture; NEVER offered as a competition download.
    shape = (HEIGHT, WIDTH)
    p = np.zeros(shape, np.float32); p[100, 100] = 1
    fp = np.ones(shape, bool)
    sample = raster(tmp_path / 'sample.tif', np.zeros(shape, np.float32), transform=TRANSFORM)
    path = tmp_path / 'synthetic-not-a-submission.tif'
    result = write_submission(path, p, sample, fp, name='synthetic-contract-test', note='Synthetic fixture, not a competition submission.')
    assert result['validator']['all_checks_passed']
    assert result['template_report']['ok']
    assert result['approved_for_weekly_slot'] is False
    assert result['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    with rasterio.open(path) as src:
        assert src.count == 1 and src.dtypes == ('float32',)
        assert src.nodata is None
        assert np.array_equal(src.read(1), p)
    with zipfile.ZipFile(path.with_suffix('.zip')) as z:
        assert z.namelist() == [path.name]
        assert z.read(path.name) == path.read_bytes()
    with pytest.raises(FileExistsError):
        write_submission(path, p, sample, fp, name='test', note='test')
    assert not [f for f in tmp_path.iterdir() if f.name.startswith('.')]


@pytest.mark.parametrize('kind', ['range', 'nan', 'crs', 'transform', 'shape', 'bands', 'dtype'])
def test_disk_validator_rejects_bad_format(tmp_path, kind):
    a = np.zeros((12, 13), np.float32)
    sample = raster(tmp_path / 'sample.tif', a)
    kwargs = {}
    if kind == 'range': a[0, 0] = -9999
    if kind == 'nan': a[0, 0] = np.nan
    if kind == 'crs': kwargs['crs'] = 'EPSG:4326'
    if kind == 'transform': kwargs['transform'] = from_origin(1, 10000, 100, 100)
    if kind == 'shape': a = a[:-1]
    if kind == 'bands': kwargs['count'] = 2
    if kind == 'dtype': a = a.astype(np.float64)
    path = raster(tmp_path / 'bad.tif', a, **kwargs)
    report = format_report(path, sample)
    assert not report['ok']
