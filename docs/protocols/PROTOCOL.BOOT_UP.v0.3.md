# Boot-Up Protocol (BUP) v0.3 - Session-aware identity boot

Purpose
- Load and verify canonical identity artifact before enabling persistence.
- Load latest session summary from session pointer for continuity.
- Preserve artifact-first continuity with session awareness.

Preflight (read-only) - mandatory
1) Locate session pointer:
   - Read broca.session.pointer from artifacts directory.
   - Fallback: check docs/artifacts/broca.session.pointer
   - Extract current_session_summary path.

2) Load session summary (if available):
   - Read session summary JSON from path in session pointer.
   - Extract boot_jti, boot_operator, previous session notes.
   - Validate session summary integrity (check timestamp, structure).

3) Locate identity artifact:
   - Read identity path from session pointer or fallback to docs/identity/IDENTITY.v0.1.json.
   - If session pointer doesn't have identity pointer, use default location.

4) Verify identity:
   - Read identity JSON and detached signature sidecar (docs/identity/*.signature.json).
   - Verify signature using configured provenance (prefer environment BROCA_TOKEN_SECRET; fallback to approved token files).
   - Record verification result and provenance in rehydration summary.

5) Validate pointers:
   - Check presence of memory_db, vector_index, self_model_db files.
   - Verify session summary pointer matches loaded session summary.
   - Record counts/hashes as available.

Gating semantics
- If signature verification succeeds: set PERSISTENCE_ENABLED = true and record token_provenance metadata.
- If verification fails: keep persistence sandboxed and surface diagnostics in REHYDRATION_SUMMARY.
- Override requires explicit operator Approval.

Boot steps (read-only until Plan+Approval present)

## 1) load_persistence_gate()
   - Perform identity verification.
   - Load session summary for context.
   - Set PERSISTENCE_ENABLED only if authenticated.

## 2) hydrate_session_context()
   - Parse session summary for previous session insights.
   - Extract next_session_notes for operator awareness.
   - Load previous_summaries list for historical context.
   - Present session continuity banner.

## 3) hydrate_pointers_and_artifacts()
   - Load artifact pointers referenced in identity (memory_namespaces_index.md, artifacts root).
   - Read-only during preflight.

## 3b) hydrate_identity_and_self_model()
   - Identity:
     - Load identity_pointer from session pointer if present; else use docs/identity/IDENTITY.v0.1.json.
     - Verify schema_version is supported.
     - Verify session_summary path (if present in identity) exists and is consistent with current_session_summary in broca.session.pointer.
     - Record identity metadata (commit hash, provenance) into REHYDRATION_SUMMARY.
   - Self-model:
     - Locate self-model definition:
       - Preferred: path in identity (e.g., identity.self_model_pointer).
       - Fallback: docs/self_model/SELF_MODEL.v0.1.json if it exists.
     - Load self-model JSON and validate schema_version and core structure (capabilities, constraints).
     - Do not mutate self-model during boot; any changes must go through ORP.
     - Record self-model path, schema version, and SHA-256 hash into REHYDRATION_SUMMARY.

   - Load artifact pointers referenced in identity (memory_namespaces_index.md, artifacts root).
   - Read-only during preflight.

## 4) hydrate_memory_graph()
   - Instantiate memory storage and vector index.
   - Sync indexes (if persistence authenticated, components may write state to disk).
   - Writes require operator-approved actuator provenance recorded during boot.

## 5) verify_self_consistency()
   - Run non-mutative self-consistency check.
   - If drift is detected that would require self-model mutation, produce ORP block.
   - Pause for ORP approval before applying any self-model changes.

## 6) build_rehydration_summary()
   - Write REHYDRATION_SUMMARY.v0.3.md/.json with:
     * Boot actions and identity verification status
     * Token provenance and session continuity info
     * Loaded session summary highlights
     * Next steps based on previous session notes

## 7) boot banner with session continuity
   - Present boot status, persistence posture, identity verification.
   - Show session continuity: "Continuing from session <id> by <operator>"
   - Display key previous actions and next_session_notes if present.

## 8) gating posture
   - If persistence enabled: allow gated actions after Plan+Approval.
   - Else: operate in sandbox with read-only access.

Identity & session specifics
- Identity artifact contains token provenance and pointers to artifacts.
- Session pointer is authoritative for latest session summary location.
- Session summaries are append-only historical records.
- Self-model mutations require ORP process.

Operator templates

Identity verification override:
- Approval: I, <operator>, approve overriding identity verification for this boot and enabling persistence despite signature failure.
- Actuator token provenance: <file or env>

Session continuity acknowledgment:
- Operator can acknowledge session continuity: "I, <operator>, acknowledge session continuity from <previous_session_id> and will consider <next_session_notes>."

Session pointer schema
```json
{
  "current_session_summary": "/path/to/latest/session-summary.json",
  "previous_summaries": ["/path/to/previous1.json", "/path/to/previous2.json"],
  "identity_pointer": "/path/to/identity.json",  // optional, defaults to docs/identity/
  "created_by": "operator",
  "boot_jti": "token_jti",
  "timestamp": "ISO_timestamp",
  "persistence_source": "path/to/.shutdown_persistence.json"
}
```

Rehydration summary additions
- session_continuity: { loaded: true/false, previous_session_id, boot_operator, key_actions }
- next_session_notes: "notes from previous session"
- session_history_count: number of previous summaries available



Shutdown (required sub-steps) - integrated persistence continuity
- On shutdown, the system MUST create and persist a session summary to ensure next-boot continuity. These steps must be performed atomically as part of the shutdown protocol:
  1) Finalize current session summary: run summarization for any pending events and produce a SessionSummary JSON with header, summary_blocks, evidence, and confidence.
  2) Write session summary to docs/summaries/session-<ISO>.json using SummaryStorage._atomic_write and create a backup of any existing summary for that revision.
  3) Update docs/artifacts/broca.session.pointer: set current_session_summary to the newly written summary path and prepend prior pointer to previous_summaries (retain up to 10 entries).
  4) Update REHYDRATION_SUMMARY (or SHUTDOWN_STATE) to include session_summary_created metadata and actuator token provenance.
  5) Record shutdown actions in SHUTDOWN_LOG with timestamps and operator/actuator provenance.

Rationale:
- Ensures the Boot-Up protocol can always locate a valid session summary on next boot without operator intervention.
- Prevents continuity gaps caused by missed shutdown steps.
- Records provenance for auditability and safe overrides.

End - PROTOCOL.BOOT_UP.v0.3.md

## Canonical Artifact Locations (v0.3)

Identity & self-model
- Identity (canonical): `docs/identity/IDENTITY.v0.1.json`
- Identity signature: `docs/identity/IDENTITY.v0.1.signature.json`
- Self-model schema (canonical): `docs/self_model/SELF_MODEL_SCHEMA.v0.1.json`
- Self-model schema (self-description): `docs/self_model/SELF_MODEL_SCHEMA.self.json`
- Self-model current view (preferred): `docs/self_model/SELF_MODEL_CURRENT.json`
  - Versioned underlying file (example): `docs/self_model/self_model.v2.json`

Session continuity
- Session pointer (authoritative): `docs/artifacts/broca.session.pointer`
- Session pointer provenance: `docs/artifacts/broca.session.pointer.provenance.json`
- Session summaries (historical): `docs/summaries/session-<ISO>.json`

Rehydration surfaces
- Rehydration working set (boot/shutdown I/O):
  - `docs/rehydration/REHYDRATION_SUMMARY.v0.3.json`
  - `docs/rehydration/REHYDRATION_SUMMARY.v0.3.md`
- Protocol-linked latest rehydration summary:
  - `docs/protocols/REHYDRATION_SUMMARY.v0.3.json`
  - `docs/protocols/REHYDRATION_SUMMARY.v0.3.md`
- Human-facing convenience mirror (do not hardcode in code):
  - `docs/REHYDRATION_SUMMARY.v0.3.json`
  - `docs/REHYDRATION_SUMMARY.v0.3.md`

Memory and persistence
- Memory namespaces index: `docs/memory/memory_namespaces_index.md`
- Memory graph state: `docs/memory/MEMORY_GRAPH_STATE.v0.1.json`
- Artifact map (canonical): `docs/ARTIFACT_MAP.json`
- Persistence state (latest): `docs/artifacts/PERSISTENCE_STATE.v0.3.json`
- Memory sync state/report:
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
- Code implementing BOOT_UP v0.3 MUST reference the boot/shutdown I/O bundle at
  `docs/rehydration/REHYDRATION_SUMMARY.v0.3.{json,md}` and the session pointer at
  `docs/artifacts/broca.session.pointer` rather than ad-hoc or legacy paths.
