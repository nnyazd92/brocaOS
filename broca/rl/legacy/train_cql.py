#!/usr/bin/env python3
"""Train a small CQL using d3rlpy on the expanded arrays (toy run)."""
from pathlib import Path
import numpy as np

try:
    import d3rlpy
    from d3rlpy.dataset import MDPDataset
except Exception as e:
    print('d3rlpy not available:', e)
    raise SystemExit(1)

base = Path('data/rl/expanded')
obs = np.load(base/'observations.npy')
acts = np.load(base/'actions.npy')
rews = np.load(base/'rewards.npy')
next_obs = np.load(base/'next_observations.npy')

# For d3rlpy MDPDataset, actions for discrete env expected int array
# Ensure shapes are correct (actions should be (N,1), rewards (N,1))
acts = acts.reshape(-1, 1) if acts.ndim == 1 else acts
rews = rews.reshape(-1, 1) if rews.ndim == 1 else rews
next_obs = next_obs

mdp = MDPDataset(obs, acts, rews, next_obs)

cql = d3rlpy.algos.CQL(
    q_func='mean',
    encoder_factory=d3rlpy.models.encoders.DefaultEncoderFactory(),
    batch_size=32,
    n_steps=100
)

# Small toy training run
cql.fit(mdp, n_epochs=5)
Path('models/rl/cql_policy').mkdir(parents=True, exist_ok=True)
cql.save_path = 'models/rl/cql_policy'
cql.save('models/rl/cql_policy')
print('saved CQL policy to models/rl/cql_policy')

# Export predicted actions on training observations for a simple lookup-based PolicyRanker
try:
    preds = cql.predict(obs)
    import json
    Path('models/rl').mkdir(parents=True, exist_ok=True)
    (Path('models/rl') / 'cql_policy_predictions.json').write_text(json.dumps([int(p) for p in preds]))
    print('saved cql predictions to models/rl/cql_policy_predictions.json')
except Exception as e:
    print('warning: could not export cql predictions:', e)
