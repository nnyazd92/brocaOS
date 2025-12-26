from z3 import *
import json

# Define nodes and edges for the provenance DAG
node_names = [
    'Co0_Dimensionless',
    'GroupOrder_Observed',
    'DimensionalBridge',
    'MappingLatencyDefined',
    'PlanckMass_Independent',
    'PlanckMass_Defined_Via_G',
    'Uses_PlanckMass',
    'G_value',
    'Derivation_Explicit'
]

nodes = {name: Bool(name) for name in node_names}

# Define implication edges (src -> dst)
edges = [
    ('GroupOrder_Observed', 'DimensionalBridge'),
    ('DimensionalBridge', 'MappingLatencyDefined'),
    ('MappingLatencyDefined', 'Derivation_Explicit'),
    ('Uses_PlanckMass', 'G_value'),
    ('PlanckMass_Independent', 'Uses_PlanckMass'),
    ('PlanckMass_Defined_Via_G', 'Uses_PlanckMass'),
    ('Co0_Dimensionless', 'GroupOrder_Observed'),
]

# Build solver with facts (implications)
solver_base = Solver()
for (src,dst) in edges:
    solver_base.add(Implies(nodes[src], nodes[dst]))

# Function: given a set of base assumptions (list of node names asserted True),
# check whether target is provable. We use a greedy minimalization to find a small subset.

def is_provable(base_assumptions, target):
    s = Solver()
    s.append(solver_base.assertions())
    # add Not(target) and check if inconsistent with assumptions
    s.add(Not(nodes[target]))
    # add base assumptions as assertions
    for b in base_assumptions:
        s.add(nodes[b])
    return s.check() == unsat

# Greedy minimal assumption finder
def minimal_assumptions(full_assumptions, target):
    # Start with full set
    cur = list(full_assumptions)
    changed = True
    while changed:
        changed = False
        for a in list(cur):
            trial = [x for x in cur if x != a]
            if is_provable(trial, target):
                cur = trial
                changed = True
    return cur

# Example: compute minimal assumptions for G_value
full_assumps = ['Co0_Dimensionless','GroupOrder_Observed','DimensionalBridge','MappingLatencyDefined','PlanckMass_Independent','Uses_PlanckMass']
print('Full assumptions:', full_assumps)
provable_full = is_provable(full_assumps, 'G_value')
print('Is G_value provable from full assumptions?', provable_full)
min_assumps = minimal_assumptions(full_assumps, 'G_value')
print('Greedy minimal assumptions for G_value:', min_assumps)

# Output provenance mapping (map nodes to source snippets / files)
provenance = {
    'Co0_Dimensionless': {'source':'manuscript_section_co0','file':'docs/physics/L_TOEC_MASTER_V5.tex'},
    'GroupOrder_Observed': {'source':'data_table_grouporder','file':'docs/physics/L_TOEC_MASTER_V5.tex'},
    'DimensionalBridge': {'source':'specs/z3_full_axioms.py','file':'docs/physics/specs/z3_full_axioms.py'},
    'MappingLatencyDefined': {'source':'specs/z3_full_axioms.py','file':'docs/physics/specs/z3_full_axioms.py'},
    'PlanckMass_Independent': {'source':'appendix_constants','file':'docs/physics/L_TOEC_MASTER_V5.tex'},
    'PlanckMass_Defined_Via_G': {'source':'notes','file':'docs/physics/CRITIQUE_V5.md'},
    'Uses_PlanckMass': {'source':'spec_proof_sketch','file':'docs/physics/CRITIQUE_V5.md'},
    'G_value': {'source':'main_claim','file':'docs/physics/L_TOEC_MASTER_V5.tex'},
    'Derivation_Explicit': {'source':'proof_section','file':'docs/physics/L_TOEC_MASTER_V5.tex'}
}

# write outputs
with open('docs/rehydration/verification_v5/z3_dag.out','w') as f:
    f.write('=== Z3 DAG Provenance Run ===\n')
    f.write('Edges:\n')
    for e in edges:
        f.write(' - %s -> %s\n' % (e[0], e[1]))
    f.write('\nFull assumptions: %s\n' % full_assumps)
    f.write('Provable from full assumptions: %s\n' % provable_full)
    f.write('Greedy minimal assumptions: %s\n' % min_assumps)

with open('docs/rehydration/verification_v5/z3_dag_provenance.json','w') as f:
    json.dump({'nodes':node_names,'edges':edges,'provenance':provenance,'full_assumptions':full_assumps,'minimal_assumptions':min_assumps},f,indent=2)

print('Wrote docs/rehydration/verification_v5/z3_dag.out and z3_dag_provenance.json')
