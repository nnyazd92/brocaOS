from __future__ import annotations
from typing import Dict, Any

# Simple Critic tool: supports heuristic and optional LLM-based evaluation

def heuristic_critic(final_output: str) -> Dict[str, Any]:
    """Return {ok: bool, issues: [str], labels: {...}}"""
    issues = []
    ok = True
    if not final_output or not final_output.strip():
        ok = False
        issues.append('empty_output')
    # detect clarifying question
    q = False
    try:
        txt = final_output.strip()
        if txt.endswith('?'):
            q = True
        import re
        if re.search(r"\bdo you mean\b|\bcould you\b|\bplease clarify\b", txt, flags=re.IGNORECASE):
            q = True
    except Exception:
        q = False
    if q:
        # check for assumption marker
        import re
        if not re.search(r"\bI assume\b|\bASSUME:\b|\bassum(e|ption)\b", final_output, flags=re.IGNORECASE):
            ok = False
            issues.append('clarifying_question_without_assumption')
    return {'ok': ok, 'issues': issues, 'labels': {}}

