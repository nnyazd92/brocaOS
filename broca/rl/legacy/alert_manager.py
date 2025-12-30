#!/usr/bin/env python3
"""Simple alert manager for RL health metrics.
Writes alerts to data/alerts.jsonl and stores a memory via store_memory.
"""
import json
from pathlib import Path
from functions import store_memory, link_memories

HEALTH = Path('data/rl/verify_progress.json')
ALERTS = Path('data/rl/alerts.jsonl')
GUIDE_MEM_ID = 153


def check_and_alert():
    if not HEALTH.exists():
        print('no verify_progress.json')
        return
    d = json.loads(HEALTH.read_text())
    policy = d.get('policy_reward_estimate')
    baseline = d.get('baseline_reward')
    alerts = []
    if policy is None:
        alerts.append({'severity':'warning','message':'Policy estimate missing due to model mismatch'})
    else:
        if policy < baseline - 0.05:
            alerts.append({'severity':'error','message':f'Policy underperforms baseline ({policy} < {baseline})'})

    if alerts:
        for a in alerts:
            entry = {'timestamp':__import__('datetime').datetime.utcnow().isoformat()+'Z','alert':a}
            with open(ALERTS,'a') as f:
                f.write(json.dumps(entry)+'\n')
            # store memory
            mem = store_memory(namespace='dev.alerts',tags=['alert','rl'],text=f"{a['severity']}: {a['message']}",importance=0.9)
            # link to guide
            try:
                link_memories(source_id=mem['id'],target_id=GUIDE_MEM_ID,relation_type='references',strength=0.9,bidirectional=True)
            except Exception:
                pass
        print('alerts created')
    else:
        print('no alerts')

if __name__=='__main__':
    check_and_alert()
