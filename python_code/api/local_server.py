"""
Local development server — mirrors the RunPod response format so the
React Native app works without any changes to the frontend API calls.

Usage:
    python local_server.py

Endpoints:
    POST /chat              { input: { messages }, session_id? }  →  { output: { role, content, memory } }
    POST /chat/stream       same body  →  SSE stream of { type, delta } / { type, memory } events
    GET  /session/{id}      →  { messages: [...] }   restore prior conversation
    DELETE /session/{id}    →  { status: "cleared" } start fresh
    GET  /                  health check
    GET  /metrics           JSON metrics snapshot
    GET  /dashboard         live observability dashboard (auto-refreshes every 5s)
"""

import json
import os
import sys
import time
import uuid
import traceback
from pathlib import Path
from typing import Annotated

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sse_starlette.sse import EventSourceResponse

from agent_controller import AgentController
from metrics import MetricsStore
from session import SessionStore

log = structlog.get_logger()

# ── Startup config validation ─────────────────────────────────────────────────
_REQUIRED_ENV = ["RUNPOD_TOKEN", "RUNPOD_CHATBOT_URL", "MODEL_NAME"]
_missing = [v for v in _REQUIRED_ENV if not os.getenv(v)]
if _missing:
    print(f"[startup] ERROR — missing required env vars: {', '.join(_missing)}")
    print("[startup] Copy python_code/api/.env_example to .env and fill in the values.")
    sys.exit(1)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["20/minute"])

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Cafe.AI Local Dev Server")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
_ALLOWED_ORIGINS = [
    "http://localhost:8081",   # Expo web
    "http://localhost:19006",  # Expo web (legacy port)
    "http://127.0.0.1:8081",
    "exp://localhost:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Cache-Control", "X-Accel-Buffering"],
)

# ── Agents ────────────────────────────────────────────────────────────────────
print("Loading agents...")
metrics_store = MetricsStore()
agent_controller = AgentController(metrics=metrics_store)
session_store = SessionStore()
print("Agents ready.")


# ── Request models ────────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str


class ChatInput(BaseModel):
    messages: list[Message]

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError("messages must not be empty")
        return v


class ChatRequest(BaseModel):
    input: ChatInput
    session_id: str = "default"


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ok", "message": "Cafe.AI local server is running"}


@app.post("/chat")
@limiter.limit("20/minute")
async def chat(request: Request, body: ChatRequest):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    log.info("request_start", request_id=request_id)
    try:
        messages = [m.model_dump() for m in body.input.messages]
        payload = {"input": {"messages": messages}}
        response = await agent_controller.get_response(payload)
        session_store.set(body.session_id, messages + [response])
        log.info("request_complete", request_id=request_id, total_ms=round((time.perf_counter() - start) * 1000))
        return {"output": response}
    except Exception as e:
        log.error("request_error", request_id=request_id, error=str(e), detail=traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
@limiter.limit("20/minute")
async def chat_stream(request: Request, body: ChatRequest):
    request_id = str(uuid.uuid4())[:8]
    log.info("stream_request_start", request_id=request_id)

    async def event_generator():
        messages = [m.model_dump() for m in body.input.messages]
        payload = {"input": {"messages": messages}}
        full_content = ""
        done_memory: dict = {}
        try:
            async for event in agent_controller.get_stream_response(payload):
                if event["type"] == "token":
                    full_content += event["delta"]
                elif event["type"] == "done":
                    done_memory = event.get("memory", {})
                yield {"data": json.dumps(event)}
        except Exception as e:
            log.error("stream_request_error", request_id=request_id, error=str(e), detail=traceback.format_exc())
            yield {"data": json.dumps({"type": "error", "message": str(e)})}
            return
        session_store.set(
            body.session_id,
            messages + [{"role": "assistant", "content": full_content, "memory": done_memory}],
        )
        log.info("session_saved", session_id=body.session_id)

    return EventSourceResponse(event_generator())


@app.get("/session/{session_id}")
def get_session(session_id: str):
    return {"messages": session_store.get(session_id)}


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    session_store.delete(session_id)
    return {"status": "cleared"}


@app.get("/metrics")
def get_metrics():
    return metrics_store.summary()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = (Path(__file__).parent / "templates" / "dashboard.html").read_text()
    return HTMLResponse(content=html)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
