import json
from collector.file_collector import FileCollector


def test_collect_valid_file(tmp_path):
    status_file = tmp_path / "agent-a1.json"
    status_file.write_text(json.dumps({
        "name": "feature-agent",
        "status": "running",
        "task": "writing tests",
        "cwd": "/home/user/project",
        "current_command": "pytest",
        "completed_tasks": 3,
    }))
    collector = FileCollector(status_dir=str(tmp_path))
    states = collector.collect()
    assert len(states) == 1
    assert states[0].id == "a1"
    assert states[0].status == "running"
    assert states[0].completed_tasks == 3


def test_collect_corrupt_file(tmp_path):
    bad_file = tmp_path / "agent-bad.json"
    bad_file.write_text("{ not valid json")
    collector = FileCollector(status_dir=str(tmp_path))
    states = collector.collect()
    # 损坏文件跳过，不崩溃
    assert states == []


def test_collect_no_files(tmp_path):
    collector = FileCollector(status_dir=str(tmp_path))
    assert collector.collect() == []


def test_collect_preserves_previous_on_corrupt(tmp_path):
    status_file = tmp_path / "agent-a1.json"
    status_file.write_text(json.dumps({"name": "a1", "status": "idle"}))
    collector = FileCollector(status_dir=str(tmp_path))
    first = collector.collect()
    assert len(first) == 1

    status_file.write_text("{ broken")
    second = collector.collect()
    # 上次有效数据保留
    assert len(second) == 1
    assert second[0].status == "idle"
