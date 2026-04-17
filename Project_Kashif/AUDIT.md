# AUDIT.md — automl_legacy Repo Audit
> Step 1 output. Read-only analysis. No code written.

---

## Scoring Key

| Score | Meaning |
|---|---|
| 0 | Missing — not present |
| 1 | Partial — present but incomplete or flawed |
| 2 | Strong — clean, correct, reusable |

**Max per repo: 12**

---

## Repo 1 — AutoFlowML

**Files read:** `src/pipeline.py`, `src/engine.py`, `src/cleaning.py`, `src/processing.py`,
`src/evaluation.py`, `src/utils/logger.py`, `tests/test_full_pipeline.py`, `config.yaml`

### Criterion Scores

| Criterion | Score | Evidence |
|---|---|---|
| sklearn Pipeline objects | **2** | `PipelineArchitect.build_pipeline()` returns a true `Pipeline(cleaning, processing, model)`. Cleaning is itself a nested `Pipeline` of three custom transformers. `AutoDFColumnTransformer` subclasses `ColumnTransformer` with pandas output enforced via `set_output(transform="pandas")`. Every step is clone-safe. |
| Working CV strategy | **2** | `CrossValidator.run_cv()` in `evaluation.py` uses `StratifiedKFold`. For regression it bins the target with `pd.qcut` before splitting — correct approach. Critically, it calls `clone(pipeline)` and re-fits the **full** pipeline on each fold, so preprocessing is never fit on held-out data. No leakage. |
| Handles mixed dtypes | **2** | `AutoDFColumnTransformer` dispatches via `make_column_selector(dtype_include=['number'])` and `make_column_selector(dtype_exclude=['number'])`. `CardinalityStripper`, `VarianceStripper`, `UniversalDropper` all operate on mixed-dtype DataFrames. `TargetEncodedModelWrapper` handles label encoding internally. |
| Modular code | **2** | Clean single-responsibility split: `cleaning.py` (drop transformers), `processing.py` (encode/scale transformers + wrapper), `pipeline.py` (assembly), `engine.py` (task detection + model registry), `evaluation.py` (metrics + CV + leaderboard), `utils/` (logger, config). Six test files covering each module. |
| Clean injection points | **2** | `build_pipeline(model_instance, task_type)` accepts any model — swap the model without touching preprocessing. The `processing` step is a standalone `ColumnTransformer`; an LLM FE step that returns a DataFrame can be inserted between `cleaning` and `processing` as a named pipeline step. `TargetEncodedModelWrapper` is a transparent proxy that exposes `feature_importances_` and `predict_proba` through `__getattr__`. |
| Code quality | **2** | Full type hints throughout. All custom transformers inherit from `BaseEstimator` and `TransformerMixin` and call `check_is_fitted`. Structured logger via `utils/logger.py`. YAML-driven config. Docstrings on all public methods. No notebooks, no flat scripts. |

**Total: 12 / 12**

### Notes
- `main.py` is a stub (`print("Hello from autoflowml!")`), but the actual entry point is the `LeaderboardEngine` in `evaluation.py` — this is intentional library design.
- The `config.yaml` makes cleaning thresholds and model selection fully configurable without touching code — ideal for a `kashif_core` port.

---

## Repo 2 — AutoML

**Files read:** `src/data_processing/preprocessing_pipeline.py`,
`src/data_processing/task_detector.py`, `src/models/registry.py`,
`src/models/trainers/classification.py`, `main_pipeline.py`, `Config/config.py`

### Criterion Scores

| Criterion | Score | Evidence |
|---|---|---|
| sklearn Pipeline objects | **1** | `PreprocessingPipeline` uses a `ColumnTransformer` internally but is itself a custom class — not a sklearn `Pipeline`. The `AutoMLPipeline` orchestrator calls `preprocessor.fit_transform()` then passes numpy arrays to `ClassificationTrainer`. Preprocessing and model are never joined into a single `Pipeline` object, so `clone()` and cross-validating the full pipeline is not possible without restructuring. |
| Working CV strategy | **1** | `ClassificationTrainer.train_model()` calls `cross_val_score(model, X_train_processed, y_train_encoded, cv=cv_folds, scoring='accuracy')`. CV runs on the already-preprocessed array — preprocessing was fit on all training data before the CV loop, which is data leakage. Also: the model is fit on `y_train` (raw labels) at line 144 but metrics are computed against `y_train_encoded` — an inconsistency. |
| Handles mixed dtypes | **2** | `PreprocessingPipeline` is thorough: boolean conversion, ID-column detection (>95% unique → drop), high-cardinality → custom `FrequencyEncoder`, low-cardinality → OHE, numeric → impute + scale. Feature tracking attributes (`numeric_features_`, `low_card_categorical_`, etc.) are populated on fit and inspectable. |
| Modular code | **2** | Excellent package layout: `src/data_processing/` (loader, validator, task_detector, preprocessing_pipeline, splitting), `src/models/` (registry, trainers/classification, trainers/regression, hyperparameter_tuning_setup, final_evaluation), `src/visualizations/`, `src/utils/`. `ModelInfo` dataclass stores per-model metadata (complexity, requires_scaling, handles_missing). Comprehensive test suite across all sub-packages. |
| Clean injection points | **1** | FE can be inserted between `run_preprocessing()` and `train_models()` inside `AutoMLPipeline` — `self.X_processed` is the mutation point. This is workable but inelegant: it is an imperative mutation of state rather than a composable pipeline step. An LLM FE transform would have to return a numpy array of matching shape or the downstream trainer breaks. |
| Code quality | **2** | Comprehensive docstrings explaining the "why". `ModelRegistry` with rich `ModelInfo` metadata is exemplary design. Type hints, dataclasses, logging with level control. `sys.path.insert` hacks in every file are a structural smell but a known pattern for this repo layout. |

**Total: 9 / 12**

### Notes
- The `TaskDetector` is the strongest single component in any of the three repos: 6 heuristic rules with weighted voting, confidence scoring, and a `get_detection_details()` debug method. Worth borrowing directly.
- The `ModelRegistry` with `ModelInfo` (strengths, weaknesses, complexity, requires_scaling) is a well-thought-out abstraction worth porting.
- The leakage in CV and the `y_train` vs `y_train_encoded` inconsistency in `classification.py:144` must be fixed if any code is ported.

---

## Repo 3 — -Auto-ML-Studio

**Files read:** `app.py`, `data_utils.py`, `model_utils.py`, `config.py`

### Criterion Scores

| Criterion | Score | Evidence |
|---|---|---|
| sklearn Pipeline objects | **1** | `preprocess_data()` in `data_utils.py` builds a `ColumnTransformer` with nested `Pipeline` steps per dtype (impute → outlier cap → scale for numeric; OHE for categorical). However, the model is trained entirely outside any Pipeline — `model.fit(X_train, y_train)` on raw processed arrays. No full end-to-end Pipeline exists. |
| Working CV strategy | **1** | `cross_val_score(model, X_train, y_train, cv=3, ...)` is called inside `evaluate_model_advanced()` — only 3 folds (low-variance estimate), runs after preprocessing (same leakage issue as AutoML). `RandomizedSearchCV(cv=3)` used in tuning. Minimal but present. |
| Handles mixed dtypes | **1** | `preprocess_data()` routes numeric and categorical into separate `ColumnTransformer` branches. High-cardinality "handling" is a hard drop in `split_and_save_data()` — any categorical column with >50 unique values is dropped before preprocessing. This discards potentially useful features silently rather than encoding them. |
| Modular code | **1** | Code is split across `app.py`, `data_utils.py`, `model_utils.py`, `plot_utils.py` — functional decomposition by concern. All files are flat function collections; no classes. No tests at all. A Jupyter notebook (`website_SAIR.ipynb`) is present in the repo root. The split is better than a monolith but far from injectable modules. |
| Clean injection points | **0** | The flow is: CSV → `preprocess_data()` → numpy arrays → `train_models_pipeline()`. Everything passes as positional arrays through Gradio state. There is no composable structure and no named step where an LLM FE transform could be inserted without rewriting the entire data flow. |
| Code quality | **1** | Readable flat code. No type hints. Minimal docstrings. `print()` instead of logging. MLflow integration is bolted on inside training loops. The `app.py` output mapping for `split_btn.click` is self-described as incorrect in a comment on line 63. Magic numbers throughout (`cv=3`, `n_iter=10`). |

**Total: 5 / 12**

### Notes
- The `OutlierHandler` (IQR capping, sklearn-compatible) in `data_utils.py` is a clean transformer worth noting — but not unique enough to borrow exclusively.
- MLflow integration exists but is entangled with Gradio UI logic — not reusable as-is.
- No CLI, no tests, one notebook: this is a demo/prototype, not a library.

---

## Ranked Recommendation Table

| Rank | Repo | Score | Verdict | Role in kashif_core |
|---|---|---|---|---|
| **1** | **AutoFlowML** | **12 / 12** | **Base repo** | Port `pipeline.py`, `cleaning.py`, `processing.py`, `evaluation.py` as the skeleton of `trainer.py`. `CrossValidator` becomes the CV engine. `PipelineArchitect` is the natural injection point for the LLM FE step. |
| **2** | **AutoML** | **9 / 12** | **Borrow parts** | Port `TaskDetector` verbatim into `profiler.py`. Port `ModelRegistry` / `ModelInfo` pattern into `trainer.py`. Fix the `y_train` / `y_train_encoded` inconsistency before use. |
| **3** | **-Auto-ML-Studio** | **5 / 12** | **Reference only** | Do not port code. Study Gradio UI patterns for a later UI phase. `OutlierHandler` can inspire a cleaning step if IQR capping is desired. |

---

## Key Findings for Step 2

1. **AutoFlowML's `CrossValidator.run_cv()` is the correct CV pattern** — clone the full pipeline, re-fit on each fold, no leakage. This must be the CV engine in `kashif_core`.

2. **The natural LLM FE injection point** exists between the `cleaning` and `processing` steps in AutoFlowML's pipeline. An LLM-generated feature transform returns a DataFrame; it inserts as `Pipeline(cleaning → fe_transform → processing → model)` with no changes to surrounding steps.

3. **AutoML's `TaskDetector`** (6-rule weighted voting with confidence score) is the best task detection component in the set and should port to `kashif_core/core/profiler.py` with minimal changes.

4. **AutoML's `ModelRegistry` + `ModelInfo`** (requires_scaling, handles_missing, complexity) is the right abstraction for model management in `trainer.py`.

5. **None of the three repos have a profiler module** (dtypes, null rates, cardinality, skew, target distribution as JSON) — `kashif_core/core/profiler.py` must be written from scratch.

6. **None of the three repos have an executor module** (sandboxed code execution, error catching, fallback) — `kashif_core/core/executor.py` must be written from scratch.
