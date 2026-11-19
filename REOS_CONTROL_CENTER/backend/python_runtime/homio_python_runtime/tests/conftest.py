from __future__ import annotations

from pathlib import Path
import sys

PYTHON_RUNTIME_ROOT = Path(__file__).resolve().parents[2]
if str(PYTHON_RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_RUNTIME_ROOT))
