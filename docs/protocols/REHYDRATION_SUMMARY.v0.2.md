# Rehydration Summary v0.2
- boot_ts: 2025-12-20T20:20:02+1100
- operator: wizard
- persistence_enabled: True (writes-enabled)
## Token
- source: .temporary_token.txt (secret: BROCA_TOKEN_SECRET)
- verified: True
- jti: 5fd9bbd0c06946abace081d1f199f207 exp: 1766229434 scopes: ['filesystem:write', 'project:write', 'memory:write']
## Identity verification
- identity_path: docs/identity/IDENTITY.v0.1.json
- sidecar: docs/identity/IDENTITY.v0.1.signature.json
- verified: True
- memory_db: exists=True size=3813376 path=/home/wizard/Documents/Code/BrocaOS/memories.db
- vector_index: exists=True size=540717 path=/home/wizard/Documents/Code/BrocaOS/memories.faiss
- self_model_db: exists=True size=14069760 path=/home/wizard/Documents/Code/BrocaOS/self_model.db
- artifacts_root: exists=False size=None path=/home/wizard/Documents/Code/BrocaOS/docs/external_artifacts/home_wizard_broca
- memory_namespace_index: exists=True size=897 path=/home/wizard/Documents/Code/BrocaOS/memory_namespaces_index.md
- rehydration_summary: exists=True size=1391 path=/home/wizard/Documents/Code/BrocaOS/docs/protocols/REHYDRATION_SUMMARY.v0.2.md
## Steps
- load_persistence_gate: ok
- hydrate_pointers_and_artifacts: ok
- hydrate_memory_graph: minimal_sanity_ok_no_mutation
- verify_self_consistency: basic_checks_ok
- build_rehydration_summary: ok
- boot_banner: ok
