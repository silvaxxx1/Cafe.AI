# Data, Models & Notebooks

---

## Data Pipeline Overview

```
Transaction history (CSV)
    │
    ├── recommendation_engine_training.ipynb
    │       → apriori_recommendations.json     (loaded by RecommendationAgent)
    │       → popularity_recommendation.csv    (loaded by RecommendationAgent)
    │
    ├── firebase_uploader.ipynb
    │       → products uploaded to Firebase Realtime DB (read by frontend)
    │
    └── build_vector_database.ipynb
            → product descriptions embedded → ChromaDB index on disk (read by DetailsAgent)
```

Notebooks are one-time setup scripts, not part of the live server.

---

## Recommendation Objects

**Location:** `python_code/api/recommendation_objects/`

### `apriori_recommendations.json`

Pre-computed market basket association rules.

**Structure:**
```json
{
  "ProductName": [
    {
      "product": "Associated Product Name",
      "product_category": "Category",
      "confidence": 0.497
    },
    ...
  ],
  ...
}
```

- 16 products have rules (those with enough co-purchase history)
- Confidence = P(B | A) — probability of buying B given A was bought
- Rules are sorted by confidence at query time in `get_apriori_recommendation()`
- Algorithm: Apriori (trained in `recommendation_engine_training.ipynb`)

**All 16 keys with sample top association:**
| Item | Top associated item | Confidence |
|---|---|---|
| Almond Croissant | Dark chocolate (Packaged) | ~0.50 |
| Cappuccino | Dark chocolate | 0.497 |
| Dark chocolate | Latte | 0.471 |
| Espresso shot | Cappuccino | varies |
| Latte | Cappuccino | varies |
| ... | ... | ... |

### `popularity_recommendation.csv`

19 rows, one per product. Columns: `product`, `product_category`, `number_of_transactions`.

**Top 10 by transaction count:**

| Rank | Product | Category | Transactions |
|---|---|---|---|
| 1 | Cappuccino | Coffee | 1290 |
| 2 | Latte | Coffee | 1256 |
| 3 | Dark chocolate (Drinking) | Drinking Chocolate | 947 |
| 4 | Espresso shot | Coffee | 628 |
| 5 | Sugar Free Vanilla syrup | Flavours | 605 |
| 6 | Chocolate syrup | Flavours | 568 |
| 7 | Hazelnut syrup | Flavours | 512 |
| 8 | Ginger Scone | Bakery | 417 |
| 9 | Chocolate Croissant | Bakery | 636 |
| 10 | Croissant | Bakery | 355 |

**Categories present:** Coffee, Bakery, Flavours, Drinking Chocolate, Packaged Chocolate

---

## Notebooks

### `recommendation_engine_training.ipynb`

**Purpose:** Train Apriori association rules + compute popularity rankings.

**What it produces:**
- `apriori_recommendations.json` — association rules per product
- `popularity_recommendation.csv` — transaction counts per product

**Apriori parameters** (inferred from output):
- `min_support` — tuned to the dataset size
- `min_confidence` — produces rules with confidence 0.3–0.5+
- Output filtered to keep only menu items (remove noise)

### `firebase_uploader.ipynb`

**Purpose:** Seed the Firebase Realtime Database with product catalog data.

**What it uploads to `products/` node:**
- Product name, category, description, image URL, price, rating
- Used by `productService.ts` on every app load

### `build_index.py` (replaces `build_vector_database.ipynb`)

**Purpose:** Embed product descriptions and write a local ChromaDB index for RAG.

**Flow:**
1. Load product data from `products/products.jsonl` + `fero_cafe_about_us.txt` + `menu_items_text.txt`
2. Embed each document via `sentence-transformers/all-MiniLM-L6-v2` (runs locally)
3. Write to `api/chroma_db/` via ChromaDB `PersistentClient` — no upload, no API key
4. `DetailsAgent` queries this at runtime with `n_results=2`

**Run once:** `cd python_code && python build_index.py` — takes ~30 seconds.

### `prompt_engineering_tutorial.ipynb`

**Purpose:** Development/experimentation notebook for testing and iterating on agent prompts. Not used at runtime.

---

## Firebase Realtime Database

**Used for:** Product catalog (menu items with images, prices, descriptions).

**Access pattern:** Read-only from frontend. Written once via `firebase_uploader.ipynb`.

**Initialization guard:**
```typescript
// config/firebaseConfig.ts
const databaseURL = process.env.EXPO_PUBLIC_FIREBASE_DATABASE_URL;
let fireBaseDB: Database | null = null;
if (databaseURL) {
    // initialize Firebase
}
export { fireBaseDB };
```

If `EXPO_PUBLIC_FIREBASE_DATABASE_URL` is not set, `fireBaseDB` is `null`, and `fetchProducts()` returns `[]`. The app renders with an empty menu — no crash.

---

## ChromaDB Vector Database

**Used for:** DetailsAgent RAG — semantic search over product/shop descriptions.

**Access pattern:** Query-only at runtime. Index built once via `python_code/build_index.py`.

**Query:**
```python
collection.query(query_embeddings=[embedding], n_results=2)
# returns: {"documents": [["chunk1 text", "chunk2 text"]]}
```

Returns 2 nearest document strings, joined and injected into the LLM prompt as context.

**Initialization guard:**
```python
chroma_path = os.getenv("CHROMA_DB_PATH", "api/chroma_db")
self.rag_enabled = os.path.isdir(chroma_path)
# → tries to load collection; gracefully disables on failure
```

Embeddings are generated locally using `sentence-transformers/all-MiniLM-L6-v2` — no external API needed. If `api/chroma_db/` is absent, `rag_enabled = False` and `get_response()` returns a fallback message immediately.

---

## Menu — Current Items

The complete menu as defined in `OrderTakingAgent`'s system prompt (single source of truth for order validation):

| Item | Price | Category |
|---|---|---|
| Cappuccino | $4.50 | Coffee |
| Latte | $4.75 | Coffee |
| Espresso shot | $2.00 | Coffee |
| Dark chocolate (Drinking Chocolate) | $5.00 | Drinking Chocolate |
| Dark chocolate (Packaged Chocolate) | $3.00 | Packaged Chocolate |
| Jumbo Savory Scone | $3.25 | Bakery |
| Cranberry Scone | $3.50 | Bakery |
| Oatmeal Scone | $3.25 | Bakery |
| Ginger Scone | $3.50 | Bakery |
| Chocolate Croissant | $3.75 | Bakery |
| Croissant | $3.25 | Bakery |
| Almond Croissant | $4.00 | Bakery |
| Chocolate Chip Biscotti | $2.50 | Bakery |
| Hazelnut Biscotti | $2.75 | Bakery |
| Ginger Biscotti | $2.50 | Bakery |
| Chocolate syrup | $1.50 | Flavours |
| Hazelnut syrup | $1.50 | Flavours |
| Carmel syrup | $1.50 | Flavours |
| Sugar Free Vanilla syrup | $1.50 | Flavours |

**This menu exists in three separate places:**
1. `OrderTakingAgent` system prompt (hardcoded string) — used for LLM validation
2. Firebase Realtime DB — used by frontend for display
3. `popularity_recommendation.csv` — used for recommendation ranking

**These can drift.** A menu change requires updating all three.
