"""
Event logger for conversation events.

Logs all user messages, assistant messages, tool calls, and tool results
to an append-only JSONL file for summarization.
"""

from __future__ import annotations

import json
import hashlib
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class EventLogger:
    """
    Append-only event logger for conversation events.
    
    Logs events to JSONL files with the format: {session_id}_raw.jsonl
    Each event includes event_id, timestamp, type, and content.
    """
    
    def __init__(self, log_dir: str | Path) -> None:
        """
        Initialize event logger.
        
        Args:
            log_dir: Directory where event log files will be stored
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized EventLogger with log_dir: {self.log_dir}")
    
    def _get_log_file(self, session_id: str) -> Path:
        """Get the log file path for a session."""
        return self.log_dir / f"{session_id}_raw.jsonl"
    
    def _compute_sha256(self, content: str | Dict[str, Any]) -> str:
        """
        Compute SHA256 hash of content.
        
        Args:
            content: String or dictionary to hash
            
        Returns:
            Hexadecimal SHA256 hash
        """
        if isinstance(content, dict):
            # Serialize dict with sorted keys for consistency
            json_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
            content_bytes = json_str.encode('utf-8')
        else:
            content_bytes = str(content).encode('utf-8')
        
        return hashlib.sha256(content_bytes).hexdigest()
    
    def _generate_event_id(self) -> str:
        """
        Generate a unique event ID.
        
        Returns:
            Unique event ID string
        """
        return f"evt_{uuid.uuid4().hex}"
    
    def _write_event(self, session_id: str, event: Dict[str, Any]) -> str:
        """
        Write an event to the log file (append-only).
        
        Args:
            session_id: Session identifier
            event: Event dictionary to write
            
        Returns:
            Event ID
        """
        log_file = self._get_log_file(session_id)
        
        # Ensure event has required fields
        if "event_id" not in event:
            event["event_id"] = self._generate_event_id()
        if "ts" not in event:
            event["ts"] = datetime.now(timezone.utc).isoformat()
        
        # Append to file (create if doesn't exist)
        with open(log_file, 'a', encoding='utf-8') as f:
            json_line = json.dumps(event, ensure_ascii=False)
            f.write(json_line + '\n')
        
        logger.debug(f"Logged event {event['event_id']} of type {event.get('type')} for session {session_id}")
        return event["event_id"]
    
    def log_user_message(self, session_id: str, content: str) -> str:
        """
        Log a user message event.
        
        Args:
            session_id: Session identifier
            content: User message content
            
        Returns:
            Event ID
        """
        event = {
            "type": "user_message",
            "role": "user",
            "content": content,
            "sha256": self._compute_sha256(content),
        }
        return self._write_event(session_id, event)
    
    def log_assistant_message(self, session_id: str, content: str) -> str:
        """
        Log an assistant message event.
        
        Args:
            session_id: Session identifier
            content: Assistant message content
            
        Returns:
            Event ID
        """
        event = {
            "type": "assistant_message",
            "role": "assistant",
            "content": content,
            "sha256": self._compute_sha256(content),
        }
        return self._write_event(session_id, event)
    
    def log_tool_call(
        self,
        session_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_call_id: Optional[str] = None
    ) -> str:
        """
        Log a tool call event.
        
        Args:
            session_id: Session identifier
            tool_name: Name of the tool being called
            tool_args: Tool arguments
            tool_call_id: Optional tool call ID from LLM
            
        Returns:
            Event ID
        """
        event = {
            "type": "tool_call",
            "tool_name": tool_name,
            "tool_args": tool_args,
            "tool_call_id": tool_call_id,
            "sha256": self._compute_sha256(tool_args),
        }
        return self._write_event(session_id, event)
    
    def log_tool_result(
        self,
        session_id: str,
        tool_name: str,
        tool_result: Dict[str, Any],
        tool_call_id: Optional[str] = None
    ) -> str:
        """
        Log a tool result event.
        
        Args:
            session_id: Session identifier
            tool_name: Name of the tool that produced the result
            tool_result: Tool result content
            tool_call_id: Optional tool call ID from LLM
            
        Returns:
            Event ID
        """
        event = {
            "type": "tool_result",
            "tool_name": tool_name,
            "tool_result": tool_result,
            "tool_call_id": tool_call_id,
            "sha256": self._compute_sha256(tool_result),
        }
        return self._write_event(session_id, event)
    
    def get_events(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of event dictionaries
        """
        log_file = self._get_log_file(session_id)
        
        if not log_file.exists():
            return []
        
        events = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse event line: {e}")
        
        return events
    
    def get_events_after(
        self,
        session_id: str,
        after_event_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get events after a specific event ID.
        
        Args:
            session_id: Session identifier
            after_event_id: Event ID to start after
            
        Returns:
            List of event dictionaries after the specified event
        """
        all_events = self.get_events(session_id)
        
        # Find the index of the event with the specified ID
        start_index = 0
        for i, event in enumerate(all_events):
            if event.get("event_id") == after_event_id:
                start_index = i + 1
                break
        
        return all_events[start_index:]
    
    def get_latest_event_id(self, session_id: str) -> Optional[str]:
        """
        Get the latest event ID for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Latest event ID, or None if no events exist
        """
        events = self.get_events(session_id)
        if not events:
            return None
        return events[-1].get("event_id")
    
    def get_event_ids_set(self, session_id: str) -> set[str]:
        """
        Get all event IDs as a set for efficient membership testing.
        
        This method is more efficient than get_events() when you only need
        to check if event IDs exist, as it avoids loading full event data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Set of event ID strings
        """
        log_file = self._get_log_file(session_id)
        
        if not log_file.exists():
            return set()
        
        event_ids = set()
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        event_id = event.get("event_id")
                        if event_id:
                            event_ids.add(event_id)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse event line: {e}")
        
        return event_ids
    
    def get_event_ids_after(
        self,
        session_id: str,
        after_event_id: Optional[str]
    ) -> set[str]:
        """
        Get event IDs added after a specific event ID.
        
        This method is optimized for incremental validation scenarios where
        you only need to check event IDs for events added after a certain point.
        
        Args:
            session_id: Session identifier
            after_event_id: Event ID to start after (None returns all event IDs)
            
        Returns:
            Set of event ID strings for events after the specified event ID
        """
        if after_event_id is None:
            # Return all event IDs if None
            return self.get_event_ids_set(session_id)
        
        log_file = self._get_log_file(session_id)
        
        if not log_file.exists():
            return set()
        
        event_ids = set()
        found_reference = False
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        event_id = event.get("event_id")
                        
                        if event_id == after_event_id:
                            found_reference = True
                            # Don't include the reference event itself
                            continue
                        
                        if event_id and found_reference:
                            event_ids.add(event_id)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse event line: {e}")
        
        # If reference event not found, return all event IDs (backward compatibility)
        if not found_reference:
            return self.get_event_ids_set(session_id)
        
        return event_ids

