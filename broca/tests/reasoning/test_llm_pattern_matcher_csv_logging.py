"""
Integration tests verifying LLMPatternMatcher logs to CSV correctly.

Ensures production LLM pattern matching calls are logged for encoder training data.
"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest


class DummyLLM:
    """Mock LLM that returns deterministic JSON responses."""
    
    def __init__(self, response: str = '[{"match": true, "confidence": 0.95}]'):
        self.response = response
        self.call_count = 0
    
    def chat(self, messages, temperature=0.0):
        self.call_count += 1
        return {"choices": [{"message": {"role": "assistant", "content": self.response}}]}
    
    def extract_assistant_content(self, response):
        return response["choices"][0]["message"]["content"]


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_llm_pattern_matcher_logs_to_csv(temp_log_dir, monkeypatch):
    """Verify LLMPatternMatcher logs batch and pair data to CSV."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    from broca.reasoning.pattern_match_logger import PatternMatchLogger, PatternMatchLogConfig
    
    # Create logger with temp path
    log_base = temp_log_dir / "llm_pattern_matching_log.csv"
    pm_logger = PatternMatchLogger(
        PatternMatchLogConfig(
            enabled=True,
            base_path=log_base,
            rotation="none",
            max_size_mb=100,
            max_content_chars=20_000,
        )
    )
    
    # Create matcher with mock LLM
    dummy_llm = DummyLLM('[{"match": true, "confidence": 0.95}]')
    matcher = LLMPatternMatcher(llm_client=dummy_llm, model="gpt-5-nano")
    
    # Inject logger
    matcher._pm_logger = pm_logger
    matcher._pm_logging_enabled = True
    
    # Call match
    pattern = {"type": "contradiction_check", "text": "The sky is blue"}
    content = {"text": "The sky is green"}
    result = matcher.match(pattern, content)
    
    assert result is True
    assert dummy_llm.call_count == 1
    
    # Verify CSV files were created
    batches_path = temp_log_dir / "llm_pattern_matching_log_batches.csv"
    pairs_path = temp_log_dir / "llm_pattern_matching_log_pairs.csv"
    
    assert batches_path.exists(), f"Batches CSV should exist at {batches_path}"
    assert pairs_path.exists(), f"Pairs CSV should exist at {pairs_path}"
    
    # Check batches CSV content
    with open(batches_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1, "Should have 1 batch logged"
        row = rows[0]
        assert row["model"] == "gpt-5-nano"
        assert row["num_pairs"] == "1"
        assert row["parse_ok"] == "True"
        assert row["error_type"] == ""
        assert "prompt_text_trunc" in row
        assert "response_text_trunc" in row
        assert len(row["prompt_text_trunc"]) > 0
        assert len(row["response_text_trunc"]) > 0
    
    # Check pairs CSV content
    with open(pairs_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1, "Should have 1 pair logged"
        row = rows[0]
        assert row["match_label"] == "True"
        assert float(row["confidence"]) == 0.95
        assert row["cache_hit"] == "False"
        assert row["llm_used"] == "True"
        assert row["parse_ok"] == "True"
        assert "input_json" in row
        assert "output_json" in row
        assert "pattern_json" in row
        assert "item_json" in row


def test_llm_pattern_matcher_logs_error_cases(temp_log_dir):
    """Verify LLMPatternMatcher logs error cases correctly."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    from broca.reasoning.pattern_match_logger import PatternMatchLogger, PatternMatchLogConfig
    
    # Create logger with temp path
    log_base = temp_log_dir / "llm_pattern_matching_log.csv"
    pm_logger = PatternMatchLogger(
        PatternMatchLogConfig(
            enabled=True,
            base_path=log_base,
            rotation="none",
            max_size_mb=100,
            max_content_chars=20_000,
        )
    )
    
    # Create matcher with LLM that returns invalid JSON
    dummy_llm = DummyLLM('not valid json at all')
    matcher = LLMPatternMatcher(llm_client=dummy_llm, model="gpt-5-nano")
    matcher._pm_logger = pm_logger
    matcher._pm_logging_enabled = True
    
    # Call match - should fail gracefully
    pattern = {"type": "test"}
    content = {"text": "test"}
    result = matcher.match(pattern, content)
    
    assert result is False
    
    # Check batches CSV logged the error
    batches_path = temp_log_dir / "llm_pattern_matching_log_batches.csv"
    with open(batches_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        row = rows[0]
        assert row["parse_ok"] == "False"
        assert row["error_type"] == "json_decode_error"


def test_llm_pattern_matcher_logs_multiple_pairs(temp_log_dir):
    """Verify LLMPatternMatcher logs multiple pairs from batch correctly."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    from broca.reasoning.pattern_match_logger import PatternMatchLogger, PatternMatchLogConfig
    
    # Create logger with temp path
    log_base = temp_log_dir / "llm_pattern_matching_log.csv"
    pm_logger = PatternMatchLogger(
        PatternMatchLogConfig(
            enabled=True,
            base_path=log_base,
            rotation="none",
            max_size_mb=100,
            max_content_chars=20_000,
        )
    )
    
    # Create matcher with LLM that returns multiple results
    response = '[{"match": true, "confidence": 0.9}, {"match": false, "confidence": 0.2}, {"match": true, "confidence": 0.7}]'
    dummy_llm = DummyLLM(response)
    matcher = LLMPatternMatcher(llm_client=dummy_llm, model="gpt-5-nano")
    matcher._pm_logger = pm_logger
    matcher._pm_logging_enabled = True
    
    # Call match_batch with 3 pairs
    pairs = [
        ({"type": "test1"}, {"text": "content1"}),
        ({"type": "test2"}, {"text": "content2"}),
        ({"type": "test3"}, {"text": "content3"}),
    ]
    results = matcher.match_batch(pairs)
    
    assert len(results) == 3
    assert results[0] == (True, 0.9)
    assert results[1] == (False, 0.2)
    assert results[2] == (True, 0.7)
    
    # Check pairs CSV has all 3 pairs
    pairs_path = temp_log_dir / "llm_pattern_matching_log_pairs.csv"
    with open(pairs_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 3
        
        # Check each pair
        assert rows[0]["pair_index"] == "0"
        assert rows[0]["match_label"] == "True"
        assert float(rows[0]["confidence"]) == 0.9
        
        assert rows[1]["pair_index"] == "1"
        assert rows[1]["match_label"] == "False"
        assert float(rows[1]["confidence"]) == 0.2
        
        assert rows[2]["pair_index"] == "2"
        assert rows[2]["match_label"] == "True"
        assert float(rows[2]["confidence"]) == 0.7


def test_llm_pattern_matcher_csv_has_training_columns(temp_log_dir):
    """Verify CSV has essential columns for training encoder-decoder models."""
    from broca.reasoning.llm_pattern_matcher import LLMPatternMatcher
    from broca.reasoning.pattern_match_logger import PatternMatchLogger, PatternMatchLogConfig
    
    log_base = temp_log_dir / "llm_pattern_matching_log.csv"
    pm_logger = PatternMatchLogger(
        PatternMatchLogConfig(
            enabled=True,
            base_path=log_base,
            rotation="none",
            max_size_mb=100,
            max_content_chars=20_000,
        )
    )
    
    dummy_llm = DummyLLM('[{"match": false, "confidence": 0.1}]')
    matcher = LLMPatternMatcher(llm_client=dummy_llm, model="gpt-5-nano")
    matcher._pm_logger = pm_logger
    matcher._pm_logging_enabled = True
    
    # Call match
    matcher.match({"type": "contradiction_check", "text": "A"}, {"text": "B"})
    
    # Check batches CSV columns
    batches_path = temp_log_dir / "llm_pattern_matching_log_batches.csv"
    with open(batches_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        required_batch_cols = [
            "timestamp", "batch_id", "model", "num_pairs", "latency_ms",
            "prompt_text_trunc", "response_text_trunc", "prompt_hash", "response_hash",
            "parse_ok", "error_type"
        ]
        for col in required_batch_cols:
            assert col in reader.fieldnames, f"Missing batch column: {col}"
    
    # Check pairs CSV columns
    pairs_path = temp_log_dir / "llm_pattern_matching_log_pairs.csv"
    with open(pairs_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        required_pair_cols = [
            "timestamp", "batch_id", "pair_index", "pattern_type",
            "match_label", "confidence", "cache_hit", "llm_used",
            "pattern_json", "item_json", "input_json", "output_json",
            "pattern_hash", "item_hash"
        ]
        for col in required_pair_cols:
            assert col in reader.fieldnames, f"Missing pair column: {col}"

