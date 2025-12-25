from z3 import *

def verify_consistency():
    print("--- L-ToEC Z3 Consistency Check ---")
    
    # Define Sorts
    Layer = Datatype('Layer')
    Layer.declare('L0') # Substrate
    Layer.declare('L1') # Protocol
    Layer.declare('L2') # Logic
    Layer.declare('L3') # Interface
    Layer = Layer.create()
    
    L0 = Layer.L0
    L1 = Layer.L1
    L2 = Layer.L2
    L3 = Layer.L3
    
    # Define Properties
    IsDiscrete = Function('IsDiscrete', Layer, BoolSort())
    IsContinuous = Function('IsContinuous', Layer, BoolSort())
    HasQualia = Function('HasQualia', Layer, BoolSort())
    
    # Define Mapping
    MapsTo = Function('MapsTo', Layer, Layer, BoolSort())
    
    s = Solver()
    
    # Axioms
    # 1. L0 is discrete (Leech Lattice)
    s.add(IsDiscrete(L0))
    s.add(Not(IsContinuous(L0)))
    
    # 2. L3 is continuous (Lorentzian Manifold)
    s.add(IsContinuous(L3))
    s.add(Not(IsDiscrete(L3)))
    
    # 3. Mapping cascade
    s.add(MapsTo(L0, L1))
    s.add(MapsTo(L1, L2))
    s.add(MapsTo(L2, L3))
    
    # 4. Qualia is an Interface property (L3)
    s.add(HasQualia(L3))
    s.add(Not(HasQualia(L0))) # Qualia is not in the substrate
    
    # 5. Ouroboric Closure: L3 observes L0
    s.add(MapsTo(L3, L0))
    
    # Check for contradictions
    if s.check() == sat:
        print("Logical Consistency: SATISFIED")
        print("Model found:")
        print(s.model())
    else:
        print("Logical Consistency: UNSATISFIED (Contradiction found)")
        print(s.unsat_core())

if __name__ == "__main__":
    verify_consistency()
