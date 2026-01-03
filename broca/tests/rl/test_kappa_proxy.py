from __future__ import annotations

import numpy as np

from broca.rl.kappa_proxy import KappaProxyTracker


def test_kappa_proxy_returns_bounded_values():
    tr = KappaProxyTracker()
    z0 = np.zeros((16,), dtype=np.float32)
    z1 = np.ones((16,), dtype=np.float32) * 0.1
    z2 = np.ones((16,), dtype=np.float32) * 0.2

    p0 = tr.update(z_t=z0, rl_signals={"dissonance_reward": 0.5, "coherence_reward": 0.5, "surprise_reward": 0.5}, success=True, tool_name="A")
    p1 = tr.update(z_t=z1, rl_signals={"dissonance_reward": 0.5, "coherence_reward": 0.5, "surprise_reward": 0.5}, success=True, tool_name="A")
    p2 = tr.update(z_t=z2, rl_signals={"dissonance_reward": 0.5, "coherence_reward": 0.5, "surprise_reward": 0.5}, success=True, tool_name="B")

    for p in (p0, p1, p2):
        assert 0.0 <= float(p["kappa"]) <= 1.0
        assert 0.0 <= float(p["kappa_contr"]) <= 1.0
        assert 0.0 <= float(p["kappa_err"]) <= 1.0


def test_kappa_proxy_penalizes_failures_and_incoherence():
    tr = KappaProxyTracker()
    z = np.zeros((16,), dtype=np.float32)

    good = tr.update(z_t=z, rl_signals={"dissonance_reward": 0.0, "coherence_reward": 1.0, "surprise_reward": 0.0}, success=True, tool_name="A")
    bad = tr.update(z_t=z, rl_signals={"dissonance_reward": 1.0, "coherence_reward": 0.0, "surprise_reward": 1.0}, success=False, tool_name="B")
    assert float(bad["kappa"]) <= float(good["kappa"])


