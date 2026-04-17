# HYBRID_PLAN.md — kashif_core Build Plan
> Step 2 output. No code written. Awaiting human approval before Step 3.

---

## Base Repo

**AutoFlowML** is the base.
Its `Pipeline(cleaning → processing → model)` architecture, clone-safe CV, and sklearn-native
transformer design are the structural skeleton of `kashif_core/core/trainer.py`.
Everything else is assembled around it.

---

## Source Map — What Comes From Where

### From AutoFlowML (base, port with minimal changes)

| Source file | Destination | What changes |
|---|---|---|
| `src/cleaning.py` | `trainer.py` — cleaning block | None. `VarianceStripper`, `UniversalDropper`, `CardinalityStripper` port verbatim. |
| `src/processing.py` | `trainer.py` — processing block | None. `get_numeric_transformer()`, `get_categorical_transformer()`, `AutoDFColumnTransformer`, `TargetEncodedModelWrapper` port verbatim. |
| `src/evaluation.py` | `trainer.py` — CV block | `CrossValidator.run_cv()` ports verbatim — this is the crown jewel (full pipeline clone per fold, no leakage). `ModelEvaluator` ports verbatim. `LeaderboardEngine` is adapted to return a structured dict instead of a DataFrame (feeds the JSON output contract). |
| `src/pipeline.py` | `trainer.py` — assembly | `PipelineArchitect.build_pipeline()` gains an optional `fe_step` parameter. When provided, the pipeline becomes `cleaning → fe_transform → processing → model`. When absent, it falls back to the original three-step form. No other changes. |
| `src/utils/logger.py` | `kashif_core/utils/logger.py` | None. |
| `src/utils/config_loader.py` | `kashif_core/utils/config_loader.py` | None. `ConfigNode` (YAML → dotted-access dict) is useful as-is. |
| `config.yaml` | `kashif_core/config.yaml` | Add `fe_agent` section (max_rounds, delta_threshold) and `llm` section (provider, model, api_key_env, temperature). Existing cleaning/settings/model_selection/evaluation keys kept. |

### From AutoML (borrow, targeted extraction)

| Source file | Destination | What changes |
|---|---|---|
| `src/data_processing/task_detector.py` — `TaskDetector` class | `profiler.py` — task detection block | Port the 6-rule weighted-voting class verbatim. Wrap it inside `profiler.run()` so it returns its result as part of the profile JSON rather than as a standalone call. |
| `src/models/registry.py` — `ModelInfo` dataclass + `ModelRegistry` class | `trainer.py` — model management block | Replace AutoFlowML's flat `MODEL_REGISTRY` dict with AutoML's richer `ModelInfo` + `ModelRegistry` pattern (adds `requires_scaling`, `handles_missing`, `complexity` metadata). Remove `sys.path.insert` hacks. Fix: use a single `random_state` source from `config.yaml` throughout. |
| `src/models/trainers/classification.py` — label encoding logic | `trainer.py` — `TargetEncodedModelWrapper` | AutoFlowML's wrapper already handles this cleanly. The AutoML trainer's label encoding is NOT ported — the wrapper approach is superior. This entry is here to confirm the AutoML trainer is explicitly discarded. |

**Explicitly NOT ported from AutoML:**
- `PreprocessingPipeline` — AutoFlowML's `AutoDFColumnTransformer` + cleaning block is superior (full Pipeline, no leakage)
- `ClassificationTrainer` / `RegressionTrainer` — replaced by `CrossValidator` from AutoFlowML
- `DataLoader`, `DataValidator`, `DataSplitter` — one-liners in `trainer.py`, no class needed
- All visualizations — not in kashif_core scope
- `mlflow_setup` — not in kashif_core scope

### Written from scratch

| Module | Reason nothing is borrowed |
|---|---|
| `profiler.py` (partial) | No repo has a structured profiling → JSON function. TaskDetector is borrowed; the profiling wrapper (dtypes, null rates, cardinality, skew, target distribution) is new. |
| `executor.py` | Not present in any repo. Safe `exec()` sandbox, full exception catch, fallback to original df. |
| `core/llm/base.py` | Not present in any repo. Abstract `BaseLLM` interface — the only LLM type `fe_agent.py` is allowed to import. |
| `core/llm/groq.py` | Not present in any repo. Groq adapter via `openai` SDK pointed at Groq base URL — default provider (fastest, cheapest, llama-3.3-70b-versatile). |
| `core/llm/anthropic.py` | Not present in any repo. Anthropic adapter via `anthropic` SDK — secondary provider. |
| `core/llm/ollama.py` | Not present in any repo. Local model adapter — built later for private deployments. |
| `fe_agent.py` | Not present in any repo. Imports `BaseLLM` only — never a provider SDK directly. Provider loaded from `config.yaml`. Karpathy reflection loop. Designed in Step 3. |
| `reporter.py` | Not present in any repo. Reads `experiment_log` JSON, produces markdown. |
| `cli/main.py` | Not present in any repo (AutoFlowML's `main.py` is a stub). Typer CLI with `kashif run` and `--llm` provider override flag. |

---

## The Injection Point — How FE Slots In

AutoFlowML's pipeline currently reads:

```
Pipeline([
    ("cleaning",    cleaning_step),
    ("processing",  processing_step),
    ("model",       wrapped_model)
])
```

Kashif extends `PipelineArchitect.build_pipeline()` to accept an optional `fe_step`:

```
Pipeline([
    ("cleaning",      cleaning_step),
    ("fe_transform",  fe_step),        # ← LLM FE lands here, optional
    ("processing",    processing_step),
    ("model",         wrapped_model)
])
```

`fe_step` is a sklearn-compatible `BaseEstimator + TransformerMixin` that wraps `executor.py`.
On `transform()` it calls `executor.execute(fe_code, df)`.
On failure it returns the original df untouched (executor's own fallback).
On `fit()` it does nothing — all learning happens inside executor at transform time.

Because it sits inside the sklearn `Pipeline`, `CrossValidator.run_cv()` calls `clone(pipeline)`
and re-fits the full chain (cleaning → FE → processing → model) on each fold independently.
No leakage. No special-casing.

Round 0 uses the three-step pipeline (no FE, baseline CV score).
Rounds 1..N inject progressively improved FE steps.

---

## Clean Module Boundaries

```
kashif_core/core/
├── profiler.py      IN:  raw DataFrame, target column name
│                    OUT: profile_json (dtypes, null_rates, cardinality,
│                         skew, target_dist, task_type, confidence)
│                    DEPS: pandas, numpy, AutoML TaskDetector
│
├── trainer.py       IN:  DataFrame, target series, fe_step (optional)
│                    OUT: cv_score (float), oof_preds, SHAP dict,
│                         best_model.pkl path, feature_names
│                    DEPS: sklearn, xgboost, lgbm, shap,
│                          AutoFlowML cleaning/processing/evaluation,
│                          AutoML ModelRegistry/ModelInfo
│
├── executor.py      IN:  fe_code (str), DataFrame
│                    OUT: (transformed_df, error_or_none)
│                    DEPS: pandas, numpy only — imports NOTHING from kashif_core
│
├── llm/
│   ├── base.py      Abstract BaseLLM with single method: complete(prompt) -> str
│   │                DEPS: abc only
│   ├── groq.py      GroqLLM(BaseLLM) — openai SDK, Groq base_url, default provider
│   │                DEPS: openai SDK, base.py
│   ├── anthropic.py AnthropicLLM(BaseLLM) — anthropic SDK, secondary provider
│   │                DEPS: anthropic SDK, base.py
│   └── ollama.py    OllamaLLM(BaseLLM) — local inference, built later
│                    DEPS: openai SDK (Ollama is OpenAI-compatible), base.py
│
├── fe_agent.py      IN:  profile_json, program.md text,
│                         experiment_log (list of round dicts)
│                    OUT: fe_code (str)
│                    DEPS: BaseLLM only (never a provider SDK) + executor.py
│                    NOTE: provider resolved at runtime from config.yaml
│
└── reporter.py      IN:  experiment_log (list of round dicts)
                     OUT: markdown string (written to outputs/report.md)
                     DEPS: none beyond stdlib

kashif_core/cli/
└── main.py          IN:  CLI args (--csv, --target, --rounds, --no-agent, --llm)
                     OUT: JSON to stdout, files to outputs/
                     DEPS: typer, all core modules
```

**Dependency rule:** modules only import downward in the list above.
`fe_agent.py` imports `BaseLLM` and `executor.py`. Nothing imports `fe_agent.py` except `cli/main.py`.
`executor.py` imports nothing from kashif_core — isolation is mandatory for the sandbox.
`core/llm/*.py` adapters import nothing from kashif_core — only their provider SDK and `base.py`.
API keys are never hardcoded — always read from environment variables named in `config.yaml`.

---

## What Gets Rewritten (vs Ported)

| Component | Decision | Reason |
|---|---|---|
| `VarianceStripper`, `UniversalDropper` | Port verbatim | Correct sklearn API, no bugs found |
| `CardinalityStripper` | Port + fix | Bug found during 4a testing: original applies uniqueness ratio to ALL dtypes including continuous floats, dropping every numeric column in regression datasets. Fix: skip `float` dtype columns — cardinality check is only meaningful for string/integer ID-like columns. |
| `AutoDFColumnTransformer` | Port verbatim | Best mixed-dtype dispatch in the set |
| `TargetEncodedModelWrapper` | Port verbatim | Clean proxy, exposes `feature_importances_`, avoids the AutoML label encoding bug |
| `CrossValidator.run_cv()` | Port verbatim | Only correct full-pipeline CV in the set — do not modify |
| `ModelEvaluator` | Port verbatim | Clean metric dispatch dict |
| `PipelineArchitect.build_pipeline()` | Port + add `fe_step` param | One new parameter, no structural changes |
| `LeaderboardEngine` | Adapt | Return structured dict instead of DataFrame to satisfy JSON contract |
| `TaskDetector` (AutoML) | Port verbatim | Best task detection in the set |
| `ModelRegistry + ModelInfo` (AutoML) | Port, remove path hacks | Richer metadata than AutoFlowML's dict; remove `sys.path.insert` |
| Profiling wrapper (null rates, skew etc.) | Written from scratch ✓ | Not present anywhere |
| `executor.py` | Written from scratch ✓ | Safe exec sandbox, SIGALRM timeout, restricted import whitelist |
| `core/llm/base.py` | Written from scratch ✓ | Abstract BaseLLM + LLMError; fe_agent.py holds this type only |
| `core/llm/groq.py` | Written from scratch ✓ | openai SDK + Groq base URL, lazy client, env-var key |
| `core/llm/anthropic.py` | Written from scratch ✓ | anthropic SDK, lazy client, content block extraction |
| `fe_agent.py` | Written from scratch ✓ | FETransformer (sklearn step), reflection loop, stall stopping |
| `reporter.py` | Write from scratch | Not present anywhere ← NEXT |
| `cli/main.py` | Write from scratch | AutoFlowML stub is not usable |

---

## Bugs Found and Fixed During Step 4a

### AutoFlowML — CardinalityStripper (cleaning.py)

**Bug:** `CardinalityStripper.fit()` computes `nunique() / n_rows` for every column regardless of dtype. Continuous `float` columns generated by `rng.normal()` have ~100% unique values, so all numeric features are dropped in regression datasets.

**Fix in kashif_core:** Skip `float` dtype columns in the uniqueness check. Cardinality stripping is only meaningful for object/integer ID-like columns (names, user IDs, codes). Continuous features are never high-cardinality IDs.

**Location:** `kashif_core/core/trainer.py` — `CardinalityStripper.fit()`

---

## Bug to Fix Before Porting (AutoML)

**File:** `AutoML/src/models/trainers/classification.py`, line 144

```python
# Bug: model fit on raw y_train, metrics computed against y_train_encoded
model.fit(X_train_processed, y_train)          # ← raw labels
y_train_pred = model.predict(X_train_processed)
result.train_accuracy = accuracy_score(y_train_encoded, y_train_pred)  # ← encoded
```

**Fix in kashif_core:** This entire training pattern is NOT ported.
`TargetEncodedModelWrapper` from AutoFlowML handles label encoding internally during `fit()`,
so the outer trainer never sees raw vs encoded label inconsistency.
The bug is resolved by architecture, not by patching the buggy code.

---

## ASCII Data Flow Diagram

```
  data.csv
      │
      ▼
┌─────────────────────────────────────────────────┐
│  cli/main.py  (typer)                           │
│  kashif run --csv data.csv --target col         │
└────────────────────┬────────────────────────────┘
                     │ raw DataFrame + target
                     ▼
┌─────────────────────────────────────────────────┐
│  profiler.py                                    │
│  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ TaskDetector │  │ column stats scan        │  │
│  │ (6-rule vote)│  │ dtypes, nulls, cardin.,  │  │
│  │  from AutoML │  │ skew, target_dist        │  │
│  └──────────────┘  └─────────────────────────┘  │
└────────────────────┬────────────────────────────┘
                     │ profile_json + task_type
                     │
                     ├──────────────────────────────────────────────┐
                     │                                              │
                     ▼                                              │ profile_json
          ┌──────────────────┐                                      │ + program.md
          │  Round 0         │                                      │ + experiment_log
          │  (no FE, baseline)                                      │
          │                  │                                      ▼
          │  trainer.py      │                           ┌─────────────────────┐
          │  Pipeline:       │                           │  fe_agent.py        │
          │  cleaning ───────►                           │  (LLM call via      │
          │  processing ─────►                           │   BaseLLM adapter)  │
          │  model ──────────►                           │  writes fe_code str │
          │                  │                           └──────────┬──────────┘
          │  CrossValidator  │                                      │ fe_code (str)
          │  StratifiedKFold │                                      ▼
          │  clone(pipeline) │                           ┌─────────────────────┐
          │  per fold        │                           │  executor.py        │
          └────────┬─────────┘                           │  exec(fe_code, df)  │
                   │                                     │  catch ALL errors   │
                   │ baseline_cv_score                   │  fallback = orig df │
                   │ + SHAP values                       └──────────┬──────────┘
                   │                                                │ transformed_df
                   │                                                │ (or orig on fail)
                   │                                                ▼
                   │                                     ┌─────────────────────┐
                   │                            Round N  │  trainer.py         │
                   │                                     │  Pipeline:          │
                   │                                     │  cleaning ──────────►
                   │                                     │  fe_transform ──────►  ← injection
                   │                                     │  processing ────────►
                   │                                     │  model ─────────────►
                   │                                     │                     │
                   │                                     │  CrossValidator     │
                   │                                     │  clone(full pipe)   │
                   │                                     │  per fold           │
                   │                                     └──────────┬──────────┘
                   │                                                │
                   │                                                │ cv_score_N
                   │                                                │ SHAP_N
                   │                                                │
                   │           ┌───────────────────────────────────┘
                   │           │
                   │           │  delta = cv_score_N - cv_score_N-1
                   │           │
                   │           ├── delta < 0.005 ──┐
                   │           │   OR max_rounds   │
                   │           │   OR no new angles│
                   │           │                   │  loop back → fe_agent.py
                   │           │                   │  with updated experiment_log
                   │           │                   │  (all prev fe_codes + scores
                   │           │                   │   + SHAP + dead features)
                   │           │                   │
                   │           ▼ (stopping met)    │
                   │  ┌──────────────────┐         │
                   │  │  experiment_log  │◄────────┘
                   │  │  (all rounds)    │
                   │  └────────┬─────────┘
                   │           │
                   └───────────┤ best round selected
                               │ (highest cv_score)
                               ▼
                   ┌─────────────────────────────────┐
                   │  reporter.py                    │
                   │  reads experiment_log           │
                   │  - score progression table      │
                   │  - top features per round       │
                   │  - fe_code that worked          │
                   │  - final recommendation         │
                   │  writes outputs/report.md       │
                   └────────────┬────────────────────┘
                                │
                                ▼
                   ┌─────────────────────────────────┐
                   │  cli/main.py                    │
                   │  prints JSON:                   │
                   │  {                              │
                   │    status, best_round,          │
                   │    cv_score, baseline_score,    │
                   │    delta, model_path,           │
                   │    feature_schema,              │
                   │    top_features, dead_features, │
                   │    rounds: [...],               │
                   │    report_path                  │
                   │  }                              │
                   └─────────────────────────────────┘
```

---

## Build Order (Step 4 sequence)

Follows BRIEF.md exactly. Each module must have a passing test before the next starts.

```
4a. trainer.py          — static pipeline, no FE step yet               ✓ COMPLETE (34/34)
                          test: test_trainer.py runs on one real CSV

4b. profiler.py         — JSON schema + task detection                   ✓ COMPLETE (34/34)
                          test: test_profiler.py on synthetic DataFrames

4c. executor.py         — sandboxed exec, fallback                       ✓ COMPLETE (38/38)
                          test: test_executor.py including deliberate bad code

4d. core/llm/ layer     — provider-agnostic LLM adapter                  ✓ COMPLETE (29/29)
                          base.py (abstract BaseLLM)
                          groq.py (default — openai SDK + Groq base_url)
                          anthropic.py (secondary — anthropic SDK)
                          Provider + api_key_env loaded from config.yaml
                          test: test_llm.py with mock completions

4e. fe_agent.py         — LLM + reflection loop                          ✓ COMPLETE (36/36)
                          imports BaseLLM only, never a provider SDK
                          test: test_fe_agent.py with mock LLM

4f. reporter.py         — markdown from experiment_log                   ← NEXT
                          test: test_reporter.py

4g. cli/main.py         — typer CLI wires everything together
                          kashif run --csv --target --rounds --no-agent --llm
                          test: manual golden-path run on 3 CSVs
```

`trainer.py` (4a) is intentionally built first without the `fe_step` injection.
The injection point is wired in 4e when `fe_agent.py` exists to provide it.
The `--no-agent` CLI flag falls back to the three-step pipeline at any point.
The `--llm` CLI flag overrides the `provider` key in `config.yaml` for that run.
