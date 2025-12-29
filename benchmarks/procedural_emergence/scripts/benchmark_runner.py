#!/usr/bin/env python3
"""
Benchmark harness skeleton for Procedural Emergence
Writes structured JSONL results per run and provides a simple aggregation utility.

This is a pluggable skeleton: implement the Runner.run_task() method to call
into your BrocaOS runtime (REPL, API, or direct function calls).

Usage examples:
  python3 scripts/benchmark_runner.py --config runtime/benchmarks/procedural_emergence/config.yaml --run-id test1 --simulate
  python3 scripts/benchmark_runner.py --config runtime/benchmarks/procedural_emergence/config.yaml --run-id run001

Options:
  --simulate: run in simulation mode (uses expected_output to mark success)
  --ablation <name>: comma-separated toggles to disable components (e.g. procedural,rl,gate)

Output:
  runtime/benchmarks/procedural_emergence/results/<run_id>.jsonl
  (one JSON object per task)
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BENCH_DIR = os.path.join(BASE_DIR, 'runtime', 'benchmarks', 'procedural_emergence')
RESULTS_DIR = os.path.join(BENCH_DIR, 'results')

os.makedirs(RESULTS_DIR, exist_ok=True)


class Runner:
    def __init__(self, config: Dict[str, Any], ablation_flags: List[str] = None, simulate: bool = False):
        self.config = config
        self.simulate = simulate
        self.ablation_flags = set(ablation_flags or [])

        # Placeholders for integration hooks
        # e.g., self.broca_client = BrocaClient(api_url=config.get('broca_api'))

    def run(self, tasks: List[Dict[str, Any]], run_id: str):
        out_path = os.path.join(RESULTS_DIR, f"{run_id}.jsonl")
        with open(out_path, 'w', encoding='utf-8') as out_file:
            for task in tasks:
                start = time.time()
                try:
                    result = self.run_task(task)
                except Exception as e:
                    result = {
                        'task_id': task.get('id'),
                        'success': False,
                        'error': str(e),
                        'tool_calls': [],
                        'procedures_applied': [],
                        'rl_signals': {},
                        'dissonance_before': None,
                        'dissonance_after': None,
                        'start_time': datetime.utcnow().isoformat() + 'Z',
                        'end_time': datetime.utcnow().isoformat() + 'Z',
                        'duration': 0.0
                    }
                # write JSONL
                out_file.write(json.dumps(result, ensure_ascii=False) + '\n')
                out_file.flush()

        print(f"Wrote results to: {out_path}")
        return out_path

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single task. Replace or extend this method to integrate with BrocaOS runtime.

        Expected return schema (see result_schema.json):
        {
          "task_id": str,
          "success": bool,
          "final_output": str | null,
          "tool_calls": [ {"tool": str, "parameters": dict, "result": dict, "timestamp": iso } ],
          "procedures_applied": [ { "procedure_name": str, "confidence": float } ],
          "rl_signals": { "composite_reward": float, ... },
          "dissonance_before": float | null,
          "dissonance_after": float | null,
          "start_time": iso8601,
          "end_time": iso8601,
          "duration": seconds
        }
        """
        task_id = task.get('id') or str(uuid.uuid4())
        start_ts = datetime.utcnow().isoformat() + 'Z'

        # If simulate, use expected_output and simple simulated tool call trace
        if self.simulate:
            # simple simulation: pretend to call a tool sequence
            tool_calls = []
            for i, step in enumerate(task.get('simulated_steps', [])):
                tool_calls.append({
                    'tool': step.get('tool', 'simulated_tool'),
                    'parameters': step.get('parameters', {}),
                    'result': {'success': True, 'output': step.get('simulated_output', '')},
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
                time.sleep(0.05)

            success = bool(task.get('expected_output'))
            final_output = task.get('expected_output') if success else ''

            result = {
                'task_id': task_id,
                'success': success,
                'final_output': final_output,
                'tool_calls': tool_calls,
                'procedures_applied': [],
                'rl_signals': {'composite_reward': 0.5},
                'dissonance_before': 0.6,
                'dissonance_after': 0.3 if success else 0.7,
                'start_time': start_ts,
                'end_time': datetime.utcnow().isoformat() + 'Z',
                'duration': round(time.time() - time.time(), 3)
            }
            return result

        # Integration examples (choose one that matches your BrocaOS setup):
        # 1) HTTP API integration: if config.runtime.broca_api is set, POST the task and await JSON response
        broca_api = None
        try:
            broca_api = self.config.get('runtime', {}).get('broca_api')
        except Exception:
            broca_api = None

        if broca_api:
            try:
                import requests
                payload = {
                    'task_id': task_id,
                    'input': task.get('input'),
                    'metadata': task.get('metadata', {})
                }
                resp = requests.post(broca_api, json=payload, timeout=self.config.get('runtime', {}).get('script_timeout_seconds', 30))
                resp.raise_for_status()
                data = resp.json()

                # Expect the BrocaOS API to return an object compatible with our result schema
                data.setdefault('task_id', task_id)
                data.setdefault('start_time', start_ts)
                data.setdefault('end_time', datetime.utcnow().isoformat() + 'Z')
                data.setdefault('duration', None)
                return data
            except Exception as e:
                # Fall through to other integration attempts or return error
                err_msg = f"HTTP broca_api call failed: {e}"
                print(err_msg, file=sys.stderr)

        # 2) Direct import integration: if this script runs in the same environment as BrocaOS
        try:
            # Example pattern: attempt to import a helper function that accepts a task dict
            # and returns a result compatible with the result schema. Adapt the function name
            # to your runtime (this is a safe guarded call).
            import broca
            # Try common entrypoints (best-effort): main_repl_runtime.process_single_task or a similarly named helper
            result = None
            # 1) preferred: broca.process_single_task
            if hasattr(broca, 'process_single_task'):
                result = broca.process_single_task(task)
            else:
                # 2) try adapter installed under benchmarks.procedural_emergence
                try:
                    from benchmarks.procedural_emergence import broca_adapter
                    if hasattr(broca_adapter, 'process_single_task'):
                        result = broca_adapter.process_single_task(task)
                except Exception:
                    result = None
                if result is None:
                    # Try deeper modules
                    try:
                        from broca import main_repl_runtime as mrr
                        if hasattr(mrr, 'process_single_task'):
                            result = mrr.process_single_task(task)
                    except Exception:
                        result = None

            if result:
                result.setdefault('task_id', task_id)
                result.setdefault('start_time', start_ts)
                result.setdefault('end_time', datetime.utcnow().isoformat() + 'Z')
                result.setdefault('duration', None)
                return result
        except Exception as e:
            # Not running in BrocaOS environment or import failed
            print(f"Direct import integration not available: {e}", file=sys.stderr)

        # 3) Fallback: structured error result indicating integration missing
        return {
            'task_id': task_id,
            'success': False,
            'final_output': None,
            'error': 'No BrocaOS integration available (set runtime.broca_api or run in same env and implement process_single_task)',
            'tool_calls': [],
            'procedures_applied': [],
            'rl_signals': {},
            'dissonance_before': None,
            'dissonance_after': None,
            'start_time': start_ts,
            'end_time': datetime.utcnow().isoformat() + 'Z',
            'duration': 0.0
        }


def load_config(path: str) -> Dict[str, Any]:
    import yaml
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_tasks(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def aggregate_results(results_path: str, out_csv: str = None):
    import csv
    records = []
    with open(results_path, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    if not records:
        print('No records found')
        return
    # Simple CSV summary: task_id, success, duration, tool_calls_count
    csv_path = out_csv or results_path + '.summary.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(['task_id', 'success', 'duration', 'tool_calls_count'])
        for r in records:
            writer.writerow([r.get('task_id'), r.get('success'), r.get('duration'), len(r.get('tool_calls', []))])
    print(f'Wrote summary CSV: {csv_path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Path to suite config YAML')
    parser.add_argument('--task-list', help='Path to task list JSON (overrides config)')
    parser.add_argument('--run-id', help='Run identifier (defaults to timestamp)', default=None)
    parser.add_argument('--simulate', action='store_true', help='Run in simulation mode')
    parser.add_argument('--ablation', help='Comma-separated ablation flags (procedural,rl,gate)')

    args = parser.parse_args()
    config = load_config(args.config)
    task_list_path = args.task_list or os.path.join(BENCH_DIR, 'task_list.json')
    tasks = load_tasks(task_list_path)

    run_id = args.run_id or datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    ablation_flags = args.ablation.split(',') if args.ablation else []

    runner = Runner(config=config, ablation_flags=ablation_flags, simulate=args.simulate)
    results_path = runner.run(tasks, run_id)
    aggregate_results(results_path)


if __name__ == '__main__':
    main()
