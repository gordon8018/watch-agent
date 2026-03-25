# Watch Agent Dashboard Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个运行在终端中的实时 dashboard，通过 Textual 展示多个并行 Claude Code agent 的工作状态、日志和进程指标。

**Architecture:** CollectorManager 每 2 秒从三路数据源（tmux 输出、状态文件、psutil 进程指标）采集数据，合并为 AgentState 列表，通过 Textual 的 `set_interval` 驱动 UI 刷新。UI 分为顶部摘要栏（所有 agent 徽章）和底部详细面板（自动展示最活跃 agent 的日志与指标）。

**Tech Stack:** Python 3.11+, Textual ≥ 0.50.0, psutil ≥ 5.9.0

---

## Chunk 1: 项目骨架与数据模型

### Task 1: 初始化项目结构与依赖

**Files:**
- Create: `pyproject.toml`
- Create: `main.py`
- Create: `collector/__init__.py`
- Create: `collector/base.py`
- Create: `dashboard/__init__.py`
- Create: `dashboard/widgets/__init__.py`
- Create: `tests/__init__.py`
- Create: `config.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "watch-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "textual>=0.50.0",
    "psutil>=5.9.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]
```

- [ ] **Step 2: 安装依赖**

```bash
pip install -e ".[dev]"
```

Expected: 安装成功，`textual --version` 输出版本号。

- [ ] **Step 3: 创建所有空的 `__init__.py`**

```bash
touch collector/__init__.py dashboard/__init__.py dashboard/widgets/__init__.py tests/__init__.py
```

- [ ] **Step 4: 创建 `config.py`**

```python
# config.py
import argparse

REFRESH_INTERVAL: float = 2.0       # 秒
LOG_LINES: int = 100                # 保留日志行数
TMUX_SESSION: str = "agents"        # tmux session 名
STATUS_DIR: str = "/tmp"            # 状态文件目录
AGENT_LINGER_SECONDS: int = 30      # agent 消失后保留卡片的秒数


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch Agent Dashboard")
    parser.add_argument("--session", default=TMUX_SESSION, help="tmux session name")
    parser.add_argument("--status-dir", default=STATUS_DIR, help="directory for agent status files")
    return parser.parse_args()
```

- [ ] **Step 5: 创建占位 `main.py`**

```python
# main.py
from config import parse_args

if __name__ == "__main__":
    args = parse_args()
    print(f"session={args.session}, status_dir={args.status_dir}")
```

- [ ] **Step 6: 验证启动**

```bash
python main.py --session test
```

Expected: 输出 `session=test, status_dir=/tmp`

- [ ] **Step 7: 提交**

```bash
git init
git add pyproject.toml main.py config.py collector/__init__.py dashboard/__init__.py dashboard/widgets/__init__.py tests/__init__.py
git commit -m "chore: init project structure and dependencies"
```

---

### Task 2: AgentState 数据模型

**Files:**
- Create: `collector/base.py`
- Create: `tests/test_base.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_base.py
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_base.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'collector.base'` 或 `ImportError`

- [ ] **Step 3: 实现 `collector/base.py`**

```python
# collector/base.py
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_base.py -v
```

Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add collector/base.py tests/test_base.py
git commit -m "feat: add AgentState dataclass with status helpers"
```

---

## Chunk 2: 数据采集层

### Task 3: 状态文件采集器

**Files:**
- Create: `collector/file_collector.py`
- Create: `tests/test_file_collector.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_file_collector.py
import json
import os
import tempfile
from collector.file_collector import FileCollector


def test_collect_valid_file(tmp_path):
    status_file = tmp_path / "agent-a1.json"
    status_file.write_text(json.dumps({
        "name": "feature-agent",
        "status": "running",
        "task": "writing tests",
        "cwd": "/home/user/project",
        "current_command": "pytest",
        "completed_tasks": 3,
    }))
    collector = FileCollector(status_dir=str(tmp_path))
    states = collector.collect()
    assert len(states) == 1
    assert states[0].id == "a1"
    assert states[0].status == "running"
    assert states[0].completed_tasks == 3


def test_collect_corrupt_file(tmp_path):
    bad_file = tmp_path / "agent-bad.json"
    bad_file.write_text("{ not valid json")
    collector = FileCollector(status_dir=str(tmp_path))
    states = collector.collect()
    # 损坏文件跳过，不崩溃
    assert states == []


def test_collect_no_files(tmp_path):
    collector = FileCollector(status_dir=str(tmp_path))
    assert collector.collect() == []


def test_collect_preserves_previous_on_corrupt(tmp_path):
    status_file = tmp_path / "agent-a1.json"
    status_file.write_text(json.dumps({"name": "a1", "status": "idle"}))
    collector = FileCollector(status_dir=str(tmp_path))
    first = collector.collect()
    assert len(first) == 1

    status_file.write_text("{ broken")
    second = collector.collect()
    # 上次有效数据保留
    assert len(second) == 1
    assert second[0].status == "idle"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_file_collector.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 `collector/file_collector.py`**

```python
# collector/file_collector.py
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_file_collector.py -v
```

Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add collector/file_collector.py tests/test_file_collector.py
git commit -m "feat: add FileCollector with corrupt-file resilience"
```

---

### Task 4: tmux + psutil 采集器

**Files:**
- Create: `collector/tmux_collector.py`
- Create: `tests/test_tmux_collector.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_tmux_collector.py
from unittest.mock import patch, MagicMock
from collector.tmux_collector import TmuxCollector


def test_list_panes_returns_empty_on_tmux_error():
    collector = TmuxCollector(session="nonexistent-session-xyz")
    panes = collector.list_panes()
    assert panes == []


def test_capture_logs_returns_empty_on_error():
    collector = TmuxCollector(session="nonexistent-session-xyz")
    logs = collector.capture_logs("0.0")
    assert logs == []


def test_capture_logs_splits_lines():
    collector = TmuxCollector(session="test")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="line1\nline2\nline3\n"
        )
        logs = collector.capture_logs("0.0", max_lines=2)
    assert logs == ["line2", "line3"]


def test_get_pane_pid_returns_none_on_error():
    collector = TmuxCollector(session="nonexistent-session-xyz")
    pid = collector.get_pane_pid("0.0")
    assert pid is None


def test_collect_metrics_returns_na_when_no_pid():
    collector = TmuxCollector(session="test")
    cpu, mem = collector.collect_metrics(None)
    assert cpu == 0.0
    assert mem == 0.0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_tmux_collector.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 `collector/tmux_collector.py`**

```python
# collector/tmux_collector.py
from __future__ import annotations
import subprocess
from typing import Optional
import psutil
from config import LOG_LINES


class TmuxCollector:
    """从 tmux 窗格采集日志输出，并通过 psutil 采集进程指标。"""

    def __init__(self, session: str) -> None:
        self._session = session

    def list_panes(self) -> list[dict]:
        """返回 session 中所有窗格的信息列表。"""
        result = subprocess.run(
            ["tmux", "list-panes", "-t", self._session, "-a",
             "-F", "#{window_index}.#{pane_index}:#{pane_title}:#{pane_pid}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return []
        panes = []
        for line in result.stdout.strip().splitlines():
            parts = line.split(":", 2)
            if len(parts) == 3:
                panes.append({
                    "pane_id": parts[0],
                    "title": parts[1],
                    "pid": int(parts[2]) if parts[2].isdigit() else None,
                })
        return panes

    def capture_logs(self, pane_id: str, max_lines: int = LOG_LINES) -> list[str]:
        """捕获指定窗格最近 max_lines 行输出。"""
        result = subprocess.run(
            ["tmux", "capture-pane", "-p", "-t",
             f"{self._session}:{pane_id}", "-S", f"-{max_lines}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return []
        lines = result.stdout.splitlines()
        return lines[-max_lines:] if len(lines) > max_lines else lines

    def get_pane_pid(self, pane_id: str) -> Optional[int]:
        """获取窗格 shell 的 PID。"""
        result = subprocess.run(
            ["tmux", "display-message", "-t", f"{self._session}:{pane_id}",
             "-p", "#{pane_pid}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return None
        pid_str = result.stdout.strip()
        return int(pid_str) if pid_str.isdigit() else None

    def collect_metrics(self, shell_pid: Optional[int]) -> tuple[float, float]:
        """返回 (cpu_percent, mem_mb)，汇总 shell 及其所有子进程。"""
        if shell_pid is None:
            return 0.0, 0.0
        try:
            proc = psutil.Process(shell_pid)
            all_procs = [proc] + proc.children(recursive=True)
            cpu = sum(p.cpu_percent(interval=None) for p in all_procs)
            mem = sum(p.memory_info().rss for p in all_procs) / (1024 * 1024)
            return round(cpu, 1), round(mem, 1)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0, 0.0
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_tmux_collector.py -v
```

Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add collector/tmux_collector.py tests/test_tmux_collector.py
git commit -m "feat: add TmuxCollector for logs and process metrics"
```

---

### Task 5: CollectorManager（聚合器）

**Files:**
- Create: `collector/manager.py`
- Create: `tests/test_manager.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_manager.py
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from collector.base import AgentState
from collector.manager import CollectorManager


def _make_state(id: str, status="running", **kwargs) -> AgentState:
    return AgentState(id=id, name=id, status=status, **kwargs)


def test_merge_file_state_with_tmux_logs():
    file_states = [_make_state("a1", status="running", task="coding")]
    tmux_logs = {"a1": ["log line 1", "log line 2"]}
    tmux_metrics = {"a1": (10.0, 64.0)}

    mgr = CollectorManager.__new__(CollectorManager)
    result = mgr._merge(file_states, tmux_logs, tmux_metrics)

    assert result[0].recent_logs == ["log line 1", "log line 2"]
    assert result[0].cpu_percent == 10.0
    assert result[0].mem_mb == 64.0
    assert result[0].task == "coding"


def test_linger_keeps_missing_agent():
    mgr = CollectorManager.__new__(CollectorManager)
    mgr._linger_seconds = 30
    old_state = _make_state("a1", status="running")
    old_state.last_updated = datetime.now() - timedelta(seconds=10)
    mgr._previous: dict[str, AgentState] = {"a1": old_state}

    result = mgr._apply_linger(current_ids=set(), all_states=[])
    assert len(result) == 1
    assert result[0].id == "a1"


def test_linger_removes_expired_agent():
    mgr = CollectorManager.__new__(CollectorManager)
    mgr._linger_seconds = 30
    old_state = _make_state("a1", status="running")
    old_state.last_updated = datetime.now() - timedelta(seconds=60)
    mgr._previous = {"a1": old_state}

    result = mgr._apply_linger(current_ids=set(), all_states=[])
    assert result == []
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_manager.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 `collector/manager.py`**

```python
# collector/manager.py
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_manager.py -v
```

Expected: 3 passed

- [ ] **Step 5: 运行全部测试**

```bash
pytest tests/ -v
```

Expected: 全部通过（12+ tests）

- [ ] **Step 6: 提交**

```bash
git add collector/manager.py tests/test_manager.py
git commit -m "feat: add CollectorManager with linger and merge logic"
```

---

## Chunk 3: Textual UI 层

### Task 6: AgentBadge（摘要栏徽章）

**Files:**
- Create: `dashboard/widgets/agent_badge.py`
- Create: `tests/test_agent_badge.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_agent_badge.py
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_agent_badge.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 `dashboard/widgets/agent_badge.py`**

```python
# dashboard/widgets/agent_badge.py
from textual.widget import Widget
from textual.reactive import reactive
from textual.app import RenderResult
from textual import on
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

    state: reactive[AgentState] = reactive(None, recompose=True)

    def __init__(self, agent_state: AgentState, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = agent_state

    def render_text(self) -> str:
        """返回可测试的纯文本表示。"""
        icon = STATUS_ICONS.get(self.state.status, "?")
        task_preview = self.state.task[:14] + "…" if len(self.state.task) > 15 else self.state.task
        return f"{icon} {self.state.name}\n{self.state.status}\n{task_preview}"

    def render(self) -> RenderResult:
        icon = STATUS_ICONS.get(self.state.status, "?")
        text = Text()
        text.append(f"{icon} ", style=self.state.status_color)
        text.append(self.state.name, style="bold")
        text.append(f"\n{self.state.status}", style=self.state.status_color)
        task_preview = self.state.task[:14] + "…" if len(self.state.task) > 15 else self.state.task
        text.append(f"\n{task_preview}", style="dim")
        return text
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_agent_badge.py -v
```

Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add dashboard/widgets/agent_badge.py tests/test_agent_badge.py
git commit -m "feat: add AgentBadge widget for summary bar"
```

---

### Task 7: AgentDetailPanel（详细面板）

**Files:**
- Create: `dashboard/widgets/agent_card.py`
- Create: `tests/test_agent_card.py`

- [ ] **Step 1: 编写失败测试**

```python
# tests/test_agent_card.py
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_agent_card.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 `dashboard/widgets/agent_card.py`**

```python
# dashboard/widgets/agent_card.py
from textual.widget import Widget
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.widgets import Log, Static
from textual.containers import Vertical
from rich.text import Text
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

    state: reactive[AgentState | None] = reactive(None, recompose=True)

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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_agent_card.py -v
```

Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add dashboard/widgets/agent_card.py tests/test_agent_card.py
git commit -m "feat: add AgentDetailPanel with info and log view"
```

---

### Task 8: SummaryBar（摘要栏容器）

**Files:**
- Create: `dashboard/widgets/summary_bar.py`

- [ ] **Step 1: 实现 `dashboard/widgets/summary_bar.py`**

```python
# dashboard/widgets/summary_bar.py
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
```

- [ ] **Step 2: 运行全量测试**

```bash
pytest tests/ -v
```

Expected: 全部通过

- [ ] **Step 3: 提交**

```bash
git add dashboard/widgets/summary_bar.py
git commit -m "feat: add SummaryBar widget with agent badge grid"
```

---

### Task 9: WatchApp 主应用与样式

**Files:**
- Create: `dashboard/app.py`
- Create: `dashboard/styles.tcss`
- Modify: `main.py`

- [ ] **Step 1: 创建 `dashboard/styles.tcss`**

```css
/* dashboard/styles.tcss */
Screen {
    background: $surface;
    layout: vertical;
}

#summary {
    height: 6;
}

#detail {
    height: 1fr;
}
```

- [ ] **Step 2: 实现 `dashboard/app.py`**

```python
# dashboard/app.py
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

    def _tick(self) -> None:
        self._states = self._manager.refresh()
        summary = self.query_one("#summary", SummaryBar)
        summary.refresh_states(self._states)

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
```

- [ ] **Step 3: 更新 `main.py`**

```python
# main.py
from config import parse_args
from dashboard.app import WatchApp

if __name__ == "__main__":
    args = parse_args()
    app = WatchApp(session=args.session, status_dir=args.status_dir)
    app.run()
```

- [ ] **Step 4: 运行全量测试**

```bash
pytest tests/ -v
```

Expected: 全部通过

- [ ] **Step 5: 手动冒烟测试**

```bash
python main.py --session agents
```

Expected: Textual dashboard 启动，显示摘要栏和详细面板，按 `q` 退出。

- [ ] **Step 6: 提交**

```bash
git add dashboard/app.py dashboard/styles.tcss main.py
git commit -m "feat: add WatchApp Textual main app with auto-refresh"
```

---

## Chunk 4: 收尾与文档

### Task 10: Agent 状态文件写入示例

**Files:**
- Create: `agent_status_writer.py`

- [ ] **Step 1: 创建写入示例脚本**

```python
# agent_status_writer.py
"""
Agent 在任务切换时调用此脚本更新状态文件。
用法: python agent_status_writer.py --id agent1 --status running --task "写测试"
"""
import argparse
import json
import os
import tempfile


def write_status(agent_id: str, status: str, task: str,
                 cwd: str, command: str, completed: int,
                 status_dir: str = "/tmp") -> None:
    data = {
        "name": agent_id,
        "status": status,
        "task": task,
        "cwd": cwd,
        "current_command": command,
        "completed_tasks": completed,
    }
    target = os.path.join(status_dir, f"agent-{agent_id}.json")
    # 原子写入：先写临时文件再重命名，避免读写竞争
    fd, tmp_path = tempfile.mkstemp(dir=status_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_path, target)
    except Exception:
        os.unlink(tmp_path)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--status", default="running")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--command", default="")
    parser.add_argument("--completed", type=int, default=0)
    parser.add_argument("--status-dir", default="/tmp")
    args = parser.parse_args()
    write_status(args.id, args.status, args.task,
                 args.cwd, args.command, args.completed, args.status_dir)
    target_path = os.path.join(args.status_dir, f"agent-{args.id}.json")
    print(f"Status written: {target_path}")
```

- [ ] **Step 2: 验证原子写入**

```bash
python agent_status_writer.py --id test1 --status running --task "testing"
cat /tmp/agent-test1.json   # 默认 status_dir=/tmp
```

Expected: 输出合法 JSON，终端打印 `Status written: /tmp/agent-test1.json`

- [ ] **Step 3: 提交**

```bash
git add agent_status_writer.py
git commit -m "feat: add atomic agent status writer script"
```

---

### Task 11: 最终验收

- [ ] **Step 1: 运行全量测试**

```bash
pytest tests/ -v --tb=short
```

Expected: 全部通过，无警告

- [ ] **Step 2: 集成冒烟测试**

```bash
# 终端1：启动一个 tmux session
tmux new-session -d -s agents -n agent1

# 终端2：写入模拟状态
python agent_status_writer.py --id agent1 --status running --task "集成测试" --command "pytest"

# 终端3：启动 dashboard
python main.py --session agents
```

Expected: Dashboard 显示 agent1 的状态，日志滚动，2 秒刷新

- [ ] **Step 3: 最终提交**

```bash
git add .
git commit -m "chore: final integration verified"
```
