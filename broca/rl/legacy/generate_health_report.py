#!/usr/bin/env python3
"""Generate a markdown health report from health_metrics.jsonl and explanations.jsonl"""
import json
from pathlib import Path
out = Path('data/rl/health_report.md')
metrics_p = Path('data/rl/health_metrics.jsonl')
report = ['# BrocaOS RL Learning Health Report\n']
if metrics_p.exists():
    lines = [json.loads(l) for l in metrics_p.read_text().splitlines()]
    report.append('## Recent Health Metrics\n')
    for e in lines[-10:]:
        report.append(f"- {e['timestamp']}: {e['metrics']}\n")
else:
    report.append('No health metrics found.\n')

out.write_text('\n'.join(report))
print('wrote', out)
