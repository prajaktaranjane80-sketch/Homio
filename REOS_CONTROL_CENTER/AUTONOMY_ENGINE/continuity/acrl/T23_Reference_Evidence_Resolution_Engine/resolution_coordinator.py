from __future__ import annotations

from .evidence_identity import fingerprint
from .evidence_models import (
    EvidenceReference,
    ResolutionDecision,
    ResolutionRequest,
    ResolutionResult,
)
from .evidence_policy import (
    EvidencePolicy,
)
from .evidence_provenance import (
    EvidenceProvenance,
)
from .evidence_registry import (
    EvidenceRegistry,
)
from .evidence_resolver import (
    resolve_references,
)
from .evidence_validation import (
    validate_evidence,
    validate_resolution_request,
)
from .resolution_store import (
    ResolutionIdentityConflict,
    ResolutionReplayError,
    ResolutionStore,
)


def _make_result(
    *,
    decision,
    request,
    selected,
    candidates,
    rejected,
    conflicting,
    stale,
    missing,
    explanation,
):
    payload = {
        "resolution_id": (
            request.resolution_id
        ),
        "subject": request.subject,
        "decision": decision.value,
        "selected": (
            selected.evidence_id
            if selected
            else None
        ),
        "candidates": [
            item.evidence_id
            for item in candidates
        ],
        "rejected": [
            item.evidence_id
            for item in rejected
        ],
        "conflicting": [
            item.evidence_id
            for item in conflicting
        ],
        "stale": [
            item.evidence_id
            for item in stale
        ],
        "missing": list(
            missing
        ),
    }

    return ResolutionResult(
        schema_version="1.0",
        decision=decision,
        resolution_id=(
            request.resolution_id
        ),
        subject=request.subject,
        selected_evidence=selected,
        candidates=tuple(
            candidates
        ),
        rejected_evidence=tuple(
            rejected
        ),
        conflicting_evidence=tuple(
            conflicting
        ),
        stale_evidence=tuple(
            stale
        ),
        missing_evidence_ids=tuple(
            missing
        ),
        request_fingerprint=(
            fingerprint(
                request.to_dict()
            )
        ),
        resolution_fingerprint=(
            fingerprint(
                payload
            )
        ),
        explanation=explanation,
    )


def resolve_evidence(
    *,
    request: ResolutionRequest,
    evidence_references: tuple[
        EvidenceReference, ...
    ],
    registry: EvidenceRegistry,
    store: ResolutionStore,
    policy: EvidencePolicy | None = None,
) -> ResolutionResult:
    policy = (
        policy
        or EvidencePolicy()
    )

    EvidenceProvenance().validate()

    validate_resolution_request(
        request
    )

    registry_items: list[
        EvidenceReference
    ] = []

    for evidence in evidence_references:
        validate_evidence(
            evidence,
            policy,
        )

        if not registry.contains(
            evidence.evidence_id
        ):
            registry.register(
                evidence
            )

        registry_items.append(
            evidence
        )

    decision, selected, candidates, rejected, stale, missing, explanation = (
        resolve_references(
            request=request,
            evidence_items=tuple(
                registry_items
            ),
            policy=policy,
        )
    )

    conflicting = (
        tuple()
    )

    if (
        decision
        is ResolutionDecision.CONFLICT
    ):
        conflicting = tuple(
            candidates
        )

    result = _make_result(
        decision=decision,
        request=request,
        selected=selected,
        candidates=candidates,
        rejected=rejected,
        conflicting=conflicting,
        stale=stale,
        missing=missing,
        explanation=explanation,
    )

    if decision is ResolutionDecision.RESOLVED:
        existing = store.get(
            request.resolution_id
        )

        if existing is not None:
            if (
                existing.resolution_fingerprint
                == result.resolution_fingerprint
            ):
                return ResolutionResult(
                    schema_version=result.schema_version,
                    decision=(
                        ResolutionDecision.READ_ONLY
                    ),
                    resolution_id=(
                        result.resolution_id
                    ),
                    subject=result.subject,
                    selected_evidence=(
                        result.selected_evidence
                    ),
                    candidates=(
                        result.candidates
                    ),
                    rejected_evidence=(
                        result.rejected_evidence
                    ),
                    conflicting_evidence=(
                        result.conflicting_evidence
                    ),
                    stale_evidence=(
                        result.stale_evidence
                    ),
                    missing_evidence_ids=(
                        result.missing_evidence_ids
                    ),
                    request_fingerprint=(
                        result.request_fingerprint
                    ),
                    resolution_fingerprint=(
                        result.resolution_fingerprint
                    ),
                    explanation=(
                        "Existing identical "
                        "resolution reused read-only."
                    ),
                )

        try:
            store.put(
                result
            )
        except ResolutionReplayError:
            return result
        except ResolutionIdentityConflict:
            return ResolutionResult(
                schema_version=result.schema_version,
                decision=(
                    ResolutionDecision.FAIL_CLOSED
                ),
                resolution_id=(
                    result.resolution_id
                ),
                subject=result.subject,
                selected_evidence=None,
                candidates=(
                    result.candidates
                ),
                rejected_evidence=(
                    result.rejected_evidence
                ),
                conflicting_evidence=(
                    result.conflicting_evidence
                ),
                stale_evidence=(
                    result.stale_evidence
                ),
                missing_evidence_ids=(
                    result.missing_evidence_ids
                ),
                request_fingerprint=(
                    result.request_fingerprint
                ),
                resolution_fingerprint=(
                    result.resolution_fingerprint
                ),
                explanation=(
                    "Resolution identity collision "
                    "detected; failed closed."
                ),
            )

    return result
