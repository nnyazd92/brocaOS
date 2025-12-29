from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class PromptTemplate:
    name: str
    text: str
    role: str = 'user'
    metadata: Dict[str, Any] = None

@dataclass
class ChainStep:
    template: PromptTemplate
    validator: Optional[Any] = None  # callable that inspects step output

@dataclass
class PromptChain:
    name: str
    steps: List[ChainStep]
    retries: int = 1

class ChainRunner:
    """Simple chain runner that executes steps using a ConversationSession-like object.
    The session must support .send(text, stream=False) and a few introspection hooks.
    """
    def __init__(self):
        pass

    def run_chain(self, session, chain: PromptChain, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}
        step_outputs = []
        tool_calls = []
        rl_signals = []
        for step in chain.steps:
            prompt_text = step.template.text.format(**(context or {}))
            # call session.send
            try:
                out = session.send(prompt_text, stream=False)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'session.send failed: {e}',
                    'step_outputs': step_outputs,
                    'tool_calls': tool_calls,
                    'rl_signals': rl_signals
                }
            # collect
            step_outputs.append({'prompt': prompt_text, 'output': out})
            # best-effort collect tool calls from session.messages
            try:
                for m in getattr(session, 'messages', [])[-3:]:
                    if m.get('role') == 'assistant' and isinstance(m.get('content'), dict):
                        tool_calls.append(m.get('content'))
            except Exception:
                pass
            # placeholder RL signals are not collected here; caller may collect
            # simple validator
            if step.validator:
                ok = step.validator(out)
                if not ok:
                    return {
                        'success': False,
                        'failed_step': step.template.name,
                        'step_outputs': step_outputs,
                        'tool_calls': tool_calls,
                        'rl_signals': rl_signals
                    }
        # final output is last step output
        final_output = step_outputs[-1]['output'] if step_outputs else None
        return {
            'success': True,
            'final_output': final_output,
            'step_outputs': step_outputs,
            'tool_calls': tool_calls,
            'rl_signals': rl_signals
        }
