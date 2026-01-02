from __future__ import annotations

from pathlib import Path

from broca.memory.priming import priming_used_score
from broca.memory.priming_learning import PrimingPolicyStore

from hypothesis import given, strategies as st, settings, HealthCheck


def test_priming_used_score_detects_overlap():
    primed = (
        "PRIMED MEMORY (why it matches, provenance, confidence, last_used):\n\n"
        "Key facts:\n"
        "- Use pytest to run targeted tests\n\n"
        "Action implications:\n"
        "- Run pytest -q\n"
    )
    assistant = "Next, we'll use pytest to run targeted tests and confirm behavior."
    score = priming_used_score(assistant_text=assistant, primed_card_text=primed)
    assert 0.05 <= score <= 1.0


def test_policy_store_updates_and_persists(tmp_path: Path):
    path = tmp_path / "priming_policy.json"
    store = PrimingPolicyStore(path=path, lr=0.2)
    b0 = store.get_boost(mode="chat", namespace="ns")
    assert b0 == 1.0

    b1 = store.update(mode="chat", namespace="ns", used_score=1.0)
    assert b1 > b0
    store.save()

    store2 = PrimingPolicyStore(path=path, lr=0.2)
    b2 = store2.get_boost(mode="chat", namespace="ns")
    assert b2 == b1


@given(
    assistant=st.text(max_size=400),
    primed=st.text(max_size=400),
)
@settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
def test_priming_used_score_is_deterministic_and_bounded(assistant: str, primed: str):
    s1 = priming_used_score(assistant_text=assistant, primed_card_text=primed)
    s2 = priming_used_score(assistant_text=assistant, primed_card_text=primed)
    assert 0.0 <= s1 <= 1.0
    assert s1 == s2


def test_policy_store_load_invalid_json_is_safe(tmp_path: Path):
    path = tmp_path / "priming_policy.json"
    path.write_text("{not json", encoding="utf-8")
    store = PrimingPolicyStore(path=path)
    assert store.get_boost(mode="chat", namespace="ns") == 1.0

