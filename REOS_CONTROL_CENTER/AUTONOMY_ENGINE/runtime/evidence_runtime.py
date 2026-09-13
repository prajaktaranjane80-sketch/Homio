from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    evidence_id: str
    kind: str
    source: str
    claim: str
    strength: str
    metadata: dict[str, Any]


class EvidenceRuntime:
    """Append-only evidence ledger."""

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def fingerprint(value: Any) -> str:
        raw = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def create(
        self,
        *,
        evidence_id: str,
        kind: str,
        source: str,
        claim: str,
        strength: str = "VERIFIED",
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceItem:
        if not all(
            isinstance(x, str) and x.strip()
            for x in (evidence_id, kind, source, claim)
        ):
            raise ValueError("evidence fields are required")

        return EvidenceItem(
            evidence_id=evidence_id,
            kind=kind,
            source=source,
            claim=claim,
            strength=strength,
            metadata=dict(metadata or {}),
        )

    def append(self, item: EvidenceItem) -> None:
        record = asdict(item)
        record["recorded_at"] = datetime.now(
            timezone.utc
        ).isoformat()
        record["fingerprint"] = self.fingerprint(record)

        with self.ledger_path.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

    def read_all(self) -> list[dict[str, Any]]:
        if not self.ledger_path.exists():
            return []

        result = []
        for line in self.ledger_path.read_text(
            encoding="utf-8"
        ).splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise RuntimeError(
                        "invalid evidence record"
                    )
                result.append(value)

        return result
