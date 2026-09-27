from __future__ import annotations

from AUTONOMY_ENGINE.core import Project as RootProject
from AUTONOMY_ENGINE.core.inventory import Project as InventoryProject
from AUTONOMY_ENGINE.core.project import Project as CompatibilityProject


def test_project_has_one_canonical_implementation() -> None:
    assert RootProject is InventoryProject
    assert CompatibilityProject is InventoryProject
