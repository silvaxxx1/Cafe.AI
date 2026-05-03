# Cafe.AI — AI-Powered Coffee Shop

> A full-stack conversational commerce app: React Native frontend + Python multi-agent backend.

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![React Native](https://img.shields.io/badge/React%20Native-Expo-blue.svg)](https://expo.dev)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3-orange.svg)](https://groq.com)
[![Tests](https://img.shields.io/badge/tests-120%20passing-brightgreen.svg)]()

Chat with an AI barista, browse the menu, get personalized recommendations, and check out — all in one flow.

---

## What's Inside

```
coffee_shop_customer_service_chatbot/
├── coffee_shop_app/    # React Native (Expo) — mobile + web
└── python_code/        # Python multi-agent backend (FastAPI + Groq)
```

**[→ Full documentation & quick start](coffee_shop_customer_service_chatbot/README.md)**

---

## Highlights

- **Multi-agent pipeline** — Guard → Classification → Details / Order / Recommendation
- **RAG** — Pinecone vector search for menu & shop questions (optional, gracefully disabled)
- **Smart ordering** — Multi-turn conversation, menu validation, automatic upsell
- **Apriori recommendations** — Market basket analysis from order history
- **React Native app** — Runs on iOS, Android, and web (Expo Router)
- **Playful editorial design** — Terracotta accent, warm light/dark theme, Sora typeface
- **SSE streaming** — Responses stream token-by-token via `POST /chat/stream`; first token in ~1s
- **Session persistence** — SQLite-backed sessions; conversation restores on reload, "New chat" to reset
- **Provider-agnostic LLM** — Swap Groq, RunPod, or any OpenAI-compatible API via `.env`
- **120 passing tests** — Unit + eval runners, no API key needed for unit tests
- **Evals** — Guard, classification, recommendation runners against the real LLM (`make evals`)
- **Observability** — structlog structured logging + live `/dashboard` with latency, token, and routing metrics

---

## Quick Start

See **[coffee_shop_customer_service_chatbot/README.md](coffee_shop_customer_service_chatbot/README.md)** for the full setup guide (5 minutes with a free Groq key).

---

**Built with ☕ and 🤖 by [SilvaLAB](https://github.com/silvaxxx1)**
