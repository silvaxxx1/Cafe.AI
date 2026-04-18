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
            → product descriptions embedded → Pinecone index (read by DetailsAgent)
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

### `build_vector_database.ipynb`

**Purpose:** Embed product descriptions and upload vectors to Pinecone for RAG.

**Flow:**
1. Load product data (descriptions, FAQs, or menu details)
2. Split into chunks
3. Embed each chunk via an embedding model (Ollama `nomic-embed-text` or RunPod endpoint)
4. Upsert into Pinecone index, namespace `"ns1"`, with `text` metadata field
5. `DetailsAgent` queries this at runtime with `top_k=2`

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

## Pinecone Vector Database

**Used for:** DetailsAgent RAG — semantic search over product/shop descriptions.

**Access pattern:** Query-only at runtime. Index built once via `build_vector_database.ipynb`.

**Query:**
```python
index.query(
    namespace="ns1",
    vector=embedding,
    top_k=2,
    include_values=False,
    include_metadata=True
)
```

Returns 2 nearest chunks. Their `metadata["text"]` fields are joined and injected into the LLM prompt as context.

**Initialization guard:**
```python
pinecone_key  = os.getenv("PINECONE_API_KEY")
self.rag_enabled = bool(pinecone_key)
```

Embeddings are generated locally using `sentence-transformers/all-MiniLM-L6-v2` — no external embedding URL needed. If `PINECONE_API_KEY` is missing, `rag_enabled = False` and `get_response()` returns a fallback message immediately.

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
