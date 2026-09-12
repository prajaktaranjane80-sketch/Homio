from .handoff_models import HandoffCapsule
from .handoff_fingerprint import handoff_fingerprint

def build_handoff(mission, state: str, residual_work=(), next_mission=None, recovery_mode="NO_RECOVERY"):
    payload = {
        "mission_id": mission.mission_id,
        "state": state,
        "completed": mission.completed_nodes,
        "residual_work": tuple(residual_work),
        "next_mission": next_mission,
        "recovery_mode": recovery_mode,
    }
    fp = handoff_fingerprint(payload)
    return HandoffCapsule(
        mission_id=mission.mission_id,
        state=state,
        summary=mission.objective,
        completed=mission.completed_nodes,
        residual_work=tuple(residual_work),
        next_mission=next_mission,
        recovery_mode=recovery_mode,
        fingerprint=fp,
        metadata={"schema": "T30-HANDOFF-1.0"},
    )
