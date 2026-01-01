from __future__ import annotations

from fastapi import FastAPI

from broca.prompting.recursive_thought import WebAPIChatBackend


def test_web_api_chat_backend_in_process_creates_and_reuses_conversation_id():
    app = FastAPI()

    state = {"calls": 0}

    @app.post("/api/chat")
    def chat(payload: dict):
        state["calls"] += 1
        cid = payload.get("conversation_id") or "conv_1"
        last = (payload.get("messages") or [{}])[-1]
        content = last.get("content") or ""
        return {"conversation_id": cid, "reply": {"role": "assistant", "content": f"echo:{content}"}}

    backend = WebAPIChatBackend(app=app)

    r1, meta1 = backend.send("hi")
    assert r1 == "echo:hi"
    assert backend.conversation_id == "conv_1"
    assert meta1["conversation_id"] == "conv_1"

    r2, meta2 = backend.send("again")
    assert r2 == "echo:again"
    assert backend.conversation_id == "conv_1"
    assert meta2["conversation_id"] == "conv_1"
    assert state["calls"] == 2

