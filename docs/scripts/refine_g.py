import math

# Constants
c = 299792458
hbar = 1.054571817e-34
m_p = 1.67262192369e-27
G_obs = 6.67430e-11

# Substrate Properties
co0_order = 8315553613086720000  # Exact order of Co0
v4 = (math.pi**2) / 2            # Volume of 4D unit ball

# L-ToE Prediction Formula:
# alpha_g = 1 / ( (V4/2) * |Co0|^2 )
# G = (alpha_g * hbar * c) / m_p^2

alpha_g_pred = 1 / ( (v4/2) * (co0_order**2) )
G_pred = (alpha_g_pred * hbar * c) / (m_p**2)

print(f"Observed G:  {G_obs:.8e}")
print(f"Predicted G: {G_pred:.8e}")
print(f"Accuracy:    {100 * (1 - abs(G_obs - G_pred)/G_obs):.4f}%")

# Let's check if the '2.45' factor is actually related to the 24D/4D ratio
v24 = (math.pi**12) / math.gamma(13)
ratio_v = v4 / v24
print(f"V4/V24 Ratio: {ratio_v:.4f}")

