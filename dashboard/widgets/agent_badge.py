from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult
from rich.text import Text
from collector.base import AgentState

STATUS_ICONS = {
    "running": "●",
    "idle": "○",
    "error": "✗",
    "unknown": "?",
}


class AgentBadge(Widget):
    """摘要栏中单个 agent 的状态徽章。"""

    DEFAULT_CSS = """
    AgentBadge {
        width: 20;
        height: 4;
        border: solid $panel;
        padding: 0 1;
    }
    AgentBadge:hover {
        border: solid $accent;
    }
    """

    state: reactive[AgentState | None] = reactive(None, recompose=True)

    def __init__(self, agent_state: AgentState, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = agent_state

    def render_text(self) -> str:
        """返回可测试的纯文本表示。"""
        if self.state is None:
            return "? loading\nunknown\n"
        icon = STATUS_ICONS.get(self.state.status, "?")
        task_preview = self.state.task[:14] + "…" if len(self.state.task) > 15 else self.state.task
        return f"{icon} {self.state.name}\n{self.state.status}\n{task_preview}"

    def render(self) -> RenderResult:
        if self.state is None:
            return Text("?")
        icon = STATUS_ICONS.get(self.state.status, "?")
        text = Text()
        text.append(f"{icon} ", style=self.state.status_color)
        text.append(self.state.name, style="bold")
        text.append(f"\n{self.state.status}", style=self.state.status_color)
        task_preview = self.state.task[:14] + "…" if len(self.state.task) > 15 else self.state.task
        text.append(f"\n{task_preview}", style="dim")
        return text
