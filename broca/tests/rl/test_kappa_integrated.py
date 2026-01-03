from __future__ import annotations

import math

from broca.rl.kappa_integrated import KappaIntegratedConfig, KappaIntegratedTracker


def test_kappa_integrated_lambda_zero_is_plain_integral():
    tr = KappaIntegratedTracker(KappaIntegratedConfig(lam=0.0, dt_max=1000.0))
    # seed time
    tr.update(1.0, now=0.0)
    tr.update(1.0, now=2.0)
    assert abs(tr.value - 2.0) < 1e-9


def test_kappa_integrated_constant_signal_converges_to_1_over_lambda():
    lam = 2.0
    tr = KappaIntegratedTracker(KappaIntegratedConfig(lam=lam, dt_max=1000.0))
    tr.update(1.0, now=0.0)
    t = 0.0
    for _ in range(200):
        t += 0.1
        tr.update(1.0, now=t)
    # steady state should approach 1/lam
    assert abs(tr.value - (1.0 / lam)) < 0.05


def test_kappa_integrated_handles_large_dt_with_clamp():
    tr = KappaIntegratedTracker(KappaIntegratedConfig(lam=1.0, dt_max=1.0))
    tr.update(1.0, now=0.0)
    v1 = tr.update(1.0, now=1000.0)  # dt clamped to 1.0
    assert math.isfinite(v1)


