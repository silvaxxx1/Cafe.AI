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
| 05 | [Data, Models & Notebooks](./05_data_and_models.md) | Recommendation data, Apriori rules, Firebase schema, Pinecone setup, notebooks |
| 06 | [Environment & Setup](./06_environment_and_setup.md) | Every env var, what it does, local dev commands, Docker, provider swap |
| 07 | [Known Issues & Gaps](./07_known_issues_and_gaps.md) | 25 documented issues: bugs, fragile patterns, design gaps |

---

## Quick Facts

- **Backend:** Python 3.12, FastAPI, OpenAI SDK (provider-agnostic), 5 agents
- **Frontend:** React Native 0.81.5, Expo 54, Expo Router, NativeWind
- **LLM:** Any OpenAI-compatible API (Groq locally, RunPod in production)
- **Databases:** Firebase Realtime DB (menu), Pinecone (RAG, optional)
- **State:** Embedded in message `memory` field — no server-side session
- **Tests:** 90 passing — unit tests + eval runner tests (`make test`)
- **Evals:** Guard, classification, recommendation runners against real LLM (`make evals`)
- **Observability:** structlog structured logging + live Chart.js dashboard at `/dashboard`
- **Streaming:** Not implemented
- **Async:** Fully async FastAPI + agents

---

## The 3 Things Most Likely to Confuse You

1. **`RUNPOD_TOKEN` holds the Groq key locally** — the variable name is the production provider, not the local one
2. **Cart is wiped every time the order agent responds** — `emptyCart()` is called in `chatRoom.tsx` before repopulating from the LLM's order object
3. **`EXPO_PUBLIC_FIREBASE_PROHECT_Id` is a typo** — "PROHECT" not "PROJECT" — in both the config file and env example; they match each other
