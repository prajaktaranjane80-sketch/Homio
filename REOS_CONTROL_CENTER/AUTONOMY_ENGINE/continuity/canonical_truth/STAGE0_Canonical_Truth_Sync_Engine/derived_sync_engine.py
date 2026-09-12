from __future__ import annotations

import json
from pathlib import Path

from .sync_receipt import build_receipt
from .sync_store import SyncStore
from .truth_fingerprint import digest
from .truth_models import CanonicalManifest, ReconciliationPlan, SyncStatus


class DerivedSyncEngine:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.store = SyncStore(self.root)

    def _derived_payload(self, manifest: CanonicalManifest) -> dict:
        return {
            "schema_version": "1.0",
            "project": manifest.project,
            "authority": "REOS_CONTROL_CENTER/data/state.json",
            "branch": manifest.branch,
            "state_digest": manifest.state_digest,
            "state_revision": manifest.state_revision,
            "current_gate": manifest.current_gate,
            "current_task": manifest.current_task,
            "current_subtask": manifest.current_subtask,
            "status": manifest.execution_status,
            "generated_from_manifest": manifest.manifest_digest,
        }

    def synchronize(self, manifest: CanonicalManifest, plan: ReconciliationPlan):
        if plan.blocked:
            receipt = build_receipt(plan, SyncStatus.BLOCKED, (), plan.targets)
            self.store.write_json("sync_receipt.json", receipt.__dict__)
            return receipt

        payload = self._derived_payload(manifest)
        synchronized: list[str] = []

        # Only derived truth artifacts are written. Canonical state is never mutated here.
        continuity = self.root / "PROJECT_CONTINUITY" / "continuity_state.json"
        continuity.parent.mkdir(parents=True, exist_ok=True)
        continuity.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        synchronized.append(continuity.as_posix())

        next_chat = self.root / "REOS_NEXT_CHAT.txt"
        next_chat.write_text(
            "HOMIO / REOS — CANONICAL CONTROL HANDOFF\n"
            "=" * 72
            + "\n"
            + f"CURRENT_GATE={manifest.current_gate}\n"
            + f"CURRENT_TASK={manifest.current_task}\n"
            + f"CURRENT_SUBTASK={manifest.current_subtask or ''}\n"
            + f"STATUS={manifest.execution_status}\n"
            + f"STATE_DIGEST={manifest.state_digest}\n"
            + "AUTHORITY=REOS_CONTROL_CENTER/data/state.json\n"
            + "RULE=CHAT_IS_NOT_PROJECT_MEMORY\n"
            + f"MANIFEST={manifest.manifest_digest}\n",
            encoding="utf-8",
        )
        synchronized.append(next_chat.as_posix())

        manifest_path = self.store.write_json("truth_manifest.json", {
            "schema_version": manifest.schema_version,
            "project": manifest.project,
            "branch": manifest.branch,
            "authority_id": manifest.authority_id,
            "canonical_state_path": manifest.canonical_state_path,
            "state_digest": manifest.state_digest,
            "state_revision": manifest.state_revision,
            "current_gate": manifest.current_gate,
            "current_task": manifest.current_task,
            "current_subtask": manifest.current_subtask,
            "execution_status": manifest.execution_status,
            "manifest_digest": manifest.manifest_digest,
        })
        synchronized.append(manifest_path.as_posix())

        receipt = build_receipt(plan, SyncStatus.SYNCHRONIZED, synchronized, ())
        self.store.write_json("sync_receipt.json", receipt.__dict__)
        return receipt
