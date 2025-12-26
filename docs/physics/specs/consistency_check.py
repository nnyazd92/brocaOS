from z3 import *
# Simple numerical consistency check for DM ratio
DM_theory = Real('DM_theory')
DM_planck = Real('DM_planck')
s = Solver()
# approximate values
s.add(DM_theory == RealVal('5.367879441171442'))
s.add(DM_planck == RealVal('5.36433'))
# assert they are within 0.01
s.add(DM_theory - DM_planck < RealVal('0.01'))
s.add(DM_planck - DM_theory < RealVal('0.01'))
print('Z3 solve status:', s.check())
m = s.model()
print('model:', m)
