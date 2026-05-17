# Cafe.AI V2 Plan

> **V1 is complete.** All 9 backend upgrade stages done, 120 tests passing, CI live.  
> V2 is about closing the gap between a solid backend demo and a product that actually feels finished end-to-end.

---

## V1 Boundary (What's Locked In)

- Multi-agent pipeline: Guard → Classification → Agent
- Streaming SSE responses
- SQLite session persistence
- Observability dashboard + structured logs
- Eval runners with 80% threshold
- CI on every push
- Production hardening: CORS, rate limiting, startup validation

---

## V2 Philosophy

V1 proved the architecture. V2 makes the **user experience match the backend quality**.  
The frontend still has decorative components, a cart that fights the chat, and zero search logic.  
Fix those first. Then raise AI quality. Then add the one missing feature (RAG).

**Priority order: Frontend parity → AI quality → Cleanup → Stretch.**

---

## Stage 1 — Frontend Functional Parity

*The biggest gap. Several UI components are visual-only. Fix them before anything else.*

### 1.1 Wire up SearchArea

`components/SearchArea.tsx` renders a search bar but has no logic. Connect it to filter the product list in `home.tsx`.

**File:** `components/SearchArea.tsx`, `app/(tabs)/home.tsx`  
**Done when:** Typing in the search bar filters products by name in real time.

### 1.2 Make SizesSection functional

`components/SizesSection.tsx` renders S/M/L size buttons but selection has no effect. Size should adjust price and be passed to the cart.

**File:** `components/SizesSection.tsx`, `app/details.tsx`  
**Done when:** Selecting a size changes the displayed price and the cart entry reflects the chosen size.

### 1.3 Fix the cart-wipe bug

Every time the order agent responds, `chatRoom.tsx` calls `emptyCart()` then rebuilds from the LLM's order. This silently wipes any items added manually from the browse screen.

```typescript
// current — chatRoom.tsx:38-42
emptyCart()
responseMessage.memory.order.forEach((item: any) => {
    addToCart(item.item, item.quantity)
})
```

**Fix:** Merge LLM order into the existing cart instead of replacing it. Items added manually should survive an agent response.

**File:** `app/(tabs)/chatRoom.tsx`, `components/CartContext.tsx`  
**Done when:** Adding a latte from the home screen, then asking the chat to add a croissant, results in both items in the cart.

### 1.4 Replace hardcoded delivery fee

`order.tsx` hardcodes `+1` for delivery. Make it a named constant and surface it clearly in the UI.

```typescript
// order.tsx:69 — current
<Text>$ {totalPrice === 0 ? 0 : totalPrice + 1}</Text>
```

**File:** `app/(tabs)/order.tsx`  
**Done when:** Delivery fee is a constant (e.g. `DELIVERY_FEE = 1`) referenced by name, not a magic number in JSX.

### 1.5 Normalise cart keys

Cart items are keyed by exact product name string. If the LLM returns `"cappuccino"` instead of `"Cappuccino"`, a duplicate entry appears.

**Fix:** Normalise keys on insert — trim whitespace, title-case or lowercase consistently.

**File:** `components/CartContext.tsx:18`  
**Done when:** `"cappuccino"`, `"Cappuccino"`, and `"Cappuccino "` all resolve to the same cart slot.

### 1.6 Show product images in chat responses

When the agent recommends or discusses products, the chat bubble should display the relevant product images inline — not just text. Images are already bundled locally; this is a frontend-only change.

**Approach:** Read product names from `memory` (already returned by recommendation and order agents) rather than parsing free-form text. Look each name up in `constants/productImages.ts` and render image cards below the assistant's text bubble.

```typescript
// chatRoom.tsx — after receiving a response
const mentionedProducts = responseMessage.memory?.order
    ?? responseMessage.memory?.recommendations
    ?? []

// render a horizontal scroll of product cards beneath the bubble
mentionedProducts.map((item) => (
    <ProductCard key={item.item} name={item.item} image={productImages[item.image_url]} />
))
```

**Files:** `app/(tabs)/chatRoom.tsx`, `components/MessageItem.tsx`, `constants/productImages.ts`  
**No backend changes needed** — `memory` already carries product names; images are already mapped locally.  
**Done when:** A recommendation response shows image cards for the suggested products beneath the chat bubble, tappable to navigate to the product detail screen.

---

## Stage 2 — AI Quality

*The agents work. Now make them feel smarter and less robotic.*

### 2.1 Give RecommendationAgent turn memory

**The problem:**  
`postprocess()` returns a bare `memory` object with no state:

```python
# agents/recommendation_agent.py:172-177
def postprocess(self, output):
    return {
        "role": "assistant",
        "content": output,
        "memory": {"agent": "recommendation_agent"}   # no items stored
    }
```

Same pattern in `get_stream_response()` at line 219:
```python
yield {"type": "done", "memory": {"agent": "recommendation_agent"}}
```

When the user asks "what else?" the ClassificationAgent re-routes to `RecommendationAgent`, which calls `recommendation_classification()` fresh with no knowledge of what it already suggested. The user gets the same list again.

**Root cause:** `recommendations` (the resolved list of product names) is computed inside `get_response()` and `get_stream_response()` but never written back into `memory` before returning.

**Fix:**  
Store the resolved `recommendations` list in `memory` on every response. On the next turn, walk back through `messages` to find the last `recommendation_agent` memory and pass `already_recommended` into the system prompt so the LLM knows to avoid repeating them.

```python
# Step 1 — store recommendations in memory (both get_response and get_stream_response)
"memory": {
    "agent": "recommendation_agent",
    "last_recommendations": recommendations   # e.g. ["Cappuccino", "Croissant"]
}

# Step 2 — read prior recommendations at the start of get_response()
already_recommended = []
for msg in reversed(messages):
    if msg.get("memory", {}).get("agent") == "recommendation_agent":
        already_recommended = msg["memory"].get("last_recommendations", [])
        break

# Step 3 — inject into recommendation_classification system prompt
"Do not recommend these items as they were already suggested: " + ", ".join(already_recommended)
```

**Files:**
- `agents/recommendation_agent.py:172-177` — `postprocess()`
- `agents/recommendation_agent.py:219` — `get_stream_response()` done event
- `agents/recommendation_agent.py:100` — `get_response()` entry point
- `agents/recommendation_agent.py:179` — `get_stream_response()` entry point
- `agents/recommendation_agent.py:73` — `recommendation_classification()` system prompt

**Done when:** Asking "what else?" after a recommendation returns a different set of products, and the agent does not repeat the items it already suggested.

---

### 2.2 Expand guard/classification context window

**The problem:**  
Both `GuardAgent` and `ClassificationAgent` slice the message history to only the last 3 turns:

```python
# agents/guard_agent.py:46
input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

# agents/classification_agent.py:35
input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]
```

`RecommendationAgent.recommendation_classification()` has the same slice at line 95.

**Consequences:**
- A user blocked by the guard can ask 3 unrelated questions and retry the blocked query — the guard will no longer see the original violation.
- The classifier loses conversation context in longer sessions (e.g. a user mid-order who switches topic briefly).
- Recommendation classification loses awareness of what the user ordered earlier in the conversation.

**Why 3 was chosen:** Likely a cost/latency trade-off at the time — smaller context = fewer tokens = faster guard calls. This is still valid reasoning; the fix is to raise it to a better default, not remove the bound entirely.

**Fix:**  
Define a single constant and use it in all three places:

```python
# agent_controller.py (or a shared config)
CONTEXT_WINDOW = 6   # covers ~3 back-and-forth turns

# agents/guard_agent.py:46
input_messages = [{"role": "system", "content": system_prompt}] + messages[-CONTEXT_WINDOW:]

# agents/classification_agent.py:35
input_messages = [{"role": "system", "content": system_prompt}] + messages[-CONTEXT_WINDOW:]

# agents/recommendation_agent.py:95
input_messages = [{"role": "system", "content": system_prompt}] + messages[-CONTEXT_WINDOW:]
```

Do **not** send the full history to guard/classification — unbounded history makes token costs unpredictable and adds latency for minimal gain. 6 messages (3 user + 3 assistant) covers all realistic conversation patterns for a coffee ordering session.

**Files:**
- `agents/guard_agent.py:46`
- `agents/classification_agent.py:35`
- `agents/recommendation_agent.py:95`, `132`, `156`, `214`

**Done when:** Guard, classification, and recommendation classification all use a shared `CONTEXT_WINDOW = 6` constant. A user cannot slip past a prior guard block by padding with 3 clean messages.

---

### 2.3 Add response variation to RecommendationAgent

**The problem:**  
`utils.py` defaults `temperature=0` for every LLM call:

```python
# agents/utils.py:25
async def get_chatbot_response(
    client, model_name, messages,
    temperature: float = 0,   # deterministic for all agents
    json_mode: bool = False,
):
```

This is correct for `GuardAgent` and `ClassificationAgent` — routing decisions must be deterministic. But `RecommendationAgent` has two distinct LLM calls:

1. **`recommendation_classification()`** — structured JSON output, picks recommendation type. Needs `temperature=0`. ✅
2. **`get_response()` line 134 / `get_stream_response()` line 216** — free-form natural language ("Here's what I'd suggest…"). Currently also `temperature=0`, producing identical phrasing on every call. ❌

**Fix:**  
Pass `temperature=0.7` only to the natural-language response call. The `get_chatbot_response` signature already accepts a `temperature` argument — no utility changes needed.

```python
# agents/recommendation_agent.py:134 — get_response()
chatbot_output = await get_chatbot_response(
    self.client, self.model_name, input_messages, temperature=0.7   # add this
)

# agents/recommendation_agent.py:216 — get_stream_response()
async for token in get_chatbot_response_stream(
    self.client, self.model_name, input_messages, temperature=0.7   # add this
):
```

Keep `recommendation_classification()` at `temperature=0` (line 97) — it uses `json_mode=True` and must be deterministic.

**Files:**
- `agents/recommendation_agent.py:134` — `get_response()` language call
- `agents/recommendation_agent.py:216` — `get_stream_response()` language call
- `agents/recommendation_agent.py:97` — `recommendation_classification()` — leave unchanged

**Done when:** Sending "what do you recommend?" twice in separate sessions produces the same product list (deterministic selection) but differently worded responses (varied language). The structured classification step remains `temperature=0`.

---

### 2.4 Fix missing `memory` key on empty recommendation response

**The problem:**  
When the recommendation list resolves to empty, both `get_response()` and `get_stream_response()` return a response with no `memory` key:

```python
# agents/recommendation_agent.py:113-114 — get_response()
if recommendations == []:
    return {"role": "assistant", "content": "Sorry, I can't help with that. Can I help you with your order?"}

# agents/recommendation_agent.py:192-196 — get_stream_response()
if not recommendations:
    content = "Sorry, I can't help with that. Can I help you with your order?"
    yield {"type": "token", "delta": content}
    yield {"type": "done", "memory": {"agent": "recommendation_agent"}}  # stream has it, get_response doesn't
```

The stream path (line 195) already yields a `memory` dict — only the non-stream `get_response()` path is missing it. Any downstream code that unconditionally reads `response["memory"]["agent"]` (e.g. metrics logging, future typed memory) will throw a `KeyError` on the empty-list code path.

**Fix:**  
Add `memory` to the early-return in `get_response()` to match the stream path:

```python
# agents/recommendation_agent.py:113-114
if recommendations == []:
    return {
        "role": "assistant",
        "content": "Sorry, I can't help with that. Can I help you with your order?",
        "memory": {"agent": "recommendation_agent"}   # add this
    }
```

**File:** `agents/recommendation_agent.py:113-114`  
**Done when:** Every response from `RecommendationAgent` — including the empty-list fallback — contains a `memory` key with `agent: "recommendation_agent"`. Both code paths are consistent.

---

### 2.5 Apply context window fix to `get_recommendations_from_order`

**The problem:**  
Section 2.2 lists the `messages[-3:]` slice in guard, classification, and `recommendation_classification()`. There is a fourth occurrence that was missed:

```python
# agents/recommendation_agent.py:156 — get_recommendations_from_order()
input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]
```

`get_recommendations_from_order()` is called by `OrderTakingAgent` to trigger an automatic upsell recommendation just before closing an order. It has the same 3-message blind spot — if the order was built across a long conversation, the upsell prompt loses earlier context about what the user said they liked or didn't want.

**Fix:**  
Apply the same `CONTEXT_WINDOW` constant from 2.2:

```python
# agents/recommendation_agent.py:156
input_messages = [{"role": "system", "content": system_prompt}] + messages[-CONTEXT_WINDOW:]
```

**File:** `agents/recommendation_agent.py:156` — `get_recommendations_from_order()`  
**Dependency:** Implement after 2.2 (the constant must exist first).  
**Done when:** All five `messages[-3:]` slices across the codebase are replaced with `messages[-CONTEXT_WINDOW:]`. No instance remains hardcoded.

---

## Stage 3 — Type Safety + Cleanup

*Low risk, high credibility. Clean up the things that would make a code reviewer wince.*

### 3.1 Type the `memory` field in the frontend

```typescript
interface MessageInterface {
    memory?: any;  // current
}
```

Define a proper union type covering all agent memory shapes: `GuardMemory`, `OrderMemory`, `RecommendationMemory`, etc.

**File:** `types/types.ts`  
**Done when:** TypeScript catches access to `memory.order` when the agent is `guard_agent`.

### 3.2 Delete dead `double_check_json_output`

All agents use `json_mode=True`. The fallback function in `agents/utils.py:65` is never called. Delete it.

**File:** `agents/utils.py`  
**Done when:** Function is gone, no references remain.

### 3.3 Remove `runpod` from local dev requirements

`runpod==1.7.1` is in `requirements.txt` but only used in `main.py` (production RunPod handler). Local dev installs it unnecessarily.

**Fix:** Either split into `requirements.txt` (local) and `requirements.prod.txt` (RunPod), or move the runpod import inside `main.py` with a lazy install note.

**File:** `requirements.txt`, `main.py`  
**Done when:** `uv pip install -r requirements.txt` for local dev does not pull `runpod`.

### 3.4 Fix Firebase env var typo (carefully)

```typescript
// config/firebaseConfig.ts
projectId: process.env.EXPO_PUBLIC_FIREBASE_PROHECT_Id  // typo
```

`PROHECT` is misspelled in both `firebaseConfig.ts` and `.env_example.txt` — they match, so it works.

**Fix:** Correct to `PROJECT` in both files simultaneously, and update any `.env` files that use the old name.

**File:** `config/firebaseConfig.ts`, `.env_example.txt`  
**Done when:** Env var is `EXPO_PUBLIC_FIREBASE_PROJECT_ID` everywhere and Firebase still initialises correctly.

---

## Stage 4 — Stretch: Wire Up DetailsAgent (RAG)

*Currently gracefully disabled when `PINECONE_API_KEY` is unset. V2 makes it real.*

`DetailsAgent` embeds queries locally with sentence-transformers and queries Pinecone. The code is written — it just needs a Pinecone index populated.

**Steps:**
1. Create a free Pinecone index
2. Run `python_code/build_index.py` to embed and upload `products/fero_cafe_about_us.txt` + product descriptions
3. Set `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` in `.env`
4. Verify: ask the chatbot "what's your sourcing story?" and confirm it retrieves from the index

**Done when:** DetailsAgent returns RAG-grounded answers about the cafe and products, not just LLM hallucination.

---

## Stage 5 — Frontend Tests

*The last gap between "strong mid-level" and "senior end-to-end". The backend has 120 tests and an eval framework. The frontend has zero. This stage closes that.*

**Infrastructure already in place** — `jest-expo` and `react-test-renderer` are already in `devDependencies`. The `test` script is wired in `package.json`. No new tooling needed — just write the tests.

```json
// package.json — already configured
"scripts": { "test": "jest --watchAll" },
"jest": { "preset": "jest-expo" }
```

---

### 5.1 CartContext — unit tests

`CartContext` is the most critical shared state in the app. It drives the cart badge, order screen total, and chat-to-cart sync. It has no tests.

**What to test:**
- `addToCart(name, qty)` — item appears in cart with correct quantity
- `addToCart` called twice with same name — quantities merge, not duplicate entries
- `addToCart` with different casing (`"cappuccino"` vs `"Cappuccino"`) — should land in same slot (once 1.5 is fixed)
- `emptyCart()` — cart is cleared
- `totalPrice` — computed correctly across multiple items
- `removeFromCart(name)` — item removed, total recalculated

**File:** `components/CartContext.tsx`  
**Test file:** `components/__tests__/CartContext.test.tsx`

```typescript
import { renderHook, act } from '@testing-library/react-native'
import { CartProvider, useCart } from '../CartContext'

const wrapper = ({ children }) => <CartProvider>{children}</CartProvider>

test('addToCart adds item with quantity', () => {
    const { result } = renderHook(() => useCart(), { wrapper })
    act(() => result.current.addToCart('Cappuccino', 2))
    expect(result.current.cart['Cappuccino']).toBe(2)
})

test('addToCart merges duplicate entries', () => {
    const { result } = renderHook(() => useCart(), { wrapper })
    act(() => result.current.addToCart('Latte', 1))
    act(() => result.current.addToCart('Latte', 1))
    expect(result.current.cart['Latte']).toBe(2)
})

test('emptyCart clears all items', () => {
    const { result } = renderHook(() => useCart(), { wrapper })
    act(() => result.current.addToCart('Croissant', 1))
    act(() => result.current.emptyCart())
    expect(Object.keys(result.current.cart)).toHaveLength(0)
})
```

---

### 5.2 MessageItem — component tests

`MessageItem` renders each chat bubble. It has two meaningful branches: user messages (right-aligned) and assistant messages (left-aligned, with optional streaming indicator). Neither is tested.

**What to test:**
- Renders user message content correctly
- Renders assistant message content correctly
- Shows typing indicator when `isTyping` prop is true
- Does not show typing indicator for user messages

**File:** `components/MessageItem.tsx`  
**Test file:** `components/__tests__/MessageItem.test.tsx`

```typescript
import { render } from '@testing-library/react-native'
import MessageItem from '../MessageItem'

test('renders user message', () => {
    const { getByText } = render(
        <MessageItem message={{ role: 'user', content: 'I want a latte' }} />
    )
    expect(getByText('I want a latte')).toBeTruthy()
})

test('renders assistant message', () => {
    const { getByText } = render(
        <MessageItem message={{ role: 'assistant', content: 'Sure! One latte coming up.' }} />
    )
    expect(getByText('Sure! One latte coming up.')).toBeTruthy()
})
```

---

### 5.3 productService — unit tests

`productService.ts` has a module-level cache with in-flight deduplication. This logic is non-trivial and untested.

**What to test:**
- Returns empty array when Firebase is not configured
- Caches result — second call returns same object reference without re-fetching
- In-flight deduplication — two simultaneous calls resolve to the same promise

**File:** `services/productService.ts`  
**Test file:** `services/__tests__/productService.test.ts`

Mock Firebase so tests run without credentials:
```typescript
jest.mock('../../config/firebaseConfig', () => ({ db: null }))
```

---

### 5.4 Add frontend test script to Makefile

Surface frontend tests alongside the backend so they're part of the same workflow:

```makefile
# Makefile
test-frontend:
    cd coffee_shop_customer_service_chatbot/coffee_shop_app && npx jest --watchAll=false

test-all: test test-frontend
```

**Done when:** `make test-all` runs both backend (120 pytest tests) and frontend (Jest) in sequence. A CI step can be added to run `test-all` on every push.

---

### Coverage target

Aim for these 3 files as the V2 baseline — they cover the most critical state and rendering logic with the fewest dependencies:

| File | Tests | Why |
|---|---|---|
| `CartContext.tsx` | 6 unit tests | Core shared state — most likely to regress |
| `MessageItem.tsx` | 4 component tests | Chat bubble rendering — core UI |
| `productService.ts` | 3 unit tests | Cache logic — non-obvious, easy to break |

**13 tests is enough for V2.** This isn't about 100% coverage — it's about demonstrating that frontend testing is a first-class concern, not an afterthought.

**Files:**
- `components/__tests__/CartContext.test.tsx` — new
- `components/__tests__/MessageItem.test.tsx` — new
- `services/__tests__/productService.test.ts` — new
- `Makefile` — add `test-frontend` and `test-all` targets

**Done when:** `make test-all` passes. Both backend and frontend tests run in CI.

---

## Summary

| Stage | What it fixes | Priority |
|---|---|---|
| 1 — Frontend parity | Search, sizes, cart-wipe, delivery fee, cart keys, product images in chat | P0 — most visible to users |
| 2 — AI quality | Recommendation memory, context window, response variation, missing memory key, order upsell window | P1 — makes AI feel smarter |
| 3 — Cleanup | Types, dead code, runpod dep, Firebase typo | P2 — code quality |
| 4 — RAG | DetailsAgent actually answers product questions | P3 — stretch feature |
| 5 — Frontend tests | CartContext, MessageItem, productService — closes the senior gap | P1 — credibility signal |

**Start with Stage 1.** Stages 2, 3, and 5 can be done in any order after that. Stage 4 requires external infrastructure (Pinecone account).

---

## What Not to Add in V2

- User authentication / accounts — scope creep; this is a demo, not a SaaS
- Payment processing — same reason
- Push notifications — the app doesn't have persistent users yet
- A new LLM provider — the OpenAI-compatible abstraction already handles this with a `.env` change
- Rewrite the frontend in Next.js — Expo is fine; the backend is the credibility signal
