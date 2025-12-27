from typing import Literal, List, Optional, Dict, Any, Generator
from uuid import uuid4
from datetime import datetime, timezone
import json
import logging
import os
import time
from pathlib import Path

import psutil
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
import uvicorn

from .main_repl_runtime import initialize_runtime, BrocaRuntime
from .repl.session import ConversationSession

# Import ResponseAnalyzer for internal sensing integration
try:
    from .internal_sensing.response_analyzer import ResponseAnalyzer
except ImportError:
    ResponseAnalyzer = None  # type: ignore

logger = logging.getLogger(__name__)

# Global runtime components (shared)
_runtime: Optional[BrocaRuntime] = None
PROJECT_ROOT: Path = Path(__file__).parent.parent.resolve()

app = FastAPI(title="BrocaOS Web API")

# --- Activity / Metrics State ---
LAST_WORK_TS: float = 0.0
ACTIVE_REQUESTS: int = 0


def mark_work() -> None:
    """Mark that the system is actively processing work."""
    global LAST_WORK_TS
    LAST_WORK_TS = time.time()


def begin_request() -> None:
    """Mark the start of a request that may involve tools / cognition."""
    global ACTIVE_REQUESTS
    ACTIVE_REQUESTS += 1
    mark_work()


def end_request() -> None:
    """Mark the end of an active request."""
    global ACTIVE_REQUESTS
    if ACTIVE_REQUESTS > 0:
        ACTIVE_REQUESTS -= 1
    mark_work()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewConversationRequest(BaseModel):
    system_prompt: Optional[str] = None

class NewConversationResponse(BaseModel):
    conversation_id: str

class Message(BaseModel):
    model_config = ConfigDict(extra='allow')
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class LoadConversationResponse(BaseModel):
    conversation_id: str
    messages: List[Message]

class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime

class ListConversationsResponse(BaseModel):
    conversations: List[ConversationSummary]

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    messages: List[Message]
    stream: bool = False
    web_search: bool = True

class ChatResponse(BaseModel):
    conversation_id: str
    reply: Message

class TitleUpdate(BaseModel):
    title: str

def get_runtime() -> BrocaRuntime:
    global _runtime
    if _runtime is None:
        _runtime = initialize_runtime()
    return _runtime

def get_storage():
    rt = get_runtime()
    if rt.conversation_storage is None:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    return rt.conversation_storage

def create_session(conversation_id: str) -> ConversationSession:
    rt = get_runtime()
    session = ConversationSession.from_storage(
        session_id=conversation_id,
        storage=rt.conversation_storage,
        tool_registry=rt.tool_registry,
        internal_sensing_framework=rt.internal_sensing,
        world_state_aggregator=rt.world_state_aggregator
    )
    return session

def generate_title(user_message: str) -> str:
    """Generate a short, punchy title using the LLM."""
    rt = get_runtime()
    prompt = f"Generate a very short (max 5 words), punchy title for a conversation that starts with: '{user_message}'. Return ONLY the title text, no quotes or punctuation."
    try:
        temp_session = ConversationSession(llm=rt.session.llm)
        title = temp_session.send(prompt, stream=False)
        return title.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f"Failed to generate title: {e}")
        return user_message[:40] + "..."


@app.get("/api/metrics")
async def metrics():
    cpu_percent = psutil.cpu_percent(interval=0.1) / 100.0
    vm = psutil.virtual_memory()
    mem_pressure = vm.used / vm.total if vm.total else 0.0
    boot_time = psutil.boot_time()
    now_sec = time.time()
    uptime = int(now_sec - boot_time)
    RECENT_WINDOW = 5.0
    is_working = ACTIVE_REQUESTS > 0 or (now_sec - LAST_WORK_TS) < RECENT_WINDOW

    return {
        "cpu": max(0.0, min(cpu_percent, 1.0)),
        "memory": max(0.0, min(mem_pressure, 1.0)),
        "uptime": uptime,
        "isWorking": is_working,
        "timestamp": int(now_sec * 1000),
    }


@app.post("/api/conversations", response_model=NewConversationResponse)
async def create_conversation(req: NewConversationRequest) -> NewConversationResponse:
    storage = get_storage()
    conversation_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    metadata = {
        "title": "New conversation",
        "created_at": now,
        "updated_at": now,
        "system_prompt": req.system_prompt
    }
    
    storage.save_conversation(conversation_id, [], metadata)
    return NewConversationResponse(conversation_id=conversation_id)

@app.get("/api/conversations", response_model=ListConversationsResponse)
async def list_conversations() -> ListConversationsResponse:
    storage = get_storage()
    convs = storage.list_conversations()
    
    items: List[ConversationSummary] = []
    for c in convs:
        cid = c.get("session_id") or c.get("conversation_id")
        if not cid: continue
        
        created_at = c.get("created_at")
        updated_at = c.get("updated_at")
        
        if isinstance(created_at, str):
            try: created_at = datetime.fromisoformat(created_at)
            except: created_at = datetime.now(timezone.utc)
        if isinstance(updated_at, str):
            try: updated_at = datetime.fromisoformat(updated_at)
            except: updated_at = datetime.now(timezone.utc)
            
        items.append(
            ConversationSummary(
                conversation_id=cid,
                title=c.get("title", "Untitled conversation"),
                created_at=created_at or datetime.now(timezone.utc),
                updated_at=updated_at or datetime.now(timezone.utc),
            )
        )
    
    items.sort(key=lambda x: x.updated_at, reverse=True)
    return ListConversationsResponse(conversations=items)

@app.get("/api/conversations/{conversation_id}", response_model=LoadConversationResponse)
async def load_conversation(conversation_id: str) -> LoadConversationResponse:
    storage = get_storage()
    data = storage.load_conversation(conversation_id)
    if not data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    raw_msgs = data.get("messages", [])
    msgs = []
    for m in raw_msgs:
        if "content" not in m:
            m["content"] = ""
        msgs.append(Message(**m))
        
    return LoadConversationResponse(conversation_id=conversation_id, messages=msgs)

@app.put("/api/conversations/{conversation_id}/title")
async def update_conversation_title(conversation_id: str, update: TitleUpdate):
    storage = get_storage()
    data = storage.load_conversation(conversation_id)
    if not data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    metadata = data.get("metadata", {})
    metadata["title"] = update.title[:100]
    metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    storage.save_conversation(conversation_id, data.get("messages", []), metadata)
    return {"success": True}

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    storage = get_storage()
    storage.delete_conversation(conversation_id)
    return {"success": True}

def stream_response(conversation_id: str, user_message: str, web_search_enabled: bool = True) -> Generator[str, None, None]:
    rt = get_runtime()
    storage = get_storage()
    session = create_session(conversation_id)

    mark_work()
    
    user_text = user_message
    if session.internal_sensing_framework and ResponseAnalyzer:
        try:
            topics = ResponseAnalyzer.extract_topics(user_text, session.messages[-5:])
            for topic, level in topics.items():
                session.internal_sensing_framework.interoception.cognition.record_attention(
                    topic, level
                )
            
            response_id = f"response_{len(session.messages) + 1}"
            session._current_response_id = response_id
            session.internal_sensing_framework.interoception.physiology._record_operation_start(
                response_id
            )
            
            session.internal_sensing_framework.interoception.affect.compute_valence_from_conversation_history(
                session.messages
            )
            session.internal_sensing_framework._last_sample_time = 0.0
            session.internal_sensing_framework.sample_internal_state()
        except Exception as e:
            logger.debug(f"Error in pre-LLM instrumentation: {e}", exc_info=True)
    
    session.messages.append({"role": "user", "content": user_message})
    
    try:
        tools = rt.tool_registry.to_openai_format() if rt.tool_registry else None
        
        if tools and not web_search_enabled:
            tools = [t for t in tools if t["function"]["name"] != "web_search"]
            logger.info("Web search tool disabled for this request")
        
        iterations = 0
        while iterations < 10:
            iterations += 1
            session._update_system_prompt()
            messages_for_llm = session._get_messages_for_llm()
            
            response = session.llm.chat(messages_for_llm, tools=tools)
            tool_calls = session.llm.extract_tool_calls(response)
            
            if session.internal_sensing_framework and tool_calls:
                try:
                    processing_depth = len(tool_calls) + iterations - 1
                    session.internal_sensing_framework.interoception.cognition.record_processing_depth(
                        f"turn_{iterations}", processing_depth
                    )
                except Exception as e:
                    logger.debug(f"Error tracking processing depth: {e}", exc_info=True)
            
            if tool_calls:
                for tc in tool_calls:
                    interleaved_assistant_msg = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc]
                    }
                    session.messages.append(interleaved_assistant_msg)
                    
                    yield json.dumps({
                        "type": "tool_call",
                        "tool_call": tc,
                        "conversation_id": conversation_id
                    }) + "\n"
                    
                    result_dict = rt.tool_registry.execute_tool_call(tc)
                    
                    yield json.dumps({
                        "type": "tool_result",
                        "tool_call_id": tc["id"],
                        "tool_name": tc["function"]["name"],
                        "result": result_dict.get("content", ""),
                        "conversation_id": conversation_id
                    }) + "\n"
                    
                    session.messages.append(result_dict)
                continue
            else:
                content = session.llm.extract_assistant_content(response)
                chunk_size = 32
                for i in range(0, len(content), chunk_size):
                    yield json.dumps({
                        "type": "text",
                        "content": content[i:i+chunk_size],
                        "conversation_id": conversation_id
                    }) + "\n"
                
                session.messages.append({"role": "assistant", "content": content})
                assistant_text = content
                break
        
        if session.internal_sensing_framework and ResponseAnalyzer and 'assistant_text' in locals():
            try:
                response_id = getattr(session, "_current_response_id", f"response_{len(session.messages)}")
                latency = session.internal_sensing_framework.interoception.physiology._record_operation_end(
                    response_id
                )
                if latency is not None and latency > 0:
                    normalized_latency = session.internal_sensing_framework.interoception.physiology._normalize_latency(
                        latency
                    )
                    if normalized_latency is not None:
                        session.internal_sensing_framework.interoception.physiology.metrics[
                            "processing_latency"
                        ] = normalized_latency
                
                confidence = None
                uncertainty = None
                if assistant_text:
                    confidence = ResponseAnalyzer.estimate_confidence(assistant_text)
                    if confidence is not None:
                        session.internal_sensing_framework.interoception.cognition.record_confidence(
                            response_id, confidence
                        )
                    else:
                        session.internal_sensing_framework.interoception.cognition.record_confidence(
                            response_id, 0.5
                        )
                        confidence = 0.5
                    
                    uncertainty = ResponseAnalyzer.detect_uncertainty(assistant_text)
                    if uncertainty is not None:
                        session.internal_sensing_framework.interoception.cognition.record_uncertainty(
                            response_id, uncertainty
                        )
                else:
                    session.internal_sensing_framework.interoception.cognition.record_confidence(
                        response_id, 0.5
                    )
                    confidence = 0.5
                    session.internal_sensing_framework.interoception.cognition.record_uncertainty(
                        response_id, 0.0
                    )
                    uncertainty = 0.0
                
                if assistant_text:
                    conversation_messages = session.messages + [
                        {"role": "assistant", "content": assistant_text}
                    ]
                    session.internal_sensing_framework.interoception.affect.compute_valence_from_conversation_history(
                        conversation_messages
                    )
                    
                    arousal = ResponseAnalyzer.compute_arousal(assistant_text)
                    if arousal is not None:
                        session.internal_sensing_framework.interoception.affect.compute_arousal(arousal)
                else:
                    conversation_messages = [m for m in session.messages if m.get("role") in ("user", "assistant")]
                    if conversation_messages:
                        session.internal_sensing_framework.interoception.affect.compute_valence_from_conversation_history(
                            conversation_messages
                        )
                    session.internal_sensing_framework.interoception.affect.compute_arousal(0.5)
                
                session.internal_sensing_framework.interoception.affect.update_from_cognitive(
                    session.internal_sensing_framework.interoception.cognition
                )
                
                session.internal_sensing_framework.interoception.cognition.record_reasoning_step(
                    f"step_{response_id}",
                    {
                        "premise": user_text[:100] if session.messages else "",
                        "conclusion": assistant_text[:100] if assistant_text else "[tool-only response]",
                        "confidence": confidence,
                    },
                )
                
                fresh_state = session.internal_sensing_framework.sample_internal_state(force=True)
                try:
                    session.internal_sensing_framework.save_state()
                except Exception as e:
                    logger.warning(f"Failed to save state after sampling: {e}", exc_info=True)
                
                if session.world_state_aggregator and session._world_state_formatter:
                    session._last_world_state_hash = None
                    session._update_system_prompt()
            except Exception as e:
                logger.error(f"Error in post-processing instrumentation: {e}", exc_info=True)
        
        data = storage.load_conversation(conversation_id)
        metadata = data.get("metadata", {}) if data else {}
        if metadata.get("title") == "New conversation":
            metadata["title"] = generate_title(user_message)
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        storage.save_conversation(conversation_id, session.messages, metadata)
        
    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        error_content = f"\n[Error: {str(e)}]"
        yield json.dumps({
            "type": "text",
            "content": error_content,
            "conversation_id": conversation_id
        }) + "\n"
        assistant_text = error_content
    
    if 'assistant_text' not in locals():
        assistant_text = None
    
    if 'session' in locals() and session.internal_sensing_framework and ResponseAnalyzer:
        try:
            response_id = getattr(session, "_current_response_id", f"response_{len(session.messages)}")
            if assistant_text:
                session.internal_sensing_framework.interoception.cognition.record_confidence(response_id, 0.5)
                session.internal_sensing_framework.interoception.affect.compute_arousal(0.5)
            session.internal_sensing_framework.sample_internal_state(force=True)
            try:
                session.internal_sensing_framework.save_state()
            except Exception:
                pass
            if session.world_state_aggregator and session._world_state_formatter:
                session._last_world_state_hash = None
                session._update_system_prompt()
        except Exception:
            pass
    
    yield json.dumps({
        "type": "done",
        "conversation_id": conversation_id
    }) + "\n"

@app.post("/api/chat")
async def chat(req: ChatRequest):
    begin_request()
    try:
        if not req.messages:
            raise HTTPException(status_code=400, detail="No messages provided")

        last = req.messages[-1]
        if last.role != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")

        if req.conversation_id is None:
            res = await create_conversation(NewConversationRequest())
            req.conversation_id = res.conversation_id

        if req.stream:
            return StreamingResponse(
                stream_response(req.conversation_id, last.content, web_search_enabled=req.web_search),
                media_type="application/x-ndjson"
            )

        session = create_session(req.conversation_id)
        reply_text = session.send(last.content, stream=False)
        
        storage = get_storage()
        data = storage.load_conversation(req.conversation_id)
        metadata = data.get("metadata", {}) if data else {}
        if metadata.get("title") == "New conversation":
            metadata["title"] = generate_title(last.content)
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        storage.save_conversation(req.conversation_id, session.messages, metadata)
        
        return ChatResponse(
            conversation_id=req.conversation_id,
            reply=Message(role="assistant", content=reply_text)
        )
    finally:
        end_request()


@app.get("/api/memories")
async def get_memories(query: Optional[str] = None):
    rt = get_runtime()
    if not rt.memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    if query:
        results = rt.memory_manager.retrieve_memories(query, limit=50)
    else:
        results = rt.memory_manager.storage.get_recent_memories(limit=50)
    
    return {
        "memories": [
            {
                "id": m.id,
                "text": m.text,
                "namespace": m.namespace,
                "importance": m.importance,
                "tags": m.tags,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "source": m.source.model_dump() if m.source else None
            } for m in results
        ]
    }

@app.get("/api/memories/graph")
async def get_memory_graph(memory_ids: str, depth: int = 2):
    """Get a subgraph of memory relationships."""
    rt = get_runtime()
    if not rt.memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    try:
        ids = [int(id_str) for id_str in memory_ids.split(",")]
        graph = rt.memory_manager.relationships.get_relationship_graph(ids, depth=depth)
        return graph
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/memories/{memory_id}/related")
async def get_related_memories(memory_id: int, limit: int = 10):
    rt = get_runtime()
    if not rt.memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    related = rt.memory_manager.relationships.get_related(memory_id, limit=limit)
    return {
        "related": [
            {
                "memory": {
                    "id": m.id,
                    "text": m.text,
                    "namespace": m.namespace,
                    "importance": m.importance,
                    "tags": m.tags,
                    "source": m.source.model_dump() if m.source else None
                },
                "relationship": {
                    "type": rel.relation_type.value,
                    "strength": rel.strength,
                    "bidirectional": rel.bidirectional
                }
            } for m, rel in related
        ]
    }

@app.get("/api/artifacts")
async def get_artifacts():
    workspace_root = PROJECT_ROOT
    artifacts_dir = workspace_root / "artifacts"
    
    if not artifacts_dir.exists():
        return {"artifacts": []}
    
    artifacts = []
    for item in artifacts_dir.rglob("*"):
        if item.name == ".gitkeep": continue
        
        rel_path = item.relative_to(workspace_root)
        artifacts.append({
            "name": item.name,
            "path": str(rel_path),
            "type": "directory" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None,
            "last_modified": datetime.fromtimestamp(item.stat().st_mtime, timezone.utc).isoformat()
        })
    
    return {"artifacts": artifacts}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BrocaOS Web API Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", default=True)
    
    args = parser.parse_args()
    uvicorn.run("broca.web_api:app", host=args.host, port=args.port, reload=args.reload)

class ProjectConfig(BaseModel):
    root_path: str

@app.get("/api/project/config")
async def get_project_config():
    global PROJECT_ROOT
    return {"root_path": str(PROJECT_ROOT)}

@app.post("/api/project/config")
async def update_project_config(config: ProjectConfig):
    global PROJECT_ROOT
    new_path = Path(config.root_path).resolve()
    if not new_path.exists():
        raise HTTPException(status_code=400, detail="Path does not exist")
    PROJECT_ROOT = new_path
    return {"success": True, "root_path": str(PROJECT_ROOT)}
