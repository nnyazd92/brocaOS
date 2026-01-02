from __future__ import annotations

from hypothesis import given, strategies as st

from broca.rl.features import RL_SIGNAL_KEYS
from broca.rl.reward import compute_reward_from_outcome


def _signals_dict():
    # Keep values broad (including weirds); reward code should sanitize/clamp.
    keys = (
        ["composite_reward", "composite_reward_varnorm"]
        + RL_SIGNAL_KEYS
        + [f"{k}_varnorm" for k in RL_SIGNAL_KEYS]
    )
    return st.dictionaries(
        keys=st.sampled_from(keys),
        values=st.one_of(
            st.floats(allow_nan=True, allow_infinity=True, width=32),
            st.integers(min_value=-10, max_value=10),
            st.text(min_size=0, max_size=20),
            st.none(),
        ),
        max_size=20,
    )


@given(
    pre=_signals_dict() | st.none(),
    post=_signals_dict() | st.none(),
    success=st.booleans(),
    exec_ms=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    rq=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    beta=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    gamma=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_reward_is_finite_and_clamped(pre, post, success, exec_ms, rq, beta, gamma):
    r, parts = compute_reward_from_outcome(
        pre_rl_signals=pre if isinstance(pre, dict) else None,
        post_rl_signals=post if isinstance(post, dict) else None,
        intrinsic_keys=RL_SIGNAL_KEYS,
        success=success,
        execution_time_ms=float(exec_ms),
        result_quality=float(rq),
        shaping_beta=float(beta),
        shaping_gamma=float(gamma),
        use_varnorm_phi=True,
    )
    assert 0.0 <= float(r) <= 1.0
    assert parts["total"] == float(r)


