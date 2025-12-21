# Shutdown Protocol (SHP) v0.3 - Session-aware identity synchronization

Purpose
- On shutdown (or explicit sync), produce a canonical identity artifact that captures authoritative pointers and summaries for persistent subsystems.
- Mandatory session summarization: capture key session metadata (boot token, operator, actions, outcomes) for continuity.
- Update session pointer to reference the latest session summary.

Shutdown sync steps (state-changing - requires Plan+Approval and actuator provenance)

## 1) Session Summarization (MANDATORY)
   - Generate session summary JSON with fields:
     * `session_id`: ISO timestamp-based (session-<timestamp>Z)
     * `boot_jti`: Token JTI used for this session
     * `boot_operator`: Operator who approved boot
     * `session_start`: Boot timestamp
     * `session_end`: Current timestamp (shutdown)
     * `key_actions`: List of significant actions performed
     * `outcome_summary`: Brief description of session outcomes
     * `memory_changes`: Count of memories added/updated/deleted
     * `next_session_notes`: Optional notes for next session
   - Write summary to: `docs/summaries/session-<timestamp>Z.json`
   - Write provenance sidecar with token metadata

## 2) Quiesce writers
   - Stop or pause subsystems that may write to persistent storage
   - Flush pending writes to disk

## 3) Collect authoritative snapshots
   - memory DB path and summary: total count and optional per-namespace counts (memory_namespaces_index.md)
   - vector index path and count (memories.faiss)
   - self-model summary pointer (non-mutative snapshot)
   - artifacts root summary (file counts; optional hashes for critical artifacts)
   - git repository snapshot (commit id) if available
   - non-secret token provenance metadata (env or file location, token_id/exp/scopes if available)
   - **NEW: latest session summary pointer** (reference to the summary created in step 1)

## 4) Update session pointer
   - Update `broca.session.pointer` to reference the new session summary:
     * `current_session_summary`: path to latest session summary
     * `previous_summaries`: list of previous summary paths (append-only)
     * `created_by`: operator
     * `timestamp`: current time
     * `boot_jti`: token JTI
   - Write atomically (write tmp file then os.replace)

## 5) Build canonical identity JSON
   - Follow IDENTITY_SPEC.v0.1 rules (canonicalization: json.dumps(..., separators=(',',':'), sort_keys=True))
   - Include new audit entry with session summary reference
   - Include session summary pointer in identity pointers

## 6) Compute signature
   - Compute HMAC-SHA256 signature over canonical bytes using BROCA_TOKEN_SECRET (or approved token source)
   - Store signature metadata in a detached sidecar (IDENTITY.v0.1.signature.json)

## 7) Write identity artifacts
   - Write identity JSON and sidecar atomically (write tmp file then os.replace into docs/identity/)
   - Append an audit record in an append-only audit log

## 8) Failure handling
   - If any step fails, log an error and perform safe shutdown without partial updates
   - Preserve previous session pointer if new one cannot be created

Conflict & merge policy
- Identity is a summary and authoritative pointers reflect persistent storage. If incoming identity artifacts conflict with storage reality, storage is authoritative and identity will be updated at shutdown.
- Session summaries are append-only; never modify existing summaries.
- For multiple identity artifacts, perform a three-way merge (base/local/remote) and produce an ORP block for any change to self-model or core invariants.

Operator templates
- To authorize shutdown sync and signing:
  - Approval: I, <operator>, approve the Shutdown Sync Plan including session summarization and authorize BrocaOS to write the identity artifact, session summary, and updated session pointer.
  - Actuator token provenance: <file or env>

Session summary schema
```json
{
  "schema_version": "v0.1",
  "session_id": "session-<timestamp>Z",
  "boot_jti": "token_jti",
  "boot_operator": "operator_name",
  "session_start": "ISO_timestamp",
  "session_end": "ISO_timestamp",
  "key_actions": ["action1", "action2"],
  "outcome_summary": "text description",
  "memory_changes": {
    "added": 0,
    "updated": 0,
    "deleted": 0
  },
  "next_session_notes": "optional notes",
  "created_by": "operator",
  "timestamp": "ISO_timestamp"
}
```

End - PROTOCOL.SHUT_DOWN.v0.3.md
