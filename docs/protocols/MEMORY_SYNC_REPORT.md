# MEMORY SYNC REPORT

generated_at: 2025-12-22T22:29:32Z
operator: nick.yazdani
actuator_token_jti: 1bf8e384cc1345a2a0c055bbe32a6d4e

summary:
- Performed dry-run validation of 20 memories referencing artifacts under ./docs
- Applied low-risk memory metadata updates for memory ids: [22,14,5,70,73,76,86,87]
- Performed medium-risk restores: created symlinks and copied artifact map
- Backups created at: ./backup/memory_sync/2025-12-22T22-17-00Z

commits:
- pre-sync snapshot: 502d2a558a09372502f595f4fde94ba024858496
- boot writes commit: a5271d4
- medium-risk restores commit: f8745e4

artifacts_touched:
- ./docs/operators/OPERATORS_GUIDE.md
- ./docs/ARTIFACT_MAP.json
- ./docs/artifacts/BROCA_SYSTEM_REPORT.md
- ./docs/identity/IDENTITY.v0.1.json

memories_updated: [22,14,5,70,73,76,86,87]

notes:
- Version control commit for medium-risk restores: f8745e4
- All memory updates are reversible via functions.update_memory

