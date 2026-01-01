"""
WEB_FETCH tool: download and extract text from a URL (HTML/PDF).

This is intentionally separate from WEB_SEARCH so RL/agents can explicitly choose
between "find sources" and "fetch source content".
"""

from __future__ import annotations

import io
from typing import Any, Dict, Optional

import httpx


class WebFetchTool:
    @property
    def name(self) -> str:
        return "WEB_FETCH"

    @property
    def description(self) -> str:
        return (
            "Fetch a URL and extract readable text. Supports HTML and PDFs. "
            "Returns extracted text plus basic response metadata."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "timeout": {
                    "type": "integer",
                    "description": "Timeout seconds (default: 30, max: 120)",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 120,
                },
                "max_bytes": {
                    "type": "integer",
                    "description": "Maximum response bytes to process (default: 2000000)",
                    "default": 2_000_000,
                    "minimum": 1,
                    "maximum": 20_000_000,
                },
                "include_html": {
                    "type": "boolean",
                    "description": "Include raw HTML (can be large; default: false)",
                    "default": False,
                },
            },
            "required": ["url"],
        }

    def execute(self, url: str, timeout: int = 30, max_bytes: int = 2_000_000, include_html: bool = False, **_: Any) -> Dict[str, Any]:
        if not isinstance(url, str) or not url.strip():
            return {"success": False, "error": "url_required"}

        timeout_i = max(1, min(120, int(timeout))) if isinstance(timeout, int) else 30
        max_bytes_i = max(1, min(20_000_000, int(max_bytes))) if isinstance(max_bytes, int) else 2_000_000

        try:
            with httpx.Client(follow_redirects=True, timeout=timeout_i) as client:
                resp = client.get(
                    url,
                    headers={
                        "User-Agent": "BrocaOS/WEB_FETCH (httpx)",
                        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
                    },
                )
        except Exception as e:
            return {"success": False, "error": f"fetch_failed:{e}"}

        content = resp.content[:max_bytes_i]
        content_type = resp.headers.get("content-type", "")

        try:
            extracted_text, title, parsed_kind = self._extract_text(url=url, content=content, content_type=content_type)
        except Exception as e:
            return {
                "success": False,
                "error": f"extract_failed:{e}",
                "url": str(resp.url),
                "status_code": int(resp.status_code),
                "content_type": content_type,
            }

        result: Dict[str, Any] = {
            "success": True,
            "url": str(resp.url),
            "status_code": int(resp.status_code),
            "content_type": content_type,
            "bytes": len(content),
            "kind": parsed_kind,
            "title": title,
            "text": extracted_text,
        }
        if include_html and parsed_kind == "html":
            result["html"] = content.decode("utf-8", errors="replace")
        return result

    def _extract_text(self, *, url: str, content: bytes, content_type: str) -> tuple[str, Optional[str], str]:
        is_pdf = "application/pdf" in (content_type or "").lower() or url.lower().endswith(".pdf")
        if is_pdf:
            return self._extract_pdf_text(content), None, "pdf"
        return self._extract_html_text(content), None, "html"

    def _extract_pdf_text(self, content: bytes) -> str:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(content))
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                parts.append("")
        return "\n".join([p for p in parts if p.strip()]).strip()

    def _extract_html_text(self, content: bytes) -> str:
        html = content.decode("utf-8", errors="replace")

        # Primary extraction: trafilatura.
        try:
            import trafilatura

            extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
            if isinstance(extracted, str) and extracted.strip():
                return extracted.strip()
        except Exception:
            pass

        # Fallback: readability-lxml + BeautifulSoup text.
        try:
            from readability import Document
            from bs4 import BeautifulSoup

            doc = Document(html)
            summary = doc.summary(html_partial=True)
            soup = BeautifulSoup(summary, "lxml")
            text = soup.get_text(separator="\n", strip=True)
            return text.strip()
        except Exception:
            # Last resort: strip tags crudely.
            return html

    def format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"WEB_FETCH error: {result.get('error', 'unknown')}"
        text = result.get("text", "") or ""
        preview = text[:1000] + ("…" if len(text) > 1000 else "")
        return (
            f"WEB_FETCH: {result.get('url')} (status={result.get('status_code')}, kind={result.get('kind')})\n\n"
            f"{preview}"
        )

