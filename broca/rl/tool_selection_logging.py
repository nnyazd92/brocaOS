"""
Shared tool selection logging for RL tool selection policies and web API.

This avoids importing a specific policy module just to get the logger and ensures
`data/rl/tool_selection.log` is always configured consistently.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Lock

_LOGGER_NAME = "broca.rl.tool_selection"
_DEFAULT_LOG_PATH = Path("data/rl/tool_selection.log")

_init_lock = Lock()
_initialized = False
_sig = None


def get_tool_selection_logger() -> logging.Logger:
    """
    Return the shared tool selection logger, ensuring it has a file handler.

    Safe to call multiple times; will not attach duplicate file handlers.
    """
    global _initialized
    global _sig

    logger = logging.getLogger(_LOGGER_NAME)

    # Allow tests and callers to override log path without polluting repo logs.
    cfg_path = os.getenv("BROCA_TOOL_SELECTION_LOG_FILE", "").strip()
    desired = Path(cfg_path) if cfg_path else _DEFAULT_LOG_PATH
    log_path = desired.resolve()
    sig = str(log_path)

    if _initialized and _sig == sig:
        return logger

    with _init_lock:
        if _initialized and _sig == sig:
            return logger

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
        _sig = sig
        return logger
