import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from bridge.readonly_controller_bridge import ReadOnlyControllerBridge

def make_cc(tmp_path):
    cc = tmp_path/"cc"
    cc.mkdir()
    (cc/"reos_control_center.py").write_text("print('fake')",encoding="utf-8")
    return cc

def test_bridge_entrypoint_exists():
    assert (Path(__file__).parents[1]/"bridge_cli.py").is_file()

def test_mutations_blocked(tmp_path):
    bridge = ReadOnlyControllerBridge(make_cc(tmp_path))
    try:
        bridge.run("approve-gate")
    except PermissionError:
        return
    raise AssertionError("mutation was not blocked")

def test_unknown_command_blocked(tmp_path):
    bridge = ReadOnlyControllerBridge(make_cc(tmp_path))
    try:
        bridge.run("anything")
    except PermissionError:
        return
    raise AssertionError("unknown command was not blocked")
