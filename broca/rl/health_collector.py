#!/usr/bin/env python3
"""Health collector: append structured health metrics to data/rl/health_metrics.jsonl"""
import json
from pathlib import Path
from datetime import datetime

BASE = Path('data/rl')
BASE.mkdir(parents=True, exist_ok=True)
PATH = BASE / 'health_metrics.jsonl'


def append_health(metrics: dict) -> None:
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'metrics': metrics
    }
    with open(PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print('appended health metrics')

if __name__ == '__main__':
    # quick smoke: read verify_progress if present
    vp = BASE / 'verify_progress.json'
    if vp.exists():
        m = json.loads(vp.read_text())
        append_health(m)
    else:
        print('no verify_progress.json to append')
