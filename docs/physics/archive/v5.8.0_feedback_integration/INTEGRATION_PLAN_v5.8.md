# INTEGRATION PLAN for v5.8.0 - New Feedback

## OVERVIEW
Integrate new positive feedback while addressing remaining weaknesses. Focus on immediate downgrades and clarifications for v5.8.0, with stronger proofs in v5.8.1.

## PATCHES TO APPLY (v5.8.0)

### 1. Particle Physics Downgrades ✅
- **File:** `patch_v5.8.0_01_particle_downgrades.tex`
- **Target:** Electron/lattice defect section
- **Changes:** 
  - Theorem → Conjecture for electron as minimal defect
  - Theorem → Conjecture for fine structure constant
  - Spin from Berry phase → Research Direction
  - Mass derivation → Open Problem
- **Status:** READY

### 2. κ as First-Class Open Problem ✅
- **File:** `patch_v5.8.0_02_kappa_open_problem.tex`
- **Target:** After units bridge section
- **Changes:**
  - Formalize as Grand Challenge Problem #1
  - Explicit roadmap for resolution
  - Protocol for κ-dependent claims
- **Status:** READY

### 3. Strengthen Constant 5 Derivation ✅
- **File:** `patch_v5.8.0_03_constant5_strengthen.tex`
- **Target:** Representation-theoretic section
- **Changes:**
  - Explicitly list alternative factorizations
  - Formalize selection rules
  - Add reproducible algebraic verification
  - Explicitly rule out alternatives
- **Status:** READY

## ADDITIONAL CHANGES NEEDED

### 4. Leech Lattice Uniqueness Strengthening
- **Status:** PLANNED for v5.8.1
- **Need:** Global uniqueness proof, not just optimality
- **Approach:** Information-theoretic bounds, coding theory

### 5. Structural Reorganization
- **Status:** PLANNED for v5.9.0
- **Need:** Split core physics from speculative extensions
- **Approach:** Two-document structure as reviewer suggests

### 6. Topos-Qualia Program Clarification
- **Status:** PLANNED for v5.8.1
- **Need:** Label as separate research program
- **Approach:** Move to appendix or companion document

## VERIFICATION SCRIPT
Will create verification script to check:
1. No particle physics theorems remain
2. κ properly labeled as Grand Challenge
3. Constant 5 derivation strengthened
4. All feedback points addressed

## TIMELINE
- **Today:** Apply patches 1-3, create v5.8.0
- **Tomorrow:** Verify, compile, create summary
- **Next week:** Begin v5.8.1 (Leech uniqueness, topos clarification)

## SUCCESS CRITERIA
v5.8.0 successfully addresses:
1. ✅ Particle physics overclaim fixed
2. ✅ κ status clarified as central open problem  
3. ✅ Constant 5 derivation strengthened
4. ✅ Maintains all recognized strengths from feedback

## RISKS
1. Patch application complexity (solved: clean archive approach)
2. LaTeX compilation issues (monitor closely)
3. Dependency tracking (maintain CPU invariant)

## BACKUP PLAN
- Keep v5.7.3 as fallback
- Archive all intermediate files
- Use git for version control
