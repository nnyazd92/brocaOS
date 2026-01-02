from __future__ import annotations

import pytest

from broca.matching import GeneralMatcher, MatcherConfig


def test_rank_text_candidates_bruteforce_fallback_orders_by_similarity():
    m = GeneralMatcher(MatcherConfig(enable_sentence_transformers=False))
    candidates = [
        "write unit tests for matcher",
        "install playwright on ubuntu",
        "policy gating and budgets",
        "apple banana orange",
    ]
    r = m.rank_text_candidates("playwright install linux", candidates, top_k=2)
    assert len(r.indices) == 2
    assert r.indices[0] == 1  # best match should be the playwright candidate


def test_rank_text_candidates_faiss_if_available_and_enabled():
    try:
        import faiss  # noqa: F401
        import sentence_transformers  # noqa: F401
    except Exception:
        pytest.skip("faiss/sentence-transformers not available")

    cfg = MatcherConfig(enable_sentence_transformers=True, enable_faiss=True, ann_min_candidates=2, ann_top_k=2)
    m = GeneralMatcher(cfg)

    candidates = [
        "write unit tests for matcher",
        "install playwright on ubuntu",
        "policy gating and budgets",
        "apple banana orange",
    ]
    r = m.rank_text_candidates("playwright install linux", candidates, top_k=2)
    assert r.backend in {"faiss", "bruteforce"}  # faiss may still fail to load model weights in CI
    assert len(r.indices) == 2
    assert r.indices[0] == 1

