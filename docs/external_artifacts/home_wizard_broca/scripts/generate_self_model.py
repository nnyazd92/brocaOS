#!/usr/bin/env python3
"""
generate_self_model.py

Lightweight scaffold to generate a self-model snapshot from artifacts and schema.
Usage: generate_self_model.py [--schema PATH] [--output-dir DIR] [--commit]

By default this is conservative: it writes snapshot to output-dir but will not update
broca.artifacts or broca.session.pointer unless --commit is provided.

This script is intentionally self-contained and avoids external LLM calls. It provides
hooks (functions) where an LLM or stronger extraction can be plugged in.
"""
import argparse
import json
import os
import time
import hashlib
import base64
import hmac
from datetime import datetime

DEFAULT_SCHEMA = '/home/wizard/broca/user/schema/broca.schema.json'
DEFAULT_OUTPUT_DIR = '/home/wizard/broca/self_models'
POINTER = '/home/wizard/broca/broca.session.pointer'
ARTINDEX = '/home/wizard/broca/broca.artifacts'


def now_ts():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def canonicalize_text_to_statements(text, source='system_prompt'):
    # Very simple canonicalization: split on paragraphs and sentences.
    parts = [p.strip() for p in text.replace('\r', '\n').split('\n') if p.strip()]
    statements = []
    sid = 1
    for p in parts:
        sentences = [ss.strip() for ss in p.split('.') if ss.strip()]
        for s in sentences:
            txt = s
            if not txt.endswith('.'):
                txt = txt + '.'
            statements.append({
                'id': f's{sid}',
                'text': txt,
                'type': 'inferred',
                'tags': [],
                'source': source,
                'last_updated': now_ts(),
                'importance': None,
                'centrality': None,
                'contradiction_flags': []
            })
            sid += 1
    return statements


def pseudo_embedding_hash(text):
    h = hashlib.sha256(text.encode()).digest()
    return base64.urlsafe_b64encode(h).decode().rstrip('=')


def compute_centrality(statements):
    tokens = [set(s['text'].lower().split()) for s in statements]
    n = len(statements)
    scores = [0.0] * n
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a = tokens[i]
            b = tokens[j]
            if not a or not b:
                continue
            inter = len(a & b)
            union = len(a | b)
            sim = inter / union if union > 0 else 0.0
            scores[i] += sim
    maxs = max(scores) if scores else 1.0
    if maxs == 0:
        maxs = 1.0
    for i in range(n):
        statements[i]['centrality'] = scores[i] / maxs
    return statements


def score_importance(statements, weights=None):
    if weights is None:
        weights = {'centrality': 0.7, 'recency': 0.1, 'tag_core': 0.2}
    now = time.time()
    from datetime import datetime as _dt
    for s in statements:
        centrality = s.get('centrality') or 0.0
        try:
            t = _dt.strptime(s.get('last_updated'), '%Y-%m-%dT%H:%M:%SZ').timestamp()
            recency = 1.0 / (1.0 + (now - t) / 86400.0)
        except Exception:
            recency = 0.0
        tag_core = 1.0 if 'core' in s.get('tags', []) else 0.0
        s['importance'] = weights['centrality'] * centrality + weights['recency'] * recency + weights['tag_core'] * tag_core
    return statements


def hmac_sign_obj(obj, secret_env='BROCA_TOKEN_SECRET'):
    secret = os.environ.get(secret_env)
    if not secret:
        return None
    serialized = json.dumps(obj, separators=(',', ':'), sort_keys=True)
    sig = hmac.new(secret.encode(), serialized.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip('=')


def build_snapshot(schema, statements, artifacts, provenance):
    snapshot = {
        'meta': {
            'schema_id': schema.get('title', 'broca.schema') if isinstance(schema, dict) else 'broca.schema',
            'version': schema.get('version', 1) if isinstance(schema, dict) else 1,
            'created_by': provenance.get('created_by', 'unknown'),
            'timestamp': now_ts()
        },
        'identity': {
            'id': 'broca',
            'name': 'BrocaOS',
            'canonical_description': 'Dynamic generated self-model snapshot for BrocaOS.'
        },
        'invariants': schema.get('invariants', []) if isinstance(schema, dict) else [],
        'statements': statements,
        'metrics': {
            'consistency_score': 1.0,
            'contradiction_count': 0,
            'last_checked': now_ts()
        },
        'artifacts': [{'path': p, 'type': 'unknown', 'sha256': None} for p in (artifacts or [])],
        'generation_config': schema.get('generation_config', {}) if isinstance(schema, dict) else {},
        'history': [],
        'provenance': provenance
    }
    h = hmac_sign_obj(snapshot)
    if h:
        snapshot.setdefault('provenance', {})['hmac'] = h
    return snapshot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema', default=DEFAULT_SCHEMA)
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--commit', action='store_true', help='If set, update broca.artifacts and broca.session.pointer')
    parser.add_argument('--system-prompt', default=None, help='Path to system prompt text to incorporate')
    args = parser.parse_args()

    schema = load_json(args.schema) or {}
    spath = args.system_prompt or schema.get('generation_config', {}).get('system_prompt_path') if isinstance(schema, dict) else None

    artifacts = []
    pointer = load_json(POINTER)
    aindex = load_json(ARTINDEX)
    if pointer:
        cur = pointer.get('current_session_summary')
        if cur:
            artifacts.append(cur)
    if aindex:
        for a in aindex.get('artifacts', []):
            path = a.get('path')
            if path and path not in artifacts:
                artifacts.append(path)

    texts = []
    if spath and os.path.exists(spath):
        try:
            texts.append(open(spath, 'r').read())
            artifacts.append(spath)
        except Exception:
            pass

    for pth in list(artifacts):
        if os.path.exists(pth):
            try:
                texts.append(open(pth, 'r').read())
            except Exception:
                pass

    combined_text = '\n\n'.join(texts) if texts else ''
    if not combined_text:
        combined_text = 'BrocaOS dynamic self-model generation. No artifacts available.'

    statements = canonicalize_text_to_statements(combined_text)
    for s in statements:
        s['embedding_hash'] = pseudo_embedding_hash(s['text'])
    statements = compute_centrality(statements)
    statements = score_importance(statements, weights=schema.get('generation_config', {}).get('importance_weights')) if isinstance(schema, dict) else score_importance(statements)

    provenance = {
        'created_by': os.environ.get('USER', 'unknown'),
        'jti': None,
        'token_file': '/home/wizard/Documents/Code/BrocaOS/.temporary_token.txt'
    }
    try:
        tok = load_json(provenance['token_file'])
        if isinstance(tok, dict) and 'payload' in tok:
            provenance['jti'] = tok['payload'].get('jti')
    except Exception:
        pass

    snapshot = build_snapshot(schema, statements, artifacts, provenance)

    os.makedirs(args.output_dir, exist_ok=True)
    fname = os.path.join(args.output_dir, 'self-' + datetime.utcnow().strftime('%Y%m%dT%H%M%SZ') + '.json')
    with open(fname, 'w') as f:
        json.dump(snapshot, f, indent=2)
    print('WROTE SNAPSHOT', fname)

    if args.commit:
        aidx = load_json(ARTINDEX) or {'artifacts': []}
        aidx['artifacts'].insert(0, {'id': os.path.basename(fname), 'type': 'self-model-snapshot', 'path': fname, 'created_by': provenance.get('created_by'), 'timestamp': now_ts(), 'sha256': None})
        with open(ARTINDEX, 'w') as f:
            json.dump(aidx, f, indent=2)
        pidx = {
            'current_session_summary': fname,
            'other_pointers': [],
            'created_by': provenance.get('created_by'),
            'persistence_source': '/home/wizard/Documents/Code/BrocaOS/.shutdown_persistence.json',
            'timestamp': now_ts()
        }
        with open(POINTER, 'w') as f:
            json.dump(pidx, f, indent=2)
        print('UPDATED POINTER AND ARTINDEX (commit)')
    else:
        print('Commit flag not set; broca.artifacts and broca.session.pointer not modified.')


if __name__ == '__main__':
    main()
