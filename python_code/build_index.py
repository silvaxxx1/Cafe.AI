"""
Builds the ChromaDB vector index for the DetailsAgent RAG pipeline.

Usage:
    cd coffee_shop_customer_service_chatbot/python_code
    python build_index.py

The index is written to api/chroma_db/ — no API key or external service needed.
Restart the backend after running this to enable RAG in DetailsAgent.
"""
import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH     = os.getenv("CHROMA_DB_PATH", "api/chroma_db")
COLLECTION_NAME = "coffeeshop"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── 1. Load embedding model ────────────────────────────────────────────────────
print("Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)
print(f"Model ready (dim=384)")

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
    texts.append("Fero Cafe about section: " + f.read())

with open("products/menu_items_text.txt") as f:
    texts.append("Menu Items: " + f.read())

print(f"Corpus ready: {len(texts)} documents")

# ── 3. Generate embeddings ─────────────────────────────────────────────────────
print("\nGenerating embeddings (local, no API needed)...")
embeddings = model.encode(texts, show_progress_bar=True).tolist()
print(f"Generated {len(embeddings)} embeddings")

# ── 4. Write to ChromaDB ───────────────────────────────────────────────────────
print(f"\nWriting to ChromaDB at '{CHROMA_PATH}'...")
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Drop and recreate so re-runs are always fresh
try:
    client.delete_collection(COLLECTION_NAME)
    print(f"Dropped existing '{COLLECTION_NAME}' collection.")
except Exception:
    pass

collection = client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

ids = [str(i) for i in range(len(texts))]
collection.add(ids=ids, embeddings=embeddings, documents=texts)
print(f"Indexed {len(texts)} documents.")

# ── 5. Smoke test ──────────────────────────────────────────────────────────────
print("\nSmoke test — querying 'Is Cappuccino lactose-free?'...")
query_embedding = model.encode("Is Cappuccino lactose-free?").tolist()
results = collection.query(query_embeddings=[query_embedding], n_results=2)
for doc in results["documents"][0]:
    print(f"  → {doc[:100]}...")

print(f"\nDone. ChromaDB index written to '{CHROMA_PATH}'.")
print("Restart the backend — DetailsAgent will print 'RAG enabled'.")
