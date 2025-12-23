from pydantic import BaseModel
from typing import List, Optional, Any

class HealthResponse(BaseModel):
    status: str = "ok"

class SessionCreate(BaseModel):
    user_id: str

class SessionResponse(BaseModel):
    session_id: str
    user_id: str

class MemoryItem(BaseModel):
    id: str
    text: str
    meta: Optional[dict] = {}

class MemoryUpsertRequest(BaseModel):
    session_id: str
    items: List[MemoryItem]

class MemoryQueryRequest(BaseModel):
    session_id: str
    query: str
    top: Optional[int] = 5

class MemoryQueryResult(BaseModel):
    id: str
    text: str
    score: float

class ActuatorRequest(BaseModel):
    session_id: str
    action: str
    payload: Optional[dict] = {}

class ActuatorApproveRequest(BaseModel):
    request_id: str
    approver: str

class ActuatorResponse(BaseModel):
    request_id: str
    status: str

class AuthContext(BaseModel):
    """Resolved authentication context for a request.

    For now this is single-tenant but includes account/api_key ids so we can
    grow into multi-tenant SaaS without changing the interface.
    """

    account_id: str | None = None
    api_key_id: str | None = None

