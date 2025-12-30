Memory Tool Optimization Guide

Overview
- This document explains best practices for using the StoreMemory and RetrieveMemories tools.

Storage best-practices
- Always provide a hierarchical namespace (e.g., "dev.rl.expanded_rich").
- Use tags to categorize memories (e.g., ["rl","dataset","expanded_rich"]).
- Set importance (0.0-1.0) higher for facts that must be retrieved reliably.
- Enable deduplicate=True for factual updates to avoid duplicates.
- Use conflict_check=True for high-impact memories (system behavior, tokens, configuration); set auto_resolve only if safe to do so.
- Provide source_type and source_metadata (e.g., token jti hash) for provenance.
- When storing experiment artifacts, include URIs/paths to data and models.

Retrieval best-practices
- Prefer semantic queries with namespaces and tag filters for precise recall.
- Set recency_weight to a value (0.0-1.0) when recent memories matter more.
- Use memory_ids when following 'Linked to' relationships to traverse graphs deterministically.
- Limit results (limit param) to the top-K most relevant and add include_linked for related contexts.

Updating and Deleting
- Use update_memory to change text/importance/tags; prefer update over delete when possible.
- Use delete_memory only for sensitive or incorrect info that must be removed.
- Keep backups of important memory namespaces periodically.

Linking and Graph Usage
- When storing a memory, set auto_link=True to create relationships.
- Link memories explicitly for causal chains: use relation types like 'supports', 'elaborates', 'references'.
- Use get_related_memories and memory_graph to traverse and reason over memory subgraphs.

Operational tips
- Use ask_user_threshold to force human confirmation on low-confidence auto_resolve situations.
- Keep importance normalized (0.1 increments) to make heuristics predictable.
- Record provenance for actuator or token-related memories (store token_jti_hash not raw tokens).

Examples
- Storing a dataset artifact:
  namespace: 'dev.rl.dataset', tags: ['rl','dataset','expanded_rich'], importance:0.9, text: 'Expanded rich dataset saved at data/rl/expanded_rich', source_metadata: {'path':'data/rl/expanded_rich','collector':'collect_initial_data.py'}

- Retrieving top memories for RL features:
  query: 'expanded_rich dataset features', namespaces:['dev.rl.dataset'], limit:5, recency_weight:0.5

