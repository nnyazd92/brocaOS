import sympy as sp

def verify_mechanism():
    x, y, z, h = sp.symbols('x y z h')
    tau = sp.Function('tau')(x, y, z)
    
    # Taylor expansions
    t_xp = tau.subs(x, x+h).series(h, 0, 3).removeO()
    t_xm = tau.subs(x, x-h).series(h, 0, 3).removeO()
    t_yp = tau.subs(y, y+h).series(h, 0, 3).removeO()
    t_ym = tau.subs(y, y-h).series(h, 0, 3).removeO()
    t_zp = tau.subs(z, z+h).series(h, 0, 3).removeO()
    t_zm = tau.subs(z, z-h).series(h, 0, 3).removeO()
    
    discrete_laplacian = (t_xp + t_xm + t_yp + t_ym + t_zp + t_zm - 6*tau) / h**2
    
    # Take limit h -> 0
    limit_laplacian = sp.limit(discrete_laplacian, h, 0)
    
    print("Continuum Limit (h -> 0):")
    sp.pprint(limit_laplacian)
    
    laplacian_target = sp.diff(tau, x, 2) + sp.diff(tau, y, 2) + sp.diff(tau, z, 2)
    
    if sp.simplify(limit_laplacian - laplacian_target) == 0:
        print("\nVERIFIED: Discrete congestion model yields Laplacian in continuum limit.")
    else:
        print("\nFAILED: Limit does not match Laplacian.")

if __name__ == "__main__":
    verify_mechanism()
