from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from .unified_runtime_context import UnifiedRuntimeContext


class ContinuityControlDecision(str, Enum):
    CONTINUE = "CONTINUE"
    BLOCKED = "BLOCKED"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class ContinuityControlResult:
    mission_id: str
    context_fingerprint: str
    stages: tuple[str, ...]
    decision: ContinuityControlDecision
    blocking_stage: str | None
    explanation: str
    control_fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "mission_id": self.mission_id,
            "context_fingerprint": self.context_fingerprint,
            "stages": list(self.stages),
            "decision": self.decision.value,
            "blocking_stage": self.blocking_stage,
            "explanation": self.explanation,
            "control_fingerprint": self.control_fingerprint,
        }


def _decision_value(result: Any) -> str | None:
    if result is None:
        return None

    decision = getattr(result, "decision", None)

    if decision is None:
        return None

    value = getattr(
        decision,
        "value",
        decision,
    )

    if value is None:
        return None

    return str(value)


def _fingerprint(
    payload: dict[str, object],
) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def _result(
    *,
    context: UnifiedRuntimeContext,
    stages: list[str],
    decision: ContinuityControlDecision,
    blocking_stage: str | None,
    explanation: str,
) -> ContinuityControlResult:
    payload = {
        "mission_id": context.mission_id,
        "context_fingerprint": context.context_fingerprint,
        "stages": stages,
        "decision": decision.value,
        "blocking_stage": blocking_stage,
        "explanation": explanation,
    }

    return ContinuityControlResult(
        mission_id=context.mission_id,
        context_fingerprint=(
            context.context_fingerprint
        ),
        stages=tuple(stages),
        decision=decision,
        blocking_stage=blocking_stage,
        explanation=explanation,
        control_fingerprint=_fingerprint(
            payload
        ),
    )


def _verify_context(
    context: UnifiedRuntimeContext,
) -> str | None:
    if not isinstance(
        context,
        UnifiedRuntimeContext,
    ):
        return "Reconstructed context type is invalid."

    if context.schema_version != "1.0":
        return "Unsupported reconstructed context schema."

    if not context.mission_id.strip():
        return "Reconstructed context mission_id is missing."

    if not context.objective.strip():
        return "Reconstructed context objective is missing."

    if not context.context_fingerprint:
        return "Reconstructed context fingerprint is missing."

    if (
        context.architecture_authority
        != "FROZEN_APPROVED_ARCHITECTURE"
    ):
        return "Architecture authority is invalid."

    if (
        context.roadmap_authority
        != "REOS_CONTROL_CENTER"
    ):
        return "Roadmap authority is invalid."

    if (
        context.execution_state_authority
        != "REOS_CONTROL_CENTER/data/state.json"
    ):
        return "Execution-state authority is invalid."

    if (
        context.code_authority
        != "GIT_REPOSITORY"
    ):
        return "Code authority is invalid."

    if (
        context.continuity_authority
        != "DERIVED_FROM_EXECUTION_STATE"
    ):
        return "Continuity authority is invalid."

    if context.chat_authority != "NONE":
        return "Chat authority must remain NONE."

    expected_task_ids = tuple(
        f"T{number:02d}"
        for number in range(1, 31)
    )

    if context.acrl_task_ids != expected_task_ids:
        return "ACRL T01-T30 sequence is invalid."

    if not context.git_head_sha:
        return "Git HEAD identity is missing."

    if not context.git_fingerprint:
        return "Git fingerprint is missing."

    return None


def control_continuity(
    *,
    context: UnifiedRuntimeContext,
    continuity_result: Any,
    evidence_result: Any,
    loop_result: Any,
    scheduler_result: Any,
    reconciliation_result: Any,
    decision_result: Any,
) -> ContinuityControlResult:
    """
    Join reconstructed context with the existing autonomous control chain.

    Flow:
        RECONSTRUCT
        -> VERIFY
        -> DEPENDENCY CHECK
        -> CONFLICT CHECK
        -> HUMAN BOUNDARY
        -> CONTINUE / BLOCK

    This controller does not execute commands or mutate canonical state.
    """

    stages: list[str] = [
        "RECONSTRUCT"
    ]

    verification_error = _verify_context(
        context
    )

    if verification_error:
        stages.append("VERIFY")

        return _result(
            context=context,
            stages=stages,
            decision=(
                ContinuityControlDecision.FAIL_CLOSED
            ),
            blocking_stage="VERIFY",
            explanation=verification_error,
        )

    continuity_decision = _decision_value(
        continuity_result
    )

    evidence_decision = _decision_value(
        evidence_result
    )

    loop_decision = _decision_value(
        loop_result
    )

    if continuity_decision not in {
        "RECOVERED",
        "READ_ONLY",
    }:
        stages.append("VERIFY")

        return _result(
            context=context,
            stages=stages,
            decision=(
                ContinuityControlDecision.BLOCKED
            ),
            blocking_stage="VERIFY",
            explanation=(
                "T24 continuity is not safely recovered."
            ),
        )

    if evidence_decision not in {
        "RESOLVED",
        "READ_ONLY",
    }:
        stages.append("VERIFY")

        return _result(
            context=context,
            stages=stages,
            decision=(
                ContinuityControlDecision.BLOCKED
            ),
            blocking_stage="VERIFY",
            explanation=(
                "T23 evidence resolution is not valid."
            ),
        )

    if loop_decision not in {
        "STARTED",
        "CONTINUE",
    }:
        stages.append("VERIFY")

        if loop_decision in {
            "REPLAY_DETECTED",
            "FAIL_CLOSED",
        }:
            final_decision = (
                ContinuityControlDecision.FAIL_CLOSED
            )
        else:
            final_decision = (
                ContinuityControlDecision.BLOCKED
            )

        return _result(
            context=context,
            stages=stages,
            decision=final_decision,
            blocking_stage="VERIFY",
            explanation=(
                "T26 autonomous execution loop "
                "is not in a runnable state."
            ),
        )

    stages.append("VERIFY")
    stages.append("DEPENDENCY_CHECK")

    scheduler_decision = _decision_value(
        scheduler_result
    )

    if scheduler_decision == "RESOURCE_BLOCKED":
        stages.append("HUMAN_BOUNDARY")

        human_decision = _decision_value(
            decision_result
        )

        if human_decision in {
            "AUTONOMY_ALLOWED",
            "HUMAN_APPROVED",
        }:
            stages.pop()
            stages.append("CONFLICT_CHECK")
            stages.append("HUMAN_BOUNDARY")

        elif human_decision in {
            "HUMAN_REQUIRED",
            "WAITING_FOR_HUMAN",
        }:
            return _result(
                context=context,
                stages=stages,
                decision=(
                    ContinuityControlDecision
                    .WAITING_FOR_HUMAN
                ),
                blocking_stage="HUMAN_BOUNDARY",
                explanation=(
                    "Dependency resource boundary "
                    "requires human decision."
                ),
            )
        else:
            return _result(
                context=context,
                stages=stages,
                decision=(
                    ContinuityControlDecision.BLOCKED
                ),
                blocking_stage="HUMAN_BOUNDARY",
                explanation=(
                    "Dependency resource boundary "
                    "did not receive a valid human boundary result."
                ),
            )

    elif scheduler_decision != "SCHEDULED":
        return _result(
            context=context,
            stages=stages,
            decision=(
                ContinuityControlDecision.BLOCKED
            ),
            blocking_stage="DEPENDENCY_CHECK",
            explanation=(
                "T27 dependency scheduler did not "
                "produce executable scheduled work."
            ),
        )

    stages.append("CONFLICT_CHECK")

    reconciliation_decision = _decision_value(
        reconciliation_result
    )

    if reconciliation_decision in {
        "NO_SAFE_RESOLUTION",
        "FAIL_CLOSED",
        "BLOCKED",
        "CONFLICT_UNRESOLVED",
    }:
        return _result(
            context=context,
            stages=stages,
            decision=(
                ContinuityControlDecision.BLOCKED
            ),
            blocking_stage="CONFLICT_CHECK",
            explanation=(
                "T28 conflict reconciliation "
                "did not produce a safe resolution."
            ),
        )

    stages.append("HUMAN_BOUNDARY")

    human_decision = _decision_value(
        decision_result
    )

    if human_decision in {
        "AUTONOMY_ALLOWED",
        "HUMAN_APPROVED",
    }:
        return _result(
            context=context,
            stages=stages,
            decision=(
                ContinuityControlDecision.CONTINUE
            ),
            blocking_stage=None,
            explanation=(
                "Reconstructed context passed "
                "verification, dependency, conflict "
                "and human-boundary controls."
            ),
        )

    if human_decision in {
        "HUMAN_REQUIRED",
        "WAITING_FOR_HUMAN",
    }:
        return _result(
            context=context,
            stages=stages,
            decision=(
                ContinuityControlDecision
                .WAITING_FOR_HUMAN
            ),
            blocking_stage="HUMAN_BOUNDARY",
            explanation=(
                "Autonomous continuation is waiting "
                "for an explicit human decision."
            ),
        )

    if human_decision in {
        "HUMAN_REJECTED",
        "HUMAN_EXPIRED",
    }:
        return _result(
            context=context,
            stages=stages,
            decision=(
                ContinuityControlDecision.BLOCKED
            ),
            blocking_stage="HUMAN_BOUNDARY",
            explanation=(
                "Human boundary did not authorize continuation."
            ),
        )

    return _result(
        context=context,
        stages=stages,
        decision=(
            ContinuityControlDecision.FAIL_CLOSED
        ),
        blocking_stage="HUMAN_BOUNDARY",
        explanation=(
            "Human-boundary decision is missing or invalid."
        ),
    )


__all__ = [
    "ContinuityControlDecision",
    "ContinuityControlResult",
    "control_continuity",
]
