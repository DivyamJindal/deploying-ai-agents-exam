"""Tests for the SqliteSaver-backed persistent checkpointer."""

from __future__ import annotations

from pathlib import Path

from langgraph.types import Command

from support_escalator.graph import build_graph, get_sqlite_checkpointer
from support_escalator.models import SupportState, TicketInput


def _state(message: str, account_id: str = "acct_1002") -> SupportState:
    return SupportState(
        ticket=TicketInput(
            title="Refund please",
            account_id=account_id,
            customer_email="ck@example.com",
            message=message,
        )
    )


def test_sqlite_checkpointer_persists_across_graph_instances(tmp_path: Path):
    db_path = tmp_path / "ck.sqlite"
    thread = "thread-persist"

    # First graph instance: kick off a run that hits the human-in-the-loop interrupt.
    cp1 = get_sqlite_checkpointer(db_path)
    graph1 = build_graph(checkpointer=cp1)
    config = {"configurable": {"thread_id": thread}}
    result = graph1.invoke(
        _state("I was charged twice for invoice 42, please refund."),
        config=config,
    )
    assert "__interrupt__" in result, "billing refund should hit the interrupt gate"

    # Second graph instance reads the same SQLite file: state must be there.
    cp2 = get_sqlite_checkpointer(db_path)
    graph2 = build_graph(checkpointer=cp2)
    snapshot = graph2.get_state(config)
    assert snapshot is not None
    assert snapshot.values, "state should be restored from disk"

    # Resuming on the second instance should complete the run.
    resumed = graph2.invoke(
        Command(
            resume={
                "approved": True,
                "guidance": "Approve refund and apologise.",
                "responder_name": "QA",
            }
        ),
        config=config,
    )
    assert resumed["final_response"], "resumed run should produce a final response"
    assert "Approve refund" in resumed["final_response"]
