from typing import Literal, List, Optional, Dict, Any, Generator
from uuid import uuid4
from datetime import datetime, timezone
import json
import logging
import time

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

app = FastAPI(title="BrocaOS Web API")

# --- Activity / Metrics State ---
LAST_WORK_TS: float = 0.0
ACTIVE_REQUESTS: int = 0


def mark_work() -> None:
    """Mark that the system is actively processing work.

    Updates the last-activity timestamp used by /api/metrics to decide
    whether the system is in a WORKING vs IDLE state for the NeuralCore.
    """
    global LAST_WORK_TS
    LAST_WORK_TS = time.time()


def begin_request() -> None:
    """Mark the start of a request that may involve tools / cognition.

    Increments ACTIVE_REQUESTS and updates the last-work timestamp.
    """
    global ACTIVE_REQUESTS
    ACTIVE_REQUESTS += 1
    mark_work()


def end_request() -> None:
    """Mark the end of an active request.

    Decrements ACTIVE_REQUESTS (safely) and bumps last-work timestamp so
    the system remains in WORKING state briefly after completion.
    """
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

class ChatResponse(BaseModel):
    conversation_id: str
    reply: Message

class TitleUpdate(BaseModel):
    title: str

def get_runtime() -> BrocaRuntime:
    """
    Get or initialize the BrocaRuntime.
    
    The runtime is cached globally. When uvicorn reloads due to file changes,
    the module is reimported, clearing this global variable, which causes
    the runtime to be reinitialized with any updated config/code.
    """
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
        # Use a clean session for title generation
        temp_session = ConversationSession(llm=rt.session.llm)
        title = temp_session.send(prompt, stream=False)
        return title.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f"Failed to generate title: {e}")
        return user_message[:40] + "..."


@app.get("/api/metrics")
async def metrics():
    """System + activity metrics for NeuralCore.

    Returns CPU, memory pressure, uptime, and a boolean isWorking flag
    based on recent chat activity, matching the shape expected by the
    NeuralCore visualization in broca-www.
    """
    # Live CPU usage as fraction [0,1]
    cpu_percent = psutil.cpu_percent(interval=0.1) / 100.0

    # Memory pressure: used / total
    vm = psutil.virtual_memory()
    mem_pressure = vm.used / vm.total if vm.total else 0.0

    # Uptime: seconds since boot
    boot_time = psutil.boot_time()
    now_sec = time.time()
    uptime = int(now_sec - boot_time)

    # "Working" if there is an active request OR recent activity
    RECENT_WINDOW = 5.0  # seconds
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

def stream_response(conversation_id: str, user_message: str) -> Generator[str, None, None]:
    rt = get_runtime()
    storage = get_storage()
    session = create_session(conversation_id)

    # Mark that we're actively processing a streaming user chat request
    mark_work()
    
    # Pre-LLM instrumentation: Record attention, start latency timer, compute valence
    user_text = user_message
    if session.internal_sensing_framework and ResponseAnalyzer:
        try:
            # Extract topics from user input and context
            topics = ResponseAnalyzer.extract_topics(user_text, session.messages[-5:])
            for topic, level in topics.items():
                session.internal_sensing_framework.interoception.cognition.record_attention(
                    topic, level
                )
            
            # Start latency timer - store response_id for later use
            response_id = f"response_{len(session.messages) + 1}"
            session._current_response_id = response_id
            session.internal_sensing_framework.interoception.physiology._record_operation_start(
                response_id
            )
            
            # Compute valence from conversation history BEFORE updating system prompt
            session.internal_sensing_framework.interoception.affect.compute_valence_from_conversation_history(
                session.messages
            )
            # Force a fresh sample to ensure updated valence is included
            session.internal_sensing_framework._last_sample_time = 0.0
            session.internal_sensing_framework.sample_internal_state()
        except Exception as e:
            logger.debug(f"Error in pre-LLM instrumentation: {e}", exc_info=True)
    
    session.messages.append({"role": "user", "content": user_message})
    
    try:
        tools = rt.tool_registry.to_openai_format() if rt.tool_registry else None
        
        iterations = 0
        while iterations < 10:
            iterations += 1
            # Update system prompt before each LLM call (includes world state)
            session._update_system_prompt()
            messages_for_llm = session._get_messages_for_llm()
            
            # Use chat() to detect tool calls
            response = session.llm.chat(messages_for_llm, tools=tools)
            
            tool_calls = session.llm.extract_tool_calls(response)
            
            # Instrumentation: Track processing depth from tool calls
            if session.internal_sensing_framework and tool_calls:
                try:
                    processing_depth = len(tool_calls) + iterations - 1
                    session.internal_sensing_framework.interoception.cognition.record_processing_depth(
                        f"turn_{iterations}", processing_depth
                    )
                except Exception as e:
                    logger.debug(f"Error tracking processing depth: {e}", exc_info=True)
            
            if tool_calls:
                # Execute tools one by one and yield call/result pairs for visual auditing
                for tc in tool_calls:
                    # Create a specific assistant message for this tool call to ensure interleaved storage
                    interleaved_assistant_msg = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc]
                    }
                    session.messages.append(interleaved_assistant_msg)
                    
                    # Yield tool call
                    yield json.dumps({
                        "type": "tool_call",
                        "tool_call": tc,
                        "conversation_id": conversation_id
                    }) + "\n"
                    
                    # Execute tool (this should trigger internal sensing updates via tool registry)
                    result_dict = rt.tool_registry.execute_tool_call(tc)
                    
                    # Yield result
                    yield json.dumps({
                        "type": "tool_result",
                        "tool_call_id": tc["id"],
                        "tool_name": tc["function"]["name"],
                        "result": result_dict.get("content", ""),
                        "conversation_id": conversation_id
                    }) + "\n"
                    
                    # Add tool result to history
                    session.messages.append(result_dict)
                
                # Continue loop to see if LLM wants to do more
                continue
            else:
                # Final response
                content = session.llm.extract_assistant_content(response)
                
                # Yield in chunks to simulate streaming
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
        
        # Post-processing: Record internal sensing metrics (same as session.send())
        # Note: assistant_text should be defined above, but check to be safe
        if session.internal_sensing_framework and ResponseAnalyzer and 'assistant_text' in locals():
            try:
                response_id = getattr(session, "_current_response_id", f"response_{len(session.messages)}")
                
                # Record latency
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
                
                # Record confidence and uncertainty
                confidence = None
                uncertainty = None
                if assistant_text:
                    # Estimate confidence from response
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
                    
                    # Detect uncertainty
                    uncertainty = ResponseAnalyzer.detect_uncertainty(assistant_text)
                    if uncertainty is not None:
                        session.internal_sensing_framework.interoception.cognition.record_uncertainty(
                            response_id, uncertainty
                        )
                else:
                    # Tool-only response: use neutral values
                    session.internal_sensing_framework.interoception.cognition.record_confidence(
                        response_id, 0.5
                    )
                    confidence = 0.5
                    session.internal_sensing_framework.interoception.cognition.record_uncertainty(
                        response_id, 0.0
                    )
                    uncertainty = 0.0
                
                # Compute valence and arousal
                if assistant_text:
                    # Include current assistant response in history for valence computation
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
                    # Tool-only response: compute valence from existing history
                    conversation_messages = [m for m in session.messages if m.get("role") in ("user", "assistant")]
                    if conversation_messages:
                        session.internal_sensing_framework.interoception.affect.compute_valence_from_conversation_history(
                            conversation_messages
                        )
                    session.internal_sensing_framework.interoception.affect.compute_arousal(0.5)
                
                # Update affective states from cognitive
                session.internal_sensing_framework.interoception.affect.update_from_cognitive(
                    session.internal_sensing_framework.interoception.cognition
                )
                
                # Record reasoning step
                session.internal_sensing_framework.interoception.cognition.record_reasoning_step(
                    f"step_{response_id}",
                    {
                        "premise": user_text[:100] if session.messages else "",
                        "conclusion": assistant_text[:100] if assistant_text else "[tool-only response]",
                        "confidence": confidence,
                    },
                )
                
                # Sample internal state after ALL recording is complete (force fresh sample)
                fresh_state = session.internal_sensing_framework.sample_internal_state(force=True)
                # Save state after sampling
                try:
                    session.internal_sensing_framework.save_state()
                except Exception as e:
                    logger.warning(f"Failed to save state after sampling: {e}", exc_info=True)
                
                # Update system prompt AFTER recording to ensure world state reflects new values
                if session.world_state_aggregator and session._world_state_formatter:
                    session._last_world_state_hash = None  # Force update
                    session._update_system_prompt()
            except Exception as e:
                logger.error(f"Error in post-processing instrumentation: {e}", exc_info=True)
        
        # Persist
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
        # Still try to do post-processing even on error
        assistant_text = error_content
    
    # Ensure assistant_text is defined even if exception occurred early
    if 'assistant_text' not in locals():
        assistant_text = None
    
    # Post-processing: Record internal sensing metrics even if exception occurred
    if 'session' in locals() and session.internal_sensing_framework and ResponseAnalyzer:
        try:
            response_id = getattr(session, "_current_response_id", f"response_{len(session.messages)}")
            # Try to record at least neutral values
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
            pass  # Don't fail on post-processing errors
    
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
                stream_response(req.conversation_id, last.content),
                media_type="application/x-ndjson"
            )

        # Non-streaming
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

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="BrocaOS Web API Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="Enable auto-reload on file changes (default: enabled)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_false",
        dest="reload",
        help="Disable auto-reload"
    )
    
    args = parser.parse_args()
    
    # Determine workspace root (parent of broca package directory)
    workspace_root = Path(__file__).parent.parent.resolve()
    
    # Configure reload settings if enabled
    reload_dirs = None
    reload_includes = None
    reload_excludes = None
    
    if args.reload:
        # Watch workspace root (which includes broca directory and .env files)
        # This will watch all Python files in broca/ and .env files in workspace root
        reload_dirs = [
            str(workspace_root),  # Watch workspace root (includes broca/ and .env files)
        ]
        
        # Include .env files and Python files
        reload_includes = [
            "*.py",
            "*.env",
            "*.env.*",
        ]
        
        # Exclude unnecessary files and directories
        reload_excludes = [
            "*/__pycache__/*",
            "*.pyc",
            "*.pyo",
            "*/.git/*",
            "*/logs/*",
            "*/log/*",
            "*/BOOT_LOGS/*",
            "*/tests/*",
            "*/htmlcov/*",
            "*/mutants/*",
            "*/backup/*",
            "*/conversations/*",
            "*/docs/*",
            "*.db",
            "*.sqlite",
            "*.faiss",
            "*.jsonl",
        ]
    
    # When reload is enabled, uvicorn needs the app as an import string
    # When reload is disabled, we can pass the app object directly
    if args.reload:
        # Use import string for reload to work properly
        uvicorn.run(
            "broca.web_api:app",  # Import string format
            host=args.host,
            port=args.port,
            reload=True,
            reload_dirs=reload_dirs,
            reload_includes=reload_includes,
            reload_excludes=reload_excludes,
        )
    else:
        # Pass app object directly when reload is disabled
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=False,
        )
