#!/usr/bin/env python3
"""
Debug the scaling calculation issue
"""

import math
import numpy as np

# Let's manually check the math
D = 24
K = 196560
d = 4

# Theoretical scaling: f_sym = (d/D)^2 = (4/24)^2 = 0.02778
theoretical_f_sym = (d/D)**2
print(f"Theoretical f_sym for d={d}, D={D}: {theoretical_f_sym:.6f}")

# The issue: Our approximation gives C_interface > C_substrate
# This suggests the scale factor is wrong

# Let's compute what the scale factor SHOULD be:
# C_substrate = K * D / 2 = 196560 * 24 / 2 = 2,358,720 bits/cycle
C_substrate_theoretical = K * D / 2
print(f"\nTheoretical C_substrate: {C_substrate_theoretical:,} bits/cycle")

# In our simulation, we got C_substrate ≈ 2.36e6 (matches!)
# But then we scaled it by factor ~6569.65
# That scale factor is applied to BOTH substrate and interface

# The problem: When we compute C_interface, we use:
# C_interface = C_per_channel * interface_weight * scale
# But scale = (K*D/2) / C_total_unscaled

# Actually, let's trace through the logic:

print("\nDebugging the scaling logic:")
print("1. We compute C_total_unscaled from graph weights")
print("2. We compute scale_factor = (K*D/2) / C_total_unscaled")
print("3. We apply scale_factor to BOTH C_substrate and C_interface")
print("4. But C_interface should be f_sym * C_substrate")

# Let's compute what f_sym we're actually getting
C_interface_reported = 14283297.249723231  # From results for d=4
C_substrate_reported = 2358720.0
actual_f_sym = C_interface_reported / C_substrate_reported
print(f"\nReported C_interface: {C_interface_reported:.2e}")
print(f"Reported C_substrate: {C_substrate_reported:.2e}")
print(f"Actual f_sym (C_int/C_sub): {actual_f_sym:.6f}")
print(f"Theoretical f_sym: {theoretical_f_sym:.6f}")
print(f"Ratio actual/theoretical: {actual_f_sym/theoretical_f_sym:.2f}")

# The problem: actual_f_sym = 6.06, but should be 0.028!
# So C_interface is 200× too large!

print("\nRoot cause analysis:")
print("1. Our random projection doesn't preserve graph topology properly")
print("2. Distances in projected space may be compressed/expanded")
print("3. Weight calculation 1/(1+dist²) may not be appropriate")
print("4. Need better model for information transfer")

print("\nProposed fixes:")
print("1. Use adjacency preservation (same edges), not distance weighting")
print("2. Compute capacity as number of usable channels, not weighted sum")
print("3. Or: C_interface = f_sym * C_substrate directly (circular!)")
print("4. Need independent measure of interface capacity")

print("\nAlternative approach:")
print("Define f_sym as probability that a substrate channel")
print("can communicate with the interface:")
print("  f_sym = P(channel projects to distinguishable interface state)")
print("This should scale as (d/D)^2 for random projections")
