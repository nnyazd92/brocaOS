from __future__ import annotations
from typing import Dict, Any

def reflect_and_suggest(trace: Dict[str, Any], failure_reason: str) -> Dict[str, Any]:
    """Produce a single concise suggestion: either an ASSUME: line or a prompt edit.
    This is a lightweight Reflexion placeholder that builds a simple suggestion string.
    In production, this would call an LLM critic/reflection model and return a structured suggestion.
    """
    # Simple heuristic: if failure_reason mentions clarifying_question, suggest an assumption
    if 'clarifying_question' in (failure_reason or ''):
        # Create a generic assumption based on last prompt if available
        last_prompt = None
        try:
            last_prompt = trace.get('step_outputs', [])[-1].get('prompt')
        except Exception:
            last_prompt = None
        assumption = "ASSUME: When details are missing, assume default context appropriate for the task."
        return {'type': 'ASSUME', 'content': assumption}
    # Otherwise, suggest a mild prompt edit
    suggestion = 'PROMPT_EDIT: Reformulate the previous prompt to include concrete default values and request a single final answer.'
    return {'type': 'PROMPT_EDIT', 'content': suggestion}
