from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .data import load_accounts, search_kb
from .models import ResolutionAttempt, SupportState, SupervisorDecision

ESCALATION_REFUND_THRESHOLD = 200
ANGER_WORDS = {"angry", "furious", "third", "nobody", "escalated", "!!!", "terrible", "blocking"}
BUG_WORDS = {"bug", "error", "crash", "failing", "failed", "broken", "upload"}
BILLING_WORDS = {"billing", "charged", "charge", "invoice", "refund", "payment", "twice"}
FEATURE_WORDS = {"feature", "export", "csv", "report", "integration", "request"}


def _append_attempt(state: SupportState, attempt: ResolutionAttempt) -> list[ResolutionAttempt]:
    return [*state.resolution_attempts, attempt]


def classifier(state: SupportState) -> dict[str, Any]:
    text = f"{state.ticket.title} {state.ticket.message}".lower()
    scores = {
        "bug": sum(word in text for word in BUG_WORDS),
        "billing": sum(word in text for word in BILLING_WORDS),
        "feature": sum(word in text for word in FEATURE_WORDS),
        "general": 1,
    }
    category = max(scores, key=scores.get)
    print(f"classifier -> {category}")
    return {"category": category, "ticket_metadata": {"category": category, "status": "classified"}}


def route_by_category(state: SupportState) -> str:
    return state.category or "general"


def sentiment_monitor(state: SupportState) -> dict[str, Any]:
    text = state.ticket.message.lower()
    anger_hits = sum(1 for word in ANGER_WORDS if word in text)
    score = min(1.0, anger_hits / 3)
    print(f"sentiment_monitor -> {score:.2f}")
    return {"sentiment_score": score}


def general_solver(state: SupportState) -> dict[str, Any]:
    hits = search_kb(state.ticket.message, "general")
    evidence = [hit.title for hit in hits]
    summary = "Shared the password reset / FAQ guidance from the knowledge base."
    if hits:
        summary = hits[0].body
    attempt = ResolutionAttempt(node="general_solver", summary=summary, evidence=evidence, resolved=True)
    return {"resolution_attempts": _append_attempt(state, attempt), "ticket_metadata": {"status": "solved_by_general_solver"}}


def feature_solver(state: SupportState) -> dict[str, Any]:
    hits = search_kb(state.ticket.message, "feature")
    evidence = [hit.title for hit in hits]
    body = hits[0].body if hits else "Documented the feature request and shared current product behaviour."
    attempt = ResolutionAttempt(node="feature_solver", summary=body, evidence=evidence, resolved=True)
    return {"resolution_attempts": _append_attempt(state, attempt), "ticket_metadata": {"status": "solved_by_feature_solver"}}


def bug_solver(state: SupportState) -> dict[str, Any]:
    hits = search_kb(state.ticket.message, "bug")
    evidence = [hit.title for hit in hits]
    summary = (
        "Matched this to a known upload issue. Asked for workspace ID, file size, timestamp, "
        "and a console screenshot, then attached known incident MC-231 for engineering follow-up."
    )
    attempt = ResolutionAttempt(node="bug_solver", summary=summary, evidence=evidence, resolved=False)
    return {"resolution_attempts": _append_attempt(state, attempt), "ticket_metadata": {"status": "needs_bug_followup"}}


def billing_solver(state: SupportState) -> dict[str, Any]:
    account = load_accounts().get(state.ticket.account_id)
    hits = search_kb(state.ticket.message, "billing")
    evidence = [hit.title for hit in hits]
    if not account:
        summary = "Could not find the account, so billing needs a human account lookup."
        resolved = False
    elif account.duplicate_charge:
        summary = f"Confirmed duplicate charge. Eligible refund is ${account.eligible_refund:.0f}."
        resolved = account.eligible_refund <= ESCALATION_REFUND_THRESHOLD
    else:
        summary = "No duplicate charge found. Explained proration and invoice timing."
        resolved = True
    attempt = ResolutionAttempt(node="billing_solver", summary=summary, evidence=evidence, resolved=resolved)
    return {"resolution_attempts": _append_attempt(state, attempt), "ticket_metadata": {"status": "billing_checked"}}


def escalation_gate(state: SupportState) -> dict[str, Any]:
    reasons: list[str] = []
    account = load_accounts().get(state.ticket.account_id)
    if state.sentiment_score >= 0.67:
        reasons.append("angry or frustrated tone detected")
    if account and account.eligible_refund > ESCALATION_REFUND_THRESHOLD:
        reasons.append(f"refund ${account.eligible_refund:.0f} exceeds ${ESCALATION_REFUND_THRESHOLD} threshold")
    if state.resolution_attempts and not state.resolution_attempts[-1].resolved:
        reasons.append("solver could not fully resolve the ticket")

    if not reasons:
        print("escalation_gate -> no escalation")
        return {"escalation_reason": None, "ticket_metadata": {"escalated": "false"}}

    reason = "; ".join(reasons)
    latest = state.resolution_attempts[-1].summary if state.resolution_attempts else "No attempted resolution yet."
    payload = {
        "ticket": state.ticket.model_dump(mode="json"),
        "category": state.category,
        "sentiment_score": state.sentiment_score,
        "escalation_reason": reason,
        "auto_resolution": latest,
    }
    print(f"escalation_gate -> interrupt: {reason}")
    decision_raw = interrupt(payload)
    decision = SupervisorDecision.model_validate(decision_raw)
    status = "approved_by_supervisor" if decision.approved else "rejected_by_supervisor"
    return {
        "escalation_reason": reason,
        "supervisor_input": f"{decision.responder_name}: {decision.guidance}",
        "ticket_metadata": {"escalated": "true", "status": status},
    }


def response_composer(state: SupportState) -> dict[str, Any]:
    latest = state.resolution_attempts[-1].summary if state.resolution_attempts else "We reviewed your ticket."
    if state.supervisor_input:
        response = (
            f"Hi, thanks for your patience. We escalated this to a supervisor because {state.escalation_reason}.\n\n"
            f"Resolution: {latest}\n\nSupervisor guidance: {state.supervisor_input}\n\n"
            "We will keep the ticket open until the follow-up is confirmed."
        )
    else:
        response = (
            "Hi, thanks for reaching out. I reviewed your ticket and found a supported resolution.\n\n"
            f"Resolution: {latest}\n\nIf this does not solve it, reply here and we will reopen the case."
        )
    return {"final_response": response, "ticket_metadata": {**state.ticket_metadata, "status": "response_ready"}}


def build_graph(checkpointer: Any | None = None):
    workflow = StateGraph(SupportState)
    workflow.add_node("classifier", classifier)
    workflow.add_node("sentiment_monitor", sentiment_monitor)
    workflow.add_node("bug_solver", bug_solver)
    workflow.add_node("billing_solver", billing_solver)
    workflow.add_node("feature_solver", feature_solver)
    workflow.add_node("general_solver", general_solver)
    workflow.add_node("escalation_gate", escalation_gate)
    workflow.add_node("response_composer", response_composer)

    workflow.add_edge(START, "classifier")
    workflow.add_edge("classifier", "sentiment_monitor")
    workflow.add_conditional_edges(
        "sentiment_monitor",
        route_by_category,
        {
            "bug": "bug_solver",
            "billing": "billing_solver",
            "feature": "feature_solver",
            "general": "general_solver",
        },
    )
    for solver in ["bug_solver", "billing_solver", "feature_solver", "general_solver"]:
        workflow.add_edge(solver, "escalation_gate")
    workflow.add_edge("escalation_gate", "response_composer")
    workflow.add_edge("response_composer", END)
    return workflow.compile(checkpointer=checkpointer or MemorySaver())
