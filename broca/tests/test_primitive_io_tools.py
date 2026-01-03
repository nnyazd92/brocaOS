from __future__ import annotations

import os
from pathlib import Path

import pytest

from broca.config import config
from broca.tools.primitive_io import (
    AppendFileTool,
    ExecuteTool,
    PatchFileTool,
    ReadFileTool,
    WriteFileTool,
)


def test_write_then_read_roundtrip(tmp_path: Path):
    writer = WriteFileTool()
    reader = ReadFileTool()

    path = tmp_path / "hello.txt"
    text = "line1\nline2\n"
    write_res = writer.execute(path=str(path), content=text)
    assert write_res["success"] is True

    read_res = reader.execute(path=str(path), max_bytes=1_000_000)
    assert read_res["success"] is True
    assert read_res["content"] == text
    assert read_res["truncated"] is False


def test_append_appends(tmp_path: Path):
    writer = WriteFileTool()
    appender = AppendFileTool()
    reader = ReadFileTool()

    path = tmp_path / "append.txt"
    writer.execute(path=str(path), content="a\n")
    appender.execute(path=str(path), content="b\n")

    res = reader.execute(path=str(path))
    assert res["success"] is True
    assert res["content"] == "a\nb\n"


def test_patch_file_line_edits_replace_and_insert(tmp_path: Path):
    writer = WriteFileTool()
    reader = ReadFileTool()
    patcher = PatchFileTool()

    path = tmp_path / "edit.txt"
    writer.execute(path=str(path), content="one\ntwo\nthree\n")

    # Replace line 2, insert before line 3
    res = patcher.execute(
        path=str(path),
        edits=[
            {"start_line": 2, "end_line": 2, "replacement": "TWO\n"},
            {"start_line": 3, "end_line": 2, "replacement": "inserted\n"},
        ],
    )
    assert res["success"] is True
    out = reader.execute(path=str(path))["content"]
    assert out == "one\nTWO\ninserted\nthree\n"


def test_patch_file_unified_diff_applies(tmp_path: Path):
    writer = WriteFileTool()
    reader = ReadFileTool()
    patcher = PatchFileTool()

    path = tmp_path / "udiff.txt"
    writer.execute(path=str(path), content="a\nb\nc\n")
    before = reader.execute(path=str(path))["content"]

    diff = (
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        "@@ -1,3 +1,3 @@\n"
        " a\n"
        "-b\n"
        "+B\n"
        " c\n"
    )
    res = patcher.execute(path=str(path), unified_diff=diff)
    assert res["success"] is True

    after = reader.execute(path=str(path))["content"]
    assert before != after
    assert after == "a\nB\nc\n"


def test_patch_file_sha256_precondition(tmp_path: Path):
    writer = WriteFileTool()
    patcher = PatchFileTool()
    reader = ReadFileTool()

    path = tmp_path / "sha.txt"
    writer.execute(path=str(path), content="x\ny\n")
    old = reader.execute(path=str(path))["content"].encode("utf-8")

    diff = (
        f"--- {path}\n"
        f"+++ {path}\n"
        "@@ -1,2 +1,2 @@\n"
        " x\n"
        "-y\n"
        "+Y\n"
    )

    # Wrong precondition should block
    blocked = patcher.execute(path=str(path), unified_diff=diff, expected_sha256="0" * 64)
    assert blocked["success"] is False
    assert blocked["error"] == "sha256_mismatch"

    # Correct precondition should apply
    import hashlib

    ok = patcher.execute(path=str(path), unified_diff=diff, expected_sha256=hashlib.sha256(old).hexdigest())
    assert ok["success"] is True


def test_read_file_missing_returns_error(tmp_path: Path):
    reader = ReadFileTool()
    res = reader.execute(path=str(tmp_path / "missing.txt"))
    assert res["success"] is False
    assert res["error"] == "not_found"


def test_read_file_fault_injection(monkeypatch, tmp_path: Path):
    reader = ReadFileTool()
    path = tmp_path / "fault.txt"
    path.write_text("x", encoding="utf-8")

    def boom(self):  # noqa: ANN001
        raise OSError("boom")

    monkeypatch.setattr(Path, "read_bytes", boom, raising=True)
    res = reader.execute(path=str(path))
    assert res["success"] is False
    assert "boom" in str(res.get("error", ""))


def test_execute_runs_command(monkeypatch, tmp_path: Path):
    tool = ExecuteTool()
    res = tool.execute(cmd="echo hi", cwd=str(tmp_path), env_allowlist=["PATH"])
    assert res["success"] is True
    assert "hi" in (res.get("stdout") or "")


def test_execute_respects_allowlist(monkeypatch, tmp_path: Path):
    tool = ExecuteTool()
    monkeypatch.setattr(config.tools, "execute_command_whitelist", ["echo"])
    res = tool.execute(cmd="ls", cwd=str(tmp_path), env_allowlist=["PATH"])
    assert res["success"] is False
    assert res["error"] == "command_not_allowed"


def test_execute_timeout(tmp_path: Path):
    tool = ExecuteTool()
    # Use a whitelisted base command (python3) so the test is robust even when
    # BROCA_EXECUTE_WHITELIST is set via .env during test runs.
    res = tool.execute(cmd="python3 -c 'import time; time.sleep(2)'", cwd=str(tmp_path), timeout=1, env_allowlist=["PATH"])
    assert res["success"] is False
    assert res["error"] == "timeout"
