# Known Issues, Gaps & Behaviours to Understand

This document captures everything in the current codebase that is non-obvious, wrong, fragile, or important to know before making changes.

---

## Backend

### ~~1. Synchronous FastAPI — Blocks on Every LLM Call~~ ✅ Fixed

`local_server.py` and all agents are now fully `async def`. LLM calls use `AsyncOpenAI`. Requests no longer queue behind each other under concurrent load.

### 2. Menu is Hardcoded in System Prompt

The full 19-item menu with prices is a hardcoded multiline string inside `OrderTakingAgent.__init__`. It also exists separately in Firebase (frontend display) and `popularity_recommendation.csv` (ranking).

**File:** `agents/order_taking_agent.py:20-45`

**Impact:** Any menu change (new item, price update) requires editing the system prompt string manually. The three copies can diverge silently.

### 3. No Streaming

Every LLM call waits for the full response before returning. The user sees nothing for 3-8 seconds, then the full message appears.

**Impact:** Poor UX for long responses (especially order summaries).

### 4. State Lives in Message History

The `OrderTakingAgent` recovers order state by walking backwards through `messages` to find the last `order_taking_agent` memory object. If `messages` is not sent in full (frontend bug, truncation), order state is lost silently.

**File:** `agents/order_taking_agent.py:42-56`

**Impact:** Fragile; depends on the frontend always sending the complete message array.

### 5. `double_check_json_output` Is Dead Code

All agents now use `json_mode=True` which guarantees valid JSON directly from the LLM. `double_check_json_output` still exists in `agents/utils.py` but is never called anywhere. Safe to delete — keeping it is harmless but misleading.

**File:** `agents/utils.py:65`

### 6. Only Last 3 Messages Sent to Guard and Classification

```python
input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]
```

Guard and Classification agents only see the last 3 messages. For very long conversations, they lose earlier context. For classification this is usually fine (intent is in recent messages), but for guard it means a user who was blocked earlier could retry after 3 turns.

### 7. `temperature=0` for All Agents

```python
# utils.py:7
response = client.chat.completions.create(
    ...
    temperature=0,
    top_p=0.8,
    ...
)
```

All agents use deterministic generation. This is correct for guard and classification (you want consistent routing). For the recommendation agent's final response ("Here are my recommendations..."), it produces identical phrasing every time, which can feel robotic.

### 8. `RunPod` Package in Requirements for Local Dev

`runpod==1.7.1` is in `requirements.txt` even though it's only used in `main.py` (production). Every local `uv pip install -r requirements.txt` installs an unnecessary package.

### 9. No Input Validation on `/chat`

```python
class ChatInput(BaseModel):
    messages: list           # untyped — accepts any list content
```

Any list (including `[null]`, `[1, 2, 3]`) passes validation. Agents will crash downstream with unhelpful errors.

### 10. CORS Fully Open

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

Appropriate for local dev. Must be locked down (specific origins) before any public deployment.

### 11. No Rate Limiting

The `/chat` endpoint has no rate limiting. A single client can send unlimited requests, exhausting the Groq free-tier quota or causing runaway costs on RunPod. Fix: `slowapi` (`@limiter.limit("20/minute")`). Part of Stage 8.

**File:** `local_server.py`

### 11b. No Startup Config Validation

The server starts even if required env vars (`RUNPOD_TOKEN`, `RUNPOD_CHATBOT_URL`, `MODEL_NAME`) are missing. The first real request will crash with a confusing error instead of failing clearly at boot. Fix: an `@app.on_event("startup")` check. Part of Stage 8.

**File:** `local_server.py`

### 11c. Recommendation Agent: Empty Result Handling

```python
if recommendations == []:
    return {"role": "assistant", "content": "Sorry, I can't help with that..."}
```

This response has no `memory` key. The frontend's `response.memory?.order` check handles `undefined` gracefully, but any code that unconditionally reads `memory.agent` will throw.

---

## Frontend

### 12. Cart Key = Product Name String

Cart items are keyed by product name (`{ "Cappuccino": 2 }`). If the LLM returns `"cappuccino"` (lowercase) or `"Cappuccino "` (trailing space), `addToCart` creates a new key and the cart shows a duplicate entry or wrong quantity.

**File:** `components/CartContext.tsx:18`

**Dependency:** The LLM must return item names that exactly match Firebase product names.

### 13. `emptyCart()` Before Re-Adding From Order

Every time the order agent responds, the frontend wipes the cart and rebuilds it from the LLM's order:

**File:** `app/(tabs)/chatRoom.tsx:38-42`
```typescript
emptyCart()
responseMessage.memory.order.forEach((item: any) => {
    addToCart(item.item, item.quantity)
})
```

This means **manual cart additions (from home.tsx or details.tsx) are wiped** the moment the order agent responds. Cart additions from the browse screen and chat orders do not co-exist cleanly.

### ~~14. Order Screen Re-Fetches Firebase~~ ✅ Fixed

`productService.ts` now has a module-level cache with in-flight deduplication. Both `home.tsx` and `order.tsx` call `fetchProducts()` but only the first call hits Firebase — the second returns the cached result immediately.

### 15. Delivery Fee is Hardcoded `+1`

```typescript
// order.tsx:69
<Text>$ {totalPrice === 0 ? 0 : totalPrice + 1}</Text>
```

$1 delivery fee hardcoded in JSX. Not a constant, not configurable.

### 16. `SearchArea` Component Does Nothing

`components/SearchArea.tsx` renders a search bar UI but has no search logic. The search input is not connected to any filter. It's visual only.

### 17. `SizesSection` Component is Static

`components/SizesSection.tsx` renders size options (S/M/L) but doesn't affect the cart or price. Size selection is decorative only.

### 18. Firebase Typo in Env Var Name

```typescript
// config/firebaseConfig.ts
projectId: process.env.EXPO_PUBLIC_FIREBASE_PROHECT_Id
```

`PROHECT` instead of `PROJECT`. This typo is in both the config and the `.env_example.txt`, so they match. **Do not fix one without fixing the other.**

### 19. `memory` Typed as `any`

```typescript
interface MessageInterface {
    memory?: any;   // no structure enforced
}
```

The memory shape varies by agent and is accessed with optional chaining (`response.memory?.order`). TypeScript provides no protection against accessing wrong fields.

### ~~20. No Error Boundary~~ ✅ Fixed

`order.tsx` now has a full error state with a descriptive message and "Try again" retry button. `home.tsx` also shows an error state with retry. Both screens handle network failures gracefully.

---

## Shared / Design

### ~~21. No Tests~~ ✅ Fixed

Backend now has 90 passing tests across all agents, the server, and the eval runners (`pytest tests/ -v`). Uses `AsyncMock` — no API key needed to run. Frontend tests remain unimplemented.

### ~~22. No Observability~~ ✅ Fixed

`structlog` is now wired into `agents/utils.py` (every LLM call logs model, latency_ms, input/output tokens) and `agent_controller.py` (logs guard decision and chosen agent). `local_server.py` and `main.py` log request start/complete with a `request_id` and `total_ms`. Live metrics visible at `GET /dashboard` (Chart.js, auto-refreshes every 5s) and raw JSON at `GET /metrics`.

### ~~23. No Eval Framework~~ ✅ Fixed

Eval datasets in `tests/eval_data/` (25 guard cases, 21 classification cases, 9 recommendation cases). Runners in `tests/evals/` hit the real LLM and report per-case PASS/FAIL with an 80% threshold. 29 unit tests cover data integrity, runner scoring, and exit codes. Run with `make evals`.

### 24. `RecommendationAgent` Has No Memory

```python
def postprocess(self, output):
    return {
        "role": "assistant",
        "content": output,
        "memory": {"agent": "recommendation_agent"}   # no state
    }
```

The recommendation agent carries no state between turns. If the user asks "what else?" after a recommendation, the agent doesn't know what it recommended before. Classification will re-route to recommendation_agent, which starts fresh.

### 25. Guard Uses Last 3 Messages, Not Full History

A harmful user could:
1. Ask something off-topic (blocked)
2. Ask 3 legitimate questions
3. Ask the off-topic question again (now outside the 3-message window)

The guard would not recall the earlier block. Not a security issue for a coffee shop, but worth understanding.

---

## Quick Reference: What Breaks Without Each Env Var

| Missing var | Effect |
|---|---|
| `RUNPOD_TOKEN` | All LLM calls fail with 401; server crashes on first request |
| `RUNPOD_CHATBOT_URL` | LLM client defaults to OpenAI API; requests fail unless you have an OpenAI key |
| `MODEL_NAME` | `None` passed as model name; LLM API returns 400 |
| `PINECONE_API_KEY` | DetailsAgent disabled (graceful) — embeddings are local, no embedding URL needed |
| `EXPO_PUBLIC_RUNPOD_API_URL` | `API_URL` is `undefined`; axios throws on send |
| `EXPO_PUBLIC_FIREBASE_DATABASE_URL` | Firebase not initialized; empty product list (graceful) |
