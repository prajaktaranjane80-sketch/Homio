"""ACRL T12 public bridge.

Canonical implementation lives in:
T12_Resume_Safety_Validation.resume_safety_validation

This module only re-exports the canonical T12 capability.
No duplicate validation logic is permitted here.
"""

from **future** import annotations

from AUTONOMY_ENGINE.continuity.acrl.T12_Resume_Safety_Validation.resume_safety_validation import (
ResumeDecision,
ResumeSafetyAuthorityError,
ResumeSafetyBlockedError,
ResumeSafetyError,
ResumeSafetyIntegrityError,
ResumeSafetyReason,
ResumeSafetyReport,
ResumeSafetyRequest,
ResumeSafetyValidationError,
ResumeSafetyValidator,
is_safe_to_resume,
validate_resume_safety,
)

**all** = [
"ResumeDecision",
"ResumeSafetyAuthorityError",
"ResumeSafetyBlockedError",
"ResumeSafetyError",
"ResumeSafetyIntegrityError",
"ResumeSafetyReason",
"ResumeSafetyReport",
"ResumeSafetyRequest",
"ResumeSafetyValidationError",
"ResumeSafetyValidator",
"is_safe_to_resume",
"validate_resume_safety",
]
