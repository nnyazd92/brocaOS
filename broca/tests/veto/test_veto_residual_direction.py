from __future__ import annotations

import numpy as np

from broca.veto.guard import VetoGuard


def _mk_guard(*, residual_direction: str) -> VetoGuard:
    g = VetoGuard(
        enabled=True,
        model_type="gru",
        input_dim=12,
        seq_len=16,
        hidden_dim=32,
        lr=0.001,
        norm_alpha=0.01,
        sigma_mult=1.5,
        fixed_margin=0.0,
        anomaly_mode="residual",
        residual_alpha=0.05,
        residual_k=3.0,
        residual_min_samples=0,  # no warmup gating for this unit test
        residual_direction=residual_direction,
        hysteresis_h=0.05,
        persist_n=8,
        persist_m=5,
        clear_k=3,
        max_train_steps_per_obs=0,
        min_train_interval_s=0.0,
        persist_latch=False,
        state_path=None,
        model_path=None,
        save_interval_s=0.0,
    )
    # Force baseline so err_thr is predictable and small.
    g._res_seen = 999
    g._res_mean = 0.0
    g._res_var = 1e-8
    return g


def test_residual_down_direction_does_not_flag_high_surprise(monkeypatch):
    g = _mk_guard(residual_direction="down")

    # Pretend the predictor expected a small I, but actual I is much higher.
    monkeypatch.setattr(g, "_predict_next_i_from_prev", lambda: (0.4, 0.1, {"ok": True, "mu": 0.4, "sigma": 0.1}))

    d = g.check(
        x_t=np.zeros((12,), dtype=np.float64),
        reason="unit_test",
        kappa_last=0.8,
        kappa_integrated=1.6,
    )
    assert bool(d.debug.get("violation")) is False
    res = d.debug.get("residual") or {}
    assert res.get("direction") == "down"
    # abs_err is large; down_err should be 0; metric used is down_err
    assert float(res.get("abs_err")) > 1.0
    assert float(res.get("down_err")) == 0.0
    assert float(res.get("err")) == 0.0


def test_residual_down_direction_flags_low_surprise(monkeypatch):
    g = _mk_guard(residual_direction="down")
    monkeypatch.setattr(g, "_predict_next_i_from_prev", lambda: (1.6, 0.1, {"ok": True, "mu": 1.6, "sigma": 0.1}))

    d = g.check(
        x_t=np.zeros((12,), dtype=np.float64),
        reason="unit_test",
        kappa_last=0.8,
        kappa_integrated=0.2,
    )
    assert bool(d.debug.get("violation")) is True
    res = d.debug.get("residual") or {}
    assert float(res.get("down_err")) > 1.0
    assert float(res.get("err")) == float(res.get("down_err"))


def test_residual_both_direction_flags_high_surprise(monkeypatch):
    g = _mk_guard(residual_direction="both")
    monkeypatch.setattr(g, "_predict_next_i_from_prev", lambda: (0.4, 0.1, {"ok": True, "mu": 0.4, "sigma": 0.1}))

    d = g.check(
        x_t=np.zeros((12,), dtype=np.float64),
        reason="unit_test",
        kappa_last=0.8,
        kappa_integrated=1.6,
    )
    assert bool(d.debug.get("violation")) is True
    res = d.debug.get("residual") or {}
    assert res.get("direction") == "both"
    assert float(res.get("err")) == float(res.get("abs_err"))


