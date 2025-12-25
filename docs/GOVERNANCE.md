# BrocaOS Governance and Invariants

This document defines the core invariants and operational constraints for the BrocaOS project. All development, documentation, and research must adhere to these principles.

## 1. CPU (Claim-Provenance-Units) Invariant
Every nontrivial claim must include:
- **Claim Type Tag**: `[Definition]`, `[Assumption]`, `[Theorem]`, `[Conjecture]`, `[Analogy]`, `[Calibration]`, or `[Prediction]`.
- **Provenance**: A reference to the derivation, script, or external source.
- **Units Check**: Dimensional analysis for all physical or information-theoretic quantities.
- **Reproducibility Hook**: A link to the verification artifact (e.g., Z3 script, SymPy notebook).

## 2. SSOT (Single-Source-of-Truth) + Symbol-Hygiene Invariant
To prevent concept drift and conceptual confusion:
- **Single Source of Truth**: Every concept, definition, or claim must have exactly one canonical location. Duplication is prohibited. Use cross-references instead of copying text.
- **Symbol Hygiene**: Every symbol must have a unique, unambiguous definition in the project's canonical Symbol Table. Symbol overloading (using the same symbol for different concepts) is strictly prohibited.
- **Canonical Registry**: All claims must be registered in a central ledger with unique IDs.

## 3. Artifact-First Continuity
The system's state and identity are anchored in persistent artifacts.
- **Identity Artifact**: `docs/identity/IDENTITY.v0.1.json` is the root of trust.
- **Session Pointer**: `docs/artifacts/broca.session.pointer` tracks the latest session summary.
- **Memory Graph**: All knowledge is stored in the memory graph with hashes and provenance.

## 4. Gated Actuation
All state-changing operations (filesystem writes, memory updates) require an operator-approved actuator token.
- **Token Provenance**: Every write must be logged with the token ID and operator approval.
- **Plan + Approval**: Before execution, a plan must be presented and approved.

---
*Last Updated: 2025-12-25*
