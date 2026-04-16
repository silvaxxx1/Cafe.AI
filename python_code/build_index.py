"""
Builds the Pinecone vector index for the DetailsAgent RAG pipeline.
Equivalent to running build_vector_database.ipynb — run this instead.

Usage:
    cd coffee_shop_customer_service_chatbot/python_code
    python build_index.py
"""
import os
import json
import pandas as pd
from time import time, sleep
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import dotenv

dotenv.load_dotenv("api/.env")

PINECONE_API_KEY   = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "coffeeshop")
EMBEDDING_MODEL    = "all-MiniLM-L6-v2"
DIMENSION          = 384

# ── 1. Load embedding model ────────────────────────────────────────────────────
print("Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)
print(f"Model ready (dim={DIMENSION})")

# ── 2. Build text corpus ───────────────────────────────────────────────────────
print("\nBuilding text corpus from products...")
df = pd.read_json("products/products.jsonl", lines=True)
df["text"] = (
    df["name"] + " : " + df["description"]
    + " -- Ingredients: " + df["ingredients"].astype(str)
    + " -- Price: $" + df["price"].astype(str)
    + " -- Rating: " + df["rating"].astype(str)
)

texts = df["text"].tolist()

with open("products/fero_cafe_about_us.txt") as f:
    about = "Fero Cafe about section: " + f.read()
texts.append(about)

with open("products/menu_items_text.txt") as f:
    menu = "Menu Items: " + f.read()
texts.append(menu)

print(f"Corpus ready: {len(texts)} documents")

# ── 3. Generate embeddings ─────────────────────────────────────────────────────
print("\nGenerating embeddings (local, no API needed)...")
embeddings = model.encode(texts, show_progress_bar=True).tolist()
print(f"Generated {len(embeddings)} embeddings, dim={len(embeddings[0])}")

# ── 4. Connect to Pinecone ─────────────────────────────────────────────────────
print("\nConnecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)

existing = [idx.name for idx in pc.list_indexes()]
if PINECONE_INDEX_NAME in existing:
    print(f"Index '{PINECONE_INDEX_NAME}' already exists — deleting and rebuilding...")
    pc.delete_index(PINECONE_INDEX_NAME)
    sleep(2)

print(f"Creating index '{PINECONE_INDEX_NAME}' (dim={DIMENSION}, metric=cosine)...")
pc.create_index(
    name=PINECONE_INDEX_NAME,
    dimension=DIMENSION,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

print("Waiting for index to be ready...")
while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
    sleep(1)
print("Index ready.")

# ── 5. Upsert vectors ─────────────────────────────────────────────────────────
print("\nUploading vectors to Pinecone...")
index = pc.Index(PINECONE_INDEX_NAME)

vectors = []
for text, embedding in zip(texts, embeddings):
    entry_id = text.split(":")[0].strip()[:50]
    vectors.append({
        "id": entry_id,
        "values": embedding,
        "metadata": {"text": text}
    })

index.upsert(vectors=vectors, namespace="ns1")
print(f"Upserted {len(vectors)} vectors.")

# ── 6. Smoke test ──────────────────────────────────────────────────────────────
print("\nSmoke test — querying 'Is Cappuccino lactose-free?'...")
sleep(2)  # let Pinecone index settle
query_embedding = model.encode("Is Cappuccino lactose-free?").tolist()
results = index.query(
    namespace="ns1",
    vector=query_embedding,
    top_k=2,
    include_values=False,
    include_metadata=True
)
for match in results["matches"]:
    print(f"  score={match['score']:.3f} | {match['metadata']['text'][:80]}...")

print("\nDone! Pinecone index is ready.")
print(f"Set PINECONE_INDEX_NAME={PINECONE_INDEX_NAME} in your .env (already set).")
