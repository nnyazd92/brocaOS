"""
Simple Critic tool for validating assistant outputs.
Provides a small API evaluate_output which returns a dict with ok(bool) and issues(list).
"""
from __future__ import annotations
from typing import Dict, Any, List
import re


def evaluate_output(text: str, task_spec: Dict[str, Any] = None) -> Dict[str, Any]:
    issues: List[str] = []
    ok = True

    if not text or not text.strip():
        ok = False
        issues.append('empty_output')

    # Clarifying question detection
    if text.strip().endswith('?'):
        # If ends with question mark, flag
        ok = False
        issues.append('clarifying_question')

    # Assume detection
    if re.search(r"\b(I assume|ASSUME:|assuming that|for the purpose of this answer)\b", text, flags=re.IGNORECASE):
        # note assumption present
        issues.append('assumption_present')

    return {'ok': ok, 'issues': issues}
