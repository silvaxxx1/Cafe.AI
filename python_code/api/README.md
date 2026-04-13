# API — Multi-Agent Chatbot Backend

Python backend for the coffee shop chatbot. Runs locally via FastAPI (`local_server.py`) or deployed on RunPod serverless (`main.py`).

## Running Locally

```bash
# From repo root (use uv — raw pip has build issues on Python 3.12)
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

cp .env_example .env
# Set RUNPOD_TOKEN to your Groq API key (free at console.groq.com)

python local_server.py       # HTTP server on :8000
python development_code.py   # CLI chat for quick testing
```

The server exposes one endpoint:
```
POST /chat
Body:  { "input": { "messages": [...] } }
Reply: { "output": { "role", "content", "memory" } }
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `RUNPOD_TOKEN` | Yes | Groq API key or RunPod token |
| `RUNPOD_CHATBOT_URL` | Yes | `https://api.groq.com/openai/v1` (Groq) or RunPod endpoint |
| `MODEL_NAME` | Yes | `llama-3.1-8b-instant` (Groq) or `meta-llama/Llama-3.1-8B-Instruct` |
| `RUNPOD_EMBEDDING_URL` | No | Embedding endpoint — leave blank to disable details/RAG agent |
| `PINECONE_API_KEY` | No | Required for RAG |
| `PINECONE_INDEX_NAME` | No | Required for RAG |

## Agent Pipeline

```
User message
  → GuardAgent           blocks off-topic / harmful queries
  → ClassificationAgent  routes to the right agent
  → DetailsAgent         RAG: embed → Pinecone → LLM (disabled if no Pinecone config)
     or OrderTakingAgent  multi-turn order collection + auto recommendation upsell
     or RecommendationAgent  Apriori market basket + popularity rankings
```

All agents share a message list. Each assistant message carries a `memory` dict with agent-specific state (step number, current order, routing decisions). All `json.loads()` calls have `try/except` fallbacks — a malformed LLM response returns a graceful message instead of crashing.

## Files

| File | Purpose |
|---|---|
| `local_server.py` | FastAPI server for local dev — mirrors RunPod response format |
| `main.py` | RunPod serverless handler — production only |
| `development_code.py` | CLI interactive chat — quick testing without HTTP |
| `agent_controller.py` | Orchestrates the full agent pipeline |
| `agents/utils.py` | OpenAI SDK wrappers for LLM completions, embeddings, JSON validation |
| `Dockerfile` | Builds Docker image for RunPod deployment |

## Deploying to RunPod

```bash
docker build -t your-dockerhub/chatbot:latest .
docker push your-dockerhub/chatbot:latest
```

Create a RunPod serverless endpoint, use the image above, and set environment variables from `.env_example`.
