from __future__ import annotations

import pytest

from broca.matching import GeneralMatcher, MatcherConfig


def test_general_matcher_capabilities_reflect_installed_backends():
    m = GeneralMatcher(MatcherConfig(enable_sentence_transformers=False))
    caps = m.capabilities()
    # At least hashing TF-IDF should be available because scikit-learn is a core dep.
    assert caps.hashing_tfidf is True


def test_general_matcher_simhash_near_duplicate_if_available():
    try:
        import simhash  # noqa: F401
    except Exception:
        pytest.skip("simhash not available")

    cfg = MatcherConfig(
        enable_hashing_tfidf=False,
        enable_rapidfuzz=False,
        enable_simhash=True,
        text_threshold=0.75,
        enable_sentence_transformers=False,
    )
    m = GeneralMatcher(cfg)

    a = "BrocaOS policy macro system should be deterministic and auditable."
    b = "BrocaOS policy macro system should be deterministic & auditable!"
    r = m.match({"text": a}, {"text": b})
    assert r.matched is True
    assert r.confidence >= 0.75


def test_general_matcher_datasketch_jaccard_if_available():
    try:
        import datasketch  # noqa: F401
    except Exception:
        pytest.skip("datasketch not available")

    cfg = MatcherConfig(
        enable_hashing_tfidf=False,
        enable_rapidfuzz=False,
        enable_datasketch_minhash=True,
        text_threshold=0.5,
        enable_sentence_transformers=False,
    )
    m = GeneralMatcher(cfg)

    a = "install playwright browsers linux ubuntu"
    b = "ubuntu linux install playwright browsers"
    r = m.match({"text": a}, {"text": b})
    assert r.matched is True
    assert r.confidence >= 0.5

