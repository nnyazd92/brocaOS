"""
Deterministic local embedding stub for demos.
Generates a fixed-dimension vector (1536) deterministically from input text.
"""
import hashlib
import random
from typing import List

DIM = 1536

def _seed_from_text(text: str) -> int:
    h = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return int(h[:16], 16)

def embed_text(text: str, dim: int = DIM) -> List[float]:
    """Return a deterministic pseudo-random vector for the given text."""
    seed = _seed_from_text(text)
    rnd = random.Random(seed)
    # generate floats in range [-1,1]
    vec = [rnd.uniform(-1.0, 1.0) for _ in range(dim)]
    # normalize to unit length
    norm = sum(x*x for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

# For convenience
def embed_texts(texts: List[str], dim: int = DIM):
    return [embed_text(t, dim) for t in texts]
