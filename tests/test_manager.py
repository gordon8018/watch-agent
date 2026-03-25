from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from collector.base import AgentState
from collector.manager import CollectorManager


def _make_state(id: str, status="running", **kwargs) -> AgentState:
    return AgentState(id=id, name=id, status=status, **kwargs)


def test_merge_file_state_with_tmux_logs():
    file_states = [_make_state("a1", status="running", task="coding")]
    tmux_logs = {"a1": ["log line 1", "log line 2"]}
    tmux_metrics = {"a1": (10.0, 64.0)}

    mgr = CollectorManager.__new__(CollectorManager)
    result = mgr._merge(file_states, tmux_logs, tmux_metrics)

    assert result[0].recent_logs == ["log line 1", "log line 2"]
    assert result[0].cpu_percent == 10.0
    assert result[0].mem_mb == 64.0
    assert result[0].task == "coding"


def test_linger_keeps_missing_agent():
    mgr = CollectorManager.__new__(CollectorManager)
    mgr._linger_seconds = 30
    old_state = _make_state("a1", status="running")
    old_state.last_updated = datetime.now() - timedelta(seconds=10)
    mgr._previous: dict[str, AgentState] = {"a1": old_state}

    result = mgr._apply_linger(current_ids=set())
    assert len(result) == 1
    assert result[0].id == "a1"


def test_linger_removes_expired_agent():
    mgr = CollectorManager.__new__(CollectorManager)
    mgr._linger_seconds = 30
    old_state = _make_state("a1", status="running")
    old_state.last_updated = datetime.now() - timedelta(seconds=60)
    mgr._previous = {"a1": old_state}

    result = mgr._apply_linger(current_ids=set())
    assert result == []
