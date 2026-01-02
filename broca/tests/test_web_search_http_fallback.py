from __future__ import annotations

import pytest

from broca.tools.web_search import WebSearchTool


class _StubHttpClient:
    def __init__(self, html: str) -> None:
        self._html = html

    def get(self, url: str, **kwargs):
        class _Resp:
            def __init__(self, text: str) -> None:
                self.text = text

            def raise_for_status(self) -> None:
                return

        return _Resp(self._html)


def test_web_search_falls_back_to_duckduckgo_html_when_in_asyncio_loop(monkeypatch: pytest.MonkeyPatch):
    html = """
    <div class="results">
      <a class="result__a" href="https://example.com/a">Result A</a>
      <a class="result__snippet" href="#">Snippet A</a>
      <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fb">Result B</a>
      <a class="result__snippet" href="#">Snippet B</a>
    </div>
    """

    monkeypatch.setattr(WebSearchTool, "_running_in_asyncio_loop", staticmethod(lambda: True))
    tool = WebSearchTool(api_key="", browse_orchestrator=None, http_client=_StubHttpClient(html))

    out = tool.execute(query="test query", max_results=5)
    assert out["provider_used"] == "duckduckgo_html"
    assert out["count"] == 2
    assert out["results"][0]["title"] == "Result A"
    assert out["results"][0]["url"] == "https://example.com/a"
    assert "Snippet A" in out["results"][0]["content"]
    assert out["results"][1]["url"] == "https://example.com/b"

