# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the Streamlit console
PYTHONPATH=src streamlit run app.py

# Run tests
PYTHONPATH=src pytest -q

# Run a single test
PYTHONPATH=src pytest tests/test_graph.py::test_billing_refund_interrupts_and_resumes -v

# Regenerate graph SVG
python scripts/draw_graph.py

# Lint
ruff check src tests
```

`pyproject.toml` configures pytest to set `pythonpath = ["src"]`, but the `PYTHONPATH=src` prefix is still needed when running from the repo root outside pytest.

## LLM vs rule-based mode

`src/support_escalator/llm.py` auto-selects between OpenAI (`gpt-4.1-nano` by default) and a deterministic keyword fallback based on whether `OPENAI_API_KEY` is set. Copy `.env.example` to `.env` in the repo root and add the key to enable LLM mode. The Streamlit header shows a **Mode** pill indicating which path is live.

## Architecture

### LangGraph graph (`src/support_escalator/graph.py`)

The graph flows: `START → classifier → sentiment_monitor → [category solver] → escalation_gate → response_composer → END`

- **classifier** and **sentiment_monitor** call `llm.py` (LLM or rule-based).
- **route_by_category** is a conditional edge off `sentiment_monitor` that fans out to one of four solver nodes based on `state.category`.
- All four solvers converge on **escalation_gate**, which calls `langgraph.types.interrupt()` when any of three criteria are met: sentiment ≥ 0.67, refund > $200, or the solver left `resolved=False`. The interrupt suspends the graph; the Streamlit supervisor tab resumes it via `Command(resume=...)`.
- **response_composer** writes the final customer response, incorporating `state.supervisor_input` if present.

### State (`src/support_escalator/models.py`)

`SupportState` is a Pydantic model used as the LangGraph state type. Key fields: `ticket`, `category`, `resolution_attempts` (list of `ResolutionAttempt`), `sentiment_score`, `escalation_reason`, `supervisor_input`, `final_response`, `ticket_metadata`.

### Persistence

`build_graph()` compiles with a `SqliteSaver` at `checkpoints/se.sqlite` (created on first run). Each Streamlit session uses a UUID thread ID. The sidebar exposes the thread ID and a picker to resume previous threads by replaying state from the checkpoint.

### Streamlit app (`app.py`)

Four tabs: **Inbox** (ticket intake + resolution timeline), **Supervisor** (escalation approval form that drives `Command(resume=...)`), **Analytics** (KPI cards + charts), **Architecture** (SVG + live state JSON).

`src/support_escalator/ui_state.py` provides a normalization layer (`to_plain`, `get_field`, `extract_interrupt`, `summarize_run`) so Pydantic models, datetimes, enums, and `Interrupt` objects render safely in Streamlit widgets.

### Data

Synthetic data in `data/`: `kb.json` (FAQ/KB), `accounts.json` (mock accounts with refund data), `demo_tickets.json` (three rubric demo flows: Password reset → autonomous; Duplicate billing → interrupt/resume; Angry upload bug → sentiment interrupt).
