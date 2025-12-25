from z3 import *

def check_layer_logic():
    # Define Sorts
    LayerSort = Datatype('LayerSort')
    LayerSort.declare('L0')
    LayerSort.declare('L1')
    LayerSort.declare('L2')
    LayerSort.declare('L3')
    LayerSort = LayerSort.create()

    # Define Properties
    Discrete = Function('Discrete', LayerSort, BoolSort())
    Smooth = Function('Smooth', LayerSort, BoolSort())
    HasDynamics = Function('HasDynamics', LayerSort, BoolSort())
    
    s = Solver()

    # Axioms
    l0, l1, l2, l3 = LayerSort.L0, LayerSort.L1, LayerSort.L2, LayerSort.L3
    
    # L0 is discrete
    s.add(Discrete(l0))
    s.add(Not(Smooth(l0)))
    
    # L3 is smooth
    s.add(Smooth(l3))
    s.add(Not(Discrete(l3)))
    
    # Mapping M: L0 -> L3
    # M must resolve the discrete-smooth incompatibility
    # We define a Protocol Layer L1 that handles this
    # We use a variable 'l' of sort LayerSort for the quantifier
    l = Const('l', LayerSort)
    s.add(Implies(And(Discrete(l0), Smooth(l3)), Exists([l], And(l == l1, HasDynamics(l), Not(Discrete(l)), Not(Smooth(l))))))
    
    # Check consistency
    if s.check() == sat:
        print("Layered Architecture Logic: CONSISTENT")
    else:
        print("Layered Architecture Logic: INCONSISTENT")

if __name__ == "__main__":
    check_layer_logic()
