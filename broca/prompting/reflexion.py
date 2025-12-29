"""
Reflexion (self-prompt) skeleton.
Provides a small API to reflect on a failed ChainResult and propose a single suggestion
(ASSUME: ... or prompt edit) that can be applied to retry.
"""
from __future__ import annotations
from typing import Dict, Any


def reflect_and_suggest(chain_result: Dict[str, Any], failure_reason: str) -> Dict[str, Any]:
    """Given a chain trace and failure reason, return a suggestion dict.
    Suggestion = { 'type': 'ASSUME'|'PROMPT_EDIT', 'content': str }
    This is a minimalistic implementation: it synthesizes a short ASSUME statement
    if failure_reason indicates missing info; otherwise suggests a conservative prompt edit.
    In practice this should call an LLM 'self-reflection' prompt to produce better suggestions.
    """
    # Very simple heuristic: if missing info, propose an ASSUME
    if failure_reason and 'clarifying_question' in failure_reason:
        # Extract hint from last reply if available
        last_reply = ''
        try:
            last_reply = chain_result.get('step_outputs', [])[-1].get('reply', '')
        except Exception:
            last_reply = ''
        # craft a generic assumption
        assume_text = "ASSUME: Missing details are X; proceed using reasonable defaults."
        return {'type': 'ASSUME', 'content': assume_text}
    # Generic prompt edit suggestion
    return {'type': 'PROMPT_EDIT', 'content': 'Please try to be more specific in your final answer and avoid clarifying questions.'}
