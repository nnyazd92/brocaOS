import threading

from fastapi.testclient import TestClient


def test_webapi_metrics_and_healthz_work_while_runtime_initializing(monkeypatch):
    """
    Regression: web API must not block the event loop on restart.

    - /api/metrics must respond immediately
    - /api/healthz must report runtime status
    - /api/chat should return 503 while runtime is initializing (instead of hanging)
    """
    from broca import web_api

    # Reset module globals for isolation.
    web_api._runtime = None
    web_api._runtime_status = "not_started"
    web_api._runtime_init_error = None
    web_api._runtime_init_started_at = None
    web_api._runtime_ready_at = None

    gate = threading.Event()

    def slow_init():
        # Block until the test ends; init runs in a daemon thread.
        gate.wait(timeout=5.0)
        raise RuntimeError("init should not complete in this test")

    monkeypatch.setattr(web_api, "initialize_runtime", slow_init)

    with TestClient(web_api.app) as client:
        r = client.get("/api/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "cpu" in data and "memory" in data and "uptime" in data

        r = client.get("/api/healthz")
        assert r.status_code == 200
        hz = r.json()
        assert hz["status"] in ("initializing", "not_started", "ready", "error")

        r = client.post(
            "/api/chat",
            json={
                "conversation_id": None,
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False,
                "web_search": False,
            },
        )
        assert r.status_code == 503


