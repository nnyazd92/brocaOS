from typing import Literal, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from .main_repl_runtime import initialize_runtime, BrocaRuntime


runtime: Optional[BrocaRuntime] = None


from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="BrocaOS Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class ChatResponse(BaseModel):
    reply: Message


def get_runtime() -> BrocaRuntime:
    global runtime
    if runtime is None:
        runtime = initialize_runtime()
    return runtime


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    rt = get_runtime()
    session = rt.session

    if not req.messages:
        return ChatResponse(
            reply=Message(role="assistant", content="No messages provided.")
        )

    last = req.messages[-1]
    if last.role != "user":
        return ChatResponse(
            reply=Message(
                role="assistant",
                content=(
                    "Please send a user message as the last item in 'messages'."
                ),
            )
        )

    reply_text = session.send(last.content, stream=False)

    return ChatResponse(
        reply=Message(
            role="assistant",
            content=reply_text,
        )
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
