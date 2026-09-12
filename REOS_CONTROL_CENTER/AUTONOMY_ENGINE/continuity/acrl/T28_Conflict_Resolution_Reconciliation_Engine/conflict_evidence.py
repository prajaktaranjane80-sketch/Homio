from .reconciliation_models import ConflictRecord


def required_evidence(conflict: ConflictRecord) -> bool:
    return conflict.severity.value in {"HIGH", "CRITICAL"}


def evidence_satisfies(
    conflict: ConflictRecord,
    evidence_ids: tuple[str, ...],
) -> bool:
    if not required_evidence(conflict):
        return True
    return bool(set(conflict.evidence_ids) & set(evidence_ids))
