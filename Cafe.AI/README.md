# Cafe.AI — AI-Powered Coffee Shop

> A full-stack conversational commerce app: React Native frontend + Python multi-agent backend.

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![React Native](https://img.shields.io/badge/React%20Native-Expo-blue.svg)](https://expo.dev)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3-orange.svg)](https://groq.com)
[![Tests](https://img.shields.io/badge/tests-160%20passing-brightgreen.svg)]()

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
- **RAG** — ChromaDB local vector search for menu & shop questions (optional, no API key needed)
- **Smart ordering** — Multi-turn conversation, menu validation, automatic upsell
- **Apriori recommendations** — Market basket analysis from order history
- **React Native app** — Runs on iOS, Android, and web (Expo Router)
- **Playful editorial design** — Terracotta accent, warm light/dark theme, Sora typeface
- **SSE streaming** — Responses stream token-by-token via `POST /chat/stream`; first token in ~1s
- **Session persistence** — SQLite-backed sessions; conversation restores on reload, "New chat" to reset
- **Provider-agnostic LLM** — Swap Groq, RunPod, or any OpenAI-compatible API via `.env`
- **160 passing tests** — 126 backend (pytest) + 34 frontend (Jest), no API key needed for unit tests
- **Live search** — filter menu by name in real time, combined with category chips
- **Size selection** — S/M/L adjusts price live; size-adjusted totals in cart
- **Product images in chat** — cards below recommendation and final-order bubbles, tappable to detail
- **Smart cart merge** — chat orders merge with browse-screen adds; no cart-wipe on agent response
- **Evals** — Guard, classification, recommendation runners against the real LLM (`make evals`)
- **Observability** — structlog structured logging + live `/dashboard` with latency, token, and routing metrics

---

## Quick Start

See **[coffee_shop_customer_service_chatbot/README.md](coffee_shop_customer_service_chatbot/README.md)** for the full setup guide (5 minutes with a free Groq key).

---

---

## Roadmap

**V1 — Complete ✅** — all 9 backend upgrade stages done. Async, streaming, sessions, observability, evals, hardening, CI.

**V2 — Complete ✅** — live search, size selection, product image cards in chat, cart-merge fix, recommendation turn memory, wider context window, response variation, AgentMemory types, 34 frontend tests, RAG via ChromaDB (local, no API key).

**V3 — Possible next** — cart→agent context awareness, product images on menu/details responses, multi-tenant SaaS deployment.

See [`V2_PLAN.md`](V2_PLAN.md) for the full plan with file references.

---

**Built with ☕ and 🤖 by [SilvaLAB](https://github.com/silvaxxx1)**
