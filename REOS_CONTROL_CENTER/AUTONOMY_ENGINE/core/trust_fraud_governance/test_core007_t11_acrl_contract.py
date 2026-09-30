"""CORE-007 Point 11 — ACRL reconstruction regression."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ..contract_primitives import fingerprint
from ..event_platform.event_acrl_contract import (
    ACRLIntegrationBoundary,
)
from .governance_acrl_contract import (
    GovernanceACRLArtifact,
    GovernanceACRLArtifactDescriptor,
    GovernanceACRLCheckpoint,
    GovernanceACRLContract,
    GovernanceACRLError,
    GovernanceACRLIntegrityError,
    GovernanceACRLScopeError,
)


def _boundary(payload):
    return ACRLIntegrationBoundary(
        reconstruct=lambda _event_id: payload,
        discover_dependencies=lambda key: [key],
        detect_drift=lambda expected, actual: (
            expected != actual
        ),
    )


def _descriptor(
    *,
    artifact_type,
    tenant_id,
    payload,
):
    return GovernanceACRLArtifactDescriptor(
        artifact_id="artifact-1",
        artifact_type=artifact_type,
        tenant_id=tenant_id,
        contract_key="CORE007:test:1",
        version=1,
        fingerprint=fingerprint(payload),
        provenance_reference="provenance-1",
    )


def test_signal_reconstruction_is_scope_and_integrity_checked():
    tenant = "tenant-1"

    payload = {
        "tenant_id": tenant,
        "signal_id": "signal-1",
        "value": "observed",
    }

    contract = GovernanceACRLContract(
        _boundary(payload)
    )

    descriptor = _descriptor(
        artifact_type=(
            GovernanceACRLArtifact.TRUST_SIGNAL
        ),
        tenant_id=tenant,
        payload=payload,
    )

    result = contract.reconstruct_signal(
        event_id=uuid4(),
        descriptor=descriptor,
    )

    assert result["signal_id"] == "signal-1"


def test_cross_tenant_reconstruction_is_rejected():
    payload = {
        "tenant_id": "tenant-other",
        "signal_id": "signal-1",
    }

    descriptor = (
        GovernanceACRLArtifactDescriptor(
            artifact_id="signal-1",
            artifact_type=(
                GovernanceACRLArtifact.TRUST_SIGNAL
            ),
            tenant_id="tenant-1",
            contract_key="CORE007:test:1",
            version=1,
            fingerprint=fingerprint(payload),
            provenance_reference="prov-1",
        )
    )

    contract = GovernanceACRLContract(
        _boundary(payload)
    )

    with pytest.raises(
        GovernanceACRLScopeError
    ):
        contract.reconstruct_signal(
            event_id=uuid4(),
            descriptor=descriptor,
        )


def test_reconstruction_fingerprint_drift_is_rejected():
    payload = {
        "tenant_id": "tenant-1",
        "signal_id": "signal-1",
    }

    descriptor = (
        GovernanceACRLArtifactDescriptor(
            artifact_id="signal-1",
            artifact_type=(
                GovernanceACRLArtifact.TRUST_SIGNAL
            ),
            tenant_id="tenant-1",
            contract_key="CORE007:test:1",
            version=1,
            fingerprint="f" * 64,
            provenance_reference="prov-1",
        )
    )

    contract = GovernanceACRLContract(
        _boundary(payload)
    )

    with pytest.raises(
        GovernanceACRLIntegrityError
    ):
        contract.reconstruct_signal(
            event_id=uuid4(),
            descriptor=descriptor,
        )


def test_checkpoint_scope_is_enforced():
    checkpoint = GovernanceACRLCheckpoint(
        checkpoint_id="checkpoint-1",
        tenant_id="tenant-1",
        sequence=10,
        event_id=uuid4(),
    )

    GovernanceACRLContract.validate_checkpoint(
        checkpoint,
        tenant_id="tenant-1",
    )

    with pytest.raises(
        GovernanceACRLScopeError
    ):
        GovernanceACRLContract.validate_checkpoint(
            checkpoint,
            tenant_id="tenant-2",
        )


def test_acrl_boundary_remains_external_authority():
    contract = GovernanceACRLContract(
        _boundary(
            {"tenant_id": "tenant-1"}
        )
    )

    assert contract.dependencies(
        "CORE007:test:1"
    ) == ("CORE007:test:1",)

    assert contract.drift_detected(
        expected_fingerprint="a",
        actual_fingerprint="b",
    )


def test_artifact_type_is_enforced():
    payload = {
        "tenant_id": "tenant-1",
        "signal_id": "signal-1",
    }

    descriptor = _descriptor(
        artifact_type=(
            GovernanceACRLArtifact.FRAUD_SIGNAL
        ),
        tenant_id="tenant-1",
        payload=payload,
    )

    contract = GovernanceACRLContract(
        _boundary(payload)
    )

    with pytest.raises(
        GovernanceACRLError
    ):
        contract.reconstruct_signal(
            event_id=uuid4(),
            descriptor=descriptor,
        )
