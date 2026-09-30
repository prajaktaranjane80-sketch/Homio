from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable
import hashlib
import json


class GovernanceEvidenceError(ValueError):
    """Base governance evidence error."""


class EvidenceIntegrityError(
    GovernanceEvidenceError
):
    """Evidence reference or envelope integrity failure."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceEvidenceError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _utc(value: datetime, field: str) -> datetime:
    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise GovernanceEvidenceError(
            f"{field} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    """One immutable evidence reference."""

    reference: str
    source_type: str
    fingerprint: str | None
    tenant_id: str
    subject_id: str
    observed_at: datetime

    provenance_reference: str = (
        "CORE-007.EVIDENCE"
    )

    def __post_init__(self) -> None:
        for name in (
            "reference",
            "source_type",
            "tenant_id",
            "subject_id",
            "provenance_reference",
        ):
            object.__setattr__(
                self,
                name,
                _text(
                    getattr(self, name),
                    name,
                ),
            )

        if self.fingerprint is not None:
            object.__setattr__(
                self,
                "fingerprint",
                _text(
                    self.fingerprint,
                    "fingerprint",
                ),
            )

        object.__setattr__(
            self,
            "observed_at",
            _utc(
                self.observed_at,
                "observed_at",
            ),
        )


@dataclass(frozen=True, slots=True)
class GovernanceEvidenceEnvelope:
    """
    Immutable evidence/explainability envelope.

    Explicit:
    - evidence reference
    - signal provenance
    - rule provenance
    - assessment explanation
    - decision explanation
    - historical snapshot
    - reproducibility
    - integrity
    """

    tenant_id: str
    subject_id: str
    correlation_id: str
    policy_id: str
    policy_version: str

    links: tuple[EvidenceLink, ...]

    created_at: datetime
    envelope_fingerprint: str

    signal_provenance: tuple[str, ...] = ()
    rule_provenance: tuple[str, ...] = ()
    assessment_explanation: str | None = None
    decision_explanation: str | None = None
    historical_snapshot: tuple[str, ...] = ()
    reproducibility: str = "DETERMINISTIC"

    evidence_integrity: str = "VERIFIED"

    @classmethod
    def build(
        cls,
        *,
        tenant_id: str,
        subject_id: str,
        correlation_id: str,
        policy_id: str,
        policy_version: str,
        links: Iterable[EvidenceLink],
        created_at: datetime,
        signal_provenance: tuple[str, ...] = (),
        rule_provenance: tuple[str, ...] = (),
        assessment_explanation: str | None = None,
        decision_explanation: str | None = None,
        historical_snapshot: tuple[str, ...] = (),
        reproducibility: str = "DETERMINISTIC",
    ) -> "GovernanceEvidenceEnvelope":
        tenant_id = _text(
            tenant_id,
            "tenant_id",
        )
        subject_id = _text(
            subject_id,
            "subject_id",
        )

        normalized_time = _utc(
            created_at,
            "created_at",
        )

        ordered_links = tuple(
            sorted(
                tuple(links),
                key=lambda item: (
                    item.source_type,
                    item.reference,
                    item.fingerprint or "",
                ),
            )
        )

        if not ordered_links:
            raise GovernanceEvidenceError(
                "At least one evidence link is required."
            )

        for link in ordered_links:
            if (
                link.tenant_id
                != tenant_id
                or link.subject_id
                != subject_id
            ):
                raise GovernanceEvidenceError(
                    "Evidence crosses tenant/subject scope."
                )

        signal_refs = tuple(
            sorted(
                {
                    _text(
                        item,
                        "signal_provenance",
                    )
                    for item in signal_provenance
                }
            )
        )

        rule_refs = tuple(
            sorted(
                {
                    _text(
                        item,
                        "rule_provenance",
                    )
                    for item in rule_provenance
                }
            )
        )

        history_refs = tuple(
            sorted(
                {
                    _text(
                        item,
                        "historical_snapshot",
                    )
                    for item in historical_snapshot
                }
            )
        )

        if assessment_explanation is not None:
            assessment_explanation = _text(
                assessment_explanation,
                "assessment_explanation",
            )

        if decision_explanation is not None:
            decision_explanation = _text(
                decision_explanation,
                "decision_explanation",
            )

        reproducibility = _text(
            reproducibility,
            "reproducibility",
        )

        payload = {
            "tenant_id": tenant_id,
            "subject_id": subject_id,
            "correlation_id": correlation_id,
            "policy_id": policy_id,
            "policy_version": policy_version,
            "links": [
                {
                    "reference": link.reference,
                    "source_type": link.source_type,
                    "fingerprint": link.fingerprint,
                    "tenant_id": link.tenant_id,
                    "subject_id": link.subject_id,
                    "observed_at": (
                        link.observed_at.isoformat()
                    ),
                    "provenance_reference": (
                        link.provenance_reference
                    ),
                }
                for link in ordered_links
            ],
            "signal_provenance": signal_refs,
            "rule_provenance": rule_refs,
            "assessment_explanation": (
                assessment_explanation
            ),
            "decision_explanation": (
                decision_explanation
            ),
            "historical_snapshot": history_refs,
            "reproducibility": reproducibility,
            "evidence_integrity": "VERIFIED",
            "created_at": (
                normalized_time.isoformat()
            ),
        }

        return cls(
            tenant_id=tenant_id,
            subject_id=subject_id,
            correlation_id=_text(
                correlation_id,
                "correlation_id",
            ),
            policy_id=_text(
                policy_id,
                "policy_id",
            ),
            policy_version=_text(
                policy_version,
                "policy_version",
            ),
            links=ordered_links,
            created_at=normalized_time,
            envelope_fingerprint=_fingerprint(
                payload
            ),
            signal_provenance=signal_refs,
            rule_provenance=rule_refs,
            assessment_explanation=(
                assessment_explanation
            ),
            decision_explanation=(
                decision_explanation
            ),
            historical_snapshot=history_refs,
            reproducibility=reproducibility,
            evidence_integrity="VERIFIED",
        )

    def verify(self) -> None:
        rebuilt = self.build(
            tenant_id=self.tenant_id,
            subject_id=self.subject_id,
            correlation_id=self.correlation_id,
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            links=self.links,
            created_at=self.created_at,
            signal_provenance=self.signal_provenance,
            rule_provenance=self.rule_provenance,
            assessment_explanation=(
                self.assessment_explanation
            ),
            decision_explanation=(
                self.decision_explanation
            ),
            historical_snapshot=(
                self.historical_snapshot
            ),
            reproducibility=self.reproducibility,
        )

        if (
            rebuilt.envelope_fingerprint
            != self.envelope_fingerprint
        ):
            raise EvidenceIntegrityError(
                "Evidence envelope fingerprint mismatch."
            )

        for link in self.links:
            if link.tenant_id != self.tenant_id:
                raise EvidenceIntegrityError(
                    "Evidence tenant mismatch."
                )

            if link.subject_id != self.subject_id:
                raise EvidenceIntegrityError(
                    "Evidence subject mismatch."
                )


__all__ = [
    "GovernanceEvidenceError",
    "EvidenceIntegrityError",
    "EvidenceLink",
    "GovernanceEvidenceEnvelope",
]
