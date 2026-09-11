from __future__ import annotations

from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_models import (
    ExecutionAuthorization,
)

from .patch_engine import (
    apply_patch,
    patch_fingerprint,
    validate_patch,
)
from .repair_authorization import validate_authorization
from .repair_identity import fingerprint
from .repair_models import (
    RepairDecision,
    RepairReason,
    RepairRequest,
    RepairResult,
    VerificationEvidence,
)
from .repair_policy import validate_policy
from .repair_provenance import RepairProvenance
from .repair_validation import validate_request
from .repair_workspace import (
    create_isolated_workspace,
    discard_workspace,
)
from .patch_verification import (
    tree_fingerprint,
    verify_patch,
)


def execute_repair_transaction(
    *,
    repository_root: Path | str,
    authorization: ExecutionAuthorization,
    request: RepairRequest,
    evidence: VerificationEvidence | None = None,
) -> RepairResult:
    policy = __import__(
        f"{__package__}.repair_models",
        fromlist=["RepairPolicy"],
    ).RepairPolicy()

    validate_policy(policy)
    RepairProvenance().validate()
    validate_authorization(authorization)
    validate_request(request, policy)
    validate_patch(request)

    baseline = tree_fingerprint(
        repository_root
    )

    if baseline != request.baseline_fingerprint:
        return RepairResult(
            schema_version="1.0",
            decision=RepairDecision.BLOCKED,
            reason=RepairReason.BASELINE_DRIFT,
            repair_id=request.repair_id,
            authorization_fingerprint=(
                request.authorization_fingerprint
            ),
            diagnosis_fingerprint=(
                request.diagnosis_fingerprint
            ),
            baseline_fingerprint=baseline,
            patch_fingerprint=patch_fingerprint(
                request.candidate_patch
            ),
            final_tree_fingerprint=baseline,
            changed_paths=(),
            attempt=request.attempt,
            verification=None,
            evidence_fingerprint=fingerprint(
                {
                    "reason": "BASELINE_DRIFT",
                    "repair_id": request.repair_id,
                }
            ),
        )

    workspace = create_isolated_workspace(
        repository_root
    )

    try:
        changed_paths = apply_patch(
            workspace,
            request,
        )

        if evidence is None:
            final_tree = tree_fingerprint(
                workspace
            )

            return RepairResult(
                schema_version="1.0",
                decision=RepairDecision.REPAIR_APPLIED,
                reason=RepairReason.VERIFICATION_REQUIRED,
                repair_id=request.repair_id,
                authorization_fingerprint=(
                    request.authorization_fingerprint
                ),
                diagnosis_fingerprint=(
                    request.diagnosis_fingerprint
                ),
                baseline_fingerprint=baseline,
                patch_fingerprint=patch_fingerprint(
                    request.candidate_patch
                ),
                final_tree_fingerprint=final_tree,
                changed_paths=changed_paths,
                attempt=request.attempt,
                verification=None,
                evidence_fingerprint=fingerprint(
                    {
                        "reason": (
                            "VERIFICATION_REQUIRED"
                        ),
                        "repair_id": request.repair_id,
                    }
                ),
            )

        verification = verify_patch(
            workspace=workspace,
            request=request,
            evidence=evidence,
        )

        if verification.passed:
            decision = RepairDecision.VERIFIED
            reason = RepairReason.VALID
        else:
            decision = RepairDecision.ROLLED_BACK
            reason = verification.reason

        return RepairResult(
            schema_version="1.0",
            decision=decision,
            reason=reason,
            repair_id=request.repair_id,
            authorization_fingerprint=(
                request.authorization_fingerprint
            ),
            diagnosis_fingerprint=(
                request.diagnosis_fingerprint
            ),
            baseline_fingerprint=baseline,
            patch_fingerprint=verification.patch_fingerprint,
            final_tree_fingerprint=(
                verification.final_tree_fingerprint
            ),
            changed_paths=(
                verification.changed_paths
            ),
            attempt=request.attempt,
            verification=verification,
            evidence_fingerprint=(
                verification.evidence.evidence_fingerprint
            ),
        )

    finally:
        discard_workspace(workspace)
