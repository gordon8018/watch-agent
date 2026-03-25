from datetime import datetime
from collector.base import AgentState


def test_agent_state_defaults():
    state = AgentState(id="a1", name="agent1")
    assert state.status == "unknown"
    assert state.recent_logs == []
    assert state.cpu_percent == 0.0
    assert state.completed_tasks == 0


def test_agent_state_is_active_running():
    state = AgentState(id="a1", name="agent1", status="running")
    assert state.is_active is True


def test_agent_state_is_active_idle():
    state = AgentState(id="a1", name="agent1", status="idle")
    assert state.is_active is False


def test_agent_state_status_color():
    assert AgentState(id="a1", name="a", status="running").status_color == "green"
    assert AgentState(id="a1", name="a", status="idle").status_color == "bright_black"
    assert AgentState(id="a1", name="a", status="error").status_color == "red"
    assert AgentState(id="a1", name="a", status="unknown").status_color == "yellow"


def test_agent_state_elapsed_str():
    state = AgentState(id="a1", name="a", elapsed_seconds=3661.0)
    assert state.elapsed_str == "01:01:01"
