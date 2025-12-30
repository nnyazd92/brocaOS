"""
Pydantic models for summarization data structures.

Defines the structure for session summaries, tasks, and project state.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


class SummaryHeader(BaseModel):
    """Header information for session summary."""
    session_id: str
    created_at: str  # ISO format timestamp
    last_updated_at: str  # ISO format timestamp
    last_summarized_event_id: Optional[str] = None
    revision: int = 0
    scope: str = ""  # Description of what this summary covers
    summarization_cycle_count: int = 0  # Number of summarization cycles completed (for gradual pruning)


class SummaryBlocks(BaseModel):
    """Summary blocks containing structured information."""
    current_goal: str = ""
    what_we_built: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    """Evidence linking claims to event IDs."""
    claim: str
    event_ids: List[str] = Field(default_factory=list)


class ConfidenceLevel(BaseModel):
    """Confidence levels for summary blocks."""
    current_goal: Literal["high", "medium", "low"] = "medium"
    what_we_built: List[Literal["high", "medium", "low"]] = Field(default_factory=list)
    open_questions: List[Literal["high", "medium", "low"]] = Field(default_factory=list)
    constraints: List[Literal["high", "medium", "low"]] = Field(default_factory=list)
    next_steps: List[Literal["high", "medium", "low"]] = Field(default_factory=list)


class SessionSummary(BaseModel):
    """Session summary structure."""
    header: SummaryHeader
    summary_blocks: SummaryBlocks
    evidence: List[EvidenceItem] = Field(default_factory=list)
    confidence: ConfidenceLevel = Field(default_factory=ConfidenceLevel)


class Task(BaseModel):
    """Task structure."""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "cancelled"] = "pending"
    owner: str = ""
    due_date: Optional[str] = None  # ISO format timestamp
    evidence_event_ids: List[str] = Field(default_factory=list)
    created_at: str  # ISO format timestamp


class TasksFile(BaseModel):
    """Tasks file structure."""
    tasks: List[Task] = Field(default_factory=list)


class ProjectState(BaseModel):
    """Project state structure."""
    repo_paths: List[str] = Field(default_factory=list)
    enabled_modules: List[str] = Field(default_factory=list)
    current_config: Dict[str, Any] = Field(default_factory=dict)
    known_issues: List[str] = Field(default_factory=list)

