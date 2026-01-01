from __future__ import annotations

from pathlib import Path

import numpy as np

from broca.matching.embedding_cache import (
    CachedEmbeddingModel,
    EmbeddingCacheConfig,
    SQLiteEmbeddingCache,
)


class FakeModel:
    def __init__(self) -> None:
        self.calls = 0

    def encode(self, texts, normalize_embeddings=True, **kwargs):
        self.calls += 1
        # Deterministic 4-dim embedding per text (no external deps).
        out = []
        for t in texts:
            s = float(sum((ord(c) % 17) for c in (t or "")))
            v = np.array([s, s + 1, s + 2, s + 3], dtype=np.float32)
            if normalize_embeddings:
                n = float(np.linalg.norm(v) + 1e-9)
                v = v / n
            out.append(v)
        return np.stack(out, axis=0)


def test_sqlite_embedding_cache_roundtrip_and_model_wrapper(tmp_path: Path):
    db = tmp_path / "embeddings.sqlite"
    cache = SQLiteEmbeddingCache(EmbeddingCacheConfig(enabled=True, path=str(db), max_entries=10))
    model = FakeModel()
    wrapped = CachedEmbeddingModel(model=model, model_name="fake", cache=cache)

    a1 = wrapped.encode(["hello", "world"], normalize_embeddings=True)
    assert model.calls == 1

    # Second call should hit cache (no additional underlying encode call).
    a2 = wrapped.encode(["hello", "world"], normalize_embeddings=True)
    assert model.calls == 1
    assert np.allclose(a1, a2)

    # New instance should still hit disk cache.
    model2 = FakeModel()
    cache2 = SQLiteEmbeddingCache(EmbeddingCacheConfig(enabled=True, path=str(db), max_entries=10))
    wrapped2 = CachedEmbeddingModel(model=model2, model_name="fake", cache=cache2)
    a3 = wrapped2.encode(["hello", "world"], normalize_embeddings=True)
    assert model2.calls == 0
    assert np.allclose(a1, a3)

