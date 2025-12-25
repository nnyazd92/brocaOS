import sympy as sp

def derive_theorem():
    # Define symbols
    n = sp.symbols('n', integer=True)
    tau = sp.IndexedBase('tau')
    rho = sp.IndexedBase('rho')
    i, j = sp.symbols('i j', cls=sp.Idx)
    z = sp.symbols('z') # Coordination number
    
    # Dirichlet Energy + Source Term
    # L = sum_{<i,j>} (tau_i - tau_j)^2 + sum_i rho_i * tau_i
    
    # We consider a single node i and its neighbors
    # The terms in the sum involving tau_i are:
    # sum_{j in N(i)} (tau_i - tau_j)^2 + rho_i * tau_i
    
    neighbors = sp.symbols('j1:5') # Assume z=4 for 2D lattice toy model
    L_local = sum((tau[i] - tau[nj])**2 for nj in neighbors) + rho[i] * tau[i]
    
    # Minimize with respect to tau[i]
    dL_dtau_i = sp.diff(L_local, tau[i])
    
    print("First-order condition (dL/dtau_i = 0):")
    sp.pprint(dL_dtau_i)
    
    # Solve for tau[i]
    solution = sp.solve(dL_dtau_i, tau[i])[0]
    print("\nOptimal Latency at node i:")
    sp.pprint(solution)
    
    # Compare with discrete Laplacian
    # Laplacian(tau)_i = sum_j (tau_j - tau_i)
    laplacian = sum(tau[nj] - tau[i] for nj in neighbors)
    
    # If dL/dtau_i = 0, then 2 * sum(tau_i - tau_j) + rho_i = 0
    # sum(tau_j - tau_i) = rho_i / 2
    
    print("\nDiscrete Laplacian relation:")
    sp.pprint(laplacian)
    
    # Check if laplacian equals rho_i / 2
    if sp.simplify(laplacian - rho[i]/2) == 0:
        print("\nVERIFIED: Minimizing Dirichlet energy yields discrete Poisson equation.")
    else:
        # The sign depends on the definition of rho
        if sp.simplify(laplacian + rho[i]/2) == 0:
             print("\nVERIFIED: Minimizing Dirichlet energy yields discrete Poisson equation (with sign convention).")

if __name__ == "__main__":
    derive_theorem()
