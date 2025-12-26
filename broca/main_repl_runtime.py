from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

    conversation_storage = _initialize_storage()
    memory_manager = _initialize_memory_manager()
    self_model, self_model_storage, epistemic_engine = _initialize_self_model()
    internal_sensing = _initialize_internal_sensing(
        embedding_service=memory_manager.embedding_service if memory_manager else None
    )
    environment_system = _initialize_environment_system()

    # Tool registry
    from .main_repl import _initialize_tool_registry  # type: ignore

    tool_registry = _initialize_tool_registry(
        memory_manager=memory_manager,
        epistemic_engine=epistemic_engine,
        self_model=self_model,
        storage=self_model_storage,
        internal_sensing=internal_sensing,
    )

    # Self-model tool
    if self_model and self_model_storage and tool_registry:
        try:
            query_tool = QuerySelfModelTool(self_model, self_model_storage)
            tool_registry.register_tool(query_tool)
        except Exception:
            pass

    # Directory structure / world state aggregator
    directory_structure_generator = None
    try:
        from .world_state.directory_structure import DirectoryStructureGenerator

        directory_structure_generator = DirectoryStructureGenerator(root_path=str(workspace_root))
    except Exception:
        directory_structure_generator = None

    world_state_aggregator = WorldStateAggregator(
        internal_sensing=internal_sensing,
        self_model=self_model,
        tool_registry=tool_registry,
        memory_manager=memory_manager,
        directory_structure_generator=directory_structure_generator,
        self_model_reduction_level=config.self_model.self_model_reduction_level,
    )

    # Color manager is not needed for web, but ConversationSession expects it.
    try:
        from .repl.color_profile import ColorManager

        color_manager = ColorManager()
        color_manager.set_profile(config.repl_color.profile)
    except Exception:
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
