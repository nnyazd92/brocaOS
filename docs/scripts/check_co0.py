import math

# Constants
c = 299792458
hbar = 1.054571817e-34
G = 6.67430e-11
m_p = 1.67262192369e-27  # proton mass
e = 1.602176634e-19
epsilon_0 = 8.8541878128e-12

# Order of Conway Group Co_0
# |Co_0| = 2^22 * 3^9 * 5^4 * 7^2 * 11 * 13 * 23
co0_order = (2**22) * (3**9) * (5**4) * (7**2) * 11 * 13 * 23
print(f"|Co0|: {co0_order:.4e}")

# Ratio of EM to Gravity for two protons
f_em_g_proton = (e**2) / (4 * math.pi * epsilon_0 * G * m_p**2)
print(f"F_em / F_g (protons): {f_em_g_proton:.4e}")

# Ratio of EM to Gravity for two electrons
m_e = 9.1093837e-31
f_em_g_electron = (e**2) / (4 * math.pi * epsilon_0 * G * m_e**2)
print(f"F_em / F_g (electrons): {f_em_g_electron:.4e}")

# Compare with |Co0|^2
print(f"|Co0|^2: {co0_order**2:.4e}")

# Dimensionless G (Gravitational coupling constant for proton)
alpha_g = (G * m_p**2) / (hbar * c)
print(f"alpha_g (proton): {alpha_g:.4e}")
print(f"1 / alpha_g: {1/alpha_g:.4e}")

# Is 1/alpha_g related to |Co0|?
# 1/alpha_g is ~ 1.7e38.
# |Co0|^2 is ~ 6.9e37.
# Ratio:
print(f"(1/alpha_g) / |Co0|^2: {(1/alpha_g) / (co0_order**2):.4f}")

# What about |Co0| * K24?
k24 = 196560
print(f"|Co0| * K24: {co0_order * k24:.4e}")
print(f"(1/alpha_g) / (|Co0| * K24): {(1/alpha_g) / (co0_order * k24):.4f}")

