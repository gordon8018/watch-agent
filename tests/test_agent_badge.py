from collector.base import AgentState
from dashboard.widgets.agent_badge import AgentBadge


def test_badge_renders_status_icon():
    state = AgentState(id="a1", name="agent1", status="running", task="coding")
    badge = AgentBadge(state)
    rendered = badge.render_text()
    assert "●" in rendered
    assert "agent1" in rendered


def test_badge_error_icon():
    state = AgentState(id="a1", name="agent1", status="error")
    badge = AgentBadge(state)
    rendered = badge.render_text()
    assert "✗" in rendered


def test_badge_idle_icon():
    state = AgentState(id="a1", name="agent1", status="idle")
    badge = AgentBadge(state)
    rendered = badge.render_text()
    assert "○" in rendered
