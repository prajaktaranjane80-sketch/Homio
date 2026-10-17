from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from ..contract_primitives import fingerprint
from ..deal_transaction.deal import Deal
from ..deal_transaction.deal_ownership_integration import DealOwnershipBinding
from ..deal_transaction.deal_parties import DealPartyLifecycle, DealPartyRole
from .commission_allocation import CommissionAllocation
from .commission_attribution import CommissionAttributionBinding
from .commission_contract import CommissionPartyType
from .financial_domain import FinancialCurrencyMismatchError, MonetaryAmount


CORE008_COMMISSION_PARTICIPANT_SPLIT_SCHEMA_VERSION = 1


class CommissionParticipantSplitError(ValueError):
    """Base error for a commission split mapped to Deal participants."""


class CommissionParticipantSplitValidationError(CommissionParticipantSplitError):
    """Allocation, attribution, ownership and Deal participants do not agree."""


@dataclass(frozen=True, slots=True)
class CommissionParticipantSplitLine:
    allocation_id: str
    entitlement_id: str
    party_type: str
    party_id: str
    deal_role: str
    relationship_key: str
    relationship_version: int
    amount: MonetaryAmount
    allocation_ratio: Decimal
    rank: int

    def __post_init__(self) -> None:
        for field in (
            "allocation_id",
            "entitlement_id",
            "party_type",
            "party_id",
            "deal_role",
            "relationship_key",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise CommissionParticipantSplitValidationError(
                    f"{field} must be non-empty text."
                )
            object.__setattr__(self, field, value.strip())

        for field in ("relationship_version", "rank"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise CommissionParticipantSplitValidationError(
                    f"{field} must be a positive integer."
                )

        if not isinstance(self.amount, MonetaryAmount):
            raise CommissionParticipantSplitValidationError(
                "amount must be MonetaryAmount."
            )
        if self.amount.amount < 0:
            raise CommissionParticipantSplitValidationError(
                "Split amounts cannot be negative."
            )

        try:
            ratio = Decimal(str(self.allocation_ratio))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise CommissionParticipantSplitValidationError(
                "allocation_ratio must be a decimal."
            ) from exc
        if not ratio.is_finite() or ratio < 0 or ratio > 100:
            raise CommissionParticipantSplitValidationError(
                "allocation_ratio must be finite and between 0 and 100."
            )
        object.__setattr__(self, "allocation_ratio", ratio)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allocation_id": self.allocation_id,
            "entitlement_id": self.entitlement_id,
            "party": {"party_type": self.party_type, "party_id": self.party_id},
            "deal_participant": {
                "role": self.deal_role,
                "relationship_key": self.relationship_key,
                "relationship_version": self.relationship_version,
            },
            "amount": self.amount.to_dict(),
            "allocation_ratio": format(self.allocation_ratio, "f"),
            "rank": self.rank,
        }


@dataclass(frozen=True, slots=True)
class CommissionParticipantSplit:
    """Immutable cross-reference; CORE-006 remains Deal authority."""

    tenant_id: str
    commission_id: str
    allocation_set_id: str
    calculation_id: str
    deal_id: str
    deal_version: int
    lead_id: str
    ownership_binding_id: str
    ownership_record_id: str
    allocation_fingerprint: str
    attribution_fingerprint: str
    total_amount: MonetaryAmount
    lines: tuple[CommissionParticipantSplitLine, ...]

    def __post_init__(self) -> None:
        for field in (
            "tenant_id",
            "commission_id",
            "allocation_set_id",
            "calculation_id",
            "deal_id",
            "lead_id",
            "ownership_binding_id",
            "ownership_record_id",
            "allocation_fingerprint",
            "attribution_fingerprint",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise CommissionParticipantSplitValidationError(
                    f"{field} must be non-empty text."
                )
            object.__setattr__(self, field, value.strip())

        if (
            isinstance(self.deal_version, bool)
            or not isinstance(self.deal_version, int)
            or self.deal_version < 1
        ):
            raise CommissionParticipantSplitValidationError(
                "deal_version must be a positive integer."
            )
        if not isinstance(self.total_amount, MonetaryAmount):
            raise CommissionParticipantSplitValidationError(
                "total_amount must be MonetaryAmount."
            )

        lines = tuple(self.lines)
        if not lines or any(not isinstance(x, CommissionParticipantSplitLine) for x in lines):
            raise CommissionParticipantSplitValidationError(
                "At least one valid split line is required."
            )
        if len({x.allocation_id for x in lines}) != len(lines):
            raise CommissionParticipantSplitValidationError(
                "Duplicate allocation IDs are not allowed."
            )
        party_keys = {(x.party_type, x.party_id) for x in lines}
        if len(party_keys) != len(lines):
            raise CommissionParticipantSplitValidationError(
                "A typed participant cannot appear more than once in a split."
            )
        rank_values = [x.rank for x in lines]
        if len(set(rank_values)) != len(rank_values):
            raise CommissionParticipantSplitValidationError(
                "Split rank values must be unique."
            )

        currencies = {x.amount.currency.identity_key for x in lines}
        if currencies != {self.total_amount.currency.identity_key}:
            raise FinancialCurrencyMismatchError(
                "Every split line must use the total allocation currency."
            )
        amount_sum = sum((x.amount.amount for x in lines), Decimal("0"))
        if amount_sum != self.total_amount.amount:
            raise CommissionParticipantSplitValidationError(
                "Participant split amounts must equal the allocation total exactly."
            )

        ratio_sum = sum((x.allocation_ratio for x in lines), Decimal("0"))
        expected_ratio = (
            Decimal("0") if self.total_amount.amount == 0 else Decimal("100")
        )
        if ratio_sum != expected_ratio:
            raise CommissionParticipantSplitValidationError(
                f"Participant split ratios must total {expected_ratio}."
            )
        object.__setattr__(self, "lines", lines)

    @classmethod
    def from_authoritative_sources(
        cls,
        allocation: CommissionAllocation,
        deal: Deal,
        attribution: CommissionAttributionBinding,
    ) -> "CommissionParticipantSplit":
        """Resolve all split recipients against the current canonical Deal."""
        if not isinstance(allocation, CommissionAllocation):
            raise CommissionParticipantSplitValidationError(
                "allocation must be CommissionAllocation."
            )
        if not isinstance(deal, Deal):
            raise CommissionParticipantSplitValidationError(
                "deal must be Deal."
            )
        if not isinstance(attribution, CommissionAttributionBinding):
            raise CommissionParticipantSplitValidationError(
                "attribution must be CommissionAttributionBinding."
            )

        if (
            allocation.tenant_id != deal.tenant_id
            or attribution.tenant_id != deal.tenant_id
        ):
            raise CommissionParticipantSplitValidationError(
                "Allocation, attribution and Deal tenant scopes differ."
            )
        if attribution.deal_id != deal.deal_id:
            raise CommissionParticipantSplitValidationError(
                "Attribution deal reference does not match the supplied Deal."
            )
        if attribution.commission_id != allocation.commission_id:
            raise CommissionParticipantSplitValidationError(
                "Attribution commission does not match the allocation."
            )
        if deal.version != attribution.deal_version:
            raise CommissionParticipantSplitValidationError(
                "Deal version does not match attribution; rebuild the binding from the current Deal."
            )
        if deal.updated_at.isoformat() != attribution.deal_updated_at:
            raise CommissionParticipantSplitValidationError(
                "Deal timestamp does not match attribution."
            )

        ownership = deal.ownership_binding
        if not isinstance(ownership, DealOwnershipBinding):
            raise CommissionParticipantSplitValidationError(
                "Deal has no authoritative ownership binding."
            )
        try:
            ownership.assert_scope(deal_id=deal.deal_id, tenant_id=deal.tenant_id)
        except (TypeError, ValueError) as exc:
            raise CommissionParticipantSplitValidationError(
                "Ownership binding crosses Deal or tenant scope."
            ) from exc

        if (
            ownership.binding_id != attribution.ownership_binding_id
            or ownership.ownership_record_id != attribution.ownership_record_id
            or ownership.owner_id != attribution.owner_id
            or ownership.reference_key != attribution.ownership_reference_key
            or ownership.authority != attribution.ownership_authority
            or ownership.authority_version != attribution.ownership_authority_version
            or ownership.bound_at.isoformat() != attribution.ownership_bound_at
            or ownership.lead_id != attribution.lead_id
        ):
            raise CommissionParticipantSplitValidationError(
                "Deal ownership binding does not match the attribution binding."
            )

        valid_contract_refs = {
            ownership.ownership_record_id,
            ownership.binding_id,
            ownership.reference_key,
        }
        if attribution.ownership_reference not in valid_contract_refs:
            raise CommissionParticipantSplitValidationError(
                "Contract ownership reference no longer resolves to the Deal."
            )

        contract_party_found = any(
            line.party.party_type.value == attribution.entitled_party_type
            and line.party.party_id == attribution.entitled_party_id
            for line in allocation.lines
        )
        if not contract_party_found:
            raise CommissionParticipantSplitValidationError(
                "Commission contract's entitled party must be present in the allocation split."
            )

        role_map = {
            CommissionPartyType.BROKER: {DealPartyRole.BROKER},
            CommissionPartyType.BROKERAGE: {DealPartyRole.BROKER},
            CommissionPartyType.AGENT: {DealPartyRole.REPRESENTATIVE},
            CommissionPartyType.REFERRAL_PARTY: {DealPartyRole.REPRESENTATIVE},
            CommissionPartyType.PARTNER: {
                DealPartyRole.BUILDER,
                DealPartyRole.SELLER,
                DealPartyRole.REPRESENTATIVE,
            },
        }

        split_lines: list[CommissionParticipantSplitLine] = []
        for allocation_line in allocation.lines:
            allowed_roles = role_map.get(allocation_line.party.party_type)
            if not allowed_roles:
                raise CommissionParticipantSplitValidationError(
                    "Commission party type has no supported Deal relationship mapping."
                )

            for participant in deal.participants:
                try:
                    participant.assert_scope(
                        deal_id=deal.deal_id,
                        tenant_id=deal.tenant_id,
                    )
                except (TypeError, ValueError) as exc:
                    raise CommissionParticipantSplitValidationError(
                        "Deal participant crosses Deal or tenant scope."
                    ) from exc

            matches = [
                participant
                for participant in deal.participants
                if participant.party_id == allocation_line.party.party_id
                and participant.role in allowed_roles
            ]
            if len(matches) != 1:
                raise CommissionParticipantSplitValidationError(
                    "Allocation recipient does not resolve to exactly one compatible Deal participant."
                )
            participant = matches[0]
            if participant.lifecycle is not DealPartyLifecycle.ACTIVE:
                raise CommissionParticipantSplitValidationError(
                    "Allocation recipient is not an active Deal participant."
                )

            split_lines.append(
                CommissionParticipantSplitLine(
                    allocation_id=allocation_line.allocation_id,
                    entitlement_id=allocation_line.entitlement_id,
                    party_type=allocation_line.party.party_type.value,
                    party_id=allocation_line.party.party_id,
                    deal_role=participant.role.value,
                    relationship_key=participant.relationship_key,
                    relationship_version=participant.relationship_version,
                    amount=allocation_line.amount,
                    allocation_ratio=allocation_line.allocation_ratio,
                    rank=allocation_line.rank,
                )
            )

        return cls(
            tenant_id=allocation.tenant_id,
            commission_id=allocation.commission_id,
            allocation_set_id=allocation.allocation_set_id,
            calculation_id=allocation.calculation_id,
            deal_id=deal.deal_id,
            deal_version=deal.version,
            lead_id=attribution.lead_id,
            ownership_binding_id=ownership.binding_id,
            ownership_record_id=ownership.ownership_record_id,
            allocation_fingerprint=allocation.immutable_fingerprint,
            attribution_fingerprint=attribution.immutable_fingerprint,
            total_amount=allocation.total_amount,
            lines=tuple(split_lines),
        )

    @property
    def immutable_fingerprint(self) -> str:
        return fingerprint(self.to_dict(include_fingerprint=False))

    def to_dict(self, *, include_fingerprint: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "binding_type": "CORE-008.COMMISSION_PARTICIPANT_SPLIT",
            "schema_version": CORE008_COMMISSION_PARTICIPANT_SPLIT_SCHEMA_VERSION,
            "authorities": {
                "allocation": "CORE-008",
                "deal": "CORE-006",
                "lead_attribution": "CORE-003",
                "ownership": "ARCH-011",
            },
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "allocation_set_id": self.allocation_set_id,
            "calculation_id": self.calculation_id,
            "deal": {"deal_id": self.deal_id, "version": self.deal_version},
            "lead_id": self.lead_id,
            "ownership_binding": {
                "binding_id": self.ownership_binding_id,
                "ownership_record_id": self.ownership_record_id,
            },
            "total_amount": self.total_amount.to_dict(),
            "lines": [line.to_dict() for line in self.lines],
            "allocation_fingerprint": self.allocation_fingerprint,
            "attribution_fingerprint": self.attribution_fingerprint,
        }
        if include_fingerprint:
            result["immutable_fingerprint"] = self.immutable_fingerprint
        return result


__all__ = [
    "CORE008_COMMISSION_PARTICIPANT_SPLIT_SCHEMA_VERSION",
    "CommissionParticipantSplitError",
    "CommissionParticipantSplitValidationError",
    "CommissionParticipantSplitLine",
    "CommissionParticipantSplit",
]