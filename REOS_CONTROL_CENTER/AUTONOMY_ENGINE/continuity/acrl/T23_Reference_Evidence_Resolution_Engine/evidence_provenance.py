from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    authority: str = (
        "REOS_CONTROL_CENTER"
    )

    layer: str = "T23"

    source: str = (
        "T23_Reference_Evidence_Resolution_Engine"
    )

    upstream_layers: tuple[int, ...] = (
        3,
        12,
        14,
        17,
        18,
        19,
        20,
        21,
        22,
    )

    mode: str = (
        "DETERMINISTIC_EVIDENCE_RESOLUTION"
    )

    def validate(self) -> None:
        if self.authority != (
            "REOS_CONTROL_CENTER"
        ):
            raise ValueError(
                "Invalid T23 authority."
            )

        if 22 not in self.upstream_layers:
            raise ValueError(
                "T22 must be upstream."
            )

        if self.mode != (
            "DETERMINISTIC_EVIDENCE_RESOLUTION"
        ):
            raise ValueError(
                "Invalid T23 provenance mode."
            )
