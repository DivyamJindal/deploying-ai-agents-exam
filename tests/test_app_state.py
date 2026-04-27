"""Regression tests for the UI-side state normalization helpers."""

from __future__ import annotations

import json

from support_escalator.models import (
    ResolutionAttempt,
    SupportState,
    TicketInput,
)
from support_escalator.ui_state import (
    extract_interrupt,
    get_field,
    summarize_run,
    to_plain,
)


def _state_with_attempt() -> dict:
    """Mimic LangGraph's mixed return: dict shell + Pydantic ResolutionAttempt."""
    ticket = TicketInput(
        title="Upload broken",
        account_id="acct_1001",
        customer_email="ceo@apex.example",
        message="Uploads keep failing",
    )
    state = SupportState(
        ticket=ticket,
        category="bug",
        sentiment_score=0.67,
        resolution_attempts=[
            ResolutionAttempt(
                node="bug_solver",
                summary="Matched to known incident MC-231.",
                evidence=["Upload retry guide"],
                resolved=False,
            )
        ],
    )
    raw = state.model_dump()
    raw["resolution_attempts"] = state.resolution_attempts
    raw["__interrupt__"] = [
        type(
            "FakeInterrupt",
            (),
            {
                "value": {
                    "escalation_reason": "angry tone detected",
                    "auto_resolution": "Asked for screenshots.",
                    "ticket": ticket.model_dump(mode="json"),
                    "category": "bug",
                    "sentiment_score": 0.67,
                }
            },
        )()
    ]
    return raw


def test_to_plain_handles_pydantic_resolution_attempt():
    attempt = ResolutionAttempt(
        node="bug_solver",
        summary="Asked for screenshots",
        evidence=["KB-123"],
        resolved=False,
    )
    plain = to_plain(attempt)

    assert isinstance(plain, dict)
    assert plain["node"] == "bug_solver"
    assert plain["resolved"] is False
    assert plain["evidence"] == ["KB-123"]
    assert json.dumps(plain), "to_plain output must be JSON-serializable"


def test_to_plain_handles_mixed_dict_with_pydantic_children():
    raw = _state_with_attempt()
    plain = to_plain(raw)

    attempt = plain["resolution_attempts"][0]
    assert attempt["node"] == "bug_solver"
    assert attempt["summary"].startswith("Matched")
    assert attempt["evidence"] == ["Upload retry guide"]
    assert json.dumps(plain), "normalized state must be JSON-serializable"


def test_get_field_supports_dict_and_attribute_access():
    attempt = ResolutionAttempt(node="general_solver", summary="ok", resolved=True)
    assert get_field(attempt, "node") == "general_solver"
    assert get_field({"node": "x"}, "node") == "x"
    assert get_field(None, "node", default="fallback") == "fallback"
    assert get_field(attempt, "missing", default=42) == 42


def test_extract_interrupt_returns_normalized_payload():
    raw = _state_with_attempt()
    payload = extract_interrupt(raw)

    assert payload is not None
    assert payload["escalation_reason"] == "angry tone detected"
    assert payload["ticket"]["account_id"] == "acct_1001"
    assert json.dumps(payload), "interrupt payload must be JSON-serializable"


def test_summarize_run_extracts_kpi_fields():
    raw = to_plain(_state_with_attempt())
    raw["final_response"] = "Hi, here is the resolution."

    summary = summarize_run(raw)

    assert summary["category"] == "bug"
    assert summary["solver"] == "bug_solver"
    assert summary["solver_resolved"] is False
    assert summary["sentiment_score"] == 0.67
    assert summary["account_id"] == "acct_1001"
    assert summary["ticket_title"] == "Upload broken"
