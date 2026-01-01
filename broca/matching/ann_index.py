from __future__ import annotations

import hashlib
import logging
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .config import MatcherConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ANNQueryResult:
    indices: List[int]
    scores: List[float]
    backend: str


class TextANNIndexCache:
    """
    Small in-memory cache for FAISS indices over a fixed candidate corpus.

    Keyed by a stable hash of the candidate strings + embedding model name.
    Intended for repeated ranking against stable corpora (skills/rules).
    """

    def __init__(self, max_size: int = 32) -> None:
        self.max_size = max(0, int(max_size))
        self._cache: Dict[str, "TextANNIndex"] = {}
        self._order: deque[str] = deque()

    def get(self, key: str) -> Optional["TextANNIndex"]:
        return self._cache.get(key)

    def set(self, key: str, idx: "TextANNIndex") -> None:
        if self.max_size <= 0:
            return
        if key in self._cache:
            self._cache[key] = idx
            return
        self._cache[key] = idx
        self._order.append(key)
        while len(self._order) > self.max_size:
            old = self._order.popleft()
            self._cache.pop(old, None)


class TextANNIndex:
    """
    ANN index for text similarity using sentence-transformers embeddings and FAISS inner product.
    Embeddings are normalized; inner product == cosine similarity.
    """

    def __init__(self, *, model: Any, texts: Sequence[str]) -> None:
        self._model = model
        self._texts = list(texts)

        self._index = None
        self._embeddings: Optional[np.ndarray] = None
        self._build()

    @property
    def size(self) -> int:
        return len(self._texts)

    @staticmethod
    def corpus_key(texts: Sequence[str], model_name: str) -> str:
        h = hashlib.sha256()
        h.update(model_name.encode("utf-8", errors="replace"))
        for t in texts:
            h.update(b"\x00")
            h.update((t or "").encode("utf-8", errors="replace"))
        return h.hexdigest()

    def _build(self) -> None:
        try:
            import faiss  # type: ignore
        except Exception as e:
            raise RuntimeError(f"faiss unavailable: {e}")

        if not self._texts:
            raise ValueError("cannot build index for empty corpus")

        emb = self._model.encode(list(self._texts), normalize_embeddings=True)
        emb = np.asarray(emb, dtype="float32")
        if emb.ndim != 2:
            raise ValueError("unexpected embedding shape")

        dim = int(emb.shape[1])
        index = faiss.IndexFlatIP(dim)
        index.add(emb)
        self._index = index
        self._embeddings = emb

    def query(self, text: str, *, top_k: int) -> ANNQueryResult:
        if self._index is None:
            return ANNQueryResult(indices=[], scores=[], backend="none")
        if not text:
            return ANNQueryResult(indices=[], scores=[], backend="faiss")

        q = self._model.encode([text], normalize_embeddings=True)
        q = np.asarray(q, dtype="float32")
        k = max(1, min(int(top_k), self.size))
        scores, idxs = self._index.search(q, k)
        idx_list = [int(i) for i in idxs[0].tolist() if int(i) >= 0]
        score_list = [float(s) for s in scores[0].tolist()][: len(idx_list)]
        return ANNQueryResult(indices=idx_list, scores=score_list, backend="faiss")


def try_rank_with_faiss(
    *,
    cfg: MatcherConfig,
    cache: TextANNIndexCache,
    model: Any,
    model_name: str,
    query: str,
    candidates: Sequence[str],
    top_k: int,
) -> Optional[ANNQueryResult]:
    if not cfg.enable_faiss:
        return None
    if not query or not candidates:
        return ANNQueryResult(indices=[], scores=[], backend="faiss")
    if len(candidates) < max(1, int(cfg.ann_min_candidates)):
        return None

    key = TextANNIndex.corpus_key(candidates, model_name=model_name)
    idx = cache.get(key)
    if idx is None:
        try:
            idx = TextANNIndex(model=model, texts=candidates)
            cache.set(key, idx)
        except Exception as e:
            logger.debug(f"FAISS ANN build failed: {e}", exc_info=True)
            return None

    try:
        return idx.query(query, top_k=top_k)
    except Exception as e:
        logger.debug(f"FAISS ANN query failed: {e}", exc_info=True)
        return None

