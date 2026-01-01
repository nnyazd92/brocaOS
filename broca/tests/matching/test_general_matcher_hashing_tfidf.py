from __future__ import annotations

from broca.matching import GeneralMatcher, MatcherConfig


def test_hashing_tfidf_similarity_can_rescue_non_substring():
    # These are semantically close but not substrings of each other.
    a = "install playwright browsers on linux"
    b = "how do i install playwright on ubuntu?"

    cfg = MatcherConfig(
        enable_hashing_tfidf=True,
        enable_sentence_transformers=False,
        enable_rapidfuzz=False,
        text_threshold=0.5,  # make sure we can observe a match
    )
    m = GeneralMatcher(cfg)

    r = m.match({"text": a}, {"text": b})
    assert r.matched is True
    assert r.confidence >= 0.5

