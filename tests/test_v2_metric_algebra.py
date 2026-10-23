"""v2 algebra regression against the existing metric, not a new evaluator."""
import numpy as np
import pytest
from gems85.metric import dti, kernel_dilate


@pytest.mark.parametrize('geometry', ['isolated', 'line', 'random', 'empty'])
@pytest.mark.parametrize('binary', [False, True])
def test_reduced_dti_identity(geometry, binary):
    rng = np.random.default_rng(306)
    g = np.zeros((17, 19), dtype=bool)
    if geometry == 'isolated':
        g[8, 9] = True
    elif geometry == 'line':
        g[2:15, 9] = True
    elif geometry == 'random':
        g = rng.random(g.shape) < 0.1
    p = rng.random(g.shape)
    p = (p > .7).astype(float) if binary else np.where(p > .7, p, 0.)
    result = dti(p, g)
    T = kernel_dilate(p)[g].sum()
    S = p.sum()
    M = (p * kernel_dilate(g.astype(float))).sum()
    denominator = .2*T + .2*(S-M) + .8*g.sum()
    reduced = T / denominator if denominator else 0.
    assert result.dti == pytest.approx(reduced, abs=1e-12)
