from reconciliation_identity import fingerprint


def resolution_fingerprint(resolutions) -> str:
    payload = [
        {
            "conflict_id": r.conflict_id,
            "kind": r.kind.value,
            "selected_value": r.selected_value,
            "rationale": r.rationale,
            "evidence_ids": list(r.evidence_ids),
        }
        for r in resolutions
    ]
    return fingerprint(payload)
