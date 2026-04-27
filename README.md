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

No paid LLM key is required for the demo version because the solvers use deterministic rubric-friendly logic over local sample data. An LLM classifier/sentiment prompt can be swapped in later if desired.

## Run the Ticketing Console

```bash
PYTHONPATH=src streamlit run app.py
```

The Streamlit app is now styled as a full **ticketing console** with four workspaces:

- **Inbox** — ticket intake card, customer/account snapshot, resolution timeline, solver attempts, and a final response composer with copy/download.
- **Supervisor** — pending escalation card with reason / risk / sentiment, approval form (approve, reject, supervisor name, guidance), and the resume-graph button that drives `Command(resume=...)`.
- **Analytics** — KPI cards (auto-resolution rate, escalations, average sentiment, refund exposure) plus Streamlit-native charts for category mix, sentiment trend, solver status, and escalation reasons.
- **Architecture** — the LangGraph SVG plus the live normalized state JSON for Q&A.

The left sidebar holds the demo ticket queue, thread management, run history, and SLA controls.

Use the sidebar demo tickets to drive the three rubric flows:

- **Password reset** — autonomous resolution through `general_solver`, no interrupt.
- **Duplicate billing charge** — billing solver confirms a $499 refund and pauses at `escalation_gate` for supervisor approval; resume to deliver the apology + refund.
- **Angry upload bug** — sentiment + unresolved-bug logic triggers an interrupt; supervisor guidance is folded into the final response.

The UI uses a normalized state layer (`src/support_escalator/ui_state.py`) so any Pydantic model, datetime, enum, or LangGraph `Interrupt` object renders safely in the dashboard, charts, and JSON viewers.

## Test

```bash
PYTHONPATH=src pytest -q
```

The suite covers both core graph behavior (`tests/test_graph.py`) and UI-side state normalization (`tests/test_app_state.py`) so the dashboard stays robust against mixed Pydantic / dict payloads.

## Data Sources

This prototype uses synthetic support data committed in `data/`:

- `data/kb.json`: small SaaS FAQ / knowledge base.
- `data/accounts.json`: mock account and refund data.
- `data/demo_tickets.json`: demo tickets mapped to the presentation flow.

## Team Roles

Update before submission:

- Member 1: Graph architecture and LangGraph interrupts
- Member 2: Streamlit UI and demo recording
- Member 3: KB/account data and solver logic
- Member 4: README, memo, deck, tests, and Q&A prep

## KPIs

- Auto-resolution rate: target 75% for routine categories (rendered live in the Analytics tab).
- Mean time to resolution: reduce routine first response from minutes to seconds.
- CSAT by category: improve angry-ticket handling through earlier escalation.
- Escalation appropriateness: supervisor agreement with the escalation trigger.
- Refund exposure: total dollars routed through supervisor approval (rendered as a KPI card).

## Bonus Features Included / Planned

- **Included**: supervisor queue UI, auto-generated escalation context, multi-demo flow, run-history KPIs, Streamlit-native analytics, normalized state layer, end-to-end + UI regression tests, dark ticketing-console theme.
- **Next**: SLA timer per category, CSV/PDF export for ticket metadata, Zendesk-style webhook adapter, multilingual response drafting.
