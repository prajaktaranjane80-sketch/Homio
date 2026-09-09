from pathlib import Path
import pytest
from .change_impact_analysis import ChangeImpactAnalyzer, ChangeImpactSecurityError

def test_absolute_escape_blocked(tmp_path: Path):
    root = tmp_path / "repo"; root.mkdir(); (root / "x.py").write_text("x=1\n")
    with pytest.raises(ChangeImpactSecurityError):
        ChangeImpactAnalyzer(root).analyze((str(tmp_path / "outside.py"),))
