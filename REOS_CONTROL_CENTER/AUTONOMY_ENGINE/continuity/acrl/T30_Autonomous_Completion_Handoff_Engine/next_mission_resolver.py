def resolve_next_mission(mission, candidates: list[dict]) -> str | None:
    ready = [c for c in candidates if c.get("ready") and not c.get("blocked")]
    if not ready:
        return None
    ready.sort(key=lambda c: (-int(c.get("priority", 0)), str(c.get("mission_id", ""))))
    return ready[0]["mission_id"]
