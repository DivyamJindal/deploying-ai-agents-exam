from __future__ import annotations

from langgraph.types import Command

from support_escalator.graph import build_graph
from support_escalator.models import SupportState, TicketInput


def make_state(message: str, title: str = "Test", account_id: str = "acct_1001") -> SupportState:
    return SupportState(
        ticket=TicketInput(
            title=title,
            account_id=account_id,
            customer_email="test@example.com",
            message=message,
        )
    )


def test_general_ticket_resolves_without_interrupt():
    graph = build_graph()
    result = graph.invoke(make_state("How do I reset my password?"), config={"configurable": {"thread_id": "t1"}})
    assert result["category"] == "general"
    assert result["final_response"]
    assert "__interrupt__" not in result


def test_billing_refund_interrupts_and_resumes():
    graph = build_graph()
    config = {"configurable": {"thread_id": "t2"}}
    result = graph.invoke(make_state("I was charged twice, please refund me", account_id="acct_1002"), config=config)
    assert "__interrupt__" in result
    interrupt_payload = result["__interrupt__"][0].value
    assert "refund" in interrupt_payload["escalation_reason"]

    resumed = graph.invoke(
        Command(resume={"approved": True, "guidance": "Approve refund and apologise.", "responder_name": "QA"}),
        config=config,
    )
    assert "Approve refund" in resumed["final_response"]
    assert resumed["supervisor_input"].startswith("QA:")


def test_angry_bug_ticket_interrupts_for_sentiment():
    graph = build_graph()
    result = graph.invoke(
        make_state("This is my third email and nobody is helping!!! Upload is failing."),
        config={"configurable": {"thread_id": "t3"}},
    )
    assert "__interrupt__" in result
    assert result["sentiment_score"] >= 0.67
