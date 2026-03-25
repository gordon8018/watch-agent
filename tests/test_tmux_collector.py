from unittest.mock import patch, MagicMock
from collector.tmux_collector import TmuxCollector


def test_list_panes_returns_empty_on_tmux_error():
    collector = TmuxCollector(session="nonexistent-session-xyz")
    panes = collector.list_panes()
    assert panes == []


def test_capture_logs_returns_empty_on_error():
    collector = TmuxCollector(session="nonexistent-session-xyz")
    logs = collector.capture_logs("0.0")
    assert logs == []


def test_capture_logs_splits_lines():
    collector = TmuxCollector(session="test")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="line1\nline2\nline3\n"
        )
        logs = collector.capture_logs("0.0", max_lines=2)
    assert logs == ["line2", "line3"]


def test_get_pane_pid_returns_none_on_error():
    collector = TmuxCollector(session="nonexistent-session-xyz")
    pid = collector.get_pane_pid("0.0")
    assert pid is None


def test_collect_metrics_returns_na_when_no_pid():
    collector = TmuxCollector(session="test")
    cpu, mem = collector.collect_metrics(None)
    assert cpu == 0.0
    assert mem == 0.0
