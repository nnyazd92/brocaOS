# BrocaOS — Local, Auditable Cognitive REPL & Research Platform

BrocaOS is a sophisticated, safety-first cognitive architecture that integrates LLM-driven conversation with gated environment access, artifact-first continuity, a versioned self-model, and auditable persistence. Designed for developers and researchers who need a safe, auditable, and extensible platform for building intelligent agent workflows.

> **TL;DR**: A safe, auditable, and developer-friendly REPL for building agent workflows locally. Designed for auditability, governance, and fast iteration with continuous learning capabilities.

## 🌟 Key Features

### **Cognitive Architecture**
- **Production Rule System**: Symbolic reasoning with working memory and goal tracking (4 active rules, 3 active goals)
- **Reinforcement Learning Integration**: Multi-dimensional reward signals for intelligent tool selection (7 reward dimensions)
- **Cognitive Dissonance Monitoring**: Real-time alignment checking and minimization (0.004 current dissonance)
- **Procedural Learning**: Pattern extraction from tool usage to create reusable skills (3 skills, 2 procedures)

### **Memory & Knowledge**
- **Vector Memory**: FAISS-based semantic search with embeddings (0.996 self-awareness accuracy)
- **Relational Memory**: Graph-based relationships (supports, contradicts, elaborates, etc.)
- **Temporal Consistency**: Time-aware memory validation
- **Conflict Resolution**: Automated detection and resolution of conflicting information
- **Epistemic Confidence**: Uncertainty quantification and confidence tracking (0.824 epistemic confidence)

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
- **Real-time Monitoring**: Affective, cognitive, and physiological state tracking
- **Explainability**: Feature contribution analysis for RL decisions
- **Health Monitoring**: Automated health reports and performance metrics
- **Continuous Learning**: Experience replay, pattern extraction, and skill refinement

## 🏗️ Architecture Overview

BrocaOS is built as a modular cognitive architecture with **554 Python files** and **184,728 total lines** of code.

### **Core Modules**
```
broca/
├── reasoning/           # Production rule system, cognitive dissonance, RL signals
├── memory/             # Vector storage, relational memory, conflict resolution
├── learning/           # Procedural learning, skill management, pattern extraction
├── tools/              # 14 tools with RL-guided selection
├── self_model/         # Versioned self-awareness with SQLite storage (v125)
├── environment/        # Sensor/actuator framework with safety controls
├── internal_sensing/   # Real-time affective/cognitive monitoring
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
- **`self_model.db`** (16.9MB SQLite) - Versioned self-model (v125)
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

2. **Prepare actuator token** (required for persistence):
   ```bash
   # Place an approval token at .temporary_token.txt
   echo "your_token_here" > .temporary_token.txt
   # OR set environment variable
   export BROCA_TOKEN_SECRET="your_token_here"
   ```

### **Running the REPL**
```bash
python -m broca.main_repl
```

**REPL Commands:**
- `/reset` - Clear session context
- `/exit` or `Ctrl+D` - Exit the REPL
- `/help` - Show available commands
- Type normally to interact with BrocaOS

## 🛠️ Available Tools (14 Total)

### **Core Tools**
1. **`terminal`** - Full shell access with interactive command handling
2. **`web_search`** - Web information retrieval (Tavily API with DuckDuckGo fallback)
3. **`reasoning`** - Production rule system and cognitive reasoning
4. **`planning`** - Structured planning with Z3 validation

### **Memory Tools**
5. **`store_memory`** - Store facts, insights, and information
6. **`retrieve_memories`** - Semantic search with namespace/tag filtering
7. **`delete_memory`** - Remove outdated or incorrect memories
8. **`update_memory`** - Update memory content and metadata
9. **`link_memories`** - Create relationships between memories
10. **`get_related_memories`** - Graph traversal of memory relationships
11. **`memory_graph`** - Build relationship subgraphs

### **System Tools**
12. **`self_model_crud`** - Manage versioned self-awareness
13. **`environment_access`** - Access sensors and actuators with safety controls
14. **`learning`** - Interact with the learning system

## 📖 Usage Examples

### **Example 1: Research and Memory Storage**
```python
# Search for information
web_search(query="python async programming best practices 2024", max_results=5)

# Store key findings
store_memory(
    namespace="programming.python.async",
    text="Python async/await performance best practices: use asyncio.gather() for concurrent tasks, avoid blocking calls in async functions, use proper error handling with asyncio.wait().",
    tags=["python", "async", "best-practices"],
    importance=0.8
)

# Retrieve when needed
retrieve_memories(query="async programming python", namespaces=["programming.python"])
```

### **Example 2: Planning and Reasoning**
```python
# Create a structured plan
planning(
    goal="Implement a web scraper with error handling",
    steps=[
        "1. Set up Playwright browser instance",
        "2. Implement page navigation with timeout handling",
        "3. Add retry logic for failed requests",
        "4. Implement data extraction with fallback selectors",
        "5. Add logging and error reporting"
    ],
    context="Building a robust web scraping tool for research purposes"
)

# Use reasoning to track progress
reasoning(
    action="set_goal",
    goal={
        "name": "implement_web_scraper",
        "description": "Build robust web scraper with error handling",
        "priority": 0.9
    }
)
```

### **Example 3: Memory Graph Navigation**
```python
# Store related memories
id1 = store_memory(namespace="project.design", text="Use microservices architecture for scalability", tags=["architecture"])
id2 = store_memory(namespace="project.design", text="Implement API gateway for service discovery", tags=["architecture"])

# Link them
link_memories(source_id=id1, target_id=id2, relation_type="elaborates")

# Explore the graph
get_related_memories(memory_id=id1, relation_types=["elaborates"])
```

## 🔬 Reinforcement Learning Integration

BrocaOS features a sophisticated RL system for intelligent tool selection with **policy reward estimate: 1.0** (perfect).

### **RL Signal System**
Computes 7-dimensional reward signals in real-time:
- **`dissonance_reward`** (0.3 weight) - Minimize cognitive dissonance
- **`surprise_reward`** (0.2 weight) - Minimize prediction error  
- **`curiosity_reward`** (0.2 weight) - Maximize exploration
- **`information_gain_reward`** (0.15 weight) - Maximize epistemic value
- **`coherence_reward`** (0.15 weight) - Maximize understanding
- **`composite_reward`** - Weighted combination
- **`exploration_balance`** - Exploration vs exploitation tradeoff

### **Confidence-Based Selection**
- **≥85% confidence**: RL forces tool selection (LLM bypassed)
- **30-85% confidence**: RL suggests top-K tools (LLM picks from subset)
- **<30% confidence**: LLM has full choice (failsafe mode)

### **Current Performance**
- **Policy Reward Estimate**: 1.0 (perfect)
- **Baseline Reward**: 0.917 (high baseline)
- **Feature Alignment**: 17 features matched perfectly
- **Tool Reliability**: Terminal: 0.964, others actively learning
- **Experience Buffer**: 79KB experiences collected

## 📊 System Status & Metrics

### **Current Operational Status**
- **LLM Provider**: DeepSeek (configurable: OpenAI, Gemini, DeepSeek)
- **Memory System**: Active with 0.996 self-awareness accuracy
- **Learning System**: Enabled with procedural learning active
- **Reasoning System**: Running with 4 production rules, 3 active goals
- **Self-Model**: Version 125, last updated Dec 29, 2025
- **Affective State**: Positive valence (0.199), moderate curiosity (0.345)
- **Resource Usage**: Low CPU (15%), moderate memory (55%)

### **Knowledge Boundaries**
1. **Training Cutoff**: Limited by underlying LLM training data
2. **Real-time Information**: Requires web search for current events
3. **System Integration**: Module-dependent capabilities
4. **Learning Context**: Needs observation data for pattern extraction

### **Constraints**
1. **Gated Execution**: Token-required for writes
2. **Provenance Requirement**: ORP-style documentation for changes
3. **Origin Revision Protocol**: Required for core logic modifications
4. **Read-Only Default**: Safe operation by design

## 🔧 Development & Testing

### **Running Tests**
```bash
# Run all tests with coverage
pytest --cov=broca --cov-branch --cov-report=term-missing

# Run mutation tests for memory modules
./scripts/run_mutation_tests.sh

# Run specific test modules
pytest broca/tests/test_repl_integration.py
pytest broca/tests/test_self_model_sqlite_storage.py
```

### **Test Coverage Requirements**
- **Memory modules**: ≥85% coverage (including branch coverage)
- **Mutation testing**: Coverage-aware mutation suite for `broca/memory/`
- **Property-based testing**: Hypothesis for core modules
- **Golden trace replay**: For REPL and tool interactions

### **Key Test Files**
- `test_repl_integration.py` - REPL interface testing
- `test_self_model_sqlite_storage.py` - Self-model persistence
- `test_memory_manager_properties.py` - Memory system properties
- `test_internal_sensing_wiring.py` - Monitoring system integration
- `test_rl_integration.py` - Reinforcement learning integration

## 📚 Documentation & Artifacts

### **Core Documentation**
- **`docs/protocols/PROTOCOL.BOOT_UP.v0.3.md`** - Boot-up and persistence protocol
- **`docs/operators/OPERATORS_GUIDE.md`** - Operator's guide with usage examples
- **`BROWSE_TOOL_USAGE.md`** - Browser navigation guide
- **`CRITIC_TOOL.md`** - Critic tool usage
- **`AGENTS.md`** - Agent development guidelines

### **Artifact Management**
- **Artifact-first continuity**: All state changes reference on-disk artifacts
- **Versioned self-models**: SQLite storage with migration tooling
- **Rehydration summaries**: Session continuity across reboots
- **Git snapshot backups**: Automatic backups of persistence state

### **Migration Tooling**
- `broca/self_model/migrations/migrate_to_v2.py` - Deterministic migration to v2.0.0
- Self-model versions stored in `self_model.db` (SQLite)
- Optional serialization to `docs/artifacts/`

## 🚨 Safety & Governance

### **Actuator Token System**
- **Token Verification**: All writes require approved actuator tokens
- **Provenance Tracking**: Every state change includes standardized provenance
- **Scope Limitation**: Tokens can be scoped to specific operations
- **Audit Trail**: Complete history of token usage and changes

### **Access Control Levels**
1. **SANDBOXED** - Read-only, no persistence
2. **SUPERVISED** - Limited writes with approval
3. **AUTONOMOUS** - Full access (requires emergency token)
4. **EMERGENCY** - Temporary elevated access

### **Origin Revision Protocol (ORP)**
- Required for modifications to invariants, identity, or core logic
- Includes migration notes, token provenance, and artifact references
- Ensures auditability and reversibility of changes

### **Boot Protocol**
- Read-only preflight verifies identity artifacts
- Gates persistence behind approved actuator tokens
- Writes include token provenance and are snapshot-backed with git
- See `docs/protocols/PROTOCOL.BOOT_UP.v0.3.md` for details

## 🔄 Learning & Adaptation

### **Procedural Learning**
- **Pattern Extraction**: Learns reusable procedures from tool usage
- **Skill Management**: 50-skill capacity with experience-based refinement
- **Auto-suggestion**: Context-aware tool and procedure suggestions
- **Experience Replay**: Prioritized sampling of past experiences

### **Reinforcement Learning**
- **Online Policy Learning**: Neural network with Monte Carlo dropout
- **Experience Buffer**: 1000-experience capacity with 30-day decay
- **Exploration Strategy**: Adaptive exploration-exploitation balance
- **Performance Tracking**: Baseline comparison and progress verification

### **Metrics & Monitoring**
- **Health Reports**: Automated system health assessment
- **Explainability**: Feature contribution analysis for decisions
- **Performance Metrics**: Success rates, execution times, confidence levels
- **Trend Analysis**: Longitudinal performance tracking

## 🤝 Contributing

### **Development Guidelines**
- Follow actuator/ORP conventions for state-changing operations
- Include token provenance and migration notes in PRs
- Maintain 85%+ test coverage for memory modules
- Use mutation testing for critical components

### **Pull Request Process**
1. Open an issue describing the change
2. Create a feature branch from `main`
3. Include comprehensive tests
4. Add ORP-style migration notes if changing persistence
5. Assign to `nnyazd92` for review

### **Code Standards**
- Type hints for all function signatures
- Comprehensive docstrings
- Property-based testing for core modules
- Mutation testing coverage

## 📄 License & Credits

- **License**: BrocaOS Personal Use License (BPUL) v1.0
- **Author**: Nick Navid Yazdani
- **Repository**: https://github.com/nnyazd92/brocaOS
- **Started**: Dec 11, 2025

## 🔍 Where to Look Next

### **For New Users**
1. **`docs/protocols/PROTOCOL.BOOT_UP.v0.3.md`** - Understand the boot process
2. **`docs/operators/OPERATORS_GUIDE.md`** - Practical usage examples
3. **`broca/main_repl.py`** - Main REPL entry point
4. **`AGENTS.md`** - Agent development guidelines

### **For Developers**
1. **`broca/reasoning/`** - Cognitive architecture core
2. **`broca/memory/`** - Advanced memory system
3. **`broca/tools/`** - Tool orchestration and RL integration
4. **`broca/rl/`** - Reinforcement learning implementation

### **For Researchers**
1. **`broca/internal_sensing/`** - Affective and cognitive monitoring
2. **`broca/learning/`** - Procedural learning system
3. **`broca/environment/`** - Sensor/actuator framework
4. **`broca/self_model/`** - Self-model and metacognition

## 🆘 Getting Help

- **Issues**: Open an issue on GitHub
- **Documentation**: Check the `docs/` directory
- **Examples**: Look at test files for usage patterns
- **Tests**: Run test suite to verify system functionality

---

**BrocaOS** - A safe, auditable, and continuously learning cognitive platform for intelligent agent development and research. Currently at **version 125** with **14 integrated tools**, **RL-guided decision making**, and **comprehensive safety controls**.

**Status**: ✅ **Fully operational** with reinforcement learning integration, memory graph navigation, and continuous learning capabilities.
