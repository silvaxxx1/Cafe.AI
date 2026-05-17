# ☕ Fero Cafe — AI-Powered Coffee Shop Chatbot

> **Open source.** A full-stack conversational commerce app built to explore multi-agent LLM pipelines in a real-world setting. A customer types naturally — *"I want a latte and a croissant"* — and a pipeline of specialized agents handles intent classification, menu validation, personalized recommendations, and order state across the conversation. The result is a cross-platform mobile app backed by a fully async Python API with SSE streaming, SQLite session persistence, 120 passing tests, LLM evals, and a live observability dashboard.

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![React Native](https://img.shields.io/badge/React%20Native-Expo-blue.svg)](https://expo.dev)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3-orange.svg)](https://groq.com)
[![Tests](https://img.shields.io/badge/tests-160%20passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Open Source](https://img.shields.io/badge/open%20source-yes-brightgreen.svg)]()

---

## 📹 Demo

![Fero Cafe Demo](fero_demo.gif)

*End-to-end walkthrough: multi-item ordering, guard agent, RAG-powered Q&A, and cart auto-population from chat*

---

## 📊 Observability Dashboard

![Observability Dashboard](images/metrics_dashboard.png)

*Live dashboard at `http://localhost:8000/dashboard` — request latency, token usage, agent distribution, and guard block rate. Auto-refreshes every 5s.*

---

## ✨ Features

| Feature | What it does |
|---------|--------------|
| 🧠 **Multi-agent pipeline** | Guard → Classification → Details / Order / Recommendation |
| 🔍 **RAG (Retrieval-Augmented Generation)** | Answers menu & shop questions via ChromaDB (local, no API key) |
| 📝 **Smart ordering** | Multi-turn conversation with menu validation and persistent state |
| 🎯 **Personalized recommendations** | Apriori market basket analysis + popularity rankings |
| 📱 **React Native app** | Browse menu, chat, review cart — one unified flow |
| ⚡ **SSE streaming** | Responses stream token-by-token via `POST /chat/stream`; first token at ~1s |
| 💾 **Session persistence** | SQLite-backed sessions; conversation restores on reload; "New chat" to reset |
| 🔄 **Provider-agnostic LLM** | Swap Groq, RunPod, or OpenAI with a single `.env` change |
| ✅ **160 passing tests** | 126 backend (pytest) + 34 frontend (Jest) — no API key needed for unit tests |
| 🔍 **Live search** | Filter menu by name in real time, combined with category chips |
| 📐 **Size selection** | S / M / L adjusts price live on the detail screen; size-adjusted totals in cart |
| 🖼️ **Products in chat** | Image cards appear below recommendation and order-confirmation bubbles |
| 🛒 **Smart cart merge** | Chat orders merge with browse-screen adds — no more cart-wipe on agent response |
| 📊 **Observability dashboard** | Live `/dashboard` — latency, tokens, routing, guard block rate |
| 🧪 **LLM evals** | Guard, classification, recommendation accuracy tested against real LLM |
| 🖼️ **Bundled product images** | Served from local assets — no Firebase Storage required |

---

## 🏗️ Architecture

```
React Native App (Expo)
        │
        │  POST /chat/stream  { messages, session_id }  (SSE)
        ▼
   FastAPI Server  (local_server.py)  ← fully async
        │
        ▼
   AgentController
        │
        ├── GuardAgent           → blocks off-topic / harmful queries
        │
        ├── ClassificationAgent  → routes intent
        │
        └── DetailsAgent         → RAG: sentence-transformers → ChromaDB (local) → LLM
            OrderTakingAgent     → multi-turn order + auto-upsell
            RecommendationAgent  → Apriori / popularity rankings
                │
                ▼
           Groq API  (llama-3.3-70b-versatile)
```

> 💡 **Design note:** Every agent uses `AsyncOpenAI` with a configurable `base_url` — no vendor lock-in. Invalid routing returns a graceful error rather than crashing the pipeline.

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **LLM** | Groq API (`llama-3.3-70b`) | Free tier, fast inference |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Runs locally, no API cost |
| **Vector DB** | ChromaDB | Local persistent index — no API key, no account |
| **Backend** | Python 3.12 + FastAPI | Async, type-safe |
| **Frontend** | React Native + Expo Router | Cross-platform, hot reload |
| **Styling** | NativeWind (Tailwind) | Utility-first, rapid UI |
| **Recommendations** | scikit-learn (Apriori) | Market basket analysis |
| **Testing** | pytest + jest-expo | 126 backend + 34 frontend, no API key needed for unit tests |
| **Observability** | structlog + Chart.js dashboard | Structured logs + live `/dashboard` |
| **Product catalog** | Firebase Realtime DB | Live product data |
| **Product images** | Bundled local assets | No Firebase Storage required |

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required
Python 3.12+
Node.js 18+

# Recommended
uv  # fast Python package manager

# Free accounts needed
Groq API key  →  https://console.groq.com
```

### 1. Backend Setup

```bash
# Clone and enter repo
git clone https://github.com/silvaxxx1/Cafe.AI.git
cd Cafe.AI

# Create virtual environment
uv venv .venv --python 3.12
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
cd python_code/api
uv pip install -r requirements.txt

# Pin httpx — newer versions break the openai async client
uv pip install "httpx==0.27.2"

# Configure environment
cp .env_example .env
```

Edit `.env` with your credentials:

```ini
# Note: these variable names reflect RunPod origins — they work equally for Groq
RUNPOD_TOKEN=your-groq-api-key-here
RUNPOD_CHATBOT_URL=https://api.groq.com/openai/v1
MODEL_NAME=llama-3.3-70b-versatile
```

Start the server:

```bash
python local_server.py
# ✅ Agents ready.
# 🚀 Uvicorn running on http://0.0.0.0:8000
```

### 2. Frontend Setup

```bash
# Open a new terminal
cd coffee_shop_app

# Copy config and fill in Firebase + backend URL
cp .env_example.txt .env

# Install and run
npm install
npm run web    # Opens at http://localhost:8081
```

### 3. Verify the Integration

```bash
# Streaming endpoint (what the app uses)
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "I want a latte and a croissant"}]}}'
```

**Expected:** SSE token stream ending with `{"type":"done","memory":{"order":[...]}}` — both items captured with correct prices. 🎯

---

## 🧪 Testing

```bash
# Backend unit tests (no API key needed)
make test          # 126 pytest tests

# Frontend unit tests
make test-frontend # 34 Jest tests (CartContext, MessageItem, SizesSection, productService)

# Both suites in sequence
make test-all

# LLM evals (requires valid Groq key in .env)
make evals
```

**126 backend tests** cover all agents, the server (streaming and session endpoints), and eval runner logic. All LLM calls are mocked with `AsyncMock` — no API key needed.

**34 frontend tests** cover CartContext (13), MessageItem (12), SizesSection (8), and productService (4).

Evals hit the real LLM and report per-case PASS/FAIL with a pass rate. Exit 1 if below 80%.

---

## 💬 Example Prompts

| You say… | Agent handles it |
|----------|-----------------|
| *"Who won the World Cup?"* | 🛡️ Guard blocks |
| *"What are your opening hours?"* | 📚 Details (RAG) |
| *"Tell me about Fero Cafe"* | 📚 Details (RAG) |
| *"What do you recommend?"* | 🎯 Recommendation |
| *"What pastry should I get?"* | 🎯 Recommendation (category-filtered) |
| *"I want a latte and a croissant"* | 📝 Order — 2 items captured |
| *"Also add an espresso"* | 📝 Order — context remembered |
| *"No thanks, that's all"* | 📝 Order — finalised with total |

---

## 🔧 Advanced Setup

### ChromaDB (RAG Q&A)

No account or API key needed — the index lives on disk.

```bash
# 1. Build the index (runs locally, ~30 seconds)
cd coffee_shop_customer_service_chatbot/python_code
python build_index.py
# → Writes index to api/chroma_db/

# 2. Restart the backend
# → [DetailsAgent] RAG enabled — local embeddings + ChromaDB.
```

Uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings locally. Without the index, `DetailsAgent` is gracefully disabled and the rest of the app functions normally.

### Firebase (live product catalog)

Firebase is pre-configured for the `fero-ai` project. To use your own:

```bash
# 1. Create a project at console.firebase.google.com
# 2. Enable Realtime Database (Spark / free plan — Storage NOT required)
# 3. Download service account JSON from Project Settings → Service Accounts
# 4. Fill python_code/.env with service account fields
# 5. Seed products (images are local, no upload needed):
cd python_code
jupyter notebook firebase_uploader.ipynb

# 6. Add Firebase web config to coffee_shop_app/.env
```

Product images are bundled in `coffee_shop_app/assets/images/products/` and mapped by filename in `constants/productImages.ts`. Firebase stores only the filename (e.g. `cappuccino.jpg`), not a remote URL.

> Without Firebase, the home tab shows an empty menu — but the chat tab works fully. The agent validates orders against `menu.json`, which is always loaded server-side.

### Running on a Physical Device

1. Install [Expo Go](https://expo.dev/go) on your phone
2. Ensure your phone and computer are on the same Wi-Fi network
3. Update `coffee_shop_app/.env`:
   ```env
   EXPO_PUBLIC_RUNPOD_API_URL='http://192.168.x.x:8000/chat'  # your local IP
   ```
4. Run and scan the QR code:
   ```bash
   npm start
   ```

---

## 🚢 Production Deployment (RunPod)

```bash
cd python_code/api
docker build -t your-dockerhub/fero-cafe:latest .
docker push your-dockerhub/fero-cafe:latest
```

1. Create a RunPod serverless endpoint with the image
2. Set env vars from `.env_example`
3. Update `EXPO_PUBLIC_RUNPOD_API_URL` in the frontend to your RunPod endpoint

---

## 📁 Project Structure

```
Cafe.AI/
├── 📱 coffee_shop_app/              # React Native (Expo)
│   ├── app/
│   │   ├── _layout.tsx            # Root layout: providers + web frame
│   │   ├── index.tsx              # Splash / landing screen
│   │   ├── details.tsx            # Product detail
│   │   ├── thankyou.tsx           # Order confirmation
│   │   └── (tabs)/
│   │       ├── _layout.tsx        # Tab bar with cart badge
│   │       ├── home.tsx           # Menu browse + category filter
│   │       ├── chatRoom.tsx       # AI chat → auto-fills cart
│   │       └── order.tsx          # Cart review + checkout
│   ├── components/                # CartContext, MessageList, UI components
│   ├── constants/
│   │   ├── theme.ts               # Light/dark token system + useTheme()
│   │   ├── responsive.ts          # useGridColumns(), webPointer utils
│   │   └── productImages.ts       # filename → require() map
│   ├── services/                  # chatBot.ts, productService.ts (cached)
│   ├── assets/images/products/    # Bundled product images (18 items)
│   ├── polyfills.ts               # setImmediate shim for web
│   └── config/                    # Firebase config
│
└── 🐍 python_code/
    ├── api/
    │   ├── agents/
    │   │   ├── guard_agent.py
    │   │   ├── classification_agent.py
    │   │   ├── details_agent.py
    │   │   ├── order_taking_agent.py
    │   │   ├── recommendation_agent.py
    │   │   ├── agent_protocol.py     # async Protocol
    │   │   └── utils.py
    │   ├── tests/                 # 126 tests ✅ (unit + eval runners)
    │   ├── recommendation_objects/
    │   ├── local_server.py        # Dev server (async FastAPI)
    │   ├── main.py                # RunPod entry point
    │   ├── agent_controller.py    # Pipeline orchestration
    │   ├── session.py             # SQLite session store
    │   └── menu.json              # Single source of truth for product names
    ├── products/
    │   ├── products.jsonl         # Full product data (seeded to Firebase)
    │   └── images/                # Source images
    ├── firebase_uploader.ipynb    # Seeds Firebase (no Storage needed)
    ├── build_vector_database.ipynb
    └── recommendation_engine_training.ipynb
```

---

## 🔐 Environment Variables

### Backend (`python_code/api/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `RUNPOD_TOKEN` | ✅ Yes | Your Groq API key (legacy name — works for any provider) |
| `RUNPOD_CHATBOT_URL` | ✅ Yes | `https://api.groq.com/openai/v1` |
| `MODEL_NAME` | ✅ Yes | `llama-3.3-70b-versatile` |
| `CHROMA_DB_PATH` | ❌ Optional | Path to ChromaDB index (default: `api/chroma_db/`). Run `build_index.py` once to create it. |

### Firebase Seeding (`python_code/.env`)

| Variable | Description |
|----------|-------------|
| `FIREBASE_*` | Service account fields from Firebase console |
| `FIREBASE_DATABASE_URL` | Realtime Database URL |

### Frontend (`coffee_shop_app/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `EXPO_PUBLIC_RUNPOD_API_URL` | ✅ Yes | Backend URL (e.g. `http://localhost:8000/chat`) |
| `EXPO_PUBLIC_FIREBASE_API_KEY` | ✅ Yes | Firebase web API key |
| `EXPO_PUBLIC_FIREBASE_DATABASE_URL` | ✅ Yes | Realtime Database URL |
| `EXPO_PUBLIC_FIREBASE_*` | ✅ Yes | Remaining Firebase web config fields |

---

## 🗺️ Roadmap

**V1 — Complete ✅**
- [x] Multi-agent pipeline — Guard → Classification → Details / Order / Recommendation
- [x] Fully async FastAPI + all agents
- [x] SSE streaming — `POST /chat/stream`; first token at ~1s
- [x] SQLite session persistence — restores conversation on reload
- [x] Dynamic menu — `menu.json` single source of truth, injected at startup
- [x] Observability — structlog structured logging + live `/dashboard`
- [x] LLM evals — guard, classification, recommendation runners (80% threshold)
- [x] 120 passing tests — unit + eval runners, no API key needed for unit tests
- [x] Production hardening — rate limiting, CORS, startup validation, typed input
- [x] CI/CD — GitHub Actions on every push

**V2 — Complete ✅**
- [x] Live search — filters menu by name in real time, combined with category chips
- [x] Size selection — S/M/L adjusts price live; size-adjusted totals flow through cart
- [x] Product images in chat — cards below recommendation and final-order bubbles, tappable to detail
- [x] Fix cart-wipe bug — `syncCartFromOrder` merges LLM orders without wiping browse-screen adds
- [x] RecommendationAgent turn memory — `last_recommendations` stored; repeats avoided next turn
- [x] Wider context window — `CONTEXT_WINDOW=6` across guard, classification, recommendation
- [x] Response variation — `temperature=0.7` on recommendation language calls
- [x] Full TypeScript types — `AgentMemory` union replacing `memory?: any` everywhere
- [x] Frontend tests — CartContext (13), MessageItem (12), SizesSection (8), productService (4)
- [x] `make test-all` — runs backend + frontend suites in sequence
- [x] RAG — ChromaDB local index (no API key); `build_index.py` populates `api/chroma_db/` in ~30s

**V3 — Possible Next Steps**
- [ ] Cart → agent context — agent awareness of items added via browse screen
- [ ] Product images on menu/details agent responses
- [ ] Multi-tenant deployment — one backend serving multiple café clients

See [`V2_PLAN.md`](../V2_PLAN.md) for the full breakdown with file references and implementation details.

---

## 📄 License

MIT — free for personal and commercial use.

---

## 🙏 Acknowledgments

- [Groq](https://groq.com) for free, fast LLM inference
- [ChromaDB](https://www.trychroma.com) for local vector storage
- [Expo](https://expo.dev) for React Native tooling
- [Firebase](https://firebase.google.com) for real-time product catalog

---

**Built with ☕ and 🤖 by SilvaLAB**