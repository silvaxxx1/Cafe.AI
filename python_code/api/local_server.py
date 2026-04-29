"""
Local development server — mirrors the RunPod response format so the
React Native app works without any changes to the frontend API calls.

Usage:
    python local_server.py

Endpoints:
    POST /chat   { input: { messages: [...] } }  →  { output: { role, content, memory } }
    GET  /        health check
    GET  /metrics JSON metrics snapshot
    GET  /dashboard live observability dashboard
"""

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

from agent_controller import AgentController
from metrics import MetricsStore

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
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ── Agents ────────────────────────────────────────────────────────────────────
print("Loading agents...")
metrics_store = MetricsStore()
agent_controller = AgentController(metrics=metrics_store)
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
        payload = {"input": {"messages": [m.model_dump() for m in body.input.messages]}}
        response = await agent_controller.get_response(payload)
        log.info("request_complete", request_id=request_id, total_ms=round((time.perf_counter() - start) * 1000))
        return {"output": response}
    except Exception as e:
        log.error("request_error", request_id=request_id, error=str(e), detail=traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def get_metrics():
    return metrics_store.summary()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = (Path(__file__).parent / "templates" / "dashboard.html").read_text()
    return HTMLResponse(content=html)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
