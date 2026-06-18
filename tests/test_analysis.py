import pandas as pd

from notebooks.ab_test_analysis import compute_confidence_interval, compute_z_test


def test_compute_confidence_interval():
    lower, upper = compute_confidence_interval(20, 100)
    assert 0.0 < lower < upper < 1.0


def test_compute_z_test():
    stat, p_value = compute_z_test(20, 100, 30, 100)
    assert p_value >= 0.0 and p_value <= 1.0
    assert isinstance(stat, float)
