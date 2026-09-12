from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .source_classifier import SourceClassifier
from .truth_fingerprint import digest
from .truth_models import ArtifactTruth, TruthRole


class DerivedArtifactReader:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.classifier = SourceClassifier()

    def _load_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def inspect(self, path: Path, artifact_id: str) -> ArtifactTruth:
        role = self.classifier.classify(path, self.root)
        if not path.exists():
            return ArtifactTruth(artifact_id, path.as_posix(), role, False, None, None, {})
        raw = path.read_bytes()
        semantic: Any
        try:
            semantic = self._load_json(path) if path.suffix.lower() == ".json" else path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError, json.JSONDecodeError):
            semantic = None
        return ArtifactTruth(
            artifact_id=artifact_id,
            path=path.as_posix(),
            role=role,
            present=True,
            digest=digest(raw.hex()),
            semantic_digest=digest(semantic) if semantic is not None else None,
            claims=self._extract_claims(semantic),
        )

    @staticmethod
    def _extract_claims(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            execution = value.get("execution")
            if isinstance(execution, dict):
                return {
                    "current_gate": execution.get("current_gate"),
                    "current_task": execution.get("current_task"),
                    "current_subtask": execution.get("current_subtask"),
                    "status": execution.get("status"),
                }
            if "current_gate" in value or "CURRENT_GATE" in value:
                return {
                    "current_gate": value.get("current_gate", value.get("CURRENT_GATE")),
                    "current_task": value.get("current_task", value.get("CURRENT_TASK")),
                    "current_subtask": value.get("current_subtask", value.get("CURRENT_SUBTASK")),
                    "status": value.get("status", value.get("STATUS")),
                }
        if isinstance(value, str):
            claims: dict[str, Any] = {}
            for line in value.splitlines():
                if "=" in line:
                    key, val = line.split("=", 1)
                    if key in {"CURRENT_GATE", "CURRENT_TASK", "CURRENT_SUBTASK", "STATUS"}:
                        claims[key.lower()] = val.strip()
            return claims
        return {}
