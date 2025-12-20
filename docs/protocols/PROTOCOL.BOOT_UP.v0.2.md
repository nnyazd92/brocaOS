# Boot-Up Protocol (BUP) v0.2 - Identity-aware

Purpose
- Extend boot semantics to load and verify a canonical identity artifact before enabling persistence or mutating the self-model.
- Preserve artifact-first continuity: identity is the authoritative pointer set used to locate durable artifacts (memories, vector index, self-model snapshot, etc.).

Preflight (read-only) - mandatory
1) Locate identity artifact:
   - Read broca.session.pointer if present to obtain the identity artifact path.
   - Fallback: docs/identity/IDENTITY.v0.1.json.
2) Read identity JSON and detached signature sidecar (docs/identity/*.signature.json).
3) Verify signature using configured provenance (prefer environment BROCA_TOKEN_SECRET; fallback to approved token files such as .temporary_token.txt). Record verification result and which provenance was used in the rehydration summary.
4) Validate pointers inside identity (check presence of memory_db, vector_index, self_model_db files) and record counts/hashes as available.

Gating semantics
- If signature verification succeeds: set PERSISTENCE_ENABLED = true and record token_provenance metadata (token_id / exp / scopes when extractable) in rehydration summary.
- If verification fails: keep persistence sandboxed and surface diagnostics in REHYDRATION_SUMMARY. Do not enable persistence unless an explicit override Approval is provided by an operator.

Boot steps (read-only until Plan+Approval present)
1) load_persistence_gate(): perform identity verification and set PERSISTENCE_ENABLED only if authenticated.
2) hydrate_pointers_and_artifacts(): load artifact pointers referenced in identity (broca.session.pointer, broca.artifacts, memory_namespaces_index.md). This is read-only during preflight.
3) hydrate_memory_graph(): instantiate memory storage and vector index and sync indexes. If persistence authenticated, the components may write state to disk as part of sync. Writes require the operator-approved actuator provenance recorded during boot.
4) verify_self_consistency(): run a non-mutative self-consistency check. If drift is detected that would require self-model mutation, produce an ORP block and pause for ORP approval before applying any self-model changes.
5) build_rehydration_summary(): write REHYDRATION_SUMMARY.v0.2.md/.json summarizing boot actions, identity verification, token provenance, and next steps.
6) boot banner: present boot status, persistence posture, identity verification result, and next steps.
7) gating posture: if persistence enabled, allow gated actions after Plan+Approval; else operate in sandbox.

Identity specifics
- Identity artifact location/pointer is authoritative for boot. Identity contains token provenance, pointers to memory/index/self-model artifacts, and a signature_meta field used for verification.
- Self-model mutations are not performed during boot. ORP process must be used for any self-model mutation.

Operator templates
- Identity verification override (if you accept risk):
  - Approval line (explicit): I, <operator>, approve overriding identity verification for this boot and enabling persistence despite signature failure.
  - Actuator token provenance: <file or env>

End - PROTOCOL.BOOT_UP.v0.2.md
