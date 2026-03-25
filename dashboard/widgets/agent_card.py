from textual.widget import Widget
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.widgets import Log, Static
from collector.base import AgentState


class AgentDetailPanel(Widget):
    """展示选中 agent 的完整信息和日志。"""

    DEFAULT_CSS = """
    AgentDetailPanel {
        height: 1fr;
        border: solid $panel;
        padding: 0 1;
    }
    AgentDetailPanel #info {
        height: 4;
    }
    AgentDetailPanel #log-view {
        height: 1fr;
        border-top: solid $panel;
    }
    """

    state: reactive[AgentState | None] = reactive(None)

    def __init__(self, agent_state: AgentState | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = agent_state

    def build_info_lines(self) -> str:
        """返回可测试的信息字符串。"""
        s = self.state
        if s is None:
            return "No agent selected"
        cpu = f"{s.cpu_percent}%" if s.cpu_percent > 0 else "N/A"
        mem = f"{s.mem_mb} MB" if s.mem_mb > 0 else "N/A"
        return (
            f"名称: {s.name}  状态: {s.status}  耗时: {s.elapsed_str}\n"
            f"目录: {s.cwd}  命令: {s.current_command}  已完成: {s.completed_tasks}\n"
            f"CPU: {cpu}  内存: {mem}"
        )

    def compose(self) -> ComposeResult:
        yield Static(self.build_info_lines(), id="info")
        log_widget = Log(id="log-view", auto_scroll=True)
        yield log_widget

    def on_mount(self) -> None:
        self._refresh_logs()

    def update_state(self, state: AgentState) -> None:
        self.state = state
        info = self.query_one("#info", Static)
        info.update(self.build_info_lines())
        self._refresh_logs()

    def _refresh_logs(self) -> None:
        if self.state is None:
            return
        log_widget = self.query_one("#log-view", Log)
        log_widget.clear()
        for line in self.state.recent_logs:
            log_widget.write_line(line)
