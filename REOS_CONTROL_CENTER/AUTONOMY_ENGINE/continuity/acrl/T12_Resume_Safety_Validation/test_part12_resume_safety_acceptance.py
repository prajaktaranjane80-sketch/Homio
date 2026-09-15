"""ACRL T12 — PART 12 Resume Safety acceptance tests."""

from **future** import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.resume_safety_validation import (
ResumeDecision,
ResumeSafetyAuthorityError,
ResumeSafetyIntegrityError,
ResumeSafetyReason,
ResumeSafetyRequest,
ResumeSafetyValidator,
is_safe_to_resume,
validate_resume_safety,
)

def make_request(
*,
checkpoint_available: bool = True,
checkpoint_valid: bool = True,
state_available: bool = True,
state_valid: bool = True,
gate_available: bool = True,
gate_valid: bool = True,
authority_valid: bool = True,
integrity_valid: bool = True,
architecture_stable: bool = True,
recovery_safe: bool = True,
state_ambiguous: bool = False,
state_stale: bool = False,
) -> ResumeSafetyRequest:
return ResumeSafetyRequest(
checkpoint_available=checkpoint_available,
checkpoint_valid=checkpoint_valid,
state_available=state_available,
state_valid=state_valid,
gate_available=gate_available,
gate_valid=gate_valid,
authority_valid=authority_valid,
integrity_valid=integrity_valid,
architecture_stable=architecture_stable,
recovery_safe=recovery_safe,
state_ambiguous=state_ambiguous,
state_stale=state_stale,
)

def test_safe_resume_is_not_blind_continue() -> None:
report = validate_resume_safety(
make_request()
)

```
assert report.validated is True
assert (
    report.decision
    == ResumeDecision.SAFE_TO_RESUME
)
assert report.reason == ResumeSafetyReason.VALID
assert report.fail_closed is False
assert is_safe_to_resume(report) is True
```

def test_missing_checkpoint_blocks_resume() -> None:
report = validate_resume_safety(
make_request(
checkpoint_available=False
)
)

```
assert report.decision == (
    ResumeDecision.BLOCK_RESUME
)
assert report.reason == (
    ResumeSafetyReason.MISSING_CHECKPOINT
)
assert is_safe_to_resume(report) is False
```

def test_invalid_checkpoint_fails_closed() -> None:
report = validate_resume_safety(
make_request(
checkpoint_valid=False
)
)

```
assert report.decision == (
    ResumeDecision.FAIL_CLOSED
)
assert report.reason == (
    ResumeSafetyReason.CHECKPOINT_INVALID
)
assert report.fail_closed is True
```

def test_unavailable_state_blocks_resume() -> None:
report = validate_resume_safety(
make_request(
state_available=False
)
)

```
assert report.decision == (
    ResumeDecision.BLOCK_RESUME
)
assert is_safe_to_resume(report) is False
```

def test_invalid_state_fails_closed() -> None:
report = validate_resume_safety(
make_request(
state_valid=False
)
)

```
assert report.decision == (
    ResumeDecision.FAIL_CLOSED
)
assert report.fail_closed is True
```

def test_invalid_gate_fails_closed() -> None:
report = validate_resume_safety(
make_request(
gate_valid=False
)
)

```
assert report.decision == (
    ResumeDecision.FAIL_CLOSED
)
assert report.reason == (
    ResumeSafetyReason.GATE_INVALID
)
```

def test_unclear_authority_is_not_accepted() -> None:
with pytest.raises(
ResumeSafetyAuthorityError
):
validate_resume_safety(
make_request(
authority_valid=False
)
)

def test_integrity_failure_is_not_accepted() -> None:
with pytest.raises(
ResumeSafetyIntegrityError
):
validate_resume_safety(
make_request(
integrity_valid=False
)
)

def test_architecture_drift_fails_closed() -> None:
report = validate_resume_safety(
make_request(
architecture_stable=False
)
)

```
assert report.decision == (
    ResumeDecision.FAIL_CLOSED
)
assert report.reason == (
    ResumeSafetyReason.ARCHITECTURE_DRIFT
)
```

def test_ambiguous_state_fails_closed() -> None:
report = validate_resume_safety(
make_request(
state_ambiguous=True
)
)

```
assert report.decision == (
    ResumeDecision.FAIL_CLOSED
)
assert report.reason == (
    ResumeSafetyReason.AMBIGUOUS_STATE
)
```

def test_stale_state_blocks_resume() -> None:
report = validate_resume_safety(
make_request(
state_stale=True
)
)

```
assert report.decision == (
    ResumeDecision.BLOCK_RESUME
)
assert report.reason == (
    ResumeSafetyReason.STALE_STATE
)
```

def test_unsafe_recovery_blocks_resume() -> None:
report = validate_resume_safety(
make_request(
recovery_safe=False
)
)

```
assert report.decision == (
    ResumeDecision.BLOCK_RESUME
)
assert report.reason == (
    ResumeSafetyReason.RECOVERY_UNSAFE
)
```

def test_all_safety_conditions_are_required() -> None:
safety_fields = (
"checkpoint_valid",
"state_valid",
"gate_valid",
"architecture_stable",
"recovery_safe",
)

```
for field in safety_fields:
    report = validate_resume_safety(
        make_request(
            **{field: False}
        )
    )

    assert (
        report.decision
        != ResumeDecision.SAFE_TO_RESUME
    )
```

def test_resume_fingerprint_is_deterministic() -> None:
request = make_request()

```
first = ResumeSafetyValidator.fingerprint(
    request.to_dict()
)

second = ResumeSafetyValidator.fingerprint(
    request.to_dict()
)

assert first == second
assert len(first) == 64
```
