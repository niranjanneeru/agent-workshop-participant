"""
FastAPI backend for the Custom Agent Evaluation UI.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from .evaluator import run_evaluation
from .models import PresetGoalConfig, RunEvalRequest

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

_checkpoints_path = Path(__file__).resolve().parent.parent / "checkpoints.yaml"
_presets: list[PresetGoalConfig] = []
if _checkpoints_path.is_file():
    with open(_checkpoints_path) as f:
        _raw = yaml.safe_load(f)
    _presets = [PresetGoalConfig(**entry) for entry in _raw.get("presets", [])]

app = FastAPI(title="Agent Evaluation API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for completed evaluations (PoC only)
eval_history: dict[str, dict] = {}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/eval/run")
async def run_eval(request: RunEvalRequest):
    """
    Start an evaluation. Returns an SSE stream of conversation turns and results.
    """
    eval_id = str(uuid4())

    async def event_generator():
        yield {"event": "start", "data": json.dumps({"eval_id": eval_id})}

        result_data = None
        async for event in run_evaluation(
            agent_config=request.agent_config,
            goal_config=request.goal_config,
            evaluator_model=request.evaluator_model,
            judge_model=request.judge_model,
        ):
            payload = event.model_dump(exclude_none=True)
            if event.type == "result":
                result_data = payload
            yield {"event": event.type, "data": json.dumps(payload)}

        if result_data:
            eval_history[eval_id] = {
                "id": eval_id,
                "name": request.name,
                "config": request.model_dump(),
                "result": result_data.get("result", {}),
            }

        yield {"event": "done", "data": json.dumps({"eval_id": eval_id})}

    return EventSourceResponse(event_generator())


@app.get("/api/eval/presets")
async def get_presets():
    return [p.model_dump() for p in _presets]


@app.get("/api/eval/history")
async def get_history():
    return list(eval_history.values())


@app.get("/api/eval/{eval_id}")
async def get_eval(eval_id: str):
    if eval_id not in eval_history:
        return {"error": "Not found"}, 404
    return eval_history[eval_id]


# Serve the built frontend if available (Docker build copies it to ../static/)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA catch-all: serve index.html for any non-API route."""
        return FileResponse(_static_dir / "index.html")
