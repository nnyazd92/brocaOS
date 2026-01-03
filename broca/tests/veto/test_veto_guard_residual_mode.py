from __future__ import annotations

from broca.veto.guard import VetoGuard


def _mk_residual_guard(*, persist_n: int = 3, persist_m: int = 1, clear_k: int = 2) -> VetoGuard:
    g = VetoGuard(
        enabled=False,
        model_type="gru",
        input_dim=12,
        seq_len=4,
        hidden_dim=8,
        lr=0.001,
        norm_alpha=0.01,
        sigma_mult=1.0,
        fixed_margin=0.0,
        anomaly_mode="residual",
        residual_alpha=0.2,
        residual_k=3.0,
        residual_min_samples=2,
        hysteresis_h=0.05,
        persist_n=persist_n,
        persist_m=persist_m,
        clear_k=clear_k,
        max_train_steps_per_obs=0,
        min_train_interval_s=0.0,
    )
    g.enabled = True
    return g


def test_residual_mode_triggers_on_large_prediction_error_and_clears_on_consecutive_safe():
    g = _mk_residual_guard(persist_n=3, persist_m=1, clear_k=2)

    # Deterministic predictor: predicts I_hat = 0.0 always.
    g._predict_next_i_from_prev = lambda: (0.0, 0.1, {"ok": True, "mu": 0.0, "sigma": 0.1})  # type: ignore[attr-defined]
    g._train_if_ready = lambda: {"trained": False, "reason": "test_forced"}  # type: ignore[attr-defined]

    # Warmup: baseline collects residuals; should not veto yet.
    for I in (0.0, 0.0):
        x = g.build_time_slice(kappa_last=1.0, kappa_integrated=I, rl_signals=None, tool_name="t")
        d = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=I)
        assert d.veto is False
        assert d.debug.get("threshold_mode") == "residual"
        assert d.debug.get("residual", {}).get("enough_samples") is False

    # Big error -> should veto (persist_m=1 so immediate).
    I = 10.0
    x = g.build_time_slice(kappa_last=1.0, kappa_integrated=I, rl_signals=None, tool_name="t")
    d = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=I)
    assert d.veto is True
    assert d.debug.get("residual", {}).get("enough_samples") is True
    assert d.debug.get("violation") is True

    # Two consecutive safe steps (small error) should clear (clear_k=2).
    for I in (0.0, 0.0):
        x = g.build_time_slice(kappa_last=1.0, kappa_integrated=I, rl_signals=None, tool_name="t")
        d = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=I)
    assert d.veto is False


