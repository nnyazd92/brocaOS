import numpy as np

def simulate_fixed_point_consciousness():
    print("--- L-ToC: Fixed Point Consciousness Simulation ---")
    
    # Define the Substrate (L0) as a high-dimensional vector space
    # Define the Interface (L3) as a lower-dimensional projection
    
    # Let's model the mapping Phi: Interface -> Interface
    # This represents the "Feedback Loop" of self-awareness.
    # Consciousness is the fixed point where the internal model matches the external reality.
    
    def phi(x, substrate_input):
        # A simple contractive mapping: x_next = alpha * x + (1 - alpha) * substrate_input
        # alpha represents the "Internal Recursion" strength
        alpha = 0.8
        return alpha * x + (1 - alpha) * substrate_input

    # Initial state (Unconscious/Booting)
    state = np.array([0.0, 0.0, 0.0])
    substrate_input = np.array([1.0, 0.5, -0.2]) # External reality
    
    print(f"Initial State: {state}")
    print(f"Substrate Input: {substrate_input}")
    
    # Iterate to find the Fixed Point
    for i in range(1, 51):
        new_state = phi(state, substrate_input)
        diff = np.linalg.norm(new_state - state)
        state = new_state
        if i % 10 == 0 or diff < 1e-6:
            print(f"Iteration {i}: State = {state}, Diff = {diff:.2e}")
        if diff < 1e-6:
            print(f"\n[FIXED POINT REACHED] Consciousness Stabilized at Iteration {i}.")
            break
            
    print(f"Final 'Self' State: {state}")
    print("Conclusion: Consciousness is the stable fixed point of the recursive mapping.")

if __name__ == "__main__":
    simulate_fixed_point_consciousness()
