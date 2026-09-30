"""CORE-007 T06 — security/evidence integration boundary.

This module creates immutable evidence references around existing
risk/governance outputs.

It does NOT:
- create another audit store,
- create another event bus,
- replace ACRL evidence,
- replace Control Center checkpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Iterable


class GovernanceEvidenceError(ValueError):
    """Base evidence error."""


class EvidenceIntegrityError(
    GovernanceEvidenceError
):
    """Evidence reference integrity failure."""


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    reference: str
    source_type: str
    fingerprint: str | None
    tenant_id: str
    subject_id: str
    observed_at: datetime

    def __post_init__(self) -> None:
        if not self.reference.strip():
            raise GovernanceEvidenceError(
                "reference is required."
            )

        if not self.source_type.strip():
            raise GovernanceEvidenceError(
                "source_type is required."
            )

        if not self.tenant_id or not self.subject_id:
            raise GovernanceEvidenceError(
                "tenant_id and subject_id are required."
            )

        if (
            self.observed_at.tzinfo is None
            or self.observed_at.utcoffset() is None
        ):
            raise GovernanceEvidenceError(
                "observed_at must be timezone-aware."
            )

        object.__setattr__(
            self,
            "observed_at",
            self.observed_at.astimezone(timezone.utc),
        )


@dataclass(frozen=True, slots=True)
class GovernanceEvidenceEnvelope:
    tenant_id: str
    subject_id: str
    correlation_id: str
    policy_id: str
    policy_version: str
    links: tuple[EvidenceLink, ...]
    created_at: datetime
    envelope_fingerprint: str

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
    ) -> "GovernanceEvidenceEnvelope":
        normalized_time = created_at.astimezone(timezone.utc)

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
                    "observed_at": link.observed_at.isoformat(),
                }
                for link in ordered_links
            ],
            "created_at": normalized_time.isoformat(),
        }

        raw = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        fingerprint = hashlib.sha256(raw).hexdigest()

        return cls(
            tenant_id=tenant_id,
            subject_id=subject_id,
            correlation_id=correlation_id,
            policy_id=policy_id,
            policy_version=policy_version,
            links=ordered_links,
            created_at=normalized_time,
            envelope_fingerprint=fingerprint,
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
        )

        if (
            rebuilt.envelope_fingerprint
            != self.envelope_fingerprint
        ):
            raise EvidenceIntegrityError(
                "Evidence envelope fingerprint mismatch."
            )
