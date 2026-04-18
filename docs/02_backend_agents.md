# Backend — Agents Deep Dive

All agents live in `coffee_shop_customer_service_chatbot/python_code/api/agents/`.

---

## AgentProtocol (`agent_protocol.py`)

```python
class AgentProtocol(Protocol):
    def get_response(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        ...
```

This is Python's **structural subtyping** (duck typing with type hints). Any class with a `get_response(messages)` method satisfies this protocol. No inheritance needed. The `AgentController` holds a `dict[str, AgentProtocol]` and calls agents by name.

---

## utils.py — Shared LLM Layer

Every agent calls these — they never import `openai` directly.

### `get_chatbot_response(client, model_name, messages, temperature=0)`

Strips the `memory` field from each message before sending to the LLM (the LLM API only accepts `role` and `content`). Fixed params: `temperature=0`, `top_p=0.8`, `max_tokens=2000`.

**Observability:** Every call is timed with `time.perf_counter()` and emits a `structlog` event:
```json
{"event": "llm_call", "model": "...", "latency_ms": 210, "input_tokens": 145, "output_tokens": 42}
```

**Token accumulation:** A `ContextVar` (`_token_counter`) accumulates input/output tokens across all LLM calls within a single request. `agent_controller.py` resets it at request start and reads the total at the end to record in `MetricsStore`.

### `reset_token_counter()` / `get_token_counts()`

Helper functions for the token `ContextVar`. Called by `AgentController` to bracket a request.

### `get_embedding(embedding_client, model_name, text_input)`

Returns a list of embedding vectors. Used only by `DetailsAgent`. Takes a list of strings, returns `[[float, ...], ...]`.

### JSON mode

All agents that require structured JSON output pass `json_mode=True` to `get_chatbot_response`, which sets `response_format={"type": "json_object"}`. This guarantees the LLM returns valid JSON without a second LLM repair call.

---

## GuardAgent (`guard_agent.py`)

**Purpose:** Safety filter. Blocks questions unrelated to the coffee shop before they reach any specialist agent.

**Input:** Last 3 messages from history (`messages[-3:]`).

**System prompt logic:**
- Allowed: coffee shop questions, menu queries, ordering, recommendations
- Blocked: anything else (recipes, staff questions, off-topic)

**Output JSON from LLM:**
```json
{
  "chain of thought": "...",
  "decision": "allowed",
  "message": ""
}
```

**Postprocess:**
```python
def postprocess(self, output):
    try:
        output = json.loads(output)
        decision = output.get('decision', 'allowed')   # default: allow on parse failure
        message  = output.get('message', '')
    except (json.JSONDecodeError, KeyError):
        decision = 'allowed'   # fail-open: don't block if LLM returns garbage
        message  = ''
```

**Returned memory shape:**
```json
{
  "agent": "guard_agent",
  "guard_decision": "allowed" | "not allowed"
}
```

**Fail-open design:** If the LLM returns malformed JSON, the guard defaults to `"allowed"`. This prevents the guard from becoming a single point of failure that breaks all conversations.

---

## ClassificationAgent (`classification_agent.py`)

**Purpose:** Intent router. Reads the last 3 messages and decides which specialist agent should handle this turn.

**Three possible routes:**
- `details_agent` — questions about the shop, menu, ingredients, hours, location
- `order_taking_agent` — placing or modifying an order
- `recommendation_agent` — asking for a suggestion

**Output JSON from LLM:**
```json
{
  "chain of thought": "...",
  "decision": "order_taking_agent",
  "message": ""
}
```

**Postprocess:**
```python
decision = output.get('decision', 'order_taking_agent')  # default route on failure
```

Defaults to `order_taking_agent` on parse failure — the most common user action.

**Returned memory shape:**
```json
{
  "agent": "classification_agent",
  "classification_decision": "details_agent" | "order_taking_agent" | "recommendation_agent"
}
```

**Important:** The classification response is **not appended to the message list**. The controller reads `classification_decision` from its memory and discards the rest. The user never sees this agent's output.

---

## DetailsAgent (`details_agent.py`)

**Purpose:** RAG-powered Q&A about coffee shop details (hours, location, ingredients, menu descriptions).

**RAG enabled when:** `PINECONE_API_KEY` is set. Embeddings are generated locally using `sentence-transformers/all-MiniLM-L6-v2` (no external embedding API needed).

**RAG disabled behavior:** Returns a fallback message:
> "I don't have detailed product info available right now, but I'd be happy to help you place an order or give you a recommendation!"

**When RAG is enabled, the flow is:**
```
User message
  → get_embedding(user_message)          # embed the question
  → Pinecone index.query(vector, top_k=2) # nearest 2 chunks
  → source_knowledge = join(chunk texts)
  → Build prompt:
      "Using the contexts below, answer the query.
       Contexts: {source_knowledge}
       Query: {user_message}"
  → LLM call with the enriched prompt
  → Return plain text response
```

**Pinecone query:** namespace=`"ns1"`, `top_k=2`, includes metadata but not raw vectors. The `text` field in metadata is the chunk content.

**Returned memory shape:**
```json
{ "agent": "details_agent" }
```

No state carried forward — each question is answered independently.

---

## OrderTakingAgent (`order_taking_agent.py`)

**Purpose:** Multi-turn conversational order collection. Validates items against the menu, accumulates the order across turns, and triggers a recommendation before closing.

**Menu:** Hardcoded in the system prompt (19 items with prices). This is the largest architectural debt in the codebase.

**State recovery at start of each turn:**
```python
# Walk backwards through message history to find the last order_taking_agent message
for message_index in range(len(messages)-1, 0, -1):
    message = messages[message_index]
    if message["role"] == "assistant" and message.get("memory",{}).get("agent") == "order_taking_agent":
        step_number = message["memory"]["step number"]
        order       = message["memory"]["order"]
        asked_recommendation_before = message["memory"]["asked_recommendation_before"]
        last_order_taking_status = f"step number: {step_number}\norder: {order}"
        break
```

This state is **prepended to the user's current message** before the LLM call:
```python
messages[-1]['content'] = last_order_taking_status + " \n " + messages[-1]['content']
```

**LLM output JSON:**
```json
{
  "chain of thought": "...",
  "step number": "3",
  "order": [
    {"item": "Cappuccino", "quantity": 2, "price": 9.00},
    {"item": "Croissant",  "quantity": 1, "price": 3.25}
  ],
  "response": "Got it! 2 Cappuccinos and a Croissant. Anything else?"
}
```

**`json_mode=True`** is used on this call to guarantee valid JSON output — no second LLM repair pass needed.

**Recommendation trigger in `postprocess`:**
```python
if not asked_recommendation_before and len(output["order"]) > 0:
    recommendation_output = self.recommendation_agent.get_recommendations_from_order(messages, output['order'])
    response = recommendation_output['content']   # replace the order response with recommendation
    asked_recommendation_before = True
```

This means the **first time** an order has items, the user sees a recommendation message instead of the order confirmation. On the next turn, the actual order summary is shown. `asked_recommendation_before` prevents this from repeating.

**Returned memory shape:**
```json
{
  "agent": "order_taking_agent",
  "step number": "3",
  "order": [...],
  "asked_recommendation_before": true
}
```

**Step numbers** (defined by the LLM in the prompt):
1. Taking the order
2. Validating items
3. Asking if they want more
4–5. Handling additions
6. Closing with total and thank-you

---

## RecommendationAgent (`recommendation_agent.py`)

**Purpose:** Suggests items based on three strategies.

### Three recommendation strategies

#### 1. Apriori (market basket analysis)

Uses pre-computed association rules from `apriori_recommendations.json`.

**Data structure:**
```json
{
  "Cappuccino": [
    {"product": "Dark chocolate", "product_category": "Packaged Chocolate", "confidence": 0.497},
    {"product": "Latte",          "product_category": "Coffee",             "confidence": 0.471},
    ...
  ],
  "Latte": [...],
  ...
}
```

16 items have association rules. Rules were pre-trained on transaction history (see `recommendation_engine_training.ipynb`).

**`get_apriori_recommendation(products, top_k=5)` logic:**
1. For each product in the input list, fetch its association rules
2. Merge all rules into one list, sort by `confidence` descending
3. Remove duplicates
4. Cap at 2 recommendations per category (prevents over-recommending one category)
5. Return top `top_k` items

#### 2. Popularity

Uses `popularity_recommendation.csv` — 19 rows, columns: `product`, `product_category`, `number_of_transactions`.

**`get_popular_recommendation(product_categories=None, top_k=5)` logic:**
1. If `product_categories` provided, filter to those categories only
2. Sort by `number_of_transactions` descending
3. Return top 5 product names

**Most popular items overall:**
1. Cappuccino (1290 transactions)
2. Latte (1256)
3. Dark chocolate / Drinking (947)
4. Espresso shot (628)
5. Sugar Free Vanilla syrup (605)

#### 3. Popularity by category

Same as popularity but filtered first. Categories: `Coffee`, `Bakery`, `Flavours`, `Drinking Chocolate`, `Packaged Chocolate`.

### How the agent decides which strategy to use

`recommendation_classification(messages)` — an LLM call that reads the user's message and returns:
```json
{
  "chain of thought": "...",
  "recommendation_type": "apriori" | "popular" | "popular by category",
  "parameters": ["Cappuccino", "Latte"]   // items for apriori, or categories for popular-by-category
}
```

Defaults to `popular` on parse failure.

### Order-triggered recommendations (`get_recommendations_from_order`)

Called directly by `OrderTakingAgent` — skips the classification step, always uses apriori strategy based on items in the current order.

### Final LLM call

After getting recommendation item names, a second LLM call formats them into a friendly message:

```python
prompt = f"""
{messages[-1]['content']}
Please recommend me those items exactly: {recommendations_str}
"""
```

The LLM is told exactly which items to recommend — it only generates the natural language phrasing.

**Returned memory shape:**
```json
{ "agent": "recommendation_agent" }
```

No state carried forward.

---

## AgentController (`agent_controller.py`)

The orchestrator. Initialized once at server startup. Accepts an optional `MetricsStore` for observability.

```python
class AgentController:
    def __init__(self, metrics: MetricsStore | None = None):
        self.metrics = metrics
        # ... agents initialized ...
```

`RecommendationAgent` is instantiated once and shared between `agent_dict` and `OrderTakingAgent` — avoids loading the same JSON/CSV twice.

**`get_response(input)` flow:**
1. Resets the token counter (`reset_token_counter()`)
2. Calls `GuardAgent` — logs decision, short-circuits if blocked
3. Calls `ClassificationAgent` — logs chosen agent
4. Calls the chosen specialist agent
5. Calls `_record()` — writes latency, tokens, guard decision, and agent to `MetricsStore`

Logs emitted per request:
```json
{"event": "guard_decision", "decision": "allowed"}
{"event": "agent_routed",   "agent": "order_taking_agent"}
```

Note: The classification agent's response is discarded after reading `classification_decision` — it is not added to `messages`.

## metrics.py — MetricsStore

In-memory store (thread-safe deque, max 500 records). Records one `RequestRecord` per request:
- `timestamp`, `total_ms`, `guard_decision`, `chosen_agent`, `input_tokens`, `output_tokens`

`summary()` computes: total requests, requests in last 60s, avg latency, block rate, agent distribution, recent latency series, total tokens.

Served as JSON at `GET /metrics` and visualised at `GET /dashboard`.

---

## local_server.py

FastAPI wrapper that makes the backend usable locally and by the frontend without any code changes.

```python
class ChatInput(BaseModel):
    messages: list           # no type validation on individual messages

class ChatRequest(BaseModel):
    input: ChatInput         # mirrors { input: { messages } } frontend shape

@app.post("/chat")
def chat(request: ChatRequest):
    payload = {"input": {"messages": request.input.messages}}
    response = agent_controller.get_response(payload)
    return {"output": response}
```

CORS is open (`allow_origins=["*"]`) — appropriate for local dev, not production.

The response `{"output": response}` mirrors RunPod's `{"output": ...}` wrapper, so `chatBot.ts` reads `response.data["output"]` in both modes.

---

## main.py (Production)

```python
from agent_controller import AgentController
import runpod

def main():
    agent_controller = AgentController()
    runpod.serverless.start({"handler": agent_controller.get_response})
```

RunPod calls `agent_controller.get_response(input)` for each request. The `input` shape is identical to what `local_server.py` builds — this is by design.
