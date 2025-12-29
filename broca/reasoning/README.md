# Reasoning System

The reasoning system provides symbolic reasoning capabilities using production rules, goal management, and logical validation.

## Components

### Production Rules
- **ProductionRule**: If-then rules that match patterns in working memory
- **ProductionRuleSystem**: Manages and executes production rules
- **RuleEngine**: Matches and executes rules with declarative memory integration

### Goal Management
- **GoalManager**: Manages hierarchical goal structures with dependencies
- **Goal**: Represents desired states or outcomes

### Working Memory
- **WorkingMemory**: Active memory buffer with activation-based retrieval
- **WorkingMemoryItem**: Items in working memory with activation levels

### PEA Loop (Planning-Execution-Assessment)

The PEA loop enforces structured problem-solving by requiring planning before execution, tracking all actions, and assessing results to enable recursive learning from failures.

#### PlanExecuteAssessLoop

Forces Broca to always follow:
1. **PLAN**: Create a plan before executing actions
2. **ACTION(S)**: Execute planned actions with tracking
3. **ASSESS**: Evaluate results and learn from failures
4. **RECURSE**: Use assessment to form new plan (if needed)

Key features:
- Prevents mindless repetition by tracking failed patterns
- Limits replan attempts (default: 3)
- Integrates with goal_manager, skill_manager, experience_logger
- Maintains execution history and assessment history

#### Configuration

PEA loop is configured via `ReasoningConfig`:

```python
pea_loop_enabled: bool = True                    # Enable/disable PEA loop
pea_loop_require_planning: bool = True          # Force planning before actions
pea_loop_max_replans: int = 3                   # Maximum replan attempts
pea_loop_success_threshold: float = 0.8         # Success rate threshold for goal achievement
pea_loop_track_failed_patterns: bool = True    # Track failed patterns to prevent repetition
pea_loop_max_failed_patterns: int = 10          # Maximum failed patterns to track
```

#### Integration Points

1. **ConversationSession**: PEA loop is initialized in session and integrated into `send()` method
2. **Tool Execution**: All tool executions are tracked with success/failure
3. **Assessment**: After tool calls complete, execution is assessed
4. **Replanning**: If assessment indicates failure, new plan is required

#### Usage

The PEA loop is automatically integrated into the conversation flow. When a user requests an action:

1. **Planning Phase**: If no plan exists, LLM is required to create a plan
2. **Action Phase**: Tool calls are executed and tracked
3. **Assessment Phase**: After execution, results are assessed
4. **Replanning**: If goal not achieved and replan attempts remain, new plan is required

#### Testing

The PEA loop includes comprehensive tests following AGENTS.md requirements:

- **Unit tests**: `test_pea_loop.py`
- **Mutation tests**: `test_pea_loop_mutation.py`
- **Property-based tests**: `test_pea_loop_property.py` (Hypothesis)
- **Fault injection**: `test_pea_loop_fault_injection.py`
- **Golden traces**: `test_pea_loop_golden_traces.py` with fixtures in `fixtures/golden_traces/pea_loop/`
- **Integration tests**: `test_pea_loop_integration.py`

### Z3 Logical Validation

The reasoning system includes Z3-based logical validation to ensure consistency:

#### Z3LogicalValidator

Validates logical consistency of:
- **Rule chains**: Ensures production rule chains are logically consistent
- **Causal chains**: Validates causal relationships with transitivity checking
- **Goal dependencies**: Checks goal dependency satisfiability and detects cycles
- **Learned procedures**: Validates learned procedures for logical soundness
- **Contradictions**: Detects conflicting propositions

#### Configuration

Z3 validation is configured via `ReasoningConfig`:

```python
z3_validation_enabled: bool = True  # Enable/disable Z3 validation
z3_validation_timeout: float = 5.0  # Timeout in seconds
z3_max_constraints: int = 1000      # Maximum constraints to process
```

#### Integration Points

1. **RuleEngine**: Validates rule chains before execution
2. **GoalManager**: Validates goal dependencies before adding goals
3. **MemoryManager**: Validates causal relationships via `CausalChainValidator`
4. **ProceduralLearning**: Validates learned procedures before storing
5. **WorldState**: Includes compact Z3 validation summary (max 200 bytes)

#### Size Limits

Z3 validation outputs are strictly size-limited to prevent unbounded growth:
- **Validation summary**: Maximum 200 bytes in world state
- **On-demand validation**: Validation occurs during reasoning cycles, not pre-computed
- **Summary-only**: World state includes only summary statistics, not full Z3 solver states

#### Graceful Degradation

The system works without Z3:
- Validation is optional enhancement
- System continues operating when Z3 is unavailable
- Validation failures log warnings but don't stop reasoning (unless critical)

## Usage

### Basic Rule Execution

```python
from broca.reasoning.rule_engine import RuleEngine
from broca.reasoning.working_memory import WorkingMemory
from broca.reasoning.production_rules import ProductionRule, RuleType

# Create rule engine
rule_engine = RuleEngine(enable_z3_validation=True)

# Add a rule
rule = ProductionRule(
    name="inference_rule",
    conditions=[{"type": "fact", "content": "premise"}],
    actions=[{"type": "add_to_memory", "content": {"type": "fact", "content": "conclusion"}}],
    rule_type=RuleType.INFERENCE
)
rule_engine.rule_system.add_rule(rule)

# Execute cycle
wm = WorkingMemory()
wm.add({"type": "fact", "content": "premise"})
results = rule_engine.execute_cycle(wm)
```

### Goal Management

```python
from broca.reasoning.goal_manager import GoalManager, Goal, GoalType, GoalStatus

# Create goal manager (Z3 validation enabled by default)
goal_manager = GoalManager()

# Add goal with dependencies
goal = Goal(
    name="complete_task",
    description="Complete the task",
    goal_type=GoalType.ACHIEVE,
    dependencies=["prepare_resources"],  # Will be validated by Z3
    status=GoalStatus.ACTIVE
)
goal_manager.add_goal(goal)  # Z3 validates dependencies
```

### Causal Chain Validation

```python
from broca.memory.causal_validator import CausalChainValidator
from broca.memory import MemoryRecord, RelationType

# Causal validator is automatically used when creating CAUSES relationships
# via MemoryManager.link_memories()
```

## Testing

The reasoning system includes comprehensive tests following AGENTS.md requirements:

- **Unit tests**: `test_z3_validator.py`
- **Property-based tests**: `test_z3_validator_property.py` (Hypothesis)
- **Fault injection**: `test_z3_validator_fault_injection.py`
- **Integration tests**: `test_z3_reasoning_integration.py`
- **Mutation testing**: Configured in `setup.cfg` for `z3_validator.py`
- **Golden traces**: `fixtures/golden_traces/z3_validation_*.json`

## Dependencies

- `z3-solver>=4.12.0.0`: Z3 theorem prover for logical validation

