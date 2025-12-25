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
