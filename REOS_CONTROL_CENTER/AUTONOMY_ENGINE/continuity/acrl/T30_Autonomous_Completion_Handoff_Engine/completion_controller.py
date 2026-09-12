from .completion_models import CompletionState, CompletionResult
from .completion_validation import validate_mission
from .proof_engine import evaluate_proof
from .residual_work_detector import detect_residual_work
from .dependency_closure import validate_dependency_closure
from .blocker_detector import classify_blockers
from .recovery_classifier import classify_recovery
from .completion_store import CompletionStore
from .next_mission_resolver import resolve_next_mission
from .handoff_builder import build_handoff
from .mission_identity import mission_fingerprint


def evaluate_completion(mission, *, evidence: dict[str, bool], dependency_graph: dict, completed_nodes: set[str], candidates=None, checkpoint_valid=True, execution_interrupted=False, evidence_consistent=True, store=None):
    validate_mission(mission)
    store = store or CompletionStore()
    proof = evaluate_proof(evidence, mission.required_dimensions)
    dep_ok, dep_gaps = validate_dependency_closure(dependency_graph, completed_nodes)
    residual = detect_residual_work(mission, proof, dep_gaps)
    blocker = classify_blockers(mission, dep_ok, residual)
    recovery = classify_recovery(checkpoint_valid=checkpoint_valid, execution_interrupted=execution_interrupted, evidence_consistent=evidence_consistent, human_rejected=mission.rejected_human_decision)
    if not evidence_consistent:
        state = CompletionState.RECOVERY_REQUIRED
        reason = "evidence inconsistency requires reconciliation"
    elif mission.rejected_human_decision:
        state = CompletionState.BLOCKED
        reason = "human rejection is terminal for autonomous continuation"
    elif recovery not in {"NO_RECOVERY"}:
        state = CompletionState.RECOVERY_REQUIRED
        reason = recovery
    elif not dep_ok or residual:
        state = CompletionState.BLOCKED if blocker.endswith("BLOCKED") else CompletionState.INCOMPLETE
        reason = blocker
    elif proof.failed or proof.missing:
        state = CompletionState.INCOMPLETE
        reason = "proof quorum incomplete"
    else:
        next_mission = resolve_next_mission(mission, candidates or [])
        state = CompletionState.HANDOFF_READY if next_mission else CompletionState.COMPLETED
        reason = "mission closure proven"
    next_mission = resolve_next_mission(mission, candidates or []) if state in {CompletionState.COMPLETED, CompletionState.HANDOFF_READY} else None
    handoff = build_handoff(mission, state.value, residual_work=residual, next_mission=next_mission, recovery_mode=recovery)
    return CompletionResult(state=state, confidence="HIGH" if state in {CompletionState.COMPLETED, CompletionState.HANDOFF_READY} else "BLOCKED", reason=reason, proof=proof, residual_work=residual, next_mission=next_mission, handoff_fingerprint=handoff.fingerprint, metadata={"recovery": recovery, "mission_fingerprint": mission_fingerprint(mission.__dict__)})
