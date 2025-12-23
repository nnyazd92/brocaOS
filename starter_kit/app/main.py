from fastapi import FastAPI, HTTPException, Depends, Header
from starter_kit.app.models import *
from starter_kit.app import db
from starter_kit.app import embeddings
from uuid import uuid4
from typing import Dict, List
import threading

app = FastAPI(title="BrocaAPI (Starter)")


# Simple API-key auth using x-api-key header.
# This is single-tenant friendly but models accounts/api_keys for future SaaS use.

from hashlib import sha256

API_KEY_HEADER_NAME = "x-api-key"


async def get_auth_context(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER_NAME)) -> AuthContext:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing API key")
    key_hash = sha256(x_api_key.encode("utf-8")).hexdigest()
    record = db.get_api_key_by_hash(key_hash)
    if not record or not record.get("is_active", False):
        raise HTTPException(status_code=401, detail="invalid API key")
    db.touch_api_key_last_used(record["id"])
    return AuthContext(account_id=record["account_id"], api_key_id=record["id"])


# Note: DB-backed stores via starter_kit/app/db.py
_actuator: Dict[str, dict] = {}
_lock = threading.Lock()

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse()

@app.post("/session", response_model=SessionResponse)
def create_session(req: SessionCreate, auth: AuthContext = Depends(get_auth_context)):
    # create session in DB
    session_id = db.create_session(req.user_id)
    # log usage: 1 unit per session created
    db.log_usage(auth.account_id, auth.api_key_id, "/session", "POST", units=1)
    return SessionResponse(session_id=session_id, user_id=req.user_id)

@app.post("/memory/upsert")
def memory_upsert(req: MemoryUpsertRequest):
    # ensure session exists
    if not db.get_session(req.session_id):
        raise HTTPException(status_code=404, detail="session not found")
    items = []
    for it in req.items:
        obj = it.model_dump()
        text = obj.get('text') or ''
        emb = embeddings.embed_text(text)
        obj['embedding'] = emb
        items.append(obj)
    count = db.upsert_memories(req.session_id, items)
    return {"ok": True, "count": count}

@app.post("/memory/query")
def memory_query(req: MemoryQueryRequest, auth: AuthContext = Depends(get_auth_context)):
    if not db.get_session(req.session_id):
        raise HTTPException(status_code=404, detail="session not found")
    top = req.top if req.top and req.top>0 else 5
    qvec = embeddings.embed_text(req.query)
    results = db.query_memories(req.session_id, qvec, top=top)
    # log usage: units = length of query string
    db.log_usage(auth.account_id, auth.api_key_id, "/memory/query", "POST", units=len(req.query))
    return {"results": [{"id": r["id"], "text": r["text"], "score": r["score"]} for r in results]}

@app.post("/actuator/request", response_model=ActuatorResponse)
def actuator_request(req: ActuatorRequest, auth: AuthContext = Depends(get_auth_context)):
    if not db.get_session(req.session_id):
        raise HTTPException(status_code=404, detail="session not found")
    request_id = str(uuid4())
    with _lock:
        _actuator[request_id] = {"session_id": req.session_id, "action": req.action, "payload": req.payload, "status": "pending"}
    # log usage: 1 unit per actuator request
    db.log_usage(auth.account_id, auth.api_key_id, "/actuator/request", "POST", units=1)
    return ActuatorResponse(request_id=request_id, status="pending")

@app.post("/actuator/approve", response_model=ActuatorResponse)
def actuator_approve(req: ActuatorApproveRequest, auth: AuthContext = Depends(get_auth_context)):
    if req.request_id not in _actuator:
        raise HTTPException(status_code=404, detail="request not found")
    with _lock:
        _actuator[req.request_id]["status"] = "approved"
        _actuator[req.request_id]["approver"] = req.approver
    # log usage: 1 unit per actuator approval
    db.log_usage(auth.account_id, auth.api_key_id, "/actuator/approve", "POST", units=1)
    return ActuatorResponse(request_id=req.request_id, status="approved")



@app.get("/admin/usage")
def admin_usage(auth: AuthContext = Depends(get_auth_context)):
    """Return recent usage events for the authenticated account.

    This is a simple introspection endpoint useful during development and
    for early monetization experiments. In a real deployment you'd likely
    restrict this further or build a dedicated admin surface.
    """
    pool = db.get_pool()
    rows = []
    with pool.connection() as conn:
        cur = conn.execute(
            "SELECT endpoint, method, units, created_at FROM usage_events WHERE account_id = %s ORDER BY created_at DESC LIMIT 100",
            (auth.account_id,),
        )
        for r in cur.fetchall():
            rows.append({
                "endpoint": r[0],
                "method": r[1],
                "units": r[2],
                "created_at": r[3].isoformat() if hasattr(r[3], 'isoformat') else str(r[3]),
            })
    return {"usage": rows}


# simple root
@app.get("/", include_in_schema=False)
def root():
    return {"msg": "BrocaAPI starter"}
