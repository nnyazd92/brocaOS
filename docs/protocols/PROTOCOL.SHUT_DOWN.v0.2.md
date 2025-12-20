# Shutdown Protocol (SHP) v0.2 - Identity synchronization

Purpose
- On shutdown (or explicit sync), produce a canonical identity artifact that captures authoritative pointers and summaries for persistent subsystems (memories, vector index, self-model summary, artifacts) and sign it so future boots can verify continuity.

Shutdown sync steps (state-changing - requires Plan+Approval and actuator provenance)
1) Quiesce writers: stop or pause subsystems that may write to persistent storage and flush pending writes to disk.
2) Collect authoritative snapshots:
   - memory DB path and summary: total count and optional per-namespace counts (memory_namespaces_index.md)
   - vector index path and count (memories.faiss)
   - self-model summary pointer (non-mutative snapshot)
   - artifacts root summary (file counts; optional hashes for critical artifacts)
   - git repository snapshot (commit id) if available
   - non-secret token provenance metadata (env or file location, token_id/exp/scopes if available)
3) Build canonical identity JSON following IDENTITY_SPEC.v0.1 rules (canonicalization: json.dumps(..., separators=(',',':'), sort_keys=True)). Include new audit entry.
4) Compute HMAC-SHA256 signature over canonical bytes using BROCA_TOKEN_SECRET (or approved token source). Store signature metadata in a detached sidecar (IDENTITY.v0.1.signature.json).
5) Write identity JSON and sidecar atomically (write tmp file then os.replace into docs/identity/). Optionally update broca.session.pointer atomically to point to new identity artifact.
6) Append an audit record in an append-only audit log.
7) If any step fails, log an error and perform safe shutdown without partial identity updates.

Conflict & merge policy
- Identity is a summary and authoritative pointers reflect persistent storage. If incoming identity artifacts conflict with storage reality, storage is authoritative and identity will be updated at shutdown.
- For multiple identity artifacts, perform a three-way merge (base/local/remote) and produce an ORP block for any change to self-model or core invariants.

Operator templates
- To authorize shutdown sync and signing:
  - Approval: I, <operator>, approve the Shutdown Sync Plan and authorize BrocaOS to write the identity artifact and signature sidecar.
  - Actuator token provenance: <file or env>

End - PROTOCOL.SHUT_DOWN.v0.2.md
