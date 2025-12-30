Procedural Emergence benchmark

This skeleton provides a minimal benchmark harness for testing BrocaOS's ability
to learn and reuse procedures from repeated tool-call sequences.

Structure
- scripts/benchmark_runner.py : CLI runner (simulation mode and hooks to integrate BrocaOS)
- runtime/benchmarks/procedural_emergence/config.yaml : suite config
- runtime/benchmarks/procedural_emergence/task_list.json : example tasks
- runtime/benchmarks/procedural_emergence/result_schema.json : JSON schema for results
- runtime/benchmarks/procedural_emergence/results/ : results directory

How to use (simulation)
1. From the skeleton root, run:
   python3 scripts/benchmark_runner.py --config runtime/benchmarks/procedural_emergence/config.yaml --run-id demo --simulate
2. The runner will write runtime/benchmarks/procedural_emergence/results/demo.jsonl and a demo.jsonl.summary.csv

How to integrate with BrocaOS runtime
- Edit Runner.run_task in scripts/benchmark_runner.py to call into your BrocaOS instance.
  Options:
  - Use a local REST API if you expose one (config.runtime.broca_api).
  - Use a REPL socket or subprocess to run commands and capture outputs.
  - Import BrocaOS python modules directly (if running in same environment) and call the reasoning loop / tool registry.

Instrumentation suggestions
- Make BrocaOS emit structured trace events on tool calls and internal signals. Save them into the 'tool_calls' and 'rl_signals' fields.
- Use ExperienceLogger, ProceduralLearner, SkillManager APIs to capture procedures_applied and internal updates.

Next steps to extend
- Add more synthetic tasks and real-world tasks (ToolBench integration)
- Implement ablation experiments by toggling ablation flags when creating Runner
- Add automated validators for success beyond exact-match (fuzzy match, regex, test execution)

