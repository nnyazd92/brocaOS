"""
Summarization module for context management.

Provides automatic summarization of conversations to keep prompts
small and stable while preserving continuity.
"""

from .event_logger import EventLogger
from .manager import SummarizationManager
from .storage import SummaryStorage
from .summarizer import Summarizer
from .prompt_builder import PromptBuilder
from .retrieval import RetrievalIndex
from .validation import SummarizationValidator
from .models import (
    SessionSummary,
    Task,
    TasksFile,
    ProjectState,
    SummaryHeader,
    SummaryBlocks,
    EvidenceItem,
    ConfidenceLevel,
)

__all__ = [
    "EventLogger",
    "SummarizationManager",
    "SummaryStorage",
    "Summarizer",
    "PromptBuilder",
    "RetrievalIndex",
    "SummarizationValidator",
    "SessionSummary",
    "Task",
    "TasksFile",
    "ProjectState",
    "SummaryHeader",
    "SummaryBlocks",
    "EvidenceItem",
    "ConfidenceLevel",
]

