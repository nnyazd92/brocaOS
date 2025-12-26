from sympy import symbols, E, N, diff
# symbolic parameters
omega_b, omega_c = symbols('omega_b omega_c')
ratio = omega_c/omega_b
# theoretical
dm_theory = 5 + 1/E
# numeric planck values
omega_b_val = 0.02237
omega_c_val = 0.1200
ratio_val = omega_c_val/omega_b_val
# sensitivity: partial derivatives
d_ratio_db = diff(ratio, omega_b)
d_ratio_dc = diff(ratio, omega_c)
# evaluate
print('dm_theory numeric:', N(dm_theory, 12))
print('dm_planck numeric:', ratio_val)
print('absolute error:', float(abs(N(dm_theory,12) - ratio_val)))
print('percent error:', float(abs(N(dm_theory,12) - ratio_val)/ratio_val*100))
print('\nSensitivity: d(ratio)/d(omega_b) at point =', float(d_ratio_db.subs({omega_b:omega_b_val,omega_c:omega_c_val})))
print('Sensitivity: d(ratio)/d(omega_c) at point =', float(d_ratio_dc.subs({omega_b:omega_b_val,omega_c:omega_c_val})))
# if small fractional change in omega_b, effect on ratio
frac_change = 0.001
delta_ratio = float(d_ratio_db.subs({omega_b:omega_b_val,omega_c:omega_c_val})*omega_b_val*frac_change)
print(f'Approx ratio change for {frac_change*100}% change in omega_b: {delta_ratio}')
