from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..contract_primitives import fingerprint


class CommissionSettlementProvenanceError(
    ValueError
):
    """Invalid settlement provenance."""


@dataclass(frozen=True, slots=True)
class CommissionSettlementProvenance:
    source_type: str
    source_reference: str
    source_version: int
    allocation_reference: str
    authorization_reference: str
    evidence_reference: str
    captured_at: datetime

    def __post_init__(self) -> None:
        for field in (
            "source_type",
            "source_reference",
            "allocation_reference",
            "authorization_reference",
            "evidence_reference",
        ):
            value = getattr(
                self,
                field,
            )

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise CommissionSettlementProvenanceError(
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
            raise CommissionSettlementProvenanceError(
                "source_version must be positive."
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
            raise CommissionSettlementProvenanceError(
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
            "source_type": (
                self.source_type
            ),
            "source_reference": (
                self.source_reference
            ),
            "source_version": (
                self.source_version
            ),
            "allocation_reference": (
                self.allocation_reference
            ),
            "authorization_reference": (
                self.authorization_reference
            ),
            "evidence_reference": (
                self.evidence_reference
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
    "CommissionSettlementProvenance",
    "CommissionSettlementProvenanceError",
]
