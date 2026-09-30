from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_tax import CommissionTaxAssessment


@dataclass(frozen=True, slots=True)
class CommissionTaxSnapshot:
    assessment_id: str
    tenant_id: str
    commission_id: str
    invoice_id: str
    assessment_version: int
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_assessment(
        cls,
        assessment: CommissionTaxAssessment,
    ) -> "CommissionTaxSnapshot":
        if not isinstance(
            assessment,
            CommissionTaxAssessment,
        ):
            raise TypeError(
                "assessment must be CommissionTaxAssessment."
            )

        payload = assessment.to_dict(
            include_fingerprint=False
        )

        return cls(
            assessment_id=assessment.assessment_id,
            tenant_id=assessment.tenant_id,
            commission_id=assessment.commission_id,
            invoice_id=assessment.invoice_id,
            assessment_version=(
                assessment.assessment_version
            ),
            canonical_payload=payload,
            snapshot_fingerprint=fingerprint(
                payload
            ),
        )

    def verify(self) -> bool:
        return (
            self.snapshot_fingerprint
            == fingerprint(
                self.canonical_payload
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "invoice_id": self.invoice_id,
            "assessment_version": (
                self.assessment_version
            ),
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionTaxSnapshot",
]
