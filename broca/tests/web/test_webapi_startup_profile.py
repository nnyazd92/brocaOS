import threading

from fastapi.testclient import TestClient


def test_startup_profile_reports_current_span_while_initializing(monkeypatch):
    from broca import web_api

    # Reset module globals for isolation.
    web_api._runtime = None
    web_api._runtime_status = "not_started"
    web_api._runtime_init_error = None
    web_api._runtime_init_started_at = None
    web_api._runtime_ready_at = None
    web_api._startup_profiler = None

    entered = threading.Event()
    release = threading.Event()

    def slow_init(*args, **kwargs):
        profiler = kwargs.get("startup_profiler")
        if profiler is not None:
            with profiler.span("test_phase"):
                entered.set()
                release.wait(timeout=2.0)
        else:
            entered.set()
            release.wait(timeout=2.0)
        raise RuntimeError("init should not complete in this test")

    monkeypatch.setattr(web_api, "initialize_runtime", slow_init)

    with TestClient(web_api.app) as client:
        assert entered.wait(timeout=1.0)

        r = client.get("/api/startup_profile")
        assert r.status_code == 200
        payload = r.json()

        assert payload["runtime"]["status"] == "initializing"
        assert payload["profile"] is not None
        assert payload["profile"]["current_span"] == "test_phase"

        r = client.get("/api/healthz")
        assert r.status_code == 200
        hz = r.json()
        assert hz["status"] == "initializing"
        assert hz["startup_span"] == "test_phase"

        release.set()

