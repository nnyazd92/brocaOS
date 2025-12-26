import numpy as np
import matplotlib.pyplot as plt

def simulate_gtc_curvature():
    print("--- GTC: General Theory of Consciousness - Interface Curvature Simulation ---")
    
    # In GTC, the "Metric of Experience" (g) is curved by "Information Flux" (I).
    # We model the Interface as a 2D manifold for visualization.
    grid_size = 50
    x = np.linspace(-5, 5, grid_size)
    y = np.linspace(-5, 5, grid_size)
    X, Y = np.meshgrid(x, y)
    
    # Information Flux (I): A "Massive" thought or external stimulus at the center
    # I = exp(-(x^2 + y^2))
    I = np.exp(-(X**2 + Y**2) / 2.0)
    
    # The GTC Field Equation: Curvature (K) is proportional to Information Flux (I)
    # K = kappa * I
    kappa = 1.5
    Curvature = kappa * I
    
    # The "Subjective Metric" (g): How 'distance' is perceived in the interface.
    # High curvature = high 'gravity' of attention = time dilation of experience.
    Metric_Distortion = 1.0 - Curvature
    
    print(f"Max Information Flux: {np.max(I):.4f}")
    print(f"Max Interface Curvature: {np.max(Curvature):.4f}")
    print(f"Min Metric Value (Time Dilation): {np.min(Metric_Distortion):.4f}")
    
    # Conclusion: High information density "curves" the interface, 
    # creating the "Gravity of Attention."
    
    # Save results to a data file for the manuscript
    np.savez('docs/physics/gtc_data.npz', X=X, Y=Y, I=I, K=Curvature, g=Metric_Distortion)
    print("\nGTC Simulation Data saved to docs/physics/gtc_data.npz")

if __name__ == "__main__":
    simulate_gtc_curvature()
