from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .commission_acrl_contract import (
    ACRLSourceReference,
    FinancialReconstructionSubject,
    CommissionACRLValidationError,
)


class CommissionACRLEvidenceError(ValueError):
    """CORE-008 ACRL evidence-discoverability error."""


@dataclass(frozen=True, slots=True)
class FinancialEvidenceReference:
    subject: FinancialReconstructionSubject
    evidence_kind: str
    evidence_id: str
    fingerprint: str
    source_reference: ACRLSourceReference

    def __post_init__(self) -> None:
        if not isinstance(
            self.subject,
            FinancialReconstructionSubject,
        ):
            raise CommissionACRLValidationError(
                "subject must be FinancialReconstructionSubject"
            )

        for name, value in (
            ("evidence_kind", self.evidence_kind),
            ("evidence_id", self.evidence_id),
            ("fingerprint", self.fingerprint),
        ):
            if not isinstance(value, str) or not value.strip():
                raise CommissionACRLEvidenceError(
                    f"{name} cannot be empty"
                )

            object.__setattr__(
                self,
                name,
                value.strip(),
            )

        if not isinstance(
            self.source_reference,
            ACRLSourceReference,
        ):
            raise CommissionACRLEvidenceError(
                "source_reference is invalid"
            )

    def to_dict(self) -> dict:
        return {
            "subject": self.subject.value,
            "evidence_kind": self.evidence_kind,
            "evidence_id": self.evidence_id,
            "fingerprint": self.fingerprint,
            "source_reference": self.source_reference.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FinancialEvidenceIndex:
    """
    Immutable discoverability index.

    This indexes evidence references only.
    It does not become an evidence repository.
    """

    references: tuple[FinancialEvidenceReference, ...]

    def __post_init__(self) -> None:
        normalized = tuple(self.references)

        seen: set[tuple[str, str]] = set()

        for reference in normalized:
            key = (
                reference.evidence_kind,
                reference.evidence_id,
            )

            if key in seen:
                raise CommissionACRLEvidenceError(
                    "duplicate evidence reference"
                )

            seen.add(key)

        object.__setattr__(
            self,
            "references",
            normalized,
        )

    @classmethod
    def from_references(
        cls,
        references: Iterable[FinancialEvidenceReference],
    ) -> "FinancialEvidenceIndex":
        return cls(
            references=tuple(references)
        )

    def for_subject(
        self,
        subject: FinancialReconstructionSubject,
    ) -> tuple[FinancialEvidenceReference, ...]:
        return tuple(
            reference
            for reference in self.references
            if reference.subject == subject
        )

    def contains(
        self,
        evidence_kind: str,
        evidence_id: str,
    ) -> bool:
        return any(
            reference.evidence_kind == evidence_kind
            and reference.evidence_id == evidence_id
            for reference in self.references
        )

    def to_dict(self) -> dict:
        return {
            "count": len(self.references),
            "references": [
                reference.to_dict()
                for reference in self.references
            ],
        }


__all__ = [
    "CommissionACRLEvidenceError",
    "FinancialEvidenceIndex",
    "FinancialEvidenceReference",
]
