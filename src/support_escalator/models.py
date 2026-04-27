from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


TicketCategory = Literal["bug", "billing", "feature", "general"]


class TicketInput(BaseModel):
    title: str
    account_id: str
    customer_email: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResolutionAttempt(BaseModel):
    node: str
    summary: str
    evidence: list[str] = Field(default_factory=list)
    resolved: bool = False


class SupervisorDecision(BaseModel):
    approved: bool
    guidance: str
    responder_name: str = "Human Supervisor"


class Account(BaseModel):
    account_id: str
    customer_name: str
    plan: str
    mrr: float
    last_invoice_amount: float
    duplicate_charge: bool
    eligible_refund: float


class KnowledgeBaseEntry(BaseModel):
    id: str
    category: str
    title: str
    body: str
    tags: list[str]


class SupportState(BaseModel):
    ticket: TicketInput
    category: TicketCategory | None = None
    resolution_attempts: list[ResolutionAttempt] = Field(default_factory=list)
    sentiment_score: float = 0.0
    escalation_reason: Optional[str] = None
    supervisor_input: Optional[str] = None
    final_response: str = ""
    ticket_metadata: dict[str, str] = Field(default_factory=dict)


class DemoTicket(str, Enum):
    PASSWORD = "Password reset"
    BILLING = "Duplicate billing charge"
    ANGRY = "Angry upload bug"
