# Notebook cell — 1. Classical Propagation — ABCD Matrices
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
