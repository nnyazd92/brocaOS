import os
from psycopg_pool import ConnectionPool
import uuid
from typing import List, Dict, Any
from datetime import datetime

# pgvector integration
try:
    from pgvector import Vector
    from pgvector.psycopg import register_vector
except Exception:
    Vector = None
    register_vector = None

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/broca')

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(DATABASE_URL)
        # register vector type on a live connection if available
        if register_vector is not None:
            try:
                with _pool.connection() as conn:
                    register_vector(conn)
            except Exception:
                # ignore registration failures; will fail later if used
                pass
    return _pool

def create_session(user_id: str) -> str:
    session_id = str(uuid.uuid4())
    pool = get_pool()
    with pool.connection() as conn:
        conn.execute("INSERT INTO sessions (id, user_id) VALUES (%s, %s)", (session_id, user_id))
    return session_id

def get_session(session_id: str) -> Dict[str, Any] | None:
    pool = get_pool()
    with pool.connection() as conn:
        row = conn.execute("SELECT id, user_id, created_at FROM sessions WHERE id = %s", (session_id,)).fetchone()
        if row:
            return {"id": row[0], "user_id": row[1], "created_at": row[2]}
    return None

def upsert_memories(session_id: str, items: List[Dict[str, Any]]) -> int:
    pool = get_pool()
    count = 0
    with pool.connection() as conn:
        for item in items:
            emb = item.get('embedding')
            emb_val = None
            if emb is not None and Vector is not None:
                try:
                    emb_val = Vector(emb)
                except Exception:
                    emb_val = None
            # Use UPSERT
            conn.execute(
                """
                INSERT INTO memories (id, session_id, text, meta, embedding, created_at)
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text, meta = EXCLUDED.meta, embedding = EXCLUDED.embedding
                """,
                (item['id'], session_id, item.get('text'), item.get('meta') or {}, emb_val)
            )
            count += 1
    return count

def query_memories(session_id: str, query_vector: List[float], top: int = 5) -> List[Dict[str, Any]]:
    pool = get_pool()
    results = []
    vec_param = None
    if query_vector is not None and Vector is not None:
        try:
            vec_param = Vector(query_vector)
        except Exception:
            vec_param = None
    with pool.connection() as conn:
        if vec_param is not None:
            rows = conn.execute(
                "SELECT id, text, meta, embedding <-> %s as distance FROM memories WHERE session_id = %s ORDER BY distance ASC LIMIT %s",
                (vec_param, session_id, top)
            ).fetchall()
            for row in rows:
                distance = row[3]
                score = 1.0 / (1.0 + distance) if distance is not None else 0.0
                results.append({"id": row[0], "text": row[1], "meta": row[2], "score": score})
        else:
            rows = conn.execute("SELECT id, text, meta FROM memories WHERE session_id = %s LIMIT %s", (session_id, top)).fetchall()
            for row in rows:
                results.append({"id": row[0], "text": row[1], "meta": row[2], "score": 0.0})
    return results

