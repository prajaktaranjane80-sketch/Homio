def load_state() -> dict[str, Any]:
    if not STATE.exists():
        raise SystemExit(f"Canonical state missing: {STATE}")

    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid state.json: {exc}") from exc

    if not isinstance(state, dict):
        raise SystemExit("Invalid state.json: canonical state must be an object.")

    integrity = state.get("integrity")

    if not isinstance(integrity, dict):
        raise SystemExit(
            "CANONICAL STATE INTEGRITY FAILURE: integrity metadata missing"
        )

    stored_hash = integrity.get("sha256")

    if not stored_hash:
        raise SystemExit(
            "CANONICAL STATE INTEGRITY FAILURE: SHA-256 missing"
        )

    calculated_hash = calculate_hash(state)

    if stored_hash != calculated_hash:
        raise SystemExit(
            "CANONICAL STATE INTEGRITY FAILURE: "
            "stored SHA-256 does not match canonical state"
        )

    state.setdefault("events", [])
    state.setdefault("checkpoints", [])
    state.setdefault("gate_plans", {})
    state.setdefault("session", {})

    return state
