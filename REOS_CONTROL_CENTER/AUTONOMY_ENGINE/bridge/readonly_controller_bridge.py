from __future__ import annotations
import subprocess, sys
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Observation:
    command: str
    returncode: int
    stdout: str
    stderr: str

class ReadOnlyControllerBridge:
    SAFE_COMMANDS = ("verify-state","status","plan","gate","verify-all")
    BLOCKED_COMMANDS = {
        "complete-subtask","verify-criterion","validate-gate",
        "approve-gate","transition","repair","reset"
    }

    def __init__(self, control_root: Path):
        self.control_root = Path(control_root).resolve()
        self.controller = self.control_root / "reos_control_center.py"

    def available(self) -> bool:
        return self.controller.is_file()

    def run(self, command: str, timeout: int = 30) -> Observation:
        if command in self.BLOCKED_COMMANDS:
            raise PermissionError(f"Mutation blocked by autonomous bridge: {command}")
        if command not in self.SAFE_COMMANDS:
            raise PermissionError(f"Command not allow-listed: {command}")
        if not self.available():
            raise FileNotFoundError(self.controller)
        p = subprocess.run(
            [sys.executable, str(self.controller), command],
            cwd=self.control_root, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace"
        )
        return Observation(command, p.returncode, p.stdout, p.stderr)

    def observe(self):
        return {cmd: self.run(cmd) for cmd in self.SAFE_COMMANDS}
