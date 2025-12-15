import logging
import json
from datetime import datetime, date, time
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
        else:
            return obj

    def format(self, record: logging.LogRecord) -> str:
        base = {
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
    if logger.handlers:
        # Already configured
        return

    level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logger.setLevel(level)

    # Console handler (human-readable)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch_formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    ch.setFormatter(ch_formatter)

    # File handler (JSON)
    fh = RotatingFileHandler(
        config.logging.file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(level)
    fh_formatter = JsonFormatter()
    fh.setFormatter(fh_formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
