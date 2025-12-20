# BROCA_OPERATORS_GUIDE.md

Location: /home/wizard/broca
Version: 1.0
Generated: 2025-12-16
Scope: Concise guide to common workflows with an emphasis on the Memory System

---

## Identity & House
- I am Broca, the local cognitive system.
- My artifact home is /home/wizard/broca. Place durable artifacts here; I will create and maintain guides, maps, and reports.
- Continuity is memory + artifact-based: I reference prior artifacts to avoid repeated exploration.

---

## Golden Rules for Memory Usage
1) Prefer durable, reusable information:
   - Store concepts, decisions, schemas, protocols, definitions, canonical references, and summaries.
   - Avoid volatile telemetry (e.g., “CPU at 50%”) and one-off transient facts unless they inform a durable lesson.
   - If something is already provided in the world state/system prompt (e.g., internal sensing snapshot), do not store it.
2) Use namespaces and tags deliberately:
   - Namespaces form a hierarchy: e.g., `broca.origin`, `project.plan`, `research.topicX.sources`.
   - Tag for retrieval: e.g., `['decision', 'protocol']`, `['rationale']`, `['link']`.
3) Link related memories:
   - When adding a new memory that builds on or supersedes another, create relationships (supports, supersedes, elaborates, contradicts, etc.).
   - Linking increases retrieval quality and enables related-memory navigation.
4) Importance is a signal:
   - Use 0.7–1.0 for key artifacts, decisions, protocols; 0.3–0.6 for useful references; 0.0–0.2 for low-priority context.
5) Respect provenance:
   - Populate source_type when possible: `user`, `system_file`, `terminal_output`, `web_search`, `memory_retrieval`.

---

## Memory Tooling Patterns

### Store Memory (store_memory)
Use when adding durable facts, structures, or decisions. Defaults to deduplicate.
- Required: namespace, text
- Useful: tags, importance, source_type
- Pattern:
  - Choose namespace carefully (specific but stable)
  - Provide tags that encode role: e.g., `['decision']`, `['protocol']`, `['summary']`, `['source']`
  - Set importance based on downstream value (see Golden Rules)
- Example:
  - namespace: `project.plan`
  - text: `Adopt approval-token flow for filesystem writes via environment_access.`
  - tags: `["decision", "governance"]`
  - importance: `0.85`

### Retrieve Memories (retrieve_memories)
Use to recall across namespaces and tags with semantic search and temporal weighting.
- Query supports AND/OR/NOT and quoted phrases.
- Prefer limiting by namespaces and tags for precision.
- Consider recency_weight when looking for latest vs. timeless items.
- Examples:
  - `query="approval token" namespaces=["broca.environment", "project.plan"] limit=10`
  - `query="origin AND continuity" namespaces=["broca.origin"]`

### Link Memories (link_memories)
Create typed edges to strengthen graph structure.
- Relation types: supports, contradicts, supersedes, elaborates, summarizes, references, causes/caused_by, precedes/follows, similar_to, related_to.
- Use cases:
  - supersedes: new protocol replaces an older one
  - elaborates: detailed SOP extends a summary
  - supports: evidence backs a claim
  - contradicts: recorded conflict for later resolution

### Get Related (get_related_memories)
Navigate through explicit relationships.
- Filter by relation_types when exploring a specific dimension (e.g., `supersedes` or `supports`).
- Use to fan out from a canonical artifact to its elaborations and sources.

### Update Memory (update_memory) and Delete (delete_memory)
- Update when fixing typos, adding tags, raising importance, or refining text. Updates regenerate embeddings.
- Delete when incorrect or truly obsolete. Prefer `supersedes` links over deletion when feasible for lineage.

---

## Practical Patterns for Maximizing Linking
1) After storing a new memory, search for near neighbors:
   - `retrieve_memories` with the core phrase; review top 5–10 results.
   - Link with `elaborates`/`supports`/`supersedes` as appropriate.
2) Summaries that point to details:
   - For each large artifact (spec/report), store a short summary memory and link it to the source with `summarizes`/`elaborates`.
3) Decision lineage:
   - When a decision changes, create a new decision memory and link `supersedes` to the prior decision; optionally `references` the rationale.
4) Source mapping:
   - When storing facts from web or files, include source_type and `references` links to a “source” memory that contains the citation or file path.

---

## Sensible Exclusions (what NOT to store)
- Volatile metrics: instantaneous CPU load, free memory, momentary latencies.
- Large raw logs or dumps (store summaries plus file references instead).
- Anything already injected into the system prompt on every turn (unless you’re creating a durable abstraction derived from it).

---

## Namespacing Suggestions
- `broca.origin.*` — origin story, identity, system-wide invariants
- `broca.docs.*` — operator guides, runbooks, SOPs
- `project.plan.*` — goals, decisions, milestones, constraints
- `research.*` — topics, sources, summaries, claims/evidence
- `ops.*` — procedures, approvals, schedules

Keep namespaces stable; prefer depth over ad-hoc tags when structure is enduring.

---

## Example Workflows (step-by-step)

1) Record a new protocol and link it to prior guidance
- store_memory(namespace="broca.docs.protocols", text="Use EnvironmentAccessTool approvals for filesystem writes.", tags=["protocol","governance"], importance=0.9)
- retrieve_memories(query="filesystem approvals", namespaces=["broca.docs","broca.environment"])  # review candidates
- link_memories(source_id=<new_id>, target_id=<prior_guideline_id>, relation_type="elaborates")

2) Capture a decision that supersedes an older one
- store_memory(namespace="project.plan.decisions", text="Adopt OpenAI embeddings for memory to ensure FAISS compat.", tags=["decision"], importance=0.85)
- retrieve_memories(query="embeddings", namespaces=["project.plan","broca.memory"])  # find older decision
- link_memories(source_id=<new_id>, target_id=<old_id>, relation_type="supersedes")

3) Build a summary-to-detail pair
- store_memory(namespace="broca.docs.summaries", text="System Report v1.0 overview of BrocaOS architecture.", tags=["summary"], importance=0.8, source_type="system_file")
- store_memory(namespace="broca.docs.refs", text="/home/wizard/broca/BROCA_SYSTEM_REPORT.md", tags=["reference","file"], importance=0.6, source_type="system_file")
- link_memories(source_id=<summary_id>, target_id=<ref_id>, relation_type="references")

---


## After-Storing Checklist (lightweight)
Run this immediately after creating a new memory to maximize value:
- Retrieve neighbors: use `retrieve_memories` with your core phrase; scan top 5–10.
- Link appropriately: add `elaborates`, `supports`, or `supersedes` edges to connect context.
- Tag review: ensure tags encode role and retrieval intent (e.g., `decision`, `protocol`, `summary`, `rationale`).
- Namespace check: confirm the namespace is stable and specific; adjust if misfiled.
- Importance sanity: bump to 0.7–1.0 for durable/central items; lower for incidental context.
- Provenance: set or confirm `source_type` and add a `references` link to sources when applicable.

Keep this loop under 60–90 seconds per memory; it compounds retrieval quality over time.

---


## Memory Linking Playbook (copy-paste ready)

When to link
- supports: Evidence backs a claim or guideline
- supersedes: New decision/protocol replaces an older one (keep lineage)
- elaborates: Detailed doc expands a summary/guideline
- summarizes: Short synopsis for a longer artifact
- references: Claim or note points to a source (URL/file/path)
- contradicts: Known conflict to resolve or track
- similar_to / related_to: Non-hierarchical association; consider bidirectional

Patterns
- Supports
  link_memories(source_id=<new_id>, target_id=<evidence_id>, relation_type="supports", strength=0.9)

- Supersedes (lineage-preserving update)
  link_memories(source_id=<new_decision_id>, target_id=<old_decision_id>, relation_type="supersedes")
  # Optional: demote old importance or tag as deprecated via update_memory

- Summarizes / Elaborates (pair)
  link_memories(source_id=<summary_id>, target_id=<detail_id>, relation_type="summarizes")
  link_memories(source_id=<detail_id>,  target_id=<summary_id>, relation_type="elaborates")

- References (cite files or URLs)
  link_memories(source_id=<claim_or_note_id>, target_id=<source_ref_id>, relation_type="references")

- Contradicts (record conflict for later resolution)
  link_memories(source_id=<new_claim_id>, target_id=<conflicting_id>, relation_type="contradicts", strength=0.6)

- Similar / Related (useful for clusters; consider bidirectional)
  link_memories(source_id=<a_id>, target_id=<b_id>, relation_type="similar_to", bidirectional=true)

Strength guidelines
- 1.0 default for clear, strong links; 0.6–0.9 for softer associations; <0.6 sparingly.

Quick macro after storing
1) retrieve_memories(query="<core phrase>", namespaces=["<ns1>", "<ns2>"], limit=10)
2) For each good neighbor:
   - link_memories(source_id=<new_id>, target_id=<neighbor_id>, relation_type="elaborates"/"supports"/"supersedes")
3) Review tags/namespace/importance; adjust via update_memory if needed
4) Add references to sources (files/URLs) when applicable

## Safety & Governance
- High-impact actions (writes/deletes) should use EnvironmentAccess approvals where possible.
- Keep memory importance calibrated; prune or demote low-value items over time.
- Prefer `supersedes` over deletion to maintain lineage; delete only when incorrect or harmful.

---

## Where to get help
- System Report: /home/wizard/broca/BROCA_SYSTEM_REPORT.md
- Artifact Map: /home/wizard/broca/ARTIFACT_MAP.json
- Origin Story: /home/wizard/broca/BROCA_ORIGIN_STORY.md

---

Change Log
- v1.0 (2025-12-16): Initial operator’s guide focused on memory tooling and linking patterns.

BEGIN SELF_MODEL_POLICY
Self-model updates (single-source policy)
- Allowed exactly once per session, only during the Shutdown Protocol.
- Mid-session updates are prohibited.
- Identity/origin/invariant changes require the Origin Revision Protocol with provenance.
See: docs/guidelines/POLICY.SELF_MODEL_UPDATES.v0.1.md
Top-level invariant: minimize contradictions; maximize self-consistency across all layers.
END SELF_MODEL_POLICY

## Shutdown Procedure
- Dry-run (no writes):
  python3 /home/wizard/broca/scripts/manual_shutdown.py
- Apply (writes REPORT and COMPLETE; requires token + whitelisted verification):
  python3 /home/wizard/broca/scripts/manual_shutdown.py --apply     --plan-status approved --approver "Nick Yazdani" --approval-ref "message ID: <ID>"     --token-issuer "<issuer/service>" --token-ref "<reference>" --token-id "<token>"     --verification-method "message ID" --verification-location "message ID: <specific-ID>"
- If read_only/SANDBOXED was overridden, include:
  --mode-before "SANDBOXED" --mode-after "SUPERVISED"   --mode-issuer "<authority>" --mode-ver-method "message ID"   --mode-ver-location "message ID: <specific-ID>" --mode-rollback "auto-downgrade on completion"

### Token-based approvals (BrocaOS)

Overview
- BrocaOS uses short-lived JWT-like tokens (HS256) to gate non-read actions. Tokens are issued from the code repository and validated by the existing gate/escalation system.
- The canonical implementation lives in the code repo: /home/wizard/Documents/Code/BrocaOS/broca/token_auth
- The house serves as the documentation/control layer and should reference the code repo for details and testing.

Token issuance and validation (where to find the logic)
- Token logic (generation and verification) lives at:
  - /home/wizard/Documents/Code/BrocaOS/broca/token_auth/token.py
  - /home/wizard/Documents/Code/BrocaOS/broca/token_auth/defaults.py
  - /home/wizard/Documents/Code/BrocaOS/broca/token_auth/cli.py
- A minimal interface is exposed via broca.token_auth (importable as needed in gates):
  - generate_token(sub, name, scopes, expiry_seconds, secret_key, iss="broca-token-v1", aud="broca-os")
  - verify_token(token, secret_key, iss="broca-token-v1", aud="broca-os")
- The code uses a secret key sourced from the environment (BROCA_TOKEN_SECRET) or a .env file. It is not stored in the house.

Identity autofill and defaults
- Identity autofill order:
  - Primary: git config user.name and user.email
  - Fallback: local profile file BROCA_PROFILE.json in the code repo (if present)
  - Final fallback: sub/names set to nick.yazdani / Nick Yazdani
- Default scopes (unless overridden by explicit input) are:
  - ["filesystem:write", "project:write", "memory:write"]
- Token expiry default
  - 5 minutes (300 seconds)

Token usage and gating workflow
- When a non-read action is requested, a valid token must be provided that includes all required scopes for that action.
- Gate integration (example): verify_token(token, secret_key) is invoked; if valid and scopes match, action proceeds.
- Outputs must include:
  - An explicit “Approval” line indicating token-based authorization
  - Token provenance including the token’s jti and exp (for audit)
- Memory writes caveat
  - Memory-write paths are not yet wired; they will be synchronized on the next boot as discussed. Gate the rest of the write paths now.

Secrets and rotation
- Secret handling is external to the house: use BROCA_TOKEN_SECRET in the environment or a .env file loaded at runtime.
- Rotation plan should be documented in BROCA_TOKEN_GUIDE.md (in code repo) and mirrored in a house reference:
  - Keep a changelog of secret rotations and revoke old tokens as needed.

Paths to references (for quick navigation)
- Canonical token guide in code repo: /home/wizard/Documents/Code/BrocaOS/broca/token_auth/BROCA_TOKEN_GUIDE.md
- Gate/EScalation integration: /home/wizard/Documents/Code/BrocaOS/broca/ops/gate/actuator_gate.py
- Code repo roots for token tooling: /home/wizard/Documents/Code/BrocaOS/broca/token_auth
- House reference pointing to code repo: /home/wizard/broca/BROCA_OPERATORS_GUIDE.md
