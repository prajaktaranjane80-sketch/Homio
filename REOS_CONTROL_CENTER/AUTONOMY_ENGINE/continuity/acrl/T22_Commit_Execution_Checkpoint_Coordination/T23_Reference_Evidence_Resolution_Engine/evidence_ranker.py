from __future__ import annotations

from .evidence_models import (
    EvidenceReference,
    EvidenceStatus,
)
from .evidence_policy import (
    EvidencePolicy,
    authority_weight,
)


def rank_evidence(
    evidence: EvidenceReference,
    *,
    preferred_authorities,
    policy: EvidencePolicy,
) -> tuple[int, int, int, int, int, str]:
    preferred = (
        1
        if evidence.authority
        in preferred_authorities
        else 0
    )

    current = (
        1
        if evidence.status
        is EvidenceStatus.CURRENT
        else 0
    )

    canonical = (
        1
        if evidence.canonical
        else 0
    )

    immutable = (
        1
        if evidence.immutable
        else 0
    )

    authority = authority_weight(
        evidence.authority,
        policy,
    )

    return (
        preferred,
        current,
        canonical,
        immutable,
        authority,
        evidence.evidence_id,
    )


def sort_evidence(
    evidence_items,
    *,
    preferred_authorities,
    policy: EvidencePolicy,
):
    return tuple(
        sorted(
            evidence_items,
            key=lambda item: rank_evidence(
                item,
                preferred_authorities=(
                    preferred_authorities
                ),
                policy=policy,
            ),
            reverse=True,
        )
    )
