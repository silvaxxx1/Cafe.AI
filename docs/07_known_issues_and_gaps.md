# Known Issues, Gaps & Behaviours to Understand

This document captures everything in the current codebase that is non-obvious, wrong, fragile, or important to know before making changes.

---

## Backend

### ~~1. Synchronous FastAPI — Blocks on Every LLM Call~~ ✅ Fixed

`local_server.py` and all agents are now fully `async def`. LLM calls use `AsyncOpenAI`. Requests no longer queue behind each other under concurrent load.

### ~~2. Menu is Hardcoded in System Prompt~~ ✅ Fixed

`menu.json` is now the single source of truth. `AgentController` loads it at startup and injects `menu_text` into `OrderTakingAgent.__init__`. Menu changes only require editing `menu.json`.

### ~~3. No Streaming~~ ✅ Fixed

`POST /chat/stream` SSE endpoint is live in `local_server.py`. `agent_controller.get_stream_response()` handles the pipeline. DetailsAgent and RecommendationAgent truly stream; OrderTakingAgent fake-streams (JSON mode constraint). Frontend uses fetch+ReadableStream, updating the bubble in-place. First token arrives in ~1s.

### 4. State Lives in Message History

The `OrderTakingAgent` recovers order state by walking backwards through `messages` to find the last `order_taking_agent` memory object. If `messages` is not sent in full (frontend bug, truncation), order state is lost silently.

**File:** `agents/order_taking_agent.py:42-56`

**Impact:** Fragile; depends on the frontend always sending the complete message array.

### ~~5. `double_check_json_output` Is Dead Code~~ ✅ Fixed

Function has been removed from `agents/utils.py`.

### ~~6. Only Last 3 Messages Sent to Guard and Classification~~ ✅ Fixed

`CONTEXT_WINDOW = 6` constant defined in `agents/utils.py` and used by all three routing agents (guard, classification, `recommendation_classification`). Guard and classification now see the last 6 messages (~3 back-and-forth turns).

### ~~7. `temperature=0` for All Agents~~ ✅ Fixed (Recommendation only)

`RecommendationAgent`'s natural-language response call now uses `temperature=0.7` — phrasing varies across sessions while product selection stays deterministic. Guard and classification remain at `temperature=0`.

### ~~8. `RunPod` Package in Requirements for Local Dev~~ ✅ Fixed

`runpod==1.7.1` removed from `requirements.txt`. `main.py` still imports it (production RunPod environment has it installed). Local dev is unaffected.

### ~~9. No Input Validation on `/chat`~~ ✅ Fixed

`messages` is now typed as `list[Message]` with required `role` and `content` string fields. Empty lists are rejected. Invalid payloads return 422 before reaching any agent.

### ~~10. CORS Fully Open~~ ✅ Fixed

`allow_origins` is now locked to `localhost:8081`, `localhost:19006`, and `127.0.0.1:8081`. Production deploy adds the Vercel frontend URL. No more `allow_origins=["*"]`.

### ~~11. No Rate Limiting~~ ✅ Fixed

`slowapi` is wired in — 20 requests/minute per IP. Exceeding the limit returns 429 automatically.

### ~~11b. No Startup Config Validation~~ ✅ Fixed

Server now checks for `RUNPOD_TOKEN`, `RUNPOD_CHATBOT_URL`, and `MODEL_NAME` at startup. If any are missing, it prints a clear error and exits before binding the port.

### ~~11c. Recommendation Agent: Empty Result Handling~~ ✅ Fixed

Both `get_response()` and `get_stream_response()` now include a `memory` key on the empty-list fallback path, consistent with all other code paths.

---

## Frontend

### ~~12. Cart Key = Product Name String~~ ✅ Fixed

`CartContext` now normalises all keys on write via `normaliseKey()` (`.trim().toLowerCase()`). `"Cappuccino"`, `"cappuccino"`, and `"Cappuccino "` all resolve to the same cart slot. Read sites (`CartProductList.tsx`, `order.tsx`) also normalise on lookup.

### ~~13. `emptyCart()` Before Re-Adding From Order~~ ✅ Fixed

`syncCartFromOrder(order)` replaces the `emptyCart()` + rebuild pattern. It tracks which keys came from LLM responses and only updates those — items added manually from the browse screen survive agent responses. Items dropped from the LLM order are removed; items not mentioned are untouched.

### ~~14. Order Screen Re-Fetches Firebase~~ ✅ Fixed

`productService.ts` now has a module-level cache with in-flight deduplication. Both `home.tsx` and `order.tsx` call `fetchProducts()` but only the first call hits Firebase — the second returns the cached result immediately.

### ~~15. Delivery Fee is Hardcoded `+1`~~ ✅ Fixed

`const DELIVERY_FEE = 1.00` defined at the top of `order.tsx`. All three JSX occurrences reference the constant.

### ~~16. `SearchArea` Component Does Nothing~~ ✅ Fixed

`SearchArea` now accepts an `onSearch` callback and renders a real `TextInput`. `home.tsx` passes `setSearchQuery` and filters `shownProducts` by both category and search query in real time.

### ~~17. `SizesSection` Component is Static~~ ✅ Fixed

`SizesSection` is now a controlled component with `selectedSize` / `onSizeChange` props. Exports `SIZE_MODIFIERS = { S: -$0.50, M: $0, L: +$0.50 }`. Each button shows the volume and price modifier. `details.tsx` tracks selected size, computes `adjustedPrice = basePrice + modifier` live, displays it in the action bar, and passes it to `addToCart`. `CartContext` stores price overrides in `cartPrices` state; `CartProductList` and `order.tsx` use the override price when computing totals.

### ~~18. Firebase Typo in Env Var Name~~ ✅ Fixed

`EXPO_PUBLIC_FIREBASE_PROHECT_Id` → `EXPO_PUBLIC_FIREBASE_PROJECT_ID` corrected simultaneously in `firebaseConfig.ts`, `.env_example.txt`, and `.env`.

### ~~19. `memory` Typed as `any`~~ ✅ Fixed

`types/types.ts` now exports a proper `AgentMemory` union type covering all four agent shapes (`GuardMemory`, `ClassificationMemory`, `OrderMemory`, `RecommendationMemory`). `MessageInterface.memory`, `chatRoom.tsx` local variable, and `chatBot.ts` `StreamEvent` all use `AgentMemory`.

### ~~20. No Error Boundary~~ ✅ Fixed

`order.tsx` now has a full error state with a descriptive message and "Try again" retry button. `home.tsx` also shows an error state with retry. Both screens handle network failures gracefully.

---

## Shared / Design

### ~~21. No Tests~~ ✅ Fixed

Backend: 126 passing pytest tests across all agents, server, streaming, session, and eval runners (`make test`). No API key needed.

Frontend: 34 passing Jest tests — `CartContext` (13), `MessageItem` (12), `SizesSection` (8), `productService` (4). Run with `make test-frontend`. `make test-all` runs both suites in sequence.

### ~~22. No Observability~~ ✅ Fixed

`structlog` is now wired into `agents/utils.py` (every LLM call logs model, latency_ms, input/output tokens) and `agent_controller.py` (logs guard decision and chosen agent). `local_server.py` and `main.py` log request start/complete with a `request_id` and `total_ms`. Live metrics visible at `GET /dashboard` (Chart.js, auto-refreshes every 5s) and raw JSON at `GET /metrics`.

### ~~23. No Eval Framework~~ ✅ Fixed

Eval datasets in `tests/eval_data/` (25 guard cases, 21 classification cases, 9 recommendation cases). Runners in `tests/evals/` hit the real LLM and report per-case PASS/FAIL with an 80% threshold. 29 unit tests cover data integrity, runner scoring, and exit codes. Run with `make evals`.

### ~~24. `RecommendationAgent` Has No Memory~~ ✅ Fixed

`postprocess()` now stores the resolved recommendation list in `memory.last_recommendations`. On the next turn, `get_response()` and `get_stream_response()` walk back through message history, find the last recommendation memory, and inject `already_recommended` items into the `recommendation_classification` system prompt — preventing the same items from being suggested again.

### ~~25. Guard Uses Last 3 Messages, Not Full History~~ ✅ Fixed

See Issue 6. Guard now uses `CONTEXT_WINDOW = 6`.

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
