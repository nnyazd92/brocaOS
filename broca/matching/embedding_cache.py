from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def _now() -> float:
    return float(time.time())


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


@dataclass(frozen=True)
class EmbeddingCacheConfig:
    enabled: bool
    path: str
    max_entries: int


class SQLiteEmbeddingCache:
    """
    Disk-backed embedding cache (SQLite).

    Keyed by (model_name, text_hash) so it is safe across model changes.
    Stores float32 vectors as raw bytes.
    """

    def __init__(self, cfg: EmbeddingCacheConfig) -> None:
        self.cfg = cfg
        self._lock = Lock()
        self._path = Path(cfg.path)
        self._conn: Optional[sqlite3.Connection] = None

        if not self.cfg.enabled:
            return

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._connect()
        self._init_schema()

    def _connect(self) -> None:
        self._conn = sqlite3.connect(str(self._path), timeout=30.0, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute("PRAGMA temp_store=MEMORY;")

    def _init_schema(self) -> None:
        assert self._conn is not None
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                key TEXT PRIMARY KEY,
                dim INTEGER NOT NULL,
                vec BLOB NOT NULL,
                created_at REAL NOT NULL,
                last_access REAL NOT NULL
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS embeddings_last_access ON embeddings(last_access)")
        self._conn.commit()

    def make_key(self, *, model_name: str, text: str) -> str:
        # We hash the text so the DB does not store raw content.
        return _sha256(f"{model_name}\x00{text}")

    def get_many(self, keys: Sequence[str]) -> Dict[str, np.ndarray]:
        if not self.cfg.enabled or not keys:
            return {}
        assert self._conn is not None

        out: Dict[str, np.ndarray] = {}
        now = _now()

        # SQLite has a limit on bound variables; chunk queries.
        CHUNK = 500
        with self._lock:
            for i in range(0, len(keys), CHUNK):
                chunk = keys[i : i + CHUNK]
                q = ",".join(["?"] * len(chunk))
                rows = self._conn.execute(
                    f"SELECT key, dim, vec FROM embeddings WHERE key IN ({q})",
                    list(chunk),
                ).fetchall()
                for k, dim, vec in rows:
                    try:
                        arr = np.frombuffer(vec, dtype=np.float32)
                        if int(dim) > 0 and arr.size == int(dim):
                            out[str(k)] = arr
                    except Exception:
                        continue
                # Update last_access for hits (best-effort).
                if rows:
                    try:
                        self._conn.executemany(
                            "UPDATE embeddings SET last_access=? WHERE key=?",
                            [(now, str(r[0])) for r in rows],
                        )
                    except Exception:
                        pass
            try:
                self._conn.commit()
            except Exception:
                pass

        return out

    def put_many(self, items: Sequence[Tuple[str, np.ndarray]]) -> None:
        if not self.cfg.enabled or not items:
            return
        assert self._conn is not None
        now = _now()

        rows = []
        for key, vec in items:
            try:
                v = np.asarray(vec, dtype=np.float32).reshape(-1)
                if v.size <= 0:
                    continue
                rows.append((str(key), int(v.size), sqlite3.Binary(v.tobytes()), now, now))
            except Exception:
                continue

        if not rows:
            return

        with self._lock:
            self._conn.executemany(
                "INSERT OR REPLACE INTO embeddings(key, dim, vec, created_at, last_access) VALUES(?,?,?,?,?)",
                rows,
            )
            self._evict_if_needed()
            self._conn.commit()

    def _evict_if_needed(self) -> None:
        if self.cfg.max_entries <= 0:
            return
        assert self._conn is not None
        try:
            (n,) = self._conn.execute("SELECT COUNT(1) FROM embeddings").fetchone()
            n = int(n)
        except Exception:
            return
        if n <= self.cfg.max_entries:
            return
        to_delete = max(0, n - self.cfg.max_entries)
        if to_delete <= 0:
            return
        try:
            self._conn.execute(
                "DELETE FROM embeddings WHERE key IN (SELECT key FROM embeddings ORDER BY last_access ASC LIMIT ?)",
                (int(to_delete),),
            )
        except Exception:
            return


class CachedEmbeddingModel:
    """
    Wrap a model with `.encode(texts, normalize_embeddings=...)` using a disk-backed cache.
    """

    def __init__(self, *, model: Any, model_name: str, cache: SQLiteEmbeddingCache) -> None:
        self._model = model
        self._model_name = str(model_name)
        self._cache = cache

    def encode(self, texts: Sequence[str], normalize_embeddings: bool = True, **kwargs: Any):
        texts_list = list(texts)
        if not texts_list:
            return np.zeros((0, 0), dtype=np.float32)

        # If cache disabled, just delegate.
        if not self._cache.cfg.enabled:
            return self._model.encode(texts_list, normalize_embeddings=normalize_embeddings, **kwargs)

        keys = [self._cache.make_key(model_name=self._model_name, text=(t or "")) for t in texts_list]
        cached = self._cache.get_many(keys)

        missing_texts: List[str] = []
        missing_keys: List[str] = []
        for k, t in zip(keys, texts_list):
            if k not in cached:
                missing_keys.append(k)
                missing_texts.append(t or "")

        if missing_texts:
            emb = self._model.encode(missing_texts, normalize_embeddings=normalize_embeddings, **kwargs)
            emb = np.asarray(emb, dtype=np.float32)
            if emb.ndim == 1:
                emb = emb.reshape(1, -1)
            to_put: List[Tuple[str, np.ndarray]] = []
            for k, row in zip(missing_keys, emb):
                to_put.append((k, row))
            try:
                self._cache.put_many(to_put)
            except Exception as e:
                logger.debug(f"Embedding cache write failed: {e}", exc_info=True)
            for k, row in to_put:
                cached[k] = np.asarray(row, dtype=np.float32).reshape(-1)

        # Reassemble in original order.
        dim = None
        out_rows: List[np.ndarray] = []
        for k in keys:
            v = cached.get(k)
            if v is None:
                continue
            if dim is None:
                dim = int(v.size)
            if int(v.size) != int(dim):
                # Shape mismatch: fall back to direct encode for safety.
                return self._model.encode(texts_list, normalize_embeddings=normalize_embeddings, **kwargs)
            out_rows.append(v.reshape(1, -1))

        if dim is None or len(out_rows) != len(texts_list):
            return self._model.encode(texts_list, normalize_embeddings=normalize_embeddings, **kwargs)

        return np.concatenate(out_rows, axis=0).astype(np.float32)


def load_embedding_cache_config_from_env() -> EmbeddingCacheConfig:
    enabled = os.getenv("BROCA_MATCHER_EMBED_CACHE_PERSIST", "true").lower() == "true"
    path = os.getenv("BROCA_MATCHER_EMBED_CACHE_PATH", "data/matching/embeddings.sqlite")
    max_entries = int(os.getenv("BROCA_MATCHER_EMBED_CACHE_DB_MAX_ENTRIES", "50000"))
    return EmbeddingCacheConfig(enabled=enabled, path=path, max_entries=max_entries)

