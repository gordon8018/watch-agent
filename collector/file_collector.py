from __future__ import annotations
import glob
import json
import os
import re
from datetime import datetime
from collector.base import AgentState, StatusType


class FileCollector:
    """从 /tmp/agent-{id}.json 文件采集 agent 状态。"""

    def __init__(self, status_dir: str = "/tmp") -> None:
        self._status_dir = status_dir
        self._cache: dict[str, AgentState] = {}

    def collect(self) -> list[AgentState]:
        pattern = os.path.join(self._status_dir, "agent-*.json")
        results: list[AgentState] = []

        for path in glob.glob(pattern):
            agent_id = self._extract_id(path)
            if agent_id is None:
                continue
            state = self._read_file(path, agent_id)
            if state is not None:
                self._cache[agent_id] = state
                results.append(state)
            elif agent_id in self._cache:
                results.append(self._cache[agent_id])

        return results

    def _extract_id(self, path: str) -> str | None:
        basename = os.path.basename(path)
        m = re.match(r"^agent-(.+)\.json$", basename)
        return m.group(1) if m else None

    def _read_file(self, path: str, agent_id: str) -> AgentState | None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        status: StatusType = data.get("status", "unknown")
        if status not in ("running", "idle", "error", "unknown"):
            status = "unknown"

        return AgentState(
            id=agent_id,
            name=data.get("name", agent_id),
            status=status,
            task=data.get("task", ""),
            cwd=data.get("cwd", ""),
            current_command=data.get("current_command", ""),
            completed_tasks=int(data.get("completed_tasks", 0)),
            last_updated=datetime.now(),
        )
