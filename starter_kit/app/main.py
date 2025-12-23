from fastapi import FastAPI, HTTPException
from .models import *
from . import db
from . import embeddings
from uuid import uuid4
from typing import Dict, List
import threading

app = FastAPI(title="BrocaAPI (Starter)")

# Note: DB-backed stores via starter_kit/app/db.py
_actuator: Dict[str, dict] = {}
_lock = threading.Lock()

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse()

@app.post("/session", response_model=SessionResponse)
def create_session(req: SessionCreate):
    # create session in DB
    session_id = db.create_session(req.user_id)
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
def memory_query(req: MemoryQueryRequest):
    if not db.get_session(req.session_id):
        raise HTTPException(status_code=404, detail="session not found")
    top = req.top if req.top and req.top>0 else 5
    qvec = embeddings.embed_text(req.query)
    results = db.query_memories(req.session_id, qvec, top=top)
    return {"results": [{"id": r['id'], "text": r['text'], "score": r['score']} for r in results]}

@app.post("/actuator/request", response_model=ActuatorResponse)
def actuator_request(req: ActuatorRequest):
    if not db.get_session(req.session_id):
        raise HTTPException(status_code=404, detail="session not found")
    request_id = str(uuid4())
    with _lock:
        _actuator[request_id] = {"session_id": req.session_id, "action": req.action, "payload": req.payload, "status": "pending"}
    return ActuatorResponse(request_id=request_id, status="pending")

@app.post("/actuator/approve", response_model=ActuatorResponse)
def actuator_approve(req: ActuatorApproveRequest):
    if req.request_id not in _actuator:
        raise HTTPException(status_code=404, detail="request not found")
    with _lock:
        _actuator[req.request_id]["status"] = "approved"
        _actuator[req.request_id]["approver"] = req.approver
    return ActuatorResponse(request_id=req.request_id, status="approved")

# simple root
@app.get("/", include_in_schema=False)
def root():
    return {"msg": "BrocaAPI starter"}
