"""
CSV logging utility for LLM pattern matching operations.

Logs all LLM pattern matching calls to CSV for training ML models.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from queue import Queue

logger = logging.getLogger(__name__)


class LLMPatternLogger:
    """
    Thread-safe CSV logger for LLM pattern matching operations.
    
    Buffers writes and flushes periodically to avoid blocking.
    """
    
    # CSV column headers
    CSV_HEADERS = [
        "timestamp",
        "component",
        "operation",
        "model",
        "input_pattern",
        "input_content",
        "input_text",
        "input_context",
        "output_match",
        "output_confidence",
        "output_bindings",
        "output_metrics",
        "cache_hit",
        "latency_ms",
        "tokens_used",
        "error",
        "metadata"
    ]
    
    def __init__(
        self,
        log_path: str = "data/llm_pattern_matching_log.csv",
        enabled: bool = True,
        buffer_size: int = 10,
        flush_interval: float = 5.0
    ):
        """
        Initialize CSV logger.
        
        Args:
            log_path: Path to CSV log file
            enabled: Whether logging is enabled
            buffer_size: Number of entries to buffer before flushing
            flush_interval: Seconds between automatic flushes
        """
        self.log_path = Path(log_path)
        self.enabled = enabled
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # Create parent directory if needed
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread-safe buffer
        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._last_flush = time.time()
        
        # Initialize CSV file with headers if it doesn't exist
        if self.enabled and not self.log_path.exists():
            self._write_headers()
        
        logger.info(f"Initialized LLMPatternLogger (enabled={enabled}, path={self.log_path})")
    
    def _write_headers(self):
        """Write CSV headers to file."""
        try:
            with open(self.log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                writer.writeheader()
        except Exception as e:
            logger.error(f"Failed to write CSV headers: {e}", exc_info=True)
    
    def log(
        self,
        component: str,
        operation: str,
        model: str,
        input_pattern: Optional[Dict[str, Any]] = None,
        input_content: Optional[Dict[str, Any]] = None,
        input_text: Optional[str] = None,
        input_context: Optional[Dict[str, Any]] = None,
        output_match: Optional[bool] = None,
        output_confidence: Optional[float] = None,
        output_bindings: Optional[Dict[str, Any]] = None,
        output_metrics: Optional[Dict[str, Any]] = None,
        cache_hit: bool = False,
        latency_ms: Optional[float] = None,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a pattern matching operation.
        
        Args:
            component: Component name (e.g., "LLMPatternMatcher")
            operation: Operation type (e.g., "match", "match_batch")
            model: LLM model used
            input_pattern: Pattern being matched (dict)
            input_content: Content being matched against (dict)
            input_text: Plain text input
            input_context: Additional context (dict)
            output_match: Match result (bool)
            output_confidence: Confidence score (float)
            output_bindings: Variable bindings (dict)
            output_metrics: All output metrics (dict)
            cache_hit: Whether result came from cache
            latency_ms: Request latency in milliseconds
            tokens_used: Number of tokens used
            error: Error message if call failed
            metadata: Additional metadata (dict)
        """
        if not self.enabled:
            return
        
        # Build row data
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": component,
            "operation": operation,
            "model": model,
            "input_pattern": json.dumps(input_pattern) if input_pattern else "",
            "input_content": json.dumps(input_content) if input_content else "",
            "input_text": input_text or "",
            "input_context": json.dumps(input_context) if input_context else "",
            "output_match": str(output_match).lower() if output_match is not None else "",
            "output_confidence": str(output_confidence) if output_confidence is not None else "",
            "output_bindings": json.dumps(output_bindings) if output_bindings else "",
            "output_metrics": json.dumps(output_metrics) if output_metrics else "",
            "cache_hit": str(cache_hit).lower(),
            "latency_ms": str(latency_ms) if latency_ms is not None else "",
            "tokens_used": str(tokens_used) if tokens_used is not None else "",
            "error": error or "",
            "metadata": json.dumps(metadata) if metadata else ""
        }
        
        # Add to buffer
        with self._lock:
            self._buffer.append(row)
            
            # Flush if buffer is full or enough time has passed
            should_flush = (
                len(self._buffer) >= self.buffer_size or
                (time.time() - self._last_flush) >= self.flush_interval
            )
            
            if should_flush:
                self._flush()
    
    def log_batch(
        self,
        component: str,
        operation: str,
        model: str,
        batch_inputs: List[Dict[str, Any]],
        batch_results: List[Dict[str, Any]],
        latency_ms: Optional[float] = None,
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a batch of pattern matching operations.
        
        Args:
            component: Component name
            operation: Operation type (e.g., "match_batch")
            model: LLM model used
            batch_inputs: List of input dicts with pattern/content/text/context
            batch_results: List of result dicts with match/confidence/bindings/metrics
            latency_ms: Total latency for batch
            tokens_used: Total tokens used
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        # Log each item in the batch separately
        for i, (input_data, result_data) in enumerate(zip(batch_inputs, batch_results)):
            batch_metadata = (metadata or {}).copy()
            batch_metadata["batch_index"] = i
            batch_metadata["batch_size"] = len(batch_inputs)
            
            self.log(
                component=component,
                operation=operation,
                model=model,
                input_pattern=input_data.get("pattern"),
                input_content=input_data.get("content"),
                input_text=input_data.get("text"),
                input_context=input_data.get("context"),
                output_match=result_data.get("match"),
                output_confidence=result_data.get("confidence"),
                output_bindings=result_data.get("bindings"),
                output_metrics=result_data.get("metrics"),
                cache_hit=result_data.get("cache_hit", False),
                latency_ms=latency_ms / len(batch_inputs) if latency_ms else None,  # Average per item
                tokens_used=tokens_used // len(batch_inputs) if tokens_used else None,  # Average per item
                error=result_data.get("error"),
                metadata=batch_metadata
            )
    
    def _flush(self):
        """Flush buffer to CSV file (thread-safe)."""
        if not self._buffer:
            return
        
        # Get buffer contents and clear
        with self._lock:
            buffer_copy = self._buffer.copy()
            self._buffer.clear()
            self._last_flush = time.time()
        
        # Write to file
        try:
            file_exists = self.log_path.exists()
            with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(buffer_copy)
        except Exception as e:
            logger.error(f"Failed to write to CSV log: {e}", exc_info=True)
            # Put items back in buffer on error (to avoid data loss)
            with self._lock:
                self._buffer = buffer_copy + self._buffer
    
    def flush(self):
        """Manually flush buffer."""
        self._flush()
    
    def close(self):
        """Close logger and flush remaining buffer."""
        self._flush()
        logger.info("LLMPatternLogger closed")


# Global logger instance
_global_logger: Optional[LLMPatternLogger] = None
_logger_lock = threading.Lock()


def get_logger() -> Optional[LLMPatternLogger]:
    """Get global logger instance."""
    return _global_logger


def initialize_logger(
    log_path: Optional[str] = None,
    enabled: Optional[bool] = None
) -> LLMPatternLogger:
    """
    Initialize global logger instance.
    
    Args:
        log_path: Path to CSV log file (uses config if None)
        enabled: Whether logging is enabled (uses config if None)
        
    Returns:
        Logger instance
    """
    global _global_logger
    
    with _logger_lock:
        if _global_logger is None:
            # Get config if not provided
            if log_path is None or enabled is None:
                try:
                    from ..config import config
                    if log_path is None:
                        log_path = getattr(config.reasoning, 'llm_pattern_log_path', 'data/llm_pattern_matching_log.csv')
                    if enabled is None:
                        enabled = getattr(config.reasoning, 'llm_pattern_logging_enabled', True)
                except Exception:
                    if log_path is None:
                        log_path = 'data/llm_pattern_matching_log.csv'
                    if enabled is None:
                        enabled = True
            
            _global_logger = LLMPatternLogger(
                log_path=log_path,
                enabled=enabled
            )
        
        return _global_logger

