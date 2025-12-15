import sys
import readline  # optional, for nicer REPL on Unix
import logging
from .logging_config import setup_logging
from .repl.session import ConversationSession
from .config import config
from .storage.json_storage import JSONFileStorage
from .storage import ConversationStorage
from .tools.registry import ToolRegistry
from .tools.web_search import WebSearchTool
from .tools.memory_tool import (
    StoreMemoryTool, RetrieveMemoriesTool, DeleteMemoryTool, UpdateMemoryTool,
    LinkMemoriesTool, GetRelatedMemoriesTool
)
from .tools.terminal import TerminalTool
from .memory.storage import MemoryStorage
from .memory.vector_index import VectorIndex
from .memory.embeddings import EmbeddingService
from .memory.manager import MemoryManager
from .self_model.model import SelfModel
from .self_model.consistency import ConsistencyChecker
from .self_model.updater import SelfModelUpdater
from .self_model.layer import ConsistencyLayer
from .tools.self_model_tool import QuerySelfModelTool, UpdateSelfModelTool
from .internal_sensing.framework import InternalSensingFramework
from .tools.internal_sensing_tool import QueryInternalStateTool, GetInteroceptiveReportTool
from .world_state.aggregator import WorldStateAggregator

logger = logging.getLogger(__name__)


def _initialize_storage() -> ConversationStorage | None:
    """
    Initialize storage backend based on configuration.
    
    Returns:
        Storage instance if successfully initialized, None otherwise.
    """
    try:
        if config.storage.storage_type == "json":
            storage = JSONFileStorage(storage_path=config.storage.storage_path)
            logger.info(f"Initialized {config.storage.storage_type} storage at {config.storage.storage_path}")
            return storage
        else:
            logger.warning(f"Unknown storage type: {config.storage.storage_type}, storage disabled")
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
    try:
        # Initialize embedding service
        try:
            embedding_service = EmbeddingService()
        except Exception as e:
            logger.warning(f"Failed to initialize embedding service: {e}, memory disabled", exc_info=True)
            return None
        
        # Initialize storage
        storage = MemoryStorage(db_path=config.memory.memory_db_path)
        
        # Initialize vector index
        try:
            vector_index = VectorIndex(
                dimension=config.memory.embedding_dimension,
                index_path=config.memory.vector_index_path
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
    consistency_layer: "ConsistencyLayer | None" = None
) -> ToolRegistry | None:
    """
    Initialize tool registry and register available tools.
    
    Args:
        memory_manager: Optional MemoryManager instance for memory tools
        epistemic_engine: Optional MetacognitiveEngine instance for epistemic tracking
        consistency_layer: Optional ConsistencyLayer for saving self-model after memory storage
    
    Returns:
        ToolRegistry instance if successfully initialized, None otherwise.
    """
    try:
        registry = ToolRegistry(epistemic_engine=epistemic_engine)
        
        # Register web search tool if enabled
        if config.tools.enable_web_search:
            if config.tools.tavily_api_key:
                try:
                    web_search_tool = WebSearchTool(api_key=config.tools.tavily_api_key)
                    registry.register_tool(web_search_tool)
                    logger.info("Registered web search tool")
                except Exception as e:
                    logger.warning(f"Failed to register web search tool: {e}", exc_info=True)
            else:
                logger.warning("Web search enabled but TAVILY_API_KEY not set, skipping web search tool")
        
        # Register memory tools if memory manager is available
        if memory_manager:
            try:
                store_tool = StoreMemoryTool(
                    memory_manager, 
                    epistemic_engine=epistemic_engine,
                    consistency_layer=consistency_layer
                )
                retrieve_tool = RetrieveMemoriesTool(memory_manager, epistemic_engine=epistemic_engine)
                delete_tool = DeleteMemoryTool(memory_manager)
                update_tool = UpdateMemoryTool(memory_manager)
                link_tool = LinkMemoriesTool(memory_manager)
                get_related_tool = GetRelatedMemoriesTool(memory_manager)
                registry.register_tool(store_tool)
                registry.register_tool(retrieve_tool)
                registry.register_tool(delete_tool)
                registry.register_tool(update_tool)
                registry.register_tool(link_tool)
                registry.register_tool(get_related_tool)
                logger.info("Registered memory tools")
            except Exception as e:
                logger.warning(f"Failed to register memory tools: {e}", exc_info=True)
        
        # Register terminal tool if enabled
        if config.tools.enable_terminal:
            try:
                terminal_tool = TerminalTool()
                registry.register_tool(terminal_tool)
                logger.info("Registered terminal tool")
            except Exception as e:
                logger.warning(f"Failed to register terminal tool: {e}", exc_info=True)
        
        # Register critic tool if enabled
        if config.tools.enable_critic:
            try:
                from .tools.critic import CriticTool
                critic_tool = CriticTool(
                    system_prompt_template=config.tools.critic_system_prompt_template
                )
                registry.register_tool(critic_tool)
                logger.info("Registered critic tool")
            except Exception as e:
                logger.warning(f"Failed to register critic tool: {e}", exc_info=True)
        
        # Register version control tool if enabled
        if config.tools.enable_version_control:
            try:
                from .tools.version_control import VersionControlTool
                repo_path = config.tools.version_control_repo_path
                version_control_tool = VersionControlTool(repo_path=repo_path)
                registry.register_tool(version_control_tool)
                logger.info("Registered version control tool")
            except Exception as e:
                logger.warning(f"Failed to register version control tool: {e}", exc_info=True)
        
        # Register project world state tool if enabled
        if config.tools.enable_project_world_state:
            try:
                from .tools.project_world_state import ProjectWorldStateTool
                project_root = config.tools.project_world_state_path
                world_state_tool = ProjectWorldStateTool(project_root=project_root)
                registry.register_tool(world_state_tool)
                logger.info("Registered project world state tool")
            except Exception as e:
                logger.warning(f"Failed to register project world state tool: {e}", exc_info=True)
        
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
) -> tuple[ConsistencyLayer | None, SelfModel | None, "MetacognitiveEngine | None"]:
    """
    Initialize self-model system if enabled.
    
    Args:
        storage_path_override: Optional path to override the config storage path (for testing)
        enable_epistemic_override: Optional override for enable_epistemic config (for testing)
    
    Returns:
        Tuple of (ConsistencyLayer instance or None, SelfModel instance or None, MetacognitiveEngine or None)
    """
    if not config.self_model.enabled:
        logger.debug("Self-model system is disabled")
        return None, None, None
    
    try:
        # Initialize storage using factory
        from .self_model.storage import create_storage
        storage_path = (
            storage_path_override or
            (config.self_model.sqlite_db_path 
             if config.self_model.storage_type == "sqlite" 
             else config.self_model.storage_path)
        )
        storage = create_storage(
            storage_type=config.self_model.storage_type,
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
            else config.self_model.enable_epistemic
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
        
        # Initialize checker and updater with optional custom prompts
        checker = ConsistencyChecker(
            check_prompt_template=config.self_model.consistency_check_prompt
        )
        updater = SelfModelUpdater(
            update_prompt_template=config.self_model.update_prompt
        )
        
        # Create consistency layer
        consistency_layer = ConsistencyLayer(
            self_model=self_model,
            storage=storage,
            checker=checker,
            updater=updater,
            strict_mode=config.self_model.strict_mode,
            auto_update=config.self_model.auto_update,
            max_iterations=config.self_model.max_iterations,
        )
        
        logger.info("Initialized self-model system")
        return consistency_layer, self_model, epistemic_engine
        
    except Exception as e:
        logger.warning(f"Failed to initialize self-model system: {e}, continuing without it", exc_info=True)
        return None, None, None


def _initialize_environment_system():
    """
    Initialize environment access system if enabled.
    
    Returns:
        EnvironmentAccessSystem instance or None
    """
    if not config.environment.enabled:
        logger.debug("Environment access system is disabled")
        return None
    
    try:
        from .environment.access_system import EnvironmentAccessSystem
        from .environment.access_types import AccessLevel
        
        # Determine initial access level
        initial_level = AccessLevel.SANDBOXED
        try:
            initial_level = AccessLevel[config.environment.access_level]
        except (KeyError, AttributeError):
            pass
        
        system = EnvironmentAccessSystem()
        system.policy_manager.current_level = initial_level
        
        # Discover and register sensors if enabled
        if config.environment.enable_sensors:
            system.discover_and_register_sensors()
            logger.info(f"Discovered and registered {len(system.sensor_registry.sensors)} sensors")
        
        logger.info("Initialized environment access system")
        return system
        
    except Exception as e:
        logger.warning(f"Failed to initialize environment system: {e}, continuing without it", exc_info=True)
        return None


def _initialize_internal_sensing() -> InternalSensingFramework | None:
    """
    Initialize internal sensing system if enabled.
    
    Returns:
        InternalSensingFramework instance or None
    """
    if not config.internal_sensing.enabled:
        logger.debug("Internal sensing system is disabled")
        return None
    
    try:
        framework = InternalSensingFramework(
            sampling_rate=config.internal_sensing.sampling_rate,
            history_window=config.internal_sensing.history_window,
        )
        
        # Enable/disable specific components based on config
        if not config.internal_sensing.enable_physiology:
            framework.interoception.physiology = None  # type: ignore
        if not config.internal_sensing.enable_cognitive:
            framework.interoception.cognition = None  # type: ignore
        if not config.internal_sensing.enable_affective:
            framework.interoception.affect = None  # type: ignore
        if not config.internal_sensing.enable_predictive:
            framework.interoception.prediction = None  # type: ignore
        
        logger.info("Initialized internal sensing system")
        return framework
        
    except Exception as e:
        logger.warning(f"Failed to initialize internal sensing system: {e}, continuing without it", exc_info=True)
        return None


def main() -> None:
    setup_logging()

    # Initialize storage
    storage = _initialize_storage()
    
    # Initialize memory manager
    memory_manager = _initialize_memory_manager()
    
    # Initialize self-model system
    consistency_layer, self_model, epistemic_engine = _initialize_self_model()
    
    # Initialize internal sensing system
    internal_sensing = _initialize_internal_sensing()
    
    # Initialize environment access system
    environment_system = _initialize_environment_system()
    
    try:
        # Initialize tool registry (with memory manager, epistemic engine, and consistency layer if available)
        tool_registry = _initialize_tool_registry(
            memory_manager=memory_manager,
            epistemic_engine=epistemic_engine,
            consistency_layer=consistency_layer
        )
        
        # Register self-model tools if self-model system is enabled
        if consistency_layer and tool_registry:
            try:
                query_tool = QuerySelfModelTool(consistency_layer)
                update_tool = UpdateSelfModelTool(consistency_layer)
                tool_registry.register_tool(query_tool)
                tool_registry.register_tool(update_tool)
                logger.info("Registered self-model tools")
            except Exception as e:
                logger.warning(f"Failed to register self-model tools: {e}", exc_info=True)
        
        # Register internal sensing tools if internal sensing is enabled
        if internal_sensing and tool_registry:
            try:
                query_state_tool = QueryInternalStateTool(internal_sensing)
                report_tool = GetInteroceptiveReportTool(internal_sensing)
                tool_registry.register_tool(query_state_tool)
                tool_registry.register_tool(report_tool)
                logger.info("Registered internal sensing tools")
            except Exception as e:
                logger.warning(f"Failed to register internal sensing tools: {e}", exc_info=True)
        
        # Register environment access tool if environment system is enabled
        if environment_system and tool_registry:
            try:
                from .environment.tools.environment_tool import EnvironmentAccessTool
                env_tool = EnvironmentAccessTool(access_system=environment_system)
                tool_registry.register_tool(env_tool)
                logger.info("Registered environment access tool")
            except Exception as e:
                logger.warning(f"Failed to register environment access tool: {e}", exc_info=True)

        # Get project world state tool if available
        project_world_state_tool = None
        if tool_registry:
            try:
                project_world_state_tool = tool_registry.get_tool("project_world_state")
            except Exception:
                pass  # Tool not registered, that's okay
        
        # Create world state aggregator
        world_state_aggregator = WorldStateAggregator(
            internal_sensing=internal_sensing,
            self_model=self_model,
            project_world_state_tool=project_world_state_tool,
            tool_registry=tool_registry,
        )
        
        session = ConversationSession(
            system_prompt=None,
            storage=storage,
            tool_registry=tool_registry,
            consistency_layer=consistency_layer,
            internal_sensing_framework=internal_sensing,
            world_state_aggregator=world_state_aggregator,
        )

        storage_status = "enabled" if storage else "disabled"
        tools_status = "enabled" if tool_registry else "disabled"
        memory_status = "enabled" if memory_manager else "disabled"
        self_model_status = "enabled" if consistency_layer else "disabled"
        sensing_status = "enabled" if internal_sensing else "disabled"
        print(f"BrocaOS REPL (DeepSeek backend). Storage: {storage_status}, Tools: {tools_status}, Memory: {memory_status}, Self-Model: {self_model_status}, Internal Sensing: {sensing_status}. Type /exit to quit, /reset to clear context.\n")

        while True:
            try:
                user_input = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
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
                session = ConversationSession(
                    system_prompt=None,
                    storage=storage,
                    tool_registry=tool_registry,
                    consistency_layer=consistency_layer,
                    internal_sensing_framework=internal_sensing,
                    world_state_aggregator=world_state_aggregator,
                )
                print("[context reset]")
                continue

            # Normal turn
            try:
                reply = session.send(user_input)
                print(f"llm> {reply}\n")
            except Exception as e:
                logger.error(f"Error in conversation turn: {e}", exc_info=True)
                print(f"llm> Error: {str(e)}\n")
                print("You can continue the conversation or use /reset to start fresh.\n")
    finally:
        # Ensure memory manager is closed and vector index is saved
        if memory_manager is not None:
            try:
                memory_manager.close()
                logger.info("Memory manager closed and vector index saved")
            except Exception as e:
                logger.error(f"Error closing memory manager: {e}", exc_info=True)


if __name__ == "__main__":
    main()
