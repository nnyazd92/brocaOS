from __future__ import annotations

import asyncio


def test_metrics_endpoint_does_not_call_blocking_cpu_percent(monkeypatch):
    """
    Regression: /api/metrics must not call psutil.cpu_percent(interval=0.1) on the async request path.
    """
    import broca.web_api as web_api

    called = {"cpu_percent": 0}

    def _cpu_percent(*args, **kwargs):
        called["cpu_percent"] += 1
        raise AssertionError("psutil.cpu_percent should not be called on /api/metrics request path")

    monkeypatch.setattr(web_api.psutil, "cpu_percent", _cpu_percent)

    # Call the handler directly; it should use cached snapshot or safe defaults.
    out = asyncio.run(web_api.metrics())
    assert isinstance(out, dict)
    assert "cpu" in out and "memory" in out and "uptime" in out and "timestamp" in out
    assert called["cpu_percent"] == 0


