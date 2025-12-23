import os
from psycopg_pool import ConnectionPool
import uuid
from typing import List, Dict, Any
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/broca')

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(DATABASE_URL)
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
            # Use UPSERT
            conn.execute(
                """
                INSERT INTO memories (id, session_id, text, meta, created_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text, meta = EXCLUDED.meta
                """,
                (item['id'], session_id, item.get('text'), item.get('meta') or {})
            )
            count += 1
    return count

def query_memories(session_id: str, query: str, top: int = 5) -> List[Dict[str, Any]]:
    pool = get_pool()
    results = []
    q_words = set(query.lower().split())
    with pool.connection() as conn:
        rows = conn.execute("SELECT id, text, meta FROM memories WHERE session_id = %s", (session_id,)).fetchall()
        for row in rows:
            text = (row[1] or "")
            score = 0
            low = text.lower()
            for w in q_words:
                if w in low:
                    score += 1
            results.append({"id": row[0], "text": text, "meta": row[2], "score": score})
    results.sort(key=lambda r: r['score'], reverse=True)
    return results[:top]

