# Notebook cell — 2. Quantum Optical Simulation — QuTiP
class QuantumOpticalCavity:
    """QuTiP model of a single-mode optical cavity with photon loss."""

    def __init__(self, N_states: int = 20):
        self.N = N_states
        self.a    = qt.destroy(N_states)
        self.adag = self.a.dag()
        self.n_op = self.adag * self.a

    def coherent_state(self, alpha: complex) -> qt.Qobj:
        return qt.coherent_dm(self.N, alpha)

    def fock_state(self, n: int) -> qt.Qobj:
        return qt.fock_dm(self.N, n)

    def g2_zero(self, rho: qt.Qobj) -> float:
        """g^(2)(0) from density matrix: <a†a†aa> / <a†a>^2."""
        n_mean = qt.expect(self.n_op, rho)
        if n_mean < 1e-12:
            return float('nan')
        n2_op = self.adag * self.adag * self.a * self.a
        return float(qt.expect(n2_op, rho)) / n_mean**2

    def decay(self, kappa: float, rho0: qt.Qobj,
              tlist: np.ndarray) -> qt.solver.Result:
        """Simulate photon loss via Lindblad master equation."""
        H     = qt.qzero(self.N)           # zero Hamiltonian in rotating frame
        c_ops = [np.sqrt(kappa) * self.a]
        e_ops = [self.n_op]
        return qt.mesolve(H, rho0, tlist, c_ops, e_ops)


# ── Demo: Fock state |3⟩ decaying in a lossy cavity ─────────────────────
cav  = QuantumOpticalCavity(N_states=20)
rho0 = cav.fock_state(3)
t    = np.linspace(0, 5, 200)
res  = cav.decay(kappa=1.0, rho0=rho0, tlist=t)

print(f"g²(0) of Fock |3⟩: {cav.g2_zero(rho0):.4f}  (theory: {(3-1)/3:.4f})")
print(f"g²(0) of coherent α=2: {cav.g2_zero(cav.coherent_state(2.0)):.4f}  (theory: 1.0000)")

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(t, res.expect[0], lw=2)
ax.set_xlabel('Time (κ⁻¹)')
ax.set_ylabel(r'$\langle \hat{n} \rangle$')
ax.set_title('Fock |3⟩ decaying in a lossy cavity (κ=1)')
plt.tight_layout()
fig.savefig('plots/nb_cavity_decay.png', dpi=150)
plt.close(fig)
