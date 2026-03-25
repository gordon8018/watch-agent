from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

StatusType = Literal["running", "idle", "error", "unknown"]

STATUS_COLORS: dict[str, str] = {
    "running": "green",
    "idle": "bright_black",
    "error": "red",
    "unknown": "yellow",
}


@dataclass
class AgentState:
    id: str
    name: str
    status: StatusType = "unknown"
    task: str = ""
    cwd: str = ""
    recent_logs: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    cpu_percent: float = 0.0
    mem_mb: float = 0.0
    completed_tasks: int = 0
    current_command: str = ""
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def is_active(self) -> bool:
        return self.status == "running"

    @property
    def status_color(self) -> str:
        return STATUS_COLORS.get(self.status, "yellow")

    @property
    def elapsed_str(self) -> str:
        total = int(self.elapsed_seconds)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
