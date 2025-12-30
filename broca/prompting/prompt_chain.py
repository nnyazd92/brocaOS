"""
PromptChainManager skeleton for BrocaOS.
Provides simple prompt-chain execution functionality.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class PromptTemplate:
    name: str
    template: str
    role: str = "user"  # 'user' or 'system' or 'assistant'
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChainStep:
    name: str
    prompt: PromptTemplate
    validator: Optional[Any] = None  # callable(result) -> bool


@dataclass
class PromptChain:
    name: str
    steps: List[ChainStep]
    retries: int = 1


class ChainResult:
    def __init__(self):
        self.step_outputs: List[Dict[str, Any]] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.final_output: Optional[str] = None
        self.rl_signals: Dict[str, Any] = {}
        self.success: bool = False
        self.started_at = datetime.utcnow().isoformat() + 'Z'
        self.ended_at: Optional[str] = None


class ChainRunner:
    """Execute a PromptChain using a ConversationSession-like object.

    The session is expected to provide .send(text, stream=False) -> reply_text
    and have accessible tool traces in session.messages if tools were called.
    """

    def __init__(self, session: Any):
        self.session = session

    def run_chain(self, chain: PromptChain, context: Dict[str, Any] = None) -> ChainResult:
        result = ChainResult()
        try:
            for step in chain.steps:
                prompt_text = step.prompt.template
                # Simple template substitution using context
                if context:
                    try:
                        prompt_text = prompt_text.format(**context)
                    except Exception:
                        pass

                reply = self.session.send(prompt_text, stream=False)

                # collect tool calls if present (best-effort)
                step_tool_calls = []
                try:
                    for m in getattr(self.session, 'messages', []):
                        if m.get('role') == 'assistant' and isinstance(m.get('content'), dict):
                            step_tool_calls.append(m.get('content'))
                except Exception:
                    step_tool_calls = []

                result.step_outputs.append({
                    'step': step.name,
                    'prompt': prompt_text,
                    'reply': reply,
                    'tool_calls': step_tool_calls
                })
                result.tool_calls.extend(step_tool_calls)

                # run validator if provided
                if step.validator:
                    try:
                        ok = step.validator(reply)
                        if not ok:
                            result.success = False
                            result.final_output = reply
                            result.ended_at = datetime.utcnow().isoformat() + 'Z'
                            return result
                    except Exception:
                        pass

            # if all steps complete
            result.success = True
            result.final_output = result.step_outputs[-1]['reply'] if result.step_outputs else None
            result.ended_at = datetime.utcnow().isoformat() + 'Z'
            return result
        except Exception as e:
            result.success = False
            result.final_output = None
            result.ended_at = datetime.utcnow().isoformat() + 'Z'
            return result
