from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()



class LLMConfig(BaseModel):
    provider: str = os.getenv("BROCA_LLM_PROVIDER", "deepseek")  # "deepseek", "openai", or "gemini"
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


class StorageConfig(BaseModel):
    storage_type: str = os.getenv("BROCA_STORAGE_TYPE", "json")
    storage_path: str = os.getenv("BROCA_STORAGE_PATH", "conversations")
    base_system_prompt: str = os.getenv("BROCA_BASE_SYSTEM_PROMPT", "")
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
    # Policy: read-only mode
    tools_mode: str = os.getenv("BROCA_TOOLS_MODE", "normal")  # "normal" or "read_only"
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
    
    # Budgets
    default_max_actions: int = int(os.getenv("BROCA_BROWSE_MAX_ACTIONS", "20"))
    default_max_wallclock_ms: int = int(os.getenv("BROCA_BROWSE_MAX_WALLCLOCK_MS", "60000"))
    default_max_domains: int = int(os.getenv("BROCA_BROWSE_MAX_DOMAINS", "5"))
    default_max_total_bytes: int = int(os.getenv("BROCA_BROWSE_MAX_TOTAL_BYTES", "10000000"))
    
    # Extraction
    extraction_mode_preference: list[str] = (
        os.getenv("BROCA_BROWSE_EXTRACTION_MODES", "readability,trafilatura,dom").split(",")
        if os.getenv("BROCA_BROWSE_EXTRACTION_MODES")
        else ["readability", "trafilatura", "dom"]
    )
    max_extracted_chars: int = int(os.getenv("BROCA_BROWSE_MAX_EXTRACTED_CHARS", "50000"))
    
    # Source Quality
    domain_reputation_file: str = os.getenv("BROCA_BROWSE_DOMAIN_REPUTATION_FILE", "data/browse_domain_reputation.json")
    
    # Traces
    trace_storage_path: str = os.getenv("BROCA_BROWSE_TRACE_STORAGE_PATH", "docs/browse_traces")
    enable_trace_replay: bool = os.getenv("BROCA_BROWSE_ENABLE_TRACE_REPLAY", "true").lower() == "true"
    
    # Safety
    safety: BrowseSafetyConfig = BrowseSafetyConfig()


class BrocaConfig(BaseModel):
    cache: CacheConfig = CacheConfig()
    llm: LLMConfig = LLMConfig()
    logging: LoggingConfig = LoggingConfig()
    storage: StorageConfig = StorageConfig()
    tools: ToolsConfig = ToolsConfig()
    memory: MemoryConfig = MemoryConfig()
    self_model: SelfModelConfig = SelfModelConfig()
    internal_sensing: InternalSensingConfig = InternalSensingConfig()
    environment: EnvironmentConfig = EnvironmentConfig()
    optimization: OptimizationConfig = OptimizationConfig()
    summarization: SummarizationConfig = SummarizationConfig()
    repl_color: ReplColorConfig = ReplColorConfig()
    browse: BrowseConfig = BrowseConfig()


config = BrocaConfig()
