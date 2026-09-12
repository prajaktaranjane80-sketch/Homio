def validate_authority(
    *,
    continuity_fingerprint: str,
    evidence_fingerprint: str,
) -> None:
    if not continuity_fingerprint.strip():
        raise PermissionError("continuity authority missing")

    if not evidence_fingerprint.strip():
        raise PermissionError("evidence authority missing")
