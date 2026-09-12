from __future__ import annotations

from datetime import datetime, timezone
import uuid


def event(event_type: str, payload: dict) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "time": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
