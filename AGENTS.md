## USE TDD, ENSURE NO REGRESSIONS

### The following are vitally important to implement
- Mutation testing
- Property based testing
- Fault injection
- Golden trace replay
- Coverage report + branch coverage

## SYSTEM PROMPT MANAGEMENT

### Size Limits and Deduplication

The system prompt must NOT grow unbounded over time. The following safeguards are in place:

1. **Size Limits** (configurable via environment variables):
   - `BROCA_MAX_SYSTEM_PROMPT_SIZE`: Maximum total system prompt size (default: 50KB)
   - `BROCA_MAX_WORLD_STATE_SIZE`: Maximum world state JSON size (default: 30KB)
   - `BROCA_MAX_SUMMARY_CONTEXT_SIZE`: Maximum summary context size (default: 15KB)

2. **Deduplication**:
   - Base system prompt is only included once
   - Summary context is checked for duplication against base prompt
   - Duplicate sections within the prompt are detected and logged
   - Hash-based change detection prevents unnecessary updates

3. **Update Logic**:
   - System prompt is always REPLACED, never appended
   - Updates only occur when world state hash changes
   - Content is validated for duplicates before update

4. **Monitoring**:
   - System prompt size is logged at each update
   - Warnings are issued when size exceeds 70% of limit
   - Duplicate sections are detected and logged

### Implementation Details

- `_update_system_prompt()` in `broca/repl/session.py` handles all system prompt updates
- `WorldStateFormatter` enforces size limits on world state JSON
- `PromptBuilder.build_context()` enforces size limits on summary context
- All size limits are configurable via `StorageConfig` in `broca/config.py`

## MEMORY SYSTEM - GRAPH TRAVERSAL

### Linked Memories in Retrieval
When memories are retrieved via `retrieve_memories`, each memory includes a "Linked to" section showing:
- Related memory IDs with relationship types (supports, elaborates, contradicts, etc.)
- Relationship strength (0.0-1.0)
- Direction (outgoing/incoming)
- Text preview of related memories

This enables the model to:
1. Traverse the memory graph by following relationships
2. Understand context and connections between memories
3. Make informed decisions about which related memories to retrieve next

### ID-Based Retrieval for Graph Traversal
Memories can be retrieved directly by ID using the `memory_ids` parameter. This is essential for graph traversal:
- When you see memory IDs in the "Linked to" section, use `memory_ids=[id1, id2, ...]` to retrieve those specific memories
- ID-based retrieval is reliable and fast - no semantic search needed
- You can retrieve multiple memories by ID in a single call
- If `memory_ids` is provided, the `query` parameter is ignored

### Relationship Types
- Logical: SUPPORTS, CONTRADICTS, SUPERSEDES
- Structural: ELABORATES, SUMMARIZES, REFERENCES
- Causal: CAUSES, CAUSED_BY
- Temporal: PRECEDES, FOLLOWS
- Semantic: SIMILAR_TO, RELATED_TO

### Configuration
- `include_linked`: Boolean flag to enable/disable linked memories (default: true)
- `linked_limit`: Maximum number of linked memories per memory (default: 5, max: 10)

### Implementation Details
- Linked memories are fetched using `MemoryManager.get_related_memories()` in `RetrieveMemoriesTool.execute()`
- Display formatting handled in `RetrieveMemoriesTool.format_result()`
- Relationship direction determined by comparing `source_id` and `target_id` with memory ID
