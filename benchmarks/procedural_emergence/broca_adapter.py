"""
Simple BrocaOS adapter for the Procedural Emergence benchmark.
Provides process_single_task(task: dict) -> dict which the benchmark runner can call
when running in the same environment as BrocaOS.

It uses broca.web_api.get_runtime() and create_session() to run a single user turn
and returns a result compatible with the benchmark result schema.
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def process_single_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single benchmark task using the local BrocaOS runtime.

    Args:
        task: task dict (expects at least task.get('input') which may be a dict)

    Returns:
        result dict conforming to result_schema.json
    """
    try:
        # Import broca web_api helpers
        from broca.web_api import get_runtime, create_session
    except Exception as e:
        return {
            'task_id': task.get('id'),
            'success': False,
            'final_output': None,
            'error': f'Failed to import broca.web_api: {e}',
            'tool_calls': [],
            'procedures_applied': [],
            'rl_signals': {},
            'dissonance_before': None,
            'dissonance_after': None,
            'start_time': datetime.utcnow().isoformat() + 'Z',
            'end_time': datetime.utcnow().isoformat() + 'Z',
            'duration': 0.0
        }

    start_ts = datetime.utcnow().isoformat() + 'Z'
    conv_id = f"bench-{uuid4()}"

    try:
        session = create_session(conv_id)
    except Exception as e:
        return {
            'task_id': task.get('id'),
            'success': False,
            'final_output': None,
            'error': f'Failed to create conversation session: {e}',
            'tool_calls': [],
            'procedures_applied': [],
            'rl_signals': {},
            'dissonance_before': None,
            'dissonance_after': None,
            'start_time': start_ts,
            'end_time': datetime.utcnow().isoformat() + 'Z',
            'duration': 0.0
        }

    # Derive input text from task
    inp = task.get('input')
    if isinstance(inp, dict):
        # Common field is 'query'
        input_text = inp.get('query') or inp.get('text') or str(inp)
    else:
        input_text = str(inp)

    try:
        # Send user text to session (synchronous)
        reply = session.send(input_text, stream=False)

        # Attempt to get simple RL signals if available via runtime
        rl_signals = None
        try:
            rt = get_runtime()
            if rt.world_state_aggregator and hasattr(rt.world_state_aggregator, 'reasoning_tool'):
                reasoning_tool = rt.world_state_aggregator.reasoning_tool
                if reasoning_tool and hasattr(reasoning_tool, 'feedback_loop_manager'):
                    feedback_loop_manager = reasoning_tool.feedback_loop_manager
                    if feedback_loop_manager and feedback_loop_manager.rl_signals_enabled and feedback_loop_manager.rl_signal_aggregator:
                        try:
                            affective_state = None
                            if session.internal_sensing_framework:
                                try:
                                    affective_state = session.internal_sensing_framework.get_current_affective_state()
                                except Exception:
                                    affective_state = None
                            prediction_error = None
                            if session.internal_sensing_framework and hasattr(session.internal_sensing_framework.interoception, 'predictive'):
                                try:
                                    prediction_error = session.internal_sensing_framework.interoception.predictive.get_rl_prediction_error_signal()
                                except Exception:
                                    prediction_error = None

                            rl_metrics = feedback_loop_manager.rl_signal_aggregator.compute_signals(
                                affective_state=affective_state,
                                prediction_error=prediction_error,
                            )
                            rl_signals = {
                                'dissonance_reward': round(rl_metrics.dissonance_reward, 3),
                                'surprise_reward': round(rl_metrics.surprise_reward, 3),
                                'curiosity_reward': round(rl_metrics.curiosity_reward, 3),
                                'information_gain_reward': round(rl_metrics.information_gain_reward, 3),
                                'coherence_reward': round(rl_metrics.coherence_reward, 3),
                                'composite_reward': round(rl_metrics.composite_reward, 3)
                            }
                        except Exception:
                            rl_signals = None
        except Exception:
            rl_signals = None

        # Determine success (simple exact match or containment if expected_output provided)
        expected = task.get('expected_output')
        if expected is None:
            success = True
        else:
            try:
                if isinstance(expected, str):
                    success = expected.strip() in (reply or '').strip()
                else:
                    success = expected == reply
            except Exception:
                success = False

        # Collect tool call traces if session exposes them (best-effort)
        tool_calls = []
        try:
            # ConversationSession may store tool events in messages or event logger
            # Try reading session.messages for assistant/tool entries
            for m in getattr(session, 'messages', []):
                # messages are dicts with role/content; tool events may be in content or metadata
                # Skip user messages
                if m.get('role') == 'assistant' and isinstance(m.get('content'), dict):
                    # If assistant content is structured with tool call info
                    tool_calls.append(m.get('content'))
        except Exception:
            tool_calls = []

        result = {
            'task_id': task.get('id'),
            'success': bool(success),
            'final_output': reply,
            'tool_calls': tool_calls,
            'procedures_applied': [],
            'rl_signals': rl_signals or {},
            'dissonance_before': None,
            'dissonance_after': None,
            'start_time': start_ts,
            'end_time': datetime.utcnow().isoformat() + 'Z',
            'duration': None
        }
        return result

    except Exception as e:
        return {
            'task_id': task.get('id'),
            'success': False,
            'final_output': None,
            'error': f'Error during session.send: {e}',
            'tool_calls': [],
            'procedures_applied': [],
            'rl_signals': {},
            'dissonance_before': None,
            'dissonance_after': None,
            'start_time': start_ts,
            'end_time': datetime.utcnow().isoformat() + 'Z',
            'duration': 0.0
        }
