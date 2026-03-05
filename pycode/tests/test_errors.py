"""
tests/test_errors.py — Unit tests for pycode/errors.py
"""
import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pycode.errors import (
    count_uncertainty,
    rate_uncertainty,
    angle_uncertainty,
    chi_squared,
    chi_squared_report,
    visibility_uncertainty,
    E_uncertainty,
    accidental_rate,
    accidental_rate_uncertainty,
    combined_uncertainty,
    rel_quad,
    abs_quad,
)


class TestCountUncertainty:
    def test_sqrt(self):
        assert count_uncertainty(100.0) == pytest.approx(10.0)

    def test_floor(self):
        # counts below minimum should return sqrt(minimum)
        assert count_uncertainty(0.0) == pytest.approx(1.0)
        assert count_uncertainty(-5.0) == pytest.approx(1.0)

    def test_array(self):
        result = count_uncertainty(np.array([1.0, 4.0, 9.0, 0.0]))
        np.testing.assert_allclose(result, [1.0, 2.0, 3.0, 1.0])


class TestRateUncertainty:
    def test_basic(self):
        # sigma_R = sqrt(N) / T
        assert rate_uncertainty(100.0, 10.0) == pytest.approx(1.0)

    def test_zero_counts(self):
        # floor at 1 → sigma_R = 1/T
        assert rate_uncertainty(0.0, 5.0) == pytest.approx(0.2)


class TestAngleUncertainty:
    def test_on_minor_tick(self):
        # 45.0° is on a 5° minor tick → delta = 5/2 = 2.5°
        assert angle_uncertainty(45.0) == pytest.approx(2.5)

    def test_between_ticks(self):
        # 22.5° is NOT on a 5° tick → delta = 5/4 = 1.25°
        assert angle_uncertainty(22.5) == pytest.approx(1.25)

    def test_zero_on_tick(self):
        assert angle_uncertainty(0.0) == pytest.approx(2.5)

    def test_custom_tick(self):
        # minor_tick_deg=2 → on tick: 1°, between: 0.5°
        assert angle_uncertainty(10.0, minor_tick_deg=2.0) == pytest.approx(1.0)
        assert angle_uncertainty(11.0, minor_tick_deg=2.0) == pytest.approx(0.5)

    def test_array_input(self):
        result = angle_uncertainty(np.array([0.0, 22.5, 45.0]))
        assert result[0] == pytest.approx(2.5)   # on tick
        assert result[1] == pytest.approx(1.25)  # between
        assert result[2] == pytest.approx(2.5)   # on tick


class TestChiSquared:
    def test_perfect_fit(self):
        obs = np.array([100.0, 200.0, 150.0])
        res = chi_squared(obs, obs.copy(), n_params=0)
        assert res["chi2"] == pytest.approx(0.0, abs=1e-10)
        assert res["chi2_red"] == pytest.approx(0.0, abs=1e-10)

    def test_dof(self):
        obs = np.ones(10)
        res = chi_squared(obs, obs, n_params=2)
        assert res["dof"] == 7   # 10 - 1 - 2

    def test_interpretation_good(self):
        rng = np.random.default_rng(42)
        obs = rng.poisson(100, size=50).astype(float)
        res = chi_squared(obs, np.full(50, 100.0), n_params=0)
        assert "good" in res["interpretation"] or "marginal" in res["interpretation"]

    def test_custom_errors(self):
        obs    = np.array([10.0, 20.0, 30.0])
        exp    = np.array([10.0, 20.0, 30.0])
        sigmas = np.array([1.0, 2.0, 3.0])
        res = chi_squared(obs, exp, observed_err=sigmas)
        assert res["chi2"] == pytest.approx(0.0, abs=1e-10)


class TestVisibilityUncertainty:
    def test_perfect(self):
        # Nmax >> Nmin → V ≈ 1
        V, dV = visibility_uncertainty(1000.0, 0.001)
        assert V == pytest.approx(1.0, abs=0.01)

    def test_zero_visibility(self):
        V, dV = visibility_uncertainty(100.0, 100.0)
        assert V == pytest.approx(0.0, abs=1e-10)

    def test_array(self):
        Nmax = np.array([100.0, 200.0])
        Nmin = np.array([0.0,   200.0])
        V, dV = visibility_uncertainty(Nmax, Nmin)
        assert V[1] == pytest.approx(0.0, abs=1e-10)


class TestEUncertainty:
    def test_zero_counts(self):
        E, dE = E_uncertainty(0, 0, 0, 0)
        assert np.isnan(E) and np.isnan(dE)

    def test_known_value(self):
        # Symmetric: Npp=Nmm=500, Npm=Nmp=50
        E, dE = E_uncertainty(500, 50, 50, 500)
        expected_E = (500 + 500 - 50 - 50) / (500 + 50 + 50 + 500)
        assert E == pytest.approx(expected_E, rel=1e-6)
        assert dE > 0


class TestAccidentalRate:
    def test_basic(self):
        assert accidental_rate(1000, 2000, 1e-9) == pytest.approx(2e-3)

    def test_uncertainty_larger_with_window_error(self):
        du_no_window = accidental_rate_uncertainty(1000, 2000, 10, 20, 1e-9, 0)
        du_with_window = accidental_rate_uncertainty(1000, 2000, 10, 20, 1e-9, 1e-10)
        assert du_with_window > du_no_window


class TestQuadrature:
    def test_rel_quad_single(self):
        # delta_f/f = dx/x for one term
        assert rel_quad((10.0, 1.0)) == pytest.approx(0.1)

    def test_abs_quad_two(self):
        # sqrt(3^2 + 4^2) = 5
        assert abs_quad(3.0, 4.0) == pytest.approx(5.0)
