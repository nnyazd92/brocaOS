import sys
import re
import readline  # optional, for nicer REPL on Unix
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from .logging_config import setup_logging
from .repl.session import ConversationSession
# Config is imported locally in functions to avoid scoping issues
from .storage.json_storage import JSONFileStorage
from .storage import ConversationStorage
from .tools.registry import ToolRegistry
from .tools.web_search import WebSearchTool
from .tools.memory_tool import (
    StoreMemoryTool, RetrieveMemoriesTool, DeleteMemoryTool, UpdateMemoryTool,
    LinkMemoriesTool, GetRelatedMemoriesTool, MemoryGraphTool
)
from .tools.terminal import TerminalTool
from .memory.storage import MemoryStorage
from .memory.vector_index import VectorIndex
from .memory.embeddings import EmbeddingService
from .memory.manager import MemoryManager
from .self_model.model import SelfModel
from .tools.self_model_crud_tool import SelfModelCRUDTool
from .internal_sensing.framework import InternalSensingFramework
from .world_state.aggregator import WorldStateAggregator

if TYPE_CHECKING:
    from .self_model.storage import SelfModelSQLiteStorage

logger = logging.getLogger(__name__)

# ANSI escape code pattern
_ANSI_ESCAPE_PATTERN = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def _strip_ansi_codes(text: str) -> str:
    """
    Strip ANSI escape codes from text.
    
    Args:
        text: Text that may contain ANSI codes
        
    Returns:
        Text with ANSI codes removed
    """
    return _ANSI_ESCAPE_PATTERN.sub('', text)


def _get_visible_width(text: str) -> int:
    """
    Get the visible width of text, excluding ANSI escape codes.
    
    Args:
        text: Text that may contain ANSI codes
        
    Returns:
        Visible width in characters
    """
    return len(_strip_ansi_codes(text))




def _initialize_storage() -> ConversationStorage | None:
    """
    Initialize storage backend based on configuration.
    
    Returns:
        Storage instance if successfully initialized, None otherwise.
    """
    from .config import config as app_config
    try:
        if app_config.storage.storage_type == "json":
            storage = JSONFileStorage(storage_path=app_config.storage.storage_path)
            logger.info(f"Initialized {app_config.storage.storage_type} storage at {app_config.storage.storage_path}")
            return storage
        else:
            logger.warning(f"Unknown storage type: {app_config.storage.storage_type}, storage disabled")
            return None
    except Exception as e:
        logger.warning(f"Failed to initialize storage: {e}, continuing without storage", exc_info=True)
        return None


def _initialize_memory_manager() -> MemoryManager | None:
    """
    Initialize memory manager with storage, vector index, and embeddings.
    
    Returns:
        MemoryManager instance if successfully initialized, None otherwise.
    """
    from .config import config as app_config
    try:
        # Initialize embedding service
        try:
            embedding_service = EmbeddingService()
        except Exception as e:
            logger.warning(f"Failed to initialize embedding service: {e}, memory disabled", exc_info=True)
            return None
        
        # Initialize storage
        storage = MemoryStorage(db_path=app_config.memory.memory_db_path)
        
        # Initialize vector index
        try:
            vector_index = VectorIndex(
                dimension=app_config.memory.embedding_dimension,
                index_path=app_config.memory.vector_index_path
            )
        except ValueError as e:
            logger.warning(f"Failed to initialize vector index: {e}, memory disabled", exc_info=True)
            storage.close()
            return None
        
        # Create memory manager
        manager = MemoryManager(storage, vector_index, embedding_service)
        logger.info("Initialized MemoryManager")
        return manager
        
    except Exception as e:
        logger.warning(f"Failed to initialize memory manager: {e}, continuing without memory", exc_info=True)
        return None


def _initialize_tool_registry(
    memory_manager: MemoryManager | None = None,
    epistemic_engine: "MetacognitiveEngine | None" = None,
    self_model: SelfModel | None = None,
    internal_sensing: InternalSensingFramework | None = None,
    storage: Any = None,
    reasoning_tool: Any = None,
    rl_signal_aggregator: Any = None,
    skill_manager: Any = None,
    goal_manager: Any = None,
) -> ToolRegistry | None:
    """
    Initialize tool registry and register available tools.
    
    Args:
        memory_manager: Optional MemoryManager instance for memory tools
        epistemic_engine: Optional MetacognitiveEngine instance for epistemic tracking
        self_model: Optional SelfModel instance for self-model tools
        storage: Optional storage instance for saving self-model
    
    Returns:
        ToolRegistry instance if successfully initialized, None otherwise.
    """
    from .config import config as app_config
    try:
        # Initialize tool selection guidance if enabled
        tool_selection_guidance = None
        if app_config.tools.selection_guidance_enabled:
            try:
                from .tools.selection_guidance import ToolSelectionGuidance, ValidationStrictness
                
                # Map config string to enum
                strictness_map = {
                    "advisory": ValidationStrictness.ADVISORY,
                    "soft_block": ValidationStrictness.SOFT_BLOCK,
                    "hard_block": ValidationStrictness.HARD_BLOCK,
                }
                validation_strictness = strictness_map.get(
                    app_config.tools.validation_strictness,
                    ValidationStrictness.ADVISORY
                )
                
                tool_selection_guidance = ToolSelectionGuidance(
                    reasoning_tool=reasoning_tool,
                    rl_signal_aggregator=rl_signal_aggregator,
                    skill_manager=skill_manager,
                    goal_manager=goal_manager,
                    max_guidance_length=app_config.tools.max_guidance_length,
                    guidance_text_style=app_config.tools.guidance_text_style,
                    ranking_algorithm=app_config.tools.ranking_algorithm,
                    validation_strictness=validation_strictness,
                    validation_confidence_threshold=app_config.tools.validation_confidence_threshold,
                    context_cache_ttl_seconds=app_config.tools.context_cache_ttl_seconds,
                    exploration_factor=app_config.tools.exploration_factor,
                )
                
                # Initialize metrics if enabled
                if app_config.tools.metrics_enabled:
                    try:
                        from .tools.selection_metrics import ToolSelectionMetrics
                        metrics = ToolSelectionMetrics(window_size=app_config.tools.metrics_window_size)
                        tool_selection_guidance.set_metrics(metrics)
                        logger.info("✓ Tool selection metrics enabled")
                    except Exception as e:
                        logger.warning(f"Failed to initialize tool selection metrics: {e}", exc_info=True)
                
                logger.info("✓ Tool selection guidance initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize tool selection guidance: {e}", exc_info=True)
        
        registry = ToolRegistry(
            epistemic_engine=epistemic_engine,
            internal_sensing_framework=internal_sensing,
            tool_selection_guidance=tool_selection_guidance
        )
        
        # Register web search tool if enabled
        # Tavily API is primary search provider (requires TAVILY_API_KEY)
        # Browser-based search is used as fallback when Tavily is unavailable
        if app_config.tools.enable_web_search:
            try:
                # WebSearchTool uses Tavily API as primary, browser search as fallback
                web_search_tool = WebSearchTool(api_key=app_config.tools.tavily_api_key or None)
                registry.register_tool(web_search_tool)
                logger.info("Registered web search tool (Tavily primary, browser fallback)")
            except Exception as e:
                logger.warning(
                    f"Failed to register web search tool: {e}. "
                    "Ensure browser navigation is enabled and Playwright is installed: "
                    "pip install playwright && playwright install chromium",
                    exc_info=True
                )
        
        # Register memory tools if memory manager is available
        if memory_manager:
            try:
                store_tool = StoreMemoryTool(
                    memory_manager, 
                    epistemic_engine=epistemic_engine,
                    self_model=self_model,
                    storage=storage
                )
                retrieve_tool = RetrieveMemoriesTool(memory_manager, epistemic_engine=epistemic_engine)
                delete_tool = DeleteMemoryTool(memory_manager)
                update_tool = UpdateMemoryTool(memory_manager)
                link_tool = LinkMemoriesTool(memory_manager)
                get_related_tool = GetRelatedMemoriesTool(memory_manager)
                memory_graph_tool = MemoryGraphTool(memory_manager)
                registry.register_tool(store_tool)
                registry.register_tool(retrieve_tool)
                registry.register_tool(delete_tool)
                registry.register_tool(update_tool)
                registry.register_tool(link_tool)
                registry.register_tool(get_related_tool)
                registry.register_tool(memory_graph_tool)
                logger.info("Registered memory tools")
            except Exception as e:
                logger.warning(f"Failed to register memory tools: {e}", exc_info=True)
        
        # Register terminal tool if enabled
        if app_config.tools.enable_terminal:
            try:
                terminal_tool = TerminalTool()
                registry.register_tool(terminal_tool)
                logger.info("Registered terminal tool")
            except Exception as e:
                logger.warning(f"Failed to register terminal tool: {e}", exc_info=True)
        
        # Register critic tool if enabled
        if app_config.tools.enable_critic:
            try:
                from .tools.critic import CriticTool
                critic_tool = CriticTool(
                    system_prompt_template=app_config.tools.critic_system_prompt_template
                )
                registry.register_tool(critic_tool)
                logger.info("Registered critic tool")
            except Exception as e:
                logger.warning(f"Failed to register critic tool: {e}", exc_info=True)
        
        # Register browser navigation tool if enabled
        if app_config.tools.enable_browser_navigation:
            try:
                from .tools.browser_navigation import BrowserNavigationTool
                browser_tool = BrowserNavigationTool(
                    headless=app_config.tools.browser_headless,
                    timeout=app_config.tools.browser_timeout,
                    stealth_mode=app_config.tools.browser_stealth_mode,
                    viewport_width=app_config.tools.browser_viewport_width,
                    viewport_height=app_config.tools.browser_viewport_height,
                    user_agents=app_config.tools.browser_user_agents
                )
                registry.register_tool(browser_tool)
                logger.info("Registered browser navigation tool")
            except Exception as e:
                logger.warning(f"Failed to register browser navigation tool: {e}", exc_info=True)
        
        # Register self-model tools if self-model is available
        if self_model and storage:
            try:
                # Register CRUD tool (comprehensive self-model management)
                # All self-model updates should be done through the CRUD tool
                crud_tool = SelfModelCRUDTool(
                    self_model=self_model,
                    storage=storage,
                    epistemic_engine=epistemic_engine
                )
                registry.register_tool(crud_tool)
                logger.info("Registered self-model CRUD tool")
            except Exception as e:
                logger.warning(f"Failed to register self-model tools: {e}", exc_info=True)
        
        # Register planning tool
        try:
            from .tools.planning_tool import PlanningTool
            planning_tool = PlanningTool()
            registry.register_tool(planning_tool)
            logger.info("Registered planning tool")
        except Exception as e:
            logger.warning(f"Failed to register planning tool: {e}", exc_info=True)
        
        # Register Z3 validator tool if enabled
        if app_config.reasoning.z3_tool_enabled:
            try:
                from .tools.z3_validator_tool import Z3ValidatorTool
                z3_tool = Z3ValidatorTool(
                    timeout=app_config.reasoning.z3_validation_timeout
                )
                registry.register_tool(z3_tool)
                logger.info("Registered Z3 validator tool")
            except Exception as e:
                logger.warning(f"Failed to register Z3 validator tool: {e}", exc_info=True)
        
        if len(registry.list_tools()) == 0:
            logger.debug("No tools registered")
            return None
        
        logger.info(f"Initialized tool registry with {len(registry.list_tools())} tool(s)")
        return registry
        
    except Exception as e:
        logger.warning(f"Failed to initialize tool registry: {e}, continuing without tools", exc_info=True)
        return None


def _backfill_epistemic_layer(
    self_model: SelfModel,
    epistemic_engine: "MetacognitiveEngine"
) -> None:
    """
    Backfill epistemic metadata for existing self-model data.
    
    Populates epistemic layer with knowledge items for existing capabilities,
    preferences, constraints, and knowledge boundaries that don't already have
    epistemic tracking.
    
    Args:
        self_model: SelfModel instance to backfill
        epistemic_engine: MetacognitiveEngine instance for tracking
    """
    from .self_model.epistemic.ids import (
        generate_capability_id,
        generate_constraint_id,
        generate_knowledge_boundary_id,
    )
    from .self_model.epistemic.models import SourceType, SourceMetadata
    from datetime import datetime, timezone
    
    try:
        # Track capabilities in epistemic layer (only if not already tracked)
        for capability in self_model.capabilities:
            # Extract text from capability dict (capabilities are stored as dicts with "text" and "source")
            capability_text = capability.get("text", str(capability)) if isinstance(capability, dict) else str(capability)
            knowledge_id = generate_capability_id(capability_text)
            # Skip if already tracked
            if epistemic_engine.epistemic_layer.has_knowledge(knowledge_id):
                continue
            
            source = SourceMetadata(
                source_type=SourceType.SYSTEM_DEFAULT,
                timestamp=datetime.now(timezone.utc)
            )
            # Use assessed source reliability instead of hardcoded value
            source_reliability = epistemic_engine.validator.assess_source_reliability(source)
            epistemic_engine.knowledge_acquisition_workflow(
                knowledge_id=knowledge_id,
                source=source,
                initial_confidence=source_reliability
            )
        
        # Note: preferences attribute was removed from SelfModel - skipping preferences backfilling
        
        # Track knowledge boundaries in epistemic layer
        for key, value_dict in self_model.knowledge_boundaries.items():
            # Extract value from knowledge_boundary dict (values are stored as dicts with "value" and "source")
            value = value_dict.get("value", str(value_dict)) if isinstance(value_dict, dict) else str(value_dict)
            knowledge_id = generate_knowledge_boundary_id(key, value)
            # Skip if already tracked
            if epistemic_engine.epistemic_layer.has_knowledge(knowledge_id):
                continue
            
            source = SourceMetadata(
                source_type=SourceType.SYSTEM_DEFAULT,
                timestamp=datetime.now(timezone.utc)
            )
            # Use assessed source reliability instead of hardcoded value
            source_reliability = epistemic_engine.validator.assess_source_reliability(source)
            epistemic_engine.knowledge_acquisition_workflow(
                knowledge_id=knowledge_id,
                source=source,
                initial_confidence=source_reliability
            )
        
        # Track constraints in epistemic layer
        for key, value_dict in self_model.constraints.items():
            # Extract value from constraint dict (values are stored as dicts with "value" and "source")
            value = value_dict.get("value", str(value_dict)) if isinstance(value_dict, dict) else str(value_dict)
            knowledge_id = generate_constraint_id(key, value)
            # Skip if already tracked
            if epistemic_engine.epistemic_layer.has_knowledge(knowledge_id):
                continue
            
            source = SourceMetadata(
                source_type=SourceType.SYSTEM_DEFAULT,
                timestamp=datetime.now(timezone.utc)
            )
            # Use assessed source reliability instead of hardcoded value
            source_reliability = epistemic_engine.validator.assess_source_reliability(source)
            epistemic_engine.knowledge_acquisition_workflow(
                knowledge_id=knowledge_id,
                source=source,
                initial_confidence=source_reliability
            )
        
        logger.info("Backfilled epistemic layer with existing model data")
        
    except Exception as e:
        logger.warning(f"Error during epistemic layer backfilling: {e}", exc_info=True)
        # Continue without backfilling - epistemic layer is still initialized


def _initialize_self_model(
    storage_path_override: str | None = None,
    enable_epistemic_override: bool | None = None
) -> tuple[SelfModel | None, Any, "MetacognitiveEngine | None"]:
    """
    Initialize self-model system if enabled.
    
    Args:
        storage_path_override: Optional path to override the config storage path (for testing)
        enable_epistemic_override: Optional override for enable_epistemic config (for testing)
    
    Returns:
        Tuple of (SelfModel instance or None, storage instance or None, MetacognitiveEngine or None)
    """
    from .config import config as app_config
    
    if not app_config or not app_config.self_model.enabled:
        logger.debug("Self-model system is disabled")
        return None, None, None
    
    try:
        # Initialize storage using factory
        from .self_model.storage import create_storage
        from pathlib import Path
        
        storage_path = (
            storage_path_override or
            (app_config.self_model.sqlite_db_path 
             if app_config.self_model.storage_type == "sqlite" 
             else app_config.self_model.storage_path)
        )
        
        # Resolve to absolute path to ensure consistent persistence location
        storage_path_obj = Path(storage_path)
        if not storage_path_obj.is_absolute():
            # Resolve relative paths to absolute (relative to workspace root)
            storage_path = str(storage_path_obj.resolve())
        else:
            storage_path = str(storage_path_obj)
        
        logger.info(f"Initializing self-model storage at: {storage_path}")
        
        storage = create_storage(
            storage_type=app_config.self_model.storage_type,
            storage_path=storage_path
        )
        
        # Load existing self-model or create default
        self_model = storage.load()
        if not self_model:
            logger.info("No existing self-model found, creating default")
            self_model = SelfModel.create_default()
            storage.save(self_model)
        else:
            logger.info(f"Loaded self-model version {self_model.metadata.get('version', 'unknown')}")
        
        # Auto-initialize epistemic layer if enabled and missing
        # Use override if provided, otherwise use config
        enable_epistemic = (
            enable_epistemic_override 
            if enable_epistemic_override is not None 
            else (app_config.self_model.enable_epistemic if app_config else False)
        )
        epistemic_engine = None
        if self_model and enable_epistemic:
            if self_model.epistemic_layer is None:
                # Initialize empty epistemic layer for existing model
                logger.info("Epistemic layer missing, initializing for existing model")
                from .self_model.epistemic.layer import EpistemicLayer
                from .self_model.epistemic.engine import MetacognitiveEngine
                
                self_model.epistemic_layer = EpistemicLayer()
                epistemic_engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
                
                # Backfill existing model data with epistemic metadata
                _backfill_epistemic_layer(self_model, epistemic_engine)
                
                # Save updated model with epistemic layer
                storage.save(self_model)
                logger.info("Initialized and saved epistemic layer for existing model")
            else:
                # Epistemic layer exists, create engine and activate
                try:
                    from .self_model.epistemic.engine import MetacognitiveEngine
                    epistemic_engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
                    
                    # Log activation status
                    knowledge_count = len(self_model.epistemic_layer.knowledge_sources)
                    logger.info(
                        f"Activated epistemic layer with {knowledge_count} knowledge items. "
                        f"MetacognitiveEngine created and ready for tracking."
                    )
                except Exception as e:
                    logger.warning(f"Failed to create MetacognitiveEngine: {e}", exc_info=True)
        
        logger.info("Initialized self-model system")
        return self_model, storage, epistemic_engine
        
    except Exception as e:
        logger.warning(f"Failed to initialize self-model system: {e}, continuing without it", exc_info=True)
        return None, None, None


def _initialize_environment_system():
    """
    Initialize environment access system if enabled.
    
    Returns:
        EnvironmentAccessSystem instance or None
    """
    from .config import config as app_config
    
    if not app_config or not app_config.environment.enabled:
        logger.debug("Environment access system is disabled")
        return None
    
    try:
        from .environment.access_system import EnvironmentAccessSystem
        from .environment.access_types import AccessLevel
        
        # Determine initial access level
        initial_level = AccessLevel.SANDBOXED
        try:
            if app_config:
                initial_level = AccessLevel[app_config.environment.access_level]
        except (KeyError, AttributeError):
            pass
        
        system = EnvironmentAccessSystem()
        system.policy_manager.current_level = initial_level
        
        # Discover and register sensors if enabled
        if app_config and app_config.environment.enable_sensors:
            system.discover_and_register_sensors()
            logger.info(f"Discovered and registered {len(system.sensor_registry.sensors)} sensors")
        
        logger.info("Initialized environment access system")
        return system
        
    except Exception as e:
        logger.warning(f"Failed to initialize environment system: {e}, continuing without it", exc_info=True)
        return None


def _initialize_internal_sensing(embedding_service: Optional[EmbeddingService] = None, epistemic_engine: Optional[Any] = None) -> InternalSensingFramework | None:
    """
    Initialize internal sensing system if enabled.
    
    Args:
        embedding_service: Optional embedding service for semantic analysis
        epistemic_engine: Optional MetacognitiveEngine for second-order metacognition
    
    Returns:
        InternalSensingFramework instance or None
    """
    from .config import config as app_config
    
    if not app_config or not app_config.internal_sensing.enabled:
        logger.debug("Internal sensing system is disabled")
        return None
    
    try:
        framework = InternalSensingFramework(
            sampling_rate=app_config.internal_sensing.sampling_rate,
            history_window=app_config.internal_sensing.history_window,
            embedding_service=embedding_service,
            epistemic_engine=epistemic_engine,
        )
        
        # Enable/disable specific components based on config
        if not app_config.internal_sensing.enable_physiology:
            framework.interoception.physiology = None  # type: ignore
        if not app_config.internal_sensing.enable_cognitive:
            framework.interoception.cognition = None  # type: ignore
        if not app_config.internal_sensing.enable_affective:
            framework.interoception.affect = None  # type: ignore
        if not app_config.internal_sensing.enable_predictive:
            framework.interoception.prediction = None  # type: ignore
        
        logger.info("Initialized internal sensing system")
        return framework
        
    except Exception as e:
        logger.warning(f"Failed to initialize internal sensing system: {e}, continuing without it", exc_info=True)
        return None


def _initialize_reasoning_system(
    memory_manager: Optional[MemoryManager] = None,
    self_model: Optional[SelfModel] = None,
    self_model_storage: Optional[Any] = None,
    internal_sensing: Optional[InternalSensingFramework] = None
) -> Optional["ReasoningTool"]:
    """
    Initialize the complete reasoning system with cognitive dissonance integration.
    
    Creates and wires together:
    - Declarative memory and spreading activation
    - Reasoning tool (rule system, goal manager, working memory)
    - Cognitive dissonance monitor
    - Self model updater and feedback loop
    - Feedback loop manager
    - State manager (if persistence enabled)
    - Reasoning daemon (if autonomous enabled)
    
    Args:
        memory_manager: Optional MemoryManager for declarative memory
        self_model: Optional SelfModel for cognitive dissonance monitoring
        self_model_storage: Optional storage for self model updates
        
    Returns:
        ReasoningTool instance if successfully initialized, None otherwise
    """
    from .config import config as app_config
    try:
        from .reasoning.config import ReasoningConfig
        from .reasoning.declarative_memory import DeclarativeMemoryInterface
        from .reasoning.spreading_activation import SpreadingActivation
        from .reasoning.integration_tool import ReasoningTool
        from .reasoning.cognitive_dissonance import CognitiveDissonanceMonitor
        from .reasoning.self_model_feedback import SelfModelFeedbackLoop
        from .reasoning.feedback_loop import FeedbackLoopManager
        from .reasoning.daemon import ReasoningDaemon
        from .reasoning.state_manager import ReasoningStateManager
        from .self_model.consistency import ConsistencyChecker
        from .self_model.updater import SelfModelUpdater
        from .llm import create_llm_client
        
        reasoning_config = ReasoningConfig()
        
        # Initialize declarative memory if memory manager is available
        declarative_memory = None
        spreading_activation = None
        if memory_manager and reasoning_config.declarative_memory_enabled:
            declarative_memory = DeclarativeMemoryInterface(
                memory_manager=memory_manager,
                reasoning_namespace=reasoning_config.reasoning_memory_namespace
            )
            logger.info("✓ Declarative memory interface initialized")
            
            spreading_activation = SpreadingActivation(
                declarative_memory=declarative_memory,
                activation_threshold=reasoning_config.spreading_activation_threshold,
                damping_factor=0.5,
                max_activations_per_cycle=3
            )
            logger.info("✓ Spreading activation initialized")
        
        # Initialize cognitive dissonance monitor if self model is available
        cognitive_dissonance_monitor = None
        consistency_checker = None
        self_model_updater = None
        self_model_feedback_loop = None
        
        if self_model and reasoning_config.cognitive_dissonance_enabled:
            # Create consistency checker
            consistency_checker = ConsistencyChecker(llm_client=create_llm_client())
            logger.info("✓ Consistency checker initialized")
            
            # Create self model updater
            if self_model_storage:
                self_model_updater = SelfModelUpdater(llm_client=create_llm_client())
                logger.info("✓ Self model updater initialized")
            
            # Get epistemic engine if available
            epistemic_engine = None
            if hasattr(self_model, 'epistemic_layer') and self_model.epistemic_layer:
                try:
                    from .self_model.epistemic.engine import MetacognitiveEngine
                    # Try to get epistemic engine from internal sensing if available
                    if internal_sensing and hasattr(internal_sensing, 'epistemic_engine'):
                        epistemic_engine = internal_sensing.epistemic_engine
                except Exception:
                    pass
            
            # Z3 validator removed - use z3_validate tool instead for explicit validation
            z3_validator = None
            
            # Create fact checker
            fact_checker = None
            try:
                from .reasoning.fact_checker import FactChecker
                # Try to get web search tool from tool registry if available
                web_search_tool = None
                # Fact checker will create its own web search tool if needed
                fact_checker = FactChecker(enable_web_search=True)
                logger.info("✓ Fact checker initialized for cognitive dissonance")
            except Exception as e:
                logger.warning(f"Failed to initialize fact checker: {e}")
            
            # Create cognitive dissonance monitor
            # Note: goal_manager will be wired after reasoning_tool is created
            cognitive_dissonance_monitor = CognitiveDissonanceMonitor(
                self_model=self_model,
                consistency_checker=consistency_checker,
                epistemic_engine=epistemic_engine,
                history_window=reasoning_config.metrics_tracking_window,
                weight_logical=reasoning_config.dissonance_weight_logical,
                weight_factual=reasoning_config.dissonance_weight_factual,
                weight_behavioral=reasoning_config.dissonance_weight_behavioral,
                weight_goal=reasoning_config.dissonance_weight_goal,
                memory_manager=memory_manager,
                fact_checker=fact_checker,
                goal_manager=None  # Will be wired after reasoning_tool is created
            )
            logger.info("✓ Cognitive dissonance monitor initialized")
            
            # Create self model feedback loop if updater is available
            if self_model_updater and reasoning_config.self_model_update_enabled:
                self_model_feedback_loop = SelfModelFeedbackLoop(
                    self_model=self_model,
                    cognitive_dissonance_monitor=cognitive_dissonance_monitor,
                    self_model_updater=self_model_updater,
                    update_cooldown_seconds=reasoning_config.self_model_update_cooldown_seconds,
                    periodic_update_interval_cycles=reasoning_config.periodic_update_interval_cycles,
                    dissonance_threshold=reasoning_config.dissonance_threshold,
                    critical_dissonance_threshold=reasoning_config.critical_dissonance_threshold,
                    effectiveness_window=reasoning_config.update_effectiveness_tracking_window
                )
                logger.info("✓ Self model feedback loop initialized")
        
        # Initialize learning tool if enabled and integration enabled
        learning_tool = None
        if app_config and app_config.learning.enabled and reasoning_config.learning_integration_enabled:
            try:
                from .learning.integration_tool import LearningTool
                learning_tool = LearningTool()
                logger.info("✓ Learning tool initialized for reasoning integration")
            except Exception as e:
                logger.warning(f"Failed to initialize learning tool: {e}", exc_info=True)
        
        # Create RL signal aggregator if RL signals are enabled
        rl_signal_aggregator = None
        if reasoning_config.feedback_loops_enabled and reasoning_config.rl_signals_enabled:
            try:
                from .reasoning.rl_signals import RLSignalAggregator
                
                # Get components for RL signal aggregator
                affective_monitor = None
                predictive_interoception = None
                epistemic_bridge = None
                
                if internal_sensing:
                    if hasattr(internal_sensing, 'interoception') and internal_sensing.interoception:
                        if hasattr(internal_sensing.interoception, 'affect'):
                            affective_monitor = internal_sensing.interoception.affect
                        # IntegratedInteroception uses .prediction (PredictiveInteroception).
                        # Keep backward-compatibility with any older attribute names.
                        if hasattr(internal_sensing.interoception, 'prediction'):
                            predictive_interoception = internal_sensing.interoception.prediction
                        elif hasattr(internal_sensing.interoception, 'predictive'):
                            predictive_interoception = internal_sensing.interoception.predictive
                        if hasattr(internal_sensing.interoception, 'epistemic_bridge'):
                            epistemic_bridge = internal_sensing.interoception.epistemic_bridge

                # Optional: LLM-based estimator for missing/low-quality RL signals.
                estimator = None
                try:
                    from .reasoning.rl_signal_estimators import LLMRLSignalEstimator
                    estimator = LLMRLSignalEstimator(
                        model=reasoning_config.llm_pattern_matching_model,
                        batch_size=reasoning_config.llm_pattern_matching_batch_size,
                        cache_size=reasoning_config.llm_pattern_matching_cache_size,
                    )
                except Exception:
                    estimator = None
                
                rl_signal_aggregator = RLSignalAggregator(
                    weight_dissonance=reasoning_config.rl_weight_dissonance,
                    weight_surprise=reasoning_config.rl_weight_surprise,
                    weight_curiosity=reasoning_config.rl_weight_curiosity,
                    weight_info_gain=reasoning_config.rl_weight_info_gain,
                    weight_coherence=reasoning_config.rl_weight_coherence,
                    cognitive_dissonance_monitor=cognitive_dissonance_monitor,
                    affective_monitor=affective_monitor,
                    predictive_interoception=predictive_interoception,
                    epistemic_bridge=epistemic_bridge,
                    estimator=estimator,
                )
                logger.info("✓ RL signal aggregator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize RL signal aggregator: {e}, continuing with dissonance-only feedback", exc_info=True)
        
        # Create feedback loop manager
        feedback_loop_manager = None
        if reasoning_config.feedback_loops_enabled:
            feedback_loop_manager = FeedbackLoopManager(
                reinforcing_enabled=reasoning_config.reinforcing_enabled,
                balancing_enabled=reasoning_config.balancing_enabled,
                metrics_window_size=reasoning_config.metrics_tracking_window,
                success_rate_threshold=reasoning_config.success_rate_threshold,
                error_rate_threshold=reasoning_config.error_rate_threshold,
                cognitive_dissonance_monitor=cognitive_dissonance_monitor,
                dissonance_threshold=reasoning_config.dissonance_threshold,
                learning_system=learning_tool,
                rl_signal_aggregator=rl_signal_aggregator,
                rl_signals_enabled=reasoning_config.rl_signals_enabled,
                surprise_threshold=reasoning_config.rl_surprise_threshold,
                curiosity_threshold=reasoning_config.rl_curiosity_threshold,
                exploration_ratio=reasoning_config.rl_exploration_ratio,
            )
            logger.info("✓ Feedback loop manager initialized")
        
        # Initialize hierarchical control if enabled
        hierarchical_controller = None
        if reasoning_config.hierarchical_control_enabled:
            try:
                from .reasoning.hierarchical_control import HierarchicalController
                hierarchical_controller = HierarchicalController(
                    goal_manager=None,  # Will be set after goal manager is created
                    strategic_threshold=reasoning_config.strategic_threshold,
                    tactical_threshold=reasoning_config.tactical_threshold
                )
                logger.info("✓ Hierarchical controller initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize hierarchical controller: {e}", exc_info=True)
        
        # Initialize recursive reasoning engine if enabled
        recursive_reasoning_engine = None
        if reasoning_config.recursive_reasoning_enabled:
            try:
                from .reasoning.recursive_reasoning import RecursiveReasoningEngine
                recursive_reasoning_engine = RecursiveReasoningEngine(
                    max_depth=reasoning_config.max_recursion_depth,
                    timeout_seconds=reasoning_config.recursion_timeout_seconds,
                    working_memory=None,  # Will be set after working memory is created
                    rule_engine=None  # Will be set after rule engine is created
                )
                logger.info("✓ Recursive reasoning engine initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize recursive reasoning engine: {e}", exc_info=True)
        
        # Initialize metacognitive loops if enabled
        metacognitive_loop = None
        if reasoning_config.recursive_reasoning_enabled:
            try:
                from .reasoning.metacognitive_loops import MetacognitiveLoop
                # Get epistemic engine if available
                epistemic_engine_for_meta = None
                if hasattr(self_model, 'epistemic_layer') and self_model.epistemic_layer:
                    try:
                        from .self_model.epistemic.engine import MetacognitiveEngine
                        if internal_sensing and hasattr(internal_sensing, 'epistemic_engine'):
                            epistemic_engine_for_meta = internal_sensing.epistemic_engine
                        else:
                            epistemic_engine_for_meta = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
                    except Exception:
                        pass
                
                metacognitive_loop = MetacognitiveLoop(
                    epistemic_engine=epistemic_engine_for_meta,
                    recursive_reasoning=recursive_reasoning_engine,
                    max_monitoring_depth=2
                )
                logger.info("✓ Metacognitive loop initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize metacognitive loop: {e}", exc_info=True)
        
        # Initialize nested feedback system if enabled
        nested_feedback_system = None
        if reasoning_config.feedback_loops_enabled:
            try:
                from .reasoning.nested_feedback import NestedFeedbackSystem, NestedFeedbackConfig
                nested_config = NestedFeedbackConfig(
                    fast_interval=0.1,
                    medium_interval=5.0,
                    slow_interval=60.0
                )
                nested_feedback_system = NestedFeedbackSystem(
                    config=nested_config,
                    feedback_loop_manager=None,  # Will be set after feedback loop manager is created
                    cognitive_dissonance_monitor=None  # Will be set after dissonance monitor is created
                )
                logger.info("✓ Nested feedback system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize nested feedback system: {e}", exc_info=True)
        
        # Initialize MPC controller if enabled
        mpc_controller = None
        if app_config and app_config.control.mpc_enabled:
            try:
                from .control.mpc_controller import MPCController
                mpc_controller = MPCController(
                    goal_manager=None,  # Will be set after goal manager is created
                    config=None  # Uses defaults
                )
                logger.info("✓ MPC controller initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize MPC controller: {e}", exc_info=True)
        
        # Initialize distributed control if enabled
        distributed_control = None
        if app_config and app_config.control.distributed_control_enabled:
            try:
                from .control.distributed_control import DistributedControlSystem
                distributed_control = DistributedControlSystem(
                    goal_manager=None  # Will be set after goal manager is created
                )
                logger.info("✓ Distributed control system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize distributed control: {e}", exc_info=True)
        
        # Create reasoning tool
        reasoning_tool = ReasoningTool(
            declarative_memory=declarative_memory,
            spreading_activation=spreading_activation
        )
        
        # Create state manager if persistence is enabled
        state_manager = None
        if reasoning_config.state_persistence_enabled:
            try:
                state_manager = ReasoningStateManager(
                    state_file_path=reasoning_config.state_file_path
                )
                logger.info("✓ Reasoning state manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize state manager: {e}", exc_info=True)
        
        # Initialize emotional regulation components if internal sensing is available
        affect_monitor = None
        if internal_sensing and app_config and app_config.internal_sensing.emotional_regulation_enabled:
            try:
                from .internal_sensing.emotional_appraisal import CognitiveAppraisalEngine
                from .internal_sensing.emotional_regulation import HomeostaticEmotionalRegulator
                
                # Get affect monitor from internal sensing framework
                affect_monitor = internal_sensing.interoception.affect
                
                # Create emotional appraisal engine
                emotional_appraisal_engine = CognitiveAppraisalEngine()
                affect_monitor.set_emotional_appraisal_engine(emotional_appraisal_engine)
                
                # Create emotional regulator
                emotional_regulator = HomeostaticEmotionalRegulator(
                    target_valence=app_config.internal_sensing.target_valence,
                    target_arousal=app_config.internal_sensing.target_arousal,
                    target_curiosity=app_config.internal_sensing.target_curiosity,
                    kp_valence=app_config.internal_sensing.pid_kp_valence,
                    ki_valence=app_config.internal_sensing.pid_ki_valence,
                    kd_valence=app_config.internal_sensing.pid_kd_valence,
                    kp_arousal=app_config.internal_sensing.pid_kp_arousal,
                    ki_arousal=app_config.internal_sensing.pid_ki_arousal,
                    kd_arousal=app_config.internal_sensing.pid_kd_arousal
                )
                affect_monitor.set_emotional_regulator(emotional_regulator)
                
                logger.info("✓ Emotional regulation components initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize emotional regulation: {e}", exc_info=True)
        
        # Wire hierarchical controller to goal manager
        if hierarchical_controller and reasoning_tool.goal_manager:
            hierarchical_controller.goal_manager = reasoning_tool.goal_manager
            reasoning_tool.hierarchical_controller = hierarchical_controller
        
        # Wire recursive reasoning to rule engine
        if recursive_reasoning_engine and reasoning_tool.rule_engine:
            recursive_reasoning_engine.rule_engine = reasoning_tool.rule_engine
            if reasoning_tool.rule_system.working_memory:
                recursive_reasoning_engine.working_memory = reasoning_tool.rule_system.working_memory
            reasoning_tool.recursive_reasoning_engine = recursive_reasoning_engine
        
        # Wire nested feedback to feedback loop manager
        if nested_feedback_system and feedback_loop_manager:
            nested_feedback_system.feedback_loop_manager = feedback_loop_manager
            nested_feedback_system.cognitive_dissonance_monitor = cognitive_dissonance_monitor
            reasoning_tool.nested_feedback_system = nested_feedback_system
        
        # Wire MPC controller to goal manager
        if mpc_controller and reasoning_tool.goal_manager:
            mpc_controller.goal_manager = reasoning_tool.goal_manager
            reasoning_tool.mpc_controller = mpc_controller
        
        # Wire distributed control to goal manager
        if distributed_control and reasoning_tool.goal_manager:
            distributed_control.goal_manager = reasoning_tool.goal_manager
            reasoning_tool.distributed_control = distributed_control
        
        # Wire feedback loop and cognitive dissonance components to reasoning tool
        # Store as attributes for access by daemon/world state aggregator
        if feedback_loop_manager:
            reasoning_tool.feedback_loop_manager = feedback_loop_manager
        if cognitive_dissonance_monitor:
            reasoning_tool.cognitive_dissonance_monitor = cognitive_dissonance_monitor
            # Wire goal_manager to cognitive dissonance monitor now that reasoning_tool exists
            if reasoning_tool.goal_manager:
                cognitive_dissonance_monitor.goal_manager = reasoning_tool.goal_manager
            # Wire affective monitor for dissonance→coherence coupling
            if affective_monitor:
                cognitive_dissonance_monitor.set_affective_monitor(affective_monitor)
                logger.info("✓ Wired dissonance→coherence coupling via affective monitor")
        if self_model_feedback_loop:
            reasoning_tool.self_model_feedback_loop = self_model_feedback_loop
        if affect_monitor:
            reasoning_tool.affect_monitor = affect_monitor
        if metacognitive_loop:
            reasoning_tool.metacognitive_loop = metacognitive_loop
        
        # Create reasoning daemon if autonomous mode is enabled
        if reasoning_config.autonomous_enabled:
            try:
                daemon = ReasoningDaemon(
                    reasoning_tool=reasoning_tool,
                    state_manager=state_manager,
                    feedback_loop_manager=feedback_loop_manager,
                    self_model_feedback_loop=self_model_feedback_loop,
                    learning_tool=learning_tool,
                    affect_monitor=affect_monitor,
                    cycle_delay_seconds=reasoning_config.cycle_delay_seconds,
                    event_acceleration_enabled=reasoning_config.event_acceleration_enabled,
                    max_cycles_per_minute=reasoning_config.max_cycles_per_minute,
                    max_rules_per_cycle=reasoning_config.max_rules_per_cycle
                )
                reasoning_tool.daemon = daemon  # Wire daemon back into reasoning tool
                logger.info("✓ Reasoning daemon initialized")
                
                # Start the daemon
                try:
                    if daemon.start():
                        logger.info("✓ Reasoning daemon started")
                    else:
                        logger.warning("✗ Failed to start reasoning daemon")
                except Exception as e:
                    logger.error(f"Error starting reasoning daemon: {e}", exc_info=True)
            except Exception as e:
                logger.warning(f"Failed to initialize reasoning daemon: {e}", exc_info=True)
        
        # Wire learning tool to reasoning tool if available
        if learning_tool:
            reasoning_tool.learning_tool = learning_tool
        
        return reasoning_tool
        
    except Exception as e:
        logger.error(f"Error initializing reasoning system: {e}", exc_info=True)
        return None


def main() -> None:
    # Import config locally at the very start to avoid scoping issues
    # This ensures config is available before any methods that might import it locally
    try:
        from .config import config as app_config
    except ImportError:
        app_config = None
    
    setup_logging()

    # Detect workspace root (parent of broca package directory)
    workspace_root = Path(__file__).parent.parent.resolve()
    logger.info(f"Detected workspace root: {workspace_root}")

    # Initialize storage
    conversation_storage = _initialize_storage()
    if conversation_storage:
        logger.info("✓ Conversation storage initialized successfully")
    else:
        logger.warning("✗ Conversation storage initialization failed or disabled")
    
    # Initialize memory manager
    memory_manager = _initialize_memory_manager()
    if memory_manager:
        logger.info("✓ Memory manager initialized successfully")
    else:
        logger.warning("✗ Memory manager initialization failed or disabled - will not be included in world state")
    
    # Initialize self-model system
    self_model, self_model_storage, epistemic_engine = _initialize_self_model()
    if self_model:
        logger.info("✓ Self-model initialized successfully")
    else:
        logger.warning("✗ Self-model initialization failed or disabled - will not be included in world state")
    
    # Initialize internal sensing system
    internal_sensing = _initialize_internal_sensing(
        embedding_service=memory_manager.embedding_service if memory_manager else None,
        epistemic_engine=epistemic_engine,
    )
    if internal_sensing:
        logger.info("✓ Internal sensing framework initialized successfully")
    else:
        logger.warning("✗ Internal sensing framework initialization failed or disabled - will not be included in world state")
    
    # Initialize environment access system
    environment_system = _initialize_environment_system()
    if environment_system:
        logger.info("✓ Environment access system initialized successfully")
    else:
        logger.debug("Environment access system disabled or failed to initialize")
    
    try:
        # Initialize tool registry (with memory manager, epistemic engine, self_model and storage if available)
        tool_registry = _initialize_tool_registry(
            memory_manager=memory_manager,
            epistemic_engine=epistemic_engine,
            self_model=self_model,
            storage=self_model_storage,
            internal_sensing=internal_sensing
        )
        if tool_registry:
            logger.info("✓ Tool registry initialized successfully")
        else:
            logger.warning("✗ Tool registry initialization failed or disabled")
        
        # Register self-model tools if self-model system is enabled (CRUD tool already registered in _initialize_tool_registry)
        # Additional tools can be registered here if needed
        pass
        
        # Internal sensing tools are NOT registered as tools since internal sensing data
        # is already included in the LLM's mutable system prompt via WorldStateAggregator.
        
        # Register environment access tool if environment system is enabled
        if environment_system and tool_registry:
            try:
                from .environment.tools.environment_tool import EnvironmentAccessTool
                env_tool = EnvironmentAccessTool(access_system=environment_system)
                tool_registry.register_tool(env_tool)
                logger.info("Registered environment access tool")
            except Exception as e:
                logger.warning(f"Failed to register environment access tool: {e}", exc_info=True)
        
        # Create directory structure generator for workspace
        directory_structure_generator = None
        try:
            from .world_state.directory_structure import DirectoryStructureGenerator
            directory_structure_generator = DirectoryStructureGenerator(root_path=str(workspace_root))
            logger.info(f"✓ Directory structure generator initialized successfully for workspace: {workspace_root}")
        except Exception as e:
            logger.warning(f"✗ Failed to initialize directory structure generator: {e} - will not be included in world state", exc_info=True)
        
        # Log world state component summary before creating aggregator
        components_summary = []
        if internal_sensing:
            components_summary.append("internal_sensing")
        if self_model:
            components_summary.append("self_model")
        if tool_registry:
            components_summary.append("tool_registry")
        if memory_manager:
            components_summary.append("memory_manager")
        if directory_structure_generator:
            components_summary.append("directory_structure")
        
        logger.info(
            f"World state aggregator will include: {', '.join(components_summary) if components_summary else 'system_info only'}. "
            f"Reduction level: {app_config.self_model.self_model_reduction_level if app_config else 'default'}"
        )
        
        # Initialize reasoning system with cognitive dissonance integration
        reasoning_tool = None
        rl_signal_aggregator = None
        skill_manager = None
        goal_manager = None
        if app_config and app_config.reasoning.enabled:
            try:
                reasoning_tool = _initialize_reasoning_system(
                    memory_manager=memory_manager,
                    self_model=self_model,
                    self_model_storage=self_model_storage,
                    internal_sensing=internal_sensing
                )
                if reasoning_tool:
                    logger.info("✓ Reasoning system initialized successfully")
                    
                    # Extract components for tool selection guidance
                    if hasattr(reasoning_tool, 'feedback_loop_manager') and reasoning_tool.feedback_loop_manager:
                        rl_signal_aggregator = getattr(reasoning_tool.feedback_loop_manager, 'rl_signal_aggregator', None)
                    if hasattr(reasoning_tool, 'goal_manager'):
                        goal_manager = reasoning_tool.goal_manager
                    
                    # Get skill manager if available (from learning tool)
                    if hasattr(reasoning_tool, 'learning_tool') and reasoning_tool.learning_tool:
                        if hasattr(reasoning_tool.learning_tool, 'skill_manager'):
                            skill_manager = reasoning_tool.learning_tool.skill_manager
                    
                    # Wire learning tool from reasoning system to tool registry for automatic observation
                    if tool_registry and hasattr(reasoning_tool, 'learning_tool') and reasoning_tool.learning_tool:
                        try:
                            tool_registry.set_learning_tool(reasoning_tool.learning_tool)
                            logger.info("✓ Learning tool (from reasoning) wired to tool registry for automatic observation")
                        except Exception as e:
                            logger.warning(f"Failed to wire reasoning learning tool to tool registry: {e}", exc_info=True)
                    
                    # Register reasoning tool in tool registry
                    if tool_registry:
                        try:
                            tool_registry.register_tool(reasoning_tool)
                            logger.info("Registered reasoning tool")
                        except Exception as e:
                            logger.warning(f"Failed to register reasoning tool: {e}", exc_info=True)
                    
                    # Register learning tool if available
                    if tool_registry and hasattr(reasoning_tool, 'learning_tool') and reasoning_tool.learning_tool:
                        try:
                            tool_registry.register_tool(reasoning_tool.learning_tool)
                            logger.info("Registered learning tool")
                        except Exception as e:
                            logger.warning(f"Failed to register learning tool: {e}", exc_info=True)
                    
                    # Wire tool selection guidance if enabled and not already initialized
                    if (tool_registry and 
                        app_config and app_config.tools.selection_guidance_enabled and
                        (tool_registry.tool_selection_guidance is None or 
                         tool_registry.tool_selection_guidance.guidance_aggregator.reasoning_tool is None)):
                        try:
                            from .tools.selection_guidance import ToolSelectionGuidance
                            # Update or create guidance with reasoning components
                            if tool_registry.tool_selection_guidance is None:
                                from .tools.selection_guidance import ValidationStrictness
                                
                                # Map config string to enum
                                strictness_map = {
                                    "advisory": ValidationStrictness.ADVISORY,
                                    "soft_block": ValidationStrictness.SOFT_BLOCK,
                                    "hard_block": ValidationStrictness.HARD_BLOCK,
                                }
                                validation_strictness = strictness_map.get(
                                    app_config.tools.validation_strictness if app_config else "advisory",
                                    ValidationStrictness.ADVISORY
                                )
                                
                                tool_registry.tool_selection_guidance = ToolSelectionGuidance(
                                    reasoning_tool=reasoning_tool,
                                    rl_signal_aggregator=rl_signal_aggregator,
                                    skill_manager=skill_manager,
                                    goal_manager=goal_manager,
                                    max_guidance_length=app_config.tools.max_guidance_length if app_config else 2000,
                                    guidance_text_style=app_config.tools.guidance_text_style if app_config else "prioritized",
                                    ranking_algorithm=app_config.tools.ranking_algorithm if app_config else "simple",
                                    validation_strictness=validation_strictness,
                                    validation_confidence_threshold=app_config.tools.validation_confidence_threshold if app_config else 0.7,
                                    context_cache_ttl_seconds=app_config.tools.context_cache_ttl_seconds if app_config else 5,
                                    exploration_factor=app_config.tools.exploration_factor if app_config else 0.1,
                                )
                                
                                # Initialize metrics if enabled
                                if app_config and app_config.tools.metrics_enabled:
                                    try:
                                        from .tools.selection_metrics import ToolSelectionMetrics
                                        metrics = ToolSelectionMetrics(window_size=app_config.tools.metrics_window_size)
                                        tool_registry.tool_selection_guidance.set_metrics(metrics)
                                    except Exception as e:
                                        logger.warning(f"Failed to initialize tool selection metrics: {e}", exc_info=True)
                                logger.info("✓ Tool selection guidance initialized with reasoning components")
                            else:
                                # Update existing guidance with reasoning components
                                tool_registry.tool_selection_guidance.guidance_aggregator.reasoning_tool = reasoning_tool
                                tool_registry.tool_selection_guidance.guidance_aggregator.rl_signal_aggregator = rl_signal_aggregator
                                tool_registry.tool_selection_guidance.guidance_aggregator.skill_manager = skill_manager
                                tool_registry.tool_selection_guidance.guidance_aggregator.goal_manager = goal_manager
                                logger.info("✓ Tool selection guidance updated with reasoning components")
                        except Exception as e:
                            logger.warning(f"Failed to wire tool selection guidance: {e}", exc_info=True)
                else:
                    logger.warning("✗ Reasoning system initialization failed or disabled")
            except Exception as e:
                logger.warning(f"Failed to initialize reasoning system: {e}", exc_info=True)
                reasoning_tool = None
        
        # Initialize LLM ensemble components if enabled
        model_router = None
        llm_ensemble = None
        recursive_prompting = None
        if app_config and app_config.llm_ensemble.enabled:
            try:
                from .llm.model_router import ModelRouter
                from .llm.ensemble import LLMEnsemble, EnsembleStrategy
                from .llm.recursive_prompting import RecursivePromptingSystem
                from .llm import create_llm_client
                
                # Create model router with primary LLM client
                primary_client = create_llm_client()
                models_dict = {app_config.llm.model if app_config else "deepseek-chat": primary_client}
                
                model_router = ModelRouter(models=models_dict)
                logger.info("✓ Model router initialized")
                
                # Create LLM ensemble
                default_strategy_name = app_config.llm_ensemble.default_strategy if app_config else "weighted"
                llm_ensemble = LLMEnsemble(
                    model_router=model_router,
                    default_strategy=EnsembleStrategy[default_strategy_name.upper()] if hasattr(EnsembleStrategy, default_strategy_name.upper()) else EnsembleStrategy.WEIGHTED
                )
                logger.info("✓ LLM ensemble initialized")
                
                # Create recursive prompting system
                recursive_prompting = RecursivePromptingSystem(
                    llm_client=primary_client,
                    ensemble=llm_ensemble,
                    max_iterations=3,
                    max_depth=2
                )
                logger.info("✓ Recursive prompting system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM ensemble components: {e}", exc_info=True)
        
        # Initialize systems components if enabled
        system_dynamics = None
        system_health_monitor = None
        reconfiguration_manager = None
        if app_config and (app_config.systems.dynamics_enabled or app_config.systems.health_monitoring_enabled):
            try:
                from .systems.dynamics import SystemDynamicsModel
                from .systems.health_monitor import SystemHealthMonitor
                from .systems.reconfiguration import ReconfigurationManager
                
                # Initialize system dynamics
                if app_config.systems.dynamics_enabled:
                    system_dynamics = SystemDynamicsModel(
                        feedback_loop_manager=None,  # Will be set after feedback loop manager is created
                        cognitive_dissonance_monitor=None  # Will be set after dissonance monitor is created
                    )
                    logger.info("✓ System dynamics model initialized")
                
                # Initialize health monitor
                if app_config.systems.health_monitoring_enabled:
                    system_health_monitor = SystemHealthMonitor(
                        system_dynamics=system_dynamics,
                        health_threshold_warning=app_config.systems.health_threshold_warning,
                        health_threshold_critical=app_config.systems.health_threshold_critical,
                        stability_threshold=app_config.systems.stability_threshold
                    )
                    logger.info("✓ System health monitor initialized")
                    
                    # Initialize reconfiguration manager
                    if app_config.systems.reconfiguration_enabled:
                        reconfiguration_manager = ReconfigurationManager(
                            health_monitor=system_health_monitor
                        )
                        logger.info("✓ Reconfiguration manager initialized")
                
                # Wire system dynamics to feedback loops and dissonance monitor
                if system_dynamics:
                    system_dynamics.feedback_loop_manager = feedback_loop_manager
                    system_dynamics.cognitive_dissonance_monitor = cognitive_dissonance_monitor
                    
            except Exception as e:
                logger.warning(f"Failed to initialize systems components: {e}", exc_info=True)
        
        # Initialize recursive self-improvement if enabled
        recursive_improvement = None
        if app_config and app_config.learning.enabled:
            try:
                from .learning.recursive_improvement import RecursiveSelfImprovement
                from .self_model.updater import SelfModelUpdater
                from .llm import create_llm_client
                
                # Get skill manager from learning tool if available
                skill_manager = None
                if learning_tool and hasattr(learning_tool, 'skill_manager'):
                    skill_manager = learning_tool.skill_manager
                
                # Get self model updater
                self_model_updater_for_improvement = None
                if self_model_updater:
                    self_model_updater_for_improvement = self_model_updater
                elif self_model_storage:
                    self_model_updater_for_improvement = SelfModelUpdater(llm_client=create_llm_client())
                
                recursive_improvement = RecursiveSelfImprovement(
                    skill_manager=skill_manager,
                    self_model_updater=self_model_updater_for_improvement,
                    max_improvement_depth=2
                )
                logger.info("✓ Recursive self-improvement initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize recursive self-improvement: {e}", exc_info=True)
        
        # Wire systems components to reasoning tool
        if reasoning_tool:
            if system_dynamics:
                reasoning_tool.system_dynamics = system_dynamics
            if system_health_monitor:
                reasoning_tool.system_health_monitor = system_health_monitor
            if reconfiguration_manager:
                reasoning_tool.reconfiguration_manager = reconfiguration_manager
            if recursive_improvement:
                reasoning_tool.recursive_improvement = recursive_improvement
        
        # Initialize learning tool independently if enabled (regardless of reasoning integration)
        learning_tool_standalone = None
        if app_config and app_config.learning.enabled:
            try:
                from .learning.integration_tool import LearningTool
                learning_tool_standalone = LearningTool()
                logger.info("✓ Learning tool initialized")
                
                # Register learning tool in tool registry if not already registered
                if tool_registry:
                    # Check if learning tool was already registered via reasoning system
                    existing_learning_tool = tool_registry.get_tool("learning")
                    if not existing_learning_tool:
                        try:
                            tool_registry.register_tool(learning_tool_standalone)
                            logger.info("Registered learning tool")
                        except ValueError as e:
                            # Tool already registered (shouldn't happen but handle gracefully)
                            logger.debug(f"Learning tool already registered: {e}")
                        except Exception as e:
                            logger.warning(f"Failed to register learning tool: {e}", exc_info=True)
                
                # Wire learning_tool to tool_registry for automatic observation
                if tool_registry and learning_tool_standalone:
                    try:
                        tool_registry.set_learning_tool(learning_tool_standalone)
                        logger.info("✓ Learning tool wired to tool registry for automatic observation")
                    except Exception as e:
                        logger.warning(f"Failed to wire learning tool to tool registry: {e}", exc_info=True)
            except Exception as e:
                logger.warning(f"Failed to initialize learning tool: {e}", exc_info=True)
        
        # Initialize self-model size manager if enabled
        size_manager = None
        if self_model and app_config and app_config.self_model.size_management_enabled:
            try:
                from .self_model.size_manager import SelfModelSizeManager, SizeLimits
                limits = SizeLimits(
                    max_capabilities=app_config.self_model.max_capabilities,
                    max_knowledge_boundaries=app_config.self_model.max_knowledge_boundaries,
                    max_constraints=app_config.self_model.max_constraints,
                    soft_capabilities=app_config.self_model.soft_capabilities,
                    soft_knowledge_boundaries=app_config.self_model.soft_knowledge_boundaries,
                    soft_constraints=app_config.self_model.soft_constraints
                )
                size_manager = SelfModelSizeManager(
                    limits=limits,
                    epistemic_engine=epistemic_engine
                )
                logger.info("✓ Self-model size manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize self-model size manager: {e}", exc_info=True)
        
        # Create world state aggregator with new components
        world_state_aggregator = WorldStateAggregator(
            internal_sensing=internal_sensing,
            self_model=self_model,
            tool_registry=tool_registry,
            memory_manager=memory_manager,
            directory_structure_generator=directory_structure_generator,
            self_model_reduction_level=app_config.self_model.self_model_reduction_level if app_config else "medium",
            reasoning_tool=reasoning_tool,
            size_manager=size_manager,
            config=app_config,
        )
        
        # Extract cognitive architecture components from reasoning tool for world state aggregator
        hierarchical_controller = None
        recursive_reasoning_engine = None
        metacognitive_loop = None
        nested_feedback_system = None
        mpc_controller = None
        distributed_control = None
        
        if reasoning_tool:
            hierarchical_controller = getattr(reasoning_tool, 'hierarchical_controller', None)
            recursive_reasoning_engine = getattr(reasoning_tool, 'recursive_reasoning_engine', None)
            metacognitive_loop = getattr(reasoning_tool, 'metacognitive_loop', None)
            nested_feedback_system = getattr(reasoning_tool, 'nested_feedback_system', None)
            mpc_controller = getattr(reasoning_tool, 'mpc_controller', None)
            distributed_control = getattr(reasoning_tool, 'distributed_control', None)
        
        # Store new components in aggregator for world state inclusion
        if hasattr(world_state_aggregator, '__dict__'):
            world_state_aggregator.hierarchical_controller = hierarchical_controller
            world_state_aggregator.recursive_reasoning_engine = recursive_reasoning_engine
            world_state_aggregator.metacognitive_loop = metacognitive_loop
            world_state_aggregator.nested_feedback_system = nested_feedback_system
            world_state_aggregator.system_dynamics = system_dynamics
            world_state_aggregator.system_health_monitor = system_health_monitor
            world_state_aggregator.mpc_controller = mpc_controller
            world_state_aggregator.distributed_control = distributed_control
            world_state_aggregator.llm_ensemble = llm_ensemble
            world_state_aggregator.recursive_prompting = recursive_prompting
            world_state_aggregator.recursive_improvement = recursive_improvement
        
        # Initialize color manager
        try:
            from .repl.color_profile import ColorManager, CustomColorProfile
            color_manager = ColorManager()
            
            # Load profile from config
            if app_config:
                color_config = app_config.repl_color
                if color_config.profile == "custom" and (
                    color_config.custom_brocaos_prompt or
                    color_config.custom_response_text or
                    color_config.custom_you_prompt or
                    color_config.custom_input_text
                ):
                    custom_profile = CustomColorProfile(
                        brocaos_prompt=color_config.custom_brocaos_prompt,
                        response_text=color_config.custom_response_text,
                        you_prompt=color_config.custom_you_prompt,
                        input_text=color_config.custom_input_text
                    )
                    color_manager.set_custom_profile(custom_profile)
                
                color_manager.set_profile(color_config.profile)
        except Exception as e:
            logger.debug(f"Failed to initialize color manager: {e}", exc_info=True)
            color_manager = None
        
        # Extract PEA loop managers from reasoning_tool if available
        goal_manager = None
        skill_manager = None
        experience_logger = None
        
        if reasoning_tool:
            if hasattr(reasoning_tool, 'goal_manager'):
                goal_manager = reasoning_tool.goal_manager
            if hasattr(reasoning_tool, 'learning_tool') and reasoning_tool.learning_tool:
                if hasattr(reasoning_tool.learning_tool, 'skill_manager'):
                    skill_manager = reasoning_tool.learning_tool.skill_manager
                if hasattr(reasoning_tool.learning_tool, 'experience_logger'):
                    experience_logger = reasoning_tool.learning_tool.experience_logger
        
        session = ConversationSession(
            system_prompt=None,
            storage=conversation_storage,
            tool_registry=tool_registry,
            internal_sensing_framework=internal_sensing,
            world_state_aggregator=world_state_aggregator,
            color_manager=color_manager,
            goal_manager=goal_manager,
            skill_manager=skill_manager,
            experience_logger=experience_logger,
        )
        
        # PEA/PFREA removed - planning is now handled via planning tool

        provider_name = (app_config.llm.provider if app_config else "deepseek").upper()
        storage_status = "enabled" if conversation_storage else "disabled"
        tools_status = "enabled" if tool_registry else "disabled"
        memory_status = "enabled" if memory_manager else "disabled"
        self_model_status = "enabled" if self_model else "disabled"
        sensing_status = "enabled" if internal_sensing else "disabled"
        print(f"BrocaOS REPL ({provider_name} backend). Storage: {storage_status}, Tools: {tools_status}, Memory: {memory_status}, Self-Model: {self_model_status}, Internal Sensing: {sensing_status}. Type /exit to quit, /reset to clear context.\n")

        while True:
            try:
                # Pause spinner updates before user input to prevent interference
                # This stops all spinner threads and clears any partial output
                if session.tool_status_display:
                    session.tool_status_display.pause_updates()
                
                # Use plain prompt for input - readline works perfectly with plain prompts
                # Colors are kept for output only to avoid readline/ANSI code conflicts
                you_prompt = "you> "
                
                # Get user input with plain prompt
                user_input = input(you_prompt).strip()
                
                # Ensure stdout is flushed and terminal is ready for streaming output
                # This is critical - after input(), the terminal needs to be in the right state
                # for streaming output to appear immediately
                sys.stdout.flush()
                
                # Resume spinner updates after user input
                if session.tool_status_display:
                    session.tool_status_display.resume_updates()
            except (EOFError, KeyboardInterrupt):
                # Resume on exception too
                if session.tool_status_display:
                    session.tool_status_display.resume_updates()
                print("\nExiting.")
                break

            if not user_input:
                continue

            if user_input in ("/exit", "/quit"):
                print("Bye.")
                break

            if user_input == "/reset":
                # Recreate the session to drop history (new session ID, fresh start)
                # Note: Memories persist across resets
                # Extract PEA loop managers from reasoning_tool if available
                goal_manager = None
                skill_manager = None
                experience_logger = None
                
                if reasoning_tool:
                    if hasattr(reasoning_tool, 'goal_manager'):
                        goal_manager = reasoning_tool.goal_manager
                    if hasattr(reasoning_tool, 'learning_tool') and reasoning_tool.learning_tool:
                        if hasattr(reasoning_tool.learning_tool, 'skill_manager'):
                            skill_manager = reasoning_tool.learning_tool.skill_manager
                        if hasattr(reasoning_tool.learning_tool, 'experience_logger'):
                            experience_logger = reasoning_tool.learning_tool.experience_logger
                
                session = ConversationSession(
                    system_prompt=None,
                    storage=conversation_storage,
                    tool_registry=tool_registry,
                    internal_sensing_framework=internal_sensing,
                    world_state_aggregator=world_state_aggregator,
                    color_manager=color_manager,
                    goal_manager=goal_manager,
                    skill_manager=skill_manager,
                    experience_logger=experience_logger,
                )
                
                # PEA/PFREA removed - planning is now handled via planning tool
                
                print("[context reset]")
                continue

            # Normal turn
            try:
                # PEA/PFREA removed - planning is now handled via planning tool
                
                # Enable streaming by default (can be disabled via config)
                # The session.send() method handles all printing:
                # - When streaming is used, it prints during streaming with "BrocaOS> " prefix
                # - When streaming is not used, it prints the response with "BrocaOS> " prefix
                # So we don't need to print here - session.send() handles it all
                stream_enabled = app_config.llm.streaming_enabled if app_config else True
                reply = session.send(user_input, stream=stream_enabled)
                
                # PEA/PFREA removed - planning is now handled via planning tool
                
                # Response is already printed by session.send(), no need to print again
            except Exception as e:
                logger.error(f"Error in conversation turn: {e}", exc_info=True)
                prompt = "BrocaOS> "
                if color_manager:
                    prompt = color_manager.colorize(prompt, "brocaos_prompt")
                print(f"{prompt}Error: {str(e)}\n")
                print("You can continue the conversation or use /reset to start fresh.\n")
    finally:
        # Shutdown RL policy ranker to save state
        if tool_registry is not None and tool_registry.online_policy_ranker is not None:
            try:
                tool_registry.online_policy_ranker.shutdown()
                logger.info("OnlinePolicyRanker shutdown and state saved")
            except Exception as e:
                logger.error(f"Error shutting down OnlinePolicyRanker: {e}", exc_info=True)
        
        # Ensure memory manager is closed and vector index is saved
        if memory_manager is not None:
            try:
                memory_manager.close()
                logger.info("Memory manager closed and vector index saved")
            except Exception as e:
                logger.error(f"Error closing memory manager: {e}", exc_info=True)


if __name__ == "__main__":
    main()
