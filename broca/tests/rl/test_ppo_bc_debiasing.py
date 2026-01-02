from __future__ import annotations

import numpy as np


def test_compute_bc_sample_weights_upsamples_minority_and_caps():
    from broca.rl.ppo_online_policy import _compute_bc_sample_weights

    # 90% class 0, 10% class 1
    actions = np.asarray([0] * 90 + [1] * 10, dtype=np.int64)
    w = _compute_bc_sample_weights(actions, alpha=1.0, max_weight=5.0)

    assert w.shape == (100,)
    # Mean is normalized ~1
    assert abs(float(w.mean()) - 1.0) < 1e-3
    # Minority should have higher weight
    assert float(w[95]) > float(w[5])
    # Cap respected
    assert float(w.max()) <= 5.0 + 1e-6


def test_sample_forced_exploration_uniform_pretraining():
    from broca.rl.ppo_online_policy import _sample_forced_exploration_action

    rng = __import__("random").Random(0)
    probs = np.asarray([0.99, 0.01], dtype=np.float32)

    # training_step=0 with uniform mode should NOT always return argmax
    xs = [
        _sample_forced_exploration_action(probs=probs, n_actions=2, training_step=0, mode="uniform", rng=rng)
        for _ in range(50)
    ]
    assert 0 in xs and 1 in xs


def test_should_run_bc_warm_start_runs_once_by_default():
    from broca.rl.ppo_online_policy import _should_run_bc_warm_start

    assert _should_run_bc_warm_start(training_step=0, bc_step=0, force=False) is True
    assert _should_run_bc_warm_start(training_step=0, bc_step=1, force=False) is False
    assert _should_run_bc_warm_start(training_step=1, bc_step=0, force=False) is False
    assert _should_run_bc_warm_start(training_step=1, bc_step=2, force=False) is False
    assert _should_run_bc_warm_start(training_step=1, bc_step=2, force=True) is True


def test_anneal_prob_decays_and_clamps():
    from broca.rl.ppo_online_policy import _anneal_prob

    assert _anneal_prob(base=0.0, min_prob=0.1, decay=0.9, progress=10) == 0.0
    assert _anneal_prob(base=0.9, min_prob=0.1, decay=1.0, progress=100) == 0.9
    p = _anneal_prob(base=0.9, min_prob=0.1, decay=0.9, progress=10)
    assert 0.1 <= p < 0.9
    assert _anneal_prob(base=0.9, min_prob=0.1, decay=0.9, progress=10_000) == 0.1


def test_stratified_reservoir_sample_caps_dominant_tool():
    from broca.rl.ppo_online_policy import _stratified_reservoir_sample_by_tool

    records = []
    for i in range(1000):
        records.append({"tool_name": "SET_GOALS", "pre_context": {"i": i}})
    for i in range(20):
        records.append({"tool_name": "READ_FILE", "pre_context": {"i": i}})

    sampled = _stratified_reservoir_sample_by_tool(records, max_total=60, max_per_tool=25, seed=0)
    assert len(sampled) <= 60
    counts = {}
    for r in sampled:
        counts[r["tool_name"]] = counts.get(r["tool_name"], 0) + 1
    assert counts.get("SET_GOALS", 0) <= 25
    assert counts.get("READ_FILE", 0) <= 20
