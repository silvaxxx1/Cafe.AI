# Python Code — Backend & Data Pipelines

This folder contains two things: the multi-agent FastAPI backend that powers the chatbot, and the three notebooks used to build and seed the data it depends on (vector DB, Firebase catalog, recommendation model).

---

## Directory Structure

```
python_code/
├── api/                                    # Multi-agent FastAPI backend
│   ├── agents/                             # Guard, Classification, Details, Order, Recommendation
│   ├── tests/                              # 90 passing tests — unit + eval runners (no API key needed for unit tests)
│   ├── recommendation_objects/             # Pre-trained Apriori model + popularity data
│   ├── local_server.py                     # Dev server (FastAPI, mirrors RunPod format)
│   ├── main.py                             # RunPod serverless entry point
│   ├── agent_controller.py                 # Pipeline orchestrator
│   ├── menu.json                           # Single source of truth for product names
│   └── requirements.txt
├── products/
│   ├── products.jsonl                      # Full product catalog (name, price, description, image)
│   └── images/                             # Source product images
├── dataset/                                # Kaggle order dataset for recommendation training
├── build_vector_database.ipynb             # Embeds menu data → Pinecone (RAG)
├── firebase_uploader.ipynb                 # Seeds products to Firebase Realtime DB
└── recommendation_engine_training.ipynb    # Trains Apriori market basket model
```

---

## Backend API

Full setup, environment variables, and agent pipeline documentation lives in **[api/README.md](api/README.md)**.

**Quick start — free, no GPU required:**

```bash
uv venv .venv --python 3.12 && source .venv/bin/activate
cd api
uv pip install -r requirements.txt
uv pip install "httpx==0.27.2"   # required — newer versions break the openai async client
cp .env_example .env             # set RUNPOD_TOKEN to your Groq key (free at console.groq.com)
python local_server.py           # → http://localhost:8000
```

---

## Notebooks

Run these once to build the data assets the backend depends on. They don't need to be re-run unless you change products or want to retrain recommendations.

### `firebase_uploader.ipynb`

Reads `products/products.jsonl` and seeds all 18 products to Firebase Realtime Database. Product **images are not uploaded** — they're bundled locally in the app at `coffee_shop_app/assets/images/products/`. Firebase stores only the image filename (e.g. `cappuccino.jpg`).

Re-run whenever you add or rename a product (and after updating `menu.json` and `products.jsonl`).

### `build_vector_database.ipynb`

Embeds menu and shop info using `sentence-transformers/all-MiniLM-L6-v2` (runs entirely locally) and upserts vectors to a Pinecone serverless index. This is what powers `DetailsAgent` RAG responses.

Requires in `api/.env`:

```ini
PINECONE_API_KEY=your-key
PINECONE_INDEX_NAME=coffeeshop
```

Without Pinecone, `DetailsAgent` is gracefully disabled and the rest of the app works normally.

### `recommendation_engine_training.ipynb`

Trains an Apriori market basket model on the Kaggle coffee shop order dataset. Outputs static files that `RecommendationAgent` loads at startup — no retraining happens at runtime.

---

## ⚠️ Data Consistency

`api/menu.json` is the **single source of truth** for product names. The order-taking agent validates all orders against it.

If you rename or add a product, update **all three** in sync:

1. `api/menu.json`
2. `products/products.jsonl`
3. Re-run `firebase_uploader.ipynb` to push changes to Firebase