from __future__ import annotations

"""SQLite-backed cache for LLM responses.

This module provides a simple key-value cache for LLM responses, intended
to be used by :class:`CachedLLMClient`.

Design goals:
- Deterministic, inspectable on-disk storage (SQLite under docs/memory).
- Thread-safe via a module-level lock.
- Minimal API surface suitable for unit tests and higher-level wrappers.

The public API is intentionally tiny:
- get_cached_response(key: str) -> dict | None
- store_cached_response(key: str, model: str, scope: str | None,
                        request_meta: dict, response: dict) -> None

Tests may monkeypatch these functions or the underlying helpers to provide
an isolated in-memory cache; this module must therefore avoid expensive
side effects at import time.
"""

from typing import Any, Dict, Optional
import json
import os
import sqlite3
from datetime import datetime, timezone
import threading


# Path is relative to the project root (Broca's "house" is ./docs)
_CACHE_DB_PATH = os.path.join("docs", "memory", "LLM_CACHE.v0.1.sqlite")
_DB_LOCK = threading.Lock()


def _ensure_db(conn: sqlite3.Connection) -> None:
    """Ensure the llm_cache table and indices exist on the given connection."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_cache (
            key TEXT PRIMARY KEY,
            model TEXT NOT NULL,
            scope TEXT,
            request_meta TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used_at TEXT NOT NULL,
            usage_count INTEGER NOT NULL DEFAULT 1
        );
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_llm_cache_model ON llm_cache(model);"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_llm_cache_scope ON llm_cache(scope);"
    )


def _open_connection() -> sqlite3.Connection:
    """Open a SQLite connection to the cache database, creating dirs as needed."""
    os.makedirs(os.path.dirname(_CACHE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_CACHE_DB_PATH, timeout=30)
    _ensure_db(conn)
    return conn


def get_cached_response(key: str) -> Optional[Dict[str, Any]]:
    """Retrieve a cached response by key.

    Returns the stored response as a dict if present, otherwise ``None``.
    Also updates the ``last_used_at`` timestamp and ``usage_count``.
    """
    now = datetime.now(timezone.utc).isoformat()

    with _DB_LOCK:
        conn = _open_connection()
        try:
            cur = conn.execute(
                "SELECT response_json FROM llm_cache WHERE key = ?",
                (key,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            conn.execute(
                "UPDATE llm_cache SET last_used_at = ?, usage_count = usage_count + 1 "
                "WHERE key = ?",
                (now, key),
            )
            conn.commit()
        finally:
            conn.close()

    response_json = row[0]
    return json.loads(response_json)


def store_cached_response(
    key: str,
    model: str,
    scope: Optional[str],
    request_meta: Dict[str, Any],
    response: Dict[str, Any],
) -> None:
    """Store or update a cached response under the given key.

    If an entry with the same key already exists, its ``created_at`` is
    preserved and ``usage_count`` is incremented while other fields are
    updated. This matches the semantics of "upsert + touch".
    """
    now = datetime.now(timezone.utc).isoformat()
    request_meta_json = json.dumps(request_meta, sort_keys=True, separators=(",", ":"))
    response_json = json.dumps(response)

    with _DB_LOCK:
        conn = _open_connection()
        try:
            # We implement an UPSERT that preserves created_at if the row exists
            # and increments usage_count.
            conn.execute(
                """
                INSERT INTO llm_cache (
                    key, model, scope, request_meta, response_json,
                    created_at, last_used_at, usage_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(key) DO UPDATE SET
                    model = excluded.model,
                    scope = excluded.scope,
                    request_meta = excluded.request_meta,
                    response_json = excluded.response_json,
                    last_used_at = excluded.last_used_at,
                    usage_count = llm_cache.usage_count + 1
                """,
                (
                    key,
                    model,
                    scope,
                    request_meta_json,
                    response_json,
                    now,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()


# --- Introspection and maintenance helpers ---

from typing import Any, Dict, Optional  # type: ignore[override]


def get_cache_stats() -> Dict[str, Any]:
    """Return basic statistics about the LLM cache.

    The result is a small JSON-serializable dict suitable for logging or
    inclusion in rehydration / shutdown summaries. All operations are
    read-only with respect to the cache contents.
    """
    with _DB_LOCK:
        conn = _open_connection()
        try:
            cur = conn.execute(
                "SELECT COUNT(*) AS n, "
                "MIN(created_at), MAX(created_at), "
                "MIN(last_used_at), MAX(last_used_at) "
                "FROM llm_cache"
            )
            row = cur.fetchone()
        finally:
            conn.close()

    if row is None:
        return {
            "row_count": 0,
            "created_at_min": None,
            "created_at_max": None,
            "last_used_at_min": None,
            "last_used_at_max": None,
        }

    count, cmin, cmax, lmin, lmax = row
    return {
        "row_count": int(count or 0),
        "created_at_min": cmin,
        "created_at_max": cmax,
        "last_used_at_min": lmin,
        "last_used_at_max": lmax,
    }


def list_cache_keys(
    limit: int = 50,
    model: Optional[str] = None,
    scope: Optional[str] = None,
    order_by: str = "last_used_at DESC",
) -> Dict[str, Any]:
    """Return a small listing of cache keys and metadata.

    This is intended for debugging and observability, not bulk export.
    """
    # Restrict order_by to a safe subset to avoid SQL injection; we only
    # allow a couple of known-good patterns and fall back otherwise.
    allowed_order = {"last_used_at DESC", "created_at DESC"}
    if order_by not in allowed_order:
        order_by = "last_used_at DESC"

    query = (
        "SELECT key, model, scope, created_at, last_used_at, usage_count "
        "FROM llm_cache"
    )
    params = []
    clauses = []
    if model is not None:
        clauses.append("model = ?")
        params.append(model)
    if scope is not None:
        clauses.append("scope = ?")
        params.append(scope)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += f" ORDER BY {order_by} LIMIT ?"
    params.append(int(limit))

    with _DB_LOCK:
        conn = _open_connection()
        try:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
        finally:
            conn.close()

    items = []
    for key, mdl, scp, c_at, l_at, count in rows:
        items.append(
            {
                "key": key,
                "model": mdl,
                "scope": scp,
                "created_at": c_at,
                "last_used_at": l_at,
                "usage_count": int(count or 0),
            }
        )

    return {"items": items}


def get_cache_health(
    stale_ttl_seconds: Optional[int] = None,
    max_rows: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute simple health indicators for the cache.

    - If ``stale_ttl_seconds`` is provided and the oldest ``last_used_at``
      is older than that, ``has_stale_entries`` will be True.
    - If ``max_rows`` is provided and the row count exceeds it,
      ``oversized`` will be True.
    """
    stats = get_cache_stats()
    from datetime import datetime, timezone  # local import to avoid cycles

    has_stale = False
    if stale_ttl_seconds is not None and stats["last_used_at_min"]:
        try:
            oldest = datetime.fromisoformat(stats["last_used_at_min"])
            # Normalize naive datetimes as UTC just in case.
            if oldest.tzinfo is None:
                oldest = oldest.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - oldest
            has_stale = age.total_seconds() > stale_ttl_seconds
        except Exception:  # pragma: no cover - defensive
            has_stale = False

    oversized = False
    if max_rows is not None:
        oversized = stats["row_count"] > max_rows

    return {
        "stats": stats,
        "has_stale_entries": has_stale,
        "oversized": oversized,
    }


# --- Eviction / TTL policies ---


def evict_stale_entries(ttl_seconds: int) -> int:
    """Delete entries whose ``last_used_at`` is older than ``ttl_seconds``.

    Returns the number of rows deleted.
    """
    if ttl_seconds <= 0:
        return 0

    from datetime import datetime, timezone  # local import to avoid cycles

    cutoff = datetime.now(timezone.utc).timestamp() - ttl_seconds

    with _DB_LOCK:
        conn = _open_connection()
        try:
            # We fetch candidates first to avoid relying on SQLite datetime
            # functions and to reuse the Python ISO8601 parsing already used
            # elsewhere. This keeps the DB schema flexible.
            cur = conn.execute(
                "SELECT key, last_used_at FROM llm_cache"
            )
            to_delete = []
            for key, last_used in cur.fetchall():
                try:
                    dt = datetime.fromisoformat(last_used)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    ts = dt.timestamp()
                    if ts < cutoff:
                        to_delete.append(key)
                except Exception:  # pragma: no cover - defensive
                    # If parsing fails, treat as non-stale to avoid
                    # accidentally deleting unknown formats.
                    continue

            deleted = 0
            if to_delete:
                conn.executemany(
                    "DELETE FROM llm_cache WHERE key = ?",
                    [(k,) for k in to_delete],
                )
                deleted = conn.total_changes
                conn.commit()
        finally:
            conn.close()

    return int(deleted)


def enforce_max_rows(max_rows: int) -> int:
    """Ensure the cache does not exceed ``max_rows`` entries.

    If there are more rows than ``max_rows``, this deletes the oldest
    entries ordered by ``last_used_at`` until the limit is satisfied.
    Returns the number of rows deleted.
    """
    if max_rows <= 0:
        return 0

    with _DB_LOCK:
        conn = _open_connection()
        try:
            cur = conn.execute("SELECT COUNT(*) FROM llm_cache")
            (count,) = cur.fetchone() or (0,)
            count = int(count or 0)
            if count <= max_rows:
                return 0

            to_evict = count - max_rows
            cur = conn.execute(
                "SELECT key FROM llm_cache "
                "ORDER BY last_used_at ASC LIMIT ?",
                (to_evict,),
            )
            keys = [row[0] for row in cur.fetchall()]
            if not keys:
                return 0

            conn.executemany(
                "DELETE FROM llm_cache WHERE key = ?",
                [(k,) for k in keys],
            )
            deleted = conn.total_changes
            conn.commit()
        finally:
            conn.close()

    return int(deleted)

