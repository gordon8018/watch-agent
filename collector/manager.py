from __future__ import annotations
from datetime import datetime
from collector.base import AgentState
from collector.file_collector import FileCollector
from collector.tmux_collector import TmuxCollector
from config import AGENT_LINGER_SECONDS


class CollectorManager:
    """聚合三路数据源，生成最新的 AgentState 列表。"""

    def __init__(self, session: str, status_dir: str) -> None:
        self._file = FileCollector(status_dir=status_dir)
        self._tmux = TmuxCollector(session=session)
        self._linger_seconds = AGENT_LINGER_SECONDS
        self._previous: dict[str, AgentState] = {}

    def refresh(self) -> list[AgentState]:
        """采集所有数据源并返回合并后的状态列表。"""
        file_states = self._file.collect()
        panes = self._tmux.list_panes()

        tmux_logs: dict[str, list[str]] = {}
        tmux_metrics: dict[str, tuple[float, float]] = {}
        for pane in panes:
            pid = pane.get("pid")
            pane_id = pane["pane_id"]
            title = pane.get("title", pane_id)
            tmux_logs[title] = self._tmux.capture_logs(pane_id)
            tmux_metrics[title] = self._tmux.collect_metrics(pid)

        merged = self._merge(file_states, tmux_logs, tmux_metrics)
        current_ids = {s.id for s in merged}
        lingered = self._apply_linger(current_ids, merged)
        all_states = merged + lingered

        self._previous = {s.id: s for s in all_states}
        return all_states

    def _merge(
        self,
        file_states: list[AgentState],
        tmux_logs: dict[str, list[str]],
        tmux_metrics: dict[str, tuple[float, float]],
    ) -> list[AgentState]:
        for state in file_states:
            if state.id in tmux_logs:
                state.recent_logs = tmux_logs[state.id]
            if state.id in tmux_metrics:
                state.cpu_percent, state.mem_mb = tmux_metrics[state.id]
        return file_states

    def _apply_linger(
        self,
        current_ids: set[str],
        all_states: list[AgentState],
    ) -> list[AgentState]:
        lingered = []
        now = datetime.now()
        for agent_id, state in self._previous.items():
            if agent_id in current_ids:
                continue
            age = (now - state.last_updated).total_seconds()
            if age < self._linger_seconds:
                lingered.append(state)
        return lingered
