# SupportEscalator

SupportEscalator is a LangGraph support-ticket agent for Mosaic Cloud. It classifies incoming SaaS tickets, routes them to category-specific solvers, monitors sentiment, and pauses for a human supervisor when policy or customer sentiment requires escalation.

## Problem Summary

Mosaic Cloud handles 2000+ support tickets daily. Routine issues should be resolved automatically, but angry customers, unresolved bugs, and material refunds must go to a human supervisor. This project demonstrates both required LangGraph patterns for Problem 9: conditional routing and human-in-the-loop interrupts.

## Architecture

Graph nodes:

1. `classifier` categorizes tickets as `bug`, `billing`, `feature`, or `general`.
2. `sentiment_monitor` scores anger/frustration signals.
3. Category solvers (`bug_solver`, `billing_solver`, `feature_solver`, `general_solver`) search local KB/account data and attempt resolution.
4. `escalation_gate` calls LangGraph `interrupt()` when escalation criteria are met.
5. `response_composer` writes the final customer response, incorporating supervisor guidance when present.

State is typed with Pydantic in `src/support_escalator/models.py` and includes the required fields: `ticket`, `category`, `resolution_attempts`, `sentiment_score`, `escalation_reason`, `supervisor_input`, and `final_response`.

Generate the graph image:

```bash
python scripts/draw_graph.py
```

This writes `assets/support_escalator_graph.svg` and `assets/support_escalator_graph.mmd`. If network access to `mermaid.ink` is available, it also writes `assets/support_escalator_graph.png`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Optional: enable the real LLM in the loop

The classifier and sentiment monitor will automatically use OpenAI when an `OPENAI_API_KEY` is configured. Otherwise they fall back to a deterministic rule-based implementation so the demo always works offline.

Copy the template and add your key:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...
# default model is gpt-4.1-nano (small, fast, cheap)
```

The Streamlit header shows a **Mode** pill (`LLM` or `Rule-based`) so reviewers can see which path is live.

### Persistent checkpoints

The graph compiles with a `SqliteSaver` checkpointer at `checkpoints/se.sqlite` by default, so any interrupted run can be resumed across restarts using its thread ID. The sidebar in the Streamlit app exposes the active thread ID and a picker to resume previous threads.

## Run the Ticketing Console

```bash
PYTHONPATH=src streamlit run app.py
```

The Streamlit app is now styled as a full **ticketing console** with four workspaces:

- **Inbox** — ticket intake card, customer/account snapshot, resolution timeline, solver attempts, and a final response composer with copy/download.
- **Supervisor** — pending escalation card with reason / risk / sentiment, approval form (approve, reject, supervisor name, guidance), and the resume-graph button that drives `Command(resume=...)`.
- **Analytics** — KPI cards (auto-resolution rate, escalations, average sentiment, refund exposure) plus Streamlit-native charts for category mix, sentiment trend, solver status, and escalation reasons.
- **Architecture** — the LangGraph SVG plus the live normalized state JSON for Q&A.

The left sidebar holds the demo ticket queue, thread management, run history, engine-mode status, and LangSmith tracing status.

Use the sidebar demo tickets to drive the three rubric flows:

- **Password reset** — autonomous resolution through `general_solver`, no interrupt.
- **Duplicate billing charge** — billing solver confirms a $499 refund and pauses at `escalation_gate` for supervisor approval; resume to deliver the apology + refund.
- **Angry upload bug** — sentiment + unresolved-bug logic triggers an interrupt; supervisor guidance is folded into the final response.

The UI uses a normalized state layer (`src/support_escalator/ui_state.py`) so any Pydantic model, datetime, enum, or LangGraph `Interrupt` object renders safely in the dashboard, charts, and JSON viewers.

## Test

```bash
PYTHONPATH=src pytest -q          # 30 tests, all deterministic (no LLM required)
PYTHONPATH=src pytest tests/test_evaluation.py -v   # evaluation framework only
```

The suite covers core graph behavior, UI state normalization, LLM fallback, checkpointer persistence, and a named evaluation framework with 6 representative scenarios (satisfies the +4 bonus rubric criterion).

## LangSmith Tracing (Bonus)

The graph auto-instruments when these env vars are set in `.env`:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...        # free tier at smith.langchain.com
LANGCHAIN_PROJECT=support-escalator
```

Once active, every run — classifier, sentiment monitor, solvers, escalation gate, response composer — is captured as a traced execution. The Streamlit sidebar shows a **● Tracing active** badge with a direct link to the trace dashboard.

## Prompt Engineering

**Classifier system prompt** (`src/support_escalator/llm.py` — `_CLASSIFIER_SYSTEM`):
- Lists all four categories with distinguishing examples to prevent bug/general confusion.
- Requires a `confidence` score (0–1) and one-sentence `rationale` — structured output forces the model to commit, reducing hedging.
- Iteration: adding explicit distinguishing examples reduced misclassification of angry billing queries as "general."

**Sentiment system prompt** (`llm.py` — `_SENTIMENT_SYSTEM`):
- Anchors the scale at 0.0 (fully calm) and 1.0 (furious) with behavioral examples (exclamation marks, capitals, churn threats, repetition).
- Iteration: adding "repeat themselves" as a frustration signal improved detection for the "third email" pattern in angry tickets.

**Rule-based fallback vocabulary** (`llm.py:29–41`):
- `_BUG_WORDS`, `_BILLING_WORDS`, `_FEATURE_WORDS`, `_ANGER_WORDS` are tuned to match the KB entries and demo ticket language.
- Confidence formula `min(0.95, 0.55 + 0.45 × hits/total)` ensures minimum 0.55 confidence on any keyword match and never reaches 1.0 (avoids false certainty). The cap at 0.95 leaves room for LLM override.

## Data Sources

This prototype uses synthetic support data committed in `data/`:

- `data/kb.json`: small SaaS FAQ / knowledge base.
- `data/accounts.json`: mock account and refund data.
- `data/demo_tickets.json`: demo tickets mapped to the presentation flow.

## KPIs

- Auto-resolution rate: target 75% for routine categories (rendered live in the Analytics tab).
- Mean time to resolution: reduce routine first response from minutes to seconds.
- CSAT by category: improve angry-ticket handling through earlier escalation.
- Escalation appropriateness: supervisor agreement with the escalation trigger.
- Refund exposure: total dollars routed through supervisor approval (rendered as a KPI card).

## Bonus Features

- **LangSmith tracing** — set `LANGCHAIN_API_KEY` to activate (see setup above).
- **Evaluation framework** — `tests/test_evaluation.py`, 6 named parametrized scenarios.
- **Prompt iteration** — documented above and visible in the LLM integration commits.
- **Auto-generated supervisor summary** — escalation_gate constructs a structured payload (ticket, category, sentiment, escalation reason, and auto_resolution) surfaced in the Supervisor tab.
- Supervisor queue UI, run-history KPIs, Streamlit-native analytics, normalized state layer, dark ticketing-console theme.

## Team

| Name | Role |
|------|------|
| Divyam Jindal | LangGraph architecture, escalation gate, checkpointing |
| Bhanu Uday | Streamlit UI, analytics workflow, supervisor experience |
| Ishaan Bansal | LLM classifier/sentiment integration, prompts, evaluation cases |
| Harman Manik | Test suite, data/KB setup, documentation, presentation support |

## Deck Link

Live deck (GitHub Pages): https://divyamjindal.github.io/deploying-ai-agents-exam/deck/

PDF deck: `deck/SupportEscalator-Group_9.pdf`

## Demo Video

Upload the 3-minute recording and replace this placeholder with the unlisted YouTube/Drive link.

