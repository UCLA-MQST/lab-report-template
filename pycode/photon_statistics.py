#!/usr/bin/env python3
"""
photon_statistics.py — General-purpose photon-statistics simulation and CHSH analysis.

Provides reusable functions for:
  1. Poissonian photon-beam simulation
  2. g^(2)(0) evaluation (second-order coherence)
  3. Polarization-correlation functions for Bell states
  4. CHSH E-correlation and S-parameter computation

These routines are independent of any specific lab configuration.
Import what you need, or run this file as a script for a self-test.

Example usage:
    from pycode.photon_statistics import generate_photon_beam, compute_g2_zero
    beam = generate_photon_beam(flux=1e4, dt=1e-6, T_run=1.0, seed=42)
    g2   = compute_g2_zero(beam)
"""

from __future__ import annotations
import numpy as np
from typing import Optional
from scipy.stats import poisson as scipy_poisson


# ---------------------------------------------------------------------------
# 1. Photon-beam simulation
# ---------------------------------------------------------------------------

def generate_photon_beam(
    flux: float,
    dt: float,
    T_run: float,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Simulate a Poissonian photon beam as an array of counts per time-bin.

    Parameters
    ----------
    flux  : mean photon rate (photons / s)
    dt    : time-bin width (s); should satisfy flux * dt << 1 for single-photon regime
    T_run : total acquisition time (s)
    seed  : optional random seed for reproducibility

    Returns
    -------
    counts : ndarray of length int(T_run / dt)
    """
    rng    = np.random.default_rng(seed)
    n_bins = int(T_run / dt)
    mu     = flux * dt           # mean photons per bin
    return rng.poisson(mu, size=n_bins)


def boxcar_rebin(counts: np.ndarray, bin_factor: int) -> np.ndarray:
    """
    Rebin an array of counts by summing consecutive *bin_factor* bins.
    Simulates a longer integration time: dt_new = dt * bin_factor.
    """
    n = len(counts) // bin_factor * bin_factor
    return counts[:n].reshape(-1, bin_factor).sum(axis=1)


# ---------------------------------------------------------------------------
# 2. Second-order coherence g^(2)(0)
# ---------------------------------------------------------------------------

def compute_g2_zero(counts: np.ndarray) -> float:
    """
    Compute g^(2)(0) = <n(n-1)> / <n>^2 from an array of per-bin coincidence counts.

    Interpretations:
        g^(2)(0) == 1  : Poissonian / coherent source
        g^(2)(0) >  1  : super-Poissonian / bunched (thermal SPDC)
        g^(2)(0) <  1  : sub-Poissonian / anti-bunched (single photon)
    """
    n_mean = counts.mean()
    if n_mean == 0:
        return float("nan")
    return (counts * (counts - 1)).mean() / n_mean ** 2


def g2_distribution(
    flux: float,
    dt: float,
    T_run: float,
    n_trials: int = 500,
    bin_factor: int = 1,
    seed: int = 0,
) -> np.ndarray:
    """
    Run *n_trials* independent simulations and return g^(2)(0) for each.
    Useful for visualizing the statistical spread of g^(2)(0) estimators.
    """
    g2_values = np.zeros(n_trials)
    for i in range(n_trials):
        beam = generate_photon_beam(flux, dt, T_run, seed=seed + i)
        if bin_factor > 1:
            beam = boxcar_rebin(beam, bin_factor)
        g2_values[i] = compute_g2_zero(beam)
    return g2_values


# ---------------------------------------------------------------------------
# 3. Polarization-correlation functions for maximally entangled Bell states
# ---------------------------------------------------------------------------

def E_bell(alpha: float, beta: float,
           state: str = "singlet") -> float:
    """
    Theoretical correlation function E(alpha, beta) for a maximally entangled
    two-photon polarization state.

    Parameters
    ----------
    alpha, beta : polarizer angles (radians)
    state       : one of "singlet" (|Ψ⁻⟩), "triplet_plus"  (|Ψ⁺⟩),
                         "phi_plus" (|Φ⁺⟩), "phi_minus" (|Φ⁻⟩)

    Returns
    -------
    E : float in [-1, 1]
    """
    match state:
        case "singlet"      : return -np.cos(2 * (alpha - beta))
        case "triplet_plus" : return  np.cos(2 * (alpha - beta))
        case "phi_minus"    : return  np.cos(2 * (alpha + beta))
        case "phi_plus"     : return -np.cos(2 * (alpha + beta))
        case _:
            raise ValueError(f"Unknown state '{state}'. "
                             "Choose from: singlet, triplet_plus, phi_plus, phi_minus")


# ---------------------------------------------------------------------------
# 4. CHSH S-parameter from coincidence data
# ---------------------------------------------------------------------------

def compute_E_from_data(
    data: dict,
    a_deg: float,
    b_deg: float,
    subtract_accidentals: bool = False,
) -> tuple[float, float]:
    """
    Compute E(a, b) from a coincidence-count dictionary.

    The dictionary must be keyed by (alpha_deg, beta_deg) tuples and each
    value must contain at least a 'N' key (coincidences) and optionally
    'N_acc' (accidentals).

    Returns (E, delta_E) — value and Poissonian propagated uncertainty.
    """
    a_perp = (a_deg + 90) % 360
    b_perp = (b_deg + 90) % 360

    def get_N(alpha: float, beta: float) -> float:
        d = data.get((alpha, beta), {"N": 0, "N_acc": 0})
        return d["N"] - d.get("N_acc", 0) if subtract_accidentals else d["N"]

    N_pp = get_N(a_deg,  b_deg)
    N_mm = get_N(a_perp, b_perp)
    N_pm = get_N(a_deg,  b_perp)
    N_mp = get_N(a_perp, b_deg)

    den = N_pp + N_mm + N_pm + N_mp
    if den == 0:
        return float("nan"), float("nan")
    E     = (N_pp + N_mm - N_pm - N_mp) / den
    dE    = np.sqrt((1 - E ** 2) / den) if abs(E) < 1 else 0.0
    return float(E), float(dE)


def compute_CHSH_S(
    data: dict,
    a: float,
    a_prime: float,
    b: float,
    b_prime: float,
    subtract_acc: bool = False,
) -> tuple[float, float]:
    """
    Compute CHSH parameter S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
    and its quadrature-propagated uncertainty delta_S.

    All angles in degrees.  Returns (S, delta_S).
    """
    (E_ab,   dE_ab)   = compute_E_from_data(data, a,       b,       subtract_acc)
    (E_abp,  dE_abp)  = compute_E_from_data(data, a,       b_prime, subtract_acc)
    (E_apb,  dE_apb)  = compute_E_from_data(data, a_prime, b,       subtract_acc)
    (E_apbp, dE_apbp) = compute_E_from_data(data, a_prime, b_prime, subtract_acc)

    S        = E_ab - E_abp + E_apb + E_apbp
    delta_S  = float(np.sqrt(dE_ab**2 + dE_abp**2 + dE_apb**2 + dE_apbp**2))
    return float(S), delta_S


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    beam = generate_photon_beam(flux=1e4, dt=1e-6, T_run=1.0, seed=42)
    print(f"Beam: {len(beam):,} bins, total counts = {beam.sum():,}")
    print(f"g^(2)(0) = {compute_g2_zero(beam):.6f}  (expect ≈ 1.0 for Poisson)")

    alpha, beta = np.pi / 4, -np.pi / 8
    for state in ("singlet", "triplet_plus", "phi_plus", "phi_minus"):
        E = E_bell(alpha, beta, state=state)
        print(f"E({np.degrees(alpha):.0f}°, {np.degrees(beta):.0f}°)  [{state}] = {E:.4f}")
