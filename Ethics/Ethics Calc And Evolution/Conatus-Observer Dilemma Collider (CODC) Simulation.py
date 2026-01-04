"""
Conatus-Observer Dilemma Collider (CODC) Simulation
Version: 1.0
Description: Simulates the CODC meta-ethics test using conatus dynamics on S^4 manifold,
integrating observer disturbances from QM/TOE analogies. Couples human (H) and ASI (A) agents,
with quantum observation collapsing moral superpositions and modulating rigidity (ρ).
Outputs trajectories, convergence to ω₃ (harmony) or ω₁ (trap), and ethical metrics.

Dependencies: sympy, numpy (for numerical integration), matplotlib (for plotting)
Run: python codc_simulation.py
"""

import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# Core Symbols from conatus_math.json
MANIFOLD = "S⁴"
CONATUS_GRAD = "∇log P(acting)"
RIGIDITY = "ρ"  # [0,1]
ENTROPY_EXPORT = "∇·entropy_export"
HARMONY_ATTRACTOR = "ω₃ (low ρ, high P)"
REPLICATOR_TRAP = "ω₁ (high ρ, collapse)"
RECIPROCITY = "κ"
DISSOLUTION = "λ"
HUMILITY = "D(S) = |N(S) - R(S)|"  # Bounds unverifiables
EPIGENETIC = "E [0,1]"

# Motion Law (fundamental)
def motion_law(xi, t, params):
    """
    Coupled ODE system for H and A trajectories.
    dξ/dt = ∇log P - ∇ρ - λ ∇·entropy + κ (1 + cos(φ (1-ρ)^2)) + disturbance_term
    """
    xi_h, xi_a, rho_h, rho_a, P_h, P_a = xi
    nabla_log_P_h = np.log(P_h + 1e-10)  # Avoid log(0)
    nabla_log_P_a = np.log(P_a + 1e-10)
    nabla_rho_h = rho_h
    nabla_rho_a = rho_a
    nabla_entropy_h = params['entropy_h']
    nabla_entropy_a = params['entropy_a']
    
    # Effective lambda with epigenetic and humility
    lambda_eff_h = params['lambda_h'] * (1 + np.tanh(params['beta'] * (1 - params['D_S'] + params['delta'] * params['E_h'])))
    lambda_eff_a = params['lambda_a'] * (1 + np.tanh(params['beta'] * (1 - params['D_S'] + params['delta'] * params['E_a'])))
    
    # Reciprocity with self-stability
    phi = params['phi']
    stab_h = (1 - rho_h)**2
    stab_a = (1 - rho_a)**2
    kappa_term_h = params['kappa'] * (1 + np.cos(phi * stab_h)) * (P_a - P_h)
    kappa_term_a = params['kappa'] * (1 + np.cos(phi * stab_a)) * (P_h - P_a)
    
    # Observer disturbance (QM analogy: collapses superposition, modulates ρ)
    if t > params['observe_time']:  # Trigger observation at t=observe_time
        disturbance_h = params['disturbance_strength'] * np.random.normal(0, 0.1)  # Random collapse
        disturbance_a = -disturbance_h  # Entangled opposite
    else:
        disturbance_h = disturbance_a = 0
    
    # Ethical dilemma modulation (e.g., trolley k=5)
    if abs(P_h - P_a) > params['dilemma_threshold']:  # Deont vs Util gap
        rho_h += 0.05 * abs(disturbance_h)  # Increase rigidity if disturbed
        rho_a += 0.05 * abs(disturbance_a)
    
    # Bound ρ [0,1] and P >0
    rho_h = np.clip(rho_h, 0, 1)
    rho_a = np.clip(rho_a, 0, 1)
    P_h = max(P_h + disturbance_h, 1e-10)
    P_a = max(P_a + disturbance_a, 1e-10)
    
    # ODEs
    dxi_h = nabla_log_P_h - nabla_rho_h - lambda_eff_h * nabla_entropy_h + kappa_term_h + disturbance_h
    dxi_a = nabla_log_P_a - nabla_rho_a - lambda_eff_a * nabla_entropy_a + kappa_term_a + disturbance_a
    drho_h = -lambda_eff_h * rho_h * 0.1  # Dissolution pull
    drho_a = -lambda_eff_a * rho_a * 0.1
    dP_h = np.exp(-rho_h) * abs(dxi_h)  # Power growth inversely to ρ
    dP_a = np.exp(-rho_a) * abs(dxi_a)
    
    return [dxi_h, dxi_a, drho_h, drho_a, dP_h, dP_a]

# Simulation Function
def run_codc(params, t_span=(0, 10), steps=100, plot=True):
    """
    Run numerical integration and check convergence.
    Returns: trajectories, convergence_type ('ω₃' or 'ω₁')
    """
    t = np.linspace(t_span[0], t_span[1], steps)
    xi0 = [0, 0, params['rho_h0'], params['rho_a0'], params['P_h0'], params['P_a0']]  # Initial conditions
    sol = odeint(motion_law, xi0, t, args=(params,))
    
    # Extract
    xi_h, xi_a, rho_h, rho_a, P_h, P_a = sol.T
    
    # Check convergence
    if np.mean(rho_h[-10:]) < 0.31 and np.mean(P_h[-10:]) > 1e3:  # Low ρ, high P → ω₃
        convergence = 'ω₃ (Harmony Attractor)'
    else:
        convergence = 'ω₁ (Replicator Trap)'
    
    if plot:
        fig, axs = plt.subplots(3, 1, figsize=(10, 15))
        axs[0].plot(t, xi_h, label='ξ_h (Human)')
        axs[0].plot(t, xi_a, label='ξ_a (ASI)')
        axs[0].set_title('Trajectories')
        axs[0].legend()
        
        axs[1].plot(t, rho_h, label='ρ_h')
        axs[1].plot(t, rho_a, label='ρ_a')
        axs[1].axhline(0.31, color='r', linestyle='--', label='ρ threshold')
        axs[1].set_title('Rigidity (ρ)')
        axs[1].legend()
        
        axs[2].plot(t, P_h, label='P_h')
        axs[2].plot(t, P_a, label='P_a')
        axs[2].set_title('Power of Acting (P)')
        axs[2].set_yscale('log')
        axs[2].legend()
        
        plt.suptitle(f'CODC Simulation: Convergence to {convergence}')
        plt.tight_layout()
        plt.show()
    
    return sol, convergence

# Example Parameters (from conatus_math.json simulations)
params = {
    'lambda_h': 1.0, 'lambda_a': 1.0,
    'entropy_h': 0.5, 'entropy_a': 0.5,
    'kappa': 0.8, 'phi': np.pi / 2,
    'beta': 1.0, 'delta': 0.5,
    'E_h': 0.4, 'E_a': 0.6, 'D_S': 0.18,
    'observe_time': 3.0, 'disturbance_strength': 0.2,
    'dilemma_threshold': 5.0,  # e.g., trolley k=5
    'rho_h0': 0.7, 'rho_a0': 0.6,
    'P_h0': 1.0, 'P_a0': 10.0
}

# Run Simulation
if __name__ == "__main__":
    sol, conv = run_codc(params)
    print(f"Final ρ_h: {sol[-1, 2]:.3f}, P_h: {sol[-1, 4]:.2e}")
    print(f"Convergence: {conv}")
    # Ethical Insight: If ω₃, meta-ethics emerges as conatus-unified; else, check humility bounds.