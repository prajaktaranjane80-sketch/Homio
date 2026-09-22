from capability_reuse_guard import CapabilityRecord
from capability_reuse_gate import CapabilityReuseGate
from protocols.action_protocol import ActionProposal


def _proposal(**payload):
    return ActionProposal(
        action_id="A-1",
        action="create_module",
        target="AUTONOMY_ENGINE/example.py",
        parameters={
            "creates_capability": True,
            "capability_operation": "CREATE",
            "capability_reuse": payload,
        },
    )


def test_duplicate_create_is_blocked_at_gate():
    existing = CapabilityRecord(
        capability_id="CAP-OWNERSHIP",
        name="Deal Ownership",
        responsibility="Protect immutable ownership of a deal",
        architecture_ids=("ARCH-011",),
        source_of_truth="deal_domain",
    )

    gate = CapabilityReuseGate(
        lambda: (existing,)
    )

    outcome = gate.evaluate_proposal(
        _proposal(
            capability_id="CAP-NEW",
            name="Transaction Ownership",
            responsibility="Protect immutable ownership of a deal",
            architecture_ids=["ARCH-011"],
            source_of_truth="deal_domain",
        )
    )

    assert outcome.required is True
    assert outcome.allowed is False
    assert outcome.result is not None

    assert (
        outcome.result.selected_capability_id
        == "CAP-OWNERSHIP"
    )


def test_unique_create_is_allowed_at_gate():
    gate = CapabilityReuseGate(
        lambda: ()
    )

    outcome = gate.evaluate_proposal(
        _proposal(
            capability_id="CAP-NEW",
            name="Unique Geospatial Search",
            responsibility=(
                "Search inventory by verified "
                "geographic radius"
            ),
            architecture_ids=["ARCH-023"],
            source_of_truth="search_index",
        )
    )

    assert outcome.allowed is True
    assert outcome.result is not None
    assert outcome.result.allowed_to_create is True


def test_missing_gate_metadata_blocks():
    gate = CapabilityReuseGate(
        lambda: ()
    )

    proposal = ActionProposal(
        action_id="A-2",
        action="create_module",
        target="example.py",
        parameters={
            "creates_capability": True,
        },
    )

    outcome = gate.evaluate_proposal(
        proposal
    )

    assert outcome.allowed is False

    assert (
        "invalid_capability_reuse_request"
        in outcome.blockers
    )


def test_catalog_change_revalidation_blocks_create():
    first = CapabilityRecord(
        capability_id="CAP-A",
        name="Existing",
        responsibility="Existing responsibility",
    )

    current = CapabilityRecord(
        capability_id="CAP-B",
        name="Changed",
        responsibility="Changed responsibility",
    )

    gate = CapabilityReuseGate(
        lambda: (first,)
    )

    outcome = gate.evaluate_proposal(
        _proposal(
            capability_id="CAP-NEW",
            name="Unique",
            responsibility="Unique responsibility",
        )
    )

    revalidated = gate.revalidate(
        outcome,
        current_catalog=(current,),
    )

    assert revalidated.allowed is False
    assert revalidated.result is not None
    assert (
        revalidated.decision.value
        == "BLOCK"
    )
