from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Label
from collector.base import AgentState
from dashboard.widgets.agent_badge import AgentBadge


class SummaryBar(Widget):
    """顶部摘要栏，横向展示所有 agent 的徽章。"""

    DEFAULT_CSS = """
    SummaryBar {
        height: 6;
        border-bottom: solid $panel;
    }
    SummaryBar #badges {
        height: 5;
        overflow-x: auto;
    }
    SummaryBar #title-row {
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._states: list[AgentState] = []

    def compose(self) -> ComposeResult:
        yield Label("", id="title-row")
        yield ScrollableContainer(Horizontal(id="badges-inner"), id="badges")

    def refresh_states(self, states: list[AgentState]) -> None:
        self._states = states
        running = sum(1 for s in states if s.status == "running")
        errors = sum(1 for s in states if s.status == "error")
        title = self.query_one("#title-row", Label)
        title.update(
            f"Watch Agent Dashboard    [总计: {len(states)}]  "
            f"[green]运行: {running}[/green]  [red]错误: {errors}[/red]"
        )
        inner = self.query_one("#badges-inner", Horizontal)
        inner.remove_children()
        for state in states:
            inner.mount(AgentBadge(state, id=f"badge-{state.id}"))
