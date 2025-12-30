#!/usr/bin/env python3
"""Helpers to register model/dataset artifacts with provenance into simple registries and as memories."""
import json
from pathlib import Path
from datetime import datetime
import subprocess

ROOT = Path('models/rl')
DATA_ROOT = Path('data/rl')


def git_commit_hash():
    try:
        out = subprocess.check_output(['git','rev-parse','--short','HEAD']).decode().strip()
        return out
    except Exception:
        return None


def register_model(path: Path, meta: dict):
    reg = ROOT / 'registry.json'
    rec = {
        'path': str(path),
        'meta': meta,
        'commit': git_commit_hash(),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    if not reg.exists():
        reg.write_text(json.dumps([rec], indent=2))
    else:
        arr = json.loads(reg.read_text())
        arr.append(rec)
        reg.write_text(json.dumps(arr, indent=2))
    print('registered model', path)


def register_dataset(path: Path, meta: dict):
    reg = DATA_ROOT / 'registry.json'
    rec = {
        'path': str(path),
        'meta': meta,
        'commit': git_commit_hash(),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    if not reg.exists():
        reg.write_text(json.dumps([rec], indent=2))
    else:
        arr = json.loads(reg.read_text())
        arr.append(rec)
        reg.write_text(json.dumps(arr, indent=2))
    print('registered dataset', path)

if __name__=='__main__':
    register_model(Path('models/rl/policy_bc.pkl'), {'type':'bc'})
    register_dataset(Path('data/rl/expanded_live'), {'type':'expanded_live'})
