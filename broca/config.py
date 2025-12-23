from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class LLMConfig(BaseModel):
    provider: str = os.getenv("BROCA_LLM_PROVIDER", "deepseek")  # "deepseek" or "openai"
    api_base: str = os.getenv("DEEPSEEK_API_BASE", "")  # Will default based on provider
    api_key: str = os.getenv("DEEPSEEK_API_KEY", "")  # Will default based on provider
    model: str = os.getenv("DEEPSEEK_MODEL", "")  # Will default based on provider
    temperature: float = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.3"))
    timeout: float = float(os.getenv("DEEPSEEK_TIMEOUT", "300.0"))  # Default 5 minutes
    streaming_enabled: bool = os.getenv("BROCA_STREAMING_ENABLED", "true").lower() == "true"
    streaming_delay: float = float(os.getenv("BROCA_STREAMING_DELAY", "0.02"))  # Delay between chunks in seconds (default 20ms)
    max_context_tokens: int = int(os.getenv("BROCA_MAX_CONTEXT_TOKENS", "272000"))  # Maximum context window size (matches API limit)
    
    def __init__(self, **kwargs):
        # Get provider first
        provider = kwargs.get("provider", os.getenv("BROCA_LLM_PROVIDER", "deepseek"))
        
        # Set defaults based on provider
        if provider == "openai":
            default_base = kwargs.get("api_base") or os.getenv("DEEPSEEK_API_BASE") or "https://api.openai.com/v1"
            # For OpenAI provider, prioritize OPENAI_API_KEY over DEEPSEEK_API_KEY
            # Explicit kwargs take precedence, then OPENAI_API_KEY, then DEEPSEEK_API_KEY as fallback
            default_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or ""
            # Model precedence: OPENAI_MODEL > BROCA_LLM_MODEL > DEEPSEEK_MODEL > default
            default_model = (
                kwargs.get("model") or
                os.getenv("OPENAI_MODEL") or
                os.getenv("BROCA_LLM_MODEL") or
                os.getenv("DEEPSEEK_MODEL") or
                "gpt-5.2"
            )
        else:  # deepseek (default)
            default_base = kwargs.get("api_base") or os.getenv("DEEPSEEK_API_BASE") or "https://api.deepseek.com/v1"
            default_key = kwargs.get("api_key") or os.getenv("DEEPSEEK_API_KEY") or ""
            default_model = kwargs.get("model") or os.getenv("BROCA_LLM_MODEL") or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
        
        # Update kwargs with defaults
        if "api_base" not in kwargs:
            kwargs["api_base"] = default_base
        if "api_key" not in kwargs:
            kwargs["api_key"] = default_key
        if "model" not in kwargs:
            kwargs["model"] = default_model
        if "provider" not in kwargs:
            kwargs["provider"] = provider
            
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
    # Project world state tool configuration
    enable_project_world_state: bool = os.getenv("BROCA_ENABLE_PROJECT_WORLD_STATE", "true").lower() == "true"
    project_world_state_path: str | None = os.getenv("BROCA_PROJECT_WORLD_STATE_PATH", None)
    project_world_state_file: str = os.getenv("BROCA_PROJECT_WORLD_STATE_FILE", "project_world_state.json")
    project_world_state_header_lines: int = int(os.getenv("BROCA_PROJECT_WORLD_STATE_HEADER_LINES", "10"))
    project_world_state_max_file_size: int = int(os.getenv("BROCA_PROJECT_WORLD_STATE_MAX_FILE_SIZE", str(1024 * 1024)))  # 1MB default
    project_world_state_max_file_size: int = int(os.getenv("BROCA_PROJECT_WORLD_STATE_MAX_FILE_SIZE", str(1024 * 1024)))  # 1MB default
    # Policy: read-only mode and web search limits
    tools_mode: str = os.getenv("BROCA_TOOLS_MODE", "normal")  # "normal" or "read_only"
    web_search_max_queries: int = int(os.getenv("BROCA_WEB_SEARCH_MAX_QUERIES", "3"))
    web_search_cooldown_turns: int = int(os.getenv("BROCA_WEB_SEARCH_COOLDOWN_TURNS", "3"))


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


config = BrocaConfig()
