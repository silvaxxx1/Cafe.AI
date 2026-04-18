# Architecture Overview

## What This System Is

Cafe.AI is a full-stack AI-powered coffee shop assistant. A customer opens a mobile app, browses a menu loaded from Firebase, and chats with a multi-agent backend to get product details, place orders, or receive recommendations. The chat backend runs locally via FastAPI or on RunPod serverless — the frontend works unchanged in both modes.

---

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     MOBILE APP (React Native / Expo)            │
│                                                                 │
│  index.tsx (splash)                                             │
│       │                                                         │
│  (tabs)/home.tsx ──── Firebase Realtime DB ──── product data    │
│  (tabs)/chatRoom.tsx ── POST /chat ──────────── backend         │
│  (tabs)/order.tsx ──── CartContext (in-memory)                  │
│  details.tsx ──────── route params from home                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP POST { input: { messages } }
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND  (FastAPI — local_server.py)               │
│                                                                 │
│  POST /chat                                                     │
│       │                                                         │
│       ▼                                                         │
│  AgentController.get_response()                                 │
│       │                                                         │
│       ├── GuardAgent          (blocks off-topic queries)        │
│       │                                                         │
│       ├── ClassificationAgent (routes to one of 3 agents)       │
│       │                                                         │
│       ├── DetailsAgent        (RAG → Pinecone → LLM)            │
│       ├── OrderTakingAgent    (multi-turn order collection)     │
│       └── RecommendationAgent (apriori / popularity ranking)   │
│                                                                 │
│  All agents → OpenAI SDK (base_url = Groq or RunPod)           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
     Groq API           RunPod LLM           Pinecone
  (local dev)          (production)       (RAG, optional)
```

---

## Two Deployment Modes

### Local Development

```
Frontend (Expo web/Android)
    │ POST http://localhost:8000/chat
    ▼
local_server.py  (FastAPI, synchronous)
    │
    ▼
AgentController → agents → Groq API (llama-3.3-70b-versatile, free)
```

- No RunPod account needed
- Groq free tier covers all development
- `PINECONE_API_KEY` left blank → DetailsAgent gracefully disabled (embeddings are local, no embedding URL needed)

### Production (RunPod Serverless)

```
Frontend (Expo APK / web build)
    │ POST https://api.runpod.ai/v2/<endpoint_id>/run
    ▼
main.py  →  runpod.serverless.start(handler=AgentController.get_response)
    │
    ▼
AgentController → agents → RunPod LLM (meta-llama/Llama-3.1-8B-Instruct)
```

- Same `AgentController` code — zero changes
- Provider swap is a `.env` change only (base_url + model_name)
- Docker image built from `python_code/api/`

---

## Response Contract

Every agent returns exactly this shape. The frontend and controller both depend on it:

```json
{
  "role": "assistant",
  "content": "The message shown to the user",
  "memory": {
    "agent": "which_agent_responded",
    "...": "agent-specific state fields"
  }
}
```

The `memory` field is the only state mechanism. There is no database or session store — state travels round-trip inside the message list.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| All agents use OpenAI SDK with configurable `base_url` | Provider-agnostic; swap Groq ↔ RunPod ↔ OpenAI in `.env` |
| `AgentProtocol` typed as a Protocol (structural typing) | Agents don't need to inherit a base class; duck-typed |
| State embedded in message `memory` field | No external DB; simplifies local dev significantly |
| RAG gracefully disabled when env vars absent | App runs fully without Pinecone; reduces setup friction |
| `json_mode=True` on all structured agents | Guarantees valid JSON from LLM; no second repair call needed |
| `local_server.py` mirrors RunPod response format | Frontend code doesn't branch on environment |
| Observability via `structlog` in `utils.py` | Single instrumentation point covers all agents automatically |
| `MetricsStore` as optional `AgentController` param | RunPod (`main.py`) works without it; local dev gets the dashboard |

## Observability Layer

```
Every LLM call (utils.py)
  → structlog: llm_call { model, latency_ms, input_tokens, output_tokens }
  → ContextVar token_counter += tokens

AgentController.get_response()
  → structlog: guard_decision, agent_routed
  → MetricsStore.record() at end of request

local_server.py
  → structlog: request_start, request_complete { request_id, total_ms }
  → GET /metrics  → MetricsStore.summary() as JSON
  → GET /dashboard → Chart.js dashboard, polls /metrics every 5s
```
