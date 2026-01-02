from __future__ import annotations

from broca.matching import GeneralMatcher, MatcherConfig


def test_field_thresholds_apply_to_full_nested_paths():
    # Without path-aware thresholds, the substring fast-path (0.92) would pass default 0.82.
    # With a strict per-path threshold, it should fail.
    cfg = MatcherConfig(
        field_thresholds_csv="goal.user_message:0.95",
        enable_sentence_transformers=False,
        enable_hashing_tfidf=False,
        enable_simhash=False,
        enable_datasketch_minhash=False,
        enable_rapidfuzz=False,
    )
    m = GeneralMatcher(cfg)

    pattern = {"goal": {"user_message": "hello"}}
    content = {"goal": {"user_message": "hello world"}}

    r = m.match(pattern, content)
    assert r.matched is False


def test_hard_keys_apply_to_full_nested_paths():
    cfg = MatcherConfig(
        hard_keys_csv="goal.user_message",
        enable_sentence_transformers=False,
        enable_hashing_tfidf=False,
        enable_simhash=False,
        enable_datasketch_minhash=False,
        enable_rapidfuzz=False,
    )
    m = GeneralMatcher(cfg)

    pattern = {"goal": {"user_message": "hello"}}
    content = {"goal": {"user_message": "hello world"}}

    r = m.match(pattern, content)
    assert r.matched is False

