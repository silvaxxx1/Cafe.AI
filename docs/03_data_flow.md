# End-to-End Data Flow

This document traces every request from user tap to screen update, with exact file and line references.

---

## Flow 1 — User Sends a Chat Message

### Step 1: User types and taps send

**File:** `app/(tabs)/chatRoom.tsx` — `handleSendMessage()`

```
User taps send
  → message = textRef.current.trim()
  → InputMessages = [...messages, { content: message, role: 'user' }]
  → setMessages(InputMessages)          // optimistic UI update
  → textRef.current = ''               // clear input
  → setIsTyping(true)                  // show TypingIndicator
  → responseMessage = await callChatBotAPI(InputMessages)
```

The **full message history** is sent on every request — not just the latest message. This is how context is preserved without a server-side session.

### Step 2: HTTP call to backend

**File:** `services/chatBot.ts` — `callChatBotAPI(messages)`

```
axios.post(API_URL, {
    input: { messages }        // { input: { messages: [...] } }
}, {
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
    }
})
```

`API_URL` = `process.env.EXPO_PUBLIC_RUNPOD_API_URL` (e.g. `http://localhost:8000/chat`).

Response read as: `output = response.data["output"]` — the `output` key wraps the agent's return value.

### Step 3: FastAPI receives the request

**File:** `python_code/api/local_server.py` — `POST /chat`

```
request.input.messages  →  payload = {"input": {"messages": [...]}}
                        →  agent_controller.get_response(payload)
                        →  return {"output": response}
```

### Step 4: AgentController orchestrates

**File:** `python_code/api/agent_controller.py` — `get_response(input)`

```
messages = input["input"]["messages"]

[1] GuardAgent.get_response(messages[-3:])
      → LLM call (Groq / RunPod)
      → json.loads(output)
      → if decision == "not allowed": return guard response immediately

[2] ClassificationAgent.get_response(messages[-3:])
      → LLM call
      → json.loads(output)
      → classification_decision = "order_taking_agent" (or details/recommendation)

[3] agent_dict[chosen_agent].get_response(messages)
      → specialist agent runs (see below)
      → returns { role, content, memory }
```

### Step 5: Response travels back

```
agent.get_response()  →  AgentController  →  local_server.py
  →  {"output": {"role": "assistant", "content": "...", "memory": {...}}}
  →  axios response  →  chatBot.ts returns outputMessage
  →  chatRoom.tsx: setIsTyping(false)
  →  setMessages(prev => [...prev, responseMessage])
```

### Step 6: Cart update (if order agent responded)

**File:** `app/(tabs)/chatRoom.tsx`

```python
if (responseMessage.memory?.order) {
    emptyCart()                                 // wipe previous cart
    responseMessage.memory.order.forEach(item => {
        addToCart(item.item, item.quantity)     // repopulate from LLM order
    })
}
```

This is the **chat-to-cart bridge**. Every time the order agent responds with a non-empty `order` array, the cart is wiped and rebuilt from the LLM's current understanding of the order.

---

## Flow 2 — Menu Browse (Home Screen)

**File:** `app/(tabs)/home.tsx`

```
useEffect (mount)
  → fetchProducts()                         // services/productService.ts
      → if (!fireBaseDB): return []         // graceful degradation
      → ref(fireBaseDB, 'products')
      → get(snapshot)
      → parse snapshot.val() into Product[]
  → setProducts(data)
  → extract unique categories → setProductCategories(...)
  → setShownProducts(data)

useEffect (selectedCategory changes)
  → if selectedCategory === 'All': show all
  → else: filter products by category
  → setShownProducts(filtered)
```

### Product data shape (from Firebase):
```typescript
interface Product {
    id: string;
    category: string;       // "Coffee", "Bakery", "Flavours", ...
    description: string;
    image_url: string;      // remote URL for Image component
    name: string;           // used as cart key
    price: number;
    rating: number;
}
```

---

## Flow 3 — Cart State Management

**File:** `components/CartContext.tsx`

Cart is pure in-memory React state. It persists across tab navigation (same React tree) but resets on app restart.

```typescript
type CartItems = { [productName: string]: number }  // name → quantity
```

**Three operations:**
- `addToCart(name, qty)` — adds qty to existing (default 0). Used by home.tsx, details.tsx, and chatRoom.tsx (from order agent)
- `SetQuantityCart(name, delta)` — increments/decrements, floors at 0. Used by order.tsx product list
- `emptyCart()` — resets to `{}`. Called before repopulating from order agent response

**Cart key = product name string** (not ID). This means "Cappuccino" in the LLM order must exactly match "Cappuccino" in Firebase. Case and spelling must align.

---

## Flow 4 — Details Page

**File:** `app/(tabs)/home.tsx` → `app/details.tsx`

Navigation uses Expo Router's route params — all product data is passed as URL params:

```typescript
router.push({
    pathname: '/details',
    params: { name, image_url, type, price, rating, description }
})
```

`details.tsx` reads params with `useLocalSearchParams()`. No second Firebase fetch. The Buy Now button calls `addToCart(name, 1)` and navigates back.

---

## Flow 5 — Order Checkout

**File:** `app/(tabs)/order.tsx`

```
useEffect (mount)
  → fetchProducts()      // same Firebase call as home.tsx — separate fetch
  → setProducts(data)

useEffect (cartItems or products change)
  → calculateTotal(products, cartItems)
  → products.reduce over cartItems quantities × prices

orderNow()
  → emptyCart()
  → Toast("Order placed!")
  → router.push('/thankyou')
```

The order screen re-fetches products from Firebase to get prices. Prices are not stored in CartContext — only product names and quantities. This means the cart never drifts from Firebase prices.

---

## Message Memory — The State Machine

The `memory` field in each assistant message acts as a mini state machine for the order flow.

```
messages = [
  { role: "user", content: "I want a latte" },
  { role: "assistant", content: "Sure! ...", memory: {
      agent: "order_taking_agent",
      "step number": "2",
      order: [{ item: "Latte", quantity: 1, price: 4.75 }],
      asked_recommendation_before: false
  }},
  { role: "user", content: "Also a croissant" },
  ...
]
```

When `OrderTakingAgent` runs, it walks backwards through `messages` to find the last message where `memory.agent == "order_taking_agent"`. That message's `step number` and `order` are prepended to the current user message as context before the LLM call.

**Why this design works:** The LLM sees the current order state as text in the user turn, so it can correctly accumulate items across multiple turns without any server-side session.

**Why it's fragile:** If the user switches from ordering to asking a details question and back, the `order_taking_agent` memory is still in history and will be correctly recovered. But if `messages` is not sent in full (e.g., a frontend bug that only sends the last message), the order state is lost.

---

## LLM Call Parameters (all agents)

```python
client.chat.completions.create(
    model    = model_name,      # from env
    messages = input_messages,  # system + last 3 messages (stripped of memory)
    temperature = 0,            # deterministic
    top_p       = 0.8,
    max_tokens  = 2000,
)
```

`temperature=0` makes agents deterministic — the same input always routes the same way. Good for guard and classification agents. May make recommendation responses feel repetitive over time.

**Only last 3 messages** are sent to guard and classification agents. Specialist agents (order, details, recommendation) receive the full history. This is a context-window optimization — guard/classification don't need full history, they only need recent intent.
