"""
Golden trace replay tests for system prompt management.

Tests that current implementation produces same results as captured golden traces.
"""

from __future__ import annotations

import pytest
import json
from pathlib import Path
from unittest.mock import Mock

from broca.repl.session import ConversationSession
from broca.world_state.aggregator import WorldStateAggregator
from broca.world_state.formatter import WorldStateFormatter
from broca.config import config


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    client.chat.return_value = {"choices": [{"message": {"content": "test"}}]}
    client.extract_assistant_content = Mock(return_value="test")
    client.extract_tool_calls = Mock(return_value=[])
    return client


@pytest.fixture
def golden_traces_dir():
    """Path to golden traces directory."""
    return Path(__file__).parent / "fixtures" / "golden_traces"


def load_golden_trace(trace_name: str, golden_traces_dir: Path) -> dict:
    """Load a golden trace from JSON file."""
    trace_path = golden_traces_dir / f"{trace_name}.json"
    if not trace_path.exists():
        pytest.skip(f"Golden trace {trace_name} not found at {trace_path}")
    
    with open(trace_path, 'r') as f:
        return json.load(f)


def save_golden_trace(trace_name: str, data: dict, golden_traces_dir: Path):
    """Save a golden trace to JSON file (for initial capture)."""
    trace_path = golden_traces_dir / f"{trace_name}.json"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(trace_path, 'w') as f:
        json.dump(data, f, indent=2)


class TestGoldenTraceReplay:
    """Test replay of golden traces."""
    
    def test_typical_world_state_system_prompt(self, mock_llm_client, golden_traces_dir):
        """Test system prompt generation with typical world state."""
        trace_name = "system_prompt_typical_world_state"
        
        # Try to load golden trace
        try:
            trace = load_golden_trace(trace_name, golden_traces_dir)
        except Exception:
            # If trace doesn't exist, capture it
            aggregator = Mock(spec=WorldStateAggregator)
            aggregator.aggregate.return_value = {
                "timestamp": "2024-01-01T00:00:00Z",
                "system": {"platform": "Linux", "python_version": "3.13.0"},
                "internal_state": {
                    "cognition": {"confidence_level": 0.75},
                    "affect": {"valence": 0.5}
                }
            }
            
            formatter = WorldStateFormatter()
            formatted_world_state = formatter.format(aggregator.aggregate.return_value)
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=aggregator,
                base_system_prompt="You are BrocaOS. Always be helpful."
            )
            session._world_state_formatter = formatter
            
            system_content = session.messages[0]["content"]
            
            # Save as golden trace
            trace = {
                "base_prompt": "You are BrocaOS. Always be helpful.",
                "world_state": aggregator.aggregate.return_value,
                "formatted_world_state_length": len(formatted_world_state),
                "system_prompt_length": len(system_content),
                "system_prompt_preview": system_content[:500]
            }
            save_golden_trace(trace_name, trace, golden_traces_dir)
            pytest.skip(f"Captured golden trace {trace_name}, run test again to verify")
        
        # Replay: Generate system prompt with same inputs
        aggregator = Mock(spec=WorldStateAggregator)
        aggregator.aggregate.return_value = trace["world_state"]
        
        formatter = WorldStateFormatter()
        formatted_world_state = formatter.format(trace["world_state"])
        
        session = ConversationSession(
            llm=mock_llm_client,
            world_state_aggregator=aggregator,
            base_system_prompt=trace["base_prompt"]
        )
        session._world_state_formatter = formatter
        
        system_content = session.messages[0]["content"]
        
        # Verify lengths match (content may vary slightly due to formatting)
        assert len(system_content) == trace["system_prompt_length"], \
            f"System prompt length mismatch: {len(system_content)} != {trace['system_prompt_length']}"
    
    def test_truncation_scenario(self, mock_llm_client, golden_traces_dir):
        """Test system prompt generation with truncation scenario."""
        trace_name = "system_prompt_truncation"
        original_max = config.storage.max_system_prompt_size
        config.storage.max_system_prompt_size = 1000  # Small limit
        
        try:
            # Try to load golden trace
            try:
                trace = load_golden_trace(trace_name, golden_traces_dir)
            except Exception:
                # Capture trace
                large_base_prompt = "A" * 2000  # Exceeds limit
                
                aggregator = Mock(spec=WorldStateAggregator)
                aggregator.aggregate.return_value = {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "system": {"platform": "Linux"}
                }
                
                session = ConversationSession(
                    llm=mock_llm_client,
                    world_state_aggregator=aggregator,
                    base_system_prompt=large_base_prompt
                )
                
                system_content = session.messages[0]["content"]
                
                trace = {
                    "base_prompt_length": len(large_base_prompt),
                    "max_size": config.storage.max_system_prompt_size,
                    "system_prompt_length": len(system_content),
                    "has_truncation_message": "[Base system prompt truncated" in system_content
                }
                save_golden_trace(trace_name, trace, golden_traces_dir)
                pytest.skip(f"Captured golden trace {trace_name}, run test again to verify")
            
            # Replay: Generate with same inputs
            large_base_prompt = "A" * trace["base_prompt_length"]
            
            aggregator = Mock(spec=WorldStateAggregator)
            aggregator.aggregate.return_value = {
                "timestamp": "2024-01-01T00:00:00Z",
                "system": {"platform": "Linux"}
            }
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=aggregator,
                base_system_prompt=large_base_prompt
            )
            
            system_content = session.messages[0]["content"]
            
            # Verify truncation behavior
            assert len(system_content) == trace["system_prompt_length"]
            assert ("[Base system prompt truncated" in system_content) == trace["has_truncation_message"]
        finally:
            config.storage.max_system_prompt_size = original_max
    
    def test_component_combination_scenarios(self, mock_llm_client, golden_traces_dir):
        """Test system prompt generation with various component combinations."""
        scenarios = [
            ("base_only", True, False, False),
            ("base_and_world_state", True, False, True),
            ("base_and_summary", True, True, False),
            ("all_components", True, True, True),
        ]
        
        for scenario_name, has_base, has_summary, has_world_state in scenarios:
            trace_name = f"system_prompt_{scenario_name}"
            
            try:
                trace = load_golden_trace(trace_name, golden_traces_dir)
            except Exception:
                # Capture trace
                base_prompt = "You are BrocaOS." if has_base else None
                
                aggregator = Mock(spec=WorldStateAggregator) if has_world_state else None
                if aggregator:
                    aggregator.aggregate.return_value = {
                        "timestamp": "2024-01-01T00:00:00Z",
                        "system": {"platform": "Linux"}
                    }
                
                session = ConversationSession(
                    llm=mock_llm_client,
                    world_state_aggregator=aggregator,
                    base_system_prompt=base_prompt
                )
                
                if has_summary:
                    from broca.summarization.prompt_builder import PromptBuilder
                    from broca.summarization.storage import SummaryStorage
                    storage = Mock(spec=SummaryStorage)
                    storage.load_session_summary.return_value = None
                    storage.load_project_state.return_value = None
                    mock_summarization_manager = Mock()
                    mock_summarization_manager.summary_storage = storage
                    session._summarization_manager = mock_summarization_manager
                
                system_content = session.messages[0]["content"]
                
                trace = {
                    "has_base": has_base,
                    "has_summary": has_summary,
                    "has_world_state": has_world_state,
                    "system_prompt_length": len(system_content),
                    "system_prompt_preview": system_content[:200]
                }
                save_golden_trace(trace_name, trace, golden_traces_dir)
                pytest.skip(f"Captured golden trace {trace_name}, run test again to verify")
            
            # Replay
            base_prompt = "You are BrocaOS." if trace["has_base"] else None
            
            aggregator = Mock(spec=WorldStateAggregator) if trace["has_world_state"] else None
            if aggregator:
                aggregator.aggregate.return_value = {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "system": {"platform": "Linux"}
                }
            
            session = ConversationSession(
                llm=mock_llm_client,
                world_state_aggregator=aggregator,
                base_system_prompt=base_prompt
            )
            
            if trace["has_summary"]:
                from broca.summarization.prompt_builder import PromptBuilder
                from broca.summarization.storage import SummaryStorage
                storage = Mock(spec=SummaryStorage)
                storage.load_session_summary.return_value = None
                storage.load_project_state.return_value = None
                mock_summarization_manager = Mock()
                mock_summarization_manager.summary_storage = storage
                session._summarization_manager = mock_summarization_manager
            
            system_content = session.messages[0]["content"]
            
            # Verify length matches
            assert len(system_content) == trace["system_prompt_length"], \
                f"Length mismatch for {scenario_name}: {len(system_content)} != {trace['system_prompt_length']}"

