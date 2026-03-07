def plot_fidelity(ax: plt.Axes, res: dict) -> None:
    """Panel D: fidelity to singlet."""
    p_vals = res["p_vals"]
    ax.plot(p_vals, res["F_p"], "royalblue", lw=2)
    ax.fill_between(p_vals, 0, res["F_p"], alpha=0.15, color="royalblue")
    ax.axhline(0.5, color="gray", ls="--", lw=1, label="Entanglement threshold")
    ax.set_xlabel("Werner mixing parameter $p$")
    ax.set_ylabel(r"Fidelity $F(\rho,\,|\Psi^-\rangle)$")
    ax.set_title("Singlet fidelity vs. state purity")
    ax.legend(fontsize=7.5)
    ax.grid(True, alpha=0.2)
