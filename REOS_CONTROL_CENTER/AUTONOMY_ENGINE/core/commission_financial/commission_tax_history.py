from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_tax import CommissionTaxAssessment


class CommissionTaxHistoryError(
    ValueError
):
    """Invalid tax-assessment history."""


@dataclass(frozen=True, slots=True)
class CommissionTaxHistoryEntry:
    assessment_id: str
    tenant_id: str
    commission_id: str
    invoice_id: str
    assessment_version: int
    state: str
    total_tax: str
    total_withholding: str
    assessment_fingerprint: str

    @classmethod
    def from_assessment(
        cls,
        assessment: CommissionTaxAssessment,
    ) -> "CommissionTaxHistoryEntry":
        if not isinstance(
            assessment,
            CommissionTaxAssessment,
        ):
            raise CommissionTaxHistoryError(
                "assessment must be CommissionTaxAssessment."
            )

        return cls(
            assessment_id=assessment.assessment_id,
            tenant_id=assessment.tenant_id,
            commission_id=assessment.commission_id,
            invoice_id=assessment.invoice_id,
            assessment_version=(
                assessment.assessment_version
            ),
            state=assessment.state.value,
            total_tax=format(
                assessment.total_tax.amount,
                "f",
            ),
            total_withholding=format(
                assessment.total_withholding.amount,
                "f",
            ),
            assessment_fingerprint=(
                assessment.immutable_fingerprint
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": (
                self.assessment_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "invoice_id": self.invoice_id,
            "assessment_version": (
                self.assessment_version
            ),
            "state": self.state,
            "total_tax": self.total_tax,
            "total_withholding": (
                self.total_withholding
            ),
            "assessment_fingerprint": (
                self.assessment_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionTaxHistory:
    entries: tuple[
        CommissionTaxHistoryEntry,
        ...
    ] = ()

    def append(
        self,
        assessment: CommissionTaxAssessment,
    ) -> "CommissionTaxHistory":
        entry = (
            CommissionTaxHistoryEntry
            .from_assessment(assessment)
        )

        if self.entries:
            latest = self.entries[-1]

            if (
                latest.tenant_id
                != entry.tenant_id
                or latest.assessment_id
                != entry.assessment_id
            ):
                raise CommissionTaxHistoryError(
                    "Tax assessment identity mismatch."
                )

            if (
                entry.assessment_version
                != latest.assessment_version + 1
            ):
                if (
                    entry.assessment_version
                    == latest.assessment_version
                    and entry.assessment_fingerprint
                    == latest.assessment_fingerprint
                ):
                    return self

                raise CommissionTaxHistoryError(
                    "Tax assessment versions must "
                    "advance sequentially."
                )

        elif entry.assessment_version != 1:
            raise CommissionTaxHistoryError(
                "First tax assessment version must be 1."
            )

        return CommissionTaxHistory(
            entries=self.entries + (entry,)
        )

    @property
    def latest(
        self,
    ) -> CommissionTaxHistoryEntry | None:
        return (
            self.entries[-1]
            if self.entries
            else None
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ]
        }


__all__ = [
    "CommissionTaxHistoryError",
    "CommissionTaxHistoryEntry",
    "CommissionTaxHistory",
]
