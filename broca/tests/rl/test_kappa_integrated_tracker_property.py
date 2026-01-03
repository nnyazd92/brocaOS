from __future__ import annotations

from hypothesis import given, strategies as st

from broca.rl.kappa_integrated import KappaIntegratedTracker


@given(
    kappas=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False, width=32),
        min_size=1,
        max_size=200,
    )
)
def test_kappa_integrated_tracker_is_finite_and_nonnegative_for_kappa_in_0_1(kappas):
    tr = KappaIntegratedTracker()
    now = 0.0
    last = tr.value
    for k in kappas:
        # Use deterministic timestamps so dt is stable and clamped logic is exercised.
        now += 1.0
        v = tr.update(float(k), now=now)
        assert v == v  # not NaN
        assert v != float("inf")
        assert v != float("-inf")
        assert v >= 0.0
        # With κ in [0,1] and λ>=0, I should not jump to negative values.
        assert v >= 0.0
        last = v


