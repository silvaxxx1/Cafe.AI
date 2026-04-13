# Coffee Shop Customer Service Chatbot

An AI-powered coffee shop chatbot built with a multi-agent Python backend and a React Native mobile app. Customers can place orders, ask menu questions, and get personalized recommendations — all through natural conversation.

## Architecture

```
React Native App (Expo)
        ↓ HTTP POST /chat
  Python FastAPI Server
        ↓
  AgentController pipeline:
    GuardAgent → ClassificationAgent → [ DetailsAgent | OrderTakingAgent | RecommendationAgent ]
        ↓
  Groq / RunPod (LLM)  +  Pinecone (RAG, optional)
```

**Agents:**
- **Guard** — blocks off-topic or harmful queries
- **Classification** — routes intent to the right agent
- **Details** — answers menu/ingredient questions via RAG (Pinecone + embeddings)
- **Order Taking** — multi-turn order collection with menu validation and auto-upsell
- **Recommendation** — suggests items using Apriori market basket analysis and popularity rankings

## Quick Start (free, no RunPod needed)

### Prerequisites
- Python 3.12, Node.js 18+
- [`uv`](https://github.com/astral-sh/uv) for Python package management
- A free [Groq API key](https://console.groq.com) for the LLM

### 1. Backend

```bash
# From the repo root
uv venv .venv --python 3.12
source .venv/bin/activate

cd coffee_shop_customer_service_chatbot/python_code/api
uv pip install -r requirements.txt

cp .env_example .env
# Edit .env — set RUNPOD_TOKEN to your Groq API key

python local_server.py       # starts on http://localhost:8000
```

Verify it works:
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "I want a latte"}]}}' \
  | python3 -m json.tool
```

### 2. Frontend

```bash
cd coffee_shop_customer_service_chatbot/coffee_shop_app
cp .env_example.txt .env
# .env already points to http://localhost:8000/chat by default

npm install
npm run web        # opens in browser at http://localhost:8081
```

The app runs without Firebase (home menu will be empty). The **Chat tab** is fully functional.

## Demo Flow

1. Open the **Chat** tab
2. Try: *"What do you recommend?"* → Recommendation agent responds
3. Try: *"I'd like a latte and a croissant"* → Order agent collects the order + auto-upsells
4. Try: *"No thanks, that's all"* → Order confirmed with total price
5. Switch to the **Order** tab → items appear automatically from the chat
6. Hit **Order** → checkout complete

Try an off-topic message like *"What's the weather?"* — the Guard agent blocks it.

## Running on a Phone

Install [Expo Go](https://expo.dev/go) on your phone. Make sure the phone is on the same Wi-Fi as your computer, then:

```bash
# Replace localhost with your computer's local IP in coffee_shop_app/.env
EXPO_PUBLIC_RUNPOD_API_URL='http://192.168.x.x:8000/chat'

npm start   # scan the QR code with Expo Go
```

## Full Setup (with Firebase + Pinecone)

For a complete setup with a real product menu and RAG-powered menu questions:

### Firebase (product catalog)
1. Create a free project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable **Realtime Database**
3. Run `python_code/firebase_uploader.ipynb` to seed the product catalog
4. Fill in `coffee_shop_app/.env` with your Firebase credentials

### Pinecone (details agent RAG)
1. Create a free index at [pinecone.io](https://www.pinecone.io)
2. Run `python_code/build_vector_database.ipynb` to build the index
3. Set `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` in `python_code/api/.env`
4. Set `RUNPOD_EMBEDDING_URL` to an embedding endpoint (Ollama or RunPod)

### Train Recommendation Models
```bash
cd python_code
jupyter notebook recommendation_engine_training.ipynb
```

## Production Deployment (RunPod)

```bash
cd coffee_shop_customer_service_chatbot/python_code/api

# Build and push Docker image
docker build -t your-dockerhub/chatbot:latest .
docker push your-dockerhub/chatbot:latest
```

Then create a RunPod serverless endpoint with the image and set environment variables from `.env_example`.

Update the frontend `.env` to point `EXPO_PUBLIC_RUNPOD_API_URL` at the RunPod endpoint.

## Directory Structure

```
coffee_shop_customer_service_chatbot/
├── coffee_shop_app/          # React Native (Expo) frontend
│   ├── app/                  # Expo Router screens
│   ├── components/           # UI components + CartContext
│   ├── services/             # API calls (chatBot.ts, productService.ts)
│   └── config/               # Firebase + API config
└── python_code/
    ├── api/                  # Multi-agent Python backend
    │   ├── agents/           # Guard, Classification, Details, Order, Recommendation
    │   ├── local_server.py   # FastAPI server for local dev
    │   ├── main.py           # RunPod serverless entry point (production)
    │   └── development_code.py # CLI chat for testing
    ├── build_vector_database.ipynb
    ├── firebase_uploader.ipynb
    └── recommendation_engine_training.ipynb
```
