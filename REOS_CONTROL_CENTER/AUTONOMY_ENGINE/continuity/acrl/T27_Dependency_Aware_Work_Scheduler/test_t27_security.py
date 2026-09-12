from pathlib import Path


SOURCE = Path(__file__).with_name(
    "scheduler_controller.py"
).read_text(
    encoding="utf-8"
)


def test_scheduler_has_no_execution_calls():
    forbidden = (
        "subprocess",
        "os.system",
        "os.popen",
        "Popen(",
        "shell=True",
        "git commit",
        "git push",
        "git reset",
    )

    for token in forbidden:
        assert token not in SOURCE


def test_scheduler_does_not_mutate_state_json():
    assert "state.json" not in SOURCE
