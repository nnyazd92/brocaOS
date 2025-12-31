"""
Shared tool selection logging for RL tool selection policies and web API.

This avoids importing a specific policy module just to get the logger and ensures
`data/rl/tool_selection.log` is always configured consistently.
"""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock

_LOGGER_NAME = "broca.rl.tool_selection"
_DEFAULT_LOG_PATH = Path("data/rl/tool_selection.log")

_init_lock = Lock()
_initialized = False


def get_tool_selection_logger() -> logging.Logger:
    """
    Return the shared tool selection logger, ensuring it has a file handler.

    Safe to call multiple times; will not attach duplicate file handlers.
    """
    global _initialized

    logger = logging.getLogger(_LOGGER_NAME)

    if _initialized:
        return logger

    with _init_lock:
        if _initialized:
            return logger

        # Resolve to an absolute path so FileHandler.baseFilename comparisons work.
        log_path = _DEFAULT_LOG_PATH.resolve()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-5s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        # Avoid duplicates when multiple modules initialize the same logger.
        if not any(
            isinstance(h, logging.FileHandler)
            and getattr(h, "baseFilename", None) == str(log_path)
            for h in logger.handlers
        ):
            logger.addHandler(file_handler)

        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        _initialized = True
        return logger
