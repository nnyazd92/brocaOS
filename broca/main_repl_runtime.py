from dataclasses import dataclass
from pathlib import Path
from typing import Any
import logging

from .logging_config import setup_logging
from .repl.session import ConversationSession
from .storage import ConversationStorage
from .memory.manager import MemoryManager
from .self_model.model import SelfModel
from .internal_sensing.framework import InternalSensingFramework
from .world_state.aggregator import WorldStateAggregator
from .tools.registry import ToolRegistry
from .tools.self_model_tool import QuerySelfModelTool
from .config import config

from .main_repl import (
    _initialize_storage,
    _initialize_memory_manager,
    _initialize_self_model,
    _initialize_internal_sensing,
    _initialize_environment_system,
)

logger = logging.getLogger(__name__)


@dataclass
class BrocaRuntime:
    session: ConversationSession
    conversation_storage: ConversationStorage | None
    memory_manager: MemoryManager | None
    self_model: SelfModel | None
    internal_sensing: InternalSensingFramework | None
    world_state_aggregator: WorldStateAggregator | None
    tool_registry: ToolRegistry | None
    environment_system: Any | None


def initialize_runtime() -> BrocaRuntime:
    """Initialize the BrocaOS runtime for non-REPL surfaces (e.g. web API).

    This mirrors the initialization path in main_repl.main(), but returns a
    ConversationSession and its core components instead of starting the
    terminal loop.
    """
    setup_logging()

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

    # Tool registry
    from .main_repl import _initialize_tool_registry  # type: ignore

    try:
        tool_registry = _initialize_tool_registry(
            memory_manager=memory_manager,
            epistemic_engine=epistemic_engine,
            self_model=self_model,
            storage=self_model_storage,
            internal_sensing=internal_sensing,
        )
        if tool_registry:
            logger.info("✓ Tool registry initialized successfully")
        else:
            logger.warning("✗ Tool registry initialization failed or disabled")
    except Exception as e:
        logger.warning(f"Failed to initialize tool registry: {e}", exc_info=True)
        tool_registry = None

    # Self-model tool
    if self_model and self_model_storage and tool_registry:
        try:
            query_tool = QuerySelfModelTool(self_model, self_model_storage)
            tool_registry.register_tool(query_tool)
            logger.info("Registered self-model query tool")
        except Exception as e:
            logger.warning(f"Failed to register self-model query tool: {e}", exc_info=True)
    
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
        directory_structure_generator = None
    
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
        f"Reduction level: {config.self_model.self_model_reduction_level}"
    )

    world_state_aggregator = WorldStateAggregator(
        internal_sensing=internal_sensing,
        self_model=self_model,
        tool_registry=tool_registry,
        memory_manager=memory_manager,
        directory_structure_generator=directory_structure_generator,
        self_model_reduction_level=config.self_model.self_model_reduction_level,
    )

    # Initialize color manager
    try:
        from .repl.color_profile import ColorManager, CustomColorProfile
        color_manager = ColorManager()
        
        # Load profile from config
        color_config = config.repl_color
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

    session = ConversationSession(
        system_prompt=None,
        storage=conversation_storage,
        tool_registry=tool_registry,
        internal_sensing_framework=internal_sensing,
        world_state_aggregator=world_state_aggregator,
        color_manager=color_manager,
    )

    return BrocaRuntime(
        session=session,
        conversation_storage=conversation_storage,
        memory_manager=memory_manager,
        self_model=self_model,
        internal_sensing=internal_sensing,
        world_state_aggregator=world_state_aggregator,
        tool_registry=tool_registry,
        environment_system=environment_system,
    )
