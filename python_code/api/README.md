# API — Multi-Agent Chatbot Backend

Python backend for the coffee shop chatbot. Runs locally via FastAPI (`local_server.py`) or deployed on RunPod serverless (`main.py`).

## Running Locally

```bash
# From repo root (use uv — raw pip has build issues on Python 3.12)
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install "httpx==0.27.2"   # pin — newer versions break openai async client

cp .env_example .env
# Set RUNPOD_TOKEN to your Groq API key (free at console.groq.com)

python local_server.py       # HTTP server on :8000
python development_code.py   # CLI chat for quick testing
```

The server exposes:
```
POST /chat        { "input": { "messages": [...] } }  →  { "output": { role, content, memory } }
GET  /            health check
GET  /metrics     JSON metrics snapshot
GET  /dashboard   live observability dashboard (Chart.js, auto-refreshes every 5s)
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `RUNPOD_TOKEN` | Yes | Groq API key or RunPod token |
| `RUNPOD_CHATBOT_URL` | Yes | `https://api.groq.com/openai/v1` (Groq) or RunPod endpoint |
| `MODEL_NAME` | Yes | `llama-3.3-70b-versatile` (Groq) or `meta-llama/Llama-3.1-8B-Instruct` |
| `PINECONE_API_KEY` | No | Required for RAG (embeddings are local, no URL needed) |
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

## Observability Dashboard

![Observability Dashboard](../../images/metrics_dashboard.png)

## Observability

Every request produces structured log lines via `structlog`:

```json
{"event": "request_start",    "request_id": "a3f2c1b0"}
{"event": "llm_call",         "model": "llama-3.3-70b", "latency_ms": 210, "input_tokens": 145, "output_tokens": 42}
{"event": "guard_decision",   "decision": "allowed"}
{"event": "agent_routed",     "agent": "order_taking_agent"}
{"event": "request_complete", "request_id": "a3f2c1b0", "total_ms": 740}
```

Visit `http://localhost:8000/dashboard` for a live Chart.js dashboard showing latency, token usage, agent distribution, and guard block rate.

## Testing

```bash
# Unit tests — no API key needed
python -m pytest tests/ -v

# LLM evals — requires valid .env
python -m tests.evals.eval_guard
python -m tests.evals.eval_classification
python -m tests.evals.eval_recommendation
```

## Files

| File | Purpose |
|---|---|
| `local_server.py` | FastAPI dev server — `/chat`, `/metrics`, `/dashboard` |
| `main.py` | RunPod serverless handler — production only |
| `development_code.py` | CLI interactive chat — quick testing without HTTP |
| `agent_controller.py` | Orchestrates the full agent pipeline + records metrics |
| `agents/utils.py` | OpenAI SDK wrapper — logs every LLM call via structlog |
| `metrics.py` | In-memory MetricsStore — tracks latency, tokens, routing per request |
| `templates/dashboard.html` | Chart.js dashboard served at `/dashboard` |
| `tests/eval_data/` | JSON eval datasets for guard, classification, recommendation |
| `tests/evals/` | Eval runners that hit the real LLM |
| `Dockerfile` | Builds Docker image for RunPod deployment |

## Deploying to RunPod

```bash
docker build -t your-dockerhub/chatbot:latest .
docker push your-dockerhub/chatbot:latest
```

Create a RunPod serverless endpoint, use the image above, and set environment variables from `.env_example`.
