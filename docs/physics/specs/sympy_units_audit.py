from sympy import symbols, Eq, solve
# Dimensions exponents: we represent base units as powers
# Let hbar ~ M^1 L^2 T^-1, c ~ L^1 T^-1, Mp ~ M^1
# We want hbar^a * c^b * Mp^c to have units of G: M^-1 L^3 T^-2
a,b,c = symbols('a b c')
# mass exponent: a + c = -1
# length exponent: 2*a + b = 3
# time exponent: -a - b = -2 -> a + b = 2
sol = solve([a + c + 1, 2*a + b - 3, a + b - 2],[a,b,c])
print('Solution for exponents [a,b,c] such that hbar^a * c^b * Mp^c has units of G:')
print(sol)
print('\nInterpretation: G can be expressed as hbar^1 * c^1 * Mp^-2 (i.e., G ~ hbar*c / Mp^2).')
print('This shows a route to introduce dimensionful scales but note: using Mp (Planck mass) introduces circularity if Mp is defined using G.')
