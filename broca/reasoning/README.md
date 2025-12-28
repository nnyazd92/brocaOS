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

