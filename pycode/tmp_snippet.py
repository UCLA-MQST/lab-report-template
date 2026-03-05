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
