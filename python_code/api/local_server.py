"""
Local development server — mirrors the RunPod response format so the
React Native app works without any changes to the frontend API calls.

Usage:
    python local_server.py

Endpoints:
    POST /chat   { input: { messages: [...] } }  →  { output: { role, content, memory } }
    GET  /        health check
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import time
import uuid
import traceback
import structlog

log = structlog.get_logger()

from pathlib import Path
from fastapi.responses import HTMLResponse
from agent_controller import AgentController
from metrics import MetricsStore

app = FastAPI(title="Cafe.AI Local Dev Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

print("Loading agents...")
metrics_store = MetricsStore()
agent_controller = AgentController(metrics=metrics_store)
print("Agents ready.")


class ChatInput(BaseModel):
    messages: list


class ChatRequest(BaseModel):
    input: ChatInput


@app.get("/")
def health():
    return {"status": "ok", "message": "Cafe.AI local server is running"}


@app.post("/chat")
async def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    log.info("request_start", request_id=request_id)
    try:
        payload = {"input": {"messages": request.input.messages}}
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
