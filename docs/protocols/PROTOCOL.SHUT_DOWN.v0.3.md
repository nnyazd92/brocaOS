# Shutdown Protocol (SDP) v0.3 - Session-aware persistence shutdown

Purpose
- Ensure that each shutdown produces a canonical SessionSummary JSON.
- Advance the broca.session.pointer so BOOT_UP can reliably locate the latest session.
- Persist token provenance and artifact pointers for auditability.
- Optionally run a memory synchronization pass to validate and back up pointers.

## 0) Preconditions

- Valid actuator token available (e.g. .temporary_token.txt) with filesystem:write and project:write scopes.
- BOOT_UP v0.3 has been run for this session and identity verification status is known.

## 1) Verify actuator token & record provenance

1. Verify actuator token validity via environment controller.
2. Extract boot_jti, subject, and scopes.
3. Record token provenance in shutdown state:
   - .shutdown_persistence.json at repo root.
   - docs/logs/SHUTDOWN_LOG.jsonl (on first use).

## 2) Memory Synchronization During Shutdown

Purpose: Ensure on-shutdown that memory pointers and artifact pointers are validated, backed up, and persisted so that subsequent boots restore consistent state.

Steps:
1. Create VCS snapshot (pre-shutdown snapshot) to allow rollback.
2. Run a memory->artifact validation pass (dry-run): retrieve pointer-like memories, resolve file paths, compute checksums and sizes, and detect missing/stale pointers.
3. Create backups for any artifacts that will be modified or used for restoration in ./backup/shutdown_sync/<timestamp>/.
4. Apply approved memory updates (metadata alignment) and optionally create symlinks/copies for moved artifacts. All writes must be recorded with exact commands in the shutdown log and committed to VCS.
5. Persist a MACHINE-READABLE shutdown sync state to ./docs/protocols/MEMORY_SYNC_STATE.json and a human-readable report to ./docs/protocols/MEMORY_SYNC_REPORT.md.
6. If any medium/high-risk changes were performed, record them in the SHUTDOWN log and require operator confirmation before completing shutdown.

Notes:
- All non-read writes require an explicit actuator token and operator approval. This section formalizes the memory sync steps we executed on 2025-12-22.

## 3) Session summarization (required)

1. Collect session context:
   - session_start, session_end (UTC ISO).
   - boot_jti, boot_operator.
   - key_actions (ordered list).
   - outcome_summary (short text).
   - memory_changes {added, updated, deleted}.
   - next_session_notes.
2. Construct a SessionSummary v0.1 object:
   ```json
   {
     "schema_version": "v0.1",
     "session_id": "session-<ISO>",
     "boot_jti": "<boot_jti>",
     "boot_operator": "<operator>",
     "session_start": "<ISO>",
     "session_end": "<ISO>",
     "key_actions": ["..."],
     "outcome_summary": "<string>",
     "memory_changes": {"added": 0, "updated": 0, "deleted": 0},
     "next_session_notes": "<string>",
     "created_by": "assistant|operator",
     "timestamp": "<ISO>"
   }
   ```
3. Write SessionSummary to:
   - docs/summaries/session-<ISO>.json
   - using SummaryStorage._atomic_write semantics:
     - Write to temp file.
     - fsync.
     - Rename to final.

## 4) Update session pointer (broca.session.pointer)

1. Load docs/artifacts/broca.session.pointer if it exists; otherwise initialize a fresh pointer.
2. Let new_summary_path = "docs/summaries/session-<ISO>.json".
3. Let old_current = pointer.current_session_summary (if present).
4. Compute new previous_summaries:
   - Prepend old_current if non-null.
   - Append up to the last 9 entries from existing previous_summaries.
5. Write updated pointer:
   ```json
   {
     "current_session_summary": "docs/summaries/session-<ISO>.json",
     "previous_summaries": ["<old_current>", "..."],
     "identity_pointer": "docs/identity/IDENTITY.v0.1.json",
     "created_by": "<operator|assistant>",
     "boot_jti": "<boot_jti>",
     "timestamp": "<ISO>",
     "persistence_source": ".shutdown_persistence.json"
   }
   ```

## 5) Update shutdown persistence state

Write .shutdown_persistence.json at repo root:

```json
{
  "last_shutdown": "<ISO>",
  "session_summary": "docs/summaries/session-<ISO>.json",
  "actuator_token_provenance": ".temporary_token.txt"
}
```

## 6) Update rehydration / shutdown summaries

1. Update docs/artifacts/REHYDRATION_SUMMARY.v0.3.json or docs/protocols/SHUTDOWN_SUMMARY.v0.3.json with:
   - session_summary_created: true
   - session_summary_path
   - pointer_state (snapshot of broca.session.pointer)
   - token_provenance
2. Optionally append a one-line JSON record to:
   - docs/logs/SHUTDOWN_LOG.jsonl.

## 7) Finalize shutdown

- Ensure all writes are flushed and committed.
- Record final status "shutdown_completed" in SHUTDOWN_STATE.v0.1.json (if used).
- Halt execution.

End - PROTOCOL.SHUT_DOWN.v0.3.md

## Canonical Artifact Locations (v0.3)

Session summaries & pointers
- Session summaries (canonical): `docs/summaries/session-<ISO>.json`
- Session pointer (authoritative): `docs/artifacts/broca.session.pointer`
- Session pointer provenance: `docs/artifacts/broca.session.pointer.provenance.json`
- Shutdown persistence state: `.shutdown_persistence.json` (repo root)

Identity & self-model (for reference)
- Identity (canonical): `docs/identity/IDENTITY.v0.1.json`
- Self-model current view: `docs/self_model/SELF_MODEL_CURRENT.json`

Rehydration & shutdown summaries
- Rehydration working set (boot/shutdown I/O):
  - `docs/rehydration/REHYDRATION_SUMMARY.v0.3.json`
  - `docs/rehydration/REHYDRATION_SUMMARY.v0.3.md`
- Protocol-linked rehydration summary:
  - `docs/protocols/REHYDRATION_SUMMARY.v0.3.json`
  - `docs/protocols/REHYDRATION_SUMMARY.v0.3.md`
- Shutdown summaries:
  - Current protocol-linked: `docs/protocols/SHUTDOWN_SUMMARY.v0.3.json`
  - Historical / working: `docs/rehydration/SHUTDOWN_SUMMARY.v0.1.md`

Memory & persistence sync
- Memory namespaces index: `docs/memory/memory_namespaces_index.md`
- Memory graph state: `docs/memory/MEMORY_GRAPH_STATE.v0.1.json`
- Artifact map: `docs/ARTIFACT_MAP.json`
- Persistence state (latest): `docs/artifacts/PERSISTENCE_STATE.v0.3.json`
- Memory sync artifacts:
  - `docs/artifacts/MEMORY_SYNC.v0.1.json`
  - `docs/artifacts/MEMORY_SYNC.v0.1.md`
  - `docs/protocols/MEMORY_SYNC_STATE.json`
  - `docs/protocols/MEMORY_SYNC_REPORT.md`

Boot/shutdown markers & logs
- Boot marker: `docs/BOOT_MARKER.txt`
- Shutdown marker: `docs/SHUTDOWN_MARKER.txt`
- Shutdown state (canonical): `docs/SHUTDOWN_STATE.v0.1.json`
- Boot log (structured): `docs/artifacts/BOOT_LOG.v0.3.txt`
- Shutdown log (structured): `docs/artifacts/SHUTDOWN_LOG.v0.1.txt`
- Detailed shutdown reports: `docs/artifacts/logs/shutdown/SHUTDOWN_*.{md,json}`

Implementation note
- Code implementing SHUT_DOWN v0.3 MUST:
  - Write the canonical SessionSummary to `docs/summaries/session-<ISO>.json`.
  - Advance `docs/artifacts/broca.session.pointer` according to this protocol.
  - Update the rehydration working set at `docs/rehydration/REHYDRATION_SUMMARY.v0.3.{json,md}`
    and, as needed, the protocol-linked `docs/protocols/REHYDRATION_SUMMARY.v0.3.{json,md}`
    and `docs/protocols/SHUTDOWN_SUMMARY.v0.3.json`.
