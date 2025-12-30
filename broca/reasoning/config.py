"""
Configuration for reasoning system.
"""

from pydantic import BaseModel
import os


class ReasoningConfig(BaseModel):
    """Configuration for reasoning system."""
    
    enabled: bool = os.getenv("BROCA_REASONING_ENABLED", "false").lower() == "true"
    
    # Production rule system
    production_rules_enabled: bool = os.getenv("BROCA_REASONING_PRODUCTION_RULES_ENABLED", "true").lower() == "true"
    rules_file_path: str = os.getenv("BROCA_REASONING_RULES_FILE", "data/reasoning_rules.json")
    max_rules_per_cycle: int = int(os.getenv("BROCA_REASONING_MAX_RULES_PER_CYCLE", "5"))
    
    # Working memory
    working_memory_capacity: int = int(os.getenv("BROCA_REASONING_WORKING_MEMORY_CAPACITY", "7"))
    working_memory_update_interval: float = float(os.getenv("BROCA_REASONING_WORKING_MEMORY_UPDATE_INTERVAL", "1.0"))
    min_activation_threshold: float = float(os.getenv("BROCA_REASONING_MIN_ACTIVATION_THRESHOLD", "0.5"))
    
    # Goal management
    goal_management_enabled: bool = os.getenv("BROCA_REASONING_GOAL_MANAGEMENT_ENABLED", "true").lower() == "true"
    goals_file_path: str = os.getenv("BROCA_REASONING_GOALS_FILE", "data/reasoning_goals.json")
    auto_decompose_goals: bool = os.getenv("BROCA_REASONING_AUTO_DECOMPOSE_GOALS", "false").lower() == "true"
    
    # Planning
    planning_enabled: bool = os.getenv("BROCA_REASONING_PLANNING_ENABLED", "true").lower() == "true"
    max_planning_depth: int = int(os.getenv("BROCA_REASONING_MAX_PLANNING_DEPTH", "3"))
    max_planning_width: int = int(os.getenv("BROCA_REASONING_MAX_PLANNING_WIDTH", "5"))
    
    # Learning
    learning_enabled: bool = os.getenv("BROCA_REASONING_LEARNING_ENABLED", "true").lower() == "true"
    rule_learning_rate: float = float(os.getenv("BROCA_REASONING_RULE_LEARNING_RATE", "0.1"))
    max_rule_strength: float = float(os.getenv("BROCA_REASONING_MAX_RULE_STRENGTH", "10.0"))
    
    # Integration
    integrate_with_llm: bool = os.getenv("BROCA_REASONING_INTEGRATE_WITH_LLM", "true").lower() == "true"
    llm_integration_mode: str = os.getenv("BROCA_REASONING_LLM_INTEGRATION_MODE", "suggestion")  # "suggestion", "control", "hybrid"
    reasoning_cycle_interval: float = float(os.getenv("BROCA_REASONING_CYCLE_INTERVAL", "2.0"))  # Seconds between cycles
    
    # Declarative memory integration
    declarative_memory_enabled: bool = os.getenv("BROCA_REASONING_DECLARATIVE_MEMORY_ENABLED", "true").lower() == "true"
    spreading_activation_threshold: float = float(os.getenv("BROCA_REASONING_SPREADING_ACTIVATION_THRESHOLD", "0.7"))
    memory_retrieval_limit: int = int(os.getenv("BROCA_REASONING_MEMORY_RETRIEVAL_LIMIT", "5"))
    auto_store_reasoning_results: bool = os.getenv("BROCA_REASONING_AUTO_STORE_RESULTS", "true").lower() == "true"
    reasoning_memory_namespace: str = os.getenv("BROCA_REASONING_MEMORY_NAMESPACE", "reasoning/")
    
    # Storage
    storage_file_path: str = os.getenv("BROCA_REASONING_STORAGE_FILE", "data/reasoning_state.json")
    history_file_path: str = os.getenv("BROCA_REASONING_HISTORY_FILE", "data/reasoning_history.json")
    
    # Autonomous operation
    autonomous_enabled: bool = os.getenv("BROCA_REASONING_AUTONOMOUS_ENABLED", "false").lower() == "true"
    cycle_delay_seconds: float = float(os.getenv("BROCA_REASONING_CYCLE_DELAY_SECONDS", "30.0"))
    event_acceleration_enabled: bool = os.getenv("BROCA_REASONING_EVENT_ACCELERATION_ENABLED", "true").lower() == "true"
    max_cycles_per_minute: int = int(os.getenv("BROCA_REASONING_MAX_CYCLES_PER_MINUTE", "10"))
    
    # State persistence
    state_persistence_enabled: bool = os.getenv("BROCA_REASONING_STATE_PERSISTENCE_ENABLED", "true").lower() == "true"
    state_file_path: str = os.getenv("BROCA_REASONING_STATE_FILE", "data/reasoning_state.json")
    auto_save_interval_seconds: float = float(os.getenv("BROCA_REASONING_AUTO_SAVE_INTERVAL_SECONDS", "60.0"))
    
    # Feedback loops
    feedback_loops_enabled: bool = os.getenv("BROCA_REASONING_FEEDBACK_LOOPS_ENABLED", "true").lower() == "true"
    reinforcing_enabled: bool = os.getenv("BROCA_REASONING_REINFORCING_ENABLED", "true").lower() == "true"
    balancing_enabled: bool = os.getenv("BROCA_REASONING_BALANCING_ENABLED", "true").lower() == "true"
    metrics_tracking_window: int = int(os.getenv("BROCA_REASONING_METRICS_TRACKING_WINDOW", "100"))
    
    # Performance thresholds for balancing loops
    success_rate_threshold: float = float(os.getenv("BROCA_REASONING_SUCCESS_RATE_THRESHOLD", "0.7"))
    error_rate_threshold: float = float(os.getenv("BROCA_REASONING_ERROR_RATE_THRESHOLD", "0.3"))
    
    # Cognitive dissonance
    cognitive_dissonance_enabled: bool = os.getenv("BROCA_REASONING_COGNITIVE_DISSONANCE_ENABLED", "true").lower() == "true"
    dissonance_threshold: float = float(os.getenv("BROCA_REASONING_DISSONANCE_THRESHOLD", "0.3"))
    critical_dissonance_threshold: float = float(os.getenv("BROCA_REASONING_CRITICAL_DISSONANCE_THRESHOLD", "0.7"))
    periodic_update_interval_cycles: int = int(os.getenv("BROCA_REASONING_PERIODIC_UPDATE_INTERVAL_CYCLES", "10"))
    dissonance_weight_logical: float = float(os.getenv("BROCA_REASONING_DISSONANCE_WEIGHT_LOGICAL", "0.3"))
    dissonance_weight_factual: float = float(os.getenv("BROCA_REASONING_DISSONANCE_WEIGHT_FACTUAL", "0.3"))
    dissonance_weight_behavioral: float = float(os.getenv("BROCA_REASONING_DISSONANCE_WEIGHT_BEHAVIORAL", "0.2"))
    dissonance_weight_goal: float = float(os.getenv("BROCA_REASONING_DISSONANCE_WEIGHT_GOAL", "0.2"))
    
    # Self model update integration
    self_model_update_enabled: bool = os.getenv("BROCA_REASONING_SELF_MODEL_UPDATE_ENABLED", "true").lower() == "true"
    self_model_update_cooldown_seconds: float = float(os.getenv("BROCA_REASONING_SELF_MODEL_UPDATE_COOLDOWN_SECONDS", "300.0"))
    update_effectiveness_tracking_window: int = int(os.getenv("BROCA_REASONING_UPDATE_EFFECTIVENESS_TRACKING_WINDOW", "20"))
    
    # Learning-reasoning integration
    learning_integration_enabled: bool = os.getenv("BROCA_REASONING_LEARNING_INTEGRATION_ENABLED", "true").lower() == "true"
    dissonance_reward_weight: float = float(os.getenv("BROCA_REASONING_DISSONANCE_REWARD_WEIGHT", "1.0"))
    adaptive_control_enabled: bool = os.getenv("BROCA_REASONING_ADAPTIVE_CONTROL_ENABLED", "true").lower() == "true"
    skill_dissonance_threshold: float = float(os.getenv("BROCA_REASONING_SKILL_DISSONANCE_THRESHOLD", "-0.2"))
    
    # Z3 tool for LLM-driven validation (tool remains available, validator removed)
    z3_tool_enabled: bool = os.getenv("BROCA_REASONING_Z3_TOOL_ENABLED", "true").lower() == "true"
    z3_auto_validation_enabled: bool = os.getenv("BROCA_REASONING_Z3_AUTO_VALIDATION_ENABLED", "false").lower() == "true"
    
    # LLM pattern matching
    llm_pattern_matching_enabled: bool = os.getenv("BROCA_REASONING_LLM_PATTERN_MATCHING_ENABLED", "true").lower() == "true"
    llm_pattern_matching_model: str = os.getenv("BROCA_REASONING_LLM_PATTERN_MATCHING_MODEL", "gpt-5-nano")
    llm_pattern_matching_cache_size: int = int(os.getenv("BROCA_REASONING_LLM_PATTERN_MATCHING_CACHE_SIZE", "100"))
    llm_pattern_matching_batch_size: int = int(os.getenv("BROCA_REASONING_LLM_PATTERN_MATCHING_BATCH_SIZE", "10"))
    
    # LLM pattern matching logging
    llm_pattern_logging_enabled: bool = os.getenv("BROCA_REASONING_LLM_PATTERN_LOGGING_ENABLED", "true").lower() == "true"
    llm_pattern_log_path: str = os.getenv("BROCA_REASONING_LLM_PATTERN_LOG_PATH", "data/llm_pattern_matching_log.csv")
    llm_pattern_log_rotation: str = os.getenv("BROCA_REASONING_LLM_PATTERN_LOG_ROTATION", "daily")  # "daily" | "size" | "none"
    llm_pattern_log_max_size_mb: int = int(os.getenv("BROCA_REASONING_LLM_PATTERN_LOG_MAX_SIZE_MB", "100"))
    
    # Loop detection
    loop_detection_enabled: bool = os.getenv("BROCA_REASONING_LOOP_DETECTION_ENABLED", "true").lower() == "true"
    loop_detection_history_window: int = int(os.getenv("BROCA_REASONING_LOOP_DETECTION_HISTORY_WINDOW", "10"))
    loop_detection_time_window: float = float(os.getenv("BROCA_REASONING_LOOP_DETECTION_TIME_WINDOW", "60.0"))
    tool_queue_max_size: int = int(os.getenv("BROCA_REASONING_TOOL_QUEUE_MAX_SIZE", "50"))
    tool_queue_max_retries: int = int(os.getenv("BROCA_REASONING_TOOL_QUEUE_MAX_RETRIES", "3"))
    
    # Hierarchical control
    hierarchical_control_enabled: bool = os.getenv("BROCA_REASONING_HIERARCHICAL_CONTROL_ENABLED", "true").lower() == "true"
    strategic_threshold: float = float(os.getenv("BROCA_REASONING_STRATEGIC_THRESHOLD", "0.8"))
    tactical_threshold: float = float(os.getenv("BROCA_REASONING_TACTICAL_THRESHOLD", "0.5"))
    
    # Recursive reasoning
    recursive_reasoning_enabled: bool = os.getenv("BROCA_REASONING_RECURSIVE_REASONING_ENABLED", "true").lower() == "true"
    max_recursion_depth: int = int(os.getenv("BROCA_REASONING_MAX_RECURSION_DEPTH", "3"))
    recursion_timeout_seconds: float = float(os.getenv("BROCA_REASONING_RECURSION_TIMEOUT_SECONDS", "30.0"))
    
    # RL Signal Configuration
    rl_signals_enabled: bool = os.getenv("BROCA_REASONING_RL_SIGNALS_ENABLED", "true").lower() == "true"
    rl_weight_dissonance: float = float(os.getenv("BROCA_REASONING_RL_WEIGHT_DISSONANCE", "0.3"))
    rl_weight_surprise: float = float(os.getenv("BROCA_REASONING_RL_WEIGHT_SURPRISE", "0.2"))
    rl_weight_curiosity: float = float(os.getenv("BROCA_REASONING_RL_WEIGHT_CURIOSITY", "0.2"))
    rl_weight_info_gain: float = float(os.getenv("BROCA_REASONING_RL_WEIGHT_INFO_GAIN", "0.15"))
    rl_weight_coherence: float = float(os.getenv("BROCA_REASONING_RL_WEIGHT_COHERENCE", "0.15"))
    rl_surprise_threshold: float = float(os.getenv("BROCA_REASONING_RL_SURPRISE_THRESHOLD", "0.3"))
    rl_curiosity_threshold: float = float(os.getenv("BROCA_REASONING_RL_CURIOSITY_THRESHOLD", "0.5"))
    rl_exploration_ratio: float = float(os.getenv("BROCA_REASONING_RL_EXPLORATION_RATIO", "0.6"))
    
    # RL Reward Logging
    rl_reward_log_enabled: bool = os.getenv("BROCA_REASONING_RL_REWARD_LOG_ENABLED", "true").lower() == "true"
    rl_reward_log_file: str = os.getenv("BROCA_REASONING_RL_REWARD_LOG_FILE", "data/rl_rewards.csv")
    rl_reward_log_append: bool = os.getenv("BROCA_REASONING_RL_REWARD_LOG_APPEND", "true").lower() == "true"
    
    # PEA/PFREA removed - planning is now handled via planning tool
    
    # Debugging
    debug_mode: bool = os.getenv("BROCA_REASONING_DEBUG_MODE", "false").lower() == "true"
    log_rule_firings: bool = os.getenv("BROCA_REASONING_LOG_RULE_FIRINGS", "true").lower() == "true"
    log_goal_changes: bool = os.getenv("BROCA_REASONING_LOG_GOAL_CHANGES", "true").lower() == "true"
