# Deployment Guide

> **Goal:** A live, always-on demo URL to show to people and potential buyers.  
> **Total cost: $7/mo** (Render paid tier). Frontend and LLM are free.

---

## Stack

| Layer | Service | Cost | Notes |
|---|---|---|---|
| Frontend | Vercel | Free | Expo web build, CDN, no cold start |
| Backend | Render (paid) | $7/mo | No cold start, persistent disk for SQLite |
| LLM | Groq | Free | Already configured in `.env` |
| Sessions | SQLite on Render disk | Included in $7 | Survives redeploys on paid tier |

> **Why not Render free tier?** It sleeps after 15 min idle — first request takes ~30s to cold-start. That kills a live demo. Never demo on free tier to a buyer.

---

## Prerequisites

- [ ] Repo pushed to GitHub
- [ ] Groq API key from [console.groq.com](https://console.groq.com) (free)
- [ ] Vercel account (free) — [vercel.com](https://vercel.com)
- [ ] Render account — [render.com](https://render.com)
- [ ] Firebase credentials (for product catalog)

---

## Step 1 — Deploy Backend to Render

### 1.1 Create the Web Service

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo (`Cafe.AI`)
3. Configure the service:

| Field | Value |
|---|---|
| **Name** | `cafe-ai-backend` |
| **Root Directory** | `coffee_shop_customer_service_chatbot/python_code/api` |
| **Runtime** | Docker |
| **Instance Type** | **Starter ($7/mo)** — do not use Free |

Render will detect the `Dockerfile` automatically.

### 1.2 Set Environment Variables

In the Render dashboard → Environment, add:

```
RUNPOD_TOKEN=your-groq-api-key
RUNPOD_CHATBOT_URL=https://api.groq.com/openai/v1
MODEL_NAME=llama-3.3-70b-versatile
```

Optional (for RAG — Stage 4 V2):
```
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=coffeeshop
```

### 1.3 Add Persistent Disk (for SQLite sessions)

In the Render dashboard → **Disks** → **Add Disk**:

| Field | Value |
|---|---|
| **Name** | `sessions-disk` |
| **Mount Path** | `/app/data` |
| **Size** | 1 GB (minimum) |

Then update `session.py` to write the SQLite DB to the persistent path:
```python
# session.py
SessionStore(path="/app/data/sessions.db")   # was: "sessions.db"
```

Update `local_server.py` to pass the path:
```python
session_store = SessionStore(path=os.getenv("SESSION_DB_PATH", "sessions.db"))
```

Add to Render env vars:
```
SESSION_DB_PATH=/app/data/sessions.db
```

### 1.4 Update CORS for Production

In `local_server.py`, add your Vercel frontend URL to `_ALLOWED_ORIGINS`:
```python
_ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "http://localhost:19006",
    "http://127.0.0.1:8081",
    "https://cafe-ai.vercel.app",   # add your Vercel URL here
]
```

### 1.5 Deploy

Click **Deploy** — Render builds the Docker image and starts the service.

Your backend URL will be: `https://cafe-ai-backend.onrender.com`

Verify it's alive:
```bash
curl https://cafe-ai-backend.onrender.com/
# → {"status": "ok"}
```

---

## Step 2 — Deploy Frontend to Vercel

### 2.1 Build the Web App

```bash
cd coffee_shop_customer_service_chatbot/coffee_shop_app

# Install dependencies if not already done
npm install

# Build the Expo web export
npx expo export -p web
# → Output goes to dist/
```

### 2.2 Deploy to Vercel

```bash
# Install Vercel CLI (once)
npm install -g vercel

# Deploy
cd dist
vercel --prod
```

Follow the prompts — link to your Vercel account and project.

### 2.3 Set Environment Variables in Vercel

In the Vercel dashboard → Project → Settings → Environment Variables:

```
EXPO_PUBLIC_RUNPOD_API_URL=https://cafe-ai-backend.onrender.com/chat/stream
EXPO_PUBLIC_FIREBASE_API_KEY=your-firebase-api-key
EXPO_PUBLIC_FIREBASE_DATABASE_URL=your-firebase-db-url
EXPO_PUBLIC_FIREBASE_PROJECT_ID=your-firebase-project-id
EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN=your-firebase-auth-domain
EXPO_PUBLIC_FIREBASE_APP_ID=your-firebase-app-id
```

Redeploy after setting env vars:
```bash
vercel --prod
```

Your frontend URL: `https://cafe-ai.vercel.app`

---

## Step 3 — Verify the Full Stack

```bash
# 1. Backend health
curl https://cafe-ai-backend.onrender.com/
# → {"status": "ok"}

# 2. Streaming endpoint
curl -N -X POST https://cafe-ai-backend.onrender.com/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "I want a latte"}]}}'
# → SSE token stream ending with {"type":"done","memory":{...}}

# 3. Observability dashboard
open https://cafe-ai-backend.onrender.com/dashboard
# → Live Chart.js dashboard — latency, tokens, agent routing
```

Open `https://cafe-ai.vercel.app` in browser — product menu loads, chat works.

---

## Step 4 — Update README with Live URLs

Once deployed, update the root `README.md`:

```markdown
## Live Demo

**[cafe-ai.vercel.app](https://cafe-ai.vercel.app)**

Try asking:
- *"What do you recommend?"*
- *"I want a latte and a croissant"*
- *"Who won the World Cup?"* (guard blocks it)

**[Observability Dashboard →](https://cafe-ai-backend.onrender.com/dashboard)**
```

---

## Step 5 — GitHub V1 Stable Release

1. Go to GitHub repo → **Releases** → **Create a new release**
2. Tag: `v1.0.0`
3. Title: `V1 — Production-Grade Release`
4. Body:

```markdown
## Cafe.AI V1

Full-stack AI coffee shop chatbot — production-grade backend, React Native frontend.

### What's in V1
- Multi-agent pipeline: Guard → Classification → Details / Order / Recommendation
- SSE streaming — tokens stream as generated, first token ~1s
- SQLite session persistence — conversation restores on reload
- 120 passing tests + LLM eval runners (80% threshold)
- Observability dashboard — live latency, token, and routing metrics
- Production hardening — rate limiting, CORS, startup validation, typed input
- CI/CD — GitHub Actions on every push

### Live Demo
[cafe-ai.vercel.app](https://cafe-ai.vercel.app)

### V2 Roadmap
See [V2_PLAN.md](V2_PLAN.md) — frontend functional parity, AI quality improvements, frontend tests.
```

5. Click **Publish release**

---

## Showcase Checklist

Before sharing the link with anyone:

- [ ] Backend responds at `/` with `{"status": "ok"}`
- [ ] Chat streaming works end-to-end
- [ ] Product menu loads in the home tab
- [ ] Cart populates when order agent responds
- [ ] Observability dashboard loads at `/dashboard`
- [ ] Live URL in README
- [ ] GitHub V1 release published
- [ ] Demo video recorded (Loom — free, 60 seconds is enough)

---

## What to Show Buyers

In order of impact:

1. **Live URL** — open it, type *"I want a latte and a croissant"*, show the cart auto-populating
2. **Guard demo** — type *"Who won the World Cup?"*, show it getting blocked
3. **Observability dashboard** — `https://cafe-ai-backend.onrender.com/dashboard` — live latency and routing metrics. Most portfolios have nothing like this.
4. **Test suite** — `make test` → 120 passing. No API key needed.
5. **V2 plan** — shows you think beyond the current state

---

## Cost Summary

| Service | Plan | Monthly Cost |
|---|---|---|
| Vercel | Free | $0 |
| Render | Starter | $7 |
| Groq | Free tier | $0 |
| **Total** | | **$7/mo** |

Upgrade path: if traffic grows, Render Standard ($25/mo) gives more RAM and CPU. No architectural changes needed.
