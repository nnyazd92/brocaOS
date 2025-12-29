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
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def process_single_task(task: Dict[str, Any], conversation_id: Optional[str] = None) -> Dict[str, Any]:
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
            'end_time': datetime.now(timezone.utc).isoformat(),
            'duration': 0.0
        }

    start_ts = datetime.now(timezone.utc).isoformat()
    conv_id = conversation_id or f"bench-{uuid4()}"

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
            'end_time': datetime.now(timezone.utc).isoformat(),
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
        import time as _time
        start_t = _time.time()

        # Inject benchmark-only system prompt for benchmark sessions (non-persistent)
        injected_benchmark_prompt = False
        try:
            if str(conv_id).startswith('bench-'):
                # Compose benchmark system prompt (concise, instructive)
                benchmark_prompt = (
                    "You are participating in an automated benchmark evaluating your ability "
                    "to solve tasks, use tools, and produce concise final answers. "
                    "When possible, provide a direct final answer rather than asking follow-up questions. "
                    "Only ask a single concise clarifying question if the task cannot be completed without it. "
                    "If you call tools, ensure tool-call actions and outcomes are recorded in structured traces so the evaluator can judge correctness. "
                    "This message is for benchmark context only and must NOT be persisted as part of the public conversation."
                )
                old_base = getattr(session, '_base_system_prompt_internal', None)
                if old_base:
                    session._base_system_prompt_internal = f"{old_base}

{benchmark_prompt}"
                else:
                    session._base_system_prompt_internal = benchmark_prompt
                injected_benchmark_prompt = True
        except Exception:
            injected_benchmark_prompt = False

        # Record procedures last_applied timestamps before running the turn (if available)
        procedures_before = {}
        try:
            rt = get_runtime()
            reasoning_tool = getattr(rt, 'reasoning_tool', None)
            learning_tool = None
            if reasoning_tool and hasattr(reasoning_tool, 'learning_tool'):
                learning_tool = reasoning_tool.learning_tool
            if not learning_tool and hasattr(rt, 'learning_tool'):
                learning_tool = getattr(rt, 'learning_tool')
            if learning_tool:
                pl = getattr(learning_tool, 'procedural_learner', None)
                if pl:
                    for name, proc in pl.procedures.items():
                        try:
                            procedures_before[name] = getattr(proc, 'last_applied', None)
                        except Exception:
                            procedures_before[name] = None
        except Exception:
            procedures_before = {}

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

        # Collect learning system snapshots (procedures, skills, recent experiences) if available
        learning_snapshot = {}
        try:
            rt = get_runtime()
            # reasoning_tool may expose learning_tool
            reasoning_tool = getattr(rt, 'reasoning_tool', None)
            learning_tool = None
            if reasoning_tool and hasattr(reasoning_tool, 'learning_tool'):
                learning_tool = reasoning_tool.learning_tool
            # fallback: standalone learning tool registered on runtime
            if not learning_tool and hasattr(rt, 'learning_tool'):
                learning_tool = getattr(rt, 'learning_tool')

            if learning_tool:
                try:
                    # Procedural learner snapshot
                    pl = getattr(learning_tool, 'procedural_learner', None)
                    if pl:
                        procedures = []
                        for name, proc in list(pl.procedures.items())[:10]:
                            procedures.append({
                                'name': proc.name,
                                'confidence': getattr(proc, 'confidence', None),
                                'success_count': getattr(proc, 'success_count', None),
                                'total_executions': getattr(proc, 'total_executions', None),
                                'dissonance_reduction_score': getattr(proc, 'dissonance_reduction_score', None),
                                'last_applied': getattr(proc, 'last_applied', None).isoformat() if getattr(proc, 'last_applied', None) else None,
                            })
                        learning_snapshot['procedures'] = procedures
                except Exception:
                    pass

                try:
                    # Skill manager snapshot
                    sm = getattr(learning_tool, 'skill_manager', None)
                    if sm:
                        skills = []
                        for name, skill in list(sm.skills.items())[:10]:
                            skills.append({
                                'name': skill.name,
                                'proficiency_level': getattr(skill, 'proficiency_level', None),
                                'confidence': getattr(skill, 'confidence', None),
                                'total_applications': getattr(skill, 'total_applications', None),
                                'average_dissonance_impact': getattr(skill, 'average_dissonance_impact', None),
                            })
                        learning_snapshot['skills'] = skills
                except Exception:
                    pass

                try:
                    # Experience logger recent experiences
                    el = getattr(learning_tool, 'experience_logger', None)
                    if el and hasattr(el, 'get_recent_experiences'):
                        recent = el.get_recent_experiences(limit=10)
                        # convert to dicts
                        recent_list = []
                        for exp in recent:
                            try:
                                recent_list.append({'type': exp.experience_type, 'outcome': exp.outcome, 'reward': exp.reward, 'timestamp': exp.timestamp.isoformat()})
                            except Exception:
                                pass
                        learning_snapshot['recent_experiences'] = recent_list
                except Exception:
                    pass
        except Exception:
            learning_snapshot = {}

        # Persist conversation so subsequent tasks using the same conversation_id
        # will see prior messages and context.
        try:
            rt = get_runtime()
            storage = None
            try:
                storage = rt.conversation_storage
            except Exception:
                storage = None
            if storage:
                try:
                    data = storage.load_conversation(conv_id) or {}
                    metadata = data.get('metadata', {}) if isinstance(data, dict) else {}
                    metadata['last_bench_update'] = datetime.now(timezone.utc).isoformat()
                    storage.save_conversation(conv_id, session.messages, metadata)
                except Exception:
                    pass
        except Exception:
            pass

        end_t = _time.time()
        duration_secs = end_t - start_t

        # Determine which procedures were applied during this turn by comparing last_applied timestamps
        procedures_applied = []
        try:
            if learning_tool and hasattr(learning_tool, 'procedural_learner'):
                pl = learning_tool.procedural_learner
                for name, proc in pl.procedures.items():
                    try:
                        before = procedures_before.get(name)
                        after = getattr(proc, 'last_applied', None)
                        if before is None and after is not None:
                            # Newly applied
                            procedures_applied.append({'procedure_name': name, 'confidence': getattr(proc, 'confidence', None)})
                        elif before is not None and after is not None and after > before:
                            procedures_applied.append({'procedure_name': name, 'confidence': getattr(proc, 'confidence', None)})
                    except Exception:
                        continue
        except Exception:
            procedures_applied = []

        result = {
            'task_id': task.get('id'),
            'success': bool(success),
            'final_output': reply,
            'tool_calls': tool_calls,
            'procedures_applied': procedures_applied,
            'learning_snapshot': learning_snapshot,
            'rl_signals': rl_signals or {},
            'benchmark_prompt_injected': injected_benchmark_prompt,
            'dissonance_before': None,
            'dissonance_after': None,
            'start_time': start_ts,
            'end_time': datetime.now(timezone.utc).isoformat(),
            'duration': duration_secs
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
            'end_time': datetime.now(timezone.utc).isoformat(),
            'duration': 0.0
        }
