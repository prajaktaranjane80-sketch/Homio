"""
REOS Diagnostic Fingerprint
===========================

Deterministic fingerprint for a diagnostic snapshot.

This is an observation fingerprint.

It is NOT a replacement for:
- Control Center state
- ACRL state fingerprint
- Git commit identity
- checkpoint identity
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .diagnostic_models import DiagnosticReport


FINGERPRINT_ALGORITHM = "sha256"


class DiagnosticFingerprint:
    """
    Produces stable hashes from normalized diagnostic information.
    """

    @staticmethod
    def generate(
        report: DiagnosticReport,
    ) -> str:
        payload: dict[str, Any] = {
            "schema_version": report.schema_version,
            "result": report.result,
            "position": {
                "gate": report.position.gate,
                "task": report.position.task,
                "subtask": report.position.subtask,
            },
            "checks": [
                {
                    "key": check.key,
                    "status": check.status,
                    "summary": check.summary,
                    "cause": check.cause,
                    "next_action": check.next_action,
                }
                for check in report.checks
            ],
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(canonical).hexdigest()
