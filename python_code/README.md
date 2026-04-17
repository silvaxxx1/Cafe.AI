# Python Code — Data Pipelines & Backend

This folder contains the multi-agent API backend and the data pipeline notebooks used to build and seed the system.

## Directory Structure

```
python_code/
├── api/                                    # Multi-agent FastAPI backend
│   ├── agents/                             # Guard, Classification, Details, Order, Recommendation
│   ├── tests/                              # 102 passing tests (no API key needed)
│   ├── recommendation_objects/             # Pre-trained Apriori model + popularity data
│   ├── local_server.py                     # Dev server (FastAPI, mirrors RunPod format)
│   ├── main.py                             # RunPod serverless entry point
│   ├── agent_controller.py                 # Pipeline orchestrator
│   ├── menu.json                           # Single source of truth for product names
│   └── requirements.txt
├── products/
│   ├── products.jsonl                      # Full product catalog (name, price, description, image)
│   └── images/                             # Source product images
├── dataset/                                # Kaggle order dataset for training recommendations
├── build_vector_database.ipynb             # Embeds menu data → Pinecone (for RAG)
├── firebase_uploader.ipynb                 # Seeds products to Firebase Realtime DB
└── recommendation_engine_training.ipynb    # Trains Apriori market basket model
```

## Backend API

See **[api/README.md](api/README.md)** for full setup, environment variables, and agent pipeline docs.

**Quick start (free, no GPU needed):**
```bash
uv venv .venv --python 3.12 && source .venv/bin/activate
cd api
uv pip install -r requirements.txt
uv pip install "httpx==0.27.2"   # pin required — newer versions break openai SDK
cp .env_example .env             # set RUNPOD_TOKEN to a free Groq key
python local_server.py           # http://localhost:8000
```

## Notebooks

### `firebase_uploader.ipynb`
Reads `products/products.jsonl` and seeds all 18 products to Firebase Realtime Database.  
Product **images are not uploaded** — they're bundled locally in the app (`coffee_shop_app/assets/images/products/`). Firebase stores only the image filename.

```bash
# Re-run after any product changes
../.venv/bin/python -c "exec(open('firebase_uploader_script.py').read())"
```

### `build_vector_database.ipynb`
Embeds menu and shop info using `sentence-transformers/all-MiniLM-L6-v2` (runs locally) and upserts to a Pinecone serverless index. Required for the `DetailsAgent` RAG feature.

```
# Needs:
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=coffeeshop
```

Without this, `DetailsAgent` is gracefully disabled and the rest of the app works fine.

### `recommendation_engine_training.ipynb`
Trains an Apriori market basket model on the Kaggle coffee shop order dataset.  
Outputs static files loaded by `RecommendationAgent` at startup — no retraining at runtime.

## Data Consistency Rule

`menu.json` (in `api/`) is the **single source of truth** for product names.  
If you rename or add a product, update all three: `menu.json`, `products.jsonl`, and re-seed Firebase.
