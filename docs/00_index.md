# Cafe.AI Documentation Index

Complete technical documentation of the project in its current state.
Read these in order before making any changes.

---

## Documents

| # | File | What it covers |
|---|---|---|
| 01 | [Architecture Overview](./01_architecture.md) | System diagram, two deployment modes, response contract, key design decisions |
| 02 | [Backend Agents Deep Dive](./02_backend_agents.md) | Every agent explained: input, prompt logic, output shape, edge cases |
| 03 | [End-to-End Data Flow](./03_data_flow.md) | 5 flows traced step by step: chat, menu browse, cart, details, checkout |
| 04 | [Frontend Deep Dive](./04_frontend.md) | All screens, components, services, routing, and state management |
| 05 | [Data, Models & Notebooks](./05_data_and_models.md) | Recommendation data, Apriori rules, Firebase schema, ChromaDB setup, notebooks |
| 06 | [Environment & Setup](./06_environment_and_setup.md) | Every env var, what it does, local dev commands, Docker, provider swap |
| 07 | [Known Issues & Gaps](./07_known_issues_and_gaps.md) | Open issues, bugs, fragile patterns — the V2 backlog |
| 08 | [Deployment Guide](./08_deployment.md) | Vercel + Render production deploy, SQLite persistence, GitHub V1 release, showcase checklist |

---

## Quick Facts

- **Backend:** Python 3.12, FastAPI, OpenAI SDK (provider-agnostic), 5 agents
- **Frontend:** React Native 0.81.5, Expo 54, Expo Router, NativeWind
- **LLM:** Any OpenAI-compatible API (Groq locally, RunPod in production)
- **Databases:** Firebase Realtime DB (menu), ChromaDB (RAG, local disk, optional), SQLite (sessions)
- **State:** SQLite-backed `SessionStore` — session restored on reload, cleared via "New chat"
- **Tests:** 126 backend + 34 frontend (160 total) — `make test-all`
- **Evals:** Guard, classification, recommendation runners against real LLM (`make evals`)
- **Observability:** structlog structured logging + live Chart.js dashboard at `/dashboard`
- **Streaming:** `POST /chat/stream` SSE — tokens stream as generated, first token ~1s
- **Async:** Fully async FastAPI + agents

---

## The 3 Things Most Likely to Confuse You

1. **`RUNPOD_TOKEN` holds the Groq key locally** — the variable name is the production provider, not the local one
2. **Cart uses `syncCartFromOrder`** — merges LLM orders into the cart without wiping manually-added items; `emptyCart()` is only called on checkout/new chat
3. **RAG requires a one-time setup** — run `python_code/build_index.py` to build the ChromaDB index; no API key or account needed
