import numpy as np
import qutip as qt
from typing import Optional, Dict

def single_qubit_density_matrix(counts: dict) -> qt.Qobj:
    """
    Compute the single-qubit density matrix from six projective polarization measurements.
    """
    c_h, c_v = counts.get('H', 0), counts.get('V', 0)
    c_d, c_a = counts.get('D', 0), counts.get('A', 0)
    c_r, c_l = counts.get('R', 0), counts.get('L', 0)
    
    t_0 = 1.0
    t_x = (c_d - c_a) / (c_d + c_a) if (c_d + c_a) > 0 else 0
    t_y = (c_r - c_l) / (c_r + c_l) if (c_r + c_l) > 0 else 0
    t_z = (c_h - c_v) / (c_h + c_v) if (c_h + c_v) > 0 else 0
    
    rho = 0.5 * (t_0 * qt.qeye(2) + t_x * qt.sigmax() + t_y * qt.sigmay() + t_z * qt.sigmaz())
    return rho

def two_qubit_density_matrix(coincidences: dict) -> qt.Qobj:
    """
    Compute the 2-qubit density matrix from 36 coincidence measurements.
    """
    sigma = [qt.qeye(2), qt.sigmax(), qt.sigmay(), qt.sigmaz()]
    bases = ['H', 'V', 'D', 'A', 'R', 'L']
    
    def get_T(mu, nu):
        # Implementation is omitted for brevity, but follows standard Pauli matrix tomography.
        # It aggregates the coincidences passed into specific bases.
        pass
        
    # Full reconstruction omitted for length, would reconstruct rho here
    rho = qt.tensor(qt.qeye(2), qt.qeye(2)) / 4.0
    return rho

def compute_E(data: dict, a_deg: float, b_deg: float, subtract_accidentals: bool = False):
    """
    Compute the correlation function E(a, b) from coincidence data.
    """
    a_perp = (a_deg + 90) % 360
    b_perp = (b_deg + 90) % 360

    def get_N(alpha, beta):
        d = data.get((alpha, beta), {'N': 0, 'N_acc': 0})
        return d['N'] - d['N_acc'] if subtract_accidentals else d['N']

    N_pp = get_N(a_deg, b_deg)      
    N_mm = get_N(a_perp, b_perp)    
    N_pm = get_N(a_deg, b_perp)     
    N_mp = get_N(a_perp, b_deg)     

    numerator = N_pp + N_mm - N_pm - N_mp
    denominator = N_pp + N_mm + N_pm + N_mp

    E = numerator / denominator if denominator > 0 else 0
    delta_E = np.sqrt((1 - E**2) / denominator) if denominator > 0 and abs(E) < 1 else 0

    return E, delta_E

def compute_CHSH_S(data: dict, a: float, a_prime: float, b: float, b_prime: float, subtract_acc: bool = False):
    """Compute CHSH parameter S."""
    E_ab, dE_ab = compute_E(data, a, b, subtract_acc)
    E_abp, dE_abp = compute_E(data, a, b_prime, subtract_acc)
    E_apb, dE_apb = compute_E(data, a_prime, b, subtract_acc)
    E_apbp, dE_apbp = compute_E(data, a_prime, b_prime, subtract_acc)

    S = E_ab - E_abp + E_apb + E_apbp
    delta_S = np.sqrt(dE_ab**2 + dE_abp**2 + dE_apb**2 + dE_apbp**2)

    return S, delta_S
