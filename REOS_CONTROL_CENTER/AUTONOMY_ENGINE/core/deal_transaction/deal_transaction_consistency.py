from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .deal_contract import DealStatus


@dataclass(frozen=True)
class DealConsistencyViolation:
    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True)
class DealConsistencyResult:
    valid: bool
    checked: tuple[str, ...]
    violations: tuple[DealConsistencyViolation, ...]

    def require_valid(self) -> "DealConsistencyResult":
        if not self.valid:
            raise ValueError(
                "; ".join(
                    violation.message
                    for violation in self.violations
                )
            )

        return self


def validate_deal_consistency(
    deal: Any,
    *,
    tenant_id: str,
) -> DealConsistencyResult:
    violations: list[DealConsistencyViolation] = []

    checked = (
        "tenant",
        "identity",
        "version",
        "history",
        "participants",
        "offers",
        "negotiation",
        "milestones",
        "ownership",
        "evidence",
        "audit",
    )

    if deal.tenant_id != tenant_id:
        violations.append(
            DealConsistencyViolation(
                "TENANT_SCOPE",
                "Deal tenant mismatch.",
                "tenant_id",
            )
        )

    if (
        not deal.deal_id
        or not deal.customer_id
        or not deal.broker_id
    ):
        violations.append(
            DealConsistencyViolation(
                "IDENTITY",
                "Deal identity is incomplete.",
            )
        )

    if (
        not isinstance(deal.version, int)
        or isinstance(deal.version, bool)
        or deal.version < 1
    ):
        violations.append(
            DealConsistencyViolation(
                "VERSION",
                "Deal version must be an integer >= 1.",
                "version",
            )
        )

    history = tuple(
        getattr(deal, "history", ())
    )

    previous_version = 0

    for entry in history:
        if entry.version != previous_version + 1:
            violations.append(
                DealConsistencyViolation(
                    "HISTORY_ORDER",
                    "Deal history versions are not contiguous.",
                    "history",
                )
            )
            break

        previous_version = entry.version

    if history and history[-1].version != deal.version:
        violations.append(
            DealConsistencyViolation(
                "HISTORY_HEAD",
                "Latest history version does not equal Deal version.",
                "history",
            )
        )

    relationships = tuple(
        getattr(deal, "participants", ())
    )

    relationship_keys = set()

    for relationship in relationships:
        try:
            relationship.assert_scope(
                deal_id=deal.deal_id,
                tenant_id=deal.tenant_id,
            )
        except ValueError as exc:
            violations.append(
                DealConsistencyViolation(
                    "PARTY_SCOPE",
                    str(exc),
                    "participants",
                )
            )

        if relationship.relationship_key in relationship_keys:
            violations.append(
                DealConsistencyViolation(
                    "PARTY_DUPLICATE",
                    "Duplicate party relationship.",
                    "participants",
                )
            )

        relationship_keys.add(
            relationship.relationship_key
        )

    offers = tuple(
        getattr(deal, "offers", ())
    )

    offer_ids = set()

    for offer in offers:
        if offer.deal_id != deal.deal_id:
            violations.append(
                DealConsistencyViolation(
                    "OFFER_SCOPE",
                    "Offer belongs to a different Deal.",
                    "offers",
                )
            )

        if offer.tenant_id != deal.tenant_id:
            violations.append(
                DealConsistencyViolation(
                    "OFFER_TENANT",
                    "Offer belongs to a different tenant.",
                    "offers",
                )
            )

        if offer.offer_id in offer_ids:
            violations.append(
                DealConsistencyViolation(
                    "OFFER_DUPLICATE",
                    "Duplicate offer identity.",
                    "offers",
                )
            )

        offer_ids.add(offer.offer_id)

    negotiation = getattr(
        deal,
        "negotiation",
        None,
    )

    if negotiation is not None:
        if negotiation.deal_id != deal.deal_id:
            violations.append(
                DealConsistencyViolation(
                    "NEGOTIATION_SCOPE",
                    "Negotiation belongs to another Deal.",
                    "negotiation",
                )
            )

        if negotiation.active_offer_id not in offer_ids:
            violations.append(
                DealConsistencyViolation(
                    "NEGOTIATION_OFFER",
                    "Active negotiation offer is absent.",
                    "negotiation",
                )
            )

    milestones = tuple(
        getattr(deal, "milestones", ())
    )

    expected_sequence = 1
    previous_status: DealStatus | None = None
    previous_version = 0

    for milestone in milestones:
        if milestone.sequence != expected_sequence:
            violations.append(
                DealConsistencyViolation(
                    "MILESTONE_SEQUENCE",
                    "Milestone sequence is not contiguous.",
                    "milestones",
                )
            )

        if milestone.deal_version <= previous_version:
            violations.append(
                DealConsistencyViolation(
                    "MILESTONE_VERSION",
                    "Milestone versions must strictly increase.",
                    "milestones",
                )
            )

        if (
            previous_status is not None
            and milestone.from_status
            is not previous_status
        ):
            violations.append(
                DealConsistencyViolation(
                    "MILESTONE_CHAIN",
                    "Milestone status chain is broken.",
                    "milestones",
                )
            )

        if milestone.deal_id != deal.deal_id:
            violations.append(
                DealConsistencyViolation(
                    "MILESTONE_SCOPE",
                    "Milestone belongs to another Deal.",
                    "milestones",
                )
            )

        if milestone.tenant_id != deal.tenant_id:
            violations.append(
                DealConsistencyViolation(
                    "MILESTONE_TENANT",
                    "Milestone belongs to another tenant.",
                    "milestones",
                )
            )

        expected_sequence += 1
        previous_version = milestone.deal_version
        previous_status = milestone.to_status

    if milestones and previous_status is not deal.status:
        violations.append(
            DealConsistencyViolation(
                "CURRENT_STATUS",
                "Deal status does not match the latest milestone.",
                "status",
            )
        )

    ownership = getattr(
        deal,
        "ownership_binding",
        None,
    )

    if ownership is not None:
        try:
            ownership.assert_scope(
                deal_id=deal.deal_id,
                tenant_id=deal.tenant_id,
            )
        except ValueError as exc:
            violations.append(
                DealConsistencyViolation(
                    "OWNERSHIP_SCOPE",
                    str(exc),
                    "ownership_binding",
                )
            )

    for evidence in tuple(
        getattr(deal, "evidence", ())
    ):
        try:
            evidence.assert_scope(
                deal_id=deal.deal_id,
                tenant_id=deal.tenant_id,
            )
        except ValueError as exc:
            violations.append(
                DealConsistencyViolation(
                    "EVIDENCE_SCOPE",
                    str(exc),
                    "evidence",
                )
            )

    for audit in tuple(
        getattr(deal, "audit_log", ())
    ):
        try:
            audit.assert_scope(
                deal_id=deal.deal_id,
                tenant_id=deal.tenant_id,
            )
        except ValueError as exc:
            violations.append(
                DealConsistencyViolation(
                    "AUDIT_SCOPE",
                    str(exc),
                    "audit_log",
                )
            )

    return DealConsistencyResult(
        valid=not violations,
        checked=checked,
        violations=tuple(violations),
    )
