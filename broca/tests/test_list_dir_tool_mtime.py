from __future__ import annotations

import time
from pathlib import Path

from broca.tools.primitive_io import ListDirTool


def test_list_dir_includes_mtime_iso_and_formats_it(tmp_path):
    p = Path(tmp_path)
    f = p / "a.txt"
    f.write_text("hi", encoding="utf-8")

    tool = ListDirTool()
    result = tool.execute(path=str(p))
    assert result["success"] is True
    assert result["entries"]
    entry = next(e for e in result["entries"] if e["name"] == "a.txt")
    assert isinstance(entry.get("mtime_iso"), str)
    assert "T" in entry["mtime_iso"]

    formatted = tool.format_result(result)
    assert "mtime=" in formatted


