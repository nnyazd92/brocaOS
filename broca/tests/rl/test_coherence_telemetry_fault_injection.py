from __future__ import annotations

import importlib

from broca.rl.coherence_telemetry import log_from_context


def test_coherence_telemetry_handles_malformed_context_without_crashing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BROCA_KAPPA_LOG_ENABLED", "true")
    monkeypatch.setenv("BROCA_KAPPA_INTEGRATED_LOG_ENABLED", "true")
    monkeypatch.setenv("BROCA_KAPPA_LOG_FILE", str(tmp_path / "data" / "rl" / "kappa_series.csv"))
    monkeypatch.setenv("BROCA_KAPPA_INTEGRATED_LOG_FILE", str(tmp_path / "data" / "rl" / "kappa_integrated_series.csv"))
    monkeypatch.setenv("BROCA_KAPPA_LOG_APPEND", "true")
    monkeypatch.setenv("BROCA_KAPPA_INTEGRATED_LOG_APPEND", "true")

    # Reload to bind env config.
    import broca.rl.coherence_telemetry as ct
    import broca.rl.kappa_logger as kl
    import broca.rl.kappa_integrated_logger as kil

    importlib.reload(ct)
    importlib.reload(kl)
    importlib.reload(kil)

    weird_ctx = {
        "rl_signals": "not-a-dict",
        "active_goals": "not-a-list",
        "working_memory_items": None,
        "recent_tools": 123,
        "production_rules": {"bad": "shape"},
    }

    s = log_from_context(weird_ctx, tool_name="X", success=None, now=1.0)
    assert s.kappa == s.kappa
    assert s.kappa_integrated == s.kappa_integrated

    assert (tmp_path / "data" / "rl" / "kappa_series.csv").exists()
    assert (tmp_path / "data" / "rl" / "kappa_integrated_series.csv").exists()


