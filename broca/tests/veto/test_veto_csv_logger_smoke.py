from __future__ import annotations

import os
from pathlib import Path

from broca.veto.guard import VetoDecision
from broca.veto.veto_logger import get_veto_csv_logger


def test_veto_csv_logger_writes_row_to_configured_path(tmp_path, monkeypatch):
    log_path = tmp_path / "veto_guard.csv"
    monkeypatch.setenv("BROCA_VETO_LOG_ENABLED", "true")
    monkeypatch.setenv("BROCA_VETO_LOG_FILE", str(log_path))
    monkeypatch.setenv("BROCA_VETO_LOG_APPEND", "true")

    lg = get_veto_csv_logger()
    d = VetoDecision(
        veto=False,
        reason="unit_test",
        threshold=0.5,
        kappa_integrated=0.25,
        kappa_last=0.9,
        debug={"violation": True, "state_changed": False, "pred": {"mu": 0.3, "sigma": 0.1, "margin": 0.2}, "train": {"trained": True, "loss": 1.23}},
    )
    lg.log_decision(d, event="decision", tool_name="T", tool_call_id="c1", turn_no=1, iteration=2)

    text = log_path.read_text(encoding="utf-8")
    assert "timestamp" in text.splitlines()[0]
    assert "veto_active" in text.splitlines()[0]
    assert "decision" in text
    assert "unit_test" in text


