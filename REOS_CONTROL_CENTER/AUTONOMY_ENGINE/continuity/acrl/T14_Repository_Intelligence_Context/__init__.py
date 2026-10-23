
"""ACRL T14 — Full Regression Layer public package.

This package exposes the regression-layer API only.
It does not re-export the separate repository-context or fast-resume API.
"""

from .regression_layer import (
    RegressionDecision,
    RegressionLayerEngine,
    RegressionLayerError,
    RegressionLayerIntegrityError,
    RegressionLayerResult,
    RegressionLayerSpec,
    RegressionLayerValidationError,
    RegressionReason,
    RegressionReport,
    acrl_regression_ready,
    validate_acrl_regression,
)
from .regression_policy import RegressionPolicy
from .regression_provenance import RegressionProvenance
from .regression_registry import (
    CanonicalLayerSpec,
    RegressionRegistry,
)

__all__ = [
    "CanonicalLayerSpec",
    "RegressionDecision",
    "RegressionLayerEngine",
    "RegressionLayerError",
    "RegressionLayerIntegrityError",
    "RegressionLayerResult",
    "RegressionLayerSpec",
    "RegressionLayerValidationError",
    "RegressionPolicy",
    "RegressionProvenance",
    "RegressionReason",
    "RegressionRegistry",
    "RegressionReport",
    "acrl_regression_ready",
    "validate_acrl_regression",
]
