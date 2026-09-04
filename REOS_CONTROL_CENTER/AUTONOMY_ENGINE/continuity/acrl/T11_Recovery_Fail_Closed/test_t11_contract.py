"""T11 contract tests."""

from __future__ import annotations

from .recovery_guard import (
    RecoveryDecision,
    RecoveryRequest,
    evaluate_recovery,
)
from .recovery_identity import (
    RecoveryIdentityEngine,
)
from .recovery_metrics import (
    RecoveryMetricsEngine,
)
from .recovery_policy import (
    RecoveryPolicyEngine,
)
from .recovery_provenance import (
    RecoveryProvenanceEngine,
)
from .recovery_validation import (
    RecoveryValidationEngine,
)


def test_t11_contract_pipeline() -> None:
    request = RecoveryRequest(
        failure_type="timeout",
        component="execution",
        recoverable=True,
        authoritative=True,
        integrity_verified=True,
    )

    policy = RecoveryPolicyEngine.default()

    assert RecoveryPolicyEngine.validate(
        policy
    ) is True

    assert RecoveryValidationEngine.validate_request(
        request,
        policy,
    ) is True

    report = evaluate_recovery(request)

    assert report.decision == (
        RecoveryDecision.RECOVER
    )

    identity = RecoveryIdentityEngine.build(
        schema_version=report.schema_version,
        authority=report.authority,
        request_fingerprint=(
            report.request_fingerprint
        ),
        decision=report.decision.value,
    )

    assert RecoveryIdentityEngine.validate(
        identity
    ) is True

    provenance = RecoveryProvenanceEngine.build(
        source_layer="T10_DRIFT_DETECTION",
        source_identity=identity.identity_fingerprint,
        source_fingerprint=(
            report.request_fingerprint
        ),
        recovery_policy_version=policy.version,
    )

    assert RecoveryProvenanceEngine.validate(
        provenance
    ) is True

    metrics = RecoveryMetricsEngine.collect(
        report
    )

    assert metrics.decision == "RECOVER"