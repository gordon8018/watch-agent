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
