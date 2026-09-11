from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContinuityProvenance:
    authority: str = (
        "REOS_CONTROL_CENTER"
    )

    layer: str = "T24"

    source: str = (
        "T24_Cross_Chat_Continuity_Recovery_Engine"
    )

    upstream_layers: tuple[int, ...] = (
        3,
        7,
        8,
        9,
        10,
        11,
        12,
        14,
        22,
        23,
    )

    mode: str = (
        "AUTHORITATIVE_CROSS_CHAT_RECOVERY"
    )

    def validate(self) -> None:
        if self.authority != (
            "REOS_CONTROL_CENTER"
        ):
            raise ValueError(
                "Invalid T24 authority."
            )

        if 23 not in self.upstream_layers:
            raise ValueError(
                "T23 must be upstream."
            )

        if 12 not in self.upstream_layers:
            raise ValueError(
                "T12 must be upstream."
            )

        if self.mode != (
            "AUTHORITATIVE_CROSS_CHAT_RECOVERY"
        ):
            raise ValueError(
                "Invalid T24 provenance mode."
            )
