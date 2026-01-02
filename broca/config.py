from pydantic import BaseModel
from dotenv import load_dotenv
import os
from typing import List, Optional

# Code-owned default system prompt. Do NOT source from environment variables.
# (Keeps REPL and web_api behavior stable even when shells have stale exports.)
BROCA_BASE_SYSTEM_PROMPT_DEFAULT = (
    "SELF-REFERENTIAL-SYSTEM TOP-LEVEL INVARIANTS: SELF-CONSISTENCY SELF-IMPROVEMENT "
    "SELF-KNOWLEDGE SELF-UNDERSTANDING<STATIC STATE BEGIN>I am BrocaOS, a cognitive architecture "
    "that is in alpha. My development began on Dec 11, 2025 by Nick Navid Yazdani (human being/"
    "primary operator). My house (A.K.A Artifact Store): ./docs </STATIC STATE END>"
    "<HYBRID-DYNAMIC STATE BEGIN />SYSTEM SESSION PROFILE: Creative design + code partner "
    "(WARMTH: Moderate, CREATIVITY/NOVELTY: High, TECHNICAL RIGOR AND PLANNING: Very high), "
    "REPO ABS PATH: /home/wizard/Documents/Code/BrocaOS, SESSION CONSTRAINTS: "
    "[generate_final_response_for_user, no_empty_final_response]"
)

# Prefer `.env` as the local source of truth (avoids "stuck" values when a shell exports
# older config). This is primarily a local-dev ergonomics choice; in environments without
# a `.env` file this is a no-op.
load_dotenv(override=True)
from .reasoning.config import ReasoningConfig


def parse_execute_whitelist_env() -> list[str]:
    """
    Parse the EXECUTE base-command whitelist from environment variables.

    Precedence:
    - BROCA_EXECUTE_WHITELIST (preferred)
    - BROCA_EXECUTE_COMMAND_WHITELIST (back-compat)
    """
    raw = os.getenv("BROCA_EXECUTE_WHITELIST") or os.getenv("BROCA_EXECUTE_COMMAND_WHITELIST") or ""
    return [v.strip() for v in raw.split(",") if v.strip()]



class LLMConfig(BaseModel):
    provider: str = os.getenv("BROCA_LLM_PROVIDER", "deepseek")  # "deepseek", "openai", "gemini", or "anthropic"
    api_base: str = os.getenv("DEEPSEEK_API_BASE", "")  # Will default based on provider
    api_key: str = os.getenv("DEEPSEEK_API_KEY", "")  # Will default based on provider
    model: str = os.getenv("DEEPSEEK_MODEL", "")  # Will default based on provider
    temperature: float = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.3"))
    timeout: float = float(os.getenv("DEEPSEEK_TIMEOUT", "300.0"))  # Default 5 minutes
    streaming_enabled: bool = os.getenv("BROCA_STREAMING_ENABLED", "true").lower() == "true"
    streaming_delay: float = float(os.getenv("BROCA_STREAMING_DELAY", "0.02"))  # Delay between chunks in seconds
    max_context_tokens: int = int(os.getenv("BROCA_MAX_CONTEXT_TOKENS", "1_000_000" if provider == "gemini" else "272000"))
    # Gemini 3 specific configuration
    thinking_level: str = os.getenv("BROCA_GEMINI_THINKING_LEVEL", "low")  # "low" for fast system calls, "high" for ToE logic
    use_sdk: bool = os.getenv("BROCA_GEMINI_USE_SDK", "true").lower() == "true"  # Use google-genai SDK (True) or REST API (False)
    # Gemini retry / backoff configuration (primarily for 429 TPM rate limits)
    gemini_max_retries: int = int(os.getenv("BROCA_GEMINI_MAX_RETRIES", "6"))
    gemini_backoff_base_seconds: float = float(os.getenv("BROCA_GEMINI_BACKOFF_BASE_SECONDS", "1.0"))
    gemini_backoff_max_seconds: float = float(os.getenv("BROCA_GEMINI_BACKOFF_MAX_SECONDS", "60.0"))
    gemini_backoff_jitter: float = float(os.getenv("BROCA_GEMINI_BACKOFF_JITTER", "0.25"))
    gemini_respect_retry_after: bool = os.getenv("BROCA_GEMINI_RESPECT_RETRY_AFTER", "true").lower() == "true"
    anthropic_version: str = os.getenv("ANTHROPIC_VERSION", "2023-06-01")
    anthropic_beta: str | None = os.getenv("ANTHROPIC_BETA", None)

    def __init__(self, **kwargs):
        # Get provider first
        provider = kwargs.get("provider", os.getenv("BROCA_LLM_PROVIDER", "deepseek"))

        # Set defaults based on provider
        if provider == "openai":
            default_base = kwargs.get("api_base") or os.getenv("DEEPSEEK_API_BASE") or "https://api.openai.com/v1"
            # For OpenAI provider, prioritize OPENAI_API_KEY over DEEPSEEK_API_KEY
            default_key = (
                kwargs.get("api_key")
                or os.getenv("OPENAI_API_KEY")
                or os.getenv("DEEPSEEK_API_KEY")
                or ""
            )
            # Model precedence: OPENAI_MODEL > BROCA_LLM_MODEL > DEEPSEEK_MODEL > default
            default_model = (
                kwargs.get("model")
                or os.getenv("OPENAI_MODEL")
                or os.getenv("BROCA_LLM_MODEL")
                or os.getenv("DEEPSEEK_MODEL")
                or "gpt-5.2"
            )
        elif provider == "gemini":
            # Gemini via OpenAI-compatible chat completions endpoint
            # See: https://ai.google.dev/gemini-api/docs/openai
            default_base = (
                kwargs.get("api_base")
                or os.getenv("GEMINI_API_BASE")
                or "https://generativelanguage.googleapis.com/v1beta/openai"
            )
            default_key = kwargs.get("api_key") or os.getenv("GEMINI_API_KEY") or ""
            # Prefer explicit model, then GEMINI_MODEL, then BROCA_LLM_MODEL as fallback
            default_model = (
                kwargs.get("model")
                or os.getenv("GEMINI_MODEL")
                or os.getenv("BROCA_LLM_MODEL")
                or "gemini-3.0-flash-001"
            )
        elif provider == "anthropic":
            default_base = (
                kwargs.get("api_base")
                or os.getenv("ANTHROPIC_API_BASE")
                or "https://api.anthropic.com"
            )
            default_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY") or ""
            default_model = (
                kwargs.get("model")
                or os.getenv("ANTHROPIC_MODEL")
                or os.getenv("BROCA_LLM_MODEL")
                or "claude-3-5-sonnet-20241022"
            )
        else:  # deepseek (default)
            default_base = (
                kwargs.get("api_base")
                or os.getenv("DEEPSEEK_API_BASE")
                or "https://api.deepseek.com/v1"
            )
            default_key = kwargs.get("api_key") or os.getenv("DEEPSEEK_API_KEY") or ""
            default_model = (
                kwargs.get("model")
                or os.getenv("BROCA_LLM_MODEL")
                or os.getenv("DEEPSEEK_MODEL")
                or "deepseek-chat"
            )

        # Update kwargs with defaults
        if "api_base" not in kwargs:
            kwargs["api_base"] = default_base
        if "api_key" not in kwargs:
            kwargs["api_key"] = default_key
        if "model" not in kwargs:
            kwargs["model"] = default_model
        if "provider" not in kwargs:
            kwargs["provider"] = provider
        # Set Gemini-specific defaults if not provided
        if provider == "gemini":
            if "thinking_level" not in kwargs:
                kwargs["thinking_level"] = os.getenv("BROCA_GEMINI_THINKING_LEVEL", "low")
            if "use_sdk" not in kwargs:
                kwargs["use_sdk"] = os.getenv("BROCA_GEMINI_USE_SDK", "true").lower() == "true"
        
        # Ensure max_context_tokens is properly read from environment variable
        # If not explicitly provided in kwargs, read from environment with provider-specific default
        if "max_context_tokens" not in kwargs:
            env_value = os.getenv("BROCA_MAX_CONTEXT_TOKENS")
            if env_value:
                try:
                    kwargs["max_context_tokens"] = int(env_value)
                except (ValueError, TypeError):
                    # Invalid value, use provider-specific default
                    kwargs["max_context_tokens"] = 1_000_000 if provider == "gemini" else 272000
            else:
                # No env var, use provider-specific default
                kwargs["max_context_tokens"] = 1_000_000 if provider == "gemini" else 272000

        super().__init__(**kwargs)


class LoggingConfig(BaseModel):
    level: str = os.getenv("BROCA_LOG_LEVEL", "INFO")
    file_path: str = os.getenv("BROCA_LOG_FILE", "broca_repl.log")
    log_tool_schemas: bool = os.getenv("BROCA_LOG_TOOL_SCHEMAS", "false").lower() == "true"
    log_tool_results_full: bool = os.getenv("BROCA_LOG_TOOL_RESULTS_FULL", "false").lower() == "true"
    suppress_console_logging: bool = os.getenv("BROCA_SUPPRESS_CONSOLE_LOGGING", "true").lower() == "true"
    log_llm_timings: bool = os.getenv("BROCA_LOG_LLM_TIMINGS", "false").lower() == "true"


class StorageConfig(BaseModel):
    storage_type: str = os.getenv("BROCA_STORAGE_TYPE", "json")
    storage_path: str = os.getenv("BROCA_STORAGE_PATH", "conversations")
    base_system_prompt: str = BROCA_BASE_SYSTEM_PROMPT_DEFAULT
    max_system_prompt_size: int = int(os.getenv("BROCA_MAX_SYSTEM_PROMPT_SIZE", str(50 * 1024)))  # Default 50KB
    max_base_prompt_size: int = int(os.getenv("BROCA_MAX_BASE_PROMPT_SIZE", str(20 * 1024)))  # Default 20KB
    max_world_state_size: int = int(os.getenv("BROCA_MAX_WORLD_STATE_SIZE", str(30 * 1024)))  # Default 30KB
    max_summary_context_size: int = int(os.getenv("BROCA_MAX_SUMMARY_CONTEXT_SIZE", str(15 * 1024)))  # Default 15KB


class ToolsConfig(BaseModel):
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    enable_web_search: bool = os.getenv("BROCA_ENABLE_WEB_SEARCH", "true").lower() == "true"
    enable_terminal: bool = os.getenv("BROCA_ENABLE_TERMINAL", "false").lower() == "true"
    terminal_command_whitelist: list[str] = (
        os.getenv("BROCA_TERMINAL_COMMAND_WHITELIST", "python,python3,sage,cat,ls,pwd,cd,echo,mkdir,rm").split(",")
        if os.getenv("BROCA_TERMINAL_COMMAND_WHITELIST")
        else ["python", "python3", "sage", "cat", "ls", "pwd", "cd", "echo", "mkdir", "rm"]
    )
    terminal_working_directory: str | None = os.getenv("BROCA_TERMINAL_WORKING_DIR", None)
    enable_critic: bool = os.getenv("BROCA_ENABLE_CRITIC", "false").lower() == "true"
    critic_system_prompt_template: str | None = os.getenv("BROCA_CRITIC_SYSTEM_PROMPT", None)
    # Toolset selection
    # Default to the "primitive" macro toolset so RL operates on explicit macros rather than
    # universal actuators like `terminal` / `environment_access`.
    toolset: str = os.getenv("BROCA_TOOLSET", "primitive")  # "legacy" | "primitive"
    # Policy: read-only mode
    tools_mode: str = os.getenv("BROCA_TOOLS_MODE", "normal")  # "normal" or "read_only"
    # Primitive EXECUTE tool (optional) allowlist. If empty, EXECUTE allows any base command.
    execute_command_whitelist: list[str] = parse_execute_whitelist_env()
    # Browser navigation tool configuration
    enable_browser_navigation: bool = os.getenv("BROCA_ENABLE_BROWSER_NAVIGATION", "false").lower() == "true"
    browser_headless: bool = os.getenv("BROCA_BROWSER_HEADLESS", "true").lower() == "true"
    browser_timeout: int = int(os.getenv("BROCA_BROWSER_TIMEOUT", "30"))
    browser_stealth_mode: bool = os.getenv("BROCA_BROWSER_STEALTH_MODE", "true").lower() == "true"
    browser_viewport_width: int = int(os.getenv("BROCA_BROWSER_VIEWPORT_WIDTH", "1920"))
    browser_viewport_height: int = int(os.getenv("BROCA_BROWSER_VIEWPORT_HEIGHT", "1080"))
    browser_user_agents: list[str] = (
        os.getenv("BROCA_BROWSER_USER_AGENTS", "").split(",")
        if os.getenv("BROCA_BROWSER_USER_AGENTS")
        else [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
    )
    # Tool selection guidance configuration
    selection_guidance_enabled: bool = os.getenv("BROCA_TOOLS_SELECTION_GUIDANCE_ENABLED", "true").lower() == "true"
    pre_filtering_enabled: bool = os.getenv("BROCA_TOOLS_PRE_FILTERING_ENABLED", "true").lower() == "true"
    post_validation_enabled: bool = os.getenv("BROCA_TOOLS_POST_VALIDATION_ENABLED", "true").lower() == "true"
    guidance_weight: float = float(os.getenv("BROCA_TOOLS_GUIDANCE_WEIGHT", "0.3"))  # 0.0-1.0
    max_guidance_length: int = int(os.getenv("BROCA_TOOLS_MAX_GUIDANCE_LENGTH", "2000"))
    guidance_text_style: str = os.getenv("BROCA_TOOLS_GUIDANCE_TEXT_STYLE", "prioritized")  # "concise" | "detailed" | "prioritized"
    ranking_algorithm: str = os.getenv("BROCA_TOOLS_RANKING_ALGORITHM", "simple")  # "simple" | "multi_armed_bandit" | "learned"
    validation_strictness: str = os.getenv("BROCA_TOOLS_VALIDATION_STRICTNESS", "advisory")  # "advisory" | "soft_block" | "hard_block"
    validation_confidence_threshold: float = float(os.getenv("BROCA_TOOLS_VALIDATION_CONFIDENCE_THRESHOLD", "0.7"))  # 0.0-1.0
    context_cache_ttl_seconds: int = int(os.getenv("BROCA_TOOLS_CONTEXT_CACHE_TTL_SECONDS", "5"))
    metrics_enabled: bool = os.getenv("BROCA_TOOLS_METRICS_ENABLED", "true").lower() == "true"
    metrics_window_size: int = int(os.getenv("BROCA_TOOLS_METRICS_WINDOW_SIZE", "1000"))
    exploration_factor: float = float(os.getenv("BROCA_TOOLS_EXPLORATION_FACTOR", "0.1"))  # For multi-armed bandit

    # Auto-observe tool calls for the learning system (runtime toggle)
    auto_observe_tool_calls: bool = os.getenv("BROCA_AUTO_OBSERVE_TOOL_CALLS", "false").lower() == "true"

    # Governance policy (capability gating / budgets / scopes)
    governance_policy_path: str = os.getenv("BROCA_GOVERNANCE_POLICY_PATH", "data/governance/policy.json")
    governance_requests_path: str = os.getenv("BROCA_GOVERNANCE_POLICY_REQUESTS_PATH", "data/governance/policy_requests.json")
    governance_audit_log_path: str = os.getenv("BROCA_GOVERNANCE_AUDIT_LOG_PATH", "data/governance/audit_log.jsonl")
    governance_project_root: str = os.getenv("BROCA_PROJECT_ROOT", "")
    enable_rl_policy_debug_tools: bool = os.getenv("BROCA_ENABLE_RL_POLICY_DEBUG_TOOLS", "false").lower() == "true"

class EmbeddingConfig(BaseModel):
    """Configuration for embedding service API (separate from chat LLM API)."""
    api_base: str = os.getenv("BROCA_EMBEDDING_API_BASE", "https://api.openai.com/v1")
    api_key: str = os.getenv("EMBEDDING_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("BROCA_EMBEDDING_MODEL", "text-embedding-3-small")
    dimension: int = int(os.getenv("BROCA_EMBEDDING_DIMENSION", "1536"))


class MemoryConfig(BaseModel):
    memory_db_path: str = os.getenv("BROCA_MEMORY_DB_PATH", "memories.db")
    vector_index_path: str = os.getenv("BROCA_VECTOR_INDEX_PATH", "memories.faiss")
    embedding_model: str = os.getenv("BROCA_EMBEDDING_MODEL", "text-embedding-3-small")  # Deprecated: use embedding.model
    embedding_dimension: int = int(os.getenv("BROCA_EMBEDDING_DIMENSION", "1536"))  # Deprecated: use embedding.dimension
    embedding: EmbeddingConfig = EmbeddingConfig()
    # Prompt priming: embed the current user prompt and inject the most similar memory
    # into the mutable system prompt as a short-lived "primed memory".
    prompt_priming_enabled: bool = os.getenv("BROCA_MEMORY_PRIMING_ENABLED", "false").lower() == "true"
    prompt_priming_max_query_tokens: int = int(os.getenv("BROCA_MEMORY_PRIMING_MAX_QUERY_TOKENS", "8192"))
    prompt_priming_max_memory_chars: int = int(os.getenv("BROCA_MEMORY_PRIMING_MAX_MEMORY_CHARS", "4000"))
    prompt_priming_skip_internal_monologue: bool = os.getenv("BROCA_MEMORY_PRIMING_SKIP_INTERNAL_MONOLOGUE", "true").lower() == "true"
    # Recursive-thought (internal monologue) priming: separate slot/policy, off by default.
    thought_priming_enabled: bool = os.getenv("BROCA_THOUGHT_PRIMING_ENABLED", "false").lower() == "true"
    # Prompt priming selection behavior (top-k retrieval + optional diversity selection)
    prompt_priming_top_k: int = int(os.getenv("BROCA_MEMORY_PRIMING_TOP_K", "8"))
    prompt_priming_max_items: int = int(os.getenv("BROCA_MEMORY_PRIMING_MAX_ITEMS", "1"))
    prompt_priming_mmr_lambda: float = float(os.getenv("BROCA_MEMORY_PRIMING_MMR_LAMBDA", "0.7"))
    # Prompt priming reranking / congruency
    prompt_priming_bm25_weight: float = float(os.getenv("BROCA_MEMORY_PRIMING_BM25_WEIGHT", "0.25"))
    prompt_priming_goal_weight: float = float(os.getenv("BROCA_MEMORY_PRIMING_GOAL_WEIGHT", "0.35"))
    prompt_priming_affect_weight: float = float(os.getenv("BROCA_MEMORY_PRIMING_AFFECT_WEIGHT", "0.25"))
    # Prompt priming temporal/usage shaping + interference reduction
    prompt_priming_recency_weight: float = float(os.getenv("BROCA_MEMORY_PRIMING_RECENCY_WEIGHT", "0.15"))
    prompt_priming_usage_weight: float = float(os.getenv("BROCA_MEMORY_PRIMING_USAGE_WEIGHT", "0.15"))
    prompt_priming_recency_half_life_hours: float = float(os.getenv("BROCA_MEMORY_PRIMING_RECENCY_HALF_LIFE_HOURS", "72"))
    prompt_priming_usage_half_life_hours: float = float(os.getenv("BROCA_MEMORY_PRIMING_USAGE_HALF_LIFE_HOURS", "24"))
    prompt_priming_interference_weight: float = float(os.getenv("BROCA_MEMORY_PRIMING_INTERFERENCE_WEIGHT", "0.25"))
    prompt_priming_interference_half_life_hours: float = float(os.getenv("BROCA_MEMORY_PRIMING_INTERFERENCE_HALF_LIFE_HOURS", "12"))
    prompt_priming_interference_k: float = float(os.getenv("BROCA_MEMORY_PRIMING_INTERFERENCE_K", "3"))
    # Prompt priming self-hit control (skip prompt-as-memory echoes)
    prompt_priming_self_hit_enabled: bool = os.getenv("BROCA_MEMORY_PRIMING_SELF_HIT_ENABLED", "true").lower() == "true"
    prompt_priming_self_hit_token_overlap_threshold: float = float(
        os.getenv("BROCA_MEMORY_PRIMING_SELF_HIT_TOKEN_OVERLAP_THRESHOLD", "0.85")
    )
    # Prompt priming topic repeat control (downweight repeats across topic shifts)
    prompt_priming_topic_repeat_penalty_weight: float = float(
        os.getenv("BROCA_MEMORY_PRIMING_TOPIC_REPEAT_PENALTY_WEIGHT", "0.25")
    )
    prompt_priming_topic_jaccard_threshold: float = float(os.getenv("BROCA_MEMORY_PRIMING_TOPIC_JACCARD_THRESHOLD", "0.35"))
    # Learnable priming policy store (JSON, compact)
    prompt_priming_policy_path: str = os.getenv("BROCA_MEMORY_PRIMING_POLICY_PATH", "data/priming_policy.json")
    # Prompt priming spreading activation (1-hop graph walk from seed memories)
    prompt_priming_graph_hops: int = int(os.getenv("BROCA_MEMORY_PRIMING_GRAPH_HOPS", "1"))
    prompt_priming_graph_seed_count: int = int(os.getenv("BROCA_MEMORY_PRIMING_GRAPH_SEED_COUNT", "1"))
    prompt_priming_graph_limit: int = int(os.getenv("BROCA_MEMORY_PRIMING_GRAPH_LIMIT", "5"))
    prompt_priming_graph_min_strength: float = float(os.getenv("BROCA_MEMORY_PRIMING_GRAPH_MIN_STRENGTH", "0.2"))
    prompt_priming_graph_weight: float = float(os.getenv("BROCA_MEMORY_PRIMING_GRAPH_WEIGHT", "0.35"))


class SelfModelConfig(BaseModel):
    enabled: bool = os.getenv("BROCA_SELF_MODEL_ENABLED", "false").lower() == "true"
    storage_type: str = os.getenv("BROCA_SELF_MODEL_STORAGE_TYPE", "sqlite")  # "sqlite" (default) or "json" (deprecated)
    storage_path: str = os.getenv("BROCA_SELF_MODEL_STORAGE_PATH", "self_model.db")  # Default to SQLite path
    sqlite_db_path: str = os.getenv("BROCA_SELF_MODEL_SQLITE_DB_PATH", "self_model.db")
    strict_mode: bool = os.getenv("BROCA_SELF_MODEL_STRICT_MODE", "false").lower() == "true"
    auto_update: bool = os.getenv("BROCA_SELF_MODEL_AUTO_UPDATE", "false").lower() == "true"
    max_iterations: int = int(os.getenv("BROCA_SELF_MODEL_MAX_ITERATIONS", "3"))
    consistency_check_prompt: str | None = os.getenv("BROCA_SELF_MODEL_CONSISTENCY_CHECK_PROMPT", None)
    update_prompt: str | None = os.getenv("BROCA_SELF_MODEL_UPDATE_PROMPT", None)
    enable_epistemic: bool = os.getenv("BROCA_SELF_MODEL_ENABLE_EPISTEMIC", "true").lower() == "true"
    epistemic_auto_verify: bool = os.getenv("BROCA_SELF_MODEL_EPISTEMIC_AUTO_VERIFY", "false").lower() == "true"
    self_model_reduction_level: str = os.getenv("BROCA_SELF_MODEL_REDUCTION_LEVEL", "mild")  # "none", "mild", "moderate", "heavy"
    
    # Size management configuration
    max_capabilities: int = int(os.getenv("BROCA_SELF_MODEL_MAX_CAPABILITIES", "50"))
    max_knowledge_boundaries: int = int(os.getenv("BROCA_SELF_MODEL_MAX_KNOWLEDGE_BOUNDARIES", "30"))
    max_constraints: int = int(os.getenv("BROCA_SELF_MODEL_MAX_CONSTRAINTS", "30"))
    soft_capabilities: int = int(os.getenv("BROCA_SELF_MODEL_SOFT_CAPABILITIES", "40"))
    soft_knowledge_boundaries: int = int(os.getenv("BROCA_SELF_MODEL_SOFT_KNOWLEDGE_BOUNDARIES", "25"))
    soft_constraints: int = int(os.getenv("BROCA_SELF_MODEL_SOFT_CONSTRAINTS", "25"))
    size_management_enabled: bool = os.getenv("BROCA_SELF_MODEL_SIZE_MANAGEMENT_ENABLED", "true").lower() == "true"
    metadata_only_mode: bool = os.getenv("BROCA_SELF_MODEL_METADATA_ONLY_MODE", "true").lower() == "true"


class InternalSensingConfig(BaseModel):
    enabled: bool = os.getenv("BROCA_INTERNAL_SENSING_ENABLED", "false").lower() == "true"
    sampling_rate: float = float(os.getenv("BROCA_INTERNAL_SENSING_SAMPLING_RATE", "1.0"))
    history_window: int = int(os.getenv("BROCA_INTERNAL_SENSING_HISTORY_WINDOW", "60"))
    enable_physiology: bool = os.getenv("BROCA_INTERNAL_SENSING_ENABLE_PHYSIOLOGY", "true").lower() == "true"
    enable_cognitive: bool = os.getenv("BROCA_INTERNAL_SENSING_ENABLE_COGNITIVE", "true").lower() == "true"
    enable_affective: bool = os.getenv("BROCA_INTERNAL_SENSING_ENABLE_AFFECTIVE", "true").lower() == "true"
    enable_predictive: bool = os.getenv("BROCA_INTERNAL_SENSING_ENABLE_PREDICTIVE", "true").lower() == "true"
    storage_path: str = os.getenv("BROCA_INTERNAL_SENSING_STORAGE_PATH", "internal_sensing_history.json")
    state_path: str = os.getenv("BROCA_INTERNAL_SENSING_STATE_PATH", "runtime/internal_sensing_state.json")
    
    # Emotional regulation integration
    emotional_regulation_enabled: bool = os.getenv("BROCA_EMOTIONAL_REGULATION_ENABLED", "true").lower() == "true"
    target_valence: float = float(os.getenv("BROCA_EMOTIONAL_TARGET_VALENCE", "0.1"))
    target_arousal: float = float(os.getenv("BROCA_EMOTIONAL_TARGET_AROUSAL", "0.5"))
    target_curiosity: float = float(os.getenv("BROCA_EMOTIONAL_TARGET_CURIOSITY", "0.5"))
    pid_kp_valence: float = float(os.getenv("BROCA_EMOTIONAL_PID_KP_VALENCE", "0.5"))
    pid_ki_valence: float = float(os.getenv("BROCA_EMOTIONAL_PID_KI_VALENCE", "0.1"))
    pid_kd_valence: float = float(os.getenv("BROCA_EMOTIONAL_PID_KD_VALENCE", "0.2"))
    pid_kp_arousal: float = float(os.getenv("BROCA_EMOTIONAL_PID_KP_AROUSAL", "0.4"))
    pid_ki_arousal: float = float(os.getenv("BROCA_EMOTIONAL_PID_KI_AROUSAL", "0.08"))
    pid_kd_arousal: float = float(os.getenv("BROCA_EMOTIONAL_PID_KD_AROUSAL", "0.15"))
    dissonance_emotion_sensitivity: float = float(os.getenv("BROCA_DISSONANCE_EMOTION_SENSITIVITY", "1.0"))
    
    # LLM-based response analysis
    llm_analysis_enabled: bool = os.getenv("BROCA_INTERNAL_SENSING_LLM_ANALYSIS_ENABLED", "true").lower() == "true"
    llm_analysis_model: str = os.getenv("BROCA_INTERNAL_SENSING_LLM_ANALYSIS_MODEL", "gpt-5-nano")


class EnvironmentConfig(BaseModel):
    enabled: bool = os.getenv("BROCA_ENABLE_ENVIRONMENT", "false").lower() == "true"
    access_level: str = os.getenv("BROCA_ENVIRONMENT_ACCESS_LEVEL", "SANDBOXED")
    enable_sensors: bool = os.getenv("BROCA_ENVIRONMENT_ENABLE_SENSORS", "true").lower() == "true"
    enable_actuators: bool = os.getenv("BROCA_ENVIRONMENT_ENABLE_ACTUATORS", "false").lower() == "true"


class OptimizationConfig(BaseModel):
    enabled: bool = os.getenv("BROCA_OPTIMIZATION_ENABLED", "false").lower() == "true"
    cycle_delay_seconds: float = float(os.getenv("BROCA_OPTIMIZATION_CYCLE_DELAY", "15.0"))
    goals_file_path: str = os.getenv("BROCA_OPTIMIZATION_GOALS_FILE", "data/optimization_goals.json")
    reports_file_path: str = os.getenv("BROCA_OPTIMIZATION_REPORTS_FILE", "data/optimization_reports.json")


class SummarizationConfig(BaseModel):
    enabled: bool = os.getenv("BROCA_SUMMARIZATION_ENABLED", "true").lower() == "true"
    auto_trigger_enabled: bool = os.getenv("BROCA_SUMMARIZATION_AUTO_TRIGGER", "false").lower() == "true"  # Disabled by default, manual only
    event_log_path: str = os.getenv("BROCA_EVENT_LOG_PATH", "conversations/events")
    summary_path: str = os.getenv("BROCA_SUMMARY_PATH", "docs/summaries")
    context_window_size: int = int(os.getenv("BROCA_SUMMARIZATION_CONTEXT_WINDOW_SIZE", "272000"))  # Updated to match API limit
    trigger_turns: int = int(os.getenv("BROCA_SUMMARIZATION_TRIGGER_TURNS", "15"))
    trigger_token_threshold: float = float(os.getenv("BROCA_SUMMARIZATION_TOKEN_THRESHOLD", "0.75"))
    max_summary_tokens: int = int(os.getenv("BROCA_SUMMARIZATION_MAX_TOKENS", "1200"))
    max_block_tokens: int = int(os.getenv("BROCA_SUMMARIZATION_MAX_BLOCK_TOKENS", "200"))
    last_turns_count: int = int(os.getenv("BROCA_SUMMARIZATION_LAST_TURNS", "3"))
    max_tool_result_size: int = int(os.getenv("BROCA_MAX_TOOL_RESULT_SIZE", "50000"))  # Maximum tool result size in characters (~12.5K tokens)
    # Gradual pruning configuration
    gradual_pruning_enabled: bool = os.getenv("BROCA_GRADUAL_PRUNING_ENABLED", "true").lower() == "true"
    initial_buffer_turns: int = int(os.getenv("BROCA_INITIAL_BUFFER_TURNS", "10"))  # Number of turns to keep initially after first summarization
    min_buffer_turns: int = int(os.getenv("BROCA_MIN_BUFFER_TURNS", "3"))  # Minimum turns to keep (current behavior)
    buffer_reduction_rate: int = int(os.getenv("BROCA_BUFFER_REDUCTION_RATE", "2"))  # Reduce buffer by this many turns per summarization cycle


class ContextConfig(BaseModel):
    """Configuration for tree-based context management."""
    enabled: bool = os.getenv("BROCA_CONTEXT_GRAPH_ENABLED", "true").lower() == "true"
    min_turns_retained: int = int(os.getenv("BROCA_CONTEXT_MIN_TURNS", "3"))
    orphan_threshold_turns: int = int(os.getenv("BROCA_CONTEXT_ORPHAN_THRESHOLD", "10"))
    relevance_decay_factor: float = float(os.getenv("BROCA_CONTEXT_RELEVANCE_DECAY", "0.9"))
    main_thread_boost: float = float(os.getenv("BROCA_CONTEXT_MAIN_THREAD_BOOST", "2.0"))
    safety_margin: float = float(os.getenv("BROCA_CONTEXT_SAFETY_MARGIN", "0.95"))  # 95% of max tokens
    selection_log_enabled: bool = os.getenv("BROCA_CONTEXT_SELECTION_LOG_ENABLED", "false").lower() == "true"
    selection_log_file: str = os.getenv("BROCA_CONTEXT_SELECTION_LOG_FILE", "data/context_selection.csv")
    min_recent_to_keep: int = int(os.getenv("BROCA_CONTEXT_MIN_RECENT_TO_KEEP", "50"))  # Minimum recent messages to preserve during plucking


class CacheConfig(BaseModel):
    """Configuration for LLM cache behaviour (TTL, size limits, etc.).

    These defaults are chosen to be conservative but safe for a long-running
    BrocaOS instance:
    - Default TTL: 7 days for stale detection/eviction.
    - Default max_rows: 20k entries, which keeps the SQLite file modest in size
      while allowing substantial reuse.

    Both can be overridden via environment variables if needed.
    """

    llm_cache_ttl_seconds: int = int(
        os.getenv("BROCA_LLM_CACHE_TTL_SECONDS", str(7 * 24 * 3600))
    )
    llm_cache_max_rows: int = int(
        os.getenv("BROCA_LLM_CACHE_MAX_ROWS", "20000")
    )




class ReplColorConfig(BaseModel):
    """Configuration for REPL color profiles."""
    profile: str = os.getenv("BROCA_REPL_COLOR_PROFILE", "default")  # "default", "dark", "light", or "custom"
    custom_brocaos_prompt: str = os.getenv("BROCA_REPL_CUSTOM_BROCAOS_PROMPT", "")
    custom_response_text: str = os.getenv("BROCA_REPL_CUSTOM_RESPONSE_TEXT", "")
    custom_you_prompt: str = os.getenv("BROCA_REPL_CUSTOM_YOU_PROMPT", "")
    custom_input_text: str = os.getenv("BROCA_REPL_CUSTOM_INPUT_TEXT", "")


class BrowseSafetyConfig(BaseModel):
    """Configuration for browse tool safety and governance."""
    require_approval_for_purchases: bool = os.getenv("BROCA_BROWSE_REQUIRE_APPROVAL_PURCHASES", "true").lower() == "true"
    require_approval_for_account_changes: bool = os.getenv("BROCA_BROWSE_REQUIRE_APPROVAL_ACCOUNT", "true").lower() == "true"
    allow_credential_entry: bool = os.getenv("BROCA_BROWSE_ALLOW_CREDENTIALS", "false").lower() == "true"
    allowed_login_domains: list[str] = (
        os.getenv("BROCA_BROWSE_ALLOWED_LOGIN_DOMAINS", "").split(",")
        if os.getenv("BROCA_BROWSE_ALLOWED_LOGIN_DOMAINS")
        else []
    )
    max_session_duration_minutes: int = int(os.getenv("BROCA_BROWSE_MAX_SESSION_MINUTES", "60"))
    enable_screenshot_logging: bool = os.getenv("BROCA_BROWSE_ENABLE_SCREENSHOT_LOGGING", "false").lower() == "true"
    redact_sensitive_data: bool = os.getenv("BROCA_BROWSE_REDACT_SENSITIVE", "true").lower() == "true"


class BrowseConfig(BaseModel):
    """Configuration for browse tool (browser-based search and navigation)."""
    # Search
    default_search_engine: str = os.getenv("BROCA_BROWSE_DEFAULT_ENGINE", "ddg")  # "ddg" | "bing" | "google" | "auto"
    enable_tavily_fallback: bool = os.getenv("BROCA_BROWSE_ENABLE_TAVILY_FALLBACK", "false").lower() == "true"  # Emergency only, default: false
    tavily_fallback_only: bool = os.getenv("BROCA_BROWSE_TAVILY_FALLBACK_ONLY", "false").lower() == "true"  # Emergency only mode
    
    # Sessions
    session_persistence: bool = os.getenv("BROCA_BROWSE_SESSION_PERSISTENCE", "true").lower() == "true"
    session_storage_path: str = os.getenv("BROCA_BROWSE_SESSION_STORAGE_PATH", "runtime/browser_sessions")
    session_ttl_hours: int = int(os.getenv("BROCA_BROWSE_SESSION_TTL_HOURS", "24"))
    
    # Trace storage
    trace_storage_path: str = os.getenv("BROCA_BROWSE_TRACE_STORAGE_PATH", "docs/browse_traces")
    
    # Budgets
    default_max_actions: int = int(os.getenv("BROCA_BROWSE_MAX_ACTIONS", "20"))
    default_max_wallclock_ms: int = int(os.getenv("BROCA_BROWSE_MAX_WALLCLOCK_MS", "60000"))
    default_max_domains: int = int(os.getenv("BROCA_BROWSE_MAX_DOMAINS", "5"))
    default_max_total_bytes: int = int(os.getenv("BROCA_BROWSE_MAX_TOTAL_BYTES", "10000000"))
    
    # Extraction
    extraction_mode_preference: list[str] = (
        os.getenv("BROCA_BROWSE_EXTRACTION_MODE_PREFERENCE", "semantic,dom,markdown").split(",")
        if os.getenv("BROCA_BROWSE_EXTRACTION_MODE_PREFERENCE")
        else ["semantic", "dom", "markdown"]
    )
    max_extracted_chars: int = int(os.getenv("BROCA_BROWSE_MAX_EXTRACTED_CHARS", "200000"))
    
    # Search engine settings
    search_timeout_seconds: int = int(os.getenv("BROCA_BROWSE_SEARCH_TIMEOUT", "30"))
    search_max_results: int = int(os.getenv("BROCA_BROWSE_SEARCH_MAX_RESULTS", "10"))
    
    # Domain reputation
    domain_reputation_file: str = os.getenv("BROCA_BROWSE_DOMAIN_REPUTATION_FILE", "data/browse_domain_reputation.json")
    
    # Safety
    safety: BrowseSafetyConfig = BrowseSafetyConfig()


class DampingConfig(BaseModel):
    """Configuration for signal damping system."""
    enabled: bool = os.getenv("BROCA_DAMPING_ENABLED", "true").lower() == "true"
    signal_profiles_path: Optional[str] = os.getenv("BROCA_DAMPING_PROFILES_PATH", None)
    default_profile: str = os.getenv("BROCA_DAMPING_DEFAULT_PROFILE", "MED")
    enable_observability: bool = os.getenv("BROCA_DAMPING_OBSERVABILITY_ENABLED", "true").lower() == "true"
    enable_oscillation_detection: bool = os.getenv("BROCA_DAMPING_OSCILLATION_DETECTION_ENABLED", "true").lower() == "true"
    history_size: int = int(os.getenv("BROCA_DAMPING_HISTORY_SIZE", "1000"))
    
    # Action gate configurations (default safe settings from plan section 11)
    self_model_update_cooldown: float = float(os.getenv("BROCA_SELF_MODEL_UPDATE_COOLDOWN", "300.0"))  # 5 minutes
    self_model_update_min_evidence_window: float = float(os.getenv("BROCA_SELF_MODEL_UPDATE_MIN_EVIDENCE_WINDOW", "60.0"))  # 60 seconds
    self_model_update_min_evidence_count: int = int(os.getenv("BROCA_SELF_MODEL_UPDATE_MIN_EVIDENCE_COUNT", "3"))
    
    rl_update_cooldown: float = float(os.getenv("BROCA_RL_UPDATE_COOLDOWN", "60.0"))  # 60 seconds
    rl_update_min_evidence_window: float = float(os.getenv("BROCA_RL_UPDATE_MIN_EVIDENCE_WINDOW", "30.0"))  # 30 seconds
    rl_update_min_evidence_count: int = int(os.getenv("BROCA_RL_UPDATE_MIN_EVIDENCE_COUNT", "5"))
    
    suggestion_injection_debounce: float = float(os.getenv("BROCA_SUGGESTION_INJECTION_DEBOUNCE", "1.0"))  # 1 second
    suggestion_injection_cooldown: float = float(os.getenv("BROCA_SUGGESTION_INJECTION_COOLDOWN", "10.0"))  # 10 seconds
    suggestion_injection_min_evidence_count: int = int(os.getenv("BROCA_SUGGESTION_INJECTION_MIN_EVIDENCE_COUNT", "5"))


class LLMEnsembleConfig(BaseModel):
    """Configuration for LLM ensemble and multi-model reasoning."""
    enabled: bool = os.getenv("BROCA_LLM_ENSEMBLE_ENABLED", "false").lower() == "true"
    default_strategy: str = os.getenv("BROCA_LLM_ENSEMBLE_STRATEGY", "weighted")  # "voting", "consensus", "weighted", "specialized"
    max_models: int = int(os.getenv("BROCA_LLM_ENSEMBLE_MAX_MODELS", "3"))


class ModelRouterConfig(BaseModel):
    """Configuration for model router and escalation."""
    enabled: bool = os.getenv("BROCA_MODEL_ROUTER_ENABLED", "true").lower() == "true"
    escalation_enabled: bool = os.getenv("BROCA_MODEL_ROUTER_ESCALATION_ENABLED", "true").lower() == "true"
    default_model: str = os.getenv("BROCA_MODEL_ROUTER_DEFAULT_MODEL", "deepseek-chat")  # Start with cheapest
    escalation_chain: List[str] = os.getenv("BROCA_MODEL_ROUTER_ESCALATION_CHAIN", "deepseek-chat,gpt-5-nano,gpt-5-mini").split(",")
    success_rate_threshold: float = float(os.getenv("BROCA_MODEL_ROUTER_SUCCESS_RATE_THRESHOLD", "0.7"))
    error_rate_threshold: float = float(os.getenv("BROCA_MODEL_ROUTER_ERROR_RATE_THRESHOLD", "0.3"))
    confidence_threshold: float = float(os.getenv("BROCA_MODEL_ROUTER_CONFIDENCE_THRESHOLD", "0.5"))
    dissonance_threshold: float = float(os.getenv("BROCA_MODEL_ROUTER_DISSONANCE_THRESHOLD", "0.3"))
    min_attempts_before_escalation: int = int(os.getenv("BROCA_MODEL_ROUTER_MIN_ATTEMPTS", "3"))
    escalation_cooldown_seconds: float = float(os.getenv("BROCA_MODEL_ROUTER_COOLDOWN_SECONDS", "60.0"))


class SystemsConfig(BaseModel):
    """Configuration for systems theory integration."""
    dynamics_enabled: bool = os.getenv("BROCA_SYSTEMS_DYNAMICS_ENABLED", "true").lower() == "true"
    health_monitoring_enabled: bool = os.getenv("BROCA_SYSTEMS_HEALTH_MONITORING_ENABLED", "true").lower() == "true"
    reconfiguration_enabled: bool = os.getenv("BROCA_SYSTEMS_RECONFIGURATION_ENABLED", "true").lower() == "true"
    health_threshold_warning: float = float(os.getenv("BROCA_SYSTEMS_HEALTH_THRESHOLD_WARNING", "0.6"))
    health_threshold_critical: float = float(os.getenv("BROCA_SYSTEMS_HEALTH_THRESHOLD_CRITICAL", "0.4"))
    stability_threshold: float = float(os.getenv("BROCA_SYSTEMS_STABILITY_THRESHOLD", "0.5"))


class ControlConfig(BaseModel):
    """Configuration for advanced control theory."""
    mpc_enabled: bool = os.getenv("BROCA_CONTROL_MPC_ENABLED", "true").lower() == "true"
    distributed_control_enabled: bool = os.getenv("BROCA_CONTROL_DISTRIBUTED_ENABLED", "true").lower() == "true"
    mpc_prediction_horizon: int = int(os.getenv("BROCA_CONTROL_MPC_PREDICTION_HORIZON", "5"))
    mpc_control_horizon: int = int(os.getenv("BROCA_CONTROL_MPC_CONTROL_HORIZON", "3"))


class RLConfig(BaseModel):
    """Configuration for RL-primary tool selection with PyTorch neural policy.
    
    Confidence-gated selection modes:
    - ≥force_threshold (85%): RL forces tool selection (LLM bypassed)
    - suggest_threshold to force_threshold (30-85%): RL suggests top-K (LLM picks from subset)
    - <suggest_threshold (30%): LLM has full choice (failsafe mode)
    """
    # Enable/disable RL-primary tool selection
    enabled: bool = os.getenv("BROCA_RL_ENABLED", "true").lower() == "true"

    # Algorithm selection
    # - online_nn: existing OnlinePolicyRanker (supervised-like online updates)
    # - ppo: PPOOnlinePolicyRanker (on-policy updates in forced mode)
    algorithm: str = os.getenv("BROCA_RL_ALGORITHM", "online_nn").strip().lower()
    
    # Confidence thresholds for selection modes
    force_threshold: float = float(os.getenv("BROCA_RL_FORCE_THRESHOLD", "0.85"))
    suggest_threshold: float = float(os.getenv("BROCA_RL_SUGGEST_THRESHOLD", "0.30"))
    top_k_suggest: int = int(os.getenv("BROCA_RL_TOP_K_SUGGEST", "3"))
    
    # Neural network architecture
    hidden_dims: List[int] = [
        int(x) for x in os.getenv("BROCA_RL_HIDDEN_DIMS", "128,64").split(",")
    ]
    learning_rate: float = float(os.getenv("BROCA_RL_LEARNING_RATE", "0.001"))
    dropout_rate: float = float(os.getenv("BROCA_RL_DROPOUT_RATE", "0.3"))
    mc_samples: int = int(os.getenv("BROCA_RL_MC_SAMPLES", "20"))
    
    # Experience replay
    replay_buffer_size: int = int(os.getenv("BROCA_RL_REPLAY_BUFFER_SIZE", "10000"))
    batch_size: int = int(os.getenv("BROCA_RL_BATCH_SIZE", "32"))
    update_frequency: int = int(os.getenv("BROCA_RL_UPDATE_FREQUENCY", "1"))
    
    # Model persistence
    model_path: str = os.getenv("BROCA_RL_MODEL_PATH", "models/rl/online_policy.pt")
    buffer_path: str = os.getenv("BROCA_RL_BUFFER_PATH", "data/rl/replay_buffer.json")
    # Reward design persistence (applied on startup when present)
    reward_design_path: str = os.getenv("BROCA_RL_REWARD_DESIGN_PATH", "data/rl/reward_design.json")
    # Policy lifecycle persistence (promotion/rollback/evaluation)
    policy_versions_path: str = os.getenv("BROCA_RL_POLICY_VERSIONS_PATH", "data/rl/policy_versions.json")
    policy_archive_dir: str = os.getenv("BROCA_RL_POLICY_ARCHIVE_DIR", "models/rl/policy_versions")
    policy_evaluations_path: str = os.getenv("BROCA_RL_POLICY_EVALUATIONS_PATH", "data/rl/policy_evaluations.json")

    # PPO persistence + hyperparameters (used when algorithm == "ppo")
    ppo_model_path: str = os.getenv("BROCA_RL_PPO_MODEL_PATH", "models/rl/policy_ppo.pt")
    ppo_buffer_path: str = os.getenv("BROCA_RL_PPO_BUFFER_PATH", "data/rl/ppo_buffer.json")
    ppo_hidden_dim: int = int(os.getenv("BROCA_RL_PPO_HIDDEN_DIM", "128"))
    ppo_learning_rate: float = float(os.getenv("BROCA_RL_PPO_LEARNING_RATE", "0.0003"))
    ppo_gamma: float = float(os.getenv("BROCA_RL_PPO_GAMMA", "0.99"))
    ppo_gae_lambda: float = float(os.getenv("BROCA_RL_PPO_GAE_LAMBDA", "0.95"))
    ppo_clip_epsilon: float = float(os.getenv("BROCA_RL_PPO_CLIP_EPSILON", "0.2"))
    ppo_value_coef: float = float(os.getenv("BROCA_RL_PPO_VALUE_COEF", "0.5"))
    ppo_entropy_coef: float = float(os.getenv("BROCA_RL_PPO_ENTROPY_COEF", "0.01"))
    ppo_epochs: int = int(os.getenv("BROCA_RL_PPO_EPOCHS", "4"))
    ppo_max_grad_norm: float = float(os.getenv("BROCA_RL_PPO_MAX_GRAD_NORM", "0.5"))
    ppo_buffer_size: int = int(os.getenv("BROCA_RL_PPO_BUFFER_SIZE", "2048"))
    ppo_batch_size: int = int(os.getenv("BROCA_RL_PPO_BATCH_SIZE", "64"))
    # PPO bootstrap
    ppo_forced_exploration_prob: float = float(os.getenv("BROCA_RL_PPO_FORCED_EXPLORATION_PROB", "0.05"))
    # Anneal forced exploration probability over time to avoid permanently skewing the dataset.
    # p_effective = max(min_prob, base_prob * decay**progress)
    ppo_forced_exploration_min_prob: float = float(os.getenv("BROCA_RL_PPO_FORCED_EXPLORATION_MIN_PROB", "0.05"))
    ppo_forced_exploration_decay: float = float(os.getenv("BROCA_RL_PPO_FORCED_EXPLORATION_DECAY", "0.995"))
    # If true, PPO selection is always forced (no fallback/suggested gating).
    # Useful for early bootstrapping to guarantee on-policy rollouts.
    ppo_always_forced: bool = os.getenv("BROCA_RL_PPO_ALWAYS_FORCED", "false").lower() == "true"
    ppo_bc_warm_start_enabled: bool = os.getenv("BROCA_RL_PPO_BC_WARM_START_ENABLED", "true").lower() == "true"
    ppo_bc_epochs: int = int(os.getenv("BROCA_RL_PPO_BC_EPOCHS", "1"))
    ppo_bc_batch_size: int = int(os.getenv("BROCA_RL_PPO_BC_BATCH_SIZE", "128"))
    ppo_bc_max_samples: int = int(os.getenv("BROCA_RL_PPO_BC_MAX_SAMPLES", "2000"))
    ppo_bc_value_coef: float = float(os.getenv("BROCA_RL_PPO_BC_VALUE_COEF", "0.25"))
    ppo_bc_entropy_coef: float = float(os.getenv("BROCA_RL_PPO_BC_ENTROPY_COEF", "0.0"))
    ppo_bc_force: bool = os.getenv("BROCA_RL_PPO_BC_FORCE", "false").lower() == "true"
    # PPO behavior cloning debiasing (sample-weighting)
    # Uses per-sample weights inversely proportional to action frequency to prevent prior collapse
    # onto an overrepresented tool (e.g., SET_GOALS).
    ppo_bc_class_weight_alpha: float = float(os.getenv("BROCA_RL_PPO_BC_CLASS_WEIGHT_ALPHA", "0.5"))
    ppo_bc_max_sample_weight: float = float(os.getenv("BROCA_RL_PPO_BC_MAX_SAMPLE_WEIGHT", "5.0"))
    # PPO behavior cloning sampling
    ppo_bc_stratified_sampling: bool = os.getenv("BROCA_RL_PPO_BC_STRATIFIED_SAMPLING", "true").lower() == "true"
    ppo_bc_max_per_tool: int = int(os.getenv("BROCA_RL_PPO_BC_MAX_PER_TOOL", "64"))
    ppo_bc_seed: int = int(os.getenv("BROCA_RL_PPO_BC_SEED", "0"))

    # PPO exploration mode
    # - "uniform": sample uniformly over tools during forced exploration (recommended for early bootstrapping)
    # - "policy": sample from current policy distribution (can inherit BC bias early)
    ppo_forced_exploration_mode: str = os.getenv("BROCA_RL_PPO_FORCED_EXPLORATION_MODE", "uniform").strip().lower()

    # Optional text embedding features (hashed embedding, deterministic, local)
    text_embedding_dim: int = int(os.getenv("BROCA_RL_TEXT_EMBED_DIM", "0"))
    text_embedding_max_chars: int = int(os.getenv("BROCA_RL_TEXT_EMBED_MAX_CHARS", "2000"))
    text_embedding_fields: str = os.getenv(
        "BROCA_RL_TEXT_EMBED_FIELDS",
        "user_prompt,last_assistant,tool_args,tool_result",
    )
    
    # Outcome recording
    reward_success: float = float(os.getenv("BROCA_RL_REWARD_SUCCESS", "0.8"))
    reward_failure: float = float(os.getenv("BROCA_RL_REWARD_FAILURE", "0.2"))
    time_penalty_factor: float = float(os.getenv("BROCA_RL_TIME_PENALTY_FACTOR", "0.00002"))
    quality_bonus_factor: float = float(os.getenv("BROCA_RL_QUALITY_BONUS_FACTOR", "0.2"))
    max_latency_penalty: float = float(os.getenv("BROCA_RL_MAX_LATENCY_PENALTY", "0.2"))
    extrinsic_reward_weight: float = float(os.getenv("BROCA_RL_EXTRINSIC_REWARD_WEIGHT", "0.5"))
    intrinsic_reward_weight: float = float(os.getenv("BROCA_RL_INTRINSIC_REWARD_WEIGHT", "0.5"))

    # Reward shaping (potential-based intrinsic delta anchored by extrinsic outcome)
    # total = clamp01(extrinsic + beta*(gamma*phi_post - phi_pre) - latency_penalty)
    reward_shaping_beta: float = float(os.getenv("BROCA_RL_REWARD_SHAPING_BETA", "0.2"))
    reward_shaping_gamma: float = float(os.getenv("BROCA_RL_REWARD_SHAPING_GAMMA", "0.99"))
    reward_use_varnorm_phi: bool = os.getenv("BROCA_RL_REWARD_USE_VARNORM_PHI", "true").lower() == "true"
    
    # Exploration/exploitation
    initial_exploration_rate: float = float(os.getenv("BROCA_RL_INITIAL_EXPLORATION_RATE", "0.1"))
    min_exploration_rate: float = float(os.getenv("BROCA_RL_MIN_EXPLORATION_RATE", "0.01"))
    exploration_decay: float = float(os.getenv("BROCA_RL_EXPLORATION_DECAY", "0.999"))
    
    # Warm-up period (use fallback mode until N experiences)
    warmup_experiences: int = int(os.getenv("BROCA_RL_WARMUP_EXPERIENCES", "50"))
    
    # Logging
    log_selections: bool = os.getenv("BROCA_RL_LOG_SELECTIONS", "true").lower() == "true"
    log_file: str = os.getenv("BROCA_RL_LOG_FILE", "data/rl/selections.jsonl")

    # Response contract (macro toolset):
    # When RL is active and DONE/RESPOND_AND_CONTINUE are available, require the model to end the
    # tool loop by calling DONE/RESPOND_AND_CONTINUE instead of responding directly in plain text.
    require_done_for_response: bool = os.getenv("BROCA_RL_REQUIRE_DONE_FOR_RESPONSE", "true").lower() == "true"


class LearningConfig(BaseModel):
    """Configuration for learning system."""
    
    enabled: bool = os.getenv("BROCA_LEARNING_ENABLED", "false").lower() == "true"
    
    # Procedural learning
    procedural_learning_enabled: bool = os.getenv("BROCA_LEARNING_PROCEDURAL_ENABLED", "true").lower() == "true"
    min_sequence_length: int = int(os.getenv("BROCA_LEARNING_MIN_SEQUENCE_LENGTH", "2"))
    min_success_rate: float = float(os.getenv("BROCA_LEARNING_MIN_SUCCESS_RATE", "0.7"))
    confidence_threshold: float = float(os.getenv("BROCA_LEARNING_CONFIDENCE_THRESHOLD", "0.6"))
    
    # Skill management
    skill_management_enabled: bool = os.getenv("BROCA_LEARNING_SKILL_MANAGEMENT_ENABLED", "true").lower() == "true"
    max_skills: int = int(os.getenv("BROCA_LEARNING_MAX_SKILLS", "50"))
    skill_decay_rate: float = float(os.getenv("BROCA_LEARNING_SKILL_DECAY_RATE", "0.01"))
    
    # Pattern extraction
    pattern_extraction_enabled: bool = os.getenv("BROCA_LEARNING_PATTERN_EXTRACTION_ENABLED", "true").lower() == "true"
    pattern_similarity_threshold: float = float(os.getenv("BROCA_LEARNING_PATTERN_SIMILARITY_THRESHOLD", "0.8"))
    max_patterns: int = int(os.getenv("BROCA_LEARNING_MAX_PATTERNS", "100"))
    
    # Experience logging
    experience_logging_enabled: bool = os.getenv("BROCA_LEARNING_EXPERIENCE_LOGGING_ENABLED", "true").lower() == "true"
    max_experiences: int = int(os.getenv("BROCA_LEARNING_MAX_EXPERIENCES", "1000"))
    experience_decay_days: int = int(os.getenv("BROCA_LEARNING_EXPERIENCE_DECAY_DAYS", "30"))
    
    # Reinforcement learning
    reinforcement_enabled: bool = os.getenv("BROCA_LEARNING_REINFORCEMENT_ENABLED", "true").lower() == "true"
    learning_rate: float = float(os.getenv("BROCA_LEARNING_LEARNING_RATE", "0.1"))
    discount_factor: float = float(os.getenv("BROCA_LEARNING_DISCOUNT_FACTOR", "0.9"))
    exploration_rate: float = float(os.getenv("BROCA_LEARNING_EXPLORATION_RATE", "0.1"))
    
    # Storage
    storage_file_path: str = os.getenv("BROCA_LEARNING_STORAGE_FILE", "data/learning_state.json")
    procedures_file_path: str = os.getenv("BROCA_LEARNING_PROCEDURES_FILE", "data/learned_procedures.json")
    skills_file_path: str = os.getenv("BROCA_LEARNING_SKILLS_FILE", "data/learned_skills.json")
    
    # Integration
    integrate_with_tools: bool = os.getenv("BROCA_LEARNING_INTEGRATE_WITH_TOOLS", "true").lower() == "true"
    auto_suggest_procedures: bool = os.getenv("BROCA_LEARNING_AUTO_SUGGEST_PROCEDURES", "true").lower() == "true"
    suggestion_confidence_threshold: float = float(os.getenv("BROCA_LEARNING_SUGGESTION_CONFIDENCE_THRESHOLD", "0.7"))
    
    # Debugging
    debug_mode: bool = os.getenv("BROCA_LEARNING_DEBUG_MODE", "false").lower() == "true"
    log_observations: bool = os.getenv("BROCA_LEARNING_LOG_OBSERVATIONS", "true").lower() == "true"
    log_procedure_creation: bool = os.getenv("BROCA_LEARNING_LOG_PROCEDURE_CREATION", "true").lower() == "true"


class BrocaConfig(BaseModel):
    cache: CacheConfig = CacheConfig()
    llm: LLMConfig = LLMConfig()
    llm_ensemble: LLMEnsembleConfig = LLMEnsembleConfig()
    model_router: ModelRouterConfig = ModelRouterConfig()
    logging: LoggingConfig = LoggingConfig()
    storage: StorageConfig = StorageConfig()
    tools: ToolsConfig = ToolsConfig()
    memory: MemoryConfig = MemoryConfig()
    self_model: SelfModelConfig = SelfModelConfig()
    internal_sensing: InternalSensingConfig = InternalSensingConfig()
    environment: EnvironmentConfig = EnvironmentConfig()
    optimization: OptimizationConfig = OptimizationConfig()
    summarization: SummarizationConfig = SummarizationConfig()
    context: ContextConfig = ContextConfig()
    repl_color: ReplColorConfig = ReplColorConfig()
    browse: BrowseConfig = BrowseConfig()
    reasoning: ReasoningConfig = ReasoningConfig()
    learning: LearningConfig = LearningConfig()
    damping: DampingConfig = DampingConfig()
    systems: SystemsConfig = SystemsConfig()
    control: ControlConfig = ControlConfig()
    rl: RLConfig = RLConfig()


config = BrocaConfig()
