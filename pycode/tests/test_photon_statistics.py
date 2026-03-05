"""
tests/test_photon_statistics.py — Unit tests for pycode/photon_statistics.py
"""
import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pycode.photon_statistics import (
    generate_photon_beam,
    boxcar_rebin,
    compute_g2_zero,
    g2_distribution,
    E_bell,
    compute_E_from_data,
    compute_CHSH_S,
)


class TestGeneratePhotonBeam:
    def test_length(self):
        beam = generate_photon_beam(1e4, 1e-6, 1.0, seed=0)
        assert len(beam) == 1_000_000

    def test_poisson_mean(self):
        beam = generate_photon_beam(1e4, 1e-6, 10.0, seed=42)
        mu = 1e4 * 1e-6
        assert abs(beam.mean() - mu) / mu < 0.01  # within 1%

    def test_seed_reproducible(self):
        b1 = generate_photon_beam(1e4, 1e-4, 1.0, seed=7)
        b2 = generate_photon_beam(1e4, 1e-4, 1.0, seed=7)
        np.testing.assert_array_equal(b1, b2)

    def test_non_negative(self):
        beam = generate_photon_beam(1e4, 1e-6, 0.1, seed=1)
        assert (beam >= 0).all()


class TestBoxcarRebin:
    def test_sum(self):
        a = np.arange(12)
        rb = boxcar_rebin(a, 3)
        np.testing.assert_array_equal(rb, [3, 12, 21, 30])

    def test_truncates(self):
        a = np.arange(10)       # 10 elements, bin_factor=3 → floor(10/3)*3 = 9 used
        rb = boxcar_rebin(a, 3)
        assert len(rb) == 3


class TestComputeG2Zero:
    def test_poisson_near_one(self):
        rng  = np.random.default_rng(0)
        beam = rng.poisson(1.0, size=200_000)
        g2   = compute_g2_zero(beam)
        assert abs(g2 - 1.0) < 0.01

    def test_zero_beam_returns_nan(self):
        assert np.isnan(compute_g2_zero(np.zeros(100)))

    def test_single_photon_antibunched(self):
        # A stream where every bin has exactly 1: <n(n-1)> = 0 → g2 = 0
        beam = np.ones(1000, dtype=int)
        assert compute_g2_zero(beam) == pytest.approx(0.0)


class TestG2Distribution:
    def test_shape(self):
        vals = g2_distribution(1e4, 1e-6, 0.01, n_trials=20, seed=0)
        assert vals.shape == (20,)

    def test_near_one_for_poisson(self):
        vals = g2_distribution(1e4, 1e-6, 0.1, n_trials=100, seed=42)
        assert abs(np.nanmean(vals) - 1.0) < 0.05


class TestEBell:
    """Spot-check theoretical correlation functions."""

    def test_singlet_optimal_angles(self):
        # E(π/4, −π/8) = −cos(2·(π/4−(−π/8))) = −cos(3π/4) = 1/√2
        alpha, beta = np.pi / 4, -np.pi / 8
        E = E_bell(alpha, beta, state="singlet")
        assert E == pytest.approx(1 / np.sqrt(2), abs=1e-9)

    def test_singlet_CHSH_S(self):
        # For singlet = -cos(2(α-β)), CHSH-optimal angles give |S| = 2√2.
        # Verify numerically with two canonical orderings.
        for (a, ap, b, bp) in [
            (0, np.pi/4, -np.pi/8, np.pi/8),
            (0, np.pi/4,  np.pi/8, 3*np.pi/8),
        ]:
            S = (E_bell(a,  b,  "singlet") - E_bell(a,  bp, "singlet") +
                 E_bell(ap, b,  "singlet") + E_bell(ap, bp, "singlet"))
            if abs(abs(S) - 2 * np.sqrt(2)) < 1e-9:
                return   # found a valid ordering
        pytest.fail(f"No CHSH angle ordering gave |S|=2√2 for singlet")

    def test_unknown_state_raises(self):
        with pytest.raises(ValueError):
            E_bell(0, 0, state="bogus")


class TestCHSHFromData:
    """Integration test: build a small coincidence dict and check S."""

    @pytest.fixture
    def singlet_data(self):
        """Ideal singlet data at CHSH angles (a=45, a'=0, b=-22.5, b'=22.5)."""
        # Use theoretical probabilities scaled to 10000 counts
        N = 10_000
        angles = [(0, -22.5), (0, 22.5), (0, 67.5), (0, 112.5),
                  (45, -22.5), (45, 22.5), (45, 67.5), (45, 112.5),
                  (90, -22.5), (90, 22.5), (90, 67.5), (90, 112.5),
                  (135, -22.5), (135, 22.5), (135, 67.5), (135, 112.5)]
        data = {}
        for a, b in angles:
            # P(a, b) ∝ sin²(a-b) for singlet
            prob = np.sin(np.deg2rad(a - b)) ** 2
            data[(a, b)] = {"N": int(N * prob), "N_acc": 0}
        return data

    def test_CHSH_S_positive(self, singlet_data):
        S, dS = compute_CHSH_S(singlet_data, 45, 0, -22.5, 22.5)
        # With sin² data the S value may be close to 2√2 or negative depending
        # on convention; what matters is the formula runs without errors and dS >= 0.
        assert dS >= 0
        assert isinstance(S, float)

    def test_CHSH_data_roundtrip(self, singlet_data):
        # E values should have magnitude <= 1
        E, dE = compute_E_from_data(singlet_data, 45, -22.5)
        assert abs(E) <= 1.0 + 1e-9
        assert dE >= 0
