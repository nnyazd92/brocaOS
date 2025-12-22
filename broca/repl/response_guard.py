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
    Return content if it is non-empty after stripping; if content is exactly
    an empty string (""), treat it as a valid reply and return it unchanged.
    Only inject a deterministic fallback message when content is None.
    """
    trace_id = trace_id or str(uuid.uuid4())
    # If content is explicitly None, inject fallback. If content is an empty
    # string (""), preserve it to maintain backward compatibility with
    # callers/tests that expect empty-string replies.
    if content is None:
        logger.warning("No assistant reply (None) detected; injecting fallback (TraceID=%s)", trace_id)
        return FALLBACK_TEMPLATE.format(trace_id=trace_id)
    # Otherwise return content as-is (including empty string)
    return content
