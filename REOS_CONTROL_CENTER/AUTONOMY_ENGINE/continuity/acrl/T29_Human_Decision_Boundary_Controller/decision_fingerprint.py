from .decision_identity import fingerprint


def decision_record_fingerprint(record) -> str:
    return fingerprint(
        {
            "decision_id": record.decision_id,
            "status": record.status.value,
            "boundary_decision": record.boundary_decision.value,
            "decision_type": record.decision_type.value,
            "decided_by": record.decided_by,
            "rationale": record.rationale,
        }
    )
