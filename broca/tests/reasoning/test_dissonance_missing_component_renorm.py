"""
Missingness semantics for cognitive dissonance.

Key invariants (reward-shaping safety):
- Missing component scores must NOT be treated as 0.0 dissonance (that inflates reward).
- Overall dissonance should be the weight-renormalized average over AVAILABLE components.
- If no components are available, overall dissonance is neutral (0.5) and has_sufficient_data=False.
- RL dissonance reward must be neutral when dissonance data is insufficient, even when a
  DissonanceMetrics object is passed directly (no bypass).
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timezone

from broca.reasoning.cognitive_dissonance import DissonanceMetrics
from broca.reasoning.rl_signals import RLSignalAggregator


def test_compute_overall_renormalizes_over_available_components():
    m = DissonanceMetrics(timestamp=datetime.now(timezone.utc))
    m.logical_dissonance = 0.9
    m.factual_dissonance = 0.8
    m.behavioral_dissonance = 0.2
    m.goal_dissonance = 0.6

    # Only behavioral + goal are available
    m.component_availability = {"logical": False, "factual": False, "behavioral": True, "goal": True}
    m.weight_logical = 0.3
    m.weight_factual = 0.3
    m.weight_behavioral = 0.2
    m.weight_goal = 0.2

    overall = m.compute_overall()

    # Renormalized: (0.2*0.2 + 0.6*0.2) / (0.2+0.2) = 0.4
    assert overall == pytest.approx(0.4, abs=1e-6)


def test_compute_overall_all_components_missing_is_neutral():
    m = DissonanceMetrics(timestamp=datetime.now(timezone.utc))
    m.logical_dissonance = 0.0
    m.factual_dissonance = 0.0
    m.behavioral_dissonance = 0.0
    m.goal_dissonance = 0.0
    m.component_availability = {"logical": False, "factual": False, "behavioral": False, "goal": False}

    overall = m.compute_overall()

    assert overall == pytest.approx(0.5, abs=1e-9)
    assert m.has_sufficient_data is False


def test_rl_dissonance_reward_neutral_when_dissonance_metrics_insufficient():
    m = DissonanceMetrics(
        timestamp=datetime.now(timezone.utc),
        overall_dissonance=0.05,
        measurement_quality="estimated",
        has_sufficient_data=False,
        component_availability={"logical": False, "factual": False, "behavioral": False, "goal": False},
    )
    agg = RLSignalAggregator()
    metrics = agg.compute_signals(dissonance_metrics=m)

    # Must be neutral, not 1 - 0.05 = 0.95
    assert metrics.dissonance_reward == pytest.approx(0.5, abs=1e-9)
    assert metrics.has_dissonance_data in (False, None)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=120)
@given(
    logical=st.floats(min_value=0.0, max_value=1.0),
    factual=st.floats(min_value=0.0, max_value=1.0),
    behavioral=st.floats(min_value=0.0, max_value=1.0),
    goal=st.floats(min_value=0.0, max_value=1.0),
    avail_logical=st.booleans(),
    avail_factual=st.booleans(),
    avail_behavioral=st.booleans(),
    avail_goal=st.booleans(),
)
def test_compute_overall_matches_weighted_average_over_available(
    logical,
    factual,
    behavioral,
    goal,
    avail_logical,
    avail_factual,
    avail_behavioral,
    avail_goal,
):
    m = DissonanceMetrics(timestamp=datetime.now(timezone.utc))
    m.logical_dissonance = logical
    m.factual_dissonance = factual
    m.behavioral_dissonance = behavioral
    m.goal_dissonance = goal
    m.weight_logical = 0.3
    m.weight_factual = 0.3
    m.weight_behavioral = 0.2
    m.weight_goal = 0.2

    m.component_availability = {
        "logical": bool(avail_logical),
        "factual": bool(avail_factual),
        "behavioral": bool(avail_behavioral),
        "goal": bool(avail_goal),
    }

    overall = m.compute_overall()

    num = 0.0
    den = 0.0
    if m.component_availability["logical"]:
        num += logical * m.weight_logical
        den += m.weight_logical
    if m.component_availability["factual"]:
        num += factual * m.weight_factual
        den += m.weight_factual
    if m.component_availability["behavioral"]:
        num += behavioral * m.weight_behavioral
        den += m.weight_behavioral
    if m.component_availability["goal"]:
        num += goal * m.weight_goal
        den += m.weight_goal

    if den == 0.0:
        assert overall == pytest.approx(0.5, abs=1e-9)
        assert m.has_sufficient_data is False
    else:
        assert 0.0 <= overall <= 1.0
        assert overall == pytest.approx(num / den, abs=1e-6)


