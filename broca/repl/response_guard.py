#!/usr/bin/env python3
"""
Response guard helper: ensure outgoing assistant messages are never empty.
Provides a deterministic fallback message with a TraceID when the composed
reply is empty or only whitespace.
"""
from __future__ import annotations
import uuid
import logging
from typing import Optional

logger = logging.getLogger(__name__)

FALLBACK_TEMPLATE = (
    "[automatic fallback] No content was generated for this turn. "
    "TraceID: {trace_id}. Please ask me to repeat or request details."
)

def ensure_non_empty(content: Optional[str], trace_id: Optional[str] = None) -> str:
    """
    Return content if it is non-empty after stripping; otherwise return a
    deterministic fallback message containing a trace id.
    """
    trace_id = trace_id or str(uuid.uuid4())
    final = (content or "").strip()
    if final:
        return final
    logger.warning("Empty assistant reply detected; injecting fallback (TraceID=%s)", trace_id)
    return FALLBACK_TEMPLATE.format(trace_id=trace_id)
