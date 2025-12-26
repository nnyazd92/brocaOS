from sympy import symbols, E, N
# Theoretical DM ratio: 5 + 1/e
dm_theory = 5 + 1/E
# Planck 2018 observational ratio (omega_c/omega_b)
omega_b_h2 = 0.02237
omega_c_h2 = 0.1200
dm_planck = omega_c_h2 / omega_b_h2
print('dm_theory (symbolic):', dm_theory)
print('dm_theory (numeric):', N(dm_theory, 10))
print('dm_planck (numeric):', dm_planck)
print('absolute error:', abs(N(dm_theory,10) - dm_planck))
print('percent error:', float(abs(N(dm_theory,10) - dm_planck)/dm_planck*100))
