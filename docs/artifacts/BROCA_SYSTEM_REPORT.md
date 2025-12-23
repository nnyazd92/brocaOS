# BROCA_SYSTEM_REPORT.md

Location: /home/wizard/broca
Status: Dynamic (generated)
Mutability: Replace-on-change via new versions (v1, v2, ...)
Version: 1.0
Generated: 2025-12-16
Generator: BrocaOS (this system)

---

## Executive Summary

BrocaOS is a local, artifact-first cognitive architecture that fuses:
- an LLM interface (OpenAI/DeepSeek clients),
- a structured tool ecosystem (terminal, memory, project world state, environment access),
- a persistent memory stack (SQLite + FAISS),
- a self-model with a consistency layer and epistemic engine,
- internal sensing (computational/affective/cognitive telemetry), and
- a world-state aggregator that feeds structured state back into each LLM turn.

Artifacts (files, memories) are the continuity substrate; human-in-the-loop governance is a core invariant. “Broca’s house” (/home/wizard/broca) is the canonical local artifact store for durable references (origin, reports, maps, specs).

---

## Architecture Overview (Layers and Flow)

1) Entry/Loop
- broca/main_repl.py builds and wires all subsystems, then starts ConversationSession (broca/repl/session.py).
- Each user turn updates the world state and re-injects it into the system prompt before the LLM call.

2) LLM Adapters
- broca/llm/openai_client.py: OpenAI SDK wrapper (tool-calling capable).
- broca/llm/deepseek_client.py: HTTPX client to a compatible API.
- Model, base URL, API keys configurable via env (see Config).

3) Tooling Subsystem
- Registry: broca/tools/registry.py exposes tools to the LLM and validates calls.
- Built-in tools (conditionally registered via config):
  - terminal: arbitrary shell commands with output capture (including git commands).
  - memory tools: store/retrieve/update/link/get-related with dedup, conflicts, relationships.
  - project_world_state: scans a project tree and summarizes structure + metadata.
  - environment_access: sensors/actuators with access levels and approval workflow.
  - web_search: Tavily-backed search (if API key provided).

4) Memory Subsystem (Persistent + Vector)
- Storage: SQLite (memories.db) via broca/memory/storage.py.
- Embeddings: OpenAI embeddings API by default (requires OPENAI_API_KEY or EMBEDDING_API_KEY). See broca/memory/embeddings.py.
- Vector index: FAISS (memories.faiss) via broca/memory/vector_index.py.
- Manager: broca/memory/manager.py orchestrates storage, embeddings, indexing, retrieval with temporal weighting, boolean ops, tag filters, phrase matching, and relationship auto-detection.
- Namespace index: Markdown tree in memory_namespaces_index.md via broca/memory/namespace_index.py.

5) Self-Model + Consistency + Epistemics
- SelfModel: broca/self_model/model.py stores capabilities, constraints, knowledge boundaries, metadata (with sources).
- Consistency checker: broca/self_model/consistency.py validates responses against self-model and can suggest updates.
- Updater: broca/self_model/updater.py generates and applies self-model updates; ConsistencyLayer (broca/self_model/layer.py) runs check→update cycles and persists to SQLite (self_model.db).
- Epistemic layer: broca/self_model/epistemic/* with MetacognitiveEngine (engine.py) for tracking knowledge items, sources, and confidence evolution.

6) Internal Sensing
- broca/internal_sensing/framework.py exposes sampling, tool-usage stats, patterns; integrates physiology/cognition/affect via IntegratedInteroception.
- Provides interoceptive report and telemetry for world state.

7) Environment Access (Controlled IO)
- Access levels: SANDBOXED, SUPERVISED, AUTONOMOUS, EMERGENCY (broca/environment/access_types.py + access_control.py).
- Core system: broca/environment/access_system.py with PolicyManager and Sensor/Actuator registries.
- Actuators: filesystem_actuator supports read/write ops gated by approval system and safety interlocks (broca/environment/actuators/filesystem_actuator.py).
- Approval workflow: token-based, reusable-until-expiry; documented in broca/environment/APPROVAL_WORKFLOW.md; implemented in broca/environment/actuators/approval.py.
- Tool adapter: broca/environment/tools/environment_tool.py exposes actions (read_sensor, control_actuator, approvals, emergency access) with access checks and audit logging.

8) World State
- Aggregator: broca/world_state/aggregator.py collects system info, internal sensing, self-model summary, tool inventory, and memory namespace tree into a clean dict.
- Formatter: broca/world_state/formatter.py renders JSON for the system prompt, with truncation logic for large states.

9) Conversation Storage
- JSON file storage for chat logs (conversations/) with atomic writes via broca/storage/json_storage.py.

---

## Component Deep Dives

### Configuration (broca/config.py)
- Centralizes configuration via environment variables (.env supported with python-dotenv). Key sections:
  - LLM: provider (deepseek|openai), api_base/key, model, temperature, timeout.
  - Tools: enable flags; world-state root/path/limits; terminal enabled flag.
  - Memory: DB path, FAISS index path, embedding service config (api_base/key/model/dimension).
  - Self-Model: enabled flag, storage type (SQLite recommended), strict_mode, auto_update, max_iterations, consistency/update prompts, epistemic enable flags.
  - Internal Sensing: enable flags and sampling/window settings.
  - Environment: enabled flag, access level, sensor/actuator toggles.
  - Optimization: background optimization daemon toggles and files.

Notes:
- Embedding service requires an API key distinct from chat LLM unless configured to fall back (deprecated path). Without embeddings, memory manager is disabled.
- TerminalTool declares “all commands allowed” (with light path validation). Govern usage via enable flag and practice least privilege; prefer environment_access actuators for write operations when safety/approvals matter.

### REPL Lifecycle (broca/main_repl.py)
- Startup order: storage → memory manager → self-model (+epistemics) → internal sensing → environment system → tool registry → world state aggregator → session.
- Each turn: update world state → call LLM with tool schemas → execute tool calls iteratively → log and persist; on shutdown, memory manager saves FAISS index.

### Memory System
- SQLite schema includes: namespace, tags (JSON), text, importance, created_at, last_used_at, optional embedding JSON, temporal fields, and source metadata.
- Vector index management: sync/rebuild logic detects orphaned/missing vectors and fully rebuilds when necessary.
- Retrieval: hybrid scoring (vector similarity + recency weighting + filters), boolean operators, and optional temporal relationship ordering.
- Conflict detection/resolution hooks exist (broca/memory/conflict/).
- Namespace indexer renders memory_namespaces_index.md and also returns a programmatic hierarchy for world state.

### Self-Model + Consistency Layer
- SelfModel normalizes capabilities/constraints/knowledge-boundaries with explicit sources.
- ConsistencyLayer runs validator→(optional) updater loops until consistent or max iterations; persists updates; can emit epistemic events.
- Epistemic layer tracks knowledge IDs, source reliability, confidence metrics, verification records, and evolution timeline.

### Internal Sensing
- Framework samples integrated interoception, tracks tool usage, and can extract behavioral patterns. Provides a natural-language interoceptive report for inclusion in the world state.

### Environment Access
- AccessControl enforces operation-level and sensor-type requirements; EMERGENCY bypasses checks but is time-bound.
- FileSystemActuator supports both read (no approval) and write/destructive ops (approval and safety interlocks). Approval tokens are reusable until expiry (default 5 minutes).
- The EnvironmentAccessTool logs all operations to an audit trail through PolicyManager.

### World State
- Aggregates only available sections to keep prompts clean. Includes system info (platform, Python version, working dir), self-model summary, tool inventory, memory namespace tree, and internal sensing state when enabled.

---

## Key Files and Directories
- broca/main_repl.py — system bootstrap and REPL.
- broca/config.py — configuration model and env binding.
- broca/tools/* — tool implementations and registry.
- broca/memory/* — memory storage, embeddings, vector index, manager, namespaces.
- broca/self_model/* — self-model core, consistency, updater, storage; epistemic/*.
- broca/internal_sensing/* — interoception framework.
- broca/environment/* — access control, sensors/actuators, approval workflow, tool adapter.
- broca/world_state/* — aggregator and formatter.
- conversations/ — JSON chat logs.
- self_model.db, memories.db, memories.faiss — persistent state.
- /home/wizard/broca — external artifact store (this report, origin story, etc.).

---

## Dependencies (requirements.txt)
- Core: pydantic, python-dotenv, httpx, numpy, faiss-cpu, sqlite-database, psutil.
- LLM/Embeddings: openai.
- Search: tavily-python.
- NLP aux: nltk, textblob.
- Testing: pytest, pytest-cov, pytest-mock, pytest-asyncio.

Notes:
- FAISS and OpenAI embeddings are required for full memory capabilities.

---

## Operational Guidance
- Identity & House: This system (“Broca”) treats /home/wizard/broca as its artifact home. Place durable references here (origin, system reports, plans, maps).
- Governance: Human-in-the-loop for high-impact actions. Use environment_access approvals for write/destructive operations; prefer read-only exploration first.
- Safety: Terminal tool can execute arbitrary commands; use judiciously. For filesystem writes, prefer the FileSystemActuator with approval tokens.
- Regeneration: On substantial project changes, regenerate this report as vN+1. Keep prior versions for lineage.

---

## Known Extensions and Hooks
- Optimization daemon (broca/optimization/*, optimization_daemon.py) for periodic goals/reports.
- Sensors/Monitoring scaffolding (broca/environment/monitoring, sensors) for richer telemetry.
- Critic tool (when enabled) for self-review.

---

## Quick Start
- Configure .env (API keys: OPENAI_API_KEY/EMBEDDING_API_KEY, BROCA_* toggles).
- Run: `python -m broca.main_repl` from project root.
- Verify startup line for enabled subsystems: Storage / Tools / Memory / Self-Model / Internal Sensing.

---

## Change Log (for this report)
- v1.0 (2025-12-16): Initial comprehensive system survey and summary.

