# BrocaOS — local, auditable cognitive REPL

BrocaOS is a local, safety-first cognitive REPL and research platform. It
integrates an LLM-driven conversational runtime with gated environment access,
artifact-first continuity, a self-model, and auditable persistence (actuator-token gated).

> TL;DR: a safe, auditable, and developer-friendly REPL for building agent
> workflows locally. Designed for auditability, governance, and fast iteration.

## Key features

- REPL interface for conversation + tool execution (terminal, memory, web search, critic).
- Safety & governance: actuator token verification, preflight boot protocol, ORP-style change gating.
- Artifact-first continuity: rehydration summaries, session pointers, and versioned self-models.
- Self-model system with versioned storage (SQLite) and migration tooling; v2.0.0 artifact available.
- Tests and automation: integration tests for REPL and storage; migration script & DB migration path.

## Quick start (local development)

Prereqs: Python 3.13+, git, gh (optional for PRs)

1. Clone the repo

   git clone https://github.com/nnyazd92/brocaOS.git
   cd brocaOS

2. Install dependencies

   python -m pip install -r requirements.txt

3. Prepare actuator token

   - Place an approval token at `.temporary_token.txt` (or export `BROCA_TOKEN_SECRET` in env).
   - Tokens are required for any persistence/state-changing operations.

4. Run the REPL

   python -m broca.main_repl

Use `/reset` to clear session context and `/exit` to quit.

## Boot & persistence

- Boot performs a read-only preflight, verifies identity artifacts, and then gates
  persistence behind an approved actuator token.
- Writes (session summaries, rehydration artifacts, self-model dumps) include token
  provenance (token jti) and are snapshot-backed with git.

See `docs/protocols/PROTOCOL.BOOT_UP.v0.3.md` for full protocol details.

## Self-model & migration

- Self-model versions are stored in `self_model.db` (SQLite) and optionally
  serialized to `docs/artifacts/`.
- Migration tooling:
  - `broca/self_model/migrations/migrate_to_v2.py` — deterministic migration to v2.0.0
- A v2 artifact was created at `docs/artifacts/self_model.v2.json` and a DB row was
  inserted as part of the migration (check migration PRs for details).

## Development & tests

Run the test suite with coverage and branch reporting:

```
pytest --cov=broca --cov-branch --cov-report=term-missing
```

Memory modules should maintain at least 85% coverage (including branch coverage); use `scripts/run_mutation_tests.sh` to execute the coverage-aware mutation suite for `broca/memory`.

Key tests: `broca/tests/test_repl_integration.py`, `broca/tests/test_self_model_sqlite_storage.py`.

## Contributing

- Follow actuator/ORP conventions: state-changing PRs that write artifacts must
  include token provenance and an ORP-style migration note.
- Open issues and PRs; assign to `nnyazd92` for quick review.

## Audit & provenance

- Non-read operations are recorded using git snapshots, REHYDRATION_SUMMARY entries,
  DB backups, and pointer memories in `self.schema.*` namespaces.
- Memory namespaces (e.g., `user.schema.nick`, `self.schema.self`) store terse pointers
  that reference richer on-disk artifacts.

## Where to look next

- `docs/protocols/PROTOCOL.BOOT_UP.v0.3.md`
- `docs/artifacts/self_model.v2.json`
- `broca/self_model/migrations/migrate_to_v2.py`

## License & credits

- Add your license here (MIT/Apache/etc).
