from __future__ import annotations

from dataclasses import dataclass

from .evidence_models import EvidenceAuthority


@dataclass(frozen=True, slots=True)
class EvidencePolicy:
    schema_version: str = "1.0"
    policy_version: str = "1.0"

    allow_unknown_status: bool = False
    allow_stale_selection: bool = False
    allow_non_immutable_evidence: bool = False
    allow_non_canonical_override: bool = False

    authority_weights: tuple[
        tuple[EvidenceAuthority, int], ...
    ] = (
        (
            EvidenceAuthority.CANONICAL_STATE,
            1000,
        ),
        (
            EvidenceAuthority.RESUME_SAFETY,
            950,
        ),
        (
            EvidenceAuthority.EXECUTION_CHECKPOINT,
            900,
        ),
        (
            EvidenceAuthority.EXECUTION_AUTHORIZATION,
            850,
        ),
        (
            EvidenceAuthority.GIT_TRANSACTION,
            800,
        ),
        (
            EvidenceAuthority.VERIFIED_REPAIR,
            750,
        ),
        (
            EvidenceAuthority.CHANGE_IMPACT,
            700,
        ),
        (
            EvidenceAuthority.TEST_DIAGNOSIS,
            650,
        ),
        (
            EvidenceAuthority.GENERAL_EVIDENCE,
            100,
        ),
    )


def authority_weight(
    authority: EvidenceAuthority,
    policy: EvidencePolicy,
) -> int:
    values = dict(
        policy.authority_weights
    )

    return values.get(
        authority,
        -1,
    )


def validate_policy(
    policy: EvidencePolicy,
) -> None:
    if policy.allow_stale_selection:
        raise ValueError(
            "T23 policy cannot select stale evidence."
        )

    if policy.allow_non_canonical_override:
        raise ValueError(
            "T23 policy cannot allow non-canonical override."
        )

    if policy.allow_unknown_status:
        raise ValueError(
            "T23 policy cannot silently select unknown evidence."
        )
