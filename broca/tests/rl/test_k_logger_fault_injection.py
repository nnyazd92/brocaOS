from __future__ import annotations

import os
from pathlib import Path

from broca.rl.k_logger import KSeriesLogger


def test_k_logger_creates_parent_dirs_and_writes(tmp_path: Path):
    log_path = tmp_path / "nested" / "k.csv"
    logger = KSeriesLogger(enabled=True, log_file=str(log_path), append=True)
    logger.log_k(0.123)
    assert log_path.exists()
    txt = log_path.read_text(encoding="utf-8")
    assert "timestamp,k" in txt


