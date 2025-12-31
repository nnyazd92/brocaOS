import httpx


class _Resp:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return dict(self._payload)


def test_deepseek_client_retries_transient_dns_error(monkeypatch):
    from broca.llm.deepseek_client import DeepSeekClient

    client = DeepSeekClient(api_key="k", base_url="https://example.test/v1", model="deepseek-chat", timeout=1.0)

    attempts = {"n": 0}

    def _post(url: str, json: dict, headers: dict):  # noqa: A002 - match httpx signature
        attempts["n"] += 1
        if attempts["n"] < 3:
            req = httpx.Request("POST", "https://example.test/v1/chat/completions")
            raise httpx.RequestError("dns fail", request=req) from OSError(-2, "Name or service not known")
        return _Resp({"choices": [{"message": {"content": "ok"}}]})

    sleeps: list[float] = []

    def _sleep(x: float) -> None:
        sleeps.append(float(x))

    monkeypatch.setattr(client._client, "post", _post)
    monkeypatch.setattr("broca.llm.deepseek_client.time.sleep", _sleep)

    out = client.chat([{"role": "user", "content": "hi"}])
    assert out["choices"][0]["message"]["content"] == "ok"
    assert attempts["n"] == 3
    # Backoff for the first two failures (0.5s then 1.0s); no sleep on final success.
    assert sleeps == [0.5, 1.0]


def test_deepseek_client_does_not_retry_non_dns_request_error(monkeypatch):
    from broca.llm.deepseek_client import DeepSeekClient

    client = DeepSeekClient(api_key="k", base_url="https://example.test/v1", model="deepseek-chat", timeout=1.0)

    attempts = {"n": 0}

    def _post(url: str, json: dict, headers: dict):  # noqa: A002 - match httpx signature
        attempts["n"] += 1
        req = httpx.Request("POST", "https://example.test/v1/chat/completions")
        raise httpx.RequestError("some other network error", request=req)

    monkeypatch.setattr(client._client, "post", _post)
    monkeypatch.setattr("broca.llm.deepseek_client.time.sleep", lambda _: None)

    try:
        client.chat([{"role": "user", "content": "hi"}])
    except ConnectionError:
        pass
    else:
        raise AssertionError("Expected ConnectionError")

    assert attempts["n"] == 1
