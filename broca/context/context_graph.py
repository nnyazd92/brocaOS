"""
Context graph implementation for intelligent conversation context management.

Uses simple oldest-first node plucking to stay within token limits:
- Estimate total tokens
- If over limit, pluck oldest nodes (by timestamp) until under limit
- Always keep: system messages, most recent N messages
- Plucked nodes are tombstoned so they won't be re-added from replayed history

This replaces the complex relevance-based pruning which was buggy and caused
token counts to keep growing despite "truncation".
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
import hashlib

from ..summarization.token_estimator import estimate_messages_tokens, estimate_tokens
from .relevance import compute_relevance_score

logger = logging.getLogger(__name__)


@dataclass
class MessageNode:
    """Represents a message in the conversation graph."""
    
    message_id: str
    role: str  # user, assistant, tool, system
    content: str
    parent_id: Optional[str] = None
    thread_id: Optional[str] = None
    relevance_score: float = 0.0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    token_count: int = 0
    children: List[str] = field(default_factory=list)
    is_orphan: bool = False
    message_data: Optional[Dict] = None  # Original message dict for reconstruction
    tool_call_chain_id: Optional[str] = None  # ID of tool call chain this message belongs to
    is_compacted: bool = False  # If True, this node must not be re-inflated from full history updates
    
    def __post_init__(self):
        """Compute token count after initialization."""
        if self.token_count == 0:
            self.token_count = estimate_tokens(self.content)
            if self.message_data:
                # More accurate estimate from full message structure
                self.token_count = estimate_tokens(self.message_data)


class ContextGraph:
    """
    Manages conversation context as a graph structure.
    
    Intelligently prunes orphaned branches while preserving the main
    conversation thread and relevant branches.
    """
    
    def __init__(
        self,
        min_turns_retained: int = 3,
        orphan_threshold_turns: int = 10,
        main_thread_boost: float = 2.0,
        main_thread_token_budget_ratio: float = 0.6,
        tool_content_max_chars: int = 8000,
        selection_logging_enabled: bool = False,
        selection_log_file: str = "data/context_selection.csv",
        min_recent_to_keep: int = 50,  # Minimum recent messages to always preserve (increased from 15 to better preserve tool call sequences)
    ):
        """
        Initialize context graph.
        
        Args:
            min_turns_retained: Minimum turns to always keep
            orphan_threshold_turns: Turns before branch considered orphan (legacy, not used)
            main_thread_boost: Boost multiplier for main thread messages (legacy, not used)
            min_recent_to_keep: Minimum number of recent messages to always keep during plucking
        """
        self.nodes: Dict[str, MessageNode] = {}
        self.root_nodes: List[str] = []
        self.main_thread_id: Optional[str] = None
        self.min_turns_retained = min_turns_retained
        self.orphan_threshold_turns = orphan_threshold_turns
        self.main_thread_boost = main_thread_boost
        # Legacy (kept for backwards compat but not used by new plucking logic)
        self.main_thread_token_budget_ratio = max(0.1, min(0.9, float(main_thread_token_budget_ratio)))
        # Store tool outputs in-graph with a strict bound so token accounting remains truthful.
        self.tool_content_max_chars = max(500, int(tool_content_max_chars))
        # Optional telemetry: per-call kept/dropped reasons for RL + debugging.
        self._selection_logger = None
        self._selection_logging_enabled = bool(selection_logging_enabled)
        self._selection_log_file = str(selection_log_file)
        self._last_selection_reasons: Dict[str, str] = {}
        self._message_order: List[str] = []  # Track insertion order (timestamps)
        self._tool_chains: Dict[str, Set[str]] = {}  # Map chain_id -> set of message_ids
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self.min_recent_to_keep = max(5, int(min_recent_to_keep))
        # Track which message IDs were plucked in the last call (for session sync)
        self._last_plucked_ids: List[str] = []
        # Tombstones: message IDs intentionally excluded from the in-graph context.
        # ConversationSession replays full history into the graph each turn; tombstones
        # prevent previously-plucked/pruned nodes from being re-inflated while still
        # allowing the persisted conversation history to remain intact.
        self._excluded_message_ids: Set[str] = set()

    def _tombstone(self, message_id: str, reason: str) -> None:
        """Record that a message ID should not be re-added to the graph."""
        self._excluded_message_ids.add(message_id)
        self._last_selection_reasons[message_id] = reason

    def _truncate_tool_content(self, content: str) -> tuple[str, Dict[str, any]]:
        """
        Truncate a tool message's content for in-graph storage, preserving prefix+suffix.
        Returns (truncated_content, metadata).
        """
        if not isinstance(content, str):
            content = str(content)

        if len(content) <= self.tool_content_max_chars:
            return content, {}

        prefix_size = int(self.tool_content_max_chars * 0.8)
        suffix_size = int(self.tool_content_max_chars * 0.1)
        prefix = content[:prefix_size]
        suffix = content[-suffix_size:] if len(content) > suffix_size else ""
        truncated_chars = len(content) - self.tool_content_max_chars
        marker = f"\n\n... [truncated {truncated_chars} characters] ...\n\n"
        truncated = f"{prefix}{marker}{suffix}"

        h = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()[:16]
        meta = {
            "_broca_truncated": True,
            "_broca_original_length": len(content),
            "_broca_content_hash": h,
        }
        return truncated, meta

    def _get_protected_tool_chain_ids(self, keep_ids: Set[str]) -> Set[str]:
        """
        Get all message IDs that are part of tool chains involving kept messages.
        
        If any message in a tool chain is in keep_ids, the entire chain must be protected.
        This prevents breaking tool chains during compaction.
        
        Args:
            keep_ids: Set of message IDs that will be kept (not compacted)
            
        Returns:
            Set of all message IDs that should be protected due to tool chain membership
        """
        protected = set()
        
        # Identify all tool chains
        chains = self._identify_tool_call_chains()
        
        # If any message in a chain is kept, protect the entire chain
        for chain_id, chain_messages in chains.items():
            if chain_messages & keep_ids:  # Intersection - any overlap?
                protected.update(chain_messages)
        
        # Also protect incomplete tool chains (assistant with tool_calls waiting for responses)
        for msg_id, node in self.nodes.items():
            if node.role != "assistant" or not node.message_data:
                continue
            
            tool_calls = node.message_data.get("tool_calls")
            if not tool_calls:
                continue
            
            # Check if all tool responses are present
            tool_call_ids = {tc.get("id") for tc in tool_calls if isinstance(tc, dict) and tc.get("id")}
            found_responses = set()
            
            for other_id, other_node in self.nodes.items():
                if other_node.role == "tool" and other_node.message_data:
                    tcid = other_node.message_data.get("tool_call_id")
                    if tcid in tool_call_ids:
                        found_responses.add(tcid)
            
            # If responses are incomplete, protect this assistant and all found responses
            if found_responses != tool_call_ids:
                protected.add(msg_id)
                for other_id, other_node in self.nodes.items():
                    if other_node.role == "tool" and other_node.message_data:
                        tcid = other_node.message_data.get("tool_call_id")
                        if tcid in tool_call_ids:
                            protected.add(other_id)
        
        return protected

    def _maybe_compact_history(self, *, max_tokens: int, safety_margin: float) -> None:
        """
        Proactively compact older history to reduce long-session weirdness.

        Key requirement: ConversationSession replays full history into the graph each turn.
        So compaction must mark nodes as compacted so they cannot be re-inflated.
        
        Tool chain protection: Never compact messages that are part of a tool chain
        if any message in that chain is in the recent/kept portion.
        """
        if not self.nodes:
            return

        effective_max = int(max_tokens * safety_margin)
        # Estimate full in-graph token load (what we'd send if we kept everything)
        all_messages = [node.message_data for node in self.nodes.values() if node.message_data]
        current_tokens = estimate_messages_tokens(all_messages) if all_messages else 0

        # Trigger only when we're well above budget (avoid thrashing).
        if current_tokens <= int(effective_max * 1.25):
            return

        # Choose the best main thread (non-budgeted) and compact its oldest portion.
        main_thread = self.identify_main_thread(token_budget=None)
        if len(main_thread) < 20:
            return

        keep_tail_count = max(self.min_turns_retained * 6, 20)
        if len(main_thread) <= keep_tail_count:
            return

        # Messages we're keeping (tail of main thread)
        keep_ids = set(main_thread[-keep_tail_count:])
        
        # Get protected tool chain IDs (entire chains if any part is kept)
        protected_ids = self._get_protected_tool_chain_ids(keep_ids)
        
        compact_ids = [mid for mid in main_thread[:-keep_tail_count] if mid in self.nodes]
        # Never compact system messages
        compact_ids = [mid for mid in compact_ids if self.nodes[mid].role != "system"]
        # Never compact messages in protected tool chains
        compact_ids = [mid for mid in compact_ids if mid not in protected_ids]
        if not compact_ids:
            return

        summary_text = self._build_compaction_summary(compact_ids, max_chars=4000)
        # Use role="system" so the model understands this is system-provided context,
        # NOT its own response. Using role="assistant" caused the model to think it
        # had already responded and start asking clarifying questions mid-task.
        summary_msg = {
            "role": "system",
            "content": f"[CONTEXT COMPACTION: Previous conversation history has been summarized due to length limits. The assistant should continue its current task based on this summary and recent messages.]\n\n{summary_text}",
            "message_id": f"summary_{uuid.uuid4()}",
            "_broca_summary": True,
            "_broca_meta": {
                "_broca_summary_of": compact_ids[-200:],  # cap provenance size
                "_broca_compacted_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        # Add summary as a root (we treat summaries as anchors later)
        self._add_message_unsafe(summary_msg, parent_id=None, thread_id=self.main_thread_id)

        # Mark compacted nodes so they can't be re-inflated and won't be emitted.
        for mid in compact_ids:
            node = self.nodes.get(mid)
            if not node:
                continue
            node.is_compacted = True
            node.content = ""
            node.message_data = None  # omit from outgoing prompt selection
            node.token_count = 0

    def _build_compaction_summary(self, msg_ids: List[str], max_chars: int = 4000) -> str:
        """
        Build a deterministic, provenance-aware summary for compacted history.
        (No LLM call here: ContextGraph runs inside the LLM call path.)
        """
        user_snips: List[str] = []
        tool_snips: List[str] = []
        assistant_snips: List[str] = []

        def add_unique(lst: List[str], s: str) -> None:
            if not s:
                return
            if s in lst:
                return
            lst.append(s)

        for mid in msg_ids:
            node = self.nodes.get(mid)
            if not node:
                continue
            role = node.role
            content = node.content or ""
            if role == "user":
                add_unique(user_snips, content[:200].strip())
            elif role == "tool":
                meta = {}
                if node.message_data and isinstance(node.message_data.get("_broca_meta"), dict):
                    meta = node.message_data.get("_broca_meta") or {}
                h = meta.get("_broca_content_hash")
                name = (node.message_data or {}).get("name") if node.message_data else None
                tool_snips.append(f"{name or 'tool'} result hash={h or 'unknown'}")
            elif role == "assistant":
                # Drop low-value planning chatter to reduce weirdness
                low = content.strip().lower()
                if len(low) < 240 and ("plan" in low or "next" in low or "i will" in low):
                    continue
                add_unique(assistant_snips, content[:200].strip())

        lines: List[str] = []
        lines.append("COMPACTED CONTEXT SUMMARY (provenance in _broca_meta._broca_summary_of)")
        if user_snips:
            lines.append("Recent user intents/constraints (excerpted):")
            for s in user_snips[-20:]:
                lines.append(f"- {s}")
        if tool_snips:
            lines.append("Notable tool outcomes (hashed pointers):")
            for s in tool_snips[-20:]:
                lines.append(f"- {s}")
        if assistant_snips:
            lines.append("Key assistant conclusions (excerpted):")
            for s in assistant_snips[-20:]:
                lines.append(f"- {s}")

        text = "\n".join(lines).strip()
        if len(text) > max_chars:
            text = text[: max_chars - 40] + "\n... [summary truncated] ..."
        return text
        
    def __enter__(self):
        """Context manager entry for atomic operations."""
        self._lock.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit for atomic operations."""
        self._lock.release()
        return False
    
    def add_message(
        self,
        message: Dict[str, any],
        parent_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> str:
        """
        Add a message to the graph.
        
        Args:
            message: Message dictionary with 'role' and 'content'
            parent_id: Optional parent message ID for threading
            thread_id: Optional thread identifier
            
        Returns:
            Message ID of the added message
        """
        with self._lock:
            return self._add_message_unsafe(message, parent_id, thread_id)
    
    def _add_message_unsafe(
        self,
        message: Dict[str, any],
        parent_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> str:
        """Internal method to add message without locking (caller must hold lock)."""
        message_id = message.get("message_id") or str(uuid.uuid4())
        
        # Ensure message_data exists
        if "message_id" not in message:
            message["message_id"] = message_id

        # Tombstoned IDs are intentionally excluded from the in-graph context.
        # Keep the persisted history unchanged, but skip re-inflation here.
        if message_id in self._excluded_message_ids:
            self._last_selection_reasons[message_id] = "excluded"
            return message_id
        
        # If message already exists, update it
        if message_id in self.nodes:
            node = self.nodes[message_id]
            # Never re-inflate compacted nodes from the full session history.
            # (ConversationSession replays full history into the graph each turn.)
            if getattr(node, "is_compacted", False):
                node.last_accessed = datetime.now(timezone.utc)
                return message_id

            # Re-apply adaptive tool truncation on updates too.
            if message.get("role") == "tool":
                content = message.get("content", "")
                truncated, meta = self._truncate_tool_content(content if isinstance(content, str) else str(content))
                if meta:
                    message["content"] = truncated
                    message.setdefault("_broca_meta", {})
                    if isinstance(message["_broca_meta"], dict):
                        message["_broca_meta"].update(meta)

            node.content = message.get("content", "")
            node.message_data = message
            node.last_accessed = datetime.now(timezone.utc)
            node.token_count = estimate_tokens(message)
            return message_id
        
        # Adaptive tool-message storage: bound tool content in-graph to prevent token blow-up.
        if message.get("role") == "tool":
            content = message.get("content", "")
            truncated, meta = self._truncate_tool_content(content if isinstance(content, str) else str(content))
            if meta:
                message["content"] = truncated
                # Attach metadata to message_data (kept out of the visible content field)
                message.setdefault("_broca_meta", {})
                if isinstance(message["_broca_meta"], dict):
                    message["_broca_meta"].update(meta)

        # Create new node
        node = MessageNode(
            message_id=message_id,
            role=message.get("role", "user"),
            content=message.get("content", ""),
            parent_id=parent_id,
            thread_id=thread_id or self.main_thread_id,
            message_data=message,
        )
        
        # Link to parent if provided
        if parent_id and parent_id in self.nodes:
            if message_id not in self.nodes[parent_id].children:
                self.nodes[parent_id].children.append(message_id)
        else:
            # Root node (no parent)
            if message_id not in self.root_nodes:
                self.root_nodes.append(message_id)
        
        self.nodes[message_id] = node
        self._message_order.append(message_id)
        
        # Update main thread if this is the first message or part of main thread
        if self.main_thread_id is None:
            self.main_thread_id = message_id
        
        # Assign thread_id if not provided
        if not thread_id:
            # If this is a user message and parent is assistant, might be topic switch
            if node.role == "user" and parent_id:
                parent_node = self.nodes.get(parent_id)
                if parent_node and parent_node.role == "assistant":
                    # Check if this is a topic switch (user asking new question)
                    # For now, use main_thread_id as default
                    node.thread_id = self.main_thread_id
                else:
                    node.thread_id = self.main_thread_id
            else:
                node.thread_id = self.main_thread_id
        
        return message_id
    
    def get_thread_context(self, thread_id: Optional[str] = None) -> List[Dict[str, any]]:
        """
        Get context for a specific thread.
        
        Args:
            thread_id: Thread identifier (defaults to main thread)
            
        Returns:
            List of messages in thread context
        """
        if not thread_id:
            thread_id = self.main_thread_id
        
        if not thread_id:
            return []
        
        # Get all messages in this thread
        thread_messages = [
            node.message_data
            for node in self.nodes.values()
            if node.thread_id == thread_id and node.message_data
        ]
        
        # Sort by insertion order
        thread_messages.sort(
            key=lambda m: self._message_order.index(m.get("message_id", ""))
            if m.get("message_id") in self._message_order
            else len(self._message_order)
        )
        
        return thread_messages
    
    def build_thread_path(self, message_id: str) -> List[str]:
        """
        Get path from root to message.
        
        Args:
            message_id: Target message ID
            
        Returns:
            List of message IDs from root to target (inclusive)
        """
        if message_id not in self.nodes:
            return []
        
        path = []
        current_id = message_id
        
        # Walk up to root
        while current_id:
            if current_id in path:  # Cycle detection
                break
            path.insert(0, current_id)
            node = self.nodes.get(current_id)
            if not node or not node.parent_id:
                break
            current_id = node.parent_id
        
        return path
    
    def identify_main_thread(self, token_budget: Optional[int] = None) -> List[str]:
        """
        Identify the main conversation thread.
        
        The main thread is the path with:
        - Most user messages (user messages indicate thread activity)
        - Longest path from root to most recent message
        - Highest message frequency
        
        Returns:
            List of message IDs in main thread (from root to most recent)
        """
        if not self.nodes:
            return []

        # Budgeted main-thread selection (prevents must-keep blow-up).
        # We keep the most recent part of the main path up to a token budget and always include system messages.
        if token_budget is not None and token_budget > 0:
            # System messages are always anchors
            system_ids = [msg_id for msg_id, node in self.nodes.items() if node.role == "system"]
            summary_ids = [
                msg_id
                for msg_id, node in self.nodes.items()
                if node.message_data and bool(node.message_data.get("_broca_summary"))
            ]

            # Reuse the same thread-selection logic as the non-budgeted path:
            # pick the best-scoring root->leaf path (prevents recent orphan roots from becoming main thread).
            most_recent_id: Optional[str] = None
            most_recent_time = None
            for msg_id, node in self.nodes.items():
                if most_recent_time is None or node.last_accessed > most_recent_time:
                    most_recent_time = node.last_accessed
                    most_recent_id = msg_id

            if not most_recent_id:
                return system_ids

            main_thread = self.build_thread_path(most_recent_id)

            if len(self.root_nodes) > 1:
                best_path = main_thread
                best_score = self._score_thread_path(main_thread)
                for root_id in self.root_nodes:
                    path = self._find_longest_path_from_root(root_id)
                    score = self._score_thread_path(path)
                    if score > best_score or (score == best_score and len(path) > len(best_path)):
                        best_path = path
                        best_score = score
                main_thread = best_path

            if not main_thread:
                return system_ids

            # Budget the suffix (most recent portion) of the chosen main thread.
            kept_rev: List[str] = []
            used = 0
            for msg_id in reversed(main_thread):
                if msg_id in kept_rev:
                    break
                node = self.nodes.get(msg_id)
                if not node:
                    continue
                cost = int(node.token_count or estimate_tokens(node.message_data or node.content))
                if kept_rev and used + cost > token_budget:
                    break
                kept_rev.append(msg_id)
                used += cost

            # Return chronological: system anchors first (stable), then the budgeted path.
            path = list(dict.fromkeys(system_ids + summary_ids + list(reversed(kept_rev))))
            return path
        
        # Find most recent message
        most_recent_id = None
        most_recent_time = None
        
        for msg_id, node in self.nodes.items():
            if most_recent_time is None or node.last_accessed > most_recent_time:
                most_recent_time = node.last_accessed
                most_recent_id = msg_id
        
        if not most_recent_id:
            return []
        
        # Build path to most recent message
        main_thread = self.build_thread_path(most_recent_id)
        
        # If we have multiple root nodes, find the best path
        if len(self.root_nodes) > 1:
            best_path = main_thread
            best_score = self._score_thread_path(main_thread)
            
            for root_id in self.root_nodes:
                path = self._find_longest_path_from_root(root_id)
                score = self._score_thread_path(path)
                if score > best_score or (score == best_score and len(path) > len(best_path)):
                    best_path = path
                    best_score = score
            
            main_thread = best_path
        
        return main_thread
    
    def _score_thread_path(self, path: List[str]) -> float:
        """
        Score a thread path based on activity and importance.
        
        Higher score = more important thread.
        
        Args:
            path: List of message IDs in path
            
        Returns:
            Thread importance score
        """
        if not path:
            return 0.0
        
        score = 0.0
        
        # Count user messages (indicates thread activity)
        user_count = sum(1 for msg_id in path if self.nodes.get(msg_id, MessageNode("", "", "")).role == "user")
        score += user_count * 2.0  # User messages are important
        
        # Path length bonus
        score += len(path) * 0.5
        
        # Recency bonus (more recent = higher score)
        for msg_id in path[-5:]:  # Last 5 messages
            node = self.nodes.get(msg_id)
            if node:
                age_hours = (datetime.now(timezone.utc) - node.last_accessed).total_seconds() / 3600.0
                score += max(0, 1.0 - age_hours / 24.0)  # Decay over 24 hours
        
        return score
    
    def _find_longest_path_from_root(self, root_id: str) -> List[str]:
        """Find longest path starting from a root node."""
        if root_id not in self.nodes:
            return []
        
        def dfs(node_id: str, path: List[str]) -> List[str]:
            """Depth-first search for longest path."""
            if node_id in path:  # Cycle detection
                return path
            
            path = path + [node_id]
            node = self.nodes.get(node_id)
            if not node:
                return path
            
            longest = path
            for child_id in node.children:
                child_path = dfs(child_id, path)
                if len(child_path) > len(longest):
                    longest = child_path
            
            return longest
        
        return dfs(root_id, [])
    
    def identify_orphans(self, recent_message_ids: Set[str]) -> Set[str]:
        """
        Find orphaned nodes with no path to recent messages.
        
        Args:
            recent_message_ids: Set of recent message IDs to check connectivity
            
        Returns:
            Set of orphaned message IDs
        """
        orphans: Set[str] = set()
        
        # Build reachability map: which nodes can reach recent messages
        reachable: Set[str] = set(recent_message_ids)
        
        # BFS from recent messages backwards to find all reachable nodes
        queue = list(recent_message_ids)
        visited = set(recent_message_ids)
        
        while queue:
            current_id = queue.pop(0)
            node = self.nodes.get(current_id)
            if not node:
                continue
            
            reachable.add(current_id)
            
            # Check parent
            if node.parent_id and node.parent_id not in visited:
                visited.add(node.parent_id)
                queue.append(node.parent_id)
            
            # Check children
            for child_id in node.children:
                if child_id not in visited:
                    visited.add(child_id)
                    queue.append(child_id)
        
        # All nodes not in reachable set are orphans
        for msg_id in self.nodes:
            if msg_id not in reachable:
                orphans.add(msg_id)
                self.nodes[msg_id].is_orphan = True
        
        return orphans
    
    def compute_relevance_scores(self, main_thread_ids: Set[str], recent_ids: Optional[Set[str]] = None) -> None:
        """
        Compute relevance scores for all nodes.
        
        Args:
            main_thread_ids: Set of message IDs in main thread
            recent_ids: Optional set of message IDs considered recent (defaults to recent on main thread)
        """
        # Default: define \"recent\" as the last N messages on the main thread (not global),
        # to avoid force-keeping unrelated orphan roots that happen to be inserted late.
        if recent_ids is None:
            recent_count = self.min_turns_retained * 2  # Conservative estimate
            recent_ids = set(self._message_order[-recent_count:]) & set(main_thread_ids)
        
        for msg_id, node in self.nodes.items():
            is_main_thread = msg_id in main_thread_ids
            is_recent = msg_id in recent_ids
            
            node.relevance_score = compute_relevance_score(
                node=node,
                is_main_thread=is_main_thread,
                is_recent=is_recent,
                main_thread_boost=self.main_thread_boost,
            )
    
    def prune_to_fit(
        self,
        max_tokens: int,
        safety_margin: float = 0.95,
    ) -> Tuple[List[str], int]:
        """
        Prune graph to fit within token limit.
        
        Preserves main thread and relevant branches while removing orphans
        and low-relevance nodes.
        
        Args:
            max_tokens: Maximum token limit
            safety_margin: Safety margin (0.95 = 95% of max)
            
        Returns:
            Tuple of (list of message IDs to keep, estimated tokens)
        """
        if not self.nodes:
            return [], 0
        
        effective_max = int(max_tokens * safety_margin)

        # Identify main thread (budgeted to avoid unbounded must-keep growth)
        main_budget = int(effective_max * self.main_thread_token_budget_ratio)
        main_thread = self.identify_main_thread(token_budget=main_budget)
        main_thread_ids = set(main_thread)
        
        # Get recent messages (from main thread tail, not global insertion order)
        recent_count = self.min_turns_retained * 2
        recent_ids = set(main_thread[-recent_count:]) if main_thread else set()
        
        # Identify orphans
        orphans = self.identify_orphans(recent_ids)
        
        # Identify tool call chains
        tool_chains = self._identify_tool_call_chains()
        
        # Compute relevance scores
        self.compute_relevance_scores(main_thread_ids, recent_ids=recent_ids)
        
        # Track reasons for telemetry
        selection_reasons: Dict[str, str] = {}

        # Always keep: main thread + recent messages (filter out non-existent)
        must_keep: Set[str] = {msg_id for msg_id in (main_thread_ids | recent_ids) if msg_id in self.nodes}
        for mid in must_keep:
            if mid in main_thread_ids:
                selection_reasons[mid] = "main_thread"
            elif mid in recent_ids:
                selection_reasons[mid] = "recent"
        
        # Preserve tool chains: if any message in a chain is kept, keep entire chain
        for chain_id, chain_messages in tool_chains.items():
            if any(msg_id in must_keep for msg_id in chain_messages):
                # Keep entire chain (filter out non-existent)
                must_keep.update({msg_id for msg_id in chain_messages if msg_id in self.nodes})
                for mid in chain_messages:
                    if mid in self.nodes:
                        selection_reasons[mid] = "tool_chain"
        
        # Calculate tokens for must-keep messages
        must_keep_messages = [self.nodes[msg_id].message_data for msg_id in must_keep if msg_id in self.nodes and self.nodes[msg_id].message_data]
        must_keep_tokens = estimate_messages_tokens(must_keep_messages) if must_keep_messages else 0
        
        # If must-keep already exceeds limit, return just main thread + minimum recent
        if must_keep_tokens > effective_max:
            # Keep only main thread + absolute minimum
            minimal_recent = set(self._message_order[-self.min_turns_retained:])
            minimal_keep = main_thread_ids | minimal_recent
            minimal_messages = [self.nodes[msg_id].message_data for msg_id in minimal_keep if self.nodes[msg_id].message_data]
            minimal_tokens = estimate_messages_tokens(minimal_messages) if minimal_messages else 0
            
            # If minimal set still exceeds limit, truncate it
            if minimal_tokens > effective_max:
                # Identify recent tool chains that MUST be kept intact
                # This prevents the model from losing context mid-task
                recent_tool_chain_ids = self._get_protected_tool_chain_ids(minimal_recent)
                
                # Sort messages by priority: system first, recent tool chains, then main thread, then by recency
                def message_priority(msg_id: str) -> tuple:
                    node = self.nodes.get(msg_id)
                    if not node:
                        return (4, 0)  # Lowest priority
                    # Priority: 0 = system, 1 = recent tool chain, 2 = main thread, 3 = recent, 4 = other
                    priority = 4
                    if node.role == "system":
                        priority = 0
                    elif msg_id in recent_tool_chain_ids:
                        # Recent tool chains get very high priority to prevent mid-task context loss
                        priority = 1
                    elif msg_id in main_thread_ids:
                        priority = 2
                    elif msg_id in minimal_recent:
                        priority = 3
                    # Recency: higher index = more recent
                    try:
                        recency = self._message_order.index(msg_id)
                    except ValueError:
                        recency = 0
                    return (priority, -recency)  # Negative for descending order
                
                # Sort message IDs by priority
                sorted_msg_ids = sorted(minimal_keep | recent_tool_chain_ids, key=message_priority)
                
                # Build truncated set, keeping highest priority messages
                truncated_messages = []
                truncated_tokens = 0
                truncated_msg_ids = []
                
                # Always keep system message if present
                system_msg_id = None
                for msg_id in sorted_msg_ids:
                    node = self.nodes.get(msg_id)
                    if node and node.role == "system":
                        system_msg_id = msg_id
                        break
                
                if system_msg_id:
                    system_msg = self.nodes[system_msg_id].message_data
                    if system_msg:
                        system_tokens = estimate_messages_tokens([system_msg])
                        if system_tokens <= effective_max:
                            truncated_messages.append(system_msg)
                            truncated_tokens = system_tokens
                            truncated_msg_ids.append(system_msg_id)
                
                # Add messages in priority order until we hit the limit
                # Track which assistant messages with tool_calls are kept
                kept_assistants_with_tool_calls: Set[str] = set()
                
                for msg_id in sorted_msg_ids:
                    if msg_id in truncated_msg_ids:
                        continue
                    
                    node = self.nodes.get(msg_id)
                    if not node or not node.message_data:
                        continue
                    
                    # If this is a tool message, check if its assistant is kept
                    if node.role == "tool":
                        # Find the assistant message that contains the tool_calls for this tool
                        assistant_id = self._find_assistant_for_tool_message(msg_id)
                        if not assistant_id:
                            # Can't find assistant, skip this tool message
                            continue
                        if assistant_id not in truncated_msg_ids:
                            # Assistant not kept, skip this tool message
                            continue
                        # Assistant is kept, mark it (will add tool message below)
                        kept_assistants_with_tool_calls.add(assistant_id)
                    
                    msg = node.message_data
                    msg_tokens = estimate_messages_tokens([msg])
                    
                    # Check if adding this message would exceed limit
                    if node.role == "assistant" and node.message_data.get("tool_calls"):
                        tool_ids, tool_tokens, is_complete = self._get_tool_message_ids_and_tokens_for_assistant(msg_id)
                        if not is_complete:
                            # Do not include tool_calls without complete tool responses.
                            continue
                        bundle_cost = msg_tokens + tool_tokens
                        if truncated_tokens + bundle_cost > effective_max:
                            continue
                        # Keep assistant + all tool responses as an atomic bundle (reserve tokens now)
                        truncated_messages.append(msg)
                        truncated_msg_ids.append(msg_id)
                        truncated_tokens += msg_tokens
                        kept_assistants_with_tool_calls.add(msg_id)
                        for tid in tool_ids:
                            if tid in truncated_msg_ids:
                                continue
                            tnode = self.nodes.get(tid)
                            if tnode and tnode.message_data:
                                truncated_messages.append(tnode.message_data)
                                truncated_msg_ids.append(tid)
                                truncated_tokens += estimate_messages_tokens([tnode.message_data])
                        continue

                    if truncated_tokens + msg_tokens <= effective_max:
                        truncated_messages.append(msg)
                        truncated_tokens += msg_tokens
                        truncated_msg_ids.append(msg_id)
                    else:
                        # Can't fit this message; skip and keep trying smaller/later items
                        continue
                
                # Tool messages are added atomically with their assistant tool_calls above.
                
                # Remove orphaned tool messages (tool messages whose assistant was removed)
                truncated_msg_ids = self._remove_orphaned_tool_messages(truncated_msg_ids)
                
                # Rebuild truncated_messages after removing orphans
                truncated_messages = [
                    self.nodes[msg_id].message_data
                    for msg_id in truncated_msg_ids
                    if msg_id in self.nodes and self.nodes[msg_id].message_data
                ]
                
                # Ensure we have at least one user/assistant pair if possible
                if not truncated_msg_ids or len(truncated_msg_ids) == 1:
                    # Try to add at least the most recent user/assistant pair
                    for msg_id in reversed(self._message_order):
                        if msg_id in truncated_msg_ids:
                            continue
                        node = self.nodes.get(msg_id)
                        if node and node.message_data and node.role in ("user", "assistant"):
                            # Skip assistants with tool_calls if we can't fit their tool messages
                            if (node.role == "assistant" and node.message_data.get("tool_calls")):
                                tool_ids, tool_tokens, is_complete = self._get_tool_message_ids_and_tokens_for_assistant(msg_id)
                                msg_tokens = estimate_messages_tokens([node.message_data])
                                if (not is_complete) or (truncated_tokens + msg_tokens + tool_tokens > effective_max):
                                    continue
                            
                            msg = node.message_data
                            msg_tokens = estimate_messages_tokens([msg])
                            if truncated_tokens + msg_tokens <= effective_max:
                                truncated_messages.append(msg)
                                truncated_tokens += msg_tokens
                                truncated_msg_ids.append(msg_id)
                                # Add its tool messages too
                                if node.role == "assistant" and node.message_data.get("tool_calls"):
                                    for tid in tool_ids:
                                        tnode = self.nodes.get(tid)
                                        if tnode and tnode.message_data and tid not in truncated_msg_ids:
                                            tmsg_tokens = estimate_messages_tokens([tnode.message_data])
                                            if truncated_tokens + tmsg_tokens <= effective_max:
                                                truncated_messages.append(tnode.message_data)
                                                truncated_tokens += tmsg_tokens
                                                truncated_msg_ids.append(tid)
                                break
                
                final_tokens = estimate_messages_tokens(truncated_messages) if truncated_messages else 0
                
                # Count how many tool chain messages were preserved
                preserved_tool_chain_count = len([mid for mid in truncated_msg_ids if mid in recent_tool_chain_ids])
                
                logger.warning(
                    f"Must-keep messages exceed token limit ({must_keep_tokens} > {effective_max}), "
                    f"minimal set also exceeded ({minimal_tokens} > {effective_max}), "
                    f"truncated to {len(truncated_msg_ids)} messages ({final_tokens} tokens), "
                    f"preserved {preserved_tool_chain_count} messages from recent tool chains"
                )
                return truncated_msg_ids, final_tokens
            
            # Validate and remove orphaned tool messages from minimal_keep
            minimal_keep_list = self._remove_orphaned_tool_messages(list(minimal_keep))
            minimal_messages = [self.nodes[msg_id].message_data for msg_id in minimal_keep_list if msg_id in self.nodes and self.nodes[msg_id].message_data]
            minimal_tokens = estimate_messages_tokens(minimal_messages) if minimal_messages else 0
            
            logger.warning(
                f"Must-keep messages exceed token limit ({must_keep_tokens} > {effective_max}), "
                f"keeping only minimal set ({minimal_tokens} tokens)"
            )
            return minimal_keep_list, minimal_tokens
        
        # Start with must-keep, then add by relevance
        to_keep: Set[str] = must_keep.copy()
        available_tokens = effective_max - must_keep_tokens
        
        # Track which assistants with tool_calls are kept
        kept_assistants_with_tool_calls: Set[str] = set()
        for msg_id in must_keep:
            node = self.nodes.get(msg_id)
            if node and node.role == "assistant" and node.message_data:
                if node.message_data.get("tool_calls"):
                    kept_assistants_with_tool_calls.add(msg_id)
        
        # Sort remaining nodes by relevance (excluding orphans and must-keep)
        candidates = [
            (msg_id, node)
            for msg_id, node in self.nodes.items()
            if msg_id not in to_keep and msg_id not in orphans
        ]
        candidates.sort(key=lambda x: x[1].relevance_score, reverse=True)
        
        # Add candidates until we run out of tokens
        current_tokens = must_keep_tokens
        for msg_id, node in candidates:
            # If this is a tool message, only add if its assistant is kept
            if node.role == "tool":
                assistant_id = self._find_assistant_for_tool_message(msg_id)
                if not assistant_id or assistant_id not in to_keep:
                    # Assistant not kept, skip this tool message
                    continue
            
            # If this is an assistant with tool_calls, check if we can fit its tool messages
            if node.role == "assistant" and node.message_data and node.message_data.get("tool_calls"):
                tool_ids, tool_tokens, is_complete = self._get_tool_message_ids_and_tokens_for_assistant(msg_id)
                if not is_complete:
                    # Never include tool_calls without all required tool responses.
                    continue
                if current_tokens + node.token_count + tool_tokens > effective_max:
                    continue
                # Add as atomic bundle and reserve token cost now
                to_keep.add(msg_id)
                current_tokens += int(node.token_count)
                kept_assistants_with_tool_calls.add(msg_id)
                for tid in tool_ids:
                    if tid in to_keep:
                        continue
                    tnode = self.nodes.get(tid)
                    if tnode and tnode.message_data:
                        to_keep.add(tid)
                        current_tokens += int(tnode.token_count)
                continue
            
            if current_tokens + node.token_count <= effective_max:
                to_keep.add(msg_id)
                current_tokens += node.token_count
                if msg_id not in selection_reasons:
                    selection_reasons[msg_id] = "relevance"
            else:
                continue
        
        # Tool messages for kept assistants are added atomically with their assistant above.
        
        # Build final message list in order
        kept_messages = [
            self.nodes[msg_id].message_data
            for msg_id in self._message_order
            if msg_id in to_keep and self.nodes[msg_id].message_data
        ]
        
        final_tokens = estimate_messages_tokens(kept_messages) if kept_messages else 0
        
        logger.debug(
            f"Pruned context: {len(self.nodes)} -> {len(to_keep)} messages, "
            f"{final_tokens} tokens (limit: {effective_max})"
        )
        
        # Validate and remove orphaned tool messages before returning
        to_keep = self._remove_orphaned_tool_messages(list(to_keep))
        
        # Rebuild kept_messages after removing orphans
        kept_messages = [
            self.nodes[msg_id].message_data
            for msg_id in self._message_order
            if msg_id in to_keep and self.nodes[msg_id].message_data
        ]
        
        final_tokens = estimate_messages_tokens(kept_messages) if kept_messages else 0
        
        logger.debug(
            f"Pruned context: {len(self.nodes)} -> {len(to_keep)} messages, "
            f"{final_tokens} tokens (limit: {effective_max})"
        )
        
        # Store last selection reasons for telemetry
        self._last_selection_reasons = selection_reasons
        return to_keep, final_tokens
    
    def _find_assistant_for_tool_message(self, tool_msg_id: str) -> Optional[str]:
        """
        Find the assistant message that contains tool_calls for a given tool message.
        
        Args:
            tool_msg_id: Message ID of the tool message
            
        Returns:
            Message ID of the assistant message with tool_calls, or None if not found
        """
        tool_node = self.nodes.get(tool_msg_id)
        if not tool_node or tool_node.role != "tool":
            return None
        
        tool_call_id = None
        if tool_node.message_data:
            tool_call_id = tool_node.message_data.get("tool_call_id")
        
        if not tool_call_id:
            return None
        
        # Search backwards in message order to find assistant with matching tool_calls
        for msg_id in reversed(self._message_order):
            if msg_id == tool_msg_id:
                continue
            
            node = self.nodes.get(msg_id)
            if not node or node.role != "assistant":
                continue
            
            if node.message_data:
                tool_calls = node.message_data.get("tool_calls", [])
                if tool_calls:
                    # Check if any tool_call has matching ID
                    for tc in tool_calls:
                        if isinstance(tc, dict) and tc.get("id") == tool_call_id:
                            return msg_id
        
        return None
    
    def _estimate_tool_messages_tokens(self, assistant_msg_id: str) -> int:
        """
        Estimate tokens for all tool messages associated with an assistant message.
        
        Args:
            assistant_msg_id: Message ID of the assistant message with tool_calls
            
        Returns:
            Estimated token count for all associated tool messages
        """
        assistant_node = self.nodes.get(assistant_msg_id)
        if not assistant_node or not assistant_node.message_data:
            return 0
        
        tool_calls = assistant_node.message_data.get("tool_calls", [])
        if not tool_calls:
            return 0
        
        tool_call_ids = {tc.get("id") for tc in tool_calls if isinstance(tc, dict) and tc.get("id")}
        if not tool_call_ids:
            return 0
        
        # Find all tool messages with matching tool_call_id
        tool_messages = []
        for msg_id in self._message_order:
            node = self.nodes.get(msg_id)
            if not node or node.role != "tool" or not node.message_data:
                continue
            
            tool_call_id = node.message_data.get("tool_call_id")
            if tool_call_id in tool_call_ids:
                tool_messages.append(node.message_data)
        
        return estimate_messages_tokens(tool_messages) if tool_messages else 0

    def _get_tool_message_ids_and_tokens_for_assistant(self, assistant_msg_id: str) -> tuple[List[str], int, bool]:
        """
        Get tool message IDs + token cost for tool responses required by an assistant tool_calls message.

        Returns:
            (tool_msg_ids_in_order, token_cost, is_complete)
        """
        assistant_node = self.nodes.get(assistant_msg_id)
        if not assistant_node or not assistant_node.message_data:
            return ([], 0, True)

        tool_calls = assistant_node.message_data.get("tool_calls", [])
        if not tool_calls:
            return ([], 0, True)

        tool_call_ids = {tc.get("id") for tc in tool_calls if isinstance(tc, dict) and tc.get("id")}
        if not tool_call_ids:
            return ([], 0, True)

        tool_msg_ids: List[str] = []
        cost = 0
        seen_ids: Set[str] = set()
        for msg_id in self._message_order:
            node = self.nodes.get(msg_id)
            if not node or node.role != "tool":
                continue
            if not node.message_data:
                continue
            tcid = node.message_data.get("tool_call_id")
            if tcid in tool_call_ids and msg_id not in tool_msg_ids:
                tool_msg_ids.append(msg_id)
                cost += int(node.token_count)
                seen_ids.add(str(tcid))

        is_complete = seen_ids == {str(x) for x in tool_call_ids}
        return (tool_msg_ids, cost, is_complete)
    
    def _remove_orphaned_tool_messages(self, msg_ids: List[str]) -> List[str]:
        """
        Remove tool messages that don't have a preceding assistant message with tool_calls.
        
        Args:
            msg_ids: List of message IDs to validate
            
        Returns:
            List of message IDs with orphaned tool messages removed
        """
        msg_id_set = set(msg_ids)
        valid_msg_ids = []
        removed_count = 0
        
        for msg_id in msg_ids:
            node = self.nodes.get(msg_id)
            if not node:
                continue
            
            # If it's a tool message, check if its assistant is in the set
            if node.role == "tool":
                assistant_id = self._find_assistant_for_tool_message(msg_id)
                if assistant_id and assistant_id in msg_id_set:
                    # Assistant is kept, keep this tool message
                    valid_msg_ids.append(msg_id)
                elif assistant_id:
                    # Assistant not in set, remove this tool message
                    removed_count += 1
                    logger.debug(
                        f"Removing orphaned tool message {msg_id} (assistant {assistant_id} not in kept set)"
                    )
                else:
                    # Couldn't find assistant, remove to be safe
                    removed_count += 1
                    logger.debug(f"Removing tool message {msg_id} (no assistant found)")
            else:
                # Not a tool message, keep it
                valid_msg_ids.append(msg_id)
        
        if removed_count > 0:
            logger.warning(
                f"Removed {removed_count} orphaned tool message(s) during truncation"
            )
        
        return valid_msg_ids
    
    def pluck_oldest_until_under_limit(
        self,
        max_tokens: int,
        min_recent_to_keep: Optional[int] = None,
    ) -> List[str]:
        """
        Simple oldest-first node plucking to stay under token limit.
        
        Algorithm:
        1. Get all non-system nodes sorted by insertion order (oldest first)
        2. Protect recent N messages from plucking
        3. Pluck oldest nodes until total tokens < max_tokens
        4. Actually remove plucked nodes from the graph
        5. Return list of plucked message IDs (for session to sync)
        
        Args:
            max_tokens: Maximum token budget
            min_recent_to_keep: Override for minimum recent messages to keep (default: self.min_recent_to_keep)
            
        Returns:
            List of message IDs that were plucked (removed from graph)
        """
        if min_recent_to_keep is None:
            min_recent_to_keep = self.min_recent_to_keep
        
        plucked_ids: List[str] = []
        
        with self._lock:
            # Get current token count
            all_messages = [node.message_data for node in self.nodes.values() if node.message_data]
            current_tokens = estimate_messages_tokens(all_messages) if all_messages else 0
            
            # If we're under limit, nothing to do
            if current_tokens <= max_tokens:
                logger.debug(f"Context within limit: {current_tokens}/{max_tokens} tokens, no plucking needed")
                self._last_plucked_ids = []
                return []
            
            logger.info(f"Context over limit: {current_tokens}/{max_tokens} tokens, plucking oldest nodes...")
            
            # Identify protected messages (system + recent N)
            protected_ids: Set[str] = set()
            
            # Always protect system messages
            for msg_id, node in self.nodes.items():
                if node.role == "system":
                    protected_ids.add(msg_id)
            
            # Protect the most recent N messages (by insertion order)
            recent_ids = set(self._message_order[-min_recent_to_keep:]) if len(self._message_order) > min_recent_to_keep else set(self._message_order)
            protected_ids.update(recent_ids)
            
            # Log protection details for debugging
            logger.debug(
                f"Protecting {len(protected_ids)} messages from plucking "
                f"(min_recent_to_keep={min_recent_to_keep}, "
                f"total_messages={len(self._message_order)}, "
                f"system_messages={len([n for n in self.nodes.values() if n.role == 'system'])})"
            )
            
            # Get pluckable candidates (oldest first = earliest in _message_order)
            pluckable = [
                msg_id for msg_id in self._message_order
                if msg_id not in protected_ids and msg_id in self.nodes
            ]
            
            # Pluck oldest nodes until we're under budget
            for msg_id in pluckable:
                node = self.nodes.get(msg_id)
                if not node or not node.message_data:
                    continue
                
                # Pluck this node
                self._pluck_node(msg_id)
                plucked_ids.append(msg_id)
                
                # Recalculate tokens
                remaining_messages = [n.message_data for n in self.nodes.values() if n.message_data]
                current_tokens = estimate_messages_tokens(remaining_messages) if remaining_messages else 0
                
                # Check if we're under limit now
                if current_tokens <= max_tokens:
                    break

            # Cleanup: remove disconnected components (orphans) created by plucking,
            # and tombstone them so they won't be re-added from replayed history.
            if self.nodes and protected_ids:
                orphans = self.identify_orphans(protected_ids)
                if orphans:
                    for orphan_id in orphans:
                        self._tombstone(orphan_id, "orphan_pruned")
                        orphan_node = self.nodes.pop(orphan_id, None)
                        if not orphan_node:
                            continue
                        if orphan_node.parent_id and orphan_node.parent_id in self.nodes:
                            parent = self.nodes[orphan_node.parent_id]
                            if orphan_id in parent.children:
                                parent.children.remove(orphan_id)
                        if orphan_id in self.root_nodes:
                            self.root_nodes.remove(orphan_id)
                        if orphan_id in self._message_order:
                            self._message_order.remove(orphan_id)
            
            if plucked_ids:
                remaining_count = len(self._message_order)
                logger.info(
                    f"Plucked {len(plucked_ids)} oldest nodes, now at {current_tokens}/{max_tokens} tokens "
                    f"(remaining: {remaining_count} messages, protected: {len(protected_ids)})"
                )
            
            self._last_plucked_ids = plucked_ids
            return plucked_ids
    
    def _pluck_node(self, msg_id: str) -> None:
        """
        Remove a node from the graph completely.
        
        Args:
            msg_id: Message ID to remove
        """
        node = self.nodes.get(msg_id)
        if not node:
            return

        # Tombstone so ConversationSession replay won't re-add it.
        self._tombstone(msg_id, "plucked")
        
        # Remove from parent's children list
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            if msg_id in parent.children:
                parent.children.remove(msg_id)
        
        # Update children to point to grandparent
        for child_id in node.children:
            child = self.nodes.get(child_id)
            if child:
                child.parent_id = node.parent_id
                # Add children to grandparent's children list
                if node.parent_id and node.parent_id in self.nodes:
                    grandparent = self.nodes[node.parent_id]
                    if child_id not in grandparent.children:
                        grandparent.children.append(child_id)
        
        # Remove from root_nodes if applicable
        if msg_id in self.root_nodes:
            self.root_nodes.remove(msg_id)
            # Promote children to root nodes
            for child_id in node.children:
                if child_id not in self.root_nodes:
                    self.root_nodes.append(child_id)
        
        # Remove from message_order
        if msg_id in self._message_order:
            self._message_order.remove(msg_id)
        
        # Remove from nodes dict
        del self.nodes[msg_id]
    
    def get_last_plucked_ids(self) -> List[str]:
        """
        Get message IDs that were plucked in the last call to pluck_oldest_until_under_limit.
        
        This is used by the session to sync its message list with the graph.
        
        Returns:
            List of message IDs that were plucked
        """
        return self._last_plucked_ids.copy()

    def get_messages_for_llm(
        self,
        max_tokens: int,
        safety_margin: float = 0.95,
    ) -> List[Dict[str, any]]:
        """
        Get messages for LLM, plucking oldest nodes if over token limit.
        
        Simple algorithm:
        1. Estimate current token usage
        2. If over limit, pluck oldest nodes (by timestamp) until under
        3. Return remaining messages in order
        
        The plucking REMOVES nodes from the graph (and tombstones their IDs),
        so token count decreases for real without mutating the persisted session history.
        
        Args:
            max_tokens: Maximum token limit
            safety_margin: Safety margin (0.95 = 95% of max)
            
        Returns:
            List of message dictionaries in order
        """
        effective_max = int(max_tokens * safety_margin)
        
        # Pluck oldest nodes if needed (this actually removes them from graph)
        self.pluck_oldest_until_under_limit(effective_max)
        
        # Build message list in insertion order from remaining nodes
        with self._lock:
            messages = []
            for msg_id in self._message_order:
                node = self.nodes.get(msg_id)
                if node and node.message_data:
                    messages.append(node.message_data)
        
        # Final validation: ensure no orphaned tool messages
        messages = self._validate_and_fix_tool_message_ordering(messages)
        
        # Telemetry: write per-message selection reasons if enabled.
        if self._selection_logging_enabled:
            try:
                if self._selection_logger is None:
                    from .context_selection_logger import ContextSelectionLogger
                    self._selection_logger = ContextSelectionLogger(
                        log_file=self._selection_log_file,
                        enabled=True,
                        append=True,
                    )
                run_id = str(uuid.uuid4())
                kept_ids = {m.get("message_id") for m in messages if m.get("message_id")}
                rows = []
                for msg_id, node in self.nodes.items():
                    if not node:
                        continue
                    kept = msg_id in kept_ids
                    rows.append(
                        {
                            "message_id": msg_id,
                            "role": node.role,
                            "token_count": node.token_count,
                            "kept": kept,
                            "kept_reason": self._last_selection_reasons.get(msg_id, "plucking"),
                            "tool_chain_id": node.tool_call_chain_id or "",
                            "is_summary": bool(node.message_data and node.message_data.get("_broca_summary")),
                            "is_compacted": bool(getattr(node, "is_compacted", False)),
                        }
                    )
                self._selection_logger.log(run_id=run_id, rows=rows)
            except Exception as e:
                logger.debug(f"Context selection telemetry failed: {e}", exc_info=True)

        return messages
    
    def _validate_and_fix_tool_message_ordering(self, messages: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Validate and fix tool message ordering in final message list.
        
        Removes:
        - Orphaned tool messages (no preceding assistant with matching tool_calls)
        - Incomplete tool call sequences (assistant with tool_calls that are missing required tool responses)
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of messages with invalid tool sequences removed
        """
        if not messages:
            return messages

        fixed_messages: List[Dict[str, any]] = []
        pending_tool_call_ids: Set[str] = set()
        last_assistant_with_tool_calls_out_idx = -1
        last_assistant_tool_call_ids: Set[str] = set()

        removed_orphan_tool = 0
        removed_incomplete_sequences = 0

        def drop_incomplete_sequence() -> None:
            nonlocal fixed_messages, pending_tool_call_ids, last_assistant_with_tool_calls_out_idx, last_assistant_tool_call_ids, removed_incomplete_sequences
            if pending_tool_call_ids and last_assistant_with_tool_calls_out_idx >= 0:
                removed = len(fixed_messages) - last_assistant_with_tool_calls_out_idx
                fixed_messages = fixed_messages[:last_assistant_with_tool_calls_out_idx]
                removed_incomplete_sequences += removed
            pending_tool_call_ids = set()
            last_assistant_with_tool_calls_out_idx = -1
            last_assistant_tool_call_ids = set()

        for i, msg in enumerate(messages):
            role = msg.get("role")

            if role == "system":
                fixed_messages.append(msg)
                continue

            if role == "assistant":
                tool_calls = msg.get("tool_calls")
                if tool_calls and isinstance(tool_calls, list):
                    # If there was a pending sequence, it's incomplete (we're starting a new assistant/tool_calls block)
                    if pending_tool_call_ids:
                        drop_incomplete_sequence()

                    current_tool_call_ids: Set[str] = set()
                    for tc in tool_calls:
                        if isinstance(tc, dict) and isinstance(tc.get("id"), str):
                            current_tool_call_ids.add(tc["id"])

                    pending_tool_call_ids = current_tool_call_ids.copy()
                    last_assistant_tool_call_ids = current_tool_call_ids.copy()
                    last_assistant_with_tool_calls_out_idx = len(fixed_messages)
                    fixed_messages.append(msg)
                else:
                    # Any non-tool_calls assistant ends a pending sequence; if pending exists, drop it.
                    if pending_tool_call_ids:
                        drop_incomplete_sequence()
                    fixed_messages.append(msg)
                continue

            if role == "tool":
                tool_call_id = msg.get("tool_call_id")
                if isinstance(tool_call_id, str) and tool_call_id in pending_tool_call_ids:
                    fixed_messages.append(msg)
                    pending_tool_call_ids.remove(tool_call_id)
                    if not pending_tool_call_ids:
                        last_assistant_with_tool_calls_out_idx = -1
                        last_assistant_tool_call_ids = set()
                else:
                    removed_orphan_tool += 1
                continue

            # user/other roles: if we're mid tool sequence, it's incomplete -> drop it.
            if pending_tool_call_ids:
                drop_incomplete_sequence()
            fixed_messages.append(msg)

        # If we ended mid tool sequence, drop it.
        if pending_tool_call_ids:
            drop_incomplete_sequence()

        if removed_orphan_tool > 0:
            logger.warning(f"Removed {removed_orphan_tool} orphaned tool message(s) during context validation")
        if removed_incomplete_sequences > 0:
            logger.warning(f"Removed {removed_incomplete_sequences} message(s) from incomplete tool_call sequence(s) during context validation")

        return fixed_messages
    
    def prune_orphans(self) -> int:
        """
        Remove all orphaned nodes from graph.
        
        Returns:
            Number of nodes removed
        """
        recent_ids = set(self._message_order[-self.min_turns_retained * 2:])
        orphans = self.identify_orphans(recent_ids)
        
        removed_count = 0
        for msg_id in orphans:
            node = self.nodes.pop(msg_id, None)
            if node:
                # Remove from parent's children
                if node.parent_id and node.parent_id in self.nodes:
                    if msg_id in self.nodes[node.parent_id].children:
                        self.nodes[node.parent_id].children.remove(msg_id)
                # Remove from root nodes
                if msg_id in self.root_nodes:
                    self.root_nodes.remove(msg_id)
                # Remove from message order
                if msg_id in self._message_order:
                    self._message_order.remove(msg_id)
                removed_count += 1
        
        logger.debug(f"Pruned {removed_count} orphaned nodes")
        return removed_count
    
    def _identify_tool_call_chains(self) -> Dict[str, Set[str]]:
        """
        Identify complete tool call chains.
        
        A tool call chain consists of:
        - Assistant message with tool_calls
        - Tool result messages (one per tool_call)
        - Next assistant message (response after tool results)
        
        Returns:
            Dictionary mapping chain_id to set of message IDs in chain
        """
        chains: Dict[str, Set[str]] = {}
        chain_counter = 0
        
        for msg_id, node in self.nodes.items():
            if node.role != "assistant" or not node.message_data:
                continue
            
            tool_calls = node.message_data.get("tool_calls")
            if not tool_calls:
                continue
            
            # Found assistant with tool_calls - start a chain
            chain_id = f"chain_{chain_counter}"
            chain_counter += 1
            chain_messages = {msg_id}
            
            # Find tool result messages
            tool_call_ids = {tc.get("id") for tc in tool_calls if isinstance(tc, dict)}
            
            for child_id in node.children:
                child_node = self.nodes.get(child_id)
                if not child_node or child_node.role != "tool":
                    continue
                
                tool_call_id = child_node.message_data.get("tool_call_id") if child_node.message_data else None
                if tool_call_id in tool_call_ids:
                    chain_messages.add(child_id)
                    # Find next assistant message (response after tool results)
                    for grandchild_id in child_node.children:
                        grandchild_node = self.nodes.get(grandchild_id)
                        if grandchild_node and grandchild_node.role == "assistant":
                            chain_messages.add(grandchild_id)
                            break
            
            if len(chain_messages) > 1:  # Only store chains with multiple messages
                chains[chain_id] = chain_messages
                # Mark nodes with chain_id
                for chain_msg_id in chain_messages:
                    if chain_msg_id in self.nodes:
                        self.nodes[chain_msg_id].tool_call_chain_id = chain_id
        
        return chains
    
    def validate_graph_integrity(self) -> List[str]:
        """
        Validate graph integrity and return list of issues found.
        
        Returns:
            List of error messages (empty if graph is valid)
        """
        issues = []
        
        # Check parent-child consistency
        for msg_id, node in self.nodes.items():
            if node.parent_id:
                parent = self.nodes.get(node.parent_id)
                if not parent:
                    issues.append(f"Node {msg_id} has parent {node.parent_id} that doesn't exist")
                elif msg_id not in parent.children:
                    issues.append(f"Node {msg_id} not in parent {node.parent_id}'s children")
            
            # Check children exist
            for child_id in node.children:
                child = self.nodes.get(child_id)
                if not child:
                    issues.append(f"Node {msg_id} has child {child_id} that doesn't exist")
                elif child.parent_id != msg_id:
                    issues.append(f"Child {child_id} doesn't point back to parent {msg_id}")
        
        # Check for cycles using DFS (only check parent->child direction, not both)
        visited = set()
        rec_stack = set()
        
        def has_cycle_forward(node_id: str) -> bool:
            """Check for cycles following parent->child direction only."""
            if node_id in rec_stack:
                return True
            if node_id in visited:
                return False
            
            visited.add(node_id)
            rec_stack.add(node_id)
            
            node = self.nodes.get(node_id)
            if node:
                # Only check children (forward direction)
                for child_id in node.children:
                    if has_cycle_forward(child_id):
                        return True
            
            rec_stack.remove(node_id)
            return False
        
        # Check each root node for cycles
        for root_id in self.root_nodes:
            if root_id not in visited:
                if has_cycle_forward(root_id):
                    issues.append(f"Cycle detected involving node {root_id}")
        
        # Also check for bidirectional cycles (parent <-> child)
        # This catches cases where A is parent of B, but B is also parent of A
        for msg_id, node in self.nodes.items():
            if node.parent_id:
                parent = self.nodes.get(node.parent_id)
                if parent:
                    # Check if this node is also a parent of its parent (cycle)
                    if msg_id in parent.children and node.parent_id in node.children:
                        issues.append(f"Bidirectional cycle between {msg_id} and {node.parent_id}")
                    # Also check if parent's parent is this node (backward cycle)
                    if parent.parent_id == msg_id:
                        issues.append(f"Backward cycle: {msg_id} -> {node.parent_id} -> {msg_id}")
        
        # Check message_order consistency
        for msg_id in self._message_order:
            if msg_id not in self.nodes:
                issues.append(f"message_order contains non-existent node {msg_id}")
        
        return issues
    
    def ensure_message_data(self) -> int:
        """
        Ensure all nodes have message_data, reconstructing if missing.
        
        Returns:
            Number of nodes that needed reconstruction
        """
        reconstructed = 0
        
        for msg_id, node in self.nodes.items():
            if not node.message_data:
                # Reconstruct from node fields
                node.message_data = {
                    "role": node.role,
                    "content": node.content,
                    "message_id": node.message_id,
                }
                if node.parent_id:
                    # Try to preserve parent relationship in message_data if needed
                    pass
                reconstructed += 1
        
        return reconstructed
