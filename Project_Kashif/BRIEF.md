# Kashif — Claude Code Brief
> كاشف — the uncoverer

## What is Kashif
Kashif is a data science agent that wraps a robust static AutoML pipeline
with an LLM-powered feature engineering loop inspired by Karpathy's
autoresearch pattern.

The agent does NOT handle everything. It handles the pipeline and writes
code wherever reasoning beats fixed rules. Everything else stays static.
This is the right mix between legacy and modern data science.

---

## Directory structure

```
Project_Kashif/
├── BRIEF.md                  ← you are here — constitution, never modify
├── AUDIT.md                  ← Claude Code produces this in Step 1
├── HYBRID_PLAN.md            ← Claude Code produces this in Step 2
├── AUTORESEARCH_NOTES.md     ← Claude Code produces this in Step 3
├── automl_legacy/            ← student repos — READ ONLY, never modify
├── autoresearch/             ← Karpathy repo — READ ONLY, study only
└── kashif_core/              ← build everything here
    ├── core/
    │   ├── profiler.py       ← data profiling + pattern detection
    │   ├── fe_agent.py       ← LLM feature engineer + reflection loop
    │   ├── executor.py       ← sandboxed code exec + fallback guard
    │   ├── trainer.py        ← sklearn pipeline (from legacy)
    │   ├── reporter.py       ← auto report generator
    │   └── llm/              ← provider-agnostic LLM adapter layer
    │       ├── base.py       ← abstract BaseLLM interface
    │       ├── groq.py       ← Groq adapter (default, OpenAI-compatible)
    │       ├── anthropic.py  ← Anthropic adapter (secondary)
    │       └── ollama.py     ← local model adapter (later)
    ├── cli/
    │   └── main.py           ← typer CLI — kashif run data.csv
    ├── tests/
    │   ├── test_trainer.py
    │   ├── test_profiler.py
    │   ├── test_executor.py
    │   ├── test_fe_agent.py
    │   └── test_reporter.py
    ├── outputs/              ← pkl + logs + reports land here
    ├── config.yaml           ← all runtime config including LLM provider
    ├── pyproject.toml        ← uv manages this automatically
    └── program.md            ← runtime directive for the agent
```

---

## Hard rules — never break these

- **Never modify** anything inside `automl_legacy/` or `autoresearch/`
- **Build in kashif_core/** only
- **One step at a time** — complete and document each step before moving on
- **Wait for human approval** after Step 1 and Step 2 before proceeding
- **Static pipeline must beat baseline** on 3 test CSVs before agent loop is added
- **Every module needs a test** before the next module is started
- **No monolithic scripts** — functions and classes in separate modules
- **Use uv for everything** — no pip, no conda, no venv manually
- **fe_agent.py must never import a provider SDK directly** — only imports BaseLLM
- **No hardcoded API keys anywhere** — always loaded from environment variables

---

## Environment — uv (mandatory)

All environment and package management uses uv exclusively.
Run these from inside `kashif_core/` when starting Step 4:

```bash
uv init
uv add scikit-learn pandas numpy shap typer openai anthropic pytest
uv add fastapi uvicorn --optional api
```

Running the project:
```bash
uv run pytest tests/
uv run python -m cli.main run --csv data.csv --target col_name
```

Adding a new dependency during build:
```bash
uv add <package-name>
```

Never manually create a virtual environment.
Never use pip install.
pyproject.toml is the single source of truth — uv manages this automatically.

---

## LLM provider layer — provider-agnostic design (mandatory)

Kashif supports multiple LLM providers. `fe_agent.py` never imports a provider SDK
directly — it only imports `BaseLLM` from `core/llm/base.py`.

### Abstract interface — core/llm/base.py

```python
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        pass
```

### Default provider — Groq (core/llm/groq.py)

Groq is the default because:
- Fastest inference — critical for a multi-round loop
- OpenAI-compatible API — minimal adapter code
- Cheapest per token at scale
- Strong code generation with llama-3.3-70b-versatile

```python
from openai import OpenAI
from .base import BaseLLM

class GroqLLM(BaseLLM):
    def __init__(self, model: str, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = model

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content
```

### Secondary provider — Anthropic (core/llm/anthropic.py)

Built second. Uses anthropic SDK directly.

### Future provider — Ollama (core/llm/ollama.py)

Built later. For local/private deployments where data cannot leave the machine.

### config.yaml — provider selection

```yaml
llm:
  provider: groq                      # groq | anthropic | ollama
  model: llama-3.3-70b-versatile
  api_key_env: GROQ_API_KEY           # env var name, never the key itself
  temperature: 0.2
```

### Environment variables required

```bash
GROQ_API_KEY=...          # required for default Groq provider
ANTHROPIC_API_KEY=...     # required if provider: anthropic
```

### CLI override

```bash
kashif run --csv data.csv --target churn --llm groq
kashif run --csv data.csv --target churn --llm anthropic
kashif run --csv data.csv --target churn --llm ollama
```

---

## Steps — execute in strict order

---

### Step 1 — Audit automl_legacy
Read every repo inside `automl_legacy/`.
Do not write any code yet.
Produce `AUDIT.md` in `Project_Kashif/` scoring each repo on:

| Criterion | What to look for |
|---|---|
| Uses sklearn Pipeline objects | Clean injectable pipeline vs raw script |
| Working cross-validation strategy | StratifiedKFold, cross_val_score etc |
| Handles mixed dtypes | Numeric + categorical in same pipeline |
| Modular code | Functions/classes not one big notebook |
| Clean injection points | Where can LLM FE slot in naturally |
| Code quality | Readable, documented, maintainable |

Score each criterion: 0 (missing) / 1 (partial) / 2 (strong)
Total out of 12 per repo.
End with a ranked recommendation table.

**→ Stop here. Show human AUDIT.md. Wait for approval.**

---

### Step 2 — Propose the hybrid
Based on AUDIT.md, propose:
- Which repo is the base (highest injectable score)
- Which specific parts to borrow from other repos
- What needs to be rewritten from scratch
- What the clean module boundaries will be

Write proposal in `HYBRID_PLAN.md` in `Project_Kashif/`.
Include a simple ASCII diagram showing the data flow.

**→ Stop here. Show human HYBRID_PLAN.md. Wait for approval.**

---

### Step 3 — Study autoresearch
Read `autoresearch/` completely.
Produce `AUTORESEARCH_NOTES.md` in `Project_Kashif/` answering:

1. What is the core loop pattern?
2. What is the role of program.md?
3. Which ideas transfer directly to Kashif (tabular ML)?
4. Which ideas do NOT apply and why?
5. How should the Kashif reflection loop differ from Karpathy's?
6. What should Kashif's program.md contain?

This document becomes the blueprint for `kashif_core/core/fe_agent.py`.

---

### Step 4 — Build kashif_core (only after Steps 1-3 approved)

Start by initialising the environment:
```bash
cd kashif_core
uv init
uv add scikit-learn pandas numpy shap typer openai anthropic pytest
```

Build in this exact order — one module at a time:

**4a. trainer.py** — the static pipeline (ported from AutoFlowML)
- Port: cleaning.py, processing.py, evaluation.py, pipeline.py verbatim
- Port: ModelRegistry + ModelInfo from AutoML (remove sys.path hacks)
- Add optional fe_step param to build_pipeline() — insert between cleaning and processing
- LeaderboardEngine adapted to return structured dict (not DataFrame)
- Must run end to end on a CSV before touching anything else
- Test: tests/test_trainer.py

**4b. profiler.py** — data profiling + task detection
- Port: TaskDetector from AutoML verbatim — wrap in profiler.run()
- Write from scratch: dtypes, null rates, cardinality, skew, target distribution
- Returns single profile_json dict
- Test: tests/test_profiler.py

**4c. executor.py** — sandboxed code executor
- Write from scratch
- Takes Python code string + DataFrame
- Executes safely, catches ALL errors including syntax, runtime, KeyError
- Returns (transformed_df, error_or_none)
- Fallback: returns original df untouched if execution fails
- Imports nothing from kashif_core — fully isolated
- Test: tests/test_executor.py including deliberate bad code cases

**4d. core/llm/ adapter layer** — provider-agnostic LLM interface
- Write base.py with abstract BaseLLM
- Write groq.py using openai SDK pointed at Groq base_url (default)
- Write anthropic.py using anthropic SDK (secondary)
- Provider loaded from config.yaml — never hardcoded
- Test: tests/test_llm.py with mock completions

**4e. fe_agent.py** — the LLM feature engineer + Karpathy loop
- Imports BaseLLM only — never a provider SDK directly
- Round 1: reads profiler JSON + program.md, writes FE code, calls executor
- Round N: reads SHAP + scores from all previous rounds, rewrites FE code
- Stopping: delta < 0.005 OR max_rounds reached OR no new angles to try
- Returns: best_df, best_code, full experiment_log
- Test: tests/test_fe_agent.py with mock LLM

**4f. reporter.py** — auto report generator
- Reads experiment_log JSON
- Produces markdown: score progression, top features per round, final recommendation
- Test: tests/test_reporter.py

**4g. cli/main.py** — typer CLI
```bash
kashif run --csv data.csv --target survived
kashif run --csv data.csv --target price --rounds 4
kashif run --csv data.csv --target churn --no-agent
kashif run --csv data.csv --target churn --llm anthropic
```

---

## What the core engine returns (always JSON)

Every run — CLI or API — returns this same structure:

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
  "rounds": [
    {"round": 1, "cv_score": 0.841, "fe_code": "...", "top_features": []},
    {"round": 2, "cv_score": 0.871, "fe_code": "...", "top_features": []},
    {"round": 3, "cv_score": 0.891, "fe_code": "...", "top_features": []}
  ],
  "report_path": "./outputs/report.md"
}
```

CLI prints this formatted.
API returns this as JSON.
UI renders this as a dashboard.
The engine never knows or cares who called it.

---

## The agent boundary — what is static vs LLM-owned

| Static — deterministic code | LLM-owned — reasoning required |
|---|---|
| Data loading | FE code generation |
| Type detection | Reflection + improvement each round |
| Preprocessing | Stopping decision reasoning |
| Model training | Report narrative generation |
| Cross-validation | Reading program.md domain hints |
| Pickle output | Deciding what to drop vs keep |

---

## Tech stack

| Layer | Tool |
|---|---|
| Environment | uv |
| ML pipeline | scikit-learn |
| Data | pandas, numpy |
| Explainability | shap |
| CLI | typer |
| LLM default | Groq via openai SDK (llama-3.3-70b-versatile) |
| LLM secondary | Anthropic via anthropic SDK |
| LLM future | Ollama (local) |
| Testing | pytest |
| API (later) | fastapi + uvicorn |
| UI (later) | TBD — streamlit or react |

---

## Reflection prompt structure (for fe_agent.py)

The LLM receives this on every round after round 1:

```
ORIGINAL SCHEMA       — so it never forgets what raw columns exist
PROGRAM.MD DIRECTIVE  — user's goal, constraints, domain hints
ALL PREVIOUS ROUNDS   — code written + CV score for each round
CURRENT RESULTS       — SHAP values, dead features, failed columns
TASK                  — write improved FE code only, no explanation
```

The prompt is the most important part of the system.
See AUTORESEARCH_NOTES.md (Step 3) for full design.