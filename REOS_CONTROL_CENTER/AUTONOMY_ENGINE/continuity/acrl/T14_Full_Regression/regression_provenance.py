"""ACRL T14 provenance model."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class RegressionProvenance:
    authority: str = "REOS_CONTROL_CENTER"
    source: str = "T14_Full_Regression"
    upstream_layers: Tuple[int, ...] = tuple(range(1, 14))
    evidence_mode: str = "READ_ONLY_SOURCE_AND_TEST_INSPECTION"

    def validate(self) -> None:
        if self.authority != "REOS_CONTROL_CENTER":
            raise ValueError("Invalid T14 provenance authority.")
        if self.source != "T14_Full_Regression":
            raise ValueError("Invalid T14 provenance source.")
        if self.upstream_layers != tuple(range(1, 14)):
            raise ValueError("T14 provenance must reference T01-T13 only.")
