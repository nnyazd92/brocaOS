# BrocaOS

BrocaOS is an alpha cognitive architecture for building agents that do more than chat:
- reason over explicit tools,
- persist memory across sessions,
- monitor internal state,
- enforce governance on state-changing actions,
- and improve behavior through RL and structured feedback.

If you want an LLM app that behaves like an inspectable, testable runtime instead of a prompt wrapper, this repo is built for that.

## Why This Project Hits Different

- Hybrid cognition: symbolic reasoning, tool orchestration, and reinforcement learning in one runtime.
- Persistent memory graph: semantic retrieval plus typed relationships (`supports`, `elaborates`, `contradicts`, etc.).
- Internal sensing + world state: built-in telemetry for confidence, coherence, dissonance, and runtime context.
- Governed actuation: policy, gating, and token-based approvals for non-read actions.
- Production surfaces: terminal REPL, FastAPI service, and optimization daemon.

## What You Can Run Right Now

- REPL runtime: `python -m broca.main_repl`
- Web API: `python -m broca.web_api --host 127.0.0.1 --port 8000`
- Optimization daemon: `python -m broca.optimization_daemon`
- Token CLI: `python -m broca.token_auth.cli generate`

## 5-Minute Quickstart

```bash
git clone https://github.com/nnyazd92/brocaOS.git
cd brocaOS

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env:
# - Set ONE chat provider key (GEMINI_API_KEY or OPENAI_API_KEY or DEEPSEEK_API_KEY or ANTHROPIC_API_KEY)
# - Optional: EMBEDDING_API_KEY for full memory vector features
# - Optional: TAVILY_API_KEY for web search provider
```

Run REPL:
```bash
python -m broca.main_repl
```

Run Web API:
```bash
python -m broca.web_api --host 127.0.0.1 --port 8000
```

Health check:
```bash
curl http://127.0.0.1:8000/api/healthz
```

## Project Structure (Walkthrough)

Top-level:
- `broca/`: core runtime modules (reasoning, memory, tools, RL, API, REPL, governance).
- `broca/tests/`: primary test suite for core runtime and subsystems.
- `tests/`: additional project-level tests and property tests.
- `docs/`: protocols, governance docs, whitepapers, reports, research artifacts.
- `benchmarks/`: benchmark harnesses (including procedural emergence benchmark).
- `scripts/`: automation for mutation testing, benchmarking, migration, and ops tasks.
- `infra/`: Terraform and deployment manifests.
- `data/`: runtime state, logs, reward traces, policy buffers, and shared world state.
- `models/`: learned model artifacts (RL policy checkpoints, etc.).

Core architecture under `broca/`:
- `broca/reasoning`: production rules, recursive reasoning, dissonance handling, reward signal modeling.
- `broca/rl`: PPO policy training, online policy logic, reward shaping, telemetry.
- `broca/memory`: storage, embeddings, FAISS index, memory relationships, conflict handling.
- `broca/world_state`: aggregation/formatting of system + cognitive state with size controls.
- `broca/internal_sensing`: affective/cognitive signal extraction and response analysis.
- `broca/tools`: primitive macro toolset (`READ_FILE`, `EXECUTE`, `WEB_SEARCH`, `SOLVE`, `DONE`, etc.).
- `broca/repl`: session loop, response guardrails, tool status rendering.
- `broca/web_api.py`: FastAPI server with chat, memory, governance, metrics, and tooling endpoints.
- `broca/token_auth`: JWT-like token issuance/verification for gated actions.

## Proof, Not Promises: Quality Stack

This repo is heavily test-instrumented:
- 455 Python test files across `broca/tests` + `tests`
- property-based tests
- mutation testing
- fault injection tests
- golden trace replay tests
- branch coverage configuration

Run core tests + branch coverage:
```bash
python -m pytest --cov=broca --cov-branch --cov-report=term-missing
```

Run mutation tests:
```bash
bash scripts/run_mutation_tests.sh
```

Run property-focused tests:
```bash
python -m pytest tests/property broca/tests -k property
```

Run fault-injection tests:
```bash
python -m pytest broca/tests tests -k fault_injection
```

Run golden trace/replay tests:
```bash
python -m pytest broca/tests tests -k "golden or replay"
```

## Governance and Safety

- Governance baseline: `docs/GOVERNANCE.md`
- Token auth guide: `broca/token_auth/BROCA_TOKEN_GUIDE.md`
- Policy and audit artifacts: `data/governance/`
- Read-only / gated tool modes are configurable via environment settings in `broca/config.py`

## Benchmarks and Research Artifacts

- Procedural emergence benchmark: `benchmarks/procedural_emergence/README.md`
- Formal and technical theory docs: `docs/research/`
- Operational/capability status docs: `docs/STATUS.md`, `docs/capabilities_report.md`

## Recommended Next Reads

1. `docs/operators/OPERATORS_GUIDE.md`
2. `docs/GOVERNANCE.md`
3. `docs/protocols/PROTOCOL.BOOT_UP.v0.3.md`
4. `docs/protocols/PROTOCOL.SHUT_DOWN.v0.3.md`
5. `broca/tools/primitive_toolset.py`

## Status

Alpha, actively evolving, and designed for fast iteration with high observability.

## License

See `LICENSE`.
