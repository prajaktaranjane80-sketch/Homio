from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge.readonly_controller_bridge import ReadOnlyControllerBridge

def main():
    if len(sys.argv) != 2:
        print("Usage: python bridge_cli.py <CONTROL_CENTER_ROOT>")
        return 2
    root = Path(sys.argv[1]).resolve()
    bridge = ReadOnlyControllerBridge(root)
    if not bridge.available():
        print(f"BLOCKED: controller not found: {bridge.controller}")
        return 3
    obs = bridge.observe()
    print("REOS AUTONOMOUS ENGINE — READ-ONLY BRIDGE")
    print("=" * 60)
    for k,v in obs.items():
        print(f"\n--- {k} ---")
        print(v.stdout.strip()[-4000:])
    print("\nMUTATION: BLOCKED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
