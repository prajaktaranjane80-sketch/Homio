from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True, slots=True)
class HandoffRecord:
    handoff_id: str
    mission_id: str
    current_gate: str | None
    current_task: str | None
    current_subtask: str | None
    status: str
    blockers: tuple[str, ...]
    next_action: str | None
    evidence_fingerprint: str | None


class HandoffRuntime:
    """Compact resumable handoff artifact."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write(
        self,
        record: HandoffRecord,
    ) -> None:
        self.path.write_text(
            json.dumps(
                asdict(record),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def read(self) -> HandoffRecord | None:
        if not self.path.exists():
            return None

        data = json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )

        return HandoffRecord(
            handoff_id=str(data["handoff_id"]),
            mission_id=str(data["mission_id"]),
            current_gate=data.get("current_gate"),
            current_task=data.get("current_task"),
            current_subtask=data.get("current_subtask"),
            status=str(data["status"]),
            blockers=tuple(data.get("blockers", [])),
            next_action=data.get("next_action"),
            evidence_fingerprint=data.get(
                "evidence_fingerprint"
            ),
        )
