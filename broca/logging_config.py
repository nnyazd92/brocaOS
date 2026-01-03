import logging
import json
from datetime import datetime, date, time, timezone
from logging.handlers import RotatingFileHandler
from .config import config


class JsonFormatter(logging.Formatter):
    """
    Simple JSON log formatter: message + extra fields.
    """

    def _make_json_serializable(self, obj):
        """
        Recursively convert non-JSON-serializable objects to serializable formats.
        
        Handles:
        - datetime.datetime -> ISO format string
        - datetime.date -> ISO format string
        - datetime.time -> ISO format string
        - Nested dicts, lists, and tuples
        
        Args:
            obj: Object to convert
            
        Returns:
            JSON-serializable version of the object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        # Common non-JSON-serializable objects (functions, methods, Path, exceptions, etc.)
        # should never crash logging. Fall back to a stable string representation.
        try:
            json.dumps(obj, ensure_ascii=False)
            return obj
        except Exception:
            try:
                # Avoid huge dumps for callables.
                if callable(obj):
                    name = getattr(obj, "__name__", None) or getattr(getattr(obj, "__class__", None), "__name__", None) or "callable"
                    mod = getattr(obj, "__module__", None) or ""
                    return f"<callable {mod}.{name}>"
            except Exception:
                pass
            try:
                return repr(obj)
            except Exception:
                return str(type(obj))

    def format(self, record: logging.LogRecord) -> str:
        base = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields if present
        for k, v in record.__dict__.items():
            if k.startswith("_"):
                continue
            if k in ("args", "msg", "levelname", "levelno", "name",
                     "pathname", "filename", "module", "exc_info",
                     "exc_text", "stack_info", "lineno", "created",
                     "msecs", "relativeCreated", "thread", "threadName",
                     "processName", "process", "funcName"):
                continue
            base[k] = v

        # Convert any datetime objects to JSON-serializable format
        base = self._make_json_serializable(base)

        return json.dumps(base, ensure_ascii=False)


def setup_logging() -> None:
    logger = logging.getLogger()
    level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logger.setLevel(level)

    # Remove existing console handlers and reconfigure
    # This ensures we always suppress INFO on console, even if logging was already set up
    import sys
    existing_console_handlers = [
        h for h in logger.handlers 
        if isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr)
    ]
    for handler in existing_console_handlers:
        logger.removeHandler(handler)

    # Console handler (human-readable) - use stderr to avoid interfering with REPL output
    # Only create console handler if console logging is not suppressed
    if not config.logging.suppress_console_logging:
        # Suppress INFO level logs on console to keep output clean - only show WARNING and above
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.WARNING)  # Only warnings and errors to console
        ch_formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        ch.setFormatter(ch_formatter)
        logger.addHandler(ch)

    # File handler (JSON) - captures all logs including INFO
    # Only add if we don't already have a file handler
    has_file_handler = any(
        isinstance(h, RotatingFileHandler) for h in logger.handlers
    )
    if not has_file_handler:
        fh = RotatingFileHandler(
            config.logging.file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setLevel(level)  # Use configured level (usually INFO)
        fh_formatter = JsonFormatter()
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)
    
    # Configure httpx logger specifically - set to WARNING level to suppress HTTP request logs
    # These logs interfere with REPL output and are not needed for normal operation
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.WARNING)  # Only show warnings and errors, not INFO requests
    
    # Also configure httpcore (httpx's underlying library) if it exists
    httpcore_logger = logging.getLogger("httpcore")
    httpcore_logger.setLevel(logging.WARNING)
