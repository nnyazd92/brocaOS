from __future__ import annotations

import json

from broca.prompting.recursive_thought import AppendOnlyThoughtLogger


def test_append_only_thought_logger_writes_jsonl_and_text(tmp_path):
    text_path = tmp_path / "stream.log"
    jsonl_path = tmp_path / "stream.jsonl"

    logger = AppendOnlyThoughtLogger(text_path=text_path, jsonl_path=jsonl_path)

    logger.append_cycle(
        cycle=1,
        kind="initial_plan",
        prompt="PLAN: test",
        response="ok",
        conversation_id="c1",
        session_id="s1",
        thought_signature="sig-1",
        meta={"x": 1},
    )
    size1_text = text_path.stat().st_size
    size1_jsonl = jsonl_path.stat().st_size

    logger.append_cycle(
        cycle=2,
        kind="cycle",
        prompt="next",
        response="ok2",
        conversation_id="c1",
        session_id="s1",
        thought_signature="sig-2",
        meta={"x": 2},
    )

    assert text_path.stat().st_size > size1_text
    assert jsonl_path.stat().st_size > size1_jsonl

    jsonl_lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    assert len(jsonl_lines) == 2

    rec1 = json.loads(jsonl_lines[0])
    rec2 = json.loads(jsonl_lines[1])
    assert rec1["cycle"] == 1
    assert rec2["cycle"] == 2
    assert rec1["conversation_id"] == "c1"
    assert rec1["thought_signature"] == "sig-1"
    assert rec2["thought_signature"] == "sig-2"

    text = text_path.read_text(encoding="utf-8")
    assert "INITIAL_PLAN" in text
    assert "CYCLE 1" in text
    assert "CYCLE 2" in text
    assert "PROMPT:" in text
    assert "RESPONSE:" in text
