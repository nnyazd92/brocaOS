from __future__ import annotations

from broca.matching import CompiledPatternSet


def test_compiled_pattern_set_indexes_nested_scalar_equality_constraints():
    patterns = [
        {"type": "goal", "goal": {"status": "active", "kind": "implementation"}},
        {"type": "goal", "goal": {"status": "done"}},
    ]
    cps = CompiledPatternSet(patterns)

    content = {"type": "goal", "goal": {"status": "active", "kind": "implementation"}}
    idxs = cps.candidate_indices_for_content(content)

    assert 0 in idxs
    assert 1 not in idxs


def test_compiled_pattern_set_does_not_overconstrain_text_like_scalar_fields():
    # Text-like fields can match fuzzily in the full matcher, so the compiled prefilter must not
    # require exact equality on them, otherwise we'd drop true matches.
    patterns = [{"type": "fact", "text": "hello"}]
    cps = CompiledPatternSet(patterns)

    content = {"type": "fact", "text": "hello world"}
    idxs = cps.candidate_indices_for_content(content)

    assert 0 in idxs


def test_compiled_pattern_set_regex_prefilter_is_conservative_for_non_string_fields():
    # GeneralMatcher applies regex to a coerced text representation, so the prefilter must not
    # drop candidates just because the field isn't a string.
    patterns = [{"type": "evt", "payload": {"regex": "bar"}}]
    cps = CompiledPatternSet(patterns)

    # payload is a dict; regex should still be considered over its text dump.
    content = {"type": "evt", "payload": {"bar": 1}}
    idxs = cps.candidate_indices_for_content(content)

    assert 0 in idxs
