"""
Local development server — mirrors the RunPod response format so the
React Native app works without any changes to the frontend API calls.

Usage:
    python local_server.py

Endpoints:
    POST /chat   { input: { messages: [...] } }  →  { output: { role, content, memory } }
    GET  /        health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from agent_controller import AgentController

app = FastAPI(title="Cafe.AI Local Dev Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

print("Loading agents...")
agent_controller = AgentController()
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
    try:
        payload = {"input": {"messages": request.input.messages}}
        response = await agent_controller.get_response(payload)
        return {"output": response}
    except Exception as e:
        logger.error("500 error:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
