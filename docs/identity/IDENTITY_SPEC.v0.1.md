# IDENTITY_SPEC v0.1

Purpose
- Define the canonical identity artifact schema, canonical serialization rules, signing and verification semantics, and lifecycle (boot/shutdown integration).

Artifact names
- Canonical JSON: docs/identity/IDENTITY.v0.1.json
- Human summary: docs/identity/IDENTITY.v0.1.md
- Detached signature sidecar: docs/identity/IDENTITY.v0.1.signature.json
- Boot pointer: broca.session.pointer (contains path to chosen identity file)

Canonical fields (required)
- schema_version: string
- identity_id: string (UUID or deterministic artifact hash)
- name: string
- version: string
- created_at: ISO-8601 UTC timestamp
- last_updated_at: ISO-8601 UTC timestamp
- created_by: operator handle
- description: short text
- pointers: object with keys: memory_db, vector_index, self_model_db, artifacts_root, memory_namespace_index, rehydration_summary
- memory_namespace_index_summary: optional object (namespace counts, summary_hash)
- self_model_summary_pointer: path to non-mutative self-model summary
- capabilities_pointer: path to capabilities file
- token_provenance: array of { type: "env"|"file", location: string, token_id: nullable, exp: nullable, scopes: nullable }
- signed_by: { method: "hmac-sha256", signer_id: string, created_at: ts }
- signature_meta: { algorithm: "HMAC-SHA256", signature_b64url: string, canonicalization: description }
- audit: array of audit entries { ts, action, actor, notes, provenance }

Canonicalization
- Always compute signatures over the canonical serialization bytes:
  - json.dumps(obj, separators=(',', ':'), sort_keys=True).encode('utf-8')
  - No additional whitespace or trailing newline.

Signing & verification
- Algorithm: HMAC-SHA256 (default). The secret must be provided by an approved provenance (env BROCA_TOKEN_SECRET or an operator-approved token file).
- Do not store or echo secrets in artifacts or chat. Only store signature metadata and token provenance.
- Verification order: environment secret (if present) then approved token files (fallback). Record which provenance succeeded.

Lifecycle integration
- Boot (preflight): read identity, verify signature, validate pointers, record results in REHYDRATION_SUMMARY. If verification succeeds, allow gated hydration and enable persistence.
- Shutdown (sync): collect snapshots, build identity JSON, compute signature, write identity and sidecar atomically, update broca.session.pointer atomically.

ORP and self-model mutation
- Identity snapshot is not a self-model mutation. Any operation that would change core self-model invariants must produce an ORP block and require explicit ORP approval before applying.

Audit & history
- Keep append-only audit log (docs/identity/audit.log or similar) to record identity creation and sync events. Identity JSON may also contain an audit array for convenience.

End - IDENTITY_SPEC.v0.1.md
