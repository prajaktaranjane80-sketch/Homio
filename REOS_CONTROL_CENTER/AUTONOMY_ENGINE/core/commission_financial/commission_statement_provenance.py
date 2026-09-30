from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..contract_primitives import fingerprint


class CommissionStatementProvenanceError(
    ValueError
):
    """Invalid statement provenance."""


@dataclass(frozen=True, slots=True)
class CommissionStatementProvenance:
    source_type: str
    source_reference: str
    source_version: int
    invoice_references: tuple[str, ...]
    settlement_references: tuple[str, ...]
    reconciliation_references: tuple[str, ...]
    adjustment_references: tuple[str, ...]
    tax_assessment_references: tuple[str, ...]
    evidence_reference: str
    authorization_reference: str
    captured_at: datetime

    def __post_init__(self) -> None:
        for field in (
            "source_type",
            "source_reference",
            "evidence_reference",
            "authorization_reference",
        ):
            value = getattr(self, field)

            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                raise CommissionStatementProvenanceError(
                    f"{field} must be non-empty text."
                )

            object.__setattr__(
                self,
                field,
                value.strip(),
            )

        if (
            isinstance(
                self.source_version,
                bool,
            )
            or not isinstance(
                self.source_version,
                int,
            )
            or self.source_version < 1
        ):
            raise CommissionStatementProvenanceError(
                "source_version must be positive."
            )

        for field in (
            "invoice_references",
            "settlement_references",
            "reconciliation_references",
            "adjustment_references",
            "tax_assessment_references",
        ):
            values = tuple(
                getattr(
                    self,
                    field,
                )
            )

            if any(
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
                for value in values
            ):
                raise CommissionStatementProvenanceError(
                    f"{field} contains invalid references."
                )

            if len(values) != len(set(values)):
                raise CommissionStatementProvenanceError(
                    f"{field} contains duplicate references."
                )

            object.__setattr__(
                self,
                field,
                tuple(
                    value.strip()
                    for value in values
                ),
            )

        captured_at = self.captured_at

        if (
            not isinstance(
                captured_at,
                datetime,
            )
            or captured_at.tzinfo is None
            or captured_at.utcoffset() is None
        ):
            raise CommissionStatementProvenanceError(
                "captured_at must be timezone-aware."
            )

        object.__setattr__(
            self,
            "captured_at",
            captured_at.astimezone(
                timezone.utc
            ),
        )

    @property
    def provenance_fingerprint(self) -> str:
        return fingerprint(
            self.to_dict(
                include_fingerprint=False
            )
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "source_type": self.source_type,
            "source_reference": (
                self.source_reference
            ),
            "source_version": (
                self.source_version
            ),
            "invoice_references": list(
                self.invoice_references
            ),
            "settlement_references": list(
                self.settlement_references
            ),
            "reconciliation_references": list(
                self.reconciliation_references
            ),
            "adjustment_references": list(
                self.adjustment_references
            ),
            "tax_assessment_references": list(
                self.tax_assessment_references
            ),
            "evidence_reference": (
                self.evidence_reference
            ),
            "authorization_reference": (
                self.authorization_reference
            ),
            "captured_at": (
                self.captured_at.isoformat()
            ),
        }

        if include_fingerprint:
            result[
                "provenance_fingerprint"
            ] = self.provenance_fingerprint

        return result


__all__ = [
    "CommissionStatementProvenance",
    "CommissionStatementProvenanceError",
]
