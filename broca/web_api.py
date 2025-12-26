from typing import Literal, List, Optional, Dict, Any, Generator
from uuid import uuid4
from datetime import datetime, timezone
import json
import logging

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
import uvicorn

from .main_repl_runtime import initialize_runtime, BrocaRuntime
from .repl.session import ConversationSession

logger = logging.getLogger(__name__)

# Global runtime components (shared)
_runtime: Optional[BrocaRuntime] = None

app = FastAPI(title="BrocaOS Web API")

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
    
    session.messages.append({"role": "user", "content": user_message})
    
    try:
        tools = rt.tool_registry.to_openai_format() if rt.tool_registry else None
        
        iterations = 0
        while iterations < 10:
            iterations += 1
            session._update_system_prompt()
            messages_for_llm = session._get_messages_for_llm()
            
            # Use chat() to detect tool calls
            response = session.llm.chat(messages_for_llm, tools=tools)
            
            tool_calls = session.llm.extract_tool_calls(response)
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
                    
                    # Execute tool
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
                break
        
        # Persist
        data = storage.load_conversation(conversation_id)
        metadata = data.get("metadata", {}) if data else {}
        if metadata.get("title") == "New conversation":
            metadata["title"] = generate_title(user_message)
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        storage.save_conversation(conversation_id, session.messages, metadata)
        
    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        yield json.dumps({
            "type": "text",
            "content": f"\n[Error: {str(e)}]",
            "conversation_id": conversation_id
        }) + "\n"
    
    yield json.dumps({
        "type": "done",
        "conversation_id": conversation_id
    }) + "\n"

@app.post("/api/chat")
async def chat(req: ChatRequest):
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
