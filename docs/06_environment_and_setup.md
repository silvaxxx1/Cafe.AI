# Environment Variables & Local Setup

---

## Backend Environment Variables

**File:** `python_code/api/.env` (copy from `.env_example`)

### Required — LLM Provider

| Variable | Description | Local dev value |
|---|---|---|
| `RUNPOD_TOKEN` | API key for LLM calls | Your Groq API key (free at console.groq.com) |
| `RUNPOD_CHATBOT_URL` | Base URL for LLM (OpenAI-compatible) | `https://api.groq.com/openai/v1` |
| `MODEL_NAME` | Model identifier | `llama-3.3-70b-versatile` |

**Variable naming:** Despite the name `RUNPOD_TOKEN`, this holds the Groq key locally. The naming reflects the production provider (RunPod) — the same variable name works in both modes because all agents use it as `api_key=os.getenv("RUNPOD_TOKEN")`.

### Optional — RAG / Embeddings

| Variable | Description | Effect if unset |
|---|---|---|
| `PINECONE_API_KEY` | Pinecone project API key | DetailsAgent disabled |
| `PINECONE_INDEX_NAME` | Name of your Pinecone index | DetailsAgent disabled |

Embeddings are generated **locally** using `sentence-transformers/all-MiniLM-L6-v2` — no external embedding API needed. Only `PINECONE_API_KEY` is required to enable RAG.

### Production values

| Variable | Production value |
|---|---|
| `RUNPOD_TOKEN` | RunPod API token |
| `RUNPOD_CHATBOT_URL` | `https://api.runpod.ai/v2/<endpoint_id>/openai/v1` |
| `MODEL_NAME` | `meta-llama/Llama-3.1-8B-Instruct` |
| `PINECONE_API_KEY` | Pinecone API key |

---

## Frontend Environment Variables

**File:** `coffee_shop_app/.env` (copy from `.env_example.txt`)

All frontend env vars must be prefixed with `EXPO_PUBLIC_` to be accessible in JavaScript.

### Required — Backend API

| Variable | Description | Local dev value |
|---|---|---|
| `EXPO_PUBLIC_RUNPOD_API_URL` | URL of the `/chat` endpoint | `http://localhost:8000/chat` |
| `EXPO_PUBLIC_RUNPOD_API_KEY` | Bearer token for the API | `'local-dev'` (any string locally) |

**Android emulator note:** `localhost` resolves to the emulator itself, not your dev machine. Use `10.0.2.2:8000` for Android emulator instead of `localhost:8000`.

### Optional — Firebase

| Variable | Description |
|---|---|
| `EXPO_PUBLIC_FIREBASE_API_KEY` | Firebase project API key |
| `EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN` | e.g., `your-project.firebaseapp.com` |
| `EXPO_PUBLIC_FIREBASE_DATABASE_URL` | Realtime DB URL (triggers initialization) |
| `EXPO_PUBLIC_FIREBASE_PROHECT_Id` | **Note the typo: "PROHECT"** — matches the config file |
| `EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET` | Firebase storage bucket |
| `EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | FCM sender ID |
| `EXPO_PUBLIC_FIREBASE_APP_ID` | Firebase app ID |
| `EXPO_PUBLIC_FIREBASE_MEASUREMENT_ID` | Analytics measurement ID |

If `EXPO_PUBLIC_FIREBASE_DATABASE_URL` is blank, Firebase is never initialized and the menu shows empty (no crash).

**Known typo:** `EXPO_PUBLIC_FIREBASE_PROHECT_Id` — "PROJECT" is misspelled as "PROHECT" in both `firebaseConfig.ts` and `.env_example.txt`. They match each other, so it works. Do not fix one without fixing the other.

---

## Local Development Setup

### 1. Python Backend

```bash
# From repo root
uv venv .venv --python 3.12
source .venv/bin/activate

cd coffee_shop_customer_service_chatbot/python_code/api
uv pip install -r requirements.txt

cp .env_example .env
# Edit .env: set RUNPOD_TOKEN to your Groq key

python local_server.py
# → Server running at http://localhost:8000
# → GET / returns {"status": "ok", ...}
```

**Why uv instead of pip:** Raw `pip` fails to build `pandas` on Python 3.12 due to a `pkg_resources` issue on this system. `uv` resolves this.

**First startup:** You'll see `"Loading agents..."` then `"Agents ready."` — this is `AgentController.__init__()` initializing all 5 agents and loading the recommendation JSON/CSV files.

**Test the server:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "What lattes do you have?"}]}}'
```

Expected response shape:
```json
{
  "output": {
    "role": "assistant",
    "content": "...",
    "memory": { "agent": "details_agent" }
  }
}
```

**CLI chat (no server):**
```bash
python development_code.py
# Interactive terminal chat — useful for quick agent testing
# Shows which agent was chosen for each message
```

### 2. React Native Frontend

```bash
cd coffee_shop_customer_service_chatbot/coffee_shop_app
cp .env_example.txt .env
# .env already has EXPO_PUBLIC_RUNPOD_API_URL=http://localhost:8000/chat

npm install

npm run web          # Browser at http://localhost:8081
npm run android      # Requires Android emulator or device + Expo Go
```

**Web mode:** Fully functional for chat and order flow. Images from Firebase load as standard `<img>` tags.

**Android mode:** Requires either a physical device with Expo Go app or Android Studio emulator. Remember to change `localhost` to `10.0.2.2` in `.env` for the emulator.

---

## Python Dependencies (`requirements.txt`)

```
pandas>=2.1.0            # popularity_recommendation.csv loading
python-dotenv==1.0.1     # .env file loading
openai==1.50.2           # LLM + embedding calls (OpenAI-compatible SDK)
runpod==1.7.1            # serverless handler (production only, used in main.py)
pinecone==5.3.1          # vector DB client (optional, DetailsAgent)
httpx==0.27.2            # HTTP client — MUST be pinned, newer versions break openai async client
fastapi==0.115.0         # local HTTP server
uvicorn==0.30.6          # ASGI server for FastAPI
sentence-transformers    # local embeddings for RAG (DetailsAgent)
structlog>=25.0.0        # structured JSON logging — observability
```

**Not in requirements but used locally:** None — all imports are in requirements.txt.

**Missing from requirements:** `pydantic` (used by FastAPI) is installed transitively. No explicit pin.

---

## Docker (Production)

```bash
cd coffee_shop_customer_service_chatbot/python_code/api
docker build -t chatbot:latest .
```

Entry point in `Dockerfile` (not shown in source, but expected): runs `main.py` which starts the RunPod serverless handler.

`local_server.py` is **not** used in the Docker image — it's local dev only. `main.py` is the production entry point.

---

## LLM Provider Swap

To switch providers, only `.env` changes are needed. No code changes:

| Provider | `RUNPOD_TOKEN` | `RUNPOD_CHATBOT_URL` | `MODEL_NAME` |
|---|---|---|---|
| Groq (free, local) | Groq API key | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| RunPod (production) | RunPod token | `https://api.runpod.ai/v2/<id>/openai/v1` | `meta-llama/Llama-3.1-8B-Instruct` |
| OpenAI | OpenAI key | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Ollama (fully local) | `ollama` | `http://localhost:11434/v1` | `llama3.1:8b` |

This works because all agents use `OpenAI(api_key=..., base_url=...)` — the SDK supports any OpenAI-compatible endpoint.
