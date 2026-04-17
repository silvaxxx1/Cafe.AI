# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What this repo is

Kashif is a tabular ML agent that wraps a static AutoML pipeline (sklearn) with an LLM-powered feature engineering loop. The LLM writes feature engineering code; a sandboxed executor runs it; cross-validation scores decide what to keep. Everything else — preprocessing, model training, evaluation — is deterministic code.

**Read these documents before doing any work:**
- `BRIEF.md` — the constitution. Contains hard rules, the full build order, and the LLM provider design.
- `AUDIT.md` — audit of the three legacy repos in `automl_legacy/`.
- `HYBRID_PLAN.md` — the porting plan: what comes from where, the injection point, module contracts.
- `AUTORESEARCH_NOTES.md` — analysis of Karpathy's autoresearch loop and how it maps to Kashif.

---

## Hard rules (from BRIEF.md)

- **Never modify** anything inside `automl_legacy/` or `autoresearch/` — read-only forever.
- **All code lives in `kashif_core/`** — no exceptions.
- **Build one module at a time.** Each module needs a passing test before the next module starts.
- **Use uv for everything.** No pip, no conda, no manual venv.
- **`fe_agent.py` must never import a provider SDK directly** — only imports `BaseLLM` from `core/llm/base.py`.
- **No hardcoded API keys** — always read from environment variables named in `config.yaml`.

---

## Environment setup (run once from `kashif_core/`)

```bash
cd kashif_core
uv init
uv add scikit-learn pandas numpy shap typer openai anthropic pytest
```

---

## Common commands (all from `kashif_core/`)

```bash
# Run all tests
uv run pytest tests/

# Run a single test file
uv run pytest tests/test_trainer.py -v

# Run a single test by name
uv run pytest tests/test_trainer.py::test_classification_pipeline -v

# Run the CLI
uv run python -m cli.main run --csv data.csv --target col_name
uv run python -m cli.main run --csv data.csv --target col_name --no-agent
uv run python -m cli.main run --csv data.csv --target col_name --llm groq
uv run python -m cli.main run --csv data.csv --target col_name --llm anthropic

# Add a dependency
uv add <package-name>
```

---

## Architecture

### Module contracts

All modules live in `kashif_core/core/`. Modules only import downward in this order:

```
profiler.py     IN: raw DataFrame + target col
                OUT: profile_json dict (dtypes, null_rates, cardinality, skew,
                     target_dist, task_type, confidence)

trainer.py      IN: DataFrame + target series + optional fe_step (sklearn transformer)
                OUT: cv_score, oof_preds, SHAP dict, model .pkl path

executor.py     IN: fe_code string + DataFrame
                OUT: (transformed_df, error_or_none)
                RULE: imports nothing from kashif_core — fully isolated

core/llm/
  base.py       Abstract BaseLLM with one method: complete(prompt: str) -> str
  groq.py       GroqLLM(BaseLLM) — openai SDK + Groq base_url — DEFAULT provider
  anthropic.py  AnthropicLLM(BaseLLM) — anthropic SDK — secondary
  ollama.py     OllamaLLM(BaseLLM) — local inference — built later

fe_agent.py     IN: profile_json + program.md text + experiment_log
                OUT: fe_code string
                RULE: imports BaseLLM only, resolved at runtime from config.yaml

reporter.py     IN: experiment_log (list of round dicts)
                OUT: markdown report string

cli/main.py     Typer CLI — wires all core modules, emits JSON output contract
```

`executor.py` and `core/llm/` adapters import nothing from kashif_core — hard isolation rule.

### The FE injection point

`trainer.py` builds an sklearn `Pipeline` from AutoFlowML's architecture:

```
Round 0 (baseline):  Pipeline(cleaning → processing → model)
Round N (with FE):   Pipeline(cleaning → fe_transform → processing → model)
```

`fe_transform` is a sklearn `BaseEstimator + TransformerMixin` that wraps `executor.py`. Because it lives inside the Pipeline, `CrossValidator.run_cv()` clones and re-fits the **full chain** (including FE) on each CV fold — no leakage. This is the central design invariant of the system.

### LLM provider selection

Provider is resolved from `config.yaml`, never hardcoded:

```yaml
llm:
  provider: groq                    # groq | anthropic | ollama
  model: llama-3.3-70b-versatile
  api_key_env: GROQ_API_KEY         # env var name, not the key itself
  temperature: 0.2
```

`fe_agent.py` only ever holds a `BaseLLM` reference. `cli/main.py` reads the config, instantiates the correct adapter, and passes it in.

Required env vars:
```bash
GROQ_API_KEY=...          # default provider
ANTHROPIC_API_KEY=...     # if provider: anthropic
```

### The reflection prompt structure

On every round after round 0, the LLM receives:
```
ORIGINAL SCHEMA        — raw column list from profiler, never changes
PROGRAM.MD DIRECTIVE   — user's domain hints (edit kashif_core/program.md)
ALL PREVIOUS ROUNDS    — fe_code + cv_score + SHAP + errors per round
CURRENT RESULTS        — SHAP values, dead features, failed columns from last round
TASK                   — write improved engineer_features(df) -> df, no explanation
```

### Stopping conditions (in fe_agent.py)

The loop stops when any of these is true:
- `delta < 0.005` — CV improvement less than 0.5% over previous best
- `max_rounds` reached (set in `config.yaml` and `program.md`)
- LLM returns no new angles to try

### JSON output contract

Every run returns this structure (CLI prints it, API returns it):
```json
{
  "status": "complete",
  "best_round": 3,
  "cv_score": 0.891,
  "baseline_score": 0.821,
  "delta": 0.070,
  "model_path": "./outputs/best_model.pkl",
  "feature_schema": "./outputs/feature_schema.json",
  "top_features": ["feature_a", "feature_b"],
  "dead_features": ["col_x", "col_y"],
  "rounds": [{"round": 1, "cv_score": 0.841, "fe_code": "...", "top_features": []}],
  "report_path": "./outputs/report.md"
}
```

---

## Build order (Step 4 from BRIEF.md)

Each step requires a passing test before proceeding. Do not skip ahead.

```
4a. trainer.py      — port AutoFlowML cleaning/processing/evaluation + AutoML ModelRegistry
4b. profiler.py     — port AutoML TaskDetector + write JSON profiling wrapper
4c. executor.py     — write from scratch, fully isolated
4d. core/llm/       — base.py (abstract) + groq.py (default) + anthropic.py (secondary)
4e. fe_agent.py     — LLM loop, imports BaseLLM only
4f. reporter.py     — markdown from experiment_log
4g. cli/main.py     — typer CLI, --csv --target --rounds --no-agent --llm
```

### What to port from legacy (do not rewrite what already works)

| From | To | Notes |
|---|---|---|
| `automl_legacy/AutoFlowML/src/cleaning.py` | `trainer.py` | Port verbatim: `VarianceStripper`, `UniversalDropper`. `CardinalityStripper` ported with fix — see bug note below. |
| `automl_legacy/AutoFlowML/src/processing.py` | `trainer.py` | Port verbatim: transformers + `AutoDFColumnTransformer` + `TargetEncodedModelWrapper` |
| `automl_legacy/AutoFlowML/src/evaluation.py` | `trainer.py` | Port verbatim: `CrossValidator.run_cv()` is the crown jewel — do not modify |
| `automl_legacy/AutoFlowML/src/pipeline.py` | `trainer.py` | Port + add optional `fe_step` param to `build_pipeline()` |
| `automl_legacy/AutoML/src/data_processing/task_detector.py` | `profiler.py` | Port verbatim: 6-rule weighted-voting `TaskDetector` |
| `automl_legacy/AutoML/src/models/registry.py` | `trainer.py` | Port `ModelInfo` dataclass + `ModelRegistry`; remove `sys.path.insert` hacks |

**Do not port** from `-Auto-ML-Studio` — reference only.

### Known bugs

**AutoML — classification.py:144 (avoided by architecture)**
`automl_legacy/AutoML/src/models/trainers/classification.py:144` fits the model on `y_train` (raw labels) but computes metrics against `y_train_encoded`. This pattern is not ported — `TargetEncodedModelWrapper` from AutoFlowML handles label encoding inside the pipeline, making the issue moot.

**AutoFlowML — CardinalityStripper (fixed in trainer.py)**
`CardinalityStripper.fit()` in the original applies `nunique() / n_rows` to every column regardless of dtype. For continuous `float` columns (e.g. all features in a regression dataset), this ratio is ~1.0 so all numeric features get dropped. Fix in `kashif_core/core/trainer.py`: skip `float` dtype columns — cardinality stripping only makes sense for string/integer ID-like columns.

---

## User-facing configuration

`kashif_core/program.md` is the user's domain directive — not code, not loop mechanics. Edit it to inject domain knowledge into every LLM prompt:
- Problem statement and what the target means
- Column descriptions (the LLM only sees names + statistics)
- Columns to exclude from FE (leakage prevention)
- Domain-specific transformation hints
- Evaluation priority (e.g., "recall matters more than precision here")

`kashif_core/config.yaml` controls: LLM provider/model/api_key_env, CV folds, cleaning thresholds, model selection, and fe_agent max_rounds/delta_threshold.

## Current build status

**Step 4 complete — all modules built and tested.**

| Module | Status |
|---|---|
| 4a trainer.py | complete — 34/34 tests passing |
| 4b profiler.py | complete — 34/34 tests passing |
| 4c executor.py | complete — 38/38 tests passing |
| 4d core/llm/ | complete — 29/29 tests passing |
| 4e fe_agent.py | complete — 36/36 tests passing |
| 4f reporter.py | complete — 42/42 tests passing |
| 4g cli/main.py | complete — 25/25 tests passing |

Update this table as each module's test passes.