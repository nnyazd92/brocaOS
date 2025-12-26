from z3 import *
import json

# Nodes
node_names = [
    'Co0_Dimensionless',
    'GroupOrder_Observed',
    'DimensionalBridge',
    'Mapping_Function_Specified',
    'MappingLatencyDefined',
    'Mapping_Latency_Positive',
    'Mapping_Latency_Value_known',
    'Derivation_Explicit',
    'Uses_PlanckMass',
    'PlanckMass_Independent',
    'PlanckMass_Defined_Via_G',
    'Units_Audit_Passed',
    'Units_Consistent',
    'NumericMatch_DM',
    'Numeric_Error_Below_Eps',
    'G_value',
    'NoCircularity'
]

nodes = {n: Bool(n) for n in node_names}

# numeric and unit symbols
DM_theory = Real('DM_theory')
DM_planck = Real('DM_planck')
eps = Real('eps')
latency = Real('latency')
# unit exponents for hbar^a * c^b * Mp^c
a,b,c = Ints('a b c')

s_base = Solver()
# Implications (stronger/conditional)
# Co0 dimensionless -> Group order observed
s_base.add(Implies(nodes['Co0_Dimensionless'], nodes['GroupOrder_Observed']))
# Group order observed + Dimensional bridge -> Mapping function specified
s_base.add(Implies(And(nodes['GroupOrder_Observed'], nodes['DimensionalBridge']), nodes['Mapping_Function_Specified']))
# Mapping function specified + latency positive -> MappingLatencyDefined
s_base.add(Implies(And(nodes['Mapping_Function_Specified'], nodes['Mapping_Latency_Positive']), nodes['MappingLatencyDefined']))
# MappingLatencyDefined -> Derivation explicit only if NumericMatch and Units consistent
s_base.add(Implies(And(nodes['MappingLatencyDefined'], nodes['NumericMatch_DM'], nodes['Units_Consistent'], nodes['NoCircularity']), nodes['Derivation_Explicit']))
# Units audit passed -> Units consistent
s_base.add(Implies(nodes['Units_Audit_Passed'], nodes['Units_Consistent']))
# Numeric error below eps -> NumericMatch_DM
s_base.add(Implies(nodes['Numeric_Error_Below_Eps'], nodes['NumericMatch_DM']))
# Planck mass independ -> Uses planck mass allowed
s_base.add(Implies(nodes['PlanckMass_Independent'], nodes['Uses_PlanckMass']))
# PlanckMass defined via G -> Uses planck mass (but creates circularity when used in numeric constraints)
s_base.add(Implies(nodes['PlanckMass_Defined_Via_G'], nodes['Uses_PlanckMass']))
# Uses planck mass + Units consistent + NumericMatch and not circular -> G_value
s_base.add(Implies(And(nodes['Uses_PlanckMass'], nodes['Units_Consistent'], nodes['NumericMatch_DM'], nodes['NoCircularity']), nodes['G_value']))

# Circularity rule: if Planck mass defined via G AND it's used to produce G, then NoCircularity is false
# We'll represent Circularity as Not(NoCircularity) when those conditions hold
s_base.add(Implies(And(nodes['PlanckMass_Defined_Via_G'], nodes['Uses_PlanckMass'], nodes['NumericMatch_DM']), Not(nodes['NoCircularity'])))

# Numeric constraints example (for Numeric_Error_Below_Eps)
s_base.add(DM_theory == RealVal('5.367879441171442'))
s_base.add(DM_planck == RealVal('5.364327223960661'))
# default eps placeholder; will be set when assumption asserted

# unit equations: require a,b,c such that hbar^a c^b Mp^c has units of G
# mass exponent: a + c = -1
# length exponent: 2*a + b = 3
# time exponent: -a - b = -2 -> a + b = 2
s_base.add(a + c == -1)
s_base.add(2*a + b == 3)
s_base.add(a + b == 2)

# Mapping latency numeric constraint (to connect Mapping_Latency_Positive)
# We will assert a specific latency when assumption is set

# helper: add assumption-based assertions
def add_assumptions(solver, assumptions):
    for assump in assumptions:
        if assump in nodes:
            solver.add(nodes[assump])
        elif assump == 'Numeric_Error_Below_Eps(0.005)':
            # add eps value and numeric closeness constraints
            solver.add(eps == RealVal('0.005'))
            solver.add(DM_theory - DM_planck < eps)
            solver.add(DM_planck - DM_theory < eps)
            solver.add(nodes['Numeric_Error_Below_Eps'])
        elif assump == 'Mapping_Latency_Positive(0.1)':
            solver.add(latency == RealVal('0.1'))
            solver.add(latency > 0)
            solver.add(nodes['Mapping_Latency_Positive'])
        elif assump == 'Units_Audit_Passed(calculated)':
            # ensure integer solution for a,b,c is consistent (Z3 will check satisfiability)
            solver.add(nodes['Units_Audit_Passed'])
        elif assump == 'PlanckMass_Independent':
            solver.add(nodes['PlanckMass_Independent'])
        elif assump == 'PlanckMass_Defined_Via_G':
            solver.add(nodes['PlanckMass_Defined_Via_G'])
        elif assump == 'Co0_Dimensionless':
            solver.add(nodes['Co0_Dimensionless'])
        elif assump == 'DimensionalBridge':
            solver.add(nodes['DimensionalBridge'])
        elif assump == 'GroupOrder_Observed':
            solver.add(nodes['GroupOrder_Observed'])
        else:
            # unrecognized assumption
            pass

# provability check

def is_provable_with_assumptions(assumptions, target):
    s = Solver()
    s.append(s_base.assertions())
    add_assumptions(s, assumptions)
    # require target to be true; we check for contradiction with Not(target)
    s.push()
    s.add(Not(nodes[target]))
    res = s.check()
    s.pop()
    return res == unsat

# greedy minimal assumptions finder

def minimal_assumptions(full_assumptions, target):
    cur = list(full_assumptions)
    changed = True
    while changed:
        changed = False
        for a in list(cur):
            trial = [x for x in cur if x != a]
            if is_provable_with_assumptions(trial, target):
                cur = trial
                changed = True
    return cur

# Example run
full_assumps = [
    'Co0_Dimensionless',
    'GroupOrder_Observed',
    'DimensionalBridge',
    'Mapping_Latency_Positive(0.1)',
    'Mapping_Latency_Positive',
    'Mapping_Latency_Value_known',
    'Units_Audit_Passed(calculated)',
    'Numeric_Error_Below_Eps(0.005)',
    'PlanckMass_Independent',
    'Uses_PlanckMass'
]

print('Full assumptions:', full_assumps)
provable = is_provable_with_assumptions(full_assumps, 'G_value')
print('Is G_value provable from full assumptions?', provable)
min_assumps = minimal_assumptions(full_assumps, 'G_value')
print('Greedy minimal assumptions for G_value:', min_assumps)

# Check unit exponent solution
u = Solver()
u.append(s_base.assertions())
# check existence of integer solution for a,b,c
if u.check() == sat:
    m = u.model()
    ae = m[a].as_long(); be = m[b].as_long(); ce = m[c].as_long()
    print('Unit exponents solution found:', (ae,be,ce))
else:
    print('No integer solution for unit exponents')

# Circularity check: if PlanckMass_Defined_Via_G used with Numeric closeness -> NoCircularity must be false
circ = Solver()
circ.append(s_base.assertions())
circ.add(nodes['PlanckMass_Defined_Via_G'])
circ.add(nodes['Uses_PlanckMass'])
# add numeric closeness
circ.add(eps == RealVal('0.005'))
circ.add(DM_theory - DM_planck < eps)
circ.add(DM_planck - DM_theory < eps)
res_circ = circ.check()
print('Circularity scenario satisfiable?', res_circ)
if res_circ == sat:
    mm = circ.model()
    # evaluate NoCircularity
    # (We check whether NoCircularity can be true under these conditions)
    circ.push(); circ.add(nodes['NoCircularity']); res2 = circ.check(); circ.pop()
    print('Can NoCircularity be true under circular-use conditions?', res2)

# write outputs
with open('docs/rehydration/verification_v5/z3_dag_expanded.out','w') as f:
    f.write('Full assumptions: %s\n' % full_assumps)
    f.write('Provable: %s\n' % provable)
    f.write('Greedy minimal assumptions: %s\n' % min_assumps)
    f.write('Circularity check satisfiable: %s\n' % res_circ)

# provenance JSON and graph edges
edges = [
    ('Co0_Dimensionless','GroupOrder_Observed'),
    ('GroupOrder_Observed','Mapping_Function_Specified'),
    ('DimensionalBridge','Mapping_Function_Specified'),
    ('Mapping_Function_Specified','MappingLatencyDefined'),
    ('Mapping_Latency_Positive','MappingLatencyDefined'),
    ('Units_Audit_Passed','Units_Consistent'),
    ('Numeric_Error_Below_Eps','NumericMatch_DM'),
    ('NumericMatch_DM','Derivation_Explicit'),
    ('Units_Consistent','Derivation_Explicit'),
    ('PlanckMass_Independent','Uses_PlanckMass'),
    ('PlanckMass_Defined_Via_G','Uses_PlanckMass'),
    ('Uses_PlanckMass','G_value')
]
provenance = {n: {'file': 'docs/physics/L_TOEC_MASTER_V5.tex' if n in ['Co0_Dimensionless','GroupOrder_Observed','G_value'] else 'docs/physics/specs/z3_dag_expanded.py'} for n in node_names}

with open('docs/rehydration/verification_v5/z3_dag_expanded.json','w') as f:
    json.dump({'nodes': node_names, 'edges': edges, 'provenance': provenance, 'full_assumptions': full_assumps, 'minimal_assumptions': min_assumps}, f, indent=2)

print('Wrote outputs to docs/rehydration/verification_v5/')
