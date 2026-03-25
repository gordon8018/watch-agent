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
