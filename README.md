# BrocaOS — Local, Auditable Cognitive REPL & Research Platform

BrocaOS is a sophisticated, safety-first cognitive architecture that integrates LLM-driven conversation with gated environment access, artifact-first continuity, a versioned self-model, and auditable persistence. Designed for developers and researchers who need a safe, auditable, and extensible platform for building intelligent agent workflows.

> **TL;DR**: A safe, auditable, and developer-friendly REPL for building agent workflows locally. Designed for auditability, governance, and fast iteration with continuous learning capabilities.

> **Technical Note**: All affective and metacognitive terms in this documentation (e.g., "valence-like diagnostics," "cognitive inconsistency signals") refer to internal scalar diagnostics and computational patterns, not claims about consciousness or subjective experience. These metrics serve as useful abstractions for modeling and improving system behavior.

## 🌟 Key Features

### **Cognitive Architecture**
- **Production Rule System**: Symbolic reasoning with working memory and goal tracking (4 active rules, 3 active goals)
- **Reinforcement Learning Integration**: Multi-dimensional reward signals for intelligent tool selection (7 reward dimensions)
- **Constraint Inconsistency Monitoring**: Real-time alignment checking and minimization (0.004 current inconsistency score)
- **Procedural Learning**: Pattern extraction from tool usage to create reusable skills (3 skills, 2 procedures)

### **Memory & Knowledge**
- **Vector Memory**: FAISS-based semantic search with embeddings (0.996 internal consistency score)
- **Relational Memory**: Graph-based relationships (supports, contradicts, elaborates, etc.)
- **Temporal Consistency**: Time-aware memory validation
- **Conflict Resolution**: Automated detection and resolution of conflicting information
- **Epistemic Confidence**: Uncertainty quantification and confidence tracking (0.824 epistemic confidence score)

### **Safety & Governance**
- **Actuator Token Gating**: All writes require operator-approved tokens
- **Provenance Tracking**: ORP-style change documentation and audit trails
- **Read-Only Default**: Safe-by-design operation
- **Escalation Protocols**: Multi-level access control (SANDBOXED → SUPERVISED → AUTONOMOUS → EMERGENCY)
- **Comprehensive Audit Logging**: Every operation tracked and verifiable

### **Tool Orchestration**
- **14 Integrated Tools**: Terminal, web search, memory operations, reasoning, planning, etc.
- **RL-Guided Selection**: Confidence-based tool selection with exploration-exploitation balance
- **Skill Management**: 50-skill capacity with decay mechanisms and auto-suggestion
- **Environment Access**: 5 sensor types (system, filesystem, process, network, user activity)

### **Observability & Learning**
- **Real-time Monitoring**: Affective-like, cognitive, and physiological state tracking
- **Explainability**: Feature contribution analysis for RL decisions
- **Health Monitoring**: Automated health reports and performance metrics
- **Continuous Learning**: Experience replay, pattern extraction, and skill refinement

## 🏗️ Architecture Overview

BrocaOS is built as a modular cognitive architecture with **554 Python files** and **184,728 total lines** of code.

### **Core Modules**
```
broca/
├── reasoning/           # Production rule system, constraint monitoring, RL signals
├── memory/             # Vector storage, relational memory, conflict resolution
├── learning/           # Procedural learning, skill management, pattern extraction
├── tools/              # 14 tools with RL-guided selection
├── self_model/         # Versioned self-representation with SQLite storage (v126)
├── environment/        # Sensor/actuator framework with safety controls
├── internal_sensing/   # Real-time diagnostic monitoring
├── repl/               # REPL interface and session management
├── context/            # Context graph and world state aggregation
├── optimization/       # Performance optimization and resource management
├── world_state/        # World state aggregation and formatting
├── summarization/      # Text summarization and compression
├── damping/            # System damping and stability controls
└── systems/            # System integration and coordination
```

### **Data Persistence**
- **`memories.db`** (4.7MB SQLite) - Structured memory storage
- **`memories.faiss`** (1MB) - Vector embeddings for semantic search
- **`self_model.db`** (16.9MB SQLite) - Versioned self-model (v126)
- **`broca_repl.log`** (4.7MB) - Comprehensive operational logging
- **`docs/`** - Artifacts, protocols, and documentation

## 🚀 Quick Start

### **Prerequisites**
- Python 3.13+
- Git
- 4GB+ RAM recommended

### **Installation**
```bash
# Clone the repository
git clone https://github.com/nnyazd92/brocaOS.git
cd brocaOS

# Create virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install browser tools (optional, for web navigation)
playwright install
```

### **Configuration**
1. **Set up environment variables**:
   ```bash
   # Copy example if available, or create your own
   cp .env.example .env  # Edit with your API keys
   ```

#### Gemini rate limit retries (429 / TPM)
If you use `BROCA_LLM_PROVIDER=gemini` and see frequent `429` errors, configure exponential backoff:

- `BROCA_GEMINI_MAX_RETRIES` (default `6`)
- `BROCA_GEMINI_BACKOFF_BASE_SECONDS` (default `1.0`)
- `BROCA_GEMINI_BACKOFF_MAX_SECONDS` (default `60.0`)
- `BROCA_GEMINI_BACKOFF_JITTER` (default `0.25`) — randomizes waits to avoid thundering herd
- `BROCA_GEMINI_RESPECT_RETRY_AFTER` (default `true`) — honors `Retry-After` when provided

2. **Run the REPL**:
   ```bash
   python -m broca.main_repl
   ```

## 🔧 Core Components

### **1. Memory System**
- **Vector Search**: Semantic similarity with FAISS backend
- **Relational Graph**: Typed relationships between memories
- **Conflict Detection**: Automated identification of contradictions
- **Epistemic Engine**: Confidence tracking and uncertainty quantification

### **2. Reasoning Engine**
- **Production Rules**: If-then rules with working memory
- **Goal Management**: Hierarchical goal decomposition and tracking
- **Cognitive Consistency**: Monitoring of constraint satisfaction
- **Z3 Validation**: Formal verification of plans and reasoning chains

### **3. Learning System**
- **Procedural Learning**: Extract reusable patterns from tool usage
- **Skill Management**: Create, update, and apply skills (50 capacity)
- **Experience Replay**: Store and learn from past interactions
- **Pattern Recognition**: Identify successful action sequences

### **4. Tool Framework**
- **14 Integrated Tools**: Terminal, web search, memory operations, reasoning, planning, self-model management, environment access, etc.
- **RL-Guided Selection**: Multi-armed bandit with exploration-exploitation
- **Skill Integration**: Tools can trigger and be guided by learned skills

### **5. Self-Model**
- **Versioned Storage**: SQLite-backed version history (v126)
- **Capability Tracking**: Dynamic updating of known capabilities
- **Constraint Management**: Runtime constraints and boundaries
- **Epistemic Awareness**: Confidence in self-knowledge

### **6. Environment Access**
- **Sensor Framework**: 5 sensor types with safety controls
- **Actuator Gating**: Token-based approval for all writes
- **Access Escalation**: Multi-level security model
- **Audit Trail**: Complete provenance tracking

## 🧠 Reinforcement Learning Design Notes

BrocaOS implements a practical RL system for intelligent tool selection:

### **Forced Exploration (PPO) and Tool Buffer Enforcement**

When `BROCA_RL_ALGORITHM=ppo`, the PPO policy may occasionally enter **forced exploration** to guarantee on-policy rollouts early in training. In forced exploration, the API advertises a **single allowed tool** (an “available tool buffer”). If the model attempts to call any tool outside that buffer, the server blocks the call and returns a tool error message listing the allowed tools, giving the model a chance to retry.

### **`delete_memory` No-Op Safety**

Because forced tool selection can occasionally force `delete_memory`, the `delete_memory` tool supports a safe no-op:
- `memory_id` omitted / empty / `0` → returns success and deletes nothing.

### **Observation Space**
- Tool confidence scores (historical success rates)
- Current task context and goals
- System state metrics (CPU, memory, latency)
- Internal diagnostic scores (consistency, uncertainty, etc.)
- Session history and recent tool outcomes

### **Action Space**
- Discrete tool selection from 14 available tools
- Parameter binding for selected tools
- Exploration vs exploitation decisions
- Skill application when applicable

### **Reward Signal**
- **Multi-dimensional rewards**: 7 distinct reward dimensions
- **Task completion success**: Binary success/failure signals
- **Efficiency metrics**: Tool call efficiency and time to completion
- **Consistency rewards**: Alignment with self-model and constraints
- **Learning signals**: Information gain and skill improvement

### **Learning Mechanism**
- **On-policy learning** with experience replay
- **Monte Carlo dropout** for uncertainty estimation
- **Confidence-based LLM bypass** for high-certainty decisions
- **Stability controls**: Learning rate annealing and gradient clipping
- **Forgetting prevention**: Experience replay with prioritized sampling

### **Safety Constraints**
- **Tool whitelisting**: Only approved tools can be selected
- **Rate limiting**: Maximum tool call frequency
- **Resource boundaries**: CPU/memory usage limits
- **Escalation requirements**: Certain operations require explicit approval

## 🔒 Core System Invariants (Informal)

BrocaOS maintains several key invariants to ensure safety and auditability:

1. **No persistent state change without verified actuator token**
   - All writes to filesystem, databases, or external systems require explicit operator approval via token gating
   - Read-only operation is the default and safest mode

2. **All persisted artifacts must be reproducible from logs**
   - Complete audit trail in `broca_repl.log`
   - SQLite databases with transaction logging
   - Git-style snapshots of important state changes

3. **Self-model versions are append-only and monotonic**
   - Version numbers only increase (v125 → v126 → v127)
   - Previous versions remain accessible for audit and rollback
   - Changes are documented with rationale and context

4. **Memory graph operations preserve referential integrity**
   - Memory deletions cascade to relationship cleanup
   - Graph traversals cannot enter infinite loops
   - Consistency checks validate relationship constraints

5. **RL decisions are explainable and auditable**
   - Feature contribution analysis available for all tool selections
   - Reward signal decomposition documented
   - Exploration/exploitation balance is tunable and logged

6. **Learning system maintains skill validity**
   - Skills decay with disuse but can be re-learned
   - Skill conflicts are detected and resolved
   - Skill application is logged for audit purposes

## 📊 Test Discipline & Quality Assurance

BrocaOS maintains rigorous testing standards:

- **Branch Coverage**: >85% target across core modules
- **Mutation Testing**: 180+ mutants killed in test suite
- **Property-Based Tests**: Hypothesis-based testing for edge cases
- **Golden Trace Replay**: Deterministic replay of recorded sessions
- **Integration Tests**: Full system integration testing
- **Performance Benchmarks**: Resource usage and latency tracking

## 📁 Project Structure

```
brocaOS/
├── broca/                    # Core cognitive architecture
│   ├── reasoning/           # Symbolic reasoning and RL
│   ├── memory/             # Memory systems and search
│   ├── learning/           # Learning and skill management
│   ├── tools/              # Tool implementations
│   ├── self_model/         # Self-representation system
│   ├── environment/        # Environment access framework
│   ├── internal_sensing/   # Diagnostic monitoring
│   └── ...                 # Additional modules
├── docs/                    # Documentation and artifacts
│   ├── artifacts/          # System artifacts and reports
│   ├── memory/             # Memory system documentation
│   ├── self_model/         # Self-model documentation
│   └── ...                 # Additional documentation
├── tests/                   # Comprehensive test suite
├── runtime/                 # Runtime state and sessions
├── conversations/           # Conversation history
├── data/                    # Data storage
└── scripts/                 # Utility scripts
```

## 🛠️ Available Tools

BrocaOS includes 14 integrated tools:

1. **`terminal`** - Execute shell commands and file operations
2. **`web_search`** - Search the web with Tavily API (fallback to browser)
3. **`store_memory`** - Store facts and insights in memory system
4. **`retrieve_memories`** - Semantic search and memory retrieval
5. **`update_memory`** - Update existing memories
6. **`delete_memory`** - Delete memories by ID
7. **`link_memories`** - Create relationships between memories
8. **`get_related_memories`** - Find related memories
9. **`memory_graph`** - Build and traverse memory graphs
10. **`reasoning`** - Cognitive reasoning and production rules
11. **`planning`** - Structured planning for complex tasks
12. **`self_model_crud`** - Manage versioned self-representation
13. **`environment_access`** - Sensor/actuator access with safety controls
14. **`learning`** - Learning system interaction and skill management

## 📈 Internal Diagnostics (Live System Metrics)

> **Note**: These metrics represent internal diagnostic scores, not benchmarked performance claims. They are useful for monitoring system behavior and tuning parameters.

**Current Session (Approximate):**
- **Production Rules**: 4 active rules, 3 active goals
- **Memory System**: Active with 0.996 internal consistency score
- **RL System**: 7-dimensional reward signals, current policy score: 1.0 (normalized internal metric)
- **Constraint Monitoring**: 0.004 inconsistency score
- **Learning System**: 3 skills, 2 procedures, 50 skill capacity
- **Self-Model**: Version 126, last updated recently
- **Epistemic Confidence**: 0.824 confidence score

**For detailed live metrics and historical trends, see `docs/STATUS.md`.**

## 🔬 Research & Development Use Cases

BrocaOS is designed for:

1. **Agent Architecture Research**
   - Study cognitive architectures and reasoning systems
   - Experiment with different learning algorithms
   - Test safety and governance frameworks

2. **Developer Tooling**
   - Build intelligent development assistants
   - Create automated code analysis tools
   - Implement context-aware programming aids

3. **AI Safety Research**
   - Test containment and control mechanisms
   - Study reward hacking prevention
   - Experiment with oversight and alignment

4. **Educational Use**
   - Teach AI architecture concepts
   - Demonstrate reinforcement learning
   - Show safe AI system design

## 🤝 Contributing

BrocaOS welcomes contributions! Please see `CONTRIBUTING.md` for guidelines.

Key contribution areas:
- New tools and capabilities
- Testing improvements
- Documentation enhancements
- Performance optimizations
- Safety and governance features

## 📄 License

BrocaOS is released under the **BrocaOS Personal Use License (BPUL) v1.0**.

**Key terms:**
- Free for personal, educational, and research use
- Commercial use requires separate licensing
- Source available with attribution requirements
- No warranty or liability

See `LICENSE` for complete terms.

## 🙏 Acknowledgments

- Built by Nick Navid Yazdani
- Inspired by cognitive architecture research
- Thanks to the open-source AI community
- Special thanks to early testers and contributors

## 📚 Additional Documentation

- `docs/ARCHITECTURE.md` - Detailed architecture specifications
- `docs/STATUS.md` - Live system metrics and diagnostics
- `docs/OPERATORS_GUIDE.md` - Operator's guide and best practices
- `docs/PLANNING_EFFECTIVENESS_FINDINGS.md` - Research findings on planning effectiveness

---

**BrocaOS**: Building safer, more auditable cognitive systems. 🧠⚡
