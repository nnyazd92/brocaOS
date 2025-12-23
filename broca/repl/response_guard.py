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
    # If content is explicitly None or only whitespace, inject fallback.
    # Historically the code preserved empty-string ("") replies for
    # backward compatibility, but that leads to blank UI responses when a
    # streaming path yields no chunks. Treat whitespace-only content as
    # missing so callers always receive a visible fallback.
    if content is None or (isinstance(content, str) and content.strip() == ""):
        logger.warning("No assistant reply (None or whitespace) detected; injecting fallback (TraceID=%s)", trace_id)
        return FALLBACK_TEMPLATE.format(trace_id=trace_id)
    return content
