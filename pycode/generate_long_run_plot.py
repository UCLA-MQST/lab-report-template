#!/usr/bin/env python3
"""
generate_long_run_plot.py — QuTiP simulation demo for the template report pipeline.

This script is the canonical "heavy computation" example managed by Snakemake.
It demonstrates how to:
  1. Use qutip to simulate entangled two-photon polarization states.
  2. Compute CHSH S-parameter sweeps over a range of measurement angles.
  3. Compare Bell-state fidelities against a noisy (Werner) state model.
  4. Cache the resulting multi-panel figure as plots/qutip_bell_simulation.png.

The computation (~5-30 s depending on resolution) is only re-run when this
script or its declared Snakemake inputs are modified.

Usage (via Snakemake or directly):
    python3 pycode/generate_long_run_plot.py [output_path]
"""

from __future__ import annotations
import sys, os
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import qutip as qt

# Ensure pycode/ is importable when run as a standalone script
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "pycode"))

from photon_statistics import E_bell
from errors import chi_squared, chi_squared_report, visibility_uncertainty


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def werner_state(p: float) -> qt.Qobj:
    """
    Werner state: rho = p |Ψ⁻><Ψ⁻| + (1-p) I/4.

    p = 1 → maximally entangled singlet.
    p = 1/3 → boundary of entanglement (threshold for CHSH violation ≈ 0.707).
    p = 0 → maximally mixed (no entanglement).
    """
    psi_minus = (qt.tensor(qt.basis(2, 0), qt.basis(2, 1)) -
                 qt.tensor(qt.basis(2, 1), qt.basis(2, 0))).unit()
    rho_singlet = psi_minus * psi_minus.dag()
    rho_mixed   = qt.tensor(qt.qeye(2), qt.qeye(2)) / 4
    return p * rho_singlet + (1 - p) * rho_mixed


def two_photon_projector(theta_deg: float, phi_deg: float = 0.0) -> qt.Qobj:
    """
    Projector onto single-photon polarization state |θ,φ⟩.
    θ = 0   → |H⟩, θ = 90 → |V⟩, θ = 45 → |D⟩, etc.
    """
    th  = np.deg2rad(theta_deg)
    phi = np.deg2rad(phi_deg)
    vec = np.cos(th) * qt.basis(2, 0) + np.exp(1j * phi) * np.sin(th) * qt.basis(2, 1)
    return vec * vec.dag()


def coincidence_rate(rho: qt.Qobj, alpha_deg: float, beta_deg: float) -> float:
    """
    Expected coincidence probability P(α, β) = Tr[ρ (Π_α ⊗ Π_β)].
    """
    Pi_a = two_photon_projector(alpha_deg)
    Pi_b = two_photon_projector(beta_deg)
    M    = qt.tensor(Pi_a, Pi_b)
    return float(np.real((rho * M).tr()))


def E_from_rho(rho: qt.Qobj, alpha_deg: float, beta_deg: float) -> float:
    """
    Correlation function E(α,β) from density matrix.
    Uses four projective combinations (++, --, +-, -+).
    """
    a, ap = alpha_deg, (alpha_deg + 90) % 360
    b, bp = beta_deg,  (beta_deg  + 90) % 360
    Npp = coincidence_rate(rho, a,  b)
    Nmm = coincidence_rate(rho, ap, bp)
    Npm = coincidence_rate(rho, a,  bp)
    Nmp = coincidence_rate(rho, ap, b)
    den = Npp + Nmm + Npm + Nmp
    return (Npp + Nmm - Npm - Nmp) / den if den > 0 else 0.0


def CHSH_S_from_rho(rho: qt.Qobj,
                    a: float = 0, a_prime: float = 45,
                    b: float = -22.5, b_prime: float = 22.5) -> float:
    """
    CHSH S-parameter computed from a density matrix.
    Default angles are CHSH-optimal for the singlet state.
    """
    return (E_from_rho(rho, a,       b) -
            E_from_rho(rho, a,       b_prime) +
            E_from_rho(rho, a_prime, b) +
            E_from_rho(rho, a_prime, b_prime))


def fidelity_to_singlet(rho: qt.Qobj) -> float:
    """Fidelity of rho to |Ψ⁻⟩."""
    psi_minus = (qt.tensor(qt.basis(2, 0), qt.basis(2, 1)) -
                 qt.tensor(qt.basis(2, 1), qt.basis(2, 0))).unit()
    return float(np.real(qt.fidelity(rho, psi_minus * psi_minus.dag()) ** 2))


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

def run_simulation(n_angle_pts: int = 60) -> dict:
    """
    Run three sub-simulations and return results dict.

    1. E(α, β) correlation surface for the Werner state at p = 0.85.
    2. CHSH S vs. Werner mixing parameter p, compared to theory.
    3. Visibility scan: singlet fringe V(α) vs. Alice angle.
    """
    # ── Sub-sim 1: E(α, β=22.5°) as function of α for three Werner p values ──
    alphas = np.linspace(0, 180, n_angle_pts)
    beta   = 22.5   # fixed Bob angle
    E_rho  = {}
    for p in [1.0, 0.85, 0.707]:
        rho    = werner_state(p)
        E_rho[p] = np.array([E_from_rho(rho, a, beta) for a in alphas])
    # Theoretical (p=1 singlet)
    E_theory = np.array([E_bell(np.deg2rad(a), np.deg2rad(beta), "singlet")
                         for a in alphas])

    # ── Sub-sim 2: CHSH S vs. p ──────────────────────────────────────────────
    p_vals = np.linspace(0, 1, 80)
    S_vals = np.array([CHSH_S_from_rho(werner_state(p)) for p in p_vals])
    S_theory = 2 * np.sqrt(2) * p_vals  # linear in p for Werner states

    # ── Sub-sim 3: fringe visibility V(α) for the singlet ────────────────────
    rho_singlet = werner_state(1.0)
    rho_noisy   = werner_state(0.85)
    vis_singlet = []
    vis_noisy   = []
    for a in alphas:
        Nmax_s = coincidence_rate(rho_singlet, a, 0)
        Nmin_s = coincidence_rate(rho_singlet, a, 90)
        Nmax_n = coincidence_rate(rho_noisy,   a, 0)
        Nmin_n = coincidence_rate(rho_noisy,   a, 90)
        # Avoid division by zero (scale to representable counts)
        scale  = 1000
        V_s, _ = visibility_uncertainty(Nmax_s * scale, Nmin_s * scale)
        V_n, _ = visibility_uncertainty(Nmax_n * scale, Nmin_n * scale)
        vis_singlet.append(V_s)
        vis_noisy.append(V_n)

    # ── Sub-sim 4: fidelity to singlet ───────────────────────────────────────
    F_p = np.array([fidelity_to_singlet(werner_state(p)) for p in p_vals])

    return dict(
        alphas=alphas, beta=beta,
        E_rho=E_rho, E_theory=E_theory,
        p_vals=p_vals, S_vals=S_vals, S_theory=S_theory,
        vis_singlet=np.array(vis_singlet), vis_noisy=np.array(vis_noisy),
        F_p=F_p,
    )


def make_figure(res: dict, out: Path) -> None:
    """Render the 2×2 simulation panel and save to *out*."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    alphas = res["alphas"]
    p_vals = res["p_vals"]

    # ── Panel A: E(α, 22.5°) ─────────────────────────────────────────────────
    ax = axes[0, 0]
    colors = {1.0: "royalblue", 0.85: "darkorange", 0.707: "seagreen"}
    labels = {1.0: "Werner $p=1$ (singlet)", 0.85: "$p=0.85$", 0.707: "$p=1/\\sqrt{2}$"}
    for p, E in res["E_rho"].items():
        ax.plot(alphas, E, color=colors[p], label=labels[p])
    ax.plot(alphas, res["E_theory"], "k--", lw=1.2, alpha=0.5, label="Theory ($p=1$)")
    ax.axhline(0, color="gray", lw=0.8, ls=":")
    ax.set_xlabel(r"Alice angle $\alpha$ (deg)")
    ax.set_ylabel(r"$E(\alpha,\, 22.5°)$")
    ax.set_title(r"Correlation function for Werner states")
    ax.legend(fontsize=7.5)
    ax.grid(True, alpha=0.2)

    # ── Panel B: CHSH S vs. p ─────────────────────────────────────────────────
    ax = axes[0, 1]
    ax.plot(p_vals, res["S_vals"],   "royalblue",  lw=2,   label="QuTiP simulation")
    ax.plot(p_vals, res["S_theory"], "k--",        lw=1.2, label=r"Theory $S=2\sqrt{2}\,p$")
    ax.axhline(2 * np.sqrt(2), color="crimson", ls="--", lw=1,
               label=r"QM max $2\sqrt{2}$")
    ax.axhline(2,              color="gray",    ls=":",  lw=1,
               label="Classical bound $|S|=2$")
    ax.fill_between(p_vals, 2, res["S_vals"],
                    where=res["S_vals"] > 2, alpha=0.12, color="royalblue",
                    label="CHSH violation region")
    ax.set_xlabel("Werner mixing parameter $p$")
    ax.set_ylabel("CHSH parameter $S$")
    ax.set_title("CHSH $S$ vs. state purity")
    ax.legend(fontsize=7.5)
    ax.grid(True, alpha=0.2)

    # ── Panel C: fringe visibility ────────────────────────────────────────────
    ax = axes[1, 0]
    ax.plot(alphas, np.abs(res["vis_singlet"]), "royalblue",  lw=2,   label="$p=1$ (singlet)")
    ax.plot(alphas, np.abs(res["vis_noisy"]),   "darkorange", lw=2,   label="$p=0.85$ (noisy)")
    ax.axhline(1 / np.sqrt(2), color="gray", ls="--", lw=1,
               label=r"CHSH threshold $1/\sqrt{2}$")
    ax.set_xlabel(r"Alice angle $\alpha$ (deg)")
    ax.set_ylabel("Visibility $V$")
    ax.set_title("Polarization fringe visibility")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(fontsize=7.5)
    ax.grid(True, alpha=0.2)

    # ── Panel D: fidelity to singlet ─────────────────────────────────────────
    ax = axes[1, 1]
    ax.plot(p_vals, res["F_p"], "royalblue", lw=2)
    ax.fill_between(p_vals, 0, res["F_p"], alpha=0.15, color="royalblue")
    ax.axhline(0.5, color="gray", ls="--", lw=1, label="Entanglement threshold")
    ax.set_xlabel("Werner mixing parameter $p$")
    ax.set_ylabel(r"Fidelity $F(\rho,\,|\Psi^-\rangle)$")
    ax.set_title("Singlet fidelity vs. state purity")
    ax.legend(fontsize=7.5)
    ax.grid(True, alpha=0.2)

    fig.suptitle(
        "QuTiP Bell-state simulation — Werner state model\n"
        r"$\rho(p) = p\,|\Psi^-\rangle\langle\Psi^-| + (1-p)\,\mathbf{I}/4$",
        fontsize=11)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(f"Saved: {out}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 \
               else Path("plots/qutip_bell_simulation.png")
    print("Running QuTiP Bell-state simulation…")
    results = run_simulation(n_angle_pts=60)
    make_figure(results, out_path)
