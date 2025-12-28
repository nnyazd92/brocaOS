"""
Configuration for learning system.
"""

from pydantic import BaseModel
import os


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
    
    # Cognitive dissonance integration
    dissonance_integration_enabled: bool = os.getenv("BROCA_LEARNING_DISSONANCE_INTEGRATION_ENABLED", "true").lower() == "true"
    dissonance_reward_weight: float = float(os.getenv("BROCA_LEARNING_DISSONANCE_REWARD_WEIGHT", "1.0"))
    filter_by_dissonance: bool = os.getenv("BROCA_LEARNING_FILTER_BY_DISSONANCE", "true").lower() == "true"
    min_dissonance_reduction: float = float(os.getenv("BROCA_LEARNING_MIN_DISSONANCE_REDUCTION", "0.0"))
    
    # Debugging
    debug_mode: bool = os.getenv("BROCA_LEARNING_DEBUG_MODE", "false").lower() == "true"
    log_observations: bool = os.getenv("BROCA_LEARNING_LOG_OBSERVATIONS", "true").lower() == "true"
    log_procedure_creation: bool = os.getenv("BROCA_LEARNING_LOG_PROCEDURE_CREATION", "true").lower() == "true"
