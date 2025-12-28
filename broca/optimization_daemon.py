"""
Optimization goal daemon.

Implements an autonomous feedback loop that:
1. Fetches optimization goal
2. Queries LLM for next actions
3. Executes tools
4. Generates report
5. Loops with configurable delay
"""

from __future__ import annotations

import sys
import signal
import time
import logging
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .logging_config import setup_logging
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
from .internal_sensing.framework import InternalSensingFramework
from .repl.session import ConversationSession
from .optimization.goal_manager import GoalManager
from .optimization.report_manager import ReportManager
from .world_state.aggregator import WorldStateAggregator

logger = logging.getLogger(__name__)


class OptimizationDaemon:
    """
    Daemon that implements autonomous optimization feedback loop.
    
    Continuously reads optimization goals, queries LLM for actions,
    executes tools, and generates reports.
    """
    
    def __init__(
        self,
        cycle_delay_seconds: Optional[float] = None,
        goal_manager: Optional[GoalManager] = None,
        report_manager: Optional[ReportManager] = None
    ) -> None:
        """
        Initialize OptimizationDaemon.
        
        Args:
            cycle_delay_seconds: Delay between cycles in seconds. If None, uses config.
            goal_manager: Optional GoalManager instance. If None, creates default.
            report_manager: Optional ReportManager instance. If None, creates default.
        """
        self.cycle_delay = cycle_delay_seconds or config.optimization.cycle_delay_seconds
        self.goal_manager = goal_manager or GoalManager()
        self.report_manager = report_manager or ReportManager()
        self.running = False
        self.shutdown_requested = False
        
        # Will be initialized in _initialize_systems
        self.session: Optional[ConversationSession] = None
        self.memory_manager: Optional[MemoryManager] = None
        
        logger.info(f"Initialized OptimizationDaemon with cycle delay: {self.cycle_delay}s")
    
    def _initialize_systems(self) -> None:
        """Initialize all systems (memory, tools, LLM, etc.) similar to main_repl.py"""
        from .main_repl import (
            _initialize_storage,
            _initialize_memory_manager,
            _initialize_self_model,
            _initialize_internal_sensing,
            _initialize_environment_system,
            _initialize_tool_registry
        )
        
        # Initialize storage
        storage = _initialize_storage()
        
        # Initialize memory manager
        self.memory_manager = _initialize_memory_manager()
        
        # Initialize self-model system
        self_model, storage, epistemic_engine = _initialize_self_model()
        
        # Initialize internal sensing system
        internal_sensing = _initialize_internal_sensing()
        
        # Initialize environment access system
        environment_system = _initialize_environment_system()
        
        # Initialize tool registry
        tool_registry = _initialize_tool_registry(
            memory_manager=self.memory_manager,
            epistemic_engine=epistemic_engine,
            self_model=self_model,
            storage=storage
        )
        
        # Remove restricted tools from daemon (safety restriction for autonomous operation)
        # Terminal and environment access tools are not allowed in autonomous mode
        restricted_tools = ["terminal", "environment_access"]
        if tool_registry and hasattr(tool_registry, 'get_tool') and hasattr(tool_registry, 'list_tools'):
            has_restricted_tool = any(tool_registry.get_tool(tool_name) for tool_name in restricted_tools)
            if has_restricted_tool:
                # Unregister restricted tools by creating new registry without them
                from .tools.registry import ToolRegistry
                new_registry = ToolRegistry(epistemic_engine=epistemic_engine)
                
                # Re-register all tools except restricted ones
                try:
                    removed_tools = []
                    for tool in tool_registry.list_tools():
                        if tool.name not in restricted_tools:
                            new_registry.register_tool(tool)
                        else:
                            removed_tools.append(tool.name)
                    
                    if removed_tools:
                        tool_registry = new_registry
                        logger.info(f"Removed restricted tools from optimization daemon (safety restriction): {', '.join(removed_tools)}")
                except (AttributeError, TypeError):
                    # If list_tools() fails (e.g., Mock object), skip removal
                    logger.debug("Could not remove restricted tools (registry may be mocked)")
        
        # Register self-model CRUD tool if self-model system is enabled
        # Note: UpdateSelfModelTool is NOT registered in autonomous mode for safety
        # CRUD tool allows querying but not updates in autonomous mode
        if self_model and storage and tool_registry:
            try:
                from .tools.self_model_crud_tool import SelfModelCRUDTool
                from .self_model.epistemic.engine import MetacognitiveEngine
                
                # Create epistemic engine if available
                epistemic_engine = None
                if hasattr(self_model, 'epistemic_layer') and self_model.epistemic_layer:
                    epistemic_engine = MetacognitiveEngine(epistemic_layer=self_model.epistemic_layer)
                
                crud_tool = SelfModelCRUDTool(self_model, storage, epistemic_engine=epistemic_engine)
                tool_registry.register_tool(crud_tool)
                logger.info("Registered self-model CRUD tool (query-only in autonomous mode)")
            except Exception as e:
                logger.warning(f"Failed to register self-model CRUD tool: {e}", exc_info=True)
        
        # Internal sensing tools are NOT registered as tools since internal sensing data
        # is already included in the LLM's mutable system prompt via WorldStateAggregator.
        
        # Register sandbox tool for safe command execution and artifact generation
        if tool_registry:
            try:
                from .tools.sandbox import SandboxTool
                sandbox_tool = SandboxTool()
                tool_registry.register_tool(sandbox_tool)
                logger.info("Registered sandbox tool for autonomous learning")
            except Exception as e:
                logger.warning(f"Failed to register sandbox tool: {e}", exc_info=True)
        
        # Skip registering environment access tool in daemon (safety restriction for autonomous operation)
        # Environment access tool is not available in autonomous optimization mode
        if environment_system:
            logger.debug("Environment access tool skipped in optimization daemon (safety restriction)")
        
        # Create directory structure generator for Broca house
        directory_structure_generator = None
        try:
            from .world_state.directory_structure import DirectoryStructureGenerator
            directory_structure_generator = DirectoryStructureGenerator(root_path="/home/wizard/broca")
            logger.info("Initialized directory structure generator for Broca house")
        except Exception as e:
            logger.warning(f"Failed to initialize directory structure generator: {e}", exc_info=True)
        
        # Create world state aggregator (enables dynamic system prompt mutation)
        world_state_aggregator = WorldStateAggregator(
            internal_sensing=internal_sensing,
            self_model=self_model,
            tool_registry=tool_registry,
            memory_manager=self.memory_manager,
            directory_structure_generator=directory_structure_generator,
            self_model_reduction_level=config.self_model.self_model_reduction_level,
        )
        
        # Create base system prompt for optimization daemon
        # This will be combined with dynamic world state by _update_system_prompt()
        system_prompt = (
            "You are BrocaOS-LLM running in autonomous optimization mode. "
            "You have access to various tools such as a memory retrieval system and web search tool. "
            "Your goal is to work towards achieving optimization goals by taking specific, actionable steps. "
            "When you complete a cycle, provide a clear summary of what you did, what you found, "
            "and what should be done next."
        )
        
        # Create conversation session with world_state_aggregator for dynamic system prompts
        self.session = ConversationSession(
            system_prompt=system_prompt,
            storage=storage,
            tool_registry=tool_registry,
            internal_sensing_framework=internal_sensing,
            world_state_aggregator=world_state_aggregator,
        )
        
        logger.info("Initialized all systems for optimization daemon")
    
    def _build_optimization_prompt(
        self, 
        goal: str, 
        previous_report: Optional[Dict[str, Any]], 
        constraints: Optional[List[str]] = None
    ) -> str:
        """
        Build the prompt for querying LLM about next actions.
        
        Args:
            goal: Current optimization goal
            previous_report: Previous cycle report if available
            constraints: Optional list of constraints for this goal
        
        Returns:
            Prompt string for LLM
        """
        if previous_report:
            previous_summary = (
                f"Last cycle (cycle {previous_report.get('cycle_number', '?')}), "
                f"I worked on '{goal}' and found that:\n"
                f"{previous_report.get('findings', 'No findings recorded')}\n\n"
                f"Actions taken: {', '.join(previous_report.get('actions_taken', []))}\n\n"
                f"Next steps suggested: {previous_report.get('next_steps', 'None')}"
            )
        else:
            previous_summary = "This is the first cycle for this goal."
        
        # Build constraints section if present
        constraints_section = ""
        if constraints:
            constraints_list = "\n".join(f"- {constraint}" for constraint in constraints)
            constraints_section = f"\n\nConstraints:\n{constraints_list}\n"
        
        prompt = (
            f"What should I do next to achieve the following optimization goal?\n\n"
            f"Goal: {goal}{constraints_section}\n"
            f"{previous_summary}\n\n"
            f"Please provide specific, actionable steps I should take. "
            f"You have access to all available tools (memory, web search, etc.). "
            f"Execute the steps using the available tools.\n\n"
            f"After completing your actions, include a structured report at the end of your response with the following sections:\n"
            f"## Report\n"
            f"**Actions Taken:** [List the tools you used]\n"
            f"**Findings:** [What you discovered, learned, or found during this cycle]\n"
            f"**Next Steps:** [What should be done in the next cycle to continue working towards the goal]\n\n"
            f"Be specific and actionable in your report."
        )
        
        return prompt
    
    def _extract_actions_from_messages(self, messages: List[Dict[str, Any]]) -> List[str]:
        """
        Extract list of tools used from conversation messages.
        
        Args:
            messages: Conversation message history
        
        Returns:
            List of tool names used
        """
        actions = []
        for message in messages:
            if message.get("role") == "tool":
                tool_name = message.get("name")
                if tool_name:
                    actions.append(tool_name)
        return actions
    
    def _format_conversation_summary(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format conversation messages into a summary for report generation.
        
        Args:
            messages: Conversation message history
        
        Returns:
            Formatted string summary
        """
        summary_parts = []
        for msg in messages[-10:]:  # Last 10 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content")
            # Handle None content gracefully
            if content is None:
                content = ""
            else:
                content = str(content)
            
            if role == "user":
                summary_parts.append(f"User: {content[:200]}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                summary_parts.append(f"Tool {tool_name}: {content[:200]}")
            elif role == "assistant":
                summary_parts.append(f"Assistant: {content[:200]}")
        
        return "\n".join(summary_parts)
    
    def _clear_conversation_context(self) -> None:
        """
        Clear conversation context to prevent overflow.
        
        Keeps only the system prompt and essential context for the next cycle.
        """
        if not self.session:
            return
        
        # Validate and ensure only one system message exists before keeping it
        # This prevents accumulation of multiple system messages
        self.session._ensure_single_system_message()
        
        # Keep only the first system message (should be at index 0 after validation)
        system_message = None
        if self.session.messages and self.session.messages[0].get("role") == "system":
            system_message = self.session.messages[0]
        
        # Clear all messages and restore only the single system message
        if system_message:
            self.session.messages = [system_message]
        else:
            self.session.messages = []
        
        logger.debug("Cleared conversation context to prevent overflow")
    
    def _parse_report_from_response(
        self, 
        goal: str, 
        cycle_number: int, 
        llm_response: str, 
        messages: List[Dict[str, Any]], 
        constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Parse report from the main LLM response (combined with actions).
        
        Args:
            goal: Optimization goal
            cycle_number: Cycle number
            llm_response: LLM response containing both actions and report
            messages: Full conversation history from the cycle
            constraints: Optional list of constraints for this goal
        
        Returns:
            Report dictionary
        """
        # Extract actions taken from messages
        actions_taken = self._extract_actions_from_messages(messages)
        
        # Parse report sections from LLM response
        parsed = self._parse_llm_report(llm_response, actions_taken)
        
        report = {
            "goal": goal,
            "cycle_number": cycle_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actions_taken": actions_taken,
            "findings": parsed["findings"],
            "next_steps": parsed["next_steps"]
        }
        
        # Include constraints in report if present
        if constraints is not None:
            report["constraints"] = constraints
        
        return report
    
    def _parse_llm_report(self, llm_response: str, actions_taken: List[str]) -> Dict[str, str]:
        """
        Parse LLM-generated report response into structured format.
        
        Args:
            llm_response: LLM response containing the report
            actions_taken: List of tools used (extracted from messages)
        
        Returns:
            Dictionary with findings and next_steps
        """
        # Try to extract structured sections from LLM response
        findings = ""
        next_steps = ""
        
        # Look for common section markers
        response_lower = llm_response.lower()
        
        # Try to find "Findings" section
        findings_markers = ["findings:", "discovered:", "learned:", "found:"]
        next_steps_markers = ["next steps:", "next:", "should be done:", "recommend:"]
        
        lines = llm_response.split("\n")
        current_section = None
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check if this line starts a section
            if any(marker in line_lower for marker in findings_markers):
                current_section = "findings"
                # Extract content after marker
                if ":" in line:
                    findings += line.split(":", 1)[1].strip() + "\n"
                continue
            elif any(marker in line_lower for marker in next_steps_markers):
                current_section = "next_steps"
                if ":" in line:
                    next_steps += line.split(":", 1)[1].strip() + "\n"
                continue
            
            # Add line to current section
            if current_section == "findings":
                findings += line.strip() + "\n"
            elif current_section == "next_steps":
                next_steps += line.strip() + "\n"
        
        # If no structured sections found, use the whole response as findings
        if not findings and not next_steps:
            findings = llm_response
        
        return {
            "findings": findings.strip(),
            "next_steps": next_steps.strip()
        }
    
    def _run_cycle(self) -> bool:
        """
        Run a single optimization cycle.
        
        Returns:
            True if cycle completed successfully, False otherwise
        """
        if not self.session:
            logger.error("Session not initialized")
            return False
        
        # Get active goal
        active_goal = self.goal_manager.get_active_goal()
        if not active_goal:
            logger.warning("No active goal found, skipping cycle")
            return False
        
        goal_text = active_goal.get("goal", "Unknown goal")
        # Extract constraints from goal (backward compatible - defaults to None if not present)
        constraints = active_goal.get("constraints")
        logger.info(f"Starting optimization cycle for goal: {goal_text}")
        if constraints:
            logger.info(f"Constraints: {constraints}")
        
        # Get previous report
        previous_report = self.report_manager.get_latest_report(goal_text)
        if previous_report:
            cycle_number = previous_report.get("cycle_number", 0) + 1
            logger.info(f"Continuing from cycle {cycle_number - 1}")
        else:
            cycle_number = 1
            logger.info("Starting first cycle for this goal")
        
        # Clear context from previous cycle (if any)
        self._clear_conversation_context()
        
        # Build prompt (includes request for report in response)
        prompt = self._build_optimization_prompt(goal_text, previous_report, constraints)
        
        try:
            # Query LLM and execute tools (response includes report)
            logger.info("Querying LLM for next actions and report...")
            response = self.session.send(prompt)
            
            # Parse report from the combined response
            logger.info("Parsing report from LLM response...")
            report = self._parse_report_from_response(
                goal=goal_text,
                cycle_number=cycle_number,
                llm_response=response,
                messages=self.session.messages,
                constraints=constraints
            )
            
            # Save report
            self.report_manager.add_report(report)
            logger.info(f"Cycle {cycle_number} completed. Actions: {report['actions_taken']}")
            logger.info(f"Findings: {report['findings'][:200]}...")
            
            # Clear context after saving report (keep only system prompt)
            self._clear_conversation_context()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in optimization cycle: {e}", exc_info=True)
            # Try to save partial report
            try:
                partial_report = {
                    "goal": goal_text,
                    "cycle_number": cycle_number,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "actions_taken": self._extract_actions_from_messages(self.session.messages) if self.session else [],
                    "findings": f"Error occurred: {str(e)}",
                    "next_steps": "Retry cycle"
                }
                # Include constraints in partial report if present
                if constraints is not None:
                    partial_report["constraints"] = constraints
                self.report_manager.add_report(partial_report)
            except Exception as save_error:
                logger.error(f"Failed to save partial report: {save_error}", exc_info=True)
            
            return False
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    def run(self) -> None:
        """Run the daemon main loop."""
        if self.running:
            logger.warning("Daemon is already running")
            return
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Initialize systems
        try:
            self._initialize_systems()
        except Exception as e:
            logger.error(f"Failed to initialize systems: {e}", exc_info=True)
            return
        
        self.running = True
        logger.info("Optimization daemon started")
        
        try:
            while not self.shutdown_requested:
                # Run cycle
                cycle_success = self._run_cycle()
                
                if not cycle_success:
                    logger.warning("Cycle failed, will retry after delay")
                
                # Wait before next cycle (unless shutdown requested)
                if not self.shutdown_requested:
                    logger.info(f"Waiting {self.cycle_delay} seconds before next cycle...")
                    time.sleep(self.cycle_delay)
        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error in daemon loop: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Optimization daemon stopped")
            
            # Cleanup
            if self.memory_manager:
                try:
                    self.memory_manager.close()
                    logger.info("Memory manager closed")
                except Exception as e:
                    logger.error(f"Error closing memory manager: {e}", exc_info=True)


def _ensure_initial_goals_file(goal_manager: GoalManager) -> None:
    """
    Ensure optimization goals file exists with example structure.
    
    Args:
        goal_manager: GoalManager instance
    """
    goals = goal_manager.load_goals()
    
    # If file doesn't exist or is empty, create example
    if not goals:
        example_goal = {
            "goal": "Learn more about the codebase structure and architecture",
            "active": True,
            "constraints": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        goal_manager.add_goal(example_goal)
        logger.info(f"Created initial optimization goals file with example goal: {example_goal['goal']}")


def main() -> None:
    """Main entry point for optimization daemon."""
    parser = argparse.ArgumentParser(description="BrocaOS Optimization Daemon")
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Delay between cycles in seconds (overrides config)"
    )
    parser.add_argument(
        "--goals-file",
        type=str,
        default=None,
        help="Path to optimization goals file (overrides config)"
    )
    parser.add_argument(
        "--reports-file",
        type=str,
        default=None,
        help="Path to optimization reports file (overrides config)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    # Create managers
    goal_manager = GoalManager(goals_file_path=args.goals_file) if args.goals_file else GoalManager()
    report_manager = ReportManager(reports_file_path=args.reports_file) if args.reports_file else ReportManager()
    
    # Ensure initial goals file exists
    _ensure_initial_goals_file(goal_manager)
    
    # Create and run daemon
    daemon = OptimizationDaemon(
        cycle_delay_seconds=args.delay,
        goal_manager=goal_manager,
        report_manager=report_manager
    )
    
    daemon.run()


if __name__ == "__main__":
    main()

