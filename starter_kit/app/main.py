from fastapi import FastAPI, HTTPException
from .models import *
from uuid import uuid4
from typing import Dict, List
import threading

app = FastAPI(title="BrocaAPI (Starter)")

# Simple in-memory stores (note: not shared across processes/workers)
_sessions: Dict[str, dict] = {}
_memories: Dict[str, List[dict]] = {}
_actuator: Dict[str, dict] = {}
_lock = threading.Lock()

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse()

@app.post("/session", response_model=SessionResponse)
def create_session(req: SessionCreate):
    session_id = str(uuid4())
    with _lock:
        _sessions[session_id] = {"user_id": req.user_id}
        _memories[session_id] = []
    return SessionResponse(session_id=session_id, user_id=req.user_id)

@app.post("/memory/upsert")
def memory_upsert(req: MemoryUpsertRequest):
    if req.session_id not in _sessions:
        raise HTTPException(status_code=404, detail="session not found")
    with _lock:
        # naive upsert: replace items with same id or append
        existing = {m['id']: m for m in _memories.get(req.session_id, [])}
        for item in req.items:
            existing[item.id] = item.model_dump()
        _memories[req.session_id] = list(existing.values())
    return {"ok": True, "count": len(req.items)}

@app.post("/memory/query")
def memory_query(req: MemoryQueryRequest):
    if req.session_id not in _sessions:
        raise HTTPException(status_code=404, detail="session not found")
    # naive similarity: return items containing any query word, otherwise return all with score 0
    items = _memories.get(req.session_id, [])
    q_words = set(req.query.lower().split())
    results = []
    for m in items:
        text = m.get('text','').lower()
        score = 0.0
        for w in q_words:
            if w in text:
                score += 1.0
        results.append({"id": m['id'], "text": m['text'], "score": score})
    # sort by score desc
    results.sort(key=lambda r: r['score'], reverse=True)
    top = results[: req.top if req.top and req.top>0 else 5]
    return {"results": top}

@app.post("/actuator/request", response_model=ActuatorResponse)
def actuator_request(req: ActuatorRequest):
    if req.session_id not in _sessions:
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

