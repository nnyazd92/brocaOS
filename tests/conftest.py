import hashlib
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from broca.memory.manager import MemoryManager
from broca.memory.storage import MemoryStorage


class FakeEmbeddingService:
    def __init__(self, dimension: int = 8) -> None:
        self.dimension = dimension

    def generate_embedding(self, text: str) -> List[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        numbers = [b for b in seed[: self.dimension]]
        midpoint = sum(numbers) / float(self.dimension) if numbers else 1.0
        return [((num - midpoint) / 128.0) for num in numbers]


class FakeVectorIndex:
    def __init__(self, dimension: int) -> None:
        self.dimension = dimension
        self.index_path = None
        self.vectors: Dict[int, List[float]] = {}
        self.insert_order: List[int] = []

    def add_vector(self, memory_id: int, embedding: List[float]) -> None:
        if len(embedding) != self.dimension:
            raise ValueError(f"Embedding dimension {len(embedding)} does not match {self.dimension}")
        self.vectors[memory_id] = embedding
        if memory_id not in self.insert_order:
            self.insert_order.append(memory_id)

    def search_similar(self, query_embedding: List[float], k: int = 5) -> List[Tuple[int, float]]:
        if not self.vectors:
            return []
        if len(query_embedding) != self.dimension:
            raise ValueError(f"Query embedding dimension {len(query_embedding)} does not match {self.dimension}")

        def cosine(vec: List[float], other: List[float]) -> float:
            dot = sum(a * b for a, b in zip(vec, other))
            denom = math.sqrt(sum(a * a for a in vec)) * math.sqrt(sum(b * b for b in other))
            return dot / denom if denom else 0.0

        scored = [
            (memory_id, cosine(query_embedding, embedding))
            for memory_id, embedding in self.vectors.items()
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:k]

    def remove_vector(self, memory_id: int) -> None:
        self.vectors.pop(memory_id, None)
        if memory_id in self.insert_order:
            self.insert_order.remove(memory_id)

    def save_index(self) -> None:  # pragma: no cover - no-op for fake index
        return

    def get_count(self) -> int:
        return len(self.vectors)

    def get_memory_ids(self) -> List[int]:
        return list(self.vectors.keys())

    def clear(self) -> None:
        self.vectors.clear()
        self.insert_order.clear()


@pytest.fixture
def temp_storage_path(tmp_path):
    return tmp_path / "memory.db"


@pytest.fixture
def fake_embedding_service():
    return FakeEmbeddingService()


@pytest.fixture
def fake_vector_index(fake_embedding_service):
    return FakeVectorIndex(dimension=fake_embedding_service.dimension)


@pytest.fixture
def memory_manager(temp_storage_path, fake_vector_index, fake_embedding_service):
    storage = MemoryStorage(str(temp_storage_path))
    manager = MemoryManager(storage=storage, vector_index=fake_vector_index, embedding_service=fake_embedding_service)
    yield manager
    storage.close()
