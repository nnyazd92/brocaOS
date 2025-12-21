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

End - PROTOCOL.BOOT_UP.v0.3.md
