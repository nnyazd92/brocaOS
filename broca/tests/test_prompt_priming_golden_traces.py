from __future__ import annotations

import json
from pathlib import Path

import pytest

from broca.memory.priming import build_structured_priming_card, build_thought_priming_card


class TestPromptPrimingGoldenTraces:
    def golden_traces_dir(self) -> Path:
        return Path(__file__).parent / "fixtures" / "golden_traces" / "prompt_priming"

    def test_priming_card_golden_trace(self):
        golden_dir = self.golden_traces_dir()
        golden_dir.mkdir(parents=True, exist_ok=True)
        golden_file = golden_dir / "priming_card.json"

        expected = {
            "card": build_structured_priming_card(
                query_preview="hello",
                cue_meta={
                    "task_type": "chat",
                    "intent": "hello",
                    "entities": [],
                    "constraints": [],
                    "goals": [],
                    "affect": {},
                },
                selection={"strategy": "mmr"},
                items=[
                    {
                        "id": 1,
                        "namespace": "ns",
                        "text": "A",
                        "importance": 0.6,
                        "created_at": "2024-01-01T00:00:00Z",
                        "last_used_at": "2024-01-02T00:00:00Z",
                        "source_type": "user",
                        "why": {"sim": 0.9, "bm25": 0.2, "goal": 0.0, "affect": 0.0, "recency": 0.4, "usage": 0.7},
                    },
                    {
                        "id": 2,
                        "namespace": "ns",
                        "text": "B",
                        "importance": 0.5,
                        "created_at": "2024-01-01T00:00:00Z",
                        "last_used_at": "2024-01-02T00:00:00Z",
                        "source_type": "user",
                        "why": {"sim": 0.7, "bm25": 0.1, "goal": 0.0, "affect": 0.0, "recency": 0.3, "usage": 0.6},
                    },
                ],
                conflicts=None,
                unknowns=None,
            )
        }

        if golden_file.exists():
            golden = json.loads(golden_file.read_text(encoding="utf-8"))
            assert expected == golden
        else:
            golden_file.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            pytest.skip("Golden trace created - run again to verify")

    def test_thought_priming_card_golden_trace(self):
        golden_dir = self.golden_traces_dir()
        golden_dir.mkdir(parents=True, exist_ok=True)
        golden_file = golden_dir / "thought_priming_card.json"

        expected = {
            "card": build_thought_priming_card(
                query_preview="hello",
                cue_meta={
                    "task_type": "chat",
                    "intent": "hello",
                    "entities": [],
                    "constraints": [],
                    "goals": [],
                    "affect": {},
                },
                selection={"strategy": "mmr"},
                items=[
                    {
                        "id": 1,
                        "namespace": "ns",
                        "text": "This is a key fact about X.",
                        "importance": 0.6,
                        "created_at": "2024-01-01T00:00:00Z",
                        "last_used_at": "2024-01-02T00:00:00Z",
                        "source_type": "user",
                        "why": {"sim": 0.9},
                    }
                ],
            )
        }

        if golden_file.exists():
            golden = json.loads(golden_file.read_text(encoding="utf-8"))
            assert expected == golden
        else:
            golden_file.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            pytest.skip("Golden trace created - run again to verify")
