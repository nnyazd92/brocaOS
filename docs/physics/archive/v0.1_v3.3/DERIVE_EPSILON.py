import numpy as np

# Constants
H0_CMB = 67.4
H0_LOCAL = 73.0
Z_CMB = 1100.0

def hubble_ratio_prediction(epsilon):
    # Local ratio (z=0)
    R_local = 5.36 # Using the more precise observed ratio
    # CMB ratio (z=1100)
    R_cmb = R_local * (1 + epsilon * np.log(1 + Z_CMB))
    
    # The Hubble tension is roughly proportional to the change in the sound horizon.
    # A higher DM density in the past (R_cmb > R_local) means a smaller sound horizon,
    # which requires a HIGHER H0 to match the observed angular size of the CMB peaks.
    # H0_local = H0_CMB * sqrt( (1 + R_cmb) / (1 + R_local) )
    
    tension_ratio = (1 + R_cmb) / (1 + R_local)
    return np.sqrt(tension_ratio)

# Solve for epsilon
target_ratio = H0_LOCAL / H0_CMB
epsilons = np.linspace(0, 0.05, 10000)
ratios = [hubble_ratio_prediction(e) for e in epsilons]

idx = np.argmin(np.abs(np.array(ratios) - target_ratio))
best_epsilon = epsilons[idx]

print(f"Target H0 Ratio: {target_ratio:.4f}")
print(f"Best Epsilon: {best_epsilon:.6f}")
print(f"Predicted R_CMB: {5.36 * (1 + best_epsilon * np.log(1 + Z_CMB)):.4f}")
print(f"Local R (z=0): 5.36")
