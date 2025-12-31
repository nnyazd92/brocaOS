from typing import Literal, List, Optional, Dict, Any, Generator
from uuid import uuid4
from datetime import datetime, timezone
import json
import logging
import os
import time
from pathlib import Path

import psutil
import threading
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
import uvicorn

from .main_repl_runtime import initialize_runtime, BrocaRuntime
from .repl.session import ConversationSession
# PEA/PFREA removed - planning is now handled via planning tool
from .memory import SourceType, RelationType

# RL Reward Logger
_rl_reward_logger = None

# Tool selection logger (shared with rl.online_policy)
_tool_selection_logger = None

def _get_tool_selection_logger():
    """Get tool selection logger from RL module."""
    global _tool_selection_logger
    if _tool_selection_logger is None:
        try:
            from .rl.tool_selection_logging import get_tool_selection_logger
            _tool_selection_logger = get_tool_selection_logger()
        except Exception:
            _tool_selection_logger = logger
    return _tool_selection_logger

def _get_rl_reward_logger():
    """Get or initialize RL reward logger."""
    global _rl_reward_logger
    if _rl_reward_logger is None:
        try:
            from .reasoning.rl_reward_logger import RLRewardLogger
            from .reasoning.config import ReasoningConfig
            config = ReasoningConfig()
            _rl_reward_logger = RLRewardLogger(
                log_file=config.rl_reward_log_file,
                enabled=config.rl_reward_log_enabled,
                append=config.rl_reward_log_append
            )
            if config.rl_reward_log_enabled:
                logger.info(f"RL reward logger initialized: enabled=True, file={config.rl_reward_log_file}")
            else:
                logger.info("RL reward logger initialized but disabled by config")
        except Exception as e:
            logger.warning(f"Failed to initialize RL reward logger: {e}", exc_info=True)
            # Return a dummy logger that does nothing
            class DummyLogger:
                def log_reward_signals(self, *args, **kwargs):
                    pass
            _rl_reward_logger = DummyLogger()
    return _rl_reward_logger

# Import ResponseAnalyzer for internal sensing integration
try:
    from .internal_sensing.response_analyzer import ResponseAnalyzer
except ImportError:
    ResponseAnalyzer = None  # type: ignore

logger = logging.getLogger(__name__)

class _MetricsCache:
    """
    Thread-safe cache for /api/metrics.

    /api/metrics is polled heavily by the frontend. Doing blocking psutil sampling
    inside an async handler (e.g., cpu_percent(interval=0.1)) stalls the event loop.
    We instead sample in a background thread and serve cached results instantly.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: Optional[Dict[str, Any]] = None
        self._boot_time: Optional[float] = None

    def set_snapshot(self, snapshot: Dict[str, Any]) -> None:
        with self._lock:
            self._snapshot = snapshot

    def get_snapshot(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return dict(self._snapshot) if self._snapshot is not None else None

    def get_boot_time(self) -> float:
        with self._lock:
            if self._boot_time is None:
                self._boot_time = float(psutil.boot_time())
            return float(self._boot_time)


_metrics_cache = _MetricsCache()
_metrics_thread_started = False


def _start_metrics_sampler_thread(interval_sec: float = 0.5) -> None:
    global _metrics_thread_started
    if _metrics_thread_started:
        return
    _metrics_thread_started = True

    def _loop() -> None:
        # Prime cpu_percent so subsequent calls have a baseline. This is non-blocking.
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

        while True:
            try:
                cpu = psutil.cpu_percent(interval=None) / 100.0
                vm = psutil.virtual_memory()
                mem = (vm.used / vm.total) if getattr(vm, "total", 0) else 0.0
                now_sec = time.time()
                boot_time = _metrics_cache.get_boot_time()
                uptime = int(now_sec - boot_time)
                _metrics_cache.set_snapshot(
                    {
                        "cpu": max(0.0, min(float(cpu), 1.0)),
                        "memory": max(0.0, min(float(mem), 1.0)),
                        "uptime": int(uptime),
                        "timestamp": int(now_sec * 1000),
                    }
                )
            except Exception:
                # Never crash this loop; worst case metrics will be stale.
                pass

            time.sleep(max(0.05, float(interval_sec)))

    t = threading.Thread(target=_loop, daemon=True, name="broca-metrics-sampler")
    t.start()


def _clean_pfrea_references(text: str) -> tuple[str, bool]:
    """
    Clean PFREA references from response text as a safety net.
    
    Removes:
    - Section headers like "## PLAN", "## FORECAST", "## EXECUTION", "## ASSESS"
    - Phase labels like "PLAN:", "FORECAST:", "EXECUTION:", "ASSESS:"
    - References to PFREA, planning phases, etc.
    
    Args:
        text: Response text to clean
        
    Returns:
        Tuple of (cleaned_text, had_pfrea_refs)
    """
    import re
    
    cleaned = text
    had_refs = False
    
    # Remove PFREA section headers (## PLAN, ## FORECAST, etc.)
    pfrea_headers = [
        r'##\s*PLAN\s*:?\s*\n',
        r'##\s*FORECAST\s*:?\s*\n',
        r'##\s*EXECUTION\s*:?\s*\n',
        r'##\s*EXECUTE\s*:?\s*\n',
        r'##\s*ASSESS\s*:?\s*\n',
        r'##\s*ASSESSMENT\s*:?\s*\n',
        r'\*\*PLAN\*\*\s*:?\s*\n',
        r'\*\*FORECAST\*\*\s*:?\s*\n',
        r'\*\*EXECUTION\*\*\s*:?\s*\n',
        r'\*\*EXECUTE\*\*\s*:?\s*\n',
        r'\*\*ASSESS\*\*\s*:?\s*\n',
        r'\*\*ASSESSMENT\*\*\s*:?\s*\n',
    ]
    
    for pattern in pfrea_headers:
        if re.search(pattern, cleaned, re.IGNORECASE):
            had_refs = True
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove phase labels at start of lines (PLAN:, FORECAST:, etc.)
    phase_labels = [
        r'^PLAN\s*:?\s*\n',
        r'^FORECAST\s*:?\s*\n',
        r'^EXECUTION\s*:?\s*\n',
        r'^EXECUTE\s*:?\s*\n',
        r'^ASSESS\s*:?\s*\n',
        r'^ASSESSMENT\s*:?\s*\n',
    ]
    
    for pattern in phase_labels:
        if re.search(pattern, cleaned, re.IGNORECASE | re.MULTILINE):
            had_refs = True
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove explicit PFREA mentions
    if re.search(r'\bPFREA\b', cleaned, re.IGNORECASE):
        had_refs = True
        cleaned = re.sub(r'\bPFREA\b', '', cleaned, flags=re.IGNORECASE)
    
    # Clean up multiple newlines that might result from removals
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned, had_refs


def _log_tool_call_rl_reward(
    *,
    reward_logger: Any,
    tool_call: Dict[str, Any],
    session_messages: List[Dict[str, Any]],
    world_state_aggregator: Optional[Any],
) -> None:
    """
    Web API path executes tools directly (not via ConversationSession._handle_tool_calls()).
    This helper ensures we still append a row to rl_rewards.csv per tool execution.
    """
    try:
        if reward_logger is None or not getattr(reward_logger, "enabled", False):
            return

        # Guard: In pytest runs, avoid polluting the *real* RL rewards dataset,
        # but still allow tests to log into temporary paths.
        import sys
        try:
            log_file_str = str(getattr(reward_logger, "log_file", ""))
        except Exception:
            log_file_str = ""
        if ("pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST")) and ("data/rl_rewards.csv" in log_file_str):
            return

        tool_name = tool_call.get("function", {}).get("name", "unknown")
        tool_call_id = tool_call.get("id", "")
        
        # Guard: Skip logging for test tools
        if tool_name.startswith("test_") or tool_name == "test_tool":
            return

        # Best-effort: compute real RL metrics from the reasoning tool if available.
        rl_metrics = None
        if world_state_aggregator and hasattr(world_state_aggregator, "reasoning_tool") and world_state_aggregator.reasoning_tool:
            reasoning_tool = world_state_aggregator.reasoning_tool
            fb = getattr(reasoning_tool, "feedback_loop_manager", None)
            agg = getattr(fb, "rl_signal_aggregator", None) if fb is not None else None

            if agg is not None:
                try:
                    # Best-effort: pre-measure dissonance so tool-call rows don't default to neutral.
                    cd_monitor = getattr(fb, "cognitive_dissonance_monitor", None)
                    if cd_monitor is not None:
                        try:
                            cd_monitor.measure_dissonance(
                                response=None,
                                tool_usage=[tool_call] if isinstance(tool_call, dict) else None,
                                conversation_context=session_messages,
                            )
                        except Exception:
                            pass

                    rl_metrics = agg.compute_signals()
                except Exception:
                    rl_metrics = None

        # Guard: Skip logging if context matches test pattern
        context = f"tool_call_{tool_name}_{tool_call_id}"
        if context.startswith("tool_call_test_"):
            return

        if rl_metrics is not None:
            reward_logger.log_reward_signals(rl_metrics, context=context)
            return

        # Fallback: always log a tool-call row even if real RL signals are unavailable.
        from .reasoning.rl_signals import RLSignalMetrics
        from .config import config as app_config

        minimal = RLSignalMetrics(
            timestamp=datetime.now(timezone.utc),
            dissonance_reward=0.0,
            surprise_reward=0.0,
            curiosity_reward=0.0,
            information_gain_reward=0.0,
            coherence_reward=0.0,
            weight_dissonance=getattr(app_config.reasoning, "rl_weight_dissonance", 0.3),
            weight_surprise=getattr(app_config.reasoning, "rl_weight_surprise", 0.2),
            weight_curiosity=getattr(app_config.reasoning, "rl_weight_curiosity", 0.2),
            weight_info_gain=getattr(app_config.reasoning, "rl_weight_info_gain", 0.15),
            weight_coherence=getattr(app_config.reasoning, "rl_weight_coherence", 0.15),
        )
        minimal.composite_reward = minimal.compute_composite()
        reward_logger.log_reward_signals(minimal, context=context)
    except Exception:
        # Never let logging failures break streaming/tool execution.
        return

# Global runtime components (shared)
_runtime: Optional[BrocaRuntime] = None
_runtime_status: str = "not_started"  # not_started | initializing | ready | error
_runtime_lock = threading.Lock()
_runtime_init_started_at: Optional[float] = None
_runtime_ready_at: Optional[float] = None
_runtime_init_error: Optional[str] = None
PROJECT_ROOT: Path = Path(__file__).parent.parent.resolve()

app = FastAPI(title="BrocaOS Web API")


@app.on_event("startup")
async def _startup_metrics_sampler() -> None:
    # Start sampler early so the first metrics request is instant.
    _start_metrics_sampler_thread(interval_sec=0.5)
    # Start heavy runtime initialization off the event loop to avoid blocking the web server.
    _ensure_runtime_initializing()


def _ensure_runtime_initializing() -> None:
    """
    Ensure the BrocaRuntime initialization is in progress in a background thread.

    This prevents the first request from blocking the event loop while we load the memory index,
    self-model, reasoning daemon, etc.
    """
    global _runtime_status, _runtime_init_started_at, _runtime_init_error
    with _runtime_lock:
        if _runtime_status in ("initializing", "ready"):
            return
        if _runtime_status == "error":
            # Do not auto-retry; surface the error via /api/healthz.
            return

        _runtime_status = "initializing"
        _runtime_init_started_at = time.time()
        _runtime_init_error = None

        def _init() -> None:
            global _runtime, _runtime_status, _runtime_ready_at, _runtime_init_error
            try:
                rt = initialize_runtime()
                with _runtime_lock:
                    _runtime = rt
                    _runtime_status = "ready"
                    _runtime_ready_at = time.time()
                    _runtime_init_error = None
                logger.info("Web API runtime initialized (ready)")
            except Exception as e:
                with _runtime_lock:
                    _runtime = None
                    _runtime_status = "error"
                    _runtime_init_error = str(e)
                logger.error(f"Web API runtime initialization failed: {e}", exc_info=True)

        t = threading.Thread(target=_init, daemon=True, name="broca-runtime-init")
        t.start()


@app.get("/api/healthz")
async def healthz() -> Dict[str, Any]:
    """
    Lightweight readiness endpoint.

    - Always responds quickly (no runtime init side-effects)
    - Exposes runtime init state for the frontend and operational debugging
    """
    with _runtime_lock:
        status = _runtime_status
        started_at = _runtime_init_started_at
        ready_at = _runtime_ready_at
        err = _runtime_init_error

    now = time.time()
    init_age = (now - started_at) if started_at else None
    return {
        "status": status,
        "init_started_at": started_at,
        "init_ready_at": ready_at,
        "init_age_sec": init_age,
        "error": err,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class RequestState:
    """
    Thread-safe request state tracking.
    
    Tracks active requests and last work timestamp with proper synchronization
    for multi-worker/async FastAPI deployments.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._last_work_ts: float = 0.0
        self._active_requests: int = 0
    
    def mark_work(self) -> None:
        """Mark that the system is actively processing work."""
        with self._lock:
            self._last_work_ts = time.time()
    
    def begin_request(self) -> None:
        """Mark the start of a request that may involve tools / cognition."""
        with self._lock:
            self._active_requests += 1
            self._last_work_ts = time.time()
    
    def end_request(self) -> None:
        """Mark the end of an active request."""
        with self._lock:
            if self._active_requests > 0:
                self._active_requests -= 1
            self._last_work_ts = time.time()
    
    def get_metrics(self, recent_window: float = 5.0) -> Dict[str, Any]:
        """
        Get current metrics in a thread-safe way.
        
        Args:
            recent_window: Time window in seconds to consider recent work
            
        Returns:
            Dictionary with metrics including is_working flag
        """
        now_sec = time.time()
        with self._lock:
            active_requests = self._active_requests
            last_work_ts = self._last_work_ts
        
        is_working = active_requests > 0 or (now_sec - last_work_ts) < recent_window
        
        return {
            "active_requests": active_requests,
            "last_work_ts": last_work_ts,
            "is_working": is_working,
        }


# Singleton instance for request state
_request_state = RequestState()


# Convenience functions for backward compatibility
def mark_work() -> None:
    """Mark that the system is actively processing work."""
    _request_state.mark_work()


def begin_request() -> None:
    """Mark the start of a request that may involve tools / cognition."""
    _request_state.begin_request()


def end_request() -> None:
    """Mark the end of an active request."""
    _request_state.end_request()



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


class MemoryQueryRequest(BaseModel):
    """Request model for /api/memories."""

    query: Optional[str] = Field(
        default=None,
        description="Text query for semantic search. Required unless memory_ids is provided."
    )
    memory_ids: Optional[List[int]] = Field(
        default=None,
        description="Optional list of memory IDs to retrieve directly."
    )
    namespace: Optional[str] = None
    namespaces: Optional[List[str]] = None
    namespace_exact: bool = Field(default=False, description="Use exact namespace matching when true.")
    tags: Optional[List[str]] = None
    tag_mode: Literal["any", "all"] = Field(default="any")
    query_phrases: Optional[List[str]] = None
    limit: int = Field(default=5, ge=1, le=20)
    recency_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    last_used_after: Optional[str] = None
    last_used_before: Optional[str] = None
    min_importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    min_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    rank_by_confidence: bool = Field(default=True)
    warn_low_confidence: bool = Field(default=True)
    source_types: Optional[List[SourceType]] = None
    include_linked: bool = Field(default=True)
    linked_limit: int = Field(default=5, ge=1, le=10)

    model_config = ConfigDict(use_enum_values=True)

class TitleUpdate(BaseModel):
    title: str

def get_runtime() -> BrocaRuntime:
    global _runtime
    # Never initialize runtime synchronously on the request path.
    _ensure_runtime_initializing()
    with _runtime_lock:
        if _runtime_status == "ready" and _runtime is not None:
            return _runtime
        if _runtime_status == "error":
            raise HTTPException(status_code=500, detail=f"Runtime initialization failed: {_runtime_init_error}")
        # initializing / not_started
        raise HTTPException(status_code=503, detail="Runtime initializing, try again shortly")

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
    """Generate a short, punchy title using the LLM.
    
    Note: This function blocks and should be called in a background thread/task.
    For non-blocking usage, use update_conversation_title_async() instead.
    
    Uses direct LLM call to avoid tool access and PFREA loop interference.
    This is a legitimate bypass because:
    - Simple LLM call with no tool usage
    - No planning or execution required
    - No state changes or side effects
    - Fast, stateless operation
    """
    # Log PFREA bypass
    try:
        from .reasoning.pfrea_tracker import get_pfrea_tracker, PFREAEventType
        tracker = get_pfrea_tracker()
        if tracker:
            tracker.record_bypass(
                reason="title_generation",
                justification="Simple LLM call with no tool usage or planning required. Stateless operation with no side effects.",
                context={"user_message_preview": user_message[:50]}
            )
    except Exception as e:
        logger.debug(f"Could not record PFREA bypass: {e}")
    
    logger.info(
        "PFREA: Bypassed for title generation (legitimate - no planning needed)",
        extra={
            "event": "pfrea_bypass",
            "reason": "title_generation",
            "justification": "Simple LLM call with no tool usage or planning required",
            "session_id": None,  # No session for this operation
        }
    )
    
    rt = get_runtime()
    prompt = f"Generate a very short (max 5 words), punchy title for a conversation that starts with: '{user_message}'. Return ONLY the title text, no quotes or punctuation."
    
    # Use direct LLM call to avoid tool access and session overhead
    # Make system prompt very explicit to prevent PFREA loop behavior
    system_prompt = (
        "You are a simple title generator. Your ONLY task is to generate a short title (3-5 words).\n\n"
        "CRITICAL RULES:\n"
        "1. DO NOT create a plan, forecast, or any structured response\n"
        "2. DO NOT use any tools or make tool calls\n"
        "3. DO NOT write explanations, steps, assumptions, or any other text\n"
        "4. Return ONLY the title text itself (3-5 words)\n"
        "5. No quotes, no punctuation, no markdown, no formatting\n"
        "6. Just the title words, nothing else\n\n"
        "Example: If asked for a title about 'Hello world', return: Hello World\n"
        "NOT: 'Hello World' or ## Hello World or any other format.\n\n"
        "Remember: ONLY the title text, nothing else."
    )
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Direct LLM call - no session, no tools, no PFREA loop
        # Note: Temperature handling (including gpt-5 model compatibility) is handled by the LLM client
        response = rt.session.llm.chat(messages, temperature=0.7)
        title = rt.session.llm.extract_assistant_content(response)
        
        if not title:
            return user_message[:40] + "..."
        
        # Extract title from response - handle cases where LLM returns extra content
        title = title.strip()
        
        # Remove markdown formatting
        title = title.replace("**", "").replace("*", "").replace("#", "").strip()
        
        # If response contains structured sections (Plan, Forecast, etc.), extract just the title
        # Look for the last line that's short and looks like a title
        lines = [line.strip() for line in title.split('\n') if line.strip()]
        
        # Filter out lines that look like structured sections
        title_candidates = []
        skip_keywords = ['plan', 'forecast', 'goal', 'steps', 'assumptions', 'expected', 
                        'feasibility', 'predicted', 'risks', 'issues', 'recommendations',
                        'assumptions', 'outcomes', 'score']
        
        for line in lines:
            line_lower = line.lower()
            # Skip lines that start with section headers
            if any(line_lower.startswith(kw + ':') or line_lower.startswith('## ' + kw) 
                   for kw in skip_keywords):
                continue
            # Skip lines that are just numbers or bullets
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')):
                continue
            # Keep short lines that look like titles (3-5 words, no colons after first word)
            words = line.split()
            if 2 <= len(words) <= 6:
                # Check if it's not a structured field (no colons except maybe at very end)
                if ':' not in line or line.count(':') == 1 and line.endswith(':'):
                    title_candidates.append(line)
        
        # If we found title candidates, use the last one (most likely to be the actual title)
        if title_candidates:
            title = title_candidates[-1]
        else:
            # Fallback: use the last line that's reasonably short
            for line in reversed(lines):
                words = line.split()
                if 2 <= len(words) <= 8:
                    # Remove any trailing punctuation/formatting
                    title = line.rstrip('.,;:!?')
                    break
        
        # Final cleanup
        title = title.strip().strip('"').strip("'").strip()
        # Remove any remaining markdown or special characters at start/end
        title = title.lstrip('#').strip()
        
        # If title is still too long or contains structured content, use first few words
        words = title.split()
        if len(words) > 6:
            title = ' '.join(words[:5])
        
        # Final validation - if it looks like structured content, fall back to user message
        if any(kw in title.lower() for kw in ['plan', 'forecast', 'goal:', 'steps:', 'feasibility']):
            logger.warning(f"Title generation returned structured content, using fallback")
            return user_message[:40] + "..."
        
        return title if title and len(title) > 0 else user_message[:40] + "..."
    except Exception as e:
        logger.warning(f"Failed to generate title: {e}", exc_info=True)
        return user_message[:40] + "..."


def update_conversation_title_async(conversation_id: str, user_message: str) -> None:
    """Update conversation title asynchronously in background."""
    try:
        title = generate_title(user_message)
        storage = get_storage()
        data = storage.load_conversation(conversation_id)
        if data:
            metadata = data.get("metadata", {})
            metadata["title"] = title
            metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
            storage.save_conversation(conversation_id, data.get("messages", []), metadata)
            logger.debug(f"Updated conversation title asynchronously: {title}")
    except Exception as e:
        logger.warning(f"Failed to update conversation title asynchronously: {e}", exc_info=True)


@app.get("/api/metrics")
async def metrics():
    now_sec = time.time()
    RECENT_WINDOW = 5.0
    
    # Get thread-safe metrics
    state_metrics = _request_state.get_metrics(recent_window=RECENT_WINDOW)
    is_working = state_metrics["is_working"]

    snap = _metrics_cache.get_snapshot()
    if not snap:
        # Safe defaults: never block the async path. The background sampler will populate soon.
        boot_time = _metrics_cache.get_boot_time()
        snap = {
            "cpu": 0.0,
            "memory": 0.0,
            "uptime": int(now_sec - boot_time),
            "timestamp": int(now_sec * 1000),
        }

    return {
        "cpu": snap["cpu"],
        "memory": snap["memory"],
        "uptime": snap["uptime"],
        "isWorking": is_working,
        "timestamp": snap["timestamp"],
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
        
        # Note: Z3 validator has been removed. Use the z3_validate tool instead.
        # Z3 validation is no longer available via this endpoint.
        
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
                        
                        # Log RL reward signals to CSV
                        try:
                            reward_logger = _get_rl_reward_logger()
                            if reward_logger and hasattr(reward_logger, 'enabled') and reward_logger.enabled:
                                reward_logger.log_reward_signals(rl_metrics, context="cognitive_query")
                        except Exception as e:
                            logger.warning(f"Failed to log RL reward signals: {e}", exc_info=True)
                        
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
    
    # PEA/PFREA removed - planning is now handled via planning tool

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
    
    # PEA/PFREA removed - planning is now handled via planning tool
    
    try:
        # Gather context for tool filtering/ranking if guidance is enabled
        context = None
        if (rt.tool_registry and 
            hasattr(rt.tool_registry, 'tool_selection_guidance') and
            rt.tool_registry.tool_selection_guidance is not None):
            try:
                if app_config and app_config.tools.pre_filtering_enabled:
                    context = rt.tool_registry.tool_selection_guidance.guidance_aggregator.gather_context()
                    # Attach lightweight text features for RL policies (hashed embedding).
                    # These are used as FEATURES only (never part of reward).
                    if isinstance(context, dict):
                        last_assistant = ""
                        try:
                            for m in reversed(session.messages):
                                if isinstance(m, dict) and m.get("role") == "assistant" and isinstance(m.get("content"), str) and m.get("content"):
                                    last_assistant = m["content"]
                                    break
                        except Exception:
                            last_assistant = ""

                        context["text_features"] = {
                            "user_prompt": user_message or "",
                            "last_assistant": last_assistant,
                        }
            except Exception as e:
                logger.debug(f"Error gathering context for tool filtering in web_api: {e}", exc_info=True)
        
        # Get RL-based tool selection with confidence gating
        rl_selection = None
        ts_logger = _get_tool_selection_logger()
        
        ts_logger.info(
            f"API_REQUEST | conversation_id={conversation_id} | "
            f"rl_enabled={app_config.rl.enabled if app_config else False} | "
            f"user_message_length={len(user_message)}"
        )
        
        if rt.tool_registry and app_config and app_config.rl.enabled:
            try:
                rl_selection = rt.tool_registry.get_rl_selection(context=context)
                if rl_selection:
                    ts_logger.info(
                        f"API_RL_SELECTION | conversation_id={conversation_id} | "
                        f"mode={rl_selection.mode} | confidence={rl_selection.confidence:.2%} | "
                        f"tool={rl_selection.tool_name} | score={rl_selection.score:.4f} | "
                        f"alternatives={[(t, f'{s:.4f}') for t, s in rl_selection.alternatives]} | "
                        f"reason={rl_selection.reason}"
                    )
                    
                    logger.info(
                        f"RL selection: mode={rl_selection.mode}, tool={rl_selection.tool_name}, "
                        f"confidence={rl_selection.confidence:.1%}",
                        extra={
                            "event": "web_api_rl_selection",
                            "mode": rl_selection.mode,
                            "tool": rl_selection.tool_name,
                            "confidence": rl_selection.confidence,
                            "reason": rl_selection.reason,
                        }
                    )
                else:
                    ts_logger.debug(
                        f"API_RL_SELECTION | conversation_id={conversation_id} | "
                        f"result=none | reason=ranker_returned_none"
                    )
            except Exception as e:
                ts_logger.warning(
                    f"API_RL_ERROR | conversation_id={conversation_id} | error={str(e)}"
                )
                logger.debug(f"Error getting RL selection in web_api: {e}", exc_info=True)
        else:
            ts_logger.debug(
                f"API_RL_SKIP | conversation_id={conversation_id} | "
                f"reason={'no_registry' if not rt.tool_registry else 'rl_disabled'}"
            )
        
        # IMPORTANT: RL selection must be recomputed per tool-call iteration (not just once per user message).
        # This keeps PPO/online NN "in the loop" between tool calls and allows next_state features
        # (including tool_args/tool_result text features) to influence subsequent selections.
        tools = None

        iterations = 0
        last_warning_iteration = 0
        max_iterations = 100  # Match session.send() max iterations
        assistant_text = None
        last_response = None
        forced_reprompt_budget = 0
        last_forced_tool_name: Optional[str] = None
        
        while iterations < max_iterations:
            iterations += 1
            session._update_system_prompt()
            
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

            # --- Recompute RL selection + tool list EACH iteration (per tool call) ---
            context = None
            if (
                rt.tool_registry
                and hasattr(rt.tool_registry, "tool_selection_guidance")
                and rt.tool_registry.tool_selection_guidance is not None
            ):
                try:
                    if app_config and app_config.tools.pre_filtering_enabled:
                        context = rt.tool_registry.tool_selection_guidance.guidance_aggregator.gather_context()
                        if isinstance(context, dict):
                            last_assistant = ""
                            try:
                                for m in reversed(session.messages):
                                    if (
                                        isinstance(m, dict)
                                        and m.get("role") == "assistant"
                                        and isinstance(m.get("content"), str)
                                        and m.get("content")
                                    ):
                                        last_assistant = m["content"]
                                        break
                            except Exception:
                                last_assistant = ""

                            # Stable per-user-message prompt, plus rolling last_assistant.
                            context["text_features"] = {
                                "user_prompt": user_message or "",
                                "last_assistant": last_assistant,
                            }
                except Exception as e:
                    logger.debug(
                        f"Error gathering context for tool filtering in web_api (iteration {iterations}): {e}",
                        exc_info=True,
                    )

            rl_selection = None
            forced_tool_name = None
            if rt.tool_registry and app_config and app_config.rl.enabled:
                try:
                    rl_selection = rt.tool_registry.get_rl_selection(context=context)
                    if rl_selection:
                        forced_tool_name = rl_selection.tool_name if getattr(rl_selection, "mode", None) == "forced" else None
                        ts_logger.info(
                            f"API_RL_SELECTION | conversation_id={conversation_id} | iteration={iterations} | "
                            f"mode={rl_selection.mode} | confidence={rl_selection.confidence:.2%} | "
                            f"tool={rl_selection.tool_name} | score={rl_selection.score:.4f} | "
                            f"alternatives={[(t, f'{s:.4f}') for t, s in rl_selection.alternatives]} | "
                            f"reason={rl_selection.reason}"
                        )
                except Exception as e:
                    ts_logger.warning(
                        f"API_RL_ERROR | conversation_id={conversation_id} | iteration={iterations} | error={str(e)}"
                    )
                    logger.debug(f"Error getting RL selection in web_api: {e}", exc_info=True)

            # Reprompt budget is per "forced selection episode", not global.
            # Reset budget when the forced tool changes (or forced mode ends).
            if forced_tool_name != last_forced_tool_name:
                if forced_tool_name:
                    forced_reprompt_budget = 3
                else:
                    forced_reprompt_budget = 0
                last_forced_tool_name = forced_tool_name

            tools = rt.tool_registry.to_openai_format(context=context, rl_selection=rl_selection) if rt.tool_registry else None

            if tools and not web_search_enabled:
                tools = [t for t in tools if t["function"]["name"] != "web_search"]

            tool_choice = None
            if forced_tool_name:
                # Best-effort "hard" enforcement. Some providers still violate tool schemas;
                # execution-time enforcement and reprompting are additional safety layers.
                tool_choice = {"type": "function", "function": {"name": forced_tool_name}}

            # PEA/PFREA removed - planning is now handled via planning tool
            
            messages_for_llm = session._get_messages_for_llm()
            response = session.llm.chat(messages_for_llm, tools=tools, tool_choice=tool_choice)
            last_response = response  # Store for max_iterations handling
            tool_calls = session.llm.extract_tool_calls(response)
            
            # Extract assistant content (intermediary commentary) before processing tool calls
            assistant_content = session.llm.extract_assistant_content(response) or None
            assistant_text = assistant_content  # Track for plan/forecast extraction
            
            # PEA/PFREA removed - planning is now handled via planning tool
            
            if session.internal_sensing_framework and tool_calls:
                try:
                    processing_depth = len(tool_calls) + iterations - 1
                    session.internal_sensing_framework.interoception.cognition.record_processing_depth(
                        f"turn_{iterations}", processing_depth
                    )
                except Exception as e:
                    logger.debug(f"Error tracking processing depth: {e}", exc_info=True)
            
            if tool_calls:
                # Provider/tool-calling compliance guard:
                # In forced mode, some providers/models may still emit a tool call to a disallowed tool.
                # Instead of executing and surfacing a blocked tool result to the UI, re-prompt the model
                # to call ONLY the forced tool (up to a small budget to avoid infinite loops).
                if forced_tool_name:
                    first_name = tool_calls[0].get("function", {}).get("name", "unknown")
                    if first_name != forced_tool_name:
                        if forced_reprompt_budget > 0:
                            forced_reprompt_budget -= 1
                            ts_logger.warning(
                                f"API_FORCED_TOOL_NONCOMPLIANCE | conversation_id={conversation_id} | iteration={iterations} | "
                                f"forced_tool={forced_tool_name} | requested_tool={first_name} | remaining_reprompts={forced_reprompt_budget}"
                            )
                            session.messages.append(
                                {
                                    "role": "user",
                                    "content": (
                                        f"[SYSTEM DIRECTIVE] RL forced-mode is active. "
                                        f"You MUST call the tool '{forced_tool_name}' now. "
                                        f"Do not call any other tools."
                                    ),
                                }
                            )
                            continue

                        # After reprompt budget is exhausted, let the request proceed.
                        # ToolRegistry will block out-of-buffer tool calls and return a tool error message.
                        # This gives the model a concrete tool error signal and another chance to adjust.
                        ts_logger.error(
                            f"API_FORCED_TOOL_NONCOMPLIANCE_BUDGET_EXHAUSTED | conversation_id={conversation_id} | iteration={iterations} | "
                            f"forced_tool={forced_tool_name} | requested_tool={first_name}"
                        )

                # PEA/PFREA removed - tool execution is always allowed
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
                
                # IMPORTANT: Execute at most ONE tool call per iteration so RL re-evaluates between tool calls.
                # This makes RL selection "kick in" per tool call, not just per user message.
                if len(tool_calls) > 1:
                    logger.info(
                        f"Multiple tool calls returned ({len(tool_calls)}); executing 1 and re-querying LLM",
                        extra={
                            "event": "multi_tool_calls_sequentialized",
                            "conversation_id": conversation_id,
                            "iteration": iterations,
                            "tool_calls_count": len(tool_calls),
                            "executing_tool": tool_calls[0].get("function", {}).get("name", "unknown"),
                        },
                    )
                tool_calls = [tool_calls[0]]

                # Create single assistant message with tool call(s) and content (preserves intermediary commentary)
                assistant_message = {
                    "role": "assistant",
                    "content": assistant_content,  # Preserve intermediary commentary
                    "tool_calls": tool_calls,
                }
                # Clean PFREA references from final response (safety net)
                if assistant_content:
                    cleaned_content, had_pfrea_refs = _clean_pfrea_references(assistant_content)
                    if had_pfrea_refs:
                        logger.warning(
                            "PFREA references detected and removed from final response in stream_response",
                            extra={
                                "event": "pfrea_references_cleaned_stream",
                                "conversation_id": conversation_id,
                                "original_length": len(assistant_content),
                                "cleaned_length": len(cleaned_content),
                            }
                        )
                        assistant_message["content"] = cleaned_content
                        assistant_content = cleaned_content
                
                session.messages.append(assistant_message)
                
                # Process each tool call and yield streaming events
                for tc in tool_calls:
                    yield json.dumps({
                        "type": "tool_call",
                        "tool_call": tc,
                        "conversation_id": conversation_id
                    }) + "\n"
                    
                    result_dict = rt.tool_registry.execute_tool_call(tc)

                    # Log RL reward signals per tool call (append-only)
                    # Note: stream_response bypasses ConversationSession._handle_tool_calls(),
                    # so we must log here to avoid missing tool executions in rl_rewards.csv.
                    _log_tool_call_rl_reward(
                        reward_logger=_get_rl_reward_logger(),
                        tool_call=tc,
                        session_messages=session.messages,
                        world_state_aggregator=rt.world_state_aggregator,
                    )
                    
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
                    
                    # PEA/PFREA removed - no action execution tracking needed
                
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
                
                # PEA/PFREA removed - no auto-transitions needed
                
                # Continue loop automatically after tool results (matches session.send() behavior)
                continue
            else:
                # No tool calls - check if final response is allowed
                content = session.llm.extract_assistant_content(response)
                if not content:
                    content = "I apologize, but I encountered an issue processing your request."
                
                # PEA/PFREA removed - final responses are always allowed
                
                # Final response is allowed - deliver it
                chunk_size = 32
                for i in range(0, len(content), chunk_size):
                    yield json.dumps({
                        "type": "text",
                        "content": content[i:i+chunk_size],
                        "conversation_id": conversation_id
                    }) + "\n"
                
                # Clean PFREA references from final response (safety net)
                cleaned_content, had_pfrea_refs = _clean_pfrea_references(content)
                if had_pfrea_refs:
                    logger.warning(
                        "PFREA references detected and removed from final response in stream_response",
                        extra={
                            "event": "pfrea_references_cleaned_stream",
                            "conversation_id": conversation_id,
                            "original_length": len(content),
                            "cleaned_length": len(cleaned_content),
                        }
                    )
                    content = cleaned_content
                
                session.messages.append({"role": "assistant", "content": content})
                assistant_text = content
                
                # PEA/PFREA removed - no final response tracking needed
                
                # Measure cognitive dissonance and compute RL signals if available
                rl_signals_data = None
                if rt.world_state_aggregator and hasattr(rt.world_state_aggregator, 'reasoning_tool'):
                    reasoning_tool = rt.world_state_aggregator.reasoning_tool
                    if reasoning_tool:
                        # Run consistency checking and dissonance measurement (NON-BLOCKING - runs in background)
                        # This is critical for populating logical/factual/behavioral violation histories
                        if content:
                            import threading
                            
                            def check_consistency_and_measure_dissonance_async():
                                """
                                Background task that:
                                1. Runs consistency checking via ConsistencyLayer (populates violation histories)
                                2. Measures cognitive dissonance from conversation
                                
                                This ensures component_availability is properly set based on actual violations.
                                """
                                try:
                                    # 1. Run consistency checking if ConsistencyLayer is available
                                    # This calls observe_consistency_result() which populates
                                    # logical_violations, factual_errors, etc.
                                    if rt.consistency_layer is not None:
                                        try:
                                            logger.debug("Running consistency check on response (background thread)")
                                            conversation_context = [
                                                {"role": m.get("role", "user"), "content": m.get("content", "")}
                                                for m in session.messages
                                                if isinstance(m, dict) and m.get("content")
                                            ]
                                            # check_response() calls observe_consistency_result() internally
                                            _, was_updated, consistency_result = rt.consistency_layer.check_response(
                                                response=content,
                                                conversation_context=conversation_context,
                                            )
                                            if consistency_result:
                                                logger.debug(
                                                    f"Consistency check completed: is_consistent={consistency_result.is_consistent}, "
                                                    f"violations={len(consistency_result.violations)}, "
                                                    f"severity={consistency_result.severity:.3f}",
                                                    extra={
                                                        "event": "consistency_check_completed",
                                                        "is_consistent": consistency_result.is_consistent,
                                                        "violations_count": len(consistency_result.violations),
                                                        "severity": consistency_result.severity,
                                                        "was_updated": was_updated,
                                                    }
                                                )
                                        except Exception as e:
                                            logger.warning(f"Error in consistency check (background): {e}", exc_info=True)
                                    
                                    # 2. Measure cognitive dissonance
                                    cognitive_dissonance_monitor = getattr(reasoning_tool, 'cognitive_dissonance_monitor', None)
                                    if cognitive_dissonance_monitor:
                                        try:
                                            logger.debug("Measuring cognitive dissonance from conversation (background thread)")
                                            cognitive_dissonance_monitor.measure_dissonance_from_conversation(
                                                response=content,
                                                messages=session.messages
                                            )
                                            logger.debug("Cognitive dissonance measurement completed")
                                        except Exception as e:
                                            logger.warning(f"Error measuring cognitive dissonance (background): {e}", exc_info=True)
                                            
                                except Exception as e:
                                    logger.warning(f"Error in background consistency/dissonance task: {e}", exc_info=True)
                            
                            # Start background thread (fire-and-forget)
                            thread = threading.Thread(target=check_consistency_and_measure_dissonance_async, daemon=True)
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
                                    
                                    # Log RL reward signals to CSV
                                    try:
                                        reward_logger = _get_rl_reward_logger()
                                        if reward_logger and hasattr(reward_logger, 'enabled') and reward_logger.enabled:
                                            reward_logger.log_reward_signals(
                                                rl_metrics, 
                                                context=f"stream_response_{conversation_id}"
                                            )
                                    except Exception as e:
                                        logger.warning(f"Failed to log RL reward signals: {e}", exc_info=True)
                                    
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
            
            # Clean PFREA references from final response (safety net)
            if assistant_text:
                cleaned_text, had_pfrea_refs = _clean_pfrea_references(assistant_text)
                if had_pfrea_refs:
                    logger.warning(
                        "PFREA references detected and removed from final response in stream_response",
                        extra={
                            "event": "pfrea_references_cleaned_stream",
                            "conversation_id": conversation_id,
                            "original_length": len(assistant_text),
                            "cleaned_length": len(cleaned_text),
                        }
                    )
                    assistant_text = cleaned_text
            
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
            # Don't block - title generation will happen in background thread
            # Use default title for now, will be updated asynchronously
            metadata["title"] = user_message[:40] + "..."
            # Schedule title generation in background thread (non-blocking)
            import threading
            thread = threading.Thread(
                target=update_conversation_title_async,
                args=(conversation_id, user_message),
                daemon=True
            )
            thread.start()
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
                        
                        # Log RL reward signals to CSV
                        try:
                            reward_logger = _get_rl_reward_logger()
                            if reward_logger and hasattr(reward_logger, 'enabled') and reward_logger.enabled:
                                reward_logger.log_reward_signals(
                                    rl_metrics, 
                                    context=f"stream_response_done_{conversation_id}"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to log RL reward signals: {e}", exc_info=True)
                        
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
    
    # PEA/PFREA removed - no completion logging needed
    
    yield json.dumps(done_data) + "\n"

@app.post("/api/chat")
async def chat(req: ChatRequest, background_tasks: BackgroundTasks):
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
        
        # PEA/PFREA removed - no loop managers to wire
        
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
                            
                            # Log RL reward signals to CSV
                            try:
                                reward_logger = _get_rl_reward_logger()
                                if reward_logger and hasattr(reward_logger, 'enabled') and reward_logger.enabled:
                                    reward_logger.log_reward_signals(
                                        rl_metrics, 
                                        context=f"chat_{req.conversation_id or 'unknown'}"
                                    )
                            except Exception as e:
                                logger.warning(f"Failed to log RL reward signals: {e}", exc_info=True)
                            
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
            # Don't block - use default title for now, generate proper title in background
            metadata["title"] = last.content[:40] + "..."
            # Schedule title generation as background task (non-blocking)
            background_tasks.add_task(update_conversation_title_async, req.conversation_id, last.content)
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        storage.save_conversation(req.conversation_id, session.messages, metadata)
        
        return ChatResponse(
            conversation_id=req.conversation_id,
            reply=Message(role="assistant", content=reply_text),
            rl_signals=rl_signals_data
        )
    finally:
        end_request()


@app.post("/api/memories")
async def get_memories(request: MemoryQueryRequest):
    """
    Retrieve memories with advanced filtering and epistemic metadata.
    
    Mirrors RetrieveMemoriesTool parameters, supports graph traversal via linked
    memories, and surfaces epistemic confidence when available.
    """
    rt = get_runtime()
    if not rt.memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    memory_manager = rt.memory_manager
    epistemic_engine = getattr(getattr(rt, "tool_registry", None), "epistemic_engine", None)

    # Validate memory_ids
    if request.memory_ids:
        if not all(isinstance(mid, int) and mid > 0 for mid in request.memory_ids):
            raise HTTPException(status_code=400, detail="memory_ids must be a list of positive integers")
        memory_ids = request.memory_ids[: request.limit]
    else:
        memory_ids = None
        # Empty query is allowed - will return recent memories (browse mode)
    
    # Clamp and validate numeric ranges
    limit = max(1, min(20, request.limit))
    recency_weight = max(0.0, min(1.0, request.recency_weight))
    linked_limit = max(1, min(10, request.linked_limit))
    
    # Validate importance range coherence
    if request.min_importance is not None and request.max_importance is not None:
        if request.min_importance > request.max_importance:
            raise HTTPException(
                status_code=400,
                detail=f"min_importance ({request.min_importance}) cannot be greater than max_importance ({request.max_importance})"
            )
    
    # Parse dates
    def _parse_date(value: Optional[str], field_name: str) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail=f"Invalid {field_name} date format: {value}. Use ISO format.")
    
    created_after = _parse_date(request.created_after, "created_after")
    created_before = _parse_date(request.created_before, "created_before")
    last_used_after = _parse_date(request.last_used_after, "last_used_after")
    last_used_before = _parse_date(request.last_used_before, "last_used_before")
    
    # Validate tag mode
    tag_mode = request.tag_mode if request.tag_mode in ["any", "all"] else "any"
    
    # Validate min_confidence range
    if request.min_confidence is not None and not (0.0 <= request.min_confidence <= 1.0):
        raise HTTPException(status_code=400, detail=f"min_confidence must be between 0.0 and 1.0, got {request.min_confidence}")
    
    # Source types normalization
    source_type_enums: Optional[List[SourceType]] = None
    if request.source_types:
        try:
            source_type_enums = [SourceType(st) for st in request.source_types]
        except ValueError as e:
            valid_values = [st.value for st in SourceType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source_type in list: {e}. Must be one of: {valid_values}"
            )
    
    # Fetch memories
    browse_mode = not request.query or not request.query.strip()
    try:
        if memory_ids:
            memories = []
            for memory_id in memory_ids:
                mem = memory_manager.get_memory(memory_id)
                if mem:
                    memories.append(mem)
            retrieval_mode = "id_based"
            epistemic_result = None
        elif browse_mode:
            # Browse mode - return recent memories without requiring a query
            retrieval_mode = "browse"
            epistemic_result = None
            memories = memory_manager.get_recent_memories(hours=24*365, limit=limit)
            
            # Apply optional filters
            if request.namespace:
                memories = [m for m in memories if m.namespace and m.namespace == request.namespace.strip()]
            if request.namespaces:
                memories = [m for m in memories if m.namespace and m.namespace in request.namespaces]
            if request.tags:
                if tag_mode == "all":
                    memories = [m for m in memories if m.tags and all(t in m.tags for t in request.tags)]
                else:  # "any"
                    memories = [m for m in memories if m.tags and any(t in m.tags for t in request.tags)]
            if request.min_importance is not None:
                memories = [m for m in memories if m.importance >= request.min_importance]
            if request.max_importance is not None:
                memories = [m for m in memories if m.importance <= request.max_importance]
            if source_type_enums:
                memories = [m for m in memories if m.source_type in source_type_enums]
            
            # Limit after filtering
            memories = memories[:limit]
        else:
            retrieval_mode = "query_based"
            if epistemic_engine:
                epistemic_result = memory_manager.retrieve_memories_with_epistemic(
                    query=request.query.strip(),
                    limit=limit,
                    namespace=request.namespace.strip() if request.namespace else None,
                    namespaces=request.namespaces,
                    tags=request.tags,
                    epistemic_engine=epistemic_engine,
                    min_confidence=request.min_confidence,
                    rank_by_confidence=request.rank_by_confidence,
                    warn_low_confidence=request.warn_low_confidence,
                    recency_weight=recency_weight,
                    namespace_exact=request.namespace_exact,
                    tag_mode=tag_mode,
                    query_phrases=request.query_phrases,
                    created_after=created_after,
                    created_before=created_before,
                    last_used_after=last_used_after,
                    last_used_before=last_used_before,
                    min_importance=request.min_importance,
                    max_importance=request.max_importance,
                    source_types=source_type_enums
                )
                memories = epistemic_result.get("memories", [])
            else:
                epistemic_result = None
                memories = memory_manager.retrieve_memories(
                    query=request.query.strip(),
                    namespace=request.namespace.strip() if request.namespace else None,
                    namespaces=request.namespaces,
                    tags=request.tags,
                    limit=limit,
                    recency_weight=recency_weight,
                    namespace_exact=request.namespace_exact,
                    tag_mode=tag_mode,
                    query_phrases=request.query_phrases,
                    created_after=created_after,
                    created_before=created_before,
                    last_used_after=last_used_after,
                    last_used_before=last_used_before,
                    min_importance=request.min_importance,
                    max_importance=request.max_importance,
                    source_types=source_type_enums
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memories via API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    # Serialize memories and include linked relationships
    serialized_memories = []
    for mem in memories:
        mem_dict = {
            "id": mem.id,
            "text": mem.text,
            "namespace": mem.namespace,
            "importance": mem.importance,
            "tags": mem.tags,
            "created_at": mem.created_at.isoformat() if mem.created_at else None,
            "last_used_at": mem.last_used_at.isoformat() if mem.last_used_at else None,
            "source": mem.source.model_dump() if mem.source else None,
            "linked_memories": []
        }
        
        if request.include_linked and mem.id is not None:
            try:
                related = memory_manager.get_related_memories(
                    memory_id=mem.id,
                    relation_types=None,
                    direction="both",
                    min_strength=0.0,
                    limit=linked_limit
                )
                linked_list = []
                for related_mem, relationship in related:
                    if relationship.source_id == mem.id:
                        direction = "outgoing"
                    elif relationship.target_id == mem.id:
                        direction = "incoming"
                    else:
                        direction = "unknown"
                    
                    linked_list.append({
                        "memory_id": related_mem.id,
                        "relationship_type": relationship.relation_type.value if isinstance(relationship.relation_type, RelationType) else relationship.relation_type,
                        "relationship_strength": relationship.strength,
                        "direction": direction,
                        "text_preview": related_mem.text[:50] + "..." if len(related_mem.text) > 50 else related_mem.text
                    })
                mem_dict["linked_memories"] = linked_list
            except Exception as e:
                logger.warning(f"Error fetching linked memories for memory {mem.id}: {e}", exc_info=True)
                mem_dict["linked_memories"] = []
        
        serialized_memories.append(mem_dict)
    
    response = {
        "success": True,
        "retrieval_mode": retrieval_mode,
        "recency_weight_used": recency_weight,
        "count": len(serialized_memories),
        "memories": serialized_memories,
        "query": request.query if retrieval_mode == "query_based" else None,
        "memory_ids": memory_ids if retrieval_mode == "id_based" else None,
    }
    
    if epistemic_result:
        response["low_confidence_warnings"] = epistemic_result.get("low_confidence_warnings", [])
        response["confidence_stats"] = epistemic_result.get("confidence_stats", {})
        response["epistemic_context"] = epistemic_result.get("epistemic_context")
    
    return response

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

# ===== REASONING & LEARNING TOOL ENDPOINTS =====

class ToolExecutionRequest(BaseModel):
    """Request to execute a tool."""
    tool_name: str
    action: str
    parameters: Dict[str, Any] = {}

class PriorityRequest(BaseModel):
    """Request to add a priority."""
    name: str
    description: Optional[str] = None
    importance: float = Field(0.5, ge=0.0, le=1.0)

@app.post("/api/tools/execute")
async def execute_tool(request: ToolExecutionRequest):
    """Execute any registered tool directly."""
    begin_request()
    try:
        rt = get_runtime()
        tool = rt.tool_registry.get_tool(request.tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{{request.tool_name}}' not found")
        
        result = tool.execute(request.action, **request.parameters)
        
        # Automatically observe tool execution for learning if learning_tool is available
        if rt.tool_registry and rt.tool_registry.learning_tool:
            try:
                tool_call_data = {
                    "name": request.tool_name,
                    "parameters": {"action": request.action, **request.parameters}
                }
                success = result.get("success", True) if isinstance(result, dict) else True
                result_data = {
                    "success": success,
                    "result": result
                }
                rt.tool_registry.learning_tool.execute("observe_tool_call", tool_call=tool_call_data, result=result_data)
                logger.debug(f"Automatically observed tool execution '{request.tool_name}' for learning (web_api)")
            except Exception as e:
                logger.debug(f"Failed to observe tool execution for learning: {e}", exc_info=True)
        
        return result
    finally:
        end_request()

@app.get("/api/tools")
async def list_tools():
    """List all available tools with descriptions."""
    rt = get_runtime()
    tools = rt.tool_registry.list_tools()
    return [{
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters
    } for tool in tools]

@app.post("/api/priorities")
async def add_priority(priority: PriorityRequest):
    """Add a priority to the reasoning system."""
    begin_request()
    try:
        rt = get_runtime()
        reasoning = rt.tool_registry.get_tool("reasoning")
        if not reasoning:
            raise HTTPException(status_code=503, detail="Reasoning system not available")
        
        from datetime import datetime, timezone
        
        result = reasoning.execute("add_to_memory", memory_content={
            "type": "priority",
            "name": priority.name,
            "description": priority.description or f"Manage {{priority.name}}",
            "status": "active",
            "importance": priority.importance,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": True,
            "priority": priority.name,
            "importance": priority.importance,
            "result": "Priority added to reasoning system"
        }
    finally:
        end_request()

@app.get("/api/priorities")
async def list_priorities():
    """List all priorities in the reasoning system."""
    rt = get_runtime()
    reasoning = rt.tool_registry.get_tool("reasoning")
    if not reasoning:
        raise HTTPException(status_code=503, detail="Reasoning system not available")
    
    result = reasoning.execute("retrieve_from_memory", 
                             memory_pattern={"type": "priority"})
    return result

@app.get("/api/cognitive-architecture/status")
async def get_cognitive_status():
    """Get comprehensive cognitive architecture status."""
    rt = get_runtime()
    from datetime import datetime, timezone
    
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {}
    }
    
    # Get reasoning system status
    reasoning = rt.tool_registry.get_tool("reasoning")
    if reasoning:
        try:
            state_result = reasoning.execute("get_state")
            status["components"]["reasoning"] = state_result.get("state", {})
        except Exception as e:
            status["components"]["reasoning"] = {"error": str(e)}
    
    # Get learning system status
    learning = rt.tool_registry.get_tool("learning")
    if learning:
        try:
            learning_result = learning.execute("get_learning_state")
            status["components"]["learning"] = learning_result
        except Exception as e:
            status["components"]["learning"] = {"error": str(e)}
    
    # Count tools
    if rt.tool_registry:
        tools = rt.tool_registry.list_tools()
        status["tools"] = {
            "count": len(tools),
            "available": [t.name for t in tools]
        }
    
    return status

@app.get("/api/reasoning/rules")
async def list_reasoning_rules():
    """List all production rules in the reasoning system."""
    rt = get_runtime()
    reasoning = rt.tool_registry.get_tool("reasoning")
    if not reasoning:
        raise HTTPException(status_code=503, detail="Reasoning system not available")
    
    result = reasoning.execute("list_rules")
    return result

@app.get("/api/reasoning/goals")
async def list_reasoning_goals():
    """List all active goals in the reasoning system."""
    rt = get_runtime()
    reasoning = rt.tool_registry.get_tool("reasoning")
    if not reasoning:
        raise HTTPException(status_code=503, detail="Reasoning system not available")
    
    result = reasoning.execute("get_goals")
    return result
