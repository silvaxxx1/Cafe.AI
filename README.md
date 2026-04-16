# Fero Cafe — AI-Powered Coffee Shop Chatbot

> A full-stack, multi-agent AI assistant for a coffee shop. Customers place orders, ask menu questions, and get personalized recommendations — all through natural conversation.

---

## Demo

<!-- Replace the link below with your actual demo video URL after uploading to YouTube/Loom -->
[![Fero Cafe Demo](https://github.com/silvaxxx1/Cafe.AI/issues/1)](https://github.com/silvaxxx1/Cafe.AI/issues/1)

> **Demo video:** Full-stack AI coffee shop chatbot showing guard agent filtering off-topic queries, RAG-powered retrieval of shop hours and menu details, multi-item order capture from natural conversation, automatic upsell recommendations, order finalization with calculated totals, and cart auto-population from chat interactions. Professional demonstration of conversational AI in action for customer service.

> **What you'll see in the demo:**
> - Guard agent blocking off-topic questions
> - RAG-powered shop info (hours, location, menu details)
> - Multi-item order: "I want a latte, croissant, and espresso" → all 3 captured
> - Automatic upsell recommendation after first order
> - Order finalization with correct total
> - Cart auto-populated from chat

---

## Features

| Feature | Details |
|---|---|
| **Multi-agent pipeline** | Guard → Classification → Details / Order / Recommendation |
| **RAG (Retrieval-Augmented Generation)** | Local sentence-transformers + Pinecone for menu & shop Q&A |
| **Smart ordering** | Multi-turn order collection, menu validation, item state carried across turns |
| **Personalized recommendations** | Apriori market basket analysis + popularity rankings |
| **React Native app** | Browse menu, chat, review cart — one unified flow |
| **Provider-agnostic LLM** | Swap between Groq, RunPod, OpenAI in a single `.env` change |
| **61 passing tests** | Full async test suite with mocked LLM calls |

---

## Architecture

```
React Native App (Expo)
        │
        │  POST /chat  { messages: [...] }
        ▼
   FastAPI Server  (local_server.py)
        │
        ▼
   AgentController
        │
        ├── GuardAgent           → blocks off-topic / harmful queries
        │
        ├── ClassificationAgent  → routes intent
        │
        └── DetailsAgent         → RAG: sentence-transformers → Pinecone → LLM
            OrderTakingAgent     → multi-turn order + auto-upsell
            RecommendationAgent  → Apriori / popularity rankings
                │
                ▼
           Groq API  (llama-3.3-70b-versatile)
```

**Every agent:**
- Uses `AsyncOpenAI` with a configurable `base_url` — no vendor lock-in
- Returns `{ role, content, memory }` — state lives in the message array, no database
- Uses `json_mode=True` for guaranteed valid JSON output

---

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Groq API (`llama-3.3-70b-versatile`) — free tier |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` — runs locally |
| **Vector DB** | Pinecone (free serverless index) |
| **Backend** | Python 3.12, FastAPI, AsyncOpenAI |
| **Frontend** | React Native, Expo Router, NativeWind (Tailwind) |
| **Recommendations** | scikit-learn (Apriori), pandas |
| **Testing** | pytest, pytest-asyncio, AsyncMock |
| **Product catalog** | Firebase Realtime Database (optional) |

---

## Quick Start

### Prerequisites
- Python 3.12, Node.js 18+
- [`uv`](https://github.com/astral-sh/uv) — fast Python package manager
- Free [Groq API key](https://console.groq.com)

### 1. Clone & set up backend

```bash
git clone <repo-url>
cd <repo>

# Create virtual environment
uv venv .venv --python 3.12
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
cd coffee_shop_customer_service_chatbot/python_code/api
uv pip install -r requirements.txt

# Configure environment
cp .env_example .env
```

Edit `.env`:
```env
RUNPOD_TOKEN=<your-groq-api-key>
RUNPOD_CHATBOT_URL=https://api.groq.com/openai/v1
MODEL_NAME=llama-3.3-70b-versatile
```

Start the server:
```bash
python local_server.py
# → Agents ready.
# → Uvicorn running on http://0.0.0.0:8000
```

### 2. Set up frontend

```bash
cd coffee_shop_customer_service_chatbot/coffee_shop_app
cp .env_example.txt .env
# EXPO_PUBLIC_RUNPOD_API_URL is already set to http://localhost:8000/chat

npm install
npm run web       # opens at http://localhost:8081
```

### 3. Quick smoke test

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "I want a latte and a croissant"}]}}' \
  | python3 -m json.tool
```

Expected: `order` contains both items with correct prices.

---

## Test Suite

```bash
cd coffee_shop_customer_service_chatbot/python_code/api
python -m pytest tests/ -v
```

```
61 passed in ~10s
```

Tests cover all 5 agents + controller + server, using `AsyncMock` to mock LLM calls — no API key needed to run tests.

---

## Full Setup (Firebase + Pinecone RAG)

### Pinecone — enable shop Q&A

```bash
# 1. Create a free account at pinecone.io and copy your API key
# 2. Add to python_code/api/.env:
PINECONE_API_KEY=<your-key>
PINECONE_INDEX_NAME=coffeeshop

# 3. Build the index (runs locally, no embedding API needed)
cd coffee_shop_customer_service_chatbot/python_code
python build_index.py
```

The index is built from product descriptions, menu items, and shop info. Embeddings are generated with `sentence-transformers/all-MiniLM-L6-v2` on your machine.

### Firebase — live product catalog

```bash
# 1. Create a free project at console.firebase.google.com
# 2. Enable Realtime Database
# 3. Seed product data:
cd python_code
jupyter notebook firebase_uploader.ipynb

# 4. Add Firebase credentials to coffee_shop_app/.env
```

Without Firebase, the home tab shows an empty menu but the **chat tab works fully**.

---

## Run on a Physical Phone

Install [Expo Go](https://expo.dev/go). Make sure your phone is on the same Wi-Fi:

```bash
# In coffee_shop_app/.env — use your machine's local IP
EXPO_PUBLIC_RUNPOD_API_URL='http://192.168.x.x:8000/chat'

npm start   # scan the QR code with Expo Go
```

---

## Production Deployment (RunPod Serverless)

```bash
cd coffee_shop_customer_service_chatbot/python_code/api

docker build -t your-dockerhub/fero-cafe:latest .
docker push your-dockerhub/fero-cafe:latest
```

1. Create a RunPod serverless endpoint with the image
2. Set env vars from `.env_example`
3. Update `EXPO_PUBLIC_RUNPOD_API_URL` in the frontend to the RunPod endpoint URL

---

## Prompts to Try

| Prompt | Agent |
|---|---|
| `"Who won the World Cup?"` | Guard blocks |
| `"What are your opening hours?"` | Details (RAG) |
| `"Tell me about Fero Cafe"` | Details (RAG) |
| `"What do you recommend?"` | Recommendation |
| `"What pastry should I get?"` | Recommendation by category |
| `"I want a latte and a croissant"` | Order — 2 items captured |
| `"Also add an espresso"` | Order — state carry-forward |
| `"No thanks, that's all"` | Order — finalize with total |

---

## Project Structure

```
coffee_shop_customer_service_chatbot/
├── coffee_shop_app/              # React Native (Expo) frontend
│   ├── app/
│   │   ├── (tabs)/
│   │   │   ├── home.tsx          # Menu browse + cart
│   │   │   ├── chatRoom.tsx      # Chat UI → auto-fills cart
│   │   │   └── order.tsx         # Cart review + checkout
│   │   └── details.tsx           # Product detail screen
│   ├── components/               # CartContext, UI components
│   ├── services/                 # chatBot.ts, productService.ts
│   └── config/                   # Firebase + API config
└── python_code/
    ├── api/
    │   ├── agents/
    │   │   ├── guard_agent.py
    │   │   ├── classification_agent.py
    │   │   ├── details_agent.py
    │   │   ├── order_taking_agent.py
    │   │   ├── recommendation_agent.py
    │   │   └── utils.py
    │   ├── tests/                # 61 passing tests
    │   ├── local_server.py       # FastAPI dev server
    │   ├── main.py               # RunPod production entry point
    │   ├── agent_controller.py   # Pipeline orchestration
    │   └── menu.json             # Single source of truth for menu
    ├── build_index.py            # Build Pinecone RAG index
    ├── build_vector_database.ipynb
    ├── firebase_uploader.ipynb
    └── recommendation_engine_training.ipynb
```

---

## Environment Variables

### Backend (`python_code/api/.env`)

| Variable | Required | Description |
|---|---|---|
| `RUNPOD_TOKEN` | Yes | Groq API key (local) or RunPod token (production) |
| `RUNPOD_CHATBOT_URL` | Yes | `https://api.groq.com/openai/v1` for Groq |
| `MODEL_NAME` | Yes | `llama-3.3-70b-versatile` (Groq) |
| `PINECONE_API_KEY` | No | Enables RAG — embeddings are generated locally |
| `PINECONE_INDEX_NAME` | No | Name of your Pinecone index (e.g. `coffeeshop`) |

### Frontend (`coffee_shop_app/.env`)

| Variable | Required | Description |
|---|---|---|
| `EXPO_PUBLIC_RUNPOD_API_URL` | Yes | Backend URL (`http://localhost:8000/chat` locally) |
| `EXPO_PUBLIC_FIREBASE_*` | No | Firebase credentials — app works without them |

---

## License

MIT
