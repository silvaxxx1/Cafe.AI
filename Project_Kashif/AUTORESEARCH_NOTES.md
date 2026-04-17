# AUTORESEARCH_NOTES.md — Study of Karpathy's autoresearch
> Step 3 output. No code written.
> Files read: README.md, program.md, train.py, prepare.py, analysis.ipynb

---

## 1. What is the core loop pattern?

The loop is defined explicitly in `program.md` and runs until manually interrupted:

```
SETUP ONCE:
  1. Create a fresh git branch (autoresearch/<tag>)
  2. Read all in-scope files for full context
  3. Verify data exists
  4. Initialize results.tsv with header row
  5. Run baseline (train.py unmodified) — this is the reference point

LOOP FOREVER:
  1. Inspect git state — know exactly where you are
  2. Form a hypothesis — pick one thing to change in train.py
  3. Edit train.py — make that change directly
  4. git commit — each experiment is a commit
  5. uv run train.py > run.log 2>&1 — redirect ALL output, fixed 5-minute wall budget
  6. grep "^val_bpb:" run.log — extract the single metric
  7. If grep is empty → crashed. Read stack trace. Fix trivial bugs; skip if fundamentally broken.
  8. Log result to results.tsv: commit hash, val_bpb, memory_gb, status, description
  9. If val_bpb IMPROVED (lower) → keep git commit, advance the branch
 10. If val_bpb same or worse → git reset --hard to previous commit (discard experiment)
```

**Structural properties of the loop:**

- **Single editable file.** Only `train.py` is modified. `prepare.py` (evaluation, dataloader, constants) is permanently frozen. This hard boundary prevents the agent from gaming the metric.
- **Single fixed metric.** `val_bpb` (validation bits-per-byte) is the only truth. Vocabulary-size-independent, so architectural changes are fairly compared.
- **Fixed time budget.** Training always runs for exactly 5 minutes regardless of what the agent changed. This makes all experiments directly comparable on the same compute.
- **Keep/discard is binary.** The branch only advances on improvement. Bad experiments are erased from git history as if they never happened.
- **Simplicity criterion.** A 0.001 improvement that adds 20 lines of hacky code is not worth it. A 0.001 improvement from deleting code is worth it. This prevents complexity drift.
- **Never stop.** Once started, the agent does not ask for permission. "The human might be asleep." ~100 experiments per overnight sleep on an H100.
- **Full context on every round.** Before each experiment, the agent reads `results.tsv` (all previous results) and the current `train.py`. It always has the full experimental history.

---

## 2. What is the role of program.md?

`program.md` is **the human's interface to the autonomous research organization** — not the training code, not the evaluation harness, but the meta-layer that governs how the agent operates.

From README: *"You are programming the `program.md` Markdown files that provide context to the AI agents and set up your autonomous research org."*

**What program.md contains:**

| Section | What it defines |
|---|---|
| Setup | Step-by-step initialization ritual before the loop begins |
| Scope constraints | What CAN be edited (train.py) and what CANNOT (prepare.py) |
| Goal | The metric to optimize (val_bpb, lower is better) and constraints (VRAM soft limit) |
| Simplicity criterion | The philosophy for deciding whether to keep a change |
| First run rule | Always establish the baseline before any experiments |
| Output format | How to read train.py's stdout output |
| Logging format | The results.tsv schema (5 columns, tab-separated, NOT comma-separated) |
| The experiment loop | The exact algorithm, step-by-step, including error handling |
| Autonomy directive | NEVER STOP. Never ask the human to continue. Think harder if stuck. |

**Key design insight:** `program.md` does NOT contain domain knowledge about the model or data. It contains procedural knowledge about how to run experiments. The agent discovers domain knowledge by reading `train.py` (which is full of comments and structure explaining what each component does) and the experimental history in `results.tsv`.

**The human's job is to iterate on `program.md`** — adding agents, changing the research culture (e.g., "be more radical"), or pointing agents at different constraints — while the agent iterates on `train.py` to improve the model.

This creates a two-level optimization:
- Inner loop: agent optimizes `train.py` → lower val_bpb
- Outer loop: human optimizes `program.md` → better research process

---

## 3. Which ideas transfer directly to Kashif (tabular ML)?

### Direct transfers

**a) Single fixed metric as ground truth**
`val_bpb` is the only thing that matters. For Kashif: CV score (F1, accuracy, R²) is the only thing that matters. SHAP values, feature counts, and code complexity are secondary signal. The stopping decision is always based on the CV delta, never on "this FE code looks clever."

**b) Baseline first, always**
The first run in autoresearch is always the unmodified `train.py` — never skip the baseline. For Kashif: Round 0 is always `--no-agent` pipeline (cleaning → processing → model, no FE). This establishes `baseline_score` before any LLM involvement.

**c) Keep/discard based on delta**
If `val_bpb` improved → keep. Otherwise → discard. For Kashif: if `cv_score_N > cv_score_best` → the FE code from round N is promoted as the new best code. Otherwise it is logged (as signal) but not used as the baseline for round N+1.

**d) Immutable evaluation harness**
`prepare.py` (specifically `evaluate_bpb()`) is never modified and never moved into `train.py`. For Kashif: `CrossValidator.run_cv()` in `trainer.py` is the immutable evaluation harness. The LLM cannot see it, cannot modify it, and `fe_agent.py` has no import path to it.

**e) Single editable artifact**
The agent modifies only `train.py`. For Kashif: the LLM produces only `fe_code` — a Python string of the form `def engineer_features(df: pd.DataFrame) -> pd.DataFrame`. The pipeline structure, preprocessing, model, and CV logic are untouchable.

**f) Carry full experimental history**
Before each new experiment, the agent reads `results.tsv` (all previous results). For Kashif: the full `experiment_log` (all previous rounds with their FE code, CV score, SHAP values, dead features, and any execution errors) is included in the reflection prompt. Nothing is hidden.

**g) Crash logging as signal, not failure**
When a run crashes, autoresearch logs it as `crash` status — the crash tells future rounds "this direction is broken." For Kashif: `executor.py` catches all errors and returns `(original_df, error_string)`. Failed FE attempts are logged in `experiment_log` with `error=True` and the error message included. The LLM in subsequent rounds can read "previous round 2 crashed with KeyError: 'income_ratio'" and avoid that path.

**h) Simplicity criterion**
A small improvement that adds ugly complexity is not worth it. Removing code that achieves equal or better results is the best outcome. For Kashif: when the stopping condition fires, the best FE code is selected by highest CV score. If two rounds have equal CV scores, shorter FE code is preferred. The reporter notes this in the final recommendation.

**i) The loop IS the product**
Autoresearch is not a single training run — it's the accumulated log of 100 overnight experiments. For Kashif: the experiment_log is the product, not any single model. `reporter.py` exists precisely to tell the story of how the final model was reached.

**j) Domain context as first-class input**
In autoresearch, `program.md` carries meta-instructions; the domain knowledge is embedded in `train.py` code comments. For Kashif: `program.md` carries domain knowledge (see Q6). The agent reads it on every round and uses it to generate contextually relevant feature transformations.

---

## 4. Which ideas do NOT apply and why?

**a) Fixed time budget (5 minutes)**
Autoresearch uses wall-clock time as the experiment budget because architecture changes alter training duration — a fixed time makes experiments comparable regardless of model size. Kashif's CV runs are deterministic in the number of samples and folds. Time is not the right budget. Kashif uses `max_rounds` (bounded iteration count) and `delta < 0.005` (diminishing-returns threshold) as stopping conditions.

**b) Git-based experiment tracking (commit/reset pattern)**
Autoresearch uses git commit to preserve good experiments and `git reset --hard` to discard bad ones. This works because the artifact (trained model weights) doesn't exist in the repo. Kashif doesn't need git for FE experiments — the `experiment_log` dict stores every FE code string in memory and outputs it to JSON at the end. Using git would be architecturally wrong (the user's git repo is the kashif_core codebase, not the experiment output).

**c) "NEVER STOP" autonomy directive**
Autoresearch is designed to run overnight, unattended, with no bound on experiments. Kashif is designed to return a result. The user calls `kashif run` and expects output. Running indefinitely would be a bug. Kashif uses explicit stopping conditions and returns the JSON output contract from BRIEF.md.

**d) GPU / VRAM constraints**
Autoresearch runs on a single NVIDIA GPU (tested on H100). VRAM is a soft constraint. Kashif runs sklearn pipelines on CPU. VRAM management is irrelevant.

**e) `val_bpb` metric and vocabulary-size independence**
Bits-per-byte is a language-model-specific metric designed to normalize across different tokenizer vocabulary sizes. Kashif uses task-appropriate CV metrics: accuracy/F1 for classification, R²/RMSE for regression. The `ModelEvaluator` from AutoFlowML already handles this dispatch.

**f) Modifying the model architecture and optimizer**
In autoresearch, the entire model (depth, attention heads, activation functions, optimizer algorithm, learning rate schedules) is fair game. The search space is the space of possible GPT training setups. In Kashif, the model and training algorithm are completely fixed — only the feature engineering step is modified. The LLM's search space is `{column transformations}`, not `{model architectures}`.

**g) Branch-per-experiment strategy**
Each autoresearch experiment lives on a git branch and is either committed (advance) or reset (discard). Kashif does not need separate branches for feature experiments. All experiments are co-located in the experiment_log and the best code is selected retrospectively. The "branch advance" analog is simply `best_code = max(experiment_log, key=lambda r: r['cv_score'])`.

**h) Pinned external validation shard**
Autoresearch pins `shard_06542.parquet` as a fixed validation set shared across ALL experiments (across all users, all runs). This ensures cross-experiment comparability on public benchmarks. Kashif has no external fixed dataset — the user provides their CSV and the validation set is derived from it by `CrossValidator` on each run.

**i) "Ask an agent for help" fallback for small compute**
The README says "Ask your favorite coding agent for help" for users adapting to smaller GPUs. Kashif is itself the agent. There is no human-in-the-loop during the feature engineering loop.

---

## 5. How should the Kashif reflection loop differ from Karpathy's?

### The five structural differences

**1. Explicit stopping condition (vs. NEVER STOP)**

Karpathy's loop runs indefinitely until the human intervenes. Kashif has three stopping conditions checked at the end of each round:
- `delta < 0.005` — diminishing returns (CV score improvement less than 0.5%)
- `max_rounds reached` — wall of rounds (configurable in `config.yaml`)
- `no new angles to try` — LLM explicitly states there is nothing left to attempt

Karpathy cannot stop autonomously because a human sleeping through the night is the intended use case. Kashif must stop because the user called a CLI command and is waiting for output.

**2. SHAP values as feedback (vs. reading code)**

Karpathy's agent learns from the experimental history by reading `results.tsv` and the current `train.py`. The feedback is: "previous val_bpb was X, here is what the code looks like now." The agent infers what mattered from the code structure.

Kashif's agent receives explicit, quantitative signal:
- SHAP feature importance scores for each round — which features actually moved the model
- Dead features — features that scored zero SHAP across all rounds
- Failed FE columns — columns that caused executor errors in previous rounds
- CV score trajectory — the numeric delta trend across all rounds

This is richer and more direct than code inspection. The LLM does not need to infer what worked — it is told via SHAP.

**3. Round context is reconstructed, not accumulated**

Karpathy's agent has the git branch and `results.tsv` as persistent state. The agent operates on a living, mutable file (`train.py`).

Kashif has no persistent state between LLM calls. Each call to `fe_agent.py` reconstructs the full prompt from scratch using `experiment_log`. The LLM receives a self-contained prompt with:
```
ORIGINAL SCHEMA       — the raw column list, never changes
PROGRAM.MD DIRECTIVE  — user's domain context, never changes
ALL PREVIOUS ROUNDS   — code written + CV score per round
CURRENT RESULTS       — SHAP values, dead features, errors from last round
TASK                  — write improved FE code only, no explanation
```
This stateless design means `fe_agent.py` is purely functional: `(experiment_log) → fe_code`. No side effects, no persistent LLM session.

**4. FE code is scoped to a single function contract**

Karpathy's agent can change any part of `train.py` — the entire model class, the optimizer, the training loop, anything. The scope is "the whole ML system."

Kashif's LLM writes exactly one thing:
```python
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    # ... transformation logic ...
    return df
```
The function signature is fixed. The LLM cannot add imports at file level, cannot modify the pipeline, cannot access the target column. `executor.py` enforces this boundary — it receives the function as a code string and executes it in a scoped context. Any attempt to do something outside this scope either fails silently (executor catches the error) or is simply outside what the function can return.

**5. No keep/reset — all rounds are permanent context**

Karpathy's `git reset --hard` erases bad experiments from history. This is intentional: the branch should only show the "winning" path.

Kashif never erases experiments. A round with a bad CV score is logged in `experiment_log` with `status: discard` and is included in every subsequent round's prompt. The LLM must know what was tried and failed — "round 2 tried polynomial interactions on income and weight and scored 0.762, worse than baseline 0.821" — so it doesn't repeat the same dead end.

The "discard" analog in Kashif is: a failed round's FE code is not promoted to be the `fe_step` in the next round's pipeline. The *best* previous code remains the basis. But the failed code stays in the log.

### Summary table

| Dimension | Karpathy's autoresearch | Kashif |
|---|---|---|
| Stopping | Never (human interrupts) | delta < 0.005 OR max_rounds OR no angles |
| Feedback signal | `results.tsv` + code reading | SHAP values + dead features + error messages |
| LLM state model | Mutable file + git history | Stateless: full context reconstructed per call |
| Edit scope | Entire `train.py` | Single `engineer_features(df) → df` function |
| Failed experiments | `git reset --hard` (erased) | Logged permanently, included in next prompt |
| Metric | `val_bpb` (lower is better) | Task-appropriate CV score (higher is better) |
| Budget | Fixed wall-clock time | Fixed rounds + delta threshold |
| Parallelism | Multiple agents possible | Single agent, sequential rounds |

---

## 6. What should Kashif's program.md contain?

**Critical distinction from autoresearch's `program.md`:**

In autoresearch, `program.md` defines the loop mechanics — HOW the agent works. Those instructions are executed by the LLM at runtime because the loop itself is a manual prompt conversation.

In Kashif, the loop mechanics are hard-coded in `fe_agent.py`. The LLM never reads the loop algorithm. `program.md` in Kashif is **purely domain context** — the user's knowledge about their specific problem, injected into the LLM's prompt on every round.

The agent reads `program.md` at the beginning of round 1 and every subsequent round. It informs what transformations to try, what to avoid, and what the data means.

### Kashif program.md template and purpose

```markdown
# [Project Name] — Kashif Program Directive

## Problem statement
What is being predicted. What does the target column represent in real-world terms.
Why this problem matters.
Example: "Predicting 30-day hospital readmission. Target: 'readmitted' (binary).
           High recall is more important than precision — false negatives have real consequences."

## Target interpretation
- Type: classification / regression
- Distribution notes: is it imbalanced? is the scale bounded?
- What does a high/low value mean in domain terms?

## Column descriptions
Describe each column in plain language. The LLM has only column names and statistics
from profiler.py — it cannot infer meaning from names like "col_a", "x14", "amt_02".
Example:
- admission_type: how the patient was admitted (1=Emergency, 2=Urgent, 3=Elective)
- num_lab_procedures: number of lab tests performed during the encounter
- time_in_hospital: number of days the patient stayed

## Known important features
Columns you believe are predictive, with reasoning.
Example: "num_medications and num_lab_procedures are likely the strongest predictors —
          sicker patients get more tests and drugs."

## Transformations to try
Domain-specific feature engineering hints.
Example:
- "Create a ratio: num_medications / time_in_hospital (intensity of treatment)"
- "age is in decade bins (e.g. '[30-40)') — extract the lower bound as a numeric"
- "Diagnoses are ICD-9 codes — group into coarse disease categories"

## Transformations to avoid
What NOT to do. Protect against target leakage, meaningless transformations.
Example:
- "Do not use 'discharge_disposition_id' — it encodes what happened after discharge
   and partially contains the target label."
- "Do not one-hot encode 'patient_nbr' — it is a unique patient ID, no signal."

## Evaluation priority
What the CV score means in context. If task is imbalanced, note it.
Example: "Optimize for F1. This dataset is 88% negative — accuracy is misleading.
          A model that always predicts 'not readmitted' scores 0.88 accuracy but is useless."
```

### What the program.md is NOT

- It is **not** loop mechanics (those are in `fe_agent.py`)
- It is **not** a list of allowed Python libraries (executor.py handles that)
- It is **not** a description of the pipeline steps (those are fixed in `trainer.py`)
- It is **not** a promise of what will work — it is domain hints, not ground truth

### Difference from autoresearch's program.md

| | autoresearch program.md | Kashif program.md |
|---|---|---|
| Primary content | Loop algorithm (how the agent works) | Domain knowledge (what the problem is) |
| Reads `train.py`? | Yes — agent studies the code | No — LLM only receives profiler JSON |
| Edited by | Human when changing research process | User when running a new CSV |
| Frequency of change | Rare (once per research org setup) | Every new dataset / problem |
| Length | Medium (~100 lines) | Short (~30-60 lines, problem-specific) |
| Audience | The LLM doing the loop | The LLM doing FE for this specific problem |

### How it is used in fe_agent.py

On every LLM call, the prompt structure is:

```
[SYSTEM]
You are a feature engineering agent for tabular machine learning.
You write a single Python function: engineer_features(df) -> df.
Do not add imports. Do not modify the target column. Return the transformed df.

[USER]
## Original schema (do not change this)
{profile_json serialized as readable summary}

## Domain directive (program.md)
{full contents of program.md}

## Experimental history (all previous rounds)
Round 0 (baseline, no FE): cv_score=0.821
Round 1: cv_score=0.843, fe_code=..., top_features=[...], dead_features=[...]
Round 2: cv_score=0.819 (DISCARD), fe_code=..., error=None, note="ratio features hurt"
...

## Current round context
Best score so far: 0.843 (round 1)
Last round SHAP top features: [...]
Last round dead features (zero SHAP): [...]
Last round errors: [...]

## Task
Write improved engineer_features(df) -> df.
Do not explain. Return only the function.
```

`program.md` is the domain anchor in this prompt. Without it, the LLM is guessing from column names. With it, the LLM has the user's domain expertise baked into every round of reasoning.

---

## Blueprint summary for fe_agent.py

This section is the direct input to Step 4e (building `fe_agent.py`).

| Design decision | Choice | Rationale from autoresearch |
|---|---|---|
| Stopping condition | `delta < 0.005` OR `max_rounds` OR `no new angles` | Karpathy runs forever — Kashif must terminate |
| Feedback mechanism | SHAP + dead features + error log | Richer than `results.tsv` alone |
| LLM state | Stateless, full context per call | No persistent session — simpler, portable across providers |
| Edit scope | Single function `engineer_features(df) → df` | Analogous to "only edit train.py" |
| Failed round handling | Log permanently, feed back as negative signal | Never erase — failures are information |
| Baseline | Round 0 always runs without FE | "First run establishes baseline" |
| Simplicity criterion | Shortest code wins on equal scores | Directly from Karpathy's simplicity principle |
| Domain context | Fed via `program.md` on every round | Analogous to domain knowledge embedded in `train.py` comments |
| Provider | Resolved from `config.yaml` via `BaseLLM` | No hardcoded SDK — same flexibility as `uv` in autoresearch |
