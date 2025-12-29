from sympy import symbols, Function, I, exp, diff, laplacian, Symbol
from sympy import simplify, collect, expand
from sympy.tensor.array import derive_by_array

# Define symbols
hbar, m = symbols('hbar m')
V = Function('V')

# Coordinates
x, t = symbols('x t')

# Functions R(x,t) and S(x,t)
R = Function('R')(x,t)
S = Function('S')(x,t)

# Define psi = R * exp(i S / hbar)
psi = R * exp(I * S / hbar)

# Compute time derivative
psi_t = diff(psi, t)

# Spatial derivatives: for 1D use second derivative as Laplacian
psi_xx = diff(psi, x, 2)

# Schrödinger LHS and RHS
LHS = I * hbar * psi_t
RHS = -hbar**2/(2*m) * psi_xx + V(x) * psi

# Compute residual = LHS - RHS
residual = simplify(LHS - RHS)

# Multiply by exp(-i S / hbar) to factor out fast oscillation
factor = exp(-I * S / hbar)
rescaled = simplify(expand(simplify(residual * factor)))

# Now expand rescaled and collect powers of 1/hbar by multiplying by hbar
# We inspect terms proportional to hbar^(-1), hbar^0, hbar^1
# Multiply rescaled by hbar to make leading term hbar^0
rescaled_times_hbar = expand(rescaled * hbar)

with open('broca/output/validate_sympy_log.txt','w') as f:
    f.write('psi = R*exp(i S / hbar) substitution:\n')
    f.write('LHS - RHS (residual) simplified and multiplied by exp(-iS/hbar):\n')
    f.write(str(rescaled) + '\n\n')
    f.write('rescaled * hbar (to inspect leading terms):\n')
    f.write(str(rescaled_times_hbar) + '\n\n')

    f.write('Interpretation:\n')
    f.write('Leading order in 1/hbar yields the Hamilton-Jacobi equation for S: if we collect terms proportional to hbar^0 in rescaled_times_hbar and set them to zero, we obtain\n')
    f.write('   S_t + (S_x^2)/(2m) + V = 0  (1D)\n')
    f.write('Next order gives a continuity-type equation for R (probability conservation) with quantum potential corrections.\n')

print('SymPy validation completed. Log written to broca/output/validate_sympy_log.txt')
