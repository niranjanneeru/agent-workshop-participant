"""
Mock agent endpoint for testing the evaluation UI.
Wraps the existing SimpleToolAgent as an OpenAI-compatible HTTP endpoint.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path so we can import shared modules
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from shared.agent import SimpleToolAgent

app = FastAPI(title="Mock Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict[str, list[dict]] = {}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "gpt-4.1-mini"
    messages: list[ChatMessage]


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatResponse(BaseModel):
    choices: list[ChatChoice]


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    agent = SimpleToolAgent(model=request.model)

    history = [m.model_dump() for m in request.messages]
    user_msg = next(
        (m.content for m in reversed(request.messages) if m.role == "user"),
        "",
    )

    prior = [m.model_dump() for m in request.messages[:-1]] if len(request.messages) > 1 else None
    trace = agent.chat(user_msg, history=prior)

    return ChatResponse(
        choices=[
            ChatChoice(
                message=ChatMessage(role="assistant", content=trace.final_response)
            )
        ]
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
