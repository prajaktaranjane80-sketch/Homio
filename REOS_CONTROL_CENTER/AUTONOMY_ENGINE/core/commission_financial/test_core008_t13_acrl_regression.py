from __future__ import annotations

from .commission_acrl_contract import (
    ACRLSourceReference,
    CommissionACRLContract,
    FinancialReconstructionRequest,
    FinancialReconstructionSubject,
)
from .commission_acrl_evidence import (
    FinancialEvidenceIndex,
    FinancialEvidenceReference,
)
from .commission_acrl_reconstruction import (
    CommissionACRLReconstructor,
)
from .commission_acrl_conflict import (
    CommissionACRLConflictError,
    assert_no_reconstruction_conflict,
)


def test_acrl_contract_supports_all_financial_reconstruction_subjects() -> None:
    contract = CommissionACRLContract.default(
        tenant_id="tenant-a",
        commission_id="commission-001",
    )

    for subject in FinancialReconstructionSubject:
        assert contract.supports(subject)

    assert contract.evidence_discoverable is True
    assert contract.checkpoint_recovery_compatible is True
    assert contract.autonomous_state_mutation_allowed is False


def test_reconstruction_is_deterministic() -> None:
    request = FinancialReconstructionRequest(
        tenant_id="tenant-a",
        commission_id="commission-001",
        subject=FinancialReconstructionSubject.COMMISSION,
        source_references=(
            ACRLSourceReference(
                source_kind="COMMISSION_CONTRACT",
                source_id="contract-001",
                fingerprint="contract-fp-001",
            ),
            ACRLSourceReference(
                source_kind="COMMISSION_CALCULATION",
                source_id="calculation-001",
                fingerprint="calculation-fp-001",
            ),
        ),
    )

    reconstructor = CommissionACRLReconstructor(
        lambda supplied: {
            "commission_id": supplied.commission_id,
            "state": "RECONSTRUCTED",
            "version": 1,
        }
    )

    first = reconstructor.reconstruct(request)
    second = reconstructor.reconstruct(request)

    assert first.result_fingerprint == second.result_fingerprint
    assert first.deterministic_fingerprint == (
        second.deterministic_fingerprint
    )
    assert first.verify() is True
    assert second.verify() is True


def test_different_reconstruction_results_for_same_subject_conflict() -> None:
    request = FinancialReconstructionRequest(
        tenant_id="tenant-a",
        commission_id="commission-001",
        subject=FinancialReconstructionSubject.SETTLEMENT,
        source_references=(
            ACRLSourceReference(
                source_kind="SETTLEMENT",
                source_id="settlement-001",
                fingerprint="settlement-fp-001",
            ),
        ),
    )

    first_reconstructor = CommissionACRLReconstructor(
        lambda _: {
            "settlement_state": "CREATED",
            "amount": "1000.00",
        }
    )

    second_reconstructor = CommissionACRLReconstructor(
        lambda _: {
            "settlement_state": "COMPLETED",
            "amount": "1000.00",
        }
    )

    first = first_reconstructor.reconstruct(
        request
    )
    second = second_reconstructor.reconstruct(
        request
    )

    try:
        assert_no_reconstruction_conflict(
            first,
            second,
        )
    except CommissionACRLConflictError:
        pass
    else:
        raise AssertionError(
            "Conflicting reconstruction results were not rejected"
        )


def test_evidence_index_remains_reference_only() -> None:
    reference = ACRLSourceReference(
        source_kind="RECONSTRUCTION",
        source_id="reconstruction-001",
        fingerprint="reconstruction-fp-001",
    )

    evidence = FinancialEvidenceReference(
        subject=FinancialReconstructionSubject.RECONCILIATION,
        evidence_kind="RECONCILIATION",
        evidence_id="reconciliation-001",
        fingerprint="reconciliation-fp-001",
        source_reference=reference,
    )

    index = FinancialEvidenceIndex.from_references(
        [evidence]
    )

    assert index.contains(
        "RECONCILIATION",
        "reconciliation-001",
    )

    assert len(
        index.for_subject(
            FinancialReconstructionSubject.RECONCILIATION
        )
    ) == 1
