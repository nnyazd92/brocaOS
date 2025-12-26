#!/usr/bin/env python3
"""
Analyze dark matter ratio identifiability using SymPy
"""

import sympy as sp
import numpy as np

print("=" * 70)
print("DARK MATTER RATIO IDENTIFIABILITY ANALYSIS")
print("=" * 70)

# Define symbols
lam = sp.symbols('lambda', positive=True)  # Poisson rate parameter
k = sp.symbols('k', positive=True)         # Structural constant (5 in L-ToEC)
R_obs = 5.367879441171442  # 5 + e^{-1}

print("\n1. CURRENT L-ToEC MODEL:")
print("   R = k + exp(-λ)")
print(f"   With k=5, λ=1: R = {5 + np.exp(-1)}")
print(f"   Observed (Planck): Ω_dm/Ω_b ≈ 5.3678")

# Define the L-ToEC model
R_ltoec = k + sp.exp(-lam)

print("\n2. ALTERNATIVE GENERATIVE MODELS:")

# Alternative 1: Negative binomial (overdispersed Poisson)
r = sp.symbols('r', positive=True)  # dispersion parameter
p = sp.symbols('p', positive=True)  # success probability
# P(X=0) for negative binomial: (1-p)^r
R_nb = k + (1-p)**r

print("   a) Negative Binomial:")
print("      R = k + (1-p)^r")
print("      Can match R_obs with infinite (p,r) pairs")

# Alternative 2: Zero-inflated Poisson
phi = sp.symbols('phi', positive=True)  # zero-inflation parameter
# P(X=0) for ZIP: phi + (1-phi)*exp(-λ)
R_zip = k + (phi + (1-phi)*sp.exp(-lam))

print("   b) Zero-Inflated Poisson:")
print("      R = k + [φ + (1-φ)exp(-λ)]")
print("      Extra parameter φ allows infinite fits")

# Alternative 3: Mixture model (log-normal rate)
# This is more complex - would require integration

print("\n3. IDENTIFIABILITY PROBLEM:")
print("   For observed R_obs = 5.3678:")
print("   - L-ToEC: 1 solution (k=5, λ=1)")
print("   - Negative Binomial: ∞ solutions in (p,r) space")
print("   - Zero-Inflated Poisson: ∞ solutions in (φ,λ) space")
print("   - Mixture models: ∞∞ solutions")

print("\n4. MODEL SELECTION CRITERIA NEEDED:")
print("   To select L-ToEC over alternatives, we need:")
print("   a) Axiomatic justification for Poisson assumption")
print("   b) Uniqueness proof: Poisson is only process satisfying axioms")
print("   c) Information-theoretic: MDL/AIC/BIC comparison")
print("   d) Predictive power: New predictions beyond R_obs")

print("\n5. POSSIBLE UNIQUENESS PROOF STRATEGY:")
print("   Theorem: Under axioms A1-A5 (substrate properties),")
print("   the unique stationary mapping process is Poisson(λ=1)")
print("   Axioms needed:")
print("   1. Memoryless property (Markov)")
print("   2. Independent increments")
print("   3. Stationarity")
print("   4. Finite mean rate")
print("   5. Substrate capacity constraints")

print("\n" + "=" * 70)
print("CONCLUSION: Need formal uniqueness theorem, not just fit")
print("=" * 70)
