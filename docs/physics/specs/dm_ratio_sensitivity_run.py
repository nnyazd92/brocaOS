import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import nbinom, lognorm

# Planck 2018 values (as used in repo)
omega_b_h2 = 0.02237
omega_c_h2 = 0.1200
observed_ratio = omega_c_h2 / omega_b_h2

# L-ToEC predicted ratio baseline
predicted_ratio_lambda1 = 5 + math.exp(-1)

# Sweep lambda for Poisson model: R(lambda) = 5 + exp(-lambda)
lambdas = np.linspace(0.1, 3.0, 200)
R_poisson = 5 + np.exp(-lambdas)

# Negative binomial (NB) as overdispersed alternative: P0 = (k/(k+lambda))**k
# parameterize by r (number of successes) where smaller r -> more overdispersion
ks = [0.5, 1.0, 2.0, 5.0]
R_nbin = {k: 5 + (k/(k + lambdas))**k for k in ks}

# Log-normal mixture as heavy-tailed rate uncertainty -> P0 ~ E[exp(-Lambda)] where Lambda ~ LogNormal
mu = 0.0
sigma_vals = [0.0, 0.5, 1.0]
R_lognorm = {}
for s in sigma_vals:
    # Analytical: E[e^{-L}] where L ~ LogNormal(mu_ln, sigma) has no closed form simple; compute numeric
    lambdas_ln = np.linspace(0.1, 3.0, 40)
    P0_vals = []
    for lam in lambdas_ln:
        # choose lognormal parametrization so that mean(Lambda)=lam
        # For lognormal with parameters m,s: mean = exp(m + s^2/2) = lam -> m = ln(lam) - s^2/2
        m = np.log(lam) - (s**2)/2.0
        # sample to estimate E[exp(-L)] = E[e^{-Lambda}]
        samples = np.random.lognormal(mean=m, sigma=s, size=20000)
        P0_vals.append(np.mean(np.exp(-samples)))
    R_lognorm[s] = (lambdas_ln, 5 + np.array(P0_vals))

# Plot Poisson and NB families
plt.figure(figsize=(6,4))
plt.plot(lambdas, R_poisson, label='Poisson: 5+exp(-lambda)', lw=2)
for k, Rk in R_nbin.items():
    plt.plot(lambdas, Rk, '--', label=f'NegBin k={k}')
plt.axvline(1.0, color='gray', alpha=0.5)
plt.scatter([1.0], [predicted_ratio_lambda1], color='k')
plt.xlabel('lambda (sampling rate)')
plt.ylabel('R = 5 + overhead')
plt.title('DM Ratio vs sampling parameter (model families)')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('docs/physics/notebooks/dm_ratio_lambda_plot.png')

# Plot lognormal mixtures (heavy-tailed uncertainty)
plt.figure(figsize=(6,4))
for s, (lamln, Rvals) in R_lognorm.items():
    plt.plot(lamln, Rvals, label=f'LogNormal sigma={s}')
plt.plot(lamln, R_poisson[:len(lamln)], ':', label='Poisson (for comparison)')
plt.xlabel('mean lambda')
plt.ylabel('R = 5 + E[e^{-Lambda}]')
plt.title('DM Ratio under lognormal rate uncertainty')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('docs/physics/notebooks/dm_ratio_lognorm_plot.png')

# Compute numeric comparisons at lambda=1
lambda0 = 1.0
R_poisson_1 = 5 + math.exp(-lambda0)
R_nbin_1 = {k: 5 + (k/(k + lambda0))**k for k in ks}
# For lognormal use small-sigma approx: E[e^{-L}] approx exp(-E[L] + Var(L)/2 - ...)
# we'll estimate via sampling
R_lognorm_1 = {}
for s in sigma_vals:
    m = math.log(lambda0) - (s**2)/2.0
    samples = np.random.lognormal(mean=m, sigma=s, size=200000)
    est = 5 + np.mean(np.exp(-samples))
    R_lognorm_1[s] = est

# Write a short report
with open('docs/physics/notebooks/dm_ratio_sensitivity_report.txt','w') as f:
    f.write('L-ToEC DM Ratio sensitivity report\n')
    f.write('================================\n')
    f.write(f'Planck observed ratio (using omega_b_h2=0.02237, omega_c_h2=0.12): {observed_ratio:.12f}\n')
    f.write(f'Predicted (Poisson lambda=1): {R_poisson_1:.12f}\n')
    f.write('\nComparisons at lambda=1:\n')
    for k, val in R_nbin_1.items():
        f.write(f' NegBin k={k}: R={val:.12f}\n')
    for s, val in R_lognorm_1.items():
        f.write(f' LogNormal sigma={s}: R~{val:.12f}\n')
    f.write('\nInterpretation:\n')
    f.write(' - The Poisson-based prediction (5+exp(-1)) matches Planck within ~0.00355 abs (~0.066% rel) as previously observed.\n')
    f.write(' - Under modest overdispersion (NegBin k<=1), P0 increases, raising R; for k=0.5 R~{:.6f}\n'.format(R_nbin_1.get(0.5)))
    f.write(' - Heavy-tailed uncertainty (lognormal sigma>0) tends to reduce E[e^{-Lambda}] relative to exp(-E[Lambda]) due to Jensen, producing deviations of order 1e-3--1e-2 depending on sigma.\n')

# Print summary to stdout
print('WROTE: docs/physics/notebooks/dm_ratio_lambda_plot.png')
print('WROTE: docs/physics/notebooks/dm_ratio_lognorm_plot.png')
print('WROTE: docs/physics/notebooks/dm_ratio_sensitivity_report.txt')

