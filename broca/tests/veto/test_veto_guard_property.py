from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, strategies as st

from broca.veto.guard import VetoGuard


def _mk_guard(*, persist_n: int, persist_m: int, clear_k: int, hysteresis_h: float) -> VetoGuard:
    # Initialize disabled to avoid torch init; tests monkeypatch threshold.
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
        hysteresis_h=float(hysteresis_h),
        persist_n=int(persist_n),
        persist_m=int(persist_m),
        clear_k=int(clear_k),
        max_train_steps_per_obs=0,
        min_train_interval_s=0.0,
    )
    g.enabled = True
    return g


def _force_threshold(g: VetoGuard, thr: float) -> None:
    g._predict_threshold = lambda: (float(thr), {"ok": True, "forced": True})  # type: ignore[attr-defined]
    g._train_if_ready = lambda: {"trained": False, "reason": "test_forced"}  # type: ignore[attr-defined]


@given(
    persist_n=st.integers(min_value=1, max_value=12),
    persist_m=st.integers(min_value=1, max_value=12),
    flags=st.lists(st.booleans(), min_size=1, max_size=50),
)
def test_veto_persistence_window_triggers_only_on_sustained_below_threshold(persist_n: int, persist_m: int, flags: list[bool]):
    persist_m = min(persist_m, persist_n)
    g = _mk_guard(persist_n=persist_n, persist_m=persist_m, clear_k=999, hysteresis_h=0.1)
    _force_threshold(g, 1.0)

    # Feed sequence: violation=True => I=0.0 (<1.0), else I=2.0 (>1.0)
    active = False
    window: list[bool] = []
    for i, v in enumerate(flags):
        I = 0.0 if v else 2.0
        x = g.build_time_slice(kappa_last=1.0, kappa_integrated=I, rl_signals=None, tool_name="t")
        d = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=I)

        # Expected trigger when, and only when, last N contains >= M violations (and once active stays active).
        window.append(bool(v))
        if len(window) > persist_n:
            window = window[-persist_n:]
        if not active and sum(1 for b in window if b) >= persist_m:
            active = True

        assert d.veto is bool(active)


def test_veto_off_by_one_kills_mutation_when_persist_m_equals_persist_n():
    g = _mk_guard(persist_n=3, persist_m=3, clear_k=999, hysteresis_h=0.1)
    _force_threshold(g, 1.0)

    # Only two below-threshold samples: should NOT trigger.
    for I in (0.0, 0.0):
        x = g.build_time_slice(kappa_last=1.0, kappa_integrated=I, rl_signals=None, tool_name="t")
        d = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=I)
        assert d.veto is False

    # Third below-threshold sample: should trigger.
    x = g.build_time_slice(kappa_last=1.0, kappa_integrated=0.0, rl_signals=None, tool_name="t")
    d = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=0.0)
    assert d.veto is True


def test_veto_clears_only_after_hysteresis_and_clear_k_consecutive():
    g = _mk_guard(persist_n=3, persist_m=2, clear_k=2, hysteresis_h=0.1)
    _force_threshold(g, 1.0)

    # Trigger veto with two violations.
    for I in (0.0, 0.0):
        x = g.build_time_slice(kappa_last=1.0, kappa_integrated=I, rl_signals=None, tool_name="t")
        _ = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=I)
    assert g.check(
        x_t=g.build_time_slice(kappa_last=1.0, kappa_integrated=0.0, rl_signals=None, tool_name="t"),
        reason="test",
        kappa_last=1.0,
        kappa_integrated=0.0,
    ).veto is True

    # One sample above threshold but NOT above threshold + hysteresis: should not clear.
    x = g.build_time_slice(kappa_last=1.0, kappa_integrated=1.05, rl_signals=None, tool_name="t")
    d = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=1.05)
    assert d.veto is True

    # Two consecutive safely above thr + h => clears.
    for I in (1.2, 1.2):
        x = g.build_time_slice(kappa_last=1.0, kappa_integrated=I, rl_signals=None, tool_name="t")
        d = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=I)
    assert d.veto is False


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_veto_guard_handles_nonfinite_inputs_fail_open(bad: float):
    g = _mk_guard(persist_n=3, persist_m=2, clear_k=2, hysteresis_h=0.1)
    _force_threshold(g, 1.0)

    # Non-finite κ_integrated should not crash; it should be treated as 0.0 internally.
    x = g.build_time_slice(kappa_last=1.0, kappa_integrated=bad, rl_signals=None, tool_name="t")
    d = g.check(x_t=x, reason="test", kappa_last=1.0, kappa_integrated=bad)
    assert isinstance(d.veto, bool)
    assert math.isfinite(float(d.threshold))


