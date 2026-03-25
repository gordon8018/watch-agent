from collector.base import AgentState
from dashboard.widgets.agent_card import AgentDetailPanel


def test_panel_renders_all_fields():
    state = AgentState(
        id="a1", name="agent1", status="running",
        task="writing tests", cwd="/home/user/proj",
        current_command="pytest", completed_tasks=5,
        elapsed_seconds=3661, cpu_percent=23.5, mem_mb=128.0,
        recent_logs=["log1", "log2"],
    )
    panel = AgentDetailPanel(state)
    info = panel.build_info_lines()
    assert "agent1" in info
    assert "01:01:01" in info
    assert "23.5%" in info
    assert "128.0 MB" in info
    assert "5" in info


def test_panel_na_on_zero_metrics():
    state = AgentState(id="a1", name="agent1", cpu_percent=0.0, mem_mb=0.0)
    panel = AgentDetailPanel(state)
    info = panel.build_info_lines()
    assert "N/A" in info
