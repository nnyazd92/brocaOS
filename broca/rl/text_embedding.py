"""
Deterministic fixed-size text embeddings for RL features.

We intentionally avoid heavyweight embedding models here. This module provides a
stable hashing-based embedding ("feature hashing") that:
- is deterministic across processes/restarts (sha256, not Python hash())
- is fast and local (no network calls)
- produces a fixed-size float vector suitable for concatenation to numeric features
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable, List

import numpy as np

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _stable_hash_u64(text: str) -> int:
    h = hashlib.sha256(text.encode("utf-8", errors="ignore")).digest()
    return int.from_bytes(h[:8], "big", signed=False)


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return _TOKEN_RE.findall(text.lower())


def hash_text_embedding(
    text: str,
    dim: int,
    *,
    seed: str = "broca.rl.text_embed.v1",
    max_chars: int = 2000,
    ngram_min: int = 1,
    ngram_max: int = 2,
) -> np.ndarray:
    """
    Produce a deterministic hashing-based embedding for `text`.

    This is not a semantic embedding; it's a stable, lightweight representation
    that helps the policy condition on recurring textual patterns.
    """
    d = int(dim)
    if d <= 0:
        return np.zeros(0, dtype=np.float32)

    if not isinstance(text, str):
        text = "" if text is None else str(text)

    if max_chars > 0:
        text = text[: int(max_chars)]

    tokens = _tokenize(text)
    if not tokens:
        return np.zeros(d, dtype=np.float32)

    ngram_min = max(1, int(ngram_min))
    ngram_max = max(ngram_min, int(ngram_max))

    vec = np.zeros(d, dtype=np.float32)

    def _ngrams(ts: List[str]) -> Iterable[str]:
        n = len(ts)
        for k in range(ngram_min, min(ngram_max, n) + 1):
            for i in range(0, n - k + 1):
                yield " ".join(ts[i : i + k])

    count = 0
    for ng in _ngrams(tokens):
        h = _stable_hash_u64(f"{seed}:{ng}")
        idx = int(h % d)
        sign = 1.0 if (h >> 63) == 0 else -1.0
        vec[idx] += sign
        count += 1

    if count <= 0:
        return vec

    # L2 normalize to keep scale stable across text length.
    norm = float(np.linalg.norm(vec))
    if norm > 1e-8:
        vec = vec / norm
    else:
        vec = vec / max(1.0, math.sqrt(float(count)))

    return vec.astype(np.float32, copy=False)

