#!/usr/bin/env python3
"""Aggregate benchmark results and produce simple CSV and plots.
Requires matplotlib.
"""
import json
import os
import sys
import csv
from statistics import mean
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'runtime', 'benchmarks', 'procedural_emergence', 'results')


def aggregate(jsonl_path):
    records = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    if not records:
        print('No records')
        return

    success_rate = mean(1 if r.get('success') else 0 for r in records)
    avg_tool_calls = mean(len(r.get('tool_calls', [])) for r in records)
    avg_composite = mean((r.get('rl_signals', {}).get('composite_reward') or 0) for r in records)
    durations = [r.get('duration') or 0 for r in records]

    summary = {
        'run': os.path.basename(jsonl_path),
        'num_tasks': len(records),
        'success_rate': success_rate,
        'avg_tool_calls': avg_tool_calls,
        'avg_composite_reward': avg_composite,
        'avg_duration': mean(durations) if durations else 0
    }

    # write CSV summary
    csv_path = jsonl_path + '.agg.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(['run', 'num_tasks', 'success_rate', 'avg_tool_calls', 'avg_composite_reward', 'avg_duration'])
        writer.writerow([summary['run'], summary['num_tasks'], summary['success_rate'], summary['avg_tool_calls'], summary['avg_composite_reward'], summary['avg_duration']])
    print('Wrote', csv_path)

    # plot composite reward per task
    comps = [r.get('rl_signals', {}).get('composite_reward') or 0 for r in records]
    plt.figure(figsize=(6,3))
    plt.plot(comps, marker='o')
    plt.title('Composite reward per task')
    plt.xlabel('task index')
    plt.ylabel('composite_reward')
    img_path = jsonl_path + '.composite.png'
    plt.savefig(img_path)
    print('Wrote', img_path)

    return summary


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: aggregate_benchmarks.py <results.jsonl>')
        sys.exit(1)
    path = sys.argv[1]
    agg = aggregate(path)
    print('Summary:', agg)
