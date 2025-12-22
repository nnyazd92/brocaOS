


## Memory Synchronization During Shutdown (added by BrocaOS 2025-12-22T22:29:32Z)

Purpose: Ensure on-shutdown that memory pointers and artifact pointers are validated, backed up, and persisted so that subsequent boots restore consistent state.

Steps:
1. Verify actuator token validity (token file: .temporary_token.txt) and record token JTI in shutdown log.
2. Create VCS snapshot (pre-shutdown snapshot) to allow rollback.
3. Run a memory->artifact validation pass (dry-run): retrieve pointer-like memories, resolve file paths, compute checksums and sizes, and detect missing/stale pointers.
4. Create backups for any artifacts that will be modified or used for restoration in ./backup/shutdown_sync/<timestamp>/.
5. Apply approved memory updates (metadata alignment) and optionally create symlinks/copies for moved artifacts. All writes must be recorded with exact commands in the shutdown log and committed to VCS.
6. Persist a MACHINE-READABLE shutdown sync state to ./docs/protocols/MEMORY_SYNC_STATE.json and a human-readable report to ./docs/protocols/MEMORY_SYNC_REPORT.md.
7. If any medium/high-risk changes were performed, record them in the SHUTDOWN log and require operator confirmation before completing shutdown.
8. Finalize shutdown: record final status 'shutdown_completed' in SHUTDOWN_STATE.v0.1.json and commit changes.

Notes:
- All non-read writes require an explicit actuator token and operator approval. This section formalizes the memory sync steps we executed on 2025-12-22.

