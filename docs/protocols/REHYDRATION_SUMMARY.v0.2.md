# Rehydration Summary v0.2
- boot_ts: 2025-12-21T12:01:11.716494
- operator: wizard
- persistence_enabled: True (writes-enabled)
- override: Operator-approved identity verification override

## Token
- source: .temporary_token.txt (override approved)
- verified: True
- jti: c6136f2c84204c06bd7e39b28679ae39 exp: 1766279046 scopes: ['filesystem:write', 'project:write', 'memory:write']
- sub: nick.yazdani name: Nick Yazdani

## Identity verification
- identity_path: docs/identity/IDENTITY.v0.1.json
- sidecar: docs/identity/IDENTITY.v0.1.signature.json
- verified_with_env: False (BROCA_TOKEN_SECRET signature mismatch)
- verified_with_override: True (operator-approved)
- signature: UHbfWUyvQdEOOb9exkFKj-CXJQ9E_r72eRP-sdOgrZ4
- override_token_jti: c6136f2c84204c06bd7e39b28679ae39

## Pointer status
- memory_db: EXISTS size=3813376 path=/home/wizard/Documents/Code/BrocaOS/memories.db
- vector_index: EXISTS size=540717 path=/home/wizard/Documents/Code/BrocaOS/memories.faiss
- self_model_db: EXISTS size=14069760 path=/home/wizard/Documents/Code/BrocaOS/self_model.db
- artifacts_root: EXISTS size=None path=/home/wizard/Documents/Code/BrocaOS/docs/artifacts
- memory_namespace_index: EXISTS size=897 path=/home/wizard/Documents/Code/BrocaOS/memory_namespaces_index.md
- rehydration_summary: EXISTS size=1740 path=/home/wizard/Documents/Code/BrocaOS/docs/protocols/REHYDRATION_SUMMARY.v0.2.md
