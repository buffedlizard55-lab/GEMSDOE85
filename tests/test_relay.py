"""RELAY geometry: synthetic ground-truth tests (session arena/22847afd)."""
import numpy as np

from gems85 import relay


def test_extension_and_bridge_fill_gap():
    m = np.zeros((101, 201), bool)
    m[50, 10:60] = True
    m[50, 90:140] = True
    f = relay.relay_field(m, np.ones_like(m))
    assert f[50, 75] > 0           # relay gap centre is filled
    assert f[10, 75] == 0          # far from the network: nothing
    assert f[50, 150] > 0          # beyond the right tip: extension
    assert f[50, 30] == 0          # on the catalogue itself: zero by construction


def test_extension_is_along_strike_not_sideways():
    m = np.zeros((201, 101), bool)
    m[10:80, 50] = True
    f = relay.relay_field(m, np.ones_like(m))
    assert f[90, 50] > f[90, 60]   # continues the trace, does not bleed sideways


def test_empty_and_speck_catalogue():
    z = np.zeros((50, 50), bool)
    assert relay.relay_field(z, np.ones_like(z)).max() == 0
    m = np.zeros((50, 50), bool)
    m[25, 25] = True               # single pixel: below min_len, no tips
    assert relay.relay_field(m, np.ones_like(m)).max() == 0


def test_field_is_zero_outside_footprint():
    m = np.zeros((101, 201), bool)
    m[50, 10:60] = True
    fp = np.zeros_like(m)
    fp[:, :100] = True
    f = relay.relay_field(m, fp)
    assert f[:, 100:].max() == 0
