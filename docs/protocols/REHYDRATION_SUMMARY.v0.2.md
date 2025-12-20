# Rehydration Summary v0.2
- boot_ts: 2025-12-20T21:44:54+1100
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
- artifacts_root: exists=True size=None path=/home/wizard/Documents/Code/BrocaOS/docs/artifacts
- memory_namespace_index: exists=True size=897 path=/home/wizard/Documents/Code/BrocaOS/memory_namespaces_index.md
- rehydration_summary: exists=True size=1391 path=/home/wizard/Documents/Code/BrocaOS/docs/protocols/REHYDRATION_SUMMARY.v0.2.md
## Memory status
- total: 88 with_embedding: 88 without_embedding: 0
## Vector index status
- path: /home/wizard/Documents/Code/BrocaOS/memories.faiss exists: True size: 540717
## Artifacts inventory
- dir: /home/wizard/Documents/Code/BrocaOS/docs/artifacts count: 6
- ARTIFACT_MAP.json: size=1296 sha256=bd96f05dffed...
- ARTIFACT_MAP.json.provenance.json: size=344 sha256=6ae213afba3e...
- broca.artifacts: size=693 sha256=dd7a29b3bc6f...
- broca.artifacts.provenance.json: size=340 sha256=b768eb91daad...
- broca.session.pointer: size=271 sha256=9f5b6bfeac05...
- broca.session.pointer.provenance.json: size=346 sha256=978c38982710...
