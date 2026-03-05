#!/usr/bin/env python3
"""
errors.py — General-purpose uncertainty and error analysis library.

Designed for optics / quantum-photonics lab reports but applicable broadly.
Import this module from analysis scripts for consistent error propagation.

Provides:
  1. Poissonian counting uncertainty: sigma_N = sqrt(N)
  2. Instrument angle readout uncertainty (generalized, configurable)
  3. Rate uncertainty: sigma_R = sigma_N / T
  4. Quadrature propagation helpers (relative and absolute)
  5. Chi-squared goodness-of-fit with p-value and interpretation
  6. Visibility and correlation (CHSH E-value) uncertainties
  7. Coincidence-window and efficiency uncertainty helpers

Usage example:
    from pycode.errors import count_uncertainty, chi_squared, chi_squared_report
    sigma_N = count_uncertainty(N)
    result  = chi_squared(observed, expected, n_params=3)
    print(chi_squared_report(result, label=\"fringe fit\"))
"""

from __future__ import annotations
import numpy as np
from scipy import stats as scipy_stats


# ---------------------------------------------------------------------------
# 1. Poissonian counting uncertainty
# ---------------------------------------------------------------------------

def count_uncertainty(N: float | np.ndarray,
                      minimum: float = 1.0) -> float | np.ndarray:
    """
    Poissonian photon-counting standard deviation: sigma_N = sqrt(max(N, minimum)).

    Parameters
    ----------
    N       : raw photon count(s)
    minimum : floor value for N before sqrt (default 1.0, avoids sigma=0)
    """
    return np.sqrt(np.maximum(N, minimum))


def rate_uncertainty(N: float | np.ndarray,
                     T: float | np.ndarray) -> float | np.ndarray:
    """Uncertainty on rate R = N/T: sigma_R = sqrt(N) / T."""
    return count_uncertainty(N) / T


def combined_uncertainty(N1: float | np.ndarray,
                         N2: float | np.ndarray) -> float | np.ndarray:
    """sqrt-quadrature uncertainty for a sum or difference: sqrt(N1 + N2)."""
    return np.sqrt(np.maximum(N1, 1.0) + np.maximum(N2, 1.0))


# ---------------------------------------------------------------------------
# 2. Angle readout uncertainty (fully configurable)
# ---------------------------------------------------------------------------

def angle_uncertainty(
    theta_deg: float | np.ndarray,
    major_tick_deg: float = 10.0,
    minor_tick_deg: float = 5.0,
) -> float | np.ndarray:
    """
    Return the readout uncertainty Δθ for a polarizer / wave-plate angle.

    Default settings match the quED analyzer dial (major ticks every 10°,
    minor ticks every 5°):
      - Angle falls on a minor tick (multiple of minor_tick_deg) → ±minor_tick_deg/2
      - Angle is read between marks → ±minor_tick_deg/4

    Parameters
    ----------
    theta_deg      : angle value(s) in degrees
    major_tick_deg : spacing of major graduations (default 10°)
    minor_tick_deg : spacing of minor graduations (default 5°)
    """
    theta = np.asarray(theta_deg, dtype=float)
    # Check if the angle is exactly on a minor division
    on_tick = np.isclose((theta % minor_tick_deg), 0, atol=1e-9) | \
              np.isclose((theta % minor_tick_deg), minor_tick_deg, atol=1e-9)
    delta = np.where(on_tick, minor_tick_deg / 2.0, minor_tick_deg / 4.0)
    if np.ndim(theta) == 0:
        return float(delta)
    return delta


def angle_uncertainty_rad(theta_deg: float | np.ndarray,
                          **kw) -> float | np.ndarray:
    """Return angle uncertainty in radians. Accepts same kwargs as angle_uncertainty."""
    return np.deg2rad(angle_uncertainty(theta_deg, **kw))


# ---------------------------------------------------------------------------
# 3. Quadrature propagation helpers
# ---------------------------------------------------------------------------

def rel_quad(*args: tuple[float | np.ndarray, float | np.ndarray]
             ) -> float | np.ndarray:
    """
    Relative quadrature uncertainty for f = x1^a1 * x2^a2 * ...

    Each argument is a (x, dx) pair. Returns delta_f/f = sqrt(sum (dx_i/x_i)^2).
    """
    return np.sqrt(sum((dx / np.maximum(np.abs(x), 1e-30)) ** 2
                       for x, dx in args))


def abs_quad(*args: float | np.ndarray) -> float | np.ndarray:
    """
    Absolute quadrature uncertainty for f = sum a_i * x_i.

    Each argument is an already-scaled partial contribution: c_i * delta_x_i.
    Returns delta_f = sqrt(sum a_i^2).
    """
    return np.sqrt(sum(np.asarray(a) ** 2 for a in args))


# ---------------------------------------------------------------------------
# 4. Chi-squared goodness-of-fit
# ---------------------------------------------------------------------------

def chi_squared(
    observed: np.ndarray,
    expected: np.ndarray,
    observed_err: np.ndarray | None = None,
    *,
    n_params: int = 0,
) -> dict:
    """
    Compute chi-squared goodness-of-fit.

    Parameters
    ----------
    observed     : measured values
    expected     : model values (same shape)
    observed_err : uncertainties; if None, uses sqrt(|observed|)
    n_params     : number of free parameters in the model

    Returns
    -------
    dict with: chi2, dof, chi2_red, p_value, residuals, interpretation
    """
    obs = np.asarray(observed, dtype=float)
    exp = np.asarray(expected, dtype=float)
    sigma = (np.sqrt(np.maximum(np.abs(obs), 1.0))
             if observed_err is None
             else np.where(np.asarray(observed_err) > 0,
                           np.asarray(observed_err, dtype=float), 1.0))
    residuals = (obs - exp) / sigma
    chi2      = float(np.sum(residuals ** 2))
    n         = len(obs)
    dof       = max(n - 1 - n_params, 1)
    chi2_red  = chi2 / dof
    p_value   = float(1.0 - scipy_stats.chi2.cdf(chi2, df=dof))

    if chi2_red < 0.5:
        interp = "overfit (chi2_red << 1)"
    elif chi2_red < 2.0:
        interp = "good fit (0.5 ≤ chi2_red < 2)"
    elif chi2_red < 5.0:
        interp = "marginal (chi2_red 2–5)"
    else:
        interp = "poor fit (chi2_red >> 1)"

    return dict(chi2=chi2, dof=dof, chi2_red=chi2_red,
                p_value=p_value, residuals=residuals,
                interpretation=interp)


def chi_squared_report(result: dict, label: str = "") -> str:
    """Format a chi_squared() result as a human-readable string."""
    prefix = f"[{label}] " if label else ""
    return (f"{prefix}chi2={result['chi2']:.3f}, "
            f"dof={result['dof']}, "
            f"chi2_red={result['chi2_red']:.3f}, "
            f"p={result['p_value']:.4f}  → {result['interpretation']}")


# ---------------------------------------------------------------------------
# 5. Physics-specific helpers
# ---------------------------------------------------------------------------

def visibility_uncertainty(
    Nmax: float | np.ndarray,
    Nmin: float | np.ndarray,
) -> tuple[float | np.ndarray, float | np.ndarray]:
    """
    Fringe visibility V = (Nmax-Nmin)/(Nmax+Nmin) and its propagated uncertainty.

    Assumes Poissonian counts.  Returns (V, dV).
    """
    Nmax = np.asarray(Nmax, dtype=float)
    Nmin = np.asarray(Nmin, dtype=float)
    den  = Nmax + Nmin
    V    = (Nmax - Nmin) / np.where(den > 0, den, 1.0)
    dV   = 2 / den ** 2 * np.sqrt(Nmin ** 2 * Nmax + Nmax ** 2 * Nmin)
    return V, dV


def E_uncertainty(
    Npp: float, Npm: float, Nmp: float, Nmm: float
) -> tuple[float, float]:
    """
    CHSH correlation E(a,b) and Poissonian uncertainty.

    E = (Npp + Nmm - Npm - Nmp) / (Npp + Npm + Nmp + Nmm)
    Returns (E, dE).
    """
    den = Npp + Npm + Nmp + Nmm
    if den == 0:
        return float("nan"), float("nan")
    E  = (Npp + Nmm - Npm - Nmp) / den
    dE = np.sqrt(
        ((1 - E) ** 2 * (Npp + Nmm) + (1 + E) ** 2 * (Npm + Nmp)) / den ** 2
    )
    return float(E), float(dE)


def accidental_rate(R_a: float, R_b: float, tau_c_s: float) -> float:
    """Accidental coincidence rate: R_acc = R_a * R_b * tau_c."""
    return R_a * R_b * tau_c_s


def accidental_rate_uncertainty(
    R_a: float, R_b: float,
    dR_a: float, dR_b: float,
    tau_c_s: float, dtau_c_s: float = 0.0,
) -> float:
    """Propagated uncertainty on accidental coincidence rate."""
    return float(np.sqrt(
        (R_b * tau_c_s * dR_a) ** 2 +
        (R_a * tau_c_s * dR_b) ** 2 +
        (R_a * R_b * dtau_c_s) ** 2
    ))


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    for th in [0, 22.5, 45, 67.5, 90]:
        print(f"  theta={th:6.1f}° → Δθ = {angle_uncertainty(th):.2f}°")

    rng = np.random.default_rng(42)
    obs = rng.poisson(100, size=10).astype(float)
    res = chi_squared(obs, np.full(10, 100.0), n_params=0)
    print("\n" + chi_squared_report(res, label="flat-rate test"))

    E, dE = E_uncertainty(500, 50, 60, 490)
    print(f"\nE = {E:.4f} ± {dE:.4f}")
