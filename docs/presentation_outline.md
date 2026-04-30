# Presentation Outline

## Slide 1: Problem

Mosaic Cloud handles 2000+ tickets/day. Goal: resolve routine issues automatically and escalate risky tickets reliably.

## Slide 2: Why LangGraph

This needs conditional routing plus human-in-the-loop interrupts. A single chatbot cannot cleanly pause, persist, and resume supervisor decisions.

## Slide 3: Graph Architecture

Show `assets/support_escalator_graph.svg` (also embedded live in the app's **Architecture** tab). Walk through classifier, sentiment monitor, solvers, escalation gate, and response composer.

## Slide 4: State Schema

Show Pydantic `SupportState`: ticket, category, resolution attempts, sentiment score, escalation reason, supervisor input, final response. Note the `ui_state.to_plain()` normalization layer that lets the dashboard render mixed Pydantic / dict / Interrupt payloads safely.

## Slide 5: Demo Path 1 — Inbox + Auto-resolution

Open the **Inbox** workspace, load the password-reset demo, run the graph, and walk through the timeline → solver attempt → final response composer. Highlight that it never hits the supervisor.

## Slide 6: Demo Path 2 — Supervisor + Refund Approval

Run the duplicate-billing demo. The header flips to *Awaiting supervisor*. Switch to the **Supervisor** workspace, show the escalation card (reason, sentiment, refund exposure, account context), approve with guidance, and resume — final response now contains supervisor guidance.

## Slide 7: Demo Path 3 — Sentiment Escalation

Run the angry upload-bug demo. Show the sentiment KPI spike, the unresolved bug attempt, and the supervisor card explaining why we paused. Demonstrate a rejection path to show the response stays open instead of auto-resolving.

## Slide 8: KPIs And Business Impact

Show the **Analytics** workspace live: auto-resolution rate KPI, escalations counter, average sentiment, refund exposure, plus charts for category mix, sentiment trend, solver status, and escalation reasons. Tie each one back to a Mosaic Cloud KPI.

## Slide 9: Edge Cases

Missing account, unresolved bug, angry tone, refund above threshold, supervisor rejection — each visible from the run history sidebar and the resolution timeline.

## Slide 10: Learnings And Next Steps

LangGraph makes routing and resumable human review explicit. The normalization layer keeps the demo robust. Next: SLA timers (sidebar control already wired), Zendesk webhook adapter, multilingual response drafting, and CSV/PDF export from the Inbox.

## Q&A Prep

- **Why this pattern?** Routing and interrupts are both required: category solvers are conditional, escalation is human-gated.
- **What happens when a node fails?** The state contains partial attempts visible in the Inbox timeline; production would wrap solvers with retry/error metadata and escalate unresolved cases.
- **How does state prevent invalid transitions?** Pydantic constrains category literals and structures resolution attempts and supervisor decisions; the UI uses `to_plain` / `get_field` so mixed shapes never crash the dashboard.
- **What if supervisor rejects?** The final response composer includes the rejection guidance and keeps the ticket open rather than auto-resolving.
- **How do you measure auto-resolution?** The Analytics tab summarizes session history via `summarize_run` to compute the auto-resolution rate, refund exposure, and category/sentiment trends in real time.