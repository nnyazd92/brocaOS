# CRITIQUE V5 — Verification Progress and Findings

Approval: APPROVE — implement-v5-and-verify (use-token-from-file)
Actuator provenance: .temporary_token.txt (jti=6cc5dd7cb9444aa992f81aee4eae7d73)

Summary of new formal checks (Z3 + SymPy):

1) Z3 axiomatic check (docs/physics/specs/z3_axioms.py)
- Demonstrates that any claim deriving G from a dimensionless group order must introduce dimensionful scales. A simple Z3 encoding shows G-derivable & units-not-introduced is unsatisfiable.
- Numeric closeness of DM theory vs Planck was checked with epsilon constraint; satisfiable for reasonable eps.
- See docs/rehydration/verification_v5/z3_axioms.out for raw output.

2) SymPy sensitivity and units audit
- DM ratio symbolic and numeric comparison: docs/rehydration/verification_v5/sympy_dm_sensitivity.out (absolute error ~0.00355; ~0.0662% relative)
- Sensitivity derivatives w.r.t omega_b and omega_c computed to estimate robustness to parameter changes.
- Units audit demonstrates that combining hbar, c, and Planck mass Mp with powers (1,1,-2) yields dimensions of G: G ~ hbar*c / Mp^2. This highlights the need to explicitly state the dimensionful bridge used in any G-from-|Co0| claim. See docs/rehydration/verification_v5/sympy_units_audit.out

Limitations encountered:
- Sage is currently unavailable (rebuild failed). All symbolic algebra was performed with SymPy instead.
- The Z3 encodings so far are intentionally minimal/proof-of-concept; they must be extended to formalize mapping-latency axioms and other structural claims.

Recommended next steps:
A) Formalize the full set of axioms in Z3: mapping-latency definitions, CPU labels, dependency DAG constraints, and then check for logical consequences and contradictions.
B) Create reproducible Jupyter notebooks for each major derivation (DM ratio, G-from-Co0) with step-by-step SymPy cells, numeric checks, and plots for sensitivity.
C) Where Planck-scale constants or Planck mass are used, avoid circular definitions: if you define Mp via G, you cannot then derive G from Mp without independent grounding.

Files produced:
- docs/physics/L_TOEC_MASTER_V5.tex
- docs/physics/L_TOEC_MASTER_V5.pdf
- docs/physics/specs/z3_axioms.py
- docs/physics/specs/sympy_dm_sensitivity.py
- docs/physics/specs/sympy_units_audit.py
- docs/rehydration/verification_v5/z3_axioms.out
- docs/rehydration/verification_v5/sympy_dm_sensitivity.out
- docs/rehydration/verification_v5/sympy_units_audit.out


## Z3 DAG & Provenance
Added a provenance-aware DAG and minimal-assumption extraction tool: docs/physics/specs/z3_dag.py
Outputs: docs/rehydration/verification_v5/z3_dag.out and z3_dag_provenance.json

### Expanded Z3 DAG and numeric/unit constraints
Added a richer provenance DAG with intermediate nodes and numeric/unit checks: docs/physics/specs/z3_dag_expanded.py
Outputs: docs/rehydration/verification_v5/z3_dag_expanded.* (runout, json, dot, png if available)


## Refined DAG: Circularity forbiddance & minimal sets
SymPy values: DM_theory=5.367879441171442, DM_planck=5.364327223960661
Provable from universe: False
Enumerated minimal proving sets: []
