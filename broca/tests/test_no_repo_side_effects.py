from __future__ import annotations

from pathlib import Path

import pytest


def test_repo_write_guard_blocks_data_dir_writes():
    """
    Tests must never write into the repo's production `data/` tree.

    This protects analysis artifacts (e.g., data/rl/*.csv) from being polluted by pytest runs.
    """
    repo_root = Path(__file__).resolve().parents[2]
    target = repo_root / "data" / "rl" / "SHOULD_NOT_WRITE_FROM_TESTS.txt"
    with pytest.raises(RuntimeError, match="TEST_WRITE_GUARD"):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("nope", encoding="utf-8")


