from __future__ import annotations

from pathlib import Path

from .truth_models import TruthRole


class SourceClassifier:
    DERIVED_NAMES = {
        "REOS_NEXT_CHAT.txt",
        "NEW_CHAT_PACKET.txt",
        "continuity_state.json",
        "truth_manifest.json",
        "truth_conflict_report.json",
        "sync_receipt.json",
    }

    def classify(self, path: Path, root: Path) -> TruthRole:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        if relative == "data/state.json":
            return TruthRole.AUTHORITATIVE
        if path.name in self.DERIVED_NAMES:
            return TruthRole.DERIVED
        if relative.startswith("PROJECT_CONTINUITY/"):
            return TruthRole.DERIVED
        if relative.startswith("packets/"):
            return TruthRole.DERIVED
        if relative.endswith(".git/HEAD"):
            return TruthRole.CONTEXTUAL
        return TruthRole.CONTEXTUAL
