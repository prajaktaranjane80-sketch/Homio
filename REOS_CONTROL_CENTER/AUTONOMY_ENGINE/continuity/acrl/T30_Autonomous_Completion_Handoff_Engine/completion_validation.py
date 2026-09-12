from .completion_models import CompletionState

def validate_mission(mission) -> None:
    if not mission.mission_id or not mission.objective:
        raise ValueError("mission identity/objective required")

def validate_terminal_state(state: CompletionState, residual_work: tuple[str, ...], human_rejected: bool) -> None:
    if state == CompletionState.COMPLETED and (residual_work or human_rejected):
        raise ValueError("invalid finalization")
