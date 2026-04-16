# ☕ Fero Cafe — AI-Powered Coffee Shop Chatbot

> **Chat with AI, order naturally, get personalized recommendations** — a complete conversational commerce experience.

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![React Native](https://img.shields.io/badge/React%20Native-Expo-blue.svg)](https://expo.dev)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3-orange.svg)](https://groq.com)
[![Tests](https://img.shields.io/badge/tests-102%20passing-brightgreen.svg)]()

---

## 📹 Demo

![Fero Cafe Demo Animation](demo.gif)

*Complete walkthrough of the AI chatbot - ordering, recommendations, and cart integration*

**What you'll see in action:**
- 🛡️ Guard agent blocking off-topic questions
- 📚 RAG-powered shop info (hours, location, menu)
- 🛒 Multi-item order: *"I want a latte, croissant, and espresso"* → all 3 captured
- 💡 Automatic upsell recommendation after first order
- ✅ Order finalization with correct total
- 🔄 Cart auto-populated from chat

---

## ✨ Features at a Glance

| Feature | What it does |
|---------|---------------|
| 🧠 **Multi-agent pipeline** | Guard → Classification → Details/Order/Recommendation |
| 🔍 **RAG (Retrieval-Augmented Generation)** | Answers menu & shop questions using Pinecone vector DB |
| 📝 **Smart ordering** | Multi-turn conversation, menu validation, remembers state |
| 🎯 **Personalized recommendations** | Apriori market basket analysis + popularity rankings |
| 📱 **React Native app** | Browse menu, chat, review cart — one unified flow |
| 🔄 **Provider-agnostic LLM** | Swap Groq, RunPod, OpenAI in one `.env` change |
| ✅ **102 passing tests** | Full async test suite with mocked LLM calls |
| 🖼️ **Local product images** | Bundled in app assets — no Firebase Storage needed |

---

## 🏗️ Architecture

```
React Native App (Expo)
        │
        │  POST /chat  { messages: [...] }
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
        └── DetailsAgent         → RAG: sentence-transformers → Pinecone → LLM
            OrderTakingAgent     → multi-turn order + auto-upsell
            RecommendationAgent  → Apriori / popularity rankings
                │
                ▼
           Groq API  (llama-3.3-70b-versatile)
```

### How it works:

1. **Guard Agent** → Blocks off-topic / harmful queries
2. **Classification Agent** → Routes intent (order, question, recommendation)
3. **Specialized Agents** → Handle specific tasks with RAG or business logic
4. **Groq API** → Powers all LLM calls with `llama-3.3-70b-versatile`

> 💡 **Design philosophy:** Every agent uses `AsyncOpenAI` with configurable `base_url` — no vendor lock-in. Invalid agent routing returns a graceful error instead of crashing.

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **LLM** | Groq API (`llama-3.3-70b`) | Free tier, blazing fast |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Runs locally, no API cost |
| **Vector DB** | Pinecone | Free serverless index (optional) |
| **Backend** | Python 3.12 + FastAPI | Async, type-safe, fast |
| **Frontend** | React Native + Expo Router | Cross-platform, hot reload |
| **Styling** | NativeWind (Tailwind) | Utility-first, rapid UI |
| **Recommendations** | scikit-learn (Apriori) | Market basket analysis |
| **Testing** | pytest + AsyncMock | 102 tests, no API key needed |
| **Product catalog** | Firebase Realtime DB | Live product data |
| **Product images** | Bundled local assets | No Firebase Storage required |

---

## 🚀 Quick Start (5 minutes)

### Prerequisites

```bash
# Required
Python 3.12+
Node.js 18+

# Recommended
uv (fast Python package manager)
Git

# Free account needed
Groq API key → https://console.groq.com
```

### 1. Backend Setup

```bash
# Clone and enter repo
git clone https://github.com/silvaxxx1/Cafe.AI.git
cd Cafe.AI/coffee_shop_customer_service_chatbot

# Create virtual environment
uv venv .venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
cd python_code/api
uv pip install -r requirements.txt

# Fix httpx version (required — newer versions break openai SDK)
uv pip install "httpx==0.27.2"

# Configure environment
cp .env_example .env
```

**Edit `.env` with your keys:**
```ini
RUNPOD_TOKEN=your-groq-api-key-here
RUNPOD_CHATBOT_URL=https://api.groq.com/openai/v1
MODEL_NAME=llama-3.3-70b-versatile
```

**Start the server:**
```bash
python local_server.py
# ✅ Agents ready.
# 🚀 Uvicorn running on http://0.0.0.0:8000
```

### 2. Frontend Setup

```bash
# Open new terminal, go to frontend
cd coffee_shop_customer_service_chatbot/coffee_shop_app

# Copy config and fill in Firebase + backend URL
cp .env_example.txt .env

# Install and run
npm install
npm run web  # Opens at http://localhost:8081
```

### 3. Test It's Working

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "I want a latte and a croissant"}]}}'
```

**Expected output:** Both items captured with correct prices 🎯

---

## 🧪 Testing

```bash
cd coffee_shop_customer_service_chatbot/python_code/api
python -m pytest tests/ -v
```

```
============================= test session starts =============================
collected 102 items

tests/test_agent_controller.py .........                                 [ 8%]
tests/test_classification_agent.py ............                          [19%]
tests/test_guard_agent.py ..............................                  [48%]
tests/test_order_taking_agent.py ......................                   [69%]
tests/test_recommendation_agent.py ...................                    [88%]
tests/test_server.py ..........                                          [97%]

============================= 102 passed ==============================
```

> 💡 **No API key needed** — tests use `AsyncMock` to mock all LLM calls.

---

## 🔧 Advanced Setup

### Pinecone (for RAG Q&A)

```bash
# 1. Create free account at pinecone.io
# 2. Add to python_code/api/.env:
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=coffeeshop

# 3. Build index (runs locally, no API cost)
cd coffee_shop_customer_service_chatbot/python_code
jupyter notebook build_vector_database.ipynb
```

The index uses `sentence-transformers/all-MiniLM-L6-v2` — all local, no API calls.  
Without Pinecone, `DetailsAgent` is gracefully disabled and the app still works.

### Firebase (live product catalog)

Firebase is already configured in this project (`fero-ai`). To set up your own:

```bash
# 1. Create project at console.firebase.google.com
# 2. Enable Realtime Database (Spark/free plan is enough — Storage NOT required)
# 3. Get service account JSON from Project Settings → Service Accounts
# 4. Fill python_code/.env with service account fields
# 5. Seed products (images are local, no upload needed):
cd python_code
jupyter notebook firebase_uploader.ipynb

# 6. Add Firebase web config to coffee_shop_app/.env
```

Product images are **bundled locally** in `coffee_shop_app/assets/images/products/` and mapped by filename in `constants/productImages.ts`. Firebase stores only the filename (e.g. `cappuccino.jpg`), not a remote URL.

> **Note:** Without Firebase, the home tab shows an empty menu, but the chat tab works fully — the agent validates orders against `menu.json` which is always loaded server-side.

---

## 📱 Run on Physical Phone

1. Install [Expo Go](https://expo.dev/go) on your phone
2. Make sure phone and computer are on same Wi-Fi
3. Update `coffee_shop_app/.env`:
   ```env
   EXPO_PUBLIC_RUNPOD_API_URL='http://192.168.x.x:8000/chat'  # Use your local IP
   ```
4. Run and scan:
   ```bash
   npm start
   # Scan QR code with Expo Go
   ```

---

## 🚢 Production Deployment (RunPod)

```bash
cd coffee_shop_customer_service_chatbot/python_code/api

docker build -t your-dockerhub/fero-cafe:latest .
docker push your-dockerhub/fero-cafe:latest
```

1. Create RunPod serverless endpoint with the image
2. Set env vars from `.env_example`
3. Update frontend `EXPO_PUBLIC_RUNPOD_API_URL` to RunPod endpoint

---

## 💬 Try These Prompts

| You say... | Agent handles it |
|------------|------------------|
| *"Who won the World Cup?"* | 🛡️ Guard blocks |
| *"What are your opening hours?"* | 📚 Details (RAG) |
| *"Tell me about Fero Cafe"* | 📚 Details (RAG) |
| *"What do you recommend?"* | 🎯 Recommendation |
| *"What pastry should I get?"* | 🎯 Recommendation (category) |
| *"I want a latte and a croissant"* | 📝 Order — 2 items captured |
| *"Also add an espresso"* | 📝 Order — remembers context |
| *"No thanks, that's all"* | 📝 Order — finalizes with total |

---

## 📁 Project Structure

```
coffee_shop_customer_service_chatbot/
├── 📱 coffee_shop_app/              # React Native (Expo)
│   ├── app/
│   │   ├── (tabs)/
│   │   │   ├── home.tsx          # Menu + cart
│   │   │   ├── chatRoom.tsx      # Chat UI → auto-fills cart
│   │   │   └── order.tsx         # Checkout
│   │   └── details.tsx           # Product detail
│   ├── assets/images/products/   # Bundled product images (18 items)
│   ├── components/               # CartContext, UI components
│   ├── constants/
│   │   └── productImages.ts      # filename → require() map
│   ├── services/                 # chatBot.ts, productService.ts
│   └── config/                   # Firebase config
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
    │   ├── tests/                # 102 tests ✅
    │   ├── recommendation_objects/
    │   ├── local_server.py       # Dev server (async FastAPI)
    │   ├── main.py               # RunPod entry point
    │   ├── agent_controller.py   # Pipeline orchestration
    │   └── menu.json             # Single source of truth for product names
    ├── products/
    │   ├── products.jsonl        # Full product data (seeded to Firebase)
    │   └── images/               # Source images
    ├── firebase_uploader.ipynb   # Seeds Firebase (no Storage needed)
    ├── build_vector_database.ipynb
    └── recommendation_engine_training.ipynb
```

---

## 🔐 Environment Variables

### Backend (`python_code/api/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `RUNPOD_TOKEN` | ✅ Yes | Groq API key |
| `RUNPOD_CHATBOT_URL` | ✅ Yes | `https://api.groq.com/openai/v1` |
| `MODEL_NAME` | ✅ Yes | `llama-3.3-70b-versatile` |
| `PINECONE_API_KEY` | ❌ No | Enables RAG in DetailsAgent |
| `PINECONE_INDEX_NAME` | ❌ No | Pinecone index name |

### Firebase Seeding (`python_code/.env`)

| Variable | Description |
|----------|-------------|
| `FIREBASE_*` | Service account fields from Firebase console |
| `FIREBASE_DATABASE_URL` | Realtime Database URL |

### Frontend (`coffee_shop_app/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `EXPO_PUBLIC_RUNPOD_API_URL` | ✅ Yes | Backend URL (`http://localhost:8000/chat`) |
| `EXPO_PUBLIC_FIREBASE_API_KEY` | ✅ Yes | Firebase web API key |
| `EXPO_PUBLIC_FIREBASE_DATABASE_URL` | ✅ Yes | Realtime Database URL |
| `EXPO_PUBLIC_FIREBASE_*` | ✅ Yes | Remaining Firebase web config fields |

---

## ⚠️ Known Issues / Notes

- **httpx version:** Pin `httpx==0.27.2` — newer versions break the `openai` async client
- **Menu names:** `menu.json` is the authority. If you rename a product, update `products.jsonl` and re-seed Firebase
- **No streaming yet:** Responses are full round-trip — streaming is the next planned feature
- **Session memory:** Conversation state lives in the frontend's React state only — lost on page refresh

---

## 📄 License

MIT — free for personal and commercial use.

---

## 🙏 Acknowledgments

- [Groq](https://groq.com) for free LLM access
- [Pinecone](https://pinecone.io) for vector database
- [Expo](https://expo.dev) for React Native tooling
- [Firebase](https://firebase.google.com) for real-time product catalog

---

**Built with ☕ and 🤖 by SilvaLAB**
