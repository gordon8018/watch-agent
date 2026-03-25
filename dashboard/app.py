from textual.app import App, ComposeResult
from textual.widgets import Footer
from collector.manager import CollectorManager
from collector.base import AgentState
from dashboard.widgets.summary_bar import SummaryBar
from dashboard.widgets.agent_card import AgentDetailPanel
from config import REFRESH_INTERVAL


class WatchApp(App):
    """Watch Agent Dashboard 主应用。"""

    CSS_PATH = "styles.tcss"
    BINDINGS = [("q", "quit", "退出")]

    def __init__(self, session: str, status_dir: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._manager = CollectorManager(session=session, status_dir=status_dir)
        self._states: list[AgentState] = []

    def compose(self) -> ComposeResult:
        yield SummaryBar(id="summary")
        yield AgentDetailPanel(id="detail")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(REFRESH_INTERVAL, self._tick)

    async def _tick(self) -> None:
        self._states = self._manager.refresh()
        summary = self.query_one("#summary", SummaryBar)
        await summary.refresh_states(self._states)

        detail = self.query_one("#detail", AgentDetailPanel)
        target = self._select_detail_agent()
        if target is not None:
            detail.update_state(target)

    def _select_detail_agent(self) -> AgentState | None:
        """优先展示 running 中最近更新的 agent。"""
        running = [s for s in self._states if s.status == "running"]
        if running:
            return max(running, key=lambda s: s.last_updated)
        if self._states:
            return max(self._states, key=lambda s: s.last_updated)
        return None
