"""
Recursive Thought Loop for BrocaOS.

This script implements a continuous "stream of thought" where BrocaOS
reflects on a goal, generates internal monologue, and potentially
triggers actions, logging the entire process for inspection.
"""

import time
import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


DEFAULT_THOUGHT_LOG_DIR = Path("docs/logs")
THOUGHT_TEXT_LOG_PATH = DEFAULT_THOUGHT_LOG_DIR / "recursive_thought_stream.log"
THOUGHT_JSONL_LOG_PATH = DEFAULT_THOUGHT_LOG_DIR / "recursive_thought_stream.jsonl"


class AppendOnlyThoughtLogger:
    """
    Append-only logger for recursive thought traces.

    Requirements:
    - Append-only (never rotates or truncates)
    - Stores both a human-readable stream and a structured JSONL trace for replay
    """

    def __init__(
        self,
        *,
        text_path: Path = THOUGHT_TEXT_LOG_PATH,
        jsonl_path: Path = THOUGHT_JSONL_LOG_PATH,
    ) -> None:
        self.text_path = Path(text_path)
        self.jsonl_path = Path(jsonl_path)
        self.text_path.parent.mkdir(parents=True, exist_ok=True)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def append_cycle(
        self,
        *,
        cycle: int,
        kind: str,
        prompt: str,
        response: str,
        conversation_id: Optional[str],
        session_id: Optional[str],
        thought_signature: Optional[str],
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        record: dict[str, Any] = {
            "ts": ts,
            "cycle": int(cycle),
            "kind": str(kind),
            "conversation_id": conversation_id,
            "session_id": session_id,
            "thought_signature": thought_signature,
            "prompt": prompt,
            "response": response,
            "meta": meta or {},
        }

        # Structured trace (golden replay friendly)
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Human-readable stream
        with self.text_path.open("a", encoding="utf-8") as f:
            f.write(f"\n--- {kind.upper()} | CYCLE {cycle} | {ts} ---\n")
            if thought_signature:
                f.write(f"thought_signature: {thought_signature}\n")
            if conversation_id:
                f.write(f"conversation_id: {conversation_id}\n")
            if session_id:
                f.write(f"session_id: {session_id}\n")
            f.write("\nPROMPT:\n")
            f.write(prompt)
            f.write("\n\nRESPONSE:\n")
            f.write(response)
            f.write("\n" + "-" * 80 + "\n")


class WebAPIChatBackend:
    """
    Drive BrocaOS via the FastAPI web layer (/api/chat).

    This ensures recursive-thought runs through the same runtime pipeline as web clients,
    including shared world state aggregation, affect/internal sensing, RL tooling, etc.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        app: Optional[Any] = None,
        test_client: Optional[Any] = None,
        max_retries: int = 20,
        retry_sleep_seconds: float = 0.25,
        request_timeout_seconds: float = 300.0,
    ) -> None:
        self._base_url = base_url.strip().rstrip("/") if isinstance(base_url, str) and base_url.strip() else None
        self._max_retries = max(0, int(max_retries))
        self._retry_sleep_seconds = max(0.0, float(retry_sleep_seconds))
        self._request_timeout_seconds = float(request_timeout_seconds)

        self.conversation_id: Optional[str] = None

        self._http_client = None
        self._test_client = test_client

        if self._base_url:
            import httpx

            self._http_client = httpx.Client(timeout=httpx.Timeout(self._request_timeout_seconds, connect=10.0))
        elif self._test_client is None:
            from fastapi.testclient import TestClient
            if app is None:
                from broca import web_api
                app = web_api.app

            self._test_client = TestClient(app)

    def send(
        self,
        prompt: str,
        *,
        web_search: bool = True,
        include_rl_signals: bool = False,
    ) -> tuple[str, dict[str, Any]]:
        payload = {
            "conversation_id": self.conversation_id,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "web_search": bool(web_search),
            "include_rl_signals": bool(include_rl_signals),
        }

        last_error: Optional[str] = None
        for attempt in range(self._max_retries + 1):
            if self._http_client is not None:
                resp = self._http_client.post(f"{self._base_url}/api/chat", json=payload)
            else:
                resp = self._test_client.post("/api/chat", json=payload)

            # Web runtime readiness can return 503 while starting up; retry.
            if resp.status_code == 503:
                last_error = resp.text
                if attempt < self._max_retries and self._retry_sleep_seconds > 0:
                    time.sleep(self._retry_sleep_seconds)
                    continue

            resp.raise_for_status()
            data = resp.json()
            self.conversation_id = data.get("conversation_id") or self.conversation_id
            reply = (data.get("reply") or {}).get("content")
            if not isinstance(reply, str):
                reply = ""
            meta = {"conversation_id": self.conversation_id, "rl_signals": data.get("rl_signals")}
            return reply, meta

        raise RuntimeError(f"web_api /api/chat failed after retries: {last_error}")


class RecursiveThoughtLoop:
    def __init__(
        self,
        seed_goal: str,
        *,
        thought_logger: Optional[AppendOnlyThoughtLogger] = None,
        backend: Optional[WebAPIChatBackend] = None,
    ):
        self.seed_goal = seed_goal
        self.backend = backend or WebAPIChatBackend(base_url=None)
        self._thought_logger = thought_logger or AppendOnlyThoughtLogger()
        self.iteration = 0

    def run(
        self,
        max_iterations: Optional[int] = 10,
        *,
        sleep_between_cycles_seconds: float = 2.0,
        auto_pivot: bool = False,
        max_total_cycles: Optional[int] = None,
        max_pivots: Optional[int] = None,
    ) -> None:
        logger.info("Starting recursive thought loop")
        
        # Initial planning step as suggested by the operator
        plan_prompt = f"PLAN: Create a comprehensive plan for the goal: {self.seed_goal}"
        initial_plan, meta = self.backend.send(plan_prompt)
        self._append_cycle(kind="initial_plan", prompt=plan_prompt, response=str(initial_plan), meta=meta)
        
        current_prompt = (
            f"SYSTEM SEED: {self.seed_goal}\n\n"
            "Reflect on the initial plan and the goal. What is the first step? What are the constraints? "
            "How can we leverage the existing tools to achieve this?"
        )

        cycles_in_topic = 0
        total_cycles = 0
        pivots_done = 0
        
        while True:
            if max_total_cycles is not None and total_cycles >= int(max_total_cycles):
                break

            if max_iterations is not None and cycles_in_topic >= int(max_iterations):
                if auto_pivot:
                    if max_pivots is not None and pivots_done >= int(max_pivots):
                        break
                    pivots_done += 1
                    pivot_prompt = (
                        "You are running an autonomous recursive thought loop.\n"
                        "Do NOT ask the operator what to do next.\n"
                        "Instead, decide what you want to think about next.\n\n"
                        "Output:\n"
                        "1) A 1-sentence next topic\n"
                        "2) A short justification\n"
                        "3) The first concrete step\n"
                    )
                    pivot_reply, pivot_meta = self.backend.send(pivot_prompt)
                    self._append_cycle(kind="pivot", prompt=pivot_prompt, response=str(pivot_reply), meta=pivot_meta)
                    cycles_in_topic = 0
                    current_prompt = (
                        "NEW TOPIC SEED:\n"
                        f"{pivot_reply}\n\n"
                        "Proceed with the first step and continue the autonomous loop."
                    )
                    continue
                break

            self.iteration += 1
            cycles_in_topic += 1
            total_cycles += 1
            
            # Generate response
            response, meta = self.backend.send(current_prompt)
            
            self._append_cycle(kind="cycle", prompt=current_prompt, response=str(response), meta=meta)

            # Prepare next prompt
            current_prompt = f"INTERNAL MONOLOGUE (Cycle {self.iteration}):\n{response}\n\nContinue the reflection. What are the implications of the previous thought? What actions should be taken next?"
            
            if sleep_between_cycles_seconds and sleep_between_cycles_seconds > 0:
                time.sleep(float(sleep_between_cycles_seconds))
            
        logger.info("Recursive thought loop completed.")

    def _append_cycle(self, *, kind: str, prompt: str, response: str, meta: Optional[dict[str, Any]] = None) -> None:
        conversation_id = getattr(self.backend, "conversation_id", None)
        self._thought_logger.append_cycle(
            cycle=self.iteration,
            kind=kind,
            prompt=prompt,
            response=response,
            conversation_id=conversation_id if isinstance(conversation_id, str) else None,
            session_id=None,
            thought_signature=None,
            meta=meta or {},
        )

if __name__ == "__main__":
    # Keep module import side-effect free; configure console logging only when run as a script.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    SEED = "Who and what is BrocaOS?"

    base_url = None
    try:
        import os
        base_url = os.getenv("BROCA_RECURSIVE_THOUGHT_WEB_API_URL") or os.getenv("BROCA_WEB_API_URL")
    except Exception:
        base_url = None

    loop = RecursiveThoughtLoop(SEED, backend=WebAPIChatBackend(base_url=base_url))
    loop.run(max_iterations=5, auto_pivot=True)
