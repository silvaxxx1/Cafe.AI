# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cafe.AI is a full-stack AI-powered coffee shop chatbot with a React Native mobile frontend and a Python multi-agent backend. The backend runs locally via FastAPI or deployed on RunPod serverless.

## Repository Layout

All source lives under `coffee_shop_customer_service_chatbot/`:
- `coffee_shop_app/` — React Native (Expo) mobile app
- `python_code/api/` — Python multi-agent backend
- `python_code/` (root notebooks) — Data pipeline: seed Firebase, train recommendation models, build ChromaDB index

## Local Dev Setup (free, no RunPod needed)

### 1. Backend

```bash
# Create venv with uv (pip has pkg_resources issues on this system)
uv venv .venv --python 3.12
source .venv/bin/activate

cd coffee_shop_customer_service_chatbot/python_code/api
uv pip install -r requirements.txt

# IMPORTANT: downgrade httpx to avoid openai SDK incompatibility
uv pip install "httpx==0.27.2"

# Copy and fill in env
cp .env_example .env
# → Set RUNPOD_TOKEN to a Groq API key (free at console.groq.com)
# → RUNPOD_CHATBOT_URL=https://api.groq.com/openai/v1
# → MODEL_NAME=llama-3.3-70b-versatile

python local_server.py        # HTTP server on :8000
python development_code.py    # CLI chat for quick testing
```

### 2. Frontend

```bash
cd coffee_shop_customer_service_chatbot/coffee_shop_app
cp .env_example.txt .env
# → Fill in EXPO_PUBLIC_FIREBASE_* and EXPO_PUBLIC_RUNPOD_API_URL
npm install
npm run web      # browser at http://localhost:8081
npm run android  # requires Android emulator or device + Expo Go
```

> **Note:** Use `uv` instead of `pip` — raw pip fails to build `pandas` on Python 3.12 due to a `pkg_resources` issue on this system.

## Known Fixes / Gotchas

- **httpx version:** The `openai` SDK requires `httpx==0.27.2`. Newer versions cause `TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'`. Always pin this after installing requirements.
- **Menu names:** `menu.json` is the single source of truth for product names. `products.jsonl`, `popularity_recommendation.csv`, and Firebase must all use the same names. Do not rename products in one place without updating the others.

## Environment Variables

**Backend** — `python_code/api/.env`:
- `RUNPOD_TOKEN` — Groq API key (local) or RunPod token (production)
- `RUNPOD_CHATBOT_URL` — `https://api.groq.com/openai/v1` (Groq) or RunPod endpoint
- `MODEL_NAME` — `llama-3.3-70b-versatile` (Groq) or `meta-llama/Llama-3.1-8B-Instruct` (RunPod)
- `CHROMA_DB_PATH` — optional; defaults to `api/chroma_db/`. RAG enabled when the directory exists (run `build_index.py` once to populate it). DetailsAgent gracefully disables when absent.

**Backend seeding** — `python_code/.env`:
- All `FIREBASE_*` fields from the Firebase service account JSON
- `FIREBASE_DATABASE_URL` — Realtime Database URL

**Frontend** — `coffee_shop_app/.env`:
- `EXPO_PUBLIC_RUNPOD_API_URL` — backend URL (`http://localhost:8000/chat` locally)
- `EXPO_PUBLIC_FIREBASE_*` — Firebase web app credentials (required for product catalog)

## Firebase Setup (already configured for this project)

The Firebase project `fero-ai` is configured:
- Realtime Database seeded with 18 products from `python_code/products/products.jsonl`
- Product images are bundled locally in `coffee_shop_app/assets/images/products/` — Firebase Storage is NOT used (free Spark plan)
- Image filenames are stored in Firebase as `image_url` and resolved via `coffee_shop_app/constants/productImages.ts`

To re-seed Firebase (e.g. after menu changes):
```bash
cd python_code
../.venv/bin/python -c "exec(open('firebase_uploader_script.py').read())"
# or run firebase_uploader.ipynb
```

## Architecture

### Multi-Agent Pipeline (Backend)

Every user message flows through `agent_controller.py`:

```
User message
  → GuardAgent          (blocks off-topic/harmful queries)
  → ClassificationAgent (routes to: details_agent | order_taking_agent | recommendation_agent)
  → Chosen Agent        (returns JSON with memory object)
```

All agents implement `agent_protocol.py` with an `async get_response(messages)` method. Each message in the shared list may carry a `memory` dict with agent-specific state (order step, items, decisions).

**Agent responsibilities:**
- `guard_agent.py` — Safety filter; returns `allowed`/`not allowed`
- `classification_agent.py` — Intent detection; picks which agent handles the turn
- `details_agent.py` — RAG: embed query locally (sentence-transformers) → ChromaDB (local disk) → LLM answer. **Gracefully disabled** when `api/chroma_db/` directory is absent (run `build_index.py` once)
- `order_taking_agent.py` — Multi-turn order collection, menu validation, triggers recommendation upsell automatically before closing
- `recommendation_agent.py` — Apriori (market basket) or popularity rankings, loaded from static files at startup

`utils.py` wraps all OpenAI SDK calls; agents never import the SDK directly. All structured-output agents use `json_mode=True` to guarantee valid JSON. All `json.loads()` calls have `try/except` fallbacks as a safety net. Every LLM call is timed and logged via `structlog` (latency_ms, input/output tokens).

`agent_controller.py` uses `.get()` on the agent dict (not direct key access) — invalid agent names return a graceful error instead of crashing. Accepts an optional `MetricsStore` for observability — logs guard decisions and agent routing on every request.

`metrics.py` — in-memory `MetricsStore` (thread-safe deque, 500 records). Records per-request: latency, guard decision, chosen agent, token counts. Served at `/metrics` and visualised at `/dashboard`.

### Local HTTP Server (`local_server.py`)

FastAPI wrapper (fully async) that mirrors the RunPod response format so the frontend works unchanged:
- `POST /chat` — `{ input: { messages }, session_id? }` → `{ output: { role, content, memory } }`
- `POST /chat/stream` — same body → SSE stream of `{"type":"token","delta":"..."}` events, terminated by `{"type":"done","memory":{...}}`
- `GET /session/{id}` — returns `{ messages: [...] }` to restore prior conversation on reload
- `DELETE /session/{id}` — clears a session (frontend "New chat" button)
- `GET /` — health check
- `GET /metrics` — JSON metrics snapshot (latency, tokens, agent distribution, guard block rate)
- `GET /dashboard` — live Chart.js observability dashboard, auto-refreshes every 5s

Session persistence (`session.py`): SQLite-backed `SessionStore`. Every turn saves the full messages list keyed by `session_id`. Frontend generates a UUID `session_id` stored in `localStorage` (falls back to `"default"` on native). `sse-starlette>=1.8.0,<3.0.0` and `starlette==0.38.6` are pinned — sse-starlette 3.x pulls starlette 1.0.0 which breaks FastAPI 0.115.0.

Production hardening:
- CORS locked to `localhost:8081`, `localhost:19006`, `127.0.0.1:8081`
- Rate limited to 20 req/min per IP via `slowapi`
- Startup exits with a clear error if `RUNPOD_TOKEN`, `RUNPOD_CHATBOT_URL`, or `MODEL_NAME` are missing
- `messages` typed as `list[Message]` — invalid payloads return 422 before reaching agents

### Frontend (React Native / Expo Router)

File-based routing under `app/`:
- `(tabs)/home.tsx` — menu browse, category + live search filter, add to cart
- `(tabs)/chatRoom.tsx` — chat UI; streams via `POST /chat/stream`; loads prior session on mount; syncs cart via `syncCartFromOrder` (preserves manually-added items); shows product image cards below recommendation and final-order bubbles; "New chat" button clears session
- `(tabs)/order.tsx` — cart review and checkout; uses `cartPrices` for size-adjusted totals
- `details.tsx` — product detail; S/M/L size selection adjusts price live via `SIZE_MODIFIERS`

`constants/productImages.ts` maps image filenames (stored in Firebase) to local `require()` bundled assets — no remote image URLs needed.

`config/firebaseConfig.ts` initializes Firebase only when `EXPO_PUBLIC_FIREBASE_DATABASE_URL` is set — app renders without it. `services/productService.ts` returns an empty list when Firebase is not configured.

### Data Flow: Chat → Cart Update

```
User sends message (chatRoom.tsx)
  → POST to /chat/stream (SSE) with full message history + session_id
  → agent pipeline: Guard → Classification → Agent
  → returns { role, content, memory: { agent, order, ... } }
  → UI appends message
  → if memory.order exists → CartContext.syncCartFromOrder()
  → if recommendation or final order → MessageItem renders product image cards
```

### Production Deployment

`main.py` is the RunPod serverless handler entry point — for production only. `local_server.py` is local dev only.

Docker build for RunPod:
```bash
cd python_code/api
docker build -t chatbot:latest .
```

## Key Patterns

- **Path alias:** `@/*` maps to the project root in `tsconfig.json`
- **Styling:** NativeWind (Tailwind) via `className` props
- **LLM provider swap:** All agents use the OpenAI SDK with a configurable `base_url` — switching between Groq, RunPod, or any OpenAI-compatible API is a `.env` change only
- **Recommendation models:** Static JSON/CSV files loaded once at startup in `recommendation_agent.py` — not retrained at runtime
- **Images:** Bundled locally in `assets/images/products/`, mapped by filename in `constants/productImages.ts`

## Design Context

### Users

Young urban professionals, 20–35, using the app during commutes and work breaks. Sessions are short and intentional — they know what they want (or want a smart recommendation, fast). They're digitally native, visually literate, and will notice if something looks generic. The AI chat is a convenience they actually want to use, like texting their regular barista.

**Job to be done**: Get great coffee, fast. Discover something new. Feel like the app knows them.

### Brand Personality

**Three words: quick, warm, clever.**

The interface should feel like a barista friend who remembers your order and occasionally surprises you. Conversational, a little cheeky, never corporate. The AI chat is the soul of the app — it should feel alive.

### Aesthetic Direction

**Direction: "Playful editorial with craft energy"**

Think of an independent coffee shop that stocks obscure design magazines and has a hand-lettered daily specials board. The menu feels curated, not catalogued. The chat feels like a conversation, not a support ticket. Layouts are unexpected — asymmetric, editorial — but the warmth is real.

**Palette**: Both light and dark mode (system toggle). Light: warm cream base, deep espresso ink, terracotta accents (built on existing #C67C4E). Dark: rich dark-roast backgrounds (not pure black), same terracotta accent. Neutrals tinted warm throughout. No cyan, no purple gradients.

**Anti-references**: Generic food delivery apps, dark coffee-brand hero layouts, rounded pastel "friendly AI" interfaces.

### Design Principles

1. **Quick but savored** — Fast interactions, but every screen has something worth noticing.
2. **The chat is the product** — The AI conversation is the core differentiator; design should celebrate it.
3. **Warmth without cliché** — No burlap, bean illustrations, or wood textures. Warmth comes from color temperature and typography.
4. **Surprise in the details** — Unexpected layouts, type choices, and micro-interactions are how this gets remembered.
5. **One palette, two moods** — Light and dark feel like the same brand in different lighting conditions.
