#!/usr/bin/env python3
"""Auto-generated from optical_simulator.ipynb by nb_to_report.py."""

# fmt: off
import sys, os
from pathlib import Path
ROOT = Path('.').resolve()
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / 'pycode'))


# ────────────────────────────────────────────────────────
# Optical Simulator
# ────────────────────────────────────────────────────────
import numpy as np
import matplotlib.pyplot as plt
import qutip as qt

plt.style.use('seaborn-v0_8-darkgrid')


# ────────────────────────────────────────────────────────
# 1. Classical Propagation — ABCD Matrices
# ────────────────────────────────────────────────────────
class OpticalComponent:
    """Base class for an optical component with an ABCD transfer matrix."""
    def __init__(self, name: str):
        self.name = name
        self.abcd = np.eye(2)

    def propagate(self, q: complex) -> complex:
        """Propagate a Gaussian beam q-parameter through this component."""
        A, B, C, D = self.abcd.flatten()
        return (A * q + B) / (C * q + D)


class FreeSpace(OpticalComponent):
    def __init__(self, distance: float):
        super().__init__(f"Free Space d={distance}")
        self.abcd = np.array([[1, distance], [0, 1]])


class ThinLens(OpticalComponent):
    def __init__(self, focal_length: float):
        super().__init__(f"Lens f={focal_length}")
        self.abcd = np.array([[1, 0], [-1/focal_length, 1]])


class CurvedMirror(OpticalComponent):
    def __init__(self, radius_of_curvature: float):
        """Concave mirror with radius R; effective focal length f = R/2."""
        super().__init__(f"Mirror R={radius_of_curvature}")
        f = radius_of_curvature / 2
        self.abcd = np.array([[1, 0], [-1/f, 1]])


class OpticalPathway:
    """Sequence of optical components; computes the cumulative transfer matrix."""
    def __init__(self):
        self.components: list[OpticalComponent] = []

    def add(self, component: OpticalComponent) -> 'OpticalPathway':
        self.components.append(component)
        return self

    def transfer_matrix(self) -> np.ndarray:
        """Return the system ABCD matrix (rightmost component applied first)."""
        M = np.eye(2)
        for comp in reversed(self.components):
            M = comp.abcd @ M
        return M

    def propagate_q(self, q0: complex) -> complex:
        for comp in self.components:
            q0 = comp.propagate(q0)
        return q0


# ── Demo: simple telescope (two thin lenses) ─────────────────────────────
path = OpticalPathway()
path.add(FreeSpace(0.10)).add(ThinLens(0.10)).add(FreeSpace(0.15))\
    .add(ThinLens(0.15))
M = path.transfer_matrix()
print("System ABCD matrix:\n", M)
# Gaussian beam: beam waist at input (q0 = i * z_R, z_R = pi * w0^2 / lambda)
lam, w0 = 810e-9, 50e-6
z_R = np.pi * w0**2 / lam
q_out = path.propagate_q(1j * z_R)
w_out = np.sqrt(-lam / (np.pi * (1/q_out).imag))
print(f"Output beam waist: {w_out*1e6:.2f} µm")


# ────────────────────────────────────────────────────────
# 2. Quantum Optical Simulation — QuTiP
# ────────────────────────────────────────────────────────
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
        H     = qt.qzero(self
            .N)           # zero Hamiltonian in rotating frame
        c_ops = [np.sqrt(kappa) * self.a]
        e_ops = [self.n_op]
        return qt.mesolve(H, rho0, tlist, c_ops, e_ops)


# ── Demo: Fock state |3⟩ decaying in a lossy cavity ─────────────────────
cav  = QuantumOpticalCavity(N_states=20)
rho0 = cav.fock_state(3)
t    = np.linspace(0, 5, 200)
res  = cav.decay(kappa=1.0, rho0=rho0, tlist=t)

print(f"g²(0) of Fock |3⟩: {cav.g2_zero(rho0):.4f}  (theory: {(3-1)/3:
    .4f})")
print(f"g²(0) of coherent α=2: {cav.g2_zero(cav.coherent_state(2.0)):
    .4f}  (theory: 1.0000)")

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(t, res.expect[0], lw=2)
ax.set_xlabel('Time (κ⁻¹)')
ax.set_ylabel(r'$\langle \hat{n} \rangle$')
ax.set_title('Fock |3⟩ decaying in a lossy cavity (κ=1)')
plt.tight_layout()
plt.show()
