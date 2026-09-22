import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from capability_reuse_guard import (
    CapabilityRecord,
    CapabilityRequest,
    CapabilityReuseGuard,
    ReuseDecision,
    ReuseReason,
)


def test_exact_capability_id_is_reused():
    guard = CapabilityReuseGuard()
    existing = [
        CapabilityRecord(
            capability_id="CAP-DEAL-OWNERSHIP",
            name="Deal Ownership",
            responsibility="Protect immutable ownership of a real estate deal",
            architecture_ids=("ARCH-011",),
            source_of_truth="deal_domain",
        )
    ]
    result = guard.evaluate(
        CapabilityRequest(
            capability_id="CAP-DEAL-OWNERSHIP",
            name="Deal Ownership",
            responsibility="Protect immutable ownership of a real estate deal",
            architecture_ids=("ARCH-011",),
            source_of_truth="deal_domain",
        ),
        existing,
    )
    assert result.decision == ReuseDecision.REUSE
    assert result.reason == ReuseReason.EXACT_CAPABILITY
    assert result.selected_capability_id == "CAP-DEAL-OWNERSHIP"


def test_same_responsibility_different_name_is_reused():
    guard = CapabilityReuseGuard()
    existing = [
        CapabilityRecord(
            capability_id="CAP-CUSTOMER-ATTRIBUTION",
            name="Customer Attribution",
            responsibility="Protect customer attribution to HOMIO broker",
            architecture_ids=("ARCH-013",),
            source_of_truth="lead_domain",
        )
    ]
    result = guard.evaluate(
        CapabilityRequest(
            capability_id="CAP-BROKER-CUSTOMER-BINDING",
            name="Broker Customer Binding",
            responsibility="Protect customer attribution to HOMIO broker",
            architecture_ids=("ARCH-013",),
            source_of_truth="lead_domain",
        ),
        existing,
    )
    assert result.decision == ReuseDecision.REUSE


def test_structural_overlap_requires_extension():
    guard = CapabilityReuseGuard()
    existing = [
        CapabilityRecord(
            capability_id="CAP-DEAL-EVIDENCE",
            name="Deal Evidence",
            responsibility="Store event evidence for a deal record",
            architecture_ids=("ARCH-014",),
            source_of_truth="deal_domain",
            inputs=("deal_id", "event"),
            outputs=("evidence_record",),
        )
    ]
    result = guard.evaluate(
        CapabilityRequest(
            capability_id="CAP-DEAL-AUDIT-EVIDENCE",
            name="Deal Audit Evidence",
            responsibility="Store audit records for deal events",
            architecture_ids=("ARCH-014",),
            source_of_truth="deal_domain",
            inputs=("deal_id", "event"),
            outputs=("evidence_record",),
        ),
        existing,
    )
    assert result.decision == ReuseDecision.EXTEND
    assert result.selected_capability_id == "CAP-DEAL-EVIDENCE"


def test_multiple_strong_candidates_block_as_ambiguous():
    guard = CapabilityReuseGuard()
    existing = [
        CapabilityRecord(
            capability_id="CAP-A",
            name="Ownership Guard",
            responsibility="Protect immutable ownership of a transaction",
            architecture_ids=("ARCH-011",),
            source_of_truth="transaction_domain",
        ),
        CapabilityRecord(
            capability_id="CAP-B",
            name="Ownership Protection",
            responsibility="Protect immutable ownership of a transaction",
            architecture_ids=("ARCH-011",),
            source_of_truth="transaction_domain",
        ),
    ]
    result = guard.evaluate(
        CapabilityRequest(
            capability_id="CAP-C",
            name="Transaction Ownership",
            responsibility="Protect immutable ownership of a transaction",
            architecture_ids=("ARCH-011",),
            source_of_truth="transaction_domain",
        ),
        existing,
    )
    assert result.decision == ReuseDecision.BLOCK
    assert result.reason == ReuseReason.MULTIPLE_MATCHES_AMBIGUOUS
    assert not result.allowed_to_create


def test_unrelated_capability_can_be_created():
    guard = CapabilityReuseGuard()
    existing = [
        CapabilityRecord(
            capability_id="CAP-LEAD",
            name="Lead Attribution",
            responsibility="Attribute inbound customer demand to a source",
            architecture_ids=("ARCH-004",),
            source_of_truth="lead_domain",
        )
    ]
    result = guard.evaluate(
        CapabilityRequest(
            capability_id="CAP-INVENTORY-GEO",
            name="Inventory Geospatial Search",
            responsibility="Search inventory by verified geographic radius",
            architecture_ids=("ARCH-023",),
            source_of_truth="search_index",
        ),
        existing,
    )
    assert result.decision == ReuseDecision.CREATE_NEW
    assert result.allowed_to_create


def test_creation_can_be_disabled():
    guard = CapabilityReuseGuard()
    result = guard.evaluate(
        CapabilityRequest(
            capability_id="CAP-NEW",
            name="New Capability",
            responsibility="Unrelated new responsibility",
            allow_create_new=False,
        ),
        [],
    )
    assert result.decision == ReuseDecision.BLOCK
    assert not result.allowed_to_create


def test_catalog_change_invalidates_prior_decision():
    guard = CapabilityReuseGuard()
    original = guard.evaluate(
        CapabilityRequest(
            capability_id="CAP-NEW",
            name="New Capability",
            responsibility="Unrelated new responsibility",
        ),
        [],
    )
    current = [
        CapabilityRecord(
            capability_id="CAP-EXISTING",
            name="Existing Capability",
            responsibility="Existing responsibility",
        )
    ]
    revalidated = guard.revalidate(original, current)
    assert revalidated.decision == ReuseDecision.BLOCK
    assert revalidated.reason == ReuseReason.CATALOG_CHANGED
    assert not revalidated.allowed_to_create


def test_expected_catalog_fingerprint_can_force_revalidation():
    guard = CapabilityReuseGuard()
    existing = [
        CapabilityRecord(
            capability_id="CAP-A",
            name="Existing",
            responsibility="Existing responsibility",
        )
    ]
    fingerprint = guard.fingerprint_catalog(existing)
    changed = list(existing)
    changed.append(
        CapabilityRecord(
            capability_id="CAP-B",
            name="Another",
            responsibility="Another responsibility",
        )
    )
    result = guard.evaluate(
        CapabilityRequest(
            capability_id="CAP-C",
            name="New",
            responsibility="New responsibility",
        ),
        changed,
        expected_catalog_fingerprint=fingerprint,
    )
    assert result.decision == ReuseDecision.BLOCK
    assert result.reason == ReuseReason.CATALOG_CHANGED


def test_decision_is_machine_serializable():
    guard = CapabilityReuseGuard()
    result = guard.evaluate(
        CapabilityRequest(
            capability_id="CAP-NEW",
            name="New Capability",
            responsibility="Unique responsibility",
        ),
        [],
    )
    payload = result.to_dict()
    assert payload["decision"] == "CREATE_NEW"
    assert payload["allowed_to_create"] is True
    assert payload["request_fingerprint"]
    assert payload["catalog_fingerprint"]
