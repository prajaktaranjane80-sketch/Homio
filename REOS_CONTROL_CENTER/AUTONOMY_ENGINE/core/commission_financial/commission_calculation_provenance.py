from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..contract_primitives import fingerprint


class CommissionCalculationProvenanceError(
    ValueError
):
    """Invalid calculation provenance."""


def _text(
    value: str,
    field: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionCalculationProvenanceError(
            f"{field} must be non-empty text."
        )

    return value.strip()


def _aware(
    value: datetime,
    field: str,
) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionCalculationProvenanceError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class CommissionCalculationProvenance:
    """Immutable provenance reference for a calculation."""

    source_type: str
    source_reference: str
    source_version: int
    eligibility_reference: str
    contract_reference: str
    captured_at: datetime
    evidence_reference: str

    def __post_init__(self) -> None:
        for field in (
            "source_type",
            "source_reference",
            "eligibility_reference",
            "contract_reference",
            "evidence_reference",
        ):
            object.__setattr__(
                self,
                field,
                _text(
                    getattr(
                        self,
                        field,
                    ),
                    field,
                ),
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
            raise CommissionCalculationProvenanceError(
                "source_version must be positive."
            )

        object.__setattr__(
            self,
            "captured_at",
            _aware(
                self.captured_at,
                "captured_at",
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
        result: dict[str, Any] = {
            "source_type": (
                self.source_type
            ),
            "source_reference": (
                self.source_reference
            ),
            "source_version": (
                self.source_version
            ),
            "eligibility_reference": (
                self.eligibility_reference
            ),
            "contract_reference": (
                self.contract_reference
            ),
            "captured_at": (
                self.captured_at.isoformat()
            ),
            "evidence_reference": (
                self.evidence_reference
            ),
        }

        if include_fingerprint:
            result[
                "provenance_fingerprint"
            ] = self.provenance_fingerprint

        return result


__all__ = [
    "CommissionCalculationProvenance",
    "CommissionCalculationProvenanceError",
]
