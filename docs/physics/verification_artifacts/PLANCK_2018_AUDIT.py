def planck_2018_audit():
    print("--- L-ToEC: Planck 2018 Parameter Audit ---")
    # Values from Planck 2018 results. VI. Cosmological parameters
    # Table 2, Column: TT,TE,EE+lowE+lensing (68% limits)
    
    omega_b_h2 = 0.02237
    omega_c_h2 = 0.1200
    
    ratio_obs = omega_c_h2 / omega_b_h2
    
    # L-ToEC Theoretical Ratio
    import math
    ratio_theo = 5 + math.exp(-1)
    
    error_pct = abs(ratio_theo - ratio_obs) / ratio_obs * 100
    
    print(f"Observed Omega_c h^2 / Omega_b h^2: {ratio_obs:.5f}")
    print(f"Theoretical Ratio (5 + 1/e):       {ratio_theo:.5f}")
    print(f"Absolute Error:                    {abs(ratio_theo - ratio_obs):.5f}")
    print(f"Percentage Error:                  {error_pct:.4f}%")
    
    if error_pct < 0.1:
        print("Audit Status: SUCCESS (<0.1% error)")
    else:
        print("Audit Status: REVIEW REQUIRED")

if __name__ == "__main__":
    planck_2018_audit()
