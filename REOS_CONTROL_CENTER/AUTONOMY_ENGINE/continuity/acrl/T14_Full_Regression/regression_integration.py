"""ACRL T14 integration adapter."""
from __future__ import annotations
from pathlib import Path


def validate_acrl_tree(acrl_root: str | Path):
    """Validate T14 against an explicit ACRL root without mutating it."""
    from .regression_layer import RegressionLayerEngine
    return RegressionLayerEngine.validate_all_layers(Path(acrl_root).resolve())
