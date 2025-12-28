"""
Context graph implementation for intelligent conversation context management.

Treats conversation as a tree/graph structure and intelligently prunes
orphaned branches while preserving the main conversation thread.
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

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
    ):
        """
        Initialize context graph.
        
        Args:
            min_turns_retained: Minimum turns to always keep
            orphan_threshold_turns: Turns before branch considered orphan
            main_thread_boost: Boost multiplier for main thread messages
        """
        self.nodes: Dict[str, MessageNode] = {}
        self.root_nodes: List[str] = []
        self.main_thread_id: Optional[str] = None
        self.min_turns_retained = min_turns_retained
        self.orphan_threshold_turns = orphan_threshold_turns
        self.main_thread_boost = main_thread_boost
        self._message_order: List[str] = []  # Track insertion order
        self._tool_chains: Dict[str, Set[str]] = {}  # Map chain_id -> set of message_ids
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
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
        
        # If message already exists, update it
        if message_id in self.nodes:
            node = self.nodes[message_id]
            node.content = message.get("content", "")
            node.message_data = message
            node.last_accessed = datetime.now(timezone.utc)
            node.token_count = estimate_tokens(message)
            return message_id
        
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
    
    def identify_main_thread(self) -> List[str]:
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
    
    def compute_relevance_scores(self, main_thread_ids: Set[str]) -> None:
        """
        Compute relevance scores for all nodes.
        
        Args:
            main_thread_ids: Set of message IDs in main thread
        """
        # Get recent messages (last N by insertion order)
        recent_count = self.min_turns_retained * 2  # Conservative estimate
        recent_ids = set(self._message_order[-recent_count:])
        
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
        
        # Identify main thread
        main_thread = self.identify_main_thread()
        main_thread_ids = set(main_thread)
        
        # Get recent messages
        recent_count = self.min_turns_retained * 2
        recent_ids = set(self._message_order[-recent_count:])
        
        # Identify orphans
        orphans = self.identify_orphans(recent_ids)
        
        # Identify tool call chains
        tool_chains = self._identify_tool_call_chains()
        
        # Compute relevance scores
        self.compute_relevance_scores(main_thread_ids)
        
        # Always keep: main thread + recent messages (filter out non-existent)
        must_keep: Set[str] = {msg_id for msg_id in (main_thread_ids | recent_ids) if msg_id in self.nodes}
        
        # Preserve tool chains: if any message in a chain is kept, keep entire chain
        for chain_id, chain_messages in tool_chains.items():
            if any(msg_id in must_keep for msg_id in chain_messages):
                # Keep entire chain (filter out non-existent)
                must_keep.update({msg_id for msg_id in chain_messages if msg_id in self.nodes})
        
        # Calculate tokens for must-keep messages
        must_keep_messages = [self.nodes[msg_id].message_data for msg_id in must_keep if msg_id in self.nodes and self.nodes[msg_id].message_data]
        must_keep_tokens = estimate_messages_tokens(must_keep_messages) if must_keep_messages else 0
        
        effective_max = int(max_tokens * safety_margin)
        
        # If must-keep already exceeds limit, return just main thread + minimum recent
        if must_keep_tokens > effective_max:
            # Keep only main thread + absolute minimum
            minimal_recent = set(self._message_order[-self.min_turns_retained:])
            minimal_keep = main_thread_ids | minimal_recent
            minimal_messages = [self.nodes[msg_id].message_data for msg_id in minimal_keep if self.nodes[msg_id].message_data]
            minimal_tokens = estimate_messages_tokens(minimal_messages) if minimal_messages else 0
            logger.warning(
                f"Must-keep messages exceed token limit ({must_keep_tokens} > {effective_max}), "
                f"keeping only minimal set ({minimal_tokens} tokens)"
            )
            return list(minimal_keep), minimal_tokens
        
        # Start with must-keep, then add by relevance
        to_keep: Set[str] = must_keep.copy()
        available_tokens = effective_max - must_keep_tokens
        
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
            if current_tokens + node.token_count <= effective_max:
                to_keep.add(msg_id)
                current_tokens += node.token_count
            else:
                break
        
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
        
        return list(to_keep), final_tokens
    
    def get_messages_for_llm(
        self,
        max_tokens: int,
        safety_margin: float = 0.95,
    ) -> List[Dict[str, any]]:
        """
        Get messages for LLM after intelligent pruning.
        
        Args:
            max_tokens: Maximum token limit
            safety_margin: Safety margin (0.95 = 95% of max)
            
        Returns:
            List of message dictionaries in order
        """
        to_keep, _ = self.prune_to_fit(max_tokens, safety_margin)
        
        # Build message list in insertion order
        messages = []
        for msg_id in self._message_order:
            if msg_id in to_keep:
                node = self.nodes[msg_id]
                if node.message_data:
                    messages.append(node.message_data)
        
        return messages
    
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

