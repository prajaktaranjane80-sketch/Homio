"""Deterministic workflow projection; not a second lifecycle authority."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any

class WorkflowPriority(str, Enum):
    NORMAL = "NORMAL"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True)
class DealWorkflowStep:
    step_id: str
    current_status: str
    allowed_next_statuses: tuple[str, ...]
    action: str
    priority: WorkflowPriority
    requires_evidence: bool
    requires_approval: bool
    description: str

    @property
    def next_status(self) -> str | None:
        return self.allowed_next_statuses[0] if self.allowed_next_statuses else None

@dataclass(frozen=True)
class DealWorkflowSnapshot:
    deal_id: str
    tenant_id: str
    current_status: str
    version: int
    steps: tuple[DealWorkflowStep, ...]

    @property
    def next_step(self) -> DealWorkflowStep | None:
        return self.steps[0] if self.steps else None

_WORKFLOW = {
    "QUALIFIED": DealWorkflowStep("MATCH", "QUALIFIED", ("MATCHED",), "MATCH", WorkflowPriority.NORMAL, False, False, "Match the qualified opportunity to inventory."),
    "MATCHED": DealWorkflowStep("VISIT_SCHEDULE", "MATCHED", ("VISIT_PENDING",), "SCHEDULE_VISIT", WorkflowPriority.NORMAL, True, False, "Schedule a traceable property visit."),
    "VISIT_PENDING": DealWorkflowStep("VISIT_COMPLETE", "VISIT_PENDING", ("VISITED",), "RECORD_VISIT", WorkflowPriority.NORMAL, True, False, "Record verifiable visit evidence."),
    "VISITED": DealWorkflowStep("MAKE_OFFER", "VISITED", ("OFFERED",), "CREATE_OFFER", WorkflowPriority.NORMAL, True, False, "Create an attributable customer offer."),
    "OFFERED": DealWorkflowStep("NEGOTIATE_OR_BOOK", "OFFERED", ("NEGOTIATING", "BOOKING_PENDING"), "NEGOTIATE_OR_BOOK", WorkflowPriority.NORMAL, True, False, "Continue negotiation or prepare booking."),
    "NEGOTIATING": DealWorkflowStep("NEGOTIATION_DECISION", "NEGOTIATING", ("OFFERED", "BOOKING_PENDING"), "NEGOTIATION_DECISION", WorkflowPriority.NORMAL, True, False, "Record negotiated terms and either return to offer or prepare booking."),
    "BOOKING_PENDING": DealWorkflowStep("BOOK", "BOOKING_PENDING", ("BOOKED",), "BOOK", WorkflowPriority.CRITICAL, True, True, "Authorize and record the booking milestone."),
    "BOOKED": DealWorkflowStep("AGREEMENT", "BOOKED", ("AGREEMENT_PENDING",), "PREPARE_AGREEMENT", WorkflowPriority.CRITICAL, True, True, "Prepare agreement completion."),
    "AGREEMENT_PENDING": DealWorkflowStep("AGREE", "AGREEMENT_PENDING", ("AGREED",), "CONFIRM_AGREEMENT", WorkflowPriority.CRITICAL, True, True, "Confirm the agreement milestone."),
    "AGREED": DealWorkflowStep("REGISTRATION", "AGREED", ("REGISTRATION_PENDING",), "PREPARE_REGISTRATION", WorkflowPriority.CRITICAL, True, True, "Prepare registration milestone."),
    "REGISTRATION_PENDING": DealWorkflowStep("REGISTER", "REGISTRATION_PENDING", ("REGISTERED",), "REGISTER", WorkflowPriority.CRITICAL, True, True, "Record registration."),
    "REGISTERED": DealWorkflowStep("COMPLETION", "REGISTERED", ("COMPLETION_PENDING",), "PREPARE_COMPLETION", WorkflowPriority.CRITICAL, True, True, "Prepare transaction completion."),
    "COMPLETION_PENDING": DealWorkflowStep("COMPLETE", "COMPLETION_PENDING", ("COMPLETED",), "COMPLETE", WorkflowPriority.CRITICAL, True, True, "Authorize final completion."),
}

def build_deal_workflow(deal: Any) -> DealWorkflowSnapshot:
    current = getattr(deal.status, "value", deal.status)
    step = _WORKFLOW.get(current)
    return DealWorkflowSnapshot(deal.deal_id, deal.tenant_id, current, deal.version, (step,) if step else ())

__all__ = ["DealWorkflowSnapshot", "DealWorkflowStep", "WorkflowPriority", "build_deal_workflow"]
