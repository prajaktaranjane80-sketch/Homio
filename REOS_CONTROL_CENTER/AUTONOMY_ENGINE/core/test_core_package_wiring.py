from __future__ import annotations


def test_autonomy_kernel_uses_canonical_package_namespace() -> None:
    from AUTONOMY_ENGINE.core.autonomy_kernel import AutonomyKernel
    from AUTONOMY_ENGINE.core.integrity import IntegrityEngine
    from AUTONOMY_ENGINE.core.models import ContextSnapshot
    from AUTONOMY_ENGINE.execution.guard import ExecutionGuard
    from AUTONOMY_ENGINE.memory.context_store import ContextStore
    from AUTONOMY_ENGINE.memory.evidence_ledger import EvidenceLedger

    assert AutonomyKernel.__module__ == (
        "AUTONOMY_ENGINE.core.autonomy_kernel"
    )

    globals_map = AutonomyKernel.__init__.__globals__

    assert globals_map["IntegrityEngine"] is IntegrityEngine
    assert globals_map["ContextSnapshot"] is ContextSnapshot
    assert globals_map["ExecutionGuard"] is ExecutionGuard
    assert globals_map["ContextStore"] is ContextStore
    assert globals_map["EvidenceLedger"] is EvidenceLedger