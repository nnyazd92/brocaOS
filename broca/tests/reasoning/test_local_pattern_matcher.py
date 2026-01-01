from __future__ import annotations

from hypothesis import given, strategies as st

from broca.reasoning.local_pattern_matcher import LocalPatternMatcher
from broca.reasoning.pattern_matcher import PatternMatcher


def test_local_pattern_matcher_dict_subset_exact_match():
    m = LocalPatternMatcher()
    ok, conf = m.match_with_confidence(
        {"type": "goal", "status": "active"},
        {"type": "goal", "status": "active", "name": "x"},
    )
    assert ok is True
    assert conf >= 0.99


def test_local_pattern_matcher_contains_operator():
    m = LocalPatternMatcher()
    ok, conf = m.match_with_confidence(
        {"type": "memory", "tags": {"contains": "related"}},
        {"type": "memory", "tags": ["foo", "related", "bar"]},
    )
    assert ok is True
    assert conf >= 0.9


def test_local_pattern_matcher_text_field_substring():
    m = LocalPatternMatcher()
    ok, conf = m.match_with_confidence(
        {"text": "python"},
        {"text": "I love Python and Rust."},
    )
    assert ok is True
    assert conf >= 0.82


def test_local_pattern_matcher_contradiction_check_antonyms():
    m = LocalPatternMatcher()
    ok, conf = m.match_with_confidence(
        {"type": "contradiction_check", "text": "I like cats"},
        {"type": "text", "text": "I hate cats"},
    )
    assert ok is True
    assert conf >= 0.7


def test_local_pattern_matcher_contradiction_check_same_statement_not_contradiction():
    m = LocalPatternMatcher()
    ok, conf = m.match_with_confidence(
        {"type": "contradiction_check", "text": "I like cats"},
        {"type": "text", "text": "I like cats"},
    )
    assert ok is False
    assert conf == 0.0


def test_local_pattern_matcher_contradiction_check_low_overlap_not_contradiction():
    m = LocalPatternMatcher()
    ok, conf = m.match_with_confidence(
        {"type": "contradiction_check", "text": "I like cats"},
        {"type": "text", "text": "I hate broccoli"},
    )
    assert ok is False
    assert conf < 0.5


def test_pattern_matcher_defaults_to_local_no_network():
    pm = PatternMatcher(llm_client=None)
    assert pm.match(
        {"type": "memory", "tags": {"contains": "related"}},
        {"type": "memory", "tags": ["related"]},
    ) is True


@given(
    base=st.dictionaries(
        keys=st.text(min_size=1, max_size=10).filter(lambda s: s != "description"),
        values=st.one_of(
            st.integers(min_value=-10, max_value=10),
            st.booleans(),
            st.text(min_size=0, max_size=20),
        ),
        min_size=1,
        max_size=8,
    ),
    subset_keys=st.sets(st.text(min_size=1, max_size=10), min_size=0, max_size=8),
)
def test_local_pattern_matcher_subset_property(base, subset_keys):
    # Restrict subset_keys to keys present in base.
    subset = {k: base[k] for k in subset_keys if k in base}
    m = LocalPatternMatcher()
    ok, _conf = m.match_with_confidence(subset, base)
    assert ok is True
