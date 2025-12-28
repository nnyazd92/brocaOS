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
    include_rl_signals: bool = False  # Include RL signal metrics in response

class ChatResponse(BaseModel):
    conversation_id: str
    reply: Message
    rl_signals: Optional[Dict[str, Any]] = None  # RL signal metrics if requested

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
    
    # Extract PEA loop managers from reasoning_tool if available
    goal_manager = None
    skill_manager = None
    experience_logger = None
    
    if rt.reasoning_tool:
        if hasattr(rt.reasoning_tool, 'goal_manager'):
            goal_manager = rt.reasoning_tool.goal_manager
        if hasattr(rt.reasoning_tool, 'learning_tool') and rt.reasoning_tool.learning_tool:
            if hasattr(rt.reasoning_tool.learning_tool, 'skill_manager'):
                skill_manager = rt.reasoning_tool.learning_tool.skill_manager
            if hasattr(rt.reasoning_tool.learning_tool, 'experience_logger'):
                experience_logger = rt.reasoning_tool.learning_tool.experience_logger
    
    session = ConversationSession.from_storage(
        session_id=conversation_id,
        storage=rt.conversation_storage,
        tool_registry=rt.tool_registry,
        internal_sensing_framework=rt.internal_sensing,
        world_state_aggregator=rt.world_state_aggregator,
        goal_manager=goal_manager,
        skill_manager=skill_manager,
        experience_logger=experience_logger,
    )
    return session

def generate_title(user_message: str) -> str:
    """Generate a short, punchy title using the LLM."""
    rt = get_runtime()
    prompt = f"Generate a very short (max 5 words), punchy title for a conversation that starts with: '{user_message}'. Return ONLY the title text, no quotes or punctuation."
    try:
        temp_session = ConversationSession(
            llm=rt.session.llm,
            internal_sensing_framework=rt.internal_sensing,
        )
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


@app.get("/api/cognitive-architecture/health")
async def get_system_health():
    """Get system health status from health monitor."""
    rt = get_runtime()
    if not rt.system_health_monitor:
        raise HTTPException(status_code=503, detail="System health monitoring not enabled")
    
    try:
        health_report = rt.system_health_monitor.assess_health()
        return {
            "overall_health": health_report.overall_health,
            "status": health_report.status.value,
            "stability_score": health_report.stability_score,
            "issues": [{"severity": issue.severity.value, "message": issue.message} for issue in health_report.issues],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cognitive-architecture/statistics")
async def get_cognitive_architecture_stats():
    """Get statistics from all cognitive architecture components."""
    rt = get_runtime()
    stats = {}
    
    # Hierarchical control stats
    if rt.hierarchical_controller:
        try:
            control_stats = rt.hierarchical_controller.get_control_statistics()
            if control_stats.get("status") != "no_data":
                stats["hierarchical_control"] = control_stats
        except Exception as e:
            logger.debug(f"Error getting hierarchical control stats: {e}")
    
    # Recursive reasoning stats
    if rt.recursive_reasoning_engine:
        try:
            reasoning_stats = rt.recursive_reasoning_engine.get_statistics()
            if reasoning_stats.get("status") != "no_data":
                stats["recursive_reasoning"] = reasoning_stats
        except Exception as e:
            logger.debug(f"Error getting recursive reasoning stats: {e}")
    
    # Metacognitive loops stats
    if rt.metacognitive_loop:
        try:
            meta_stats = rt.metacognitive_loop.get_statistics()
            if meta_stats.get("status") != "no_data":
                stats["metacognitive"] = meta_stats
        except Exception as e:
            logger.debug(f"Error getting metacognitive stats: {e}")
    
    # Nested feedback stats
    if rt.nested_feedback_system:
        try:
            feedback_stats = rt.nested_feedback_system.get_statistics()
            stats["nested_feedback"] = feedback_stats
        except Exception as e:
            logger.debug(f"Error getting nested feedback stats: {e}")
    
    # System dynamics stats
    if rt.system_dynamics:
        try:
            dynamics_stats = rt.system_dynamics.get_statistics()
            if dynamics_stats.get("status") != "no_data":
                stats["system_dynamics"] = dynamics_stats
        except Exception as e:
            logger.debug(f"Error getting system dynamics stats: {e}")
    
    # System health stats
    if rt.system_health_monitor:
        try:
            health_report = rt.system_health_monitor.assess_health()
            stats["system_health"] = {
                "overall_health": health_report.overall_health,
                "status": health_report.status.value,
                "stability_score": health_report.stability_score,
                "issues_count": len(health_report.issues)
            }
        except Exception as e:
            logger.debug(f"Error getting system health stats: {e}")
    
    # MPC controller stats
    if rt.mpc_controller:
        try:
            mpc_stats = rt.mpc_controller.get_statistics()
            if mpc_stats.get("status") != "no_data":
                stats["mpc_control"] = mpc_stats
        except Exception as e:
            logger.debug(f"Error getting MPC controller stats: {e}")
    
    # Distributed control stats
    if rt.distributed_control:
        try:
            dist_stats = rt.distributed_control.get_statistics()
            stats["distributed_control"] = dist_stats
        except Exception as e:
            logger.debug(f"Error getting distributed control stats: {e}")
    
    # Recursive improvement stats
    if rt.recursive_improvement:
        try:
            improvement_stats = rt.recursive_improvement.get_statistics()
            stats["recursive_improvement"] = improvement_stats
        except Exception as e:
            logger.debug(f"Error getting recursive improvement stats: {e}")
    
    return {
        "components": stats,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }



class CognitiveQueryRequest(BaseModel):
    query: str
    include_z3_validation: bool = True
    include_affective_state: bool = True
    include_thought_process: bool = True
    include_memory_traversal: bool = False
    include_rl_signals: bool = False  # Include RL signal metrics in response

class CognitiveQueryResponse(BaseModel):
    response: str
    thought_process: List[Dict[str, Any]] = []
    z3_validation: Optional[Dict[str, Any]] = None
    affective_state: Optional[Dict[str, Any]] = None
    memory_traversal: Optional[Dict[str, Any]] = None
    rl_signals: Optional[Dict[str, Any]] = None  # RL signal metrics if requested
    processing_time_ms: int

@app.post("/api/cognitive/query", response_model=CognitiveQueryResponse)
async def cognitive_query(req: CognitiveQueryRequest):
    """Process a cognitive query with full introspection."""
    # Import config locally at the very start to avoid scoping issues
    from .config import config as app_config
    
    begin_request()
    start_time = time.time()
    try:
        rt = get_runtime()
        
        # Extract PEA loop managers from reasoning_tool if available
        goal_manager = None
        skill_manager = None
        experience_logger = None
        
        if rt.reasoning_tool:
            if hasattr(rt.reasoning_tool, 'goal_manager'):
                goal_manager = rt.reasoning_tool.goal_manager
            if hasattr(rt.reasoning_tool, 'learning_tool') and rt.reasoning_tool.learning_tool:
                if hasattr(rt.reasoning_tool.learning_tool, 'skill_manager'):
                    skill_manager = rt.reasoning_tool.learning_tool.skill_manager
                if hasattr(rt.reasoning_tool.learning_tool, 'experience_logger'):
                    experience_logger = rt.reasoning_tool.learning_tool.experience_logger
        
        # Create a temporary session for this query
        temp_session = ConversationSession(
            llm=rt.session.llm,
            tool_registry=rt.tool_registry,
            internal_sensing_framework=rt.internal_sensing,
            world_state_aggregator=rt.world_state_aggregator,
            goal_manager=goal_manager,
            skill_manager=skill_manager,
            experience_logger=experience_logger,
        )
        
        # Get the response
        response_text = temp_session.send(req.query, stream=False)
        
        # Build response with introspection data
        result = {
            "response": response_text,
            "thought_process": [],
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
        # Add Z3 validation if requested and available
        if req.include_z3_validation and hasattr(rt, 'z3_validator') and rt.z3_validator:
            try:
                # This would be implemented in the Z3 validator
                pass
            except Exception as e:
                logger.warning(f"Z3 validation failed: {e}")
        
        # Add affective state if requested
        if req.include_affective_state and rt.internal_sensing:
            try:
                affective_state = rt.internal_sensing.get_current_affective_state()
                if affective_state:
                    result["affective_state"] = affective_state
            except Exception as e:
                logger.warning(f"Affective state retrieval failed: {e}")
        
        # Add RL signals if requested
        if req.include_rl_signals and rt.world_state_aggregator and hasattr(rt.world_state_aggregator, 'reasoning_tool'):
            reasoning_tool = rt.world_state_aggregator.reasoning_tool
            if reasoning_tool and hasattr(reasoning_tool, 'feedback_loop_manager'):
                feedback_loop_manager = reasoning_tool.feedback_loop_manager
                if feedback_loop_manager and feedback_loop_manager.rl_signals_enabled and feedback_loop_manager.rl_signal_aggregator:
                    try:
                        # Get affective state for RL signals
                        affective_state = None
                        if rt.internal_sensing:
                            try:
                                affective_state = rt.internal_sensing.get_current_affective_state()
                            except Exception:
                                pass
                        
                        # Get prediction error if available
                        prediction_error = None
                        if rt.internal_sensing and hasattr(rt.internal_sensing.interoception, 'predictive'):
                            try:
                                prediction_error = rt.internal_sensing.interoception.predictive.get_rl_prediction_error_signal()
                            except Exception:
                                pass
                        
                        # Compute RL signals
                        rl_metrics = feedback_loop_manager.rl_signal_aggregator.compute_signals(
                            affective_state=affective_state,
                            prediction_error=prediction_error,
                        )
                        
                        # Prepare RL signals data for response
                        result["rl_signals"] = {
                            "dissonance_reward": round(rl_metrics.dissonance_reward, 3),
                            "surprise_reward": round(rl_metrics.surprise_reward, 3),
                            "curiosity_reward": round(rl_metrics.curiosity_reward, 3),
                            "information_gain_reward": round(rl_metrics.information_gain_reward, 3),
                            "coherence_reward": round(rl_metrics.coherence_reward, 3),
                            "composite_reward": round(rl_metrics.composite_reward, 3),
                            "exploration_balance": round(rl_metrics.get_exploration_exploitation_balance(), 3),
                            "weights": {
                                "dissonance": rl_metrics.weight_dissonance,
                                "surprise": rl_metrics.weight_surprise,
                                "curiosity": rl_metrics.weight_curiosity,
                                "info_gain": rl_metrics.weight_info_gain,
                                "coherence": rl_metrics.weight_coherence,
                            }
                        }
                        
                        # Apply RL feedback
                        try:
                            from .reasoning.feedback_loop import FeedbackMetrics
                            feedback_metrics = FeedbackMetrics(window_size=1)
                            feedback_loop_manager._apply_rl_feedback(
                                feedback_metrics,
                                emotional_state=affective_state
                            )
                        except Exception as e:
                            logger.debug(f"Error applying RL feedback in cognitive query: {e}", exc_info=True)
                            
                    except Exception as e:
                        logger.warning(f"Error computing RL signals in cognitive query: {e}", exc_info=True)
        
        # Add memory traversal if requested
        if req.include_memory_traversal and rt.memory_manager:
            try:
                # Get memories related to the query
                memories = rt.memory_manager.retrieve_memories(req.query, limit=10)
                if memories:
                    result["memory_traversal"] = {
                        "retrieved_memories": [
                            {
                                "id": m.id,
                                "text": m.text[:200] + "..." if len(m.text) > 200 else m.text,
                                "relevance": m.relevance_score if hasattr(m, 'relevance_score') else 0.5,
                                "namespace": m.namespace
                            }
                            for m in memories
                        ],
                        "relationships_found": len(memories)
                    }
            except Exception as e:
                logger.warning(f"Memory traversal failed: {e}")
        
        return CognitiveQueryResponse(**result)
        
    finally:
        end_request()
@app.post("/api/cognitive-architecture/reconfigure")
async def trigger_reconfiguration():
    """Trigger system reconfiguration (if authorized)."""
    rt = get_runtime()
    if not rt.reconfiguration_manager:
        raise HTTPException(status_code=503, detail="Reconfiguration not enabled")
    
    try:
        result = rt.reconfiguration_manager.reconfigure()
        return {
            "success": result.success,
            "changes": result.changes if result.success else [],
            "message": result.message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering reconfiguration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
        # Filter out SYSTEM DIRECTIVE messages - these are internal system warnings
        # and should not be exposed via the API
        if m.get("role") == "user":
            content = m.get("content", "")
            if content and "[SYSTEM DIRECTIVE" in content:
                continue  # Skip this message
        
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

def stream_response(conversation_id: str, user_message: str, web_search_enabled: bool = True, include_rl_signals: bool = False) -> Generator[str, None, None]:
    # Import config locally at the very start to avoid scoping issues
    # This ensures config is available before any methods that might import it locally
    from .config import config as app_config
    
    rt = get_runtime()
    storage = get_storage()
    session = create_session(conversation_id)
    
    # Ensure PEA loop managers are wired (in case they weren't available during create_session)
    if session.pea_loop and rt.reasoning_tool:
        goal_manager = None
        skill_manager = None
        experience_logger = None
        
        if hasattr(rt.reasoning_tool, 'goal_manager'):
            goal_manager = rt.reasoning_tool.goal_manager
        if hasattr(rt.reasoning_tool, 'learning_tool') and rt.reasoning_tool.learning_tool:
            if hasattr(rt.reasoning_tool.learning_tool, 'skill_manager'):
                skill_manager = rt.reasoning_tool.learning_tool.skill_manager
            if hasattr(rt.reasoning_tool.learning_tool, 'experience_logger'):
                experience_logger = rt.reasoning_tool.learning_tool.experience_logger
        
        if goal_manager or skill_manager or experience_logger:
            session.wire_pea_loop_managers(
                goal_manager=goal_manager,
                skill_manager=skill_manager,
                experience_logger=experience_logger,
            )

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
        # Gather context for tool filtering/ranking if guidance is enabled
        context = None
        if (rt.tool_registry and 
            hasattr(rt.tool_registry, 'tool_selection_guidance') and
            rt.tool_registry.tool_selection_guidance is not None):
            try:
                if app_config and app_config.tools.pre_filtering_enabled:
                    context = rt.tool_registry.tool_selection_guidance.guidance_aggregator.gather_context()
            except Exception as e:
                logger.debug(f"Error gathering context for tool filtering in web_api: {e}", exc_info=True)
        
        tools = rt.tool_registry.to_openai_format(context=context) if rt.tool_registry else None
        
        if tools and not web_search_enabled:
            tools = [t for t in tools if t["function"]["name"] != "web_search"]
            logger.info("Web search tool disabled for this request")
        
        iterations = 0
        last_warning_iteration = 0
        max_iterations = 100  # Match session.send() max iterations
        assistant_text = None
        last_response = None
        
        while iterations < max_iterations:
            iterations += 1
            session._update_system_prompt()
            messages_for_llm = session._get_messages_for_llm()
            
            # Check for loop conditions and inject warnings if needed (same as session.send())
            warning_thresholds = [10, 20, 30, 50, 75, 90]
            should_warn = False
            warning_message = None
            
            for threshold in warning_thresholds:
                if iterations >= threshold and last_warning_iteration < threshold:
                    should_warn = True
                    last_warning_iteration = threshold
                    
                    # Detect loops using session's method
                    loop_info = session._detect_tool_call_loop(iterations) if hasattr(session, '_detect_tool_call_loop') else None
                    
                    # Generate warning message based on severity
                    if iterations >= 75:
                        severity = "CRITICAL"
                        urgency = "MUST"
                    elif iterations >= 50:
                        severity = "CRITICAL"
                        urgency = "MUST"
                    elif iterations >= 30:
                        severity = "HIGH"
                        urgency = "should"
                    else:
                        severity = "MEDIUM"
                        urgency = "should"
                    
                    if loop_info:
                        tool_name = loop_info["tool_name"]
                        repeat_count = loop_info["repeat_count"]
                        pattern = loop_info["pattern_description"]
                        warning_message = (
                            f"[SYSTEM DIRECTIVE - {severity} WARNING] You are on iteration {iterations}. "
                            f"A loop has been detected: {pattern}. You {urgency} break out of this loop. "
                            "Review the tool results you've received and either:\n"
                            "- Make different tool calls if you need different information\n"
                            "- Provide your final comprehensive response to the user if you have enough information\n"
                            "Do not continue making the same tool calls repeatedly. The system automatically continues "
                            "after tool results - you should review results and respond accordingly."
                        )
                    else:
                        if iterations >= 50:
                            warning_message = (
                                f"[SYSTEM DIRECTIVE - {severity} WARNING] Very high iteration count ({iterations}). "
                                f"You {urgency} provide a final response to the user. Review all tool results you've received "
                                "and provide a comprehensive answer. The system automatically continues after tool results - "
                                "you should respond with your final answer, not wait for user input."
                            )
                        elif iterations >= 30:
                            warning_message = (
                                f"[SYSTEM DIRECTIVE - {severity} WARNING] High iteration count ({iterations}). "
                                "You may be stuck in a loop. Review tool results and either make different tool calls "
                                "if needed, or provide your final response. The system automatically continues - "
                                "you should respond based on tool results, not wait for user prompts."
                            )
                        else:
                            warning_message = (
                                f"[SYSTEM DIRECTIVE - {severity} WARNING] You're on iteration {iterations}. "
                                "Consider if your current approach is working. If you're making progress with tool calls, continue. "
                                "If you have enough information from tool results, provide your final response. "
                                "Remember: the system automatically continues after tool results - review them and respond accordingly."
                            )
                    break
            
            if should_warn and warning_message:
                session.messages.append({"role": "user", "content": warning_message})
                logger.warning(
                    f"Injected loop warning at iteration {iterations}",
                    extra={
                        "event": "loop_warning_injected",
                        "iteration": iterations,
                        "warning_threshold": last_warning_iteration,
                    }
                )
            
            response = session.llm.chat(messages_for_llm, tools=tools)
            last_response = response  # Store for max_iterations handling
            tool_calls = session.llm.extract_tool_calls(response)
            
            # Extract assistant content (intermediary commentary) before processing tool calls
            assistant_content = session.llm.extract_assistant_content(response) or None
            
            if session.internal_sensing_framework and tool_calls:
                try:
                    processing_depth = len(tool_calls) + iterations - 1
                    session.internal_sensing_framework.interoception.cognition.record_processing_depth(
                        f"turn_{iterations}", processing_depth
                    )
                except Exception as e:
                    logger.debug(f"Error tracking processing depth: {e}", exc_info=True)
            
            if tool_calls:
                # Log tool calls detected for automatic continuation
                tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls]
                logger.info(
                    f"Tool calls detected in stream_response (iteration {iterations})",
                    extra={
                        "event": "tool_calls_detected",
                        "tool_calls_count": len(tool_calls),
                        "tool_names": tool_names,
                        "iteration": iterations,
                    },
                )
                
                # Create single assistant message with all tool calls and content (preserves intermediary commentary)
                # This matches session.send() behavior
                assistant_message = {
                    "role": "assistant",
                    "content": assistant_content,  # Preserve intermediary commentary
                    "tool_calls": tool_calls,
                }
                session.messages.append(assistant_message)
                
                # Process each tool call and yield streaming events
                for tc in tool_calls:
                    yield json.dumps({
                        "type": "tool_call",
                        "tool_call": tc,
                        "conversation_id": conversation_id
                    }) + "\n"
                    
                    result_dict = rt.tool_registry.execute_tool_call(tc)
                    
                    # Verify tool result was properly added (logging for debugging)
                    logger.debug(
                        f"Tool result added in stream_response: {tc.get('function', {}).get('name', 'unknown')} (call_id: {tc.get('id', '')})",
                        extra={
                            "event": "tool_result_added",
                            "tool_name": tc.get("function", {}).get("name", "unknown"),
                            "tool_call_id": tc.get("id", ""),
                            "messages_count": len(session.messages),
                        }
                    )
                    
                    yield json.dumps({
                        "type": "tool_result",
                        "tool_call_id": tc["id"],
                        "tool_name": tc["function"]["name"],
                        "result": result_dict.get("content", ""),
                        "conversation_id": conversation_id
                    }) + "\n"
                    
                    session.messages.append(result_dict)
                
                # Verify automatic continuation - log that we're continuing after tool calls
                tool_results_count = sum(1 for msg in session.messages if msg.get("role") == "tool")
                logger.debug(
                    f"Continuing after tool calls in stream_response: {len(tool_calls)} tool calls made, {tool_results_count} total tool results in messages",
                    extra={
                        "event": "auto_continuation_after_tools",
                        "iteration": iterations,
                        "tool_calls_count": len(tool_calls),
                        "tool_results_count": tool_results_count,
                        "messages_count": len(session.messages),
                    }
                )
                
                # Continue loop automatically after tool results (matches session.send() behavior)
                continue
            else:
                # No tool calls - final response
                content = session.llm.extract_assistant_content(response)
                if not content:
                    content = "I apologize, but I encountered an issue processing your request."
                
                chunk_size = 32
                for i in range(0, len(content), chunk_size):
                    yield json.dumps({
                        "type": "text",
                        "content": content[i:i+chunk_size],
                        "conversation_id": conversation_id
                    }) + "\n"
                
                session.messages.append({"role": "assistant", "content": content})
                assistant_text = content
                
                # Measure cognitive dissonance and compute RL signals if available
                rl_signals_data = None
                if rt.world_state_aggregator and hasattr(rt.world_state_aggregator, 'reasoning_tool'):
                    reasoning_tool = rt.world_state_aggregator.reasoning_tool
                    if reasoning_tool:
                        # Measure cognitive dissonance (NON-BLOCKING - runs in background)
                        if hasattr(reasoning_tool, 'cognitive_dissonance_monitor'):
                            cognitive_dissonance_monitor = reasoning_tool.cognitive_dissonance_monitor
                            if cognitive_dissonance_monitor:
                                # Run in background thread to avoid blocking conversation
                                import threading
                                
                                def measure_dissonance_async():
                                    try:
                                        # Extract tool usage from messages
                                        tool_usage = []
                                        for msg in session.messages[-20:]:  # Check last 20 messages
                                            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                                                tool_usage.extend(msg.get("tool_calls", []))
                                        
                                        # Measure dissonance
                                        conversation_context = [
                                            {"role": m.get("role"), "content": (m.get("content") or "")[:200]}
                                            for m in session.messages[-5:]
                                        ]
                                        
                                        cognitive_dissonance_monitor.measure_dissonance(
                                            response=content,
                                            conversation_context=conversation_context,
                                            tool_usage=tool_usage if tool_usage else None
                                        )
                                    except Exception as e:
                                        logger.warning(f"Error measuring cognitive dissonance in web_api (background): {e}", exc_info=True)
                                
                                # Start background thread (fire-and-forget)
                                thread = threading.Thread(target=measure_dissonance_async, daemon=True)
                                thread.start()
                        
                        # Compute RL signals if feedback loop manager is available
                        if hasattr(reasoning_tool, 'feedback_loop_manager') and reasoning_tool.feedback_loop_manager:
                            feedback_loop_manager = reasoning_tool.feedback_loop_manager
                            if feedback_loop_manager.rl_signals_enabled and feedback_loop_manager.rl_signal_aggregator:
                                try:
                                    from .reasoning.rl_signals import RLSignalAggregator
                                    
                                    # Get affective state for RL signals
                                    affective_state = None
                                    if session.internal_sensing_framework:
                                        try:
                                            affective_state = session.internal_sensing_framework.get_current_affective_state()
                                        except Exception:
                                            pass
                                    
                                    # Get prediction error if available
                                    prediction_error = None
                                    if session.internal_sensing_framework and hasattr(session.internal_sensing_framework.interoception, 'predictive'):
                                        try:
                                            prediction_error = session.internal_sensing_framework.interoception.predictive.get_rl_prediction_error_signal()
                                        except Exception:
                                            pass
                                    
                                    # Compute RL signals
                                    rl_metrics = feedback_loop_manager.rl_signal_aggregator.compute_signals(
                                        affective_state=affective_state,
                                        prediction_error=prediction_error,
                                    )
                                    
                                    # Prepare RL signals data for response
                                    rl_signals_data = {
                                        "dissonance_reward": round(rl_metrics.dissonance_reward, 3),
                                        "surprise_reward": round(rl_metrics.surprise_reward, 3),
                                        "curiosity_reward": round(rl_metrics.curiosity_reward, 3),
                                        "information_gain_reward": round(rl_metrics.information_gain_reward, 3),
                                        "coherence_reward": round(rl_metrics.coherence_reward, 3),
                                        "composite_reward": round(rl_metrics.composite_reward, 3),
                                        "exploration_balance": round(rl_metrics.get_exploration_exploitation_balance(), 3),
                                        "weights": {
                                            "dissonance": rl_metrics.weight_dissonance,
                                            "surprise": rl_metrics.weight_surprise,
                                            "curiosity": rl_metrics.weight_curiosity,
                                            "info_gain": rl_metrics.weight_info_gain,
                                            "coherence": rl_metrics.weight_coherence,
                                        }
                                    }
                                    
                                    # Apply RL feedback if feedback loop manager is available
                                    if hasattr(feedback_loop_manager, '_apply_rl_feedback'):
                                        try:
                                            from .reasoning.feedback_loop import FeedbackMetrics
                                            # Create minimal feedback metrics for RL feedback
                                            feedback_metrics = FeedbackMetrics(window_size=1)
                                            feedback_loop_manager._apply_rl_feedback(
                                                feedback_metrics,
                                                emotional_state=affective_state
                                            )
                                        except Exception as e:
                                            logger.debug(f"Error applying RL feedback in web_api: {e}", exc_info=True)
                                    
                                except Exception as e:
                                    logger.warning(f"Error computing RL signals in web_api: {e}", exc_info=True)
                
                break
        
        # Handle max iterations reached (same as session.send())
        if iterations >= max_iterations and not assistant_text:
            logger.warning(
                f"Reached max tool iterations ({max_iterations}) in stream_response",
                extra={
                    "event": "max_tool_iterations_reached",
                    "max_iterations": max_iterations,
                    "iteration": iterations,
                },
            )
            # Try to extract any response content from last iteration
            if last_response:
                assistant_text = session.llm.extract_assistant_content(last_response) or "I apologize, but I encountered an issue processing your request."
            else:
                assistant_text = "I apologize, but I encountered an issue processing your request."
            
            # Stream the error message
            chunk_size = 32
            for i in range(0, len(assistant_text), chunk_size):
                yield json.dumps({
                    "type": "text",
                    "content": assistant_text[i:i+chunk_size],
                    "conversation_id": conversation_id
                }) + "\n"
            
            session.messages.append({"role": "assistant", "content": assistant_text})
        
        if session.internal_sensing_framework and ResponseAnalyzer and 'assistant_text' in locals():
            try:
                response_id = getattr(session, "_current_response_id", f"response_{len(session.messages)}")
                # Only record operation end if operation start was called (check if response_id exists in starts)
                if hasattr(session.internal_sensing_framework.interoception.physiology, '_operation_starts'):
                    if response_id in session.internal_sensing_framework.interoception.physiology._operation_starts:
                        latency = session.internal_sensing_framework.interoception.physiology._record_operation_end(
                            response_id
                        )
                    else:
                        logger.debug(f"Skipping operation end for {response_id}: operation start not found")
                        latency = None
                else:
                    latency = None
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
    
    # Include RL signals in done message if requested
    done_data = {
        "type": "done",
        "conversation_id": conversation_id
    }
    
    # Add RL signals if requested and available
    if include_rl_signals and 'session' in locals() and 'rt' in locals():
        if rt.world_state_aggregator and hasattr(rt.world_state_aggregator, 'reasoning_tool'):
            reasoning_tool = rt.world_state_aggregator.reasoning_tool
            if reasoning_tool and hasattr(reasoning_tool, 'feedback_loop_manager'):
                feedback_loop_manager = reasoning_tool.feedback_loop_manager
                if feedback_loop_manager and feedback_loop_manager.rl_signals_enabled and feedback_loop_manager.rl_signal_aggregator:
                    try:
                        # Get affective state for RL signals
                        affective_state = None
                        if session.internal_sensing_framework:
                            try:
                                affective_state = session.internal_sensing_framework.get_current_affective_state()
                            except Exception:
                                pass
                        
                        # Get prediction error if available
                        prediction_error = None
                        if session.internal_sensing_framework and hasattr(session.internal_sensing_framework.interoception, 'predictive'):
                            try:
                                prediction_error = session.internal_sensing_framework.interoception.predictive.get_rl_prediction_error_signal()
                            except Exception:
                                pass
                        
                        # Compute RL signals
                        rl_metrics = feedback_loop_manager.rl_signal_aggregator.compute_signals(
                            affective_state=affective_state,
                            prediction_error=prediction_error,
                        )
                        
                        # Add RL signals to done message
                        done_data["rl_signals"] = {
                            "dissonance_reward": round(rl_metrics.dissonance_reward, 3),
                            "surprise_reward": round(rl_metrics.surprise_reward, 3),
                            "curiosity_reward": round(rl_metrics.curiosity_reward, 3),
                            "information_gain_reward": round(rl_metrics.information_gain_reward, 3),
                            "coherence_reward": round(rl_metrics.coherence_reward, 3),
                            "composite_reward": round(rl_metrics.composite_reward, 3),
                            "exploration_balance": round(rl_metrics.get_exploration_exploitation_balance(), 3),
                            "weights": {
                                "dissonance": rl_metrics.weight_dissonance,
                                "surprise": rl_metrics.weight_surprise,
                                "curiosity": rl_metrics.weight_curiosity,
                                "info_gain": rl_metrics.weight_info_gain,
                                "coherence": rl_metrics.weight_coherence,
                            }
                        }
                        
                        # Apply RL feedback
                        try:
                            from .reasoning.feedback_loop import FeedbackMetrics
                            feedback_metrics = FeedbackMetrics(window_size=1)
                            feedback_loop_manager._apply_rl_feedback(
                                feedback_metrics,
                                emotional_state=affective_state
                            )
                        except Exception as e:
                            logger.debug(f"Error applying RL feedback in stream_response: {e}", exc_info=True)
                            
                    except Exception as e:
                        logger.warning(f"Error computing RL signals in stream_response: {e}", exc_info=True)
    
    yield json.dumps(done_data) + "\n"

@app.post("/api/chat")
async def chat(req: ChatRequest):
    # Import config locally at the very start to avoid scoping issues
    from .config import config as app_config
    
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
                stream_response(req.conversation_id, last.content, web_search_enabled=req.web_search, include_rl_signals=req.include_rl_signals),
                media_type="application/x-ndjson"
            )

        session = create_session(req.conversation_id)
        
        # Ensure PEA loop managers are wired (in case they weren't available during create_session)
        rt = get_runtime()
        if session.pea_loop and rt.reasoning_tool:
            goal_manager = None
            skill_manager = None
            experience_logger = None
            
            if hasattr(rt.reasoning_tool, 'goal_manager'):
                goal_manager = rt.reasoning_tool.goal_manager
            if hasattr(rt.reasoning_tool, 'learning_tool') and rt.reasoning_tool.learning_tool:
                if hasattr(rt.reasoning_tool.learning_tool, 'skill_manager'):
                    skill_manager = rt.reasoning_tool.learning_tool.skill_manager
                if hasattr(rt.reasoning_tool.learning_tool, 'experience_logger'):
                    experience_logger = rt.reasoning_tool.learning_tool.experience_logger
            
            if goal_manager or skill_manager or experience_logger:
                session.wire_pea_loop_managers(
                    goal_manager=goal_manager,
                    skill_manager=skill_manager,
                    experience_logger=experience_logger,
                )
        
        reply_text = session.send(last.content, stream=False)
        
        # Compute RL signals if requested and available
        rl_signals_data = None
        if req.include_rl_signals:
            rt = get_runtime()
            if rt.world_state_aggregator and hasattr(rt.world_state_aggregator, 'reasoning_tool'):
                reasoning_tool = rt.world_state_aggregator.reasoning_tool
                if reasoning_tool and hasattr(reasoning_tool, 'feedback_loop_manager'):
                    feedback_loop_manager = reasoning_tool.feedback_loop_manager
                    if feedback_loop_manager and feedback_loop_manager.rl_signals_enabled and feedback_loop_manager.rl_signal_aggregator:
                        try:
                            # Get affective state for RL signals
                            affective_state = None
                            if session.internal_sensing_framework:
                                try:
                                    affective_state = session.internal_sensing_framework.get_current_affective_state()
                                except Exception:
                                    pass
                            
                            # Get prediction error if available
                            prediction_error = None
                            if session.internal_sensing_framework and hasattr(session.internal_sensing_framework.interoception, 'predictive'):
                                try:
                                    prediction_error = session.internal_sensing_framework.interoception.predictive.get_rl_prediction_error_signal()
                                except Exception:
                                    pass
                            
                            # Compute RL signals
                            rl_metrics = feedback_loop_manager.rl_signal_aggregator.compute_signals(
                                affective_state=affective_state,
                                prediction_error=prediction_error,
                            )
                            
                            # Prepare RL signals data for response
                            rl_signals_data = {
                                "dissonance_reward": round(rl_metrics.dissonance_reward, 3),
                                "surprise_reward": round(rl_metrics.surprise_reward, 3),
                                "curiosity_reward": round(rl_metrics.curiosity_reward, 3),
                                "information_gain_reward": round(rl_metrics.information_gain_reward, 3),
                                "coherence_reward": round(rl_metrics.coherence_reward, 3),
                                "composite_reward": round(rl_metrics.composite_reward, 3),
                                "exploration_balance": round(rl_metrics.get_exploration_exploitation_balance(), 3),
                                "weights": {
                                    "dissonance": rl_metrics.weight_dissonance,
                                    "surprise": rl_metrics.weight_surprise,
                                    "curiosity": rl_metrics.weight_curiosity,
                                    "info_gain": rl_metrics.weight_info_gain,
                                    "coherence": rl_metrics.weight_coherence,
                                }
                            }
                            
                            # Apply RL feedback
                            try:
                                from .reasoning.feedback_loop import FeedbackMetrics
                                feedback_metrics = FeedbackMetrics(window_size=1)
                                feedback_loop_manager._apply_rl_feedback(
                                    feedback_metrics,
                                    emotional_state=affective_state
                                )
                            except Exception as e:
                                logger.debug(f"Error applying RL feedback in chat endpoint: {e}", exc_info=True)
                                
                        except Exception as e:
                            logger.warning(f"Error computing RL signals in chat endpoint: {e}", exc_info=True)
        
        storage = get_storage()
        data = storage.load_conversation(req.conversation_id)
        metadata = data.get("metadata", {}) if data else {}
        if metadata.get("title") == "New conversation":
            metadata["title"] = generate_title(last.content)
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        storage.save_conversation(req.conversation_id, session.messages, metadata)
        
        return ChatResponse(
            conversation_id=req.conversation_id,
            reply=Message(role="assistant", content=reply_text),
            rl_signals=rl_signals_data
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
async def update_project_config(project_config: ProjectConfig):
    """Update project configuration."""
    global PROJECT_ROOT
    new_path = Path(project_config.root_path).resolve()
    if not new_path.exists():
        raise HTTPException(status_code=400, detail="Path does not exist")
    PROJECT_ROOT = new_path
    return {"success": True, "root_path": str(PROJECT_ROOT)}
