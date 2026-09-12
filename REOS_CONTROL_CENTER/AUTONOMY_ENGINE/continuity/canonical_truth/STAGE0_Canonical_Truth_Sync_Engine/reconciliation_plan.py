from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .truth_models import ReconciliationPlan


def to_dict(plan: ReconciliationPlan) -> dict[str, Any]:
    return asdict(plan)
