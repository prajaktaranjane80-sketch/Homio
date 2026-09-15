"""ACRL T10 — PART 10 Drift Detection acceptance tests."""

from **future** import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.drift_detection import (
DriftAuthorityError,
DriftDetectionEngine,
DriftDetectionError,
DriftSeverity,
DriftType,
create_drift_baseline,
detect_drift,
)

def make_context(
*,
gate: str = "CORE-005",
subtask: str = "CORE-005-T01",
) -> dict[str, dict[str, object]]:
"""Build deterministic authoritative reconstructed context."""

```
return {
    "project_identity": {
        "project": "HOMIO / REOS",
        "authority": "REOS_CONTROL_CENTER",
    },
    "architecture": {
        "status": "LOCKED",
        "version": "1.0",
    },
    "execution": {
        "current_gate": gate,
        "current_subtask": subtask,
        "status": "CONTROL_CENTER_DRIVEN",
    },
    "gate_continuity": {
        "current_gate": gate,
        "current_subtask": subtask,
    },
    "dependency_authority": {
        "authority": "REOS_CONTROL_CENTER",
        "status": "VALID",
    },
    "checkpoint": {
        "checkpoint_id": "CP-P10-001",
        "status": "VALID",
    },
}
```

def test_state_drift_is_detected() -> None:
baseline_context = make_context()

```
baseline = create_drift_baseline(
    baseline_context
)

current = make_context()

current["execution"][
    "current_subtask"
] = "CORE-005-T02"

report = detect_drift(
    baseline,
    current,
)

assert report.drift_detected is True

assert any(
    finding.drift_type
    == DriftType.EXECUTION
    for finding in report.findings
)
```

def test_architecture_drift_is_detected() -> None:
baseline = create_drift_baseline(
make_context()
)

```
current = make_context()

current["architecture"][
    "status"
] = "UNLOCKED"

report = detect_drift(
    baseline,
    current,
)

assert report.drift_detected is True
assert report.severity == (
    DriftSeverity.CRITICAL
)
assert report.fail_closed is True
```

def test_continuity_drift_is_detected() -> None:
baseline = create_drift_baseline(
make_context()
)

```
current = make_context()

current["gate_continuity"][
    "current_gate"
] = "CORE-006"

report = detect_drift(
    baseline,
    current,
)

assert report.drift_detected is True

assert any(
    finding.drift_type
    == DriftType.GATE_CONTINUITY
    for finding in report.findings
)
```

def test_stale_context_is_detected() -> None:
baseline = create_drift_baseline(
make_context(
gate="CORE-005",
subtask="CORE-005-T01",
)
)

```
stale_context = make_context(
    gate="CORE-005",
    subtask="CORE-005-T01",
)

# The reconstructed context is stale because the
# authoritative current position has moved forward.
stale_context["execution"][
    "current_gate"
] = "CORE-004"

report = detect_drift(
    baseline,
    stale_context,
)

assert report.drift_detected is True

assert any(
    finding.drift_type
    == DriftType.EXECUTION
    for finding in report.findings
)
```

def test_reconstruction_mismatch_is_detected() -> None:
baseline_context = make_context()

```
baseline = create_drift_baseline(
    baseline_context
)

reconstructed = make_context()

reconstructed["gate_continuity"][
    "current_subtask"
] = "CORE-005-T02"

report = detect_drift(
    baseline,
    reconstructed,
)

assert report.drift_detected is True
assert report.current_fingerprint != (
    report.baseline_fingerprint
)
```

def test_unexpected_authoritative_change_is_detected() -> None:
baseline = create_drift_baseline(
make_context()
)

```
current = make_context()

current["execution"][
    "unexpected_field"
] = "UNEXPECTED"

report = detect_drift(
    baseline,
    current,
)

assert report.drift_detected is True
```

def test_dependency_authority_drift_is_unsafe() -> None:
baseline = create_drift_baseline(
make_context()
)

```
current = make_context()

current["dependency_authority"][
    "authority"
] = "UNKNOWN"

report = detect_drift(
    baseline,
    current,
)

assert report.severity == DriftSeverity.HIGH
assert report.fail_closed is True

with pytest.raises(
    DriftDetectionError
):
    DriftDetectionEngine.detect_or_raise(
        baseline,
        current,
    )
```

def test_checkpoint_drift_is_reported() -> None:
baseline = create_drift_baseline(
make_context()
)

```
current = make_context()

current["checkpoint"][
    "checkpoint_id"
] = "CP-P10-999"

report = detect_drift(
    baseline,
    current,
)

assert report.drift_detected is True

assert any(
    finding.drift_type
    == DriftType.CHECKPOINT
    for finding in report.findings
)
```

def test_unchanged_reconstructed_context_is_trusted() -> None:
context = make_context()

```
baseline = create_drift_baseline(
    context
)

report = detect_drift(
    baseline,
    make_context(),
)

assert report.drift_detected is False
assert report.severity == DriftSeverity.NONE
assert report.fail_closed is False
assert report.findings == ()
```

def test_missing_reconstructed_context_is_not_trusted() -> None:
baseline = create_drift_baseline(
make_context()
)

```
current = make_context()

del current["checkpoint"]

with pytest.raises(
    DriftAuthorityError
):
    detect_drift(
        baseline,
        current,
    )
```

def test_baseline_tampering_prevents_trusted_detection() -> None:
baseline = create_drift_baseline(
make_context()
)

```
altered = dict(
    baseline.components
)

altered["architecture"] = {
    "status": "UNLOCKED",
}

object.__setattr__(
    baseline,
    "components",
    altered,
)

with pytest.raises(Exception):
    DriftDetectionEngine.detect(
        baseline,
        make_context(),
    )
```

def test_drift_detection_is_deterministic() -> None:
baseline = create_drift_baseline(
make_context()
)

```
current = make_context()

current["execution"][
    "current_subtask"
] = "CORE-005-T02"

first = detect_drift(
    baseline,
    current,
)

second = detect_drift(
    baseline,
    current,
)

assert first.to_dict() == (
    second.to_dict()
)
```
