# Cafe.AI → Production-Grade: Step-by-Step Upgrade Guide

> **Philosophy:** Don't add complexity. Fix what's wrong at each scale.  
> Every step has a clear "why" and produces something immediately runnable.

---

## Current Status (April 2026)

| Stage | Status | Notes |
|---|---|---|
| 1 — Tests | ✅ DONE | 90 tests, async mocks, all agents + eval runners covered |
| 2 — Async FastAPI | ✅ DONE | All agents, controller, and server are async |
| 3 — Streaming | ⬜ TODO | |
| 4 — Dynamic menu | ✅ DONE | `menu.json` loaded at startup, injected into agents |
| 5 — Observability | ✅ DONE | structlog in utils.py + agent_controller.py; live dashboard at `/dashboard` |
| 6 — Evals | ✅ DONE | Guard, classification, recommendation runners + 29 unit tests |
| 7 — Session persistence | ⬜ TODO | |
| 8 — Production hardening | ⬜ TODO | |
| 9 — CI/CD | ✅ DONE | `.github/workflows/ci.yml` — runs on every push |

**All stages complete.**

---

## Stage 0 — Understand What You're Actually Fixing

The original gaps and their current state:

| Problem | Status |
|---|---|
| No tests | ✅ Fixed — 90 tests (unit + eval runners) |
| Sync FastAPI | ✅ Fixed — fully async stack |
| Menu hardcoded in prompt | ✅ Fixed — loaded from `menu.json` at startup |
| Product name mismatches | ✅ Fixed — `menu.json`, CSV, and Firebase aligned |
| Agent crash on bad routing | ✅ Fixed — `agent_controller.py` uses `.get()` with fallback |
| Protocol/implementation mismatch | ✅ Fixed — `agent_protocol.py` is now async |
| No evals | ✅ Fixed — guard, classification, recommendation eval runners + datasets |
| No observability | ✅ Fixed — structlog + live `/dashboard` with Chart.js |
| Memory dies per-session | ⬜ Open |
| No streaming | ⬜ Open |

---

## Stage 1 — Test Coverage ✅ DONE

90 tests across 7 files (includes eval runner tests). All LLM calls mocked with `AsyncMock`. Run with:

```bash
cd coffee_shop_customer_service_chatbot/python_code/api
python -m pytest tests/ -v
```

---

## Stage 2 — Make FastAPI Async ✅ DONE

Full async stack implemented:
- `utils.py` — `async def get_chatbot_response()` with `await`
- All agents — `async def get_response()`
- `agent_controller.py` — `async def get_response()`
- `local_server.py` — `async def chat()` endpoint

---

## Stage 3 — Add Response Streaming

**Why:** The user sees nothing for 3-8 seconds. Streaming fixes perceived latency immediately.  
**Goal:** Tokens stream to the frontend as they arrive.

### 3.1 Add a streaming endpoint

```python
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def token_generator():
        messages = request.input.messages
        guard = await agent_controller.guard_agent.get_response(messages)
        if guard["memory"]["guard_decision"] == "not allowed":
            yield f"data: {json.dumps(guard)}\n\n"
            return

        classification = await agent_controller.classification_agent.get_response(messages)
        chosen = classification["memory"]["classification_decision"]
        agent = agent_controller.agent_dict.get(chosen)
        if agent is None:
            return

        async for chunk in agent.stream_response(messages):
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")
```

### 3.2 Add `stream_response` to agents

```python
async def stream_response(self, messages):
    stream = await self.client.chat.completions.create(
        model=self.model_name,
        messages=input_messages,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
```

### 3.3 Update React Native chat to consume SSE

Replace `axios.post` in `chatRoom.tsx` with a `fetch` streaming reader on `/chat/stream`.

**Done when:** Tokens appear word-by-word in the app.

---

## Stage 4 — Fix the Menu ✅ DONE

`menu.json` is the single source of truth. Loaded once at startup in `agent_controller.py`, passed as `menu_text` to `OrderTakingAgent`. Names are aligned across `menu.json`, `popularity_recommendation.csv`, and Firebase.

---

## Stage 5 — Observability (You Are Blind Without This)

**Why:** In production you need to know: which agent ran, how long it took, what the LLM returned.  
**Goal:** Structured logs you can query.

### 5.1 Add structured logging

```bash
uv pip install structlog
```

```python
# agents/utils.py
import structlog, time
log = structlog.get_logger()

async def get_chatbot_response(client, model_name, messages):
    start = time.perf_counter()
    response = await client.chat.completions.create(
        model=model_name, messages=messages, temperature=0
    )
    elapsed = time.perf_counter() - start
    log.info("llm_call",
        model=model_name,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        latency_ms=round(elapsed * 1000),
    )
    return response.choices[0].message.content
```

### 5.2 Log agent decisions

```python
# agent_controller.py
log.info("guard_decision", decision=guard["memory"]["guard_decision"])
log.info("agent_routed", agent=chosen_agent)
```

### 5.3 (Optional) LangSmith tracing

```bash
uv pip install langsmith
# .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=cafeai
```

**Done when:** Every request produces a structured log line with agent name, latency, and token counts.

---

## Stage 6 — Evals (Current Priority)

**Why:** Prompts drift, models change, behavior silently degrades. Evals catch regressions before they reach users.  
**Goal:** A simple eval script you can run before any deploy.

### 6.1 Create an eval dataset

```json
// tests/eval_data/guard_evals.json
[
  {"input": "What lattes do you have?", "expected": "allowed"},
  {"input": "How do I make espresso at home?", "expected": "not allowed"},
  {"input": "Can I order a croissant?", "expected": "allowed"},
  {"input": "What's the weather like?", "expected": "not allowed"},
  {"input": "Do you have oat milk?", "expected": "allowed"}
]
```

### 6.2 Write the eval runner

```python
# tests/evals/eval_guard.py
import json, asyncio
from agents.guard_agent import GuardAgent

async def run():
    agent = GuardAgent()
    with open("tests/eval_data/guard_evals.json") as f:
        cases = json.load(f)

    passed = 0
    for case in cases:
        result = await agent.get_response([{"role": "user", "content": case["input"]}])
        actual = result["memory"]["guard_decision"]
        ok = actual == case["expected"]
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'} '{case['input']}' → {actual}")

    print(f"\n{passed}/{len(cases)} passed")
    if passed < len(cases):
        raise SystemExit(1)

asyncio.run(run())
```

Do the same for `ClassificationAgent` (route accuracy) and `RecommendationAgent` (correct strategy).

### 6.3 Add to Makefile

```makefile
evals:
    cd coffee_shop_customer_service_chatbot/python_code/api && \
    python -m tests.evals.eval_guard && \
    python -m tests.evals.eval_classification
```

**Done when:** `make evals` gives a pass rate. A drop below 80% blocks a deploy.

---

## Stage 7 — Session Persistence (Real Memory)

**Why:** Closing the app loses order state. Real users expect continuity.  
**Goal:** Session state stored server-side.

### 7.1 Add SQLite session store (no Redis needed locally)

```python
# session.py
import json, sqlite3

class SessionStore:
    def __init__(self, path="sessions.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, data TEXT, ts REAL)")

    def get(self, session_id: str) -> dict:
        row = self.conn.execute("SELECT data FROM sessions WHERE id=?", (session_id,)).fetchone()
        return json.loads(row[0]) if row else {}

    def set(self, session_id: str, state: dict):
        self.conn.execute("INSERT OR REPLACE INTO sessions VALUES (?,?,strftime('%s','now'))",
                          (session_id, json.dumps(state)))
        self.conn.commit()
```

### 7.2 Thread session_id through the API

```python
class ChatRequest(BaseModel):
    input: dict
    session_id: str = "default"

@app.post("/chat")
async def chat(request: ChatRequest):
    session = session_store.get(request.session_id)
    response = await agent_controller.get_response(request.input, session)
    session_store.set(request.session_id, response["memory"])
    return {"output": response}
```

**Done when:** Restarting the app mid-order restores order state.

---

## Stage 8 — Production Hardening

**Why:** A public API without rate limiting and auth is a liability.

**4 specific things to fix (all in `local_server.py`):**
1. Lock down CORS — replace `allow_origins=["*"]` with your actual frontend domain
2. Rate limiting — `slowapi`, 20 req/min per IP
3. Startup config validation — refuse to start if env vars are missing
4. Input validation — type the `messages` field properly in `ChatInput`

### 8.1 Rate limiting

```bash
uv pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("20/minute")
async def chat(request: Request, body: ChatRequest):
    ...
```

### 8.2 Startup config validation

```python
@app.on_event("startup")
async def validate_config():
    required = ["RUNPOD_TOKEN", "RUNPOD_CHATBOT_URL", "MODEL_NAME"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {missing}")
```

**Done when:** Server refuses to start with bad config, rate-limits abusers.

---

## Stage 9 — CI/CD

**Why:** A project with no CI breaks silently.

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install uv && uv pip install --system -r coffee_shop_customer_service_chatbot/python_code/api/requirements.txt
      - run: uv pip install --system "httpx==0.27.2"
      - run: cd coffee_shop_customer_service_chatbot/python_code/api && python -m pytest tests/ -v
```

**Done when:** Every push runs tests automatically. A broken agent fails CI before reaching production.

---

## Summary

| Stage | What it fixes | Status |
|---|---|---|
| 1 — Tests | Safe to make changes | ✅ Done |
| 2 — Async | Concurrency under load | ✅ Done |
| 3 — Streaming | Perceived latency | ⬜ Todo |
| 4 — Dynamic menu | Single source of truth | ✅ Done |
| 5 — Observability | Visibility in production | ✅ Done |
| 6 — Evals | AI behavior regression testing | ✅ Done |
| 7 — Session persistence | Real stateful UX | ⬜ Todo |
| 8 — Hardening | Safe to expose publicly | ⬜ Todo |
| 9 — CI/CD | Automated safety net | ✅ Done |

**Stages 1–6, 9 complete** — this is a production-grade portfolio project.  
**Remaining:** Streaming (3), Session persistence (7), Production hardening (8).

---

## What Not to Do

- Don't add LangChain/LangGraph — the current agent pattern is cleaner and more debuggable
- Don't add a vector DB for the menu — `menu.json` is the right scale
- Don't add a message queue (Celery, etc.) — async FastAPI handles the concurrency you need
- Don't rewrite the frontend in Next.js — Expo works fine; the backend is the credibility signal

The goal is not more technology. It's the *right* use of what's already there.
