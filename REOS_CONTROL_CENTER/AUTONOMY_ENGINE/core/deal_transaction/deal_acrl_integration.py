from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class DealACRLBundle:
    deal_id: str
    tenant_id: str
    bundle_version: str
    deal_snapshot: Mapping[str, Any]
    reconstruction_fingerprint: str
    dependencies: tuple[str, ...]
    checkpoint_safe: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "bundle_version": self.bundle_version,
            "deal_snapshot": dict(
                self.deal_snapshot
            ),
            "reconstruction_fingerprint": (
                self.reconstruction_fingerprint
            ),
            "dependencies": list(
                self.dependencies
            ),
            "checkpoint_safe": self.checkpoint_safe,
        }


def _fingerprint(
    payload: Mapping[str, Any],
) -> str:
    body = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return sha256(
        body.encode("utf-8")
    ).hexdigest()


def build_acrl_bundle(
    deal: Any,
) -> DealACRLBundle:
    snapshot = deal.to_dict(
        include_contract=True
    )

    payload = {
        "deal_id": deal.deal_id,
        "tenant_id": deal.tenant_id,
        "snapshot": snapshot,
    }

    return DealACRLBundle(
        deal_id=deal.deal_id,
        tenant_id=deal.tenant_id,
        bundle_version="1.0",
        deal_snapshot=snapshot,
        reconstruction_fingerprint=(
            _fingerprint(payload)
        ),
        dependencies=(
            "CORE-001",
            "CORE-003",
            "CORE-004",
            "CORE-005",
            "ARCH-011",
            "ARCH-014",
        ),
        checkpoint_safe=True,
    )


def verify_acrl_bundle(
    bundle: DealACRLBundle,
    *,
    expected_deal_id: str,
    expected_tenant_id: str,
) -> bool:
    if bundle.deal_id != expected_deal_id:
        return False

    if bundle.tenant_id != expected_tenant_id:
        return False

    payload = {
        "deal_id": bundle.deal_id,
        "tenant_id": bundle.tenant_id,
        "snapshot": dict(
            bundle.deal_snapshot
        ),
    }

    return (
        bundle.reconstruction_fingerprint
        == _fingerprint(payload)
    )
